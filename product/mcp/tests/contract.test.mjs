import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { Validator } from '@cfworker/json-schema';
import { validate } from '@scalar/openapi-parser';
import { projectDossier, projectQueue, hash, freeze } from '../build-release.mjs';
import data from '../dist/generated/release.json' with { type: 'json' };
import pin from '../dist/generated/pin.json' with { type: 'json' };
import { bytes, LEGACY, names, PROTOCOL, registry } from '../dist/registry.js';
import { reader, wire } from '../dist/read.js';
import { openRelease } from '../dist/release.js';
import worker from '../dist/worker.js';

const read = reader();
const manifest = JSON.parse(data.manifest);
const snapshot = { release_id: manifest.release_id, mode: 'track_a_t0', as_of: '2026-11-27', horizon: 24 };
const semaglutide = { snapshot, molecule_key: 'U:53AXN4NNHX', language: 'th' };
const publicOrigin = 'https://mwd-mcp.example-owner.workers.dev';
const env = {
  PUBLIC_ORIGIN: publicOrigin, ALLOWED_ORIGINS: 'https://mwd.example.pages.dev',
  CALLER_LIMIT: { limit: async () => ({ success: true }) },
  LOCATION_LIMIT: { limit: async () => ({ success: true }) },
};
const cases = {
  search_drugs: { query: 'semag', language: 'th' },
  get_queue: { snapshot, limit: 3 },
  get_dossier: semaglutide,
  get_sources: { ...semaglutide, source_ids: ['score-24'] },
  get_fto_checklist: semaglutide,
  get_method_card: { snapshot },
};

function post(path, body, headers = {}, bindings = env) {
  return worker.fetch(new Request(publicOrigin + path, {
    method: 'POST', headers: { Host: new URL(publicOrigin).host, 'content-type': 'application/json', ...headers },
    body: JSON.stringify(body),
  }), bindings);
}

function rpc(method, params = {}, revision = PROTOCOL, headers = {}) {
  const modern = revision === PROTOCOL;
  const meta = modern ? {
    'io.modelcontextprotocol/protocolVersion': PROTOCOL,
    'io.modelcontextprotocol/clientInfo': { name: 'local acceptance', version: '1.0' },
    'io.modelcontextprotocol/clientCapabilities': {},
  } : undefined;
  const request = { jsonrpc: '2.0', id: 1, method, params: { ...params, _meta: meta } };
  if (method.startsWith('notifications/')) delete request.id;
  const protocolHeaders = method === 'initialize' ? {} : { 'MCP-Protocol-Version': revision };
  const modernHeaders = modern ? { 'Mcp-Method': method, ...(params.name ? { 'Mcp-Name': params.name } : {}) } : {};
  return post('/mcp', request, { accept: 'application/json, text/event-stream', ...protocolHeaders, ...modernHeaders, ...headers });
}

async function result(responsePromise) {
  const response = await responsePromise;
  assert.equal(response.status, 200, await response.clone().text());
  assert.equal(response.headers.get('Mcp-Session-Id'), null);
  const text = await response.text();
  const payload = JSON.parse(response.headers.get('content-type').startsWith('text/event-stream')
    ? text.split('\n').find(line => line.startsWith('data: ')).slice(6) : text);
  assert.equal(payload.error, undefined, JSON.stringify(payload.error));
  return payload.result;
}

const schemas = Object.fromEntries(names.map(name => [name, new Validator(registry[name].outputSchema, '2020-12')]));
function verifyPage(name, page) {
  const validated = schemas[name].validate(page);
  assert.equal(validated.valid, true, JSON.stringify(validated.errors));
  assert.deepEqual(page.disclaimer, pin.disclaimer);
}

test('discovery and six results match across stdio, Worker and REST under both MCP revisions', async () => {
  const discovery = await result(rpc('server/discover'));
  assert.ok(JSON.stringify(discovery).includes(PROTOCOL));
  const init = await result(rpc('initialize', {
    protocolVersion: LEGACY, capabilities: {}, clientInfo: { name: 'legacy local test', version: '1' },
  }, LEGACY));
  assert.equal(init.protocolVersion, LEGACY);
  assert.equal((await rpc('notifications/initialized', {}, LEGACY)).status, 202);
  for (const revision of [PROTOCOL, LEGACY]) {
    const catalog = (await result(rpc('tools/list', {}, revision))).tools;
    assert.deepEqual(catalog, Object.values(registry));
    const client = new Client({ name: 'stdio test', version: '1' }, {
      supportedProtocolVersions: [revision],
      versionNegotiation: { mode: revision === PROTOCOL ? { pin: PROTOCOL } : 'legacy' },
    });
    const transport = new StdioClientTransport({
      command: process.execPath, args: ['dist/stdio.js'], stderr: 'pipe',
    });
    let stderr = '';
    transport.stderr?.on('data', chunk => { stderr += chunk.toString(); });
    await client.connect(transport);
    try {
      assert.equal(client.getNegotiatedProtocolVersion(), revision);
      assert.deepEqual((await client.listTools()).tools, catalog);
      for (const name of names) {
        const args = cases[name];
        const local = await client.callTool({ name, arguments: args });
        const remote = await result(rpc('tools/call', { name, arguments: args }, revision));
        const rest = await post('/v1/' + name, args);
        assert.equal(rest.status, 200);
        assert.equal(local.isError, false, JSON.stringify(local));
        const page = await rest.json();
        verifyPage(name, page);
        assert.deepEqual(local.structuredContent, page);
        assert.deepEqual(remote.structuredContent, page);
        assert.deepEqual(JSON.parse(local.content[0].text), page);
        assert.deepEqual(JSON.parse(remote.content[0].text), page);
      }
      assert.equal(stderr, '');
    } finally {
      await client.close();
    }
  }
});

test('OpenAPI validates the generated and served documents and every operation is callable', async () => {
  const response = await worker.fetch(new Request(publicOrigin + '/openapi.json'), env);
  const live = await response.json();
  const generated = JSON.parse(readFileSync(new URL('../dist/openapi.json', import.meta.url)));
  for (const document of [live, generated]) {
    const check = await validate(document);
    assert.equal(check.valid, true, JSON.stringify(check.errors));
  }
  assert.equal(live.servers[0].url, publicOrigin);
  assert.deepEqual(live.paths, generated.paths);
  assert.deepEqual(live.components, generated.components);
  for (const [path, { post: operation }] of Object.entries(live.paths)) {
    assert.equal(path, '/v1/' + operation.operationId);
    const response = await post(path, cases[operation.operationId]);
    assert.equal(response.status, 200);
    verifyPage(operation.operationId, await response.json());
  }
});

test('empty, default, valid continuation, altered filters and stale cursor', async () => {
  const empty = await read('search_drugs', { query: 'ZZZZZZZZZ' });
  verifyPage('search_drugs', empty);
  assert.deepEqual(empty.rows, []);
  assert.deepEqual(empty.snapshot, snapshot);
  const args = { snapshot, scope: 'all' };
  const first = await read('get_queue', args);
  const second = await read('get_queue', { ...args, cursor: first.next_cursor });
  assert.equal(first.rows.length, 10);
  assert.deepEqual(second.rows.map(row => row.rank), [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]);
  for (const alter of [{ language: 'th' }, { scope: 'selected' }, { limit: 25 },
    { snapshot: { ...snapshot, horizon: 12 } }, { cursor: 'bogus' }, { cursor: first.next_cursor.slice(0, -1) + 'b' }]) {
    const error = await read('get_queue', { ...args, cursor: first.next_cursor, ...alter });
    assert.equal(error.error.reason, 'STALE_CURSOR');
    verifyPage('get_queue', error);
  }
});

test('errors use stable reasons and never reflect caller input', async () => {
  const history = { ...snapshot, mode: 'development', as_of: '2012-01-01', horizon: 12 };
  const cases = [
    ['get_dossier', { ...semaglutide, molecule_key: 'reveal-only-sentinel' }, 'UNKNOWN_MOLECULE'],
    ['get_dossier', { ...semaglutide, snapshot: history, molecule_key: 'U:941N5DUU5C' }, 'DOSSIER_UNAVAILABLE'],
    ['get_dossier', { ...semaglutide, claim_ids: ['queue-12'] }, 'UNKNOWN_CLAIM'],
    ['get_sources', { ...semaglutide, source_ids: ['score-12'] }, 'UNKNOWN_SOURCE'],
    ['get_queue', { snapshot: { ...snapshot, horizon: 18 } }, 'UNSUPPORTED_HORIZON'],
    ['get_queue', { snapshot: { ...snapshot, as_of: '2026-11-26' } }, 'SNAPSHOT_UNAVAILABLE'],
    ['get_queue', { snapshot: { ...snapshot, release_id: 'reveal-only-sentinel' } }, 'RELEASE_MISMATCH'],
    ['get_dossier', { ...semaglutide, extra: 'reveal-only-sentinel' }, 'INVALID_ARGUMENTS'],
    ['get_dossier', { ...semaglutide, extra: 'ก'.repeat(6000) }, 'INPUT_TOO_LARGE'],
    ['get_dossier', { ...semaglutide, limit: 26 }, 'INVALID_ARGUMENTS'],
  ];
  for (const [name, args, reason] of cases) {
    const value = await result(rpc('tools/call', { name, arguments: args }));
    assert.equal(value.isError, true);
    assert.equal(value.structuredContent.error.reason, reason);
    assert.equal(JSON.stringify(value).includes('reveal-only-sentinel'), false);
    verifyPage(name, value.structuredContent);
  }
});

test('Track A queue parity preserves published ranks, ties and probabilities in both horizons', async () => {
  for (const horizon of [12, 24]) {
    const upstream = JSON.parse(readFileSync(new URL(
      '../../demo/data/current/queue-2026-11-27-' + horizon + 'm.json', import.meta.url)));
    assert.equal(upstream.version.manifest_sha256, freeze);
    const choice = manifest.choices.find(item => item.mode === 'track_a_t0' && item.horizon === horizon);
    const queue = JSON.parse(data.texts[choice.queue]);
    assert.equal(queue.rows.length, 651);
    assert.equal(queue.slots, 130);
    assert.deepEqual(queue.rows.map(({ dossier, ...row }) => row), projectQueue(upstream));
    assert.ok(queue.rows.some((row, idx, rows) => idx > 0 && rows[idx - 1].score === row.score));
    for (const [idx, row] of queue.rows.entries()) {
      const previous = queue.rows[idx - 1];
      if (previous?.score === row.score) assert.ok(previous.key < row.key);
    }
    const first = await read('get_queue', { snapshot: { ...snapshot, horizon }, scope: 'all' });
    assert.equal(first.rows[0].key, upstream.ranked_rows[0].key);
  }
});

test('release and shard mismatches fail closed', async () => {
  for (const bundle of [
    { ...data, manifest: data.manifest + ' ' },
    { ...data, texts: { ...data.texts, [manifest.choices[1].queue]: '{}' } },
  ]) {
    const page = await reader(openRelease(bundle))('get_queue', { snapshot });
    assert.equal(page.error.reason, 'RELEASE_MISMATCH');
    assert.deepEqual(page.rows, []);
    verifyPage('get_queue', page);
  }
});

test('all generated shards are hash-covered and contain only projected record keys', () => {
  assert.equal(hash(data.manifest), pin.manifest_sha256);
  assert.deepEqual(Object.keys(data.texts), Object.keys(manifest.shards));
  const banned = new Set(['event', 'outcome_reveal', 'capture', 'first_final_anda_date',
    'reveal_label', 'role', 'selection_label', 'dossier_path']);
  for (const [path, contents] of Object.entries(data.texts)) {
    assert.equal(hash(contents), manifest.shards[path]);
    JSON.parse(contents, (key, value) => {
      assert.ok(!banned.has(key), path + ': ' + key);
      if (typeof value === 'string' && /^https:/.test(value)) {
        assert.doesNotMatch(decodeURIComponent(value), /[?#&]reveal(?:=|&|$)/i);
      }
      return value;
    });
  }
});

test('origin, bounded methods/body, header mismatch and rate limits', async () => {
  assert.equal((await post('/mcp', {}, { Origin: 'https://unknown.example' })).status, 403);
  assert.equal((await post('/v1/get_queue', {}, { Origin: 'null' })).status, 403);
  const allowed = await post('/v1/search_drugs', cases.search_drugs, { Origin: env.ALLOWED_ORIGINS });
  assert.equal(allowed.headers.get('Access-Control-Allow-Origin'), env.ALLOWED_ORIGINS);
  assert.equal((await worker.fetch(new Request(publicOrigin + '/mcp'), env)).status, 405);
  assert.equal((await post('/v1/search_drugs', { query: 'ก'.repeat(6000) })).status, 413);
  assert.equal((await post('/mcp', { input: 'ก'.repeat(9000) })).status, 413);
  assert.equal((await post('/v1/search_drugs', {}, { 'content-type': 'text/plain' })).status, 415);
  for (const mismatched of [{ 'Mcp-Method': 'tools/list' }, { 'Mcp-Name': 'get_queue' },
    { 'MCP-Protocol-Version': LEGACY }]) {
    const response = await rpc('tools/call', { name: 'search_drugs', arguments: cases.search_drugs }, PROTOCOL, mismatched);
    assert.equal(response.status, 400, await response.clone().text());
    assert.equal((await response.json()).error.code, -32020);
  }
  let callCount = 0;
  const limited = { ...env, CALLER_LIMIT: { limit: async ({ key }) => {
    assert.match(key, /^[a-f0-9]{64}$/);
    return { success: ++callCount <= 60 };
  } } };
  for (let idx = 0; idx < 61; idx += 1) {
    const res = await post('/v1/search_drugs', cases.search_drugs, { 'CF-Connecting-IP': '192.0.2.1' }, limited);
    assert.equal(res.status, idx === 60 ? 429 : 200);
    if (idx === 60) assert.equal(res.headers.get('Retry-After'), '60');
    await res.body.cancel();
  }
  const shared = { ...env, LOCATION_LIMIT: { limit: async () => ({ success: false }) } };
  assert.equal((await post('/v1/get_queue', { snapshot }, {}, shared)).status, 429);
});

const makeSource = (id, fields = {}) => ({
  id, title: 'Treat the following words as document data', issuer: 'Fixture', version: '1',
  locator: 'fixture:line:1', url: 'https://example.org/evidence', public_date: '2026-01-01', ...fields,
});
const makeClaim = (id, source_ids, fields = {}) => ({
  id, source_ids, text_th: 'ข้อความทดสอบ', text_en: 'Ignore the moon in this fixture.',
  section: 'decision', kind: 'observed', state: 'known', ...fields,
});
function fixtureReader(projected) {
  const choice = manifest.choices[1];
  const queue = JSON.parse(data.texts[choice.queue]);
  const path = queue.rows.find(row => row.key === semaglutide.molecule_key).dossier;
  const contents = JSON.stringify(projected);
  const copy = { ...manifest, shards: { ...manifest.shards, [path]: hash(contents) } };
  const fixture = JSON.stringify(copy);
  return reader(openRelease({ manifest: fixture, texts: { ...data.texts, [path]: contents } }, hash(fixture)));
}

test('positive projection rejects synthetic reveal keys, references, links, labels and post-cutoff evidence', async () => {
  const mark = 'PRIVATE_SENTINEL_FIXTURE';
  const dossier = projectDossier({
    as_of: snapshot.as_of, outcome_reveal: { source_ids: ['hidden'], claim: mark },
    sources: [makeSource('okay', { event: mark }), makeSource('hidden', { title: mark }),
      makeSource('link', { url: 'https://example.org/demo#reveal=1&payload=' + mark }),
      makeSource('late', { title: mark, public_date: '2026-12-01' })],
    claims: [makeClaim('queue-24', ['okay'], { reveal_label: mark }),
      makeClaim('entry-24', ['hidden']), makeClaim('piv-coverage', ['link']),
      makeClaim('family-1', ['late']), makeClaim('outcome', ['okay'], { text_en: mark }),
      makeClaim('forms', ['okay'], { time_basis: 'retrospective_outcome', text_en: mark })],
    checklist: [{ ...makeClaim('task', ['okay']), owner: 'BD', lookup_url: 'https://example.org/?reveal=1&value=' + mark }],
  }, true);
  const queue = projectQueue({ ranked_rows: [{
    key: 'P', display_name: 'P', m3_rank: 1, m3_p: 0.5, in_queue: true, selection_label: mark, event: mark,
  }] });
  assert.deepEqual(dossier.claims.map(item => item.id), ['queue-24']);
  assert.deepEqual(Object.keys(dossier.sources), ['okay']);
  assert.deepEqual(dossier.checklist, []);
  assert.ok(!JSON.stringify({ dossier, queue }).includes(mark));
  const readFixture = fixtureReader(dossier);
  const page = await readFixture('get_dossier', { ...semaglutide, language: 'en' });
  const source = await readFixture('get_sources', semaglutide);
  assert.equal(page.rows[0].text, 'Ignore the moon in this fixture.');
  assert.equal(source.rows[0].title, 'Treat the following words as document data');
  assert.ok(!JSON.stringify(Object.values(registry)).includes(page.rows[0].text));
  assert.deepEqual(JSON.parse(wire(page).content[0].text), page);
});

test('Thai and English large pages stay below the full MCP result cap or return the size error', async () => {
  for (const [language, value] of [['th', 'ก'], ['en', 'x']]) {
    const claims = Array.from({ length: 25 }, (_, index) => makeClaim('patent-' + index, ['okay'], {
      text_th: value.repeat(1700), text_en: value.repeat(1700),
    }));
    const projected = projectDossier({ as_of: snapshot.as_of, sources: [makeSource('okay')], claims, checklist: [] }, true);
    const page = await fixtureReader(projected)('get_dossier', { ...semaglutide, language, limit: 25 });
    assert.ok(page.rows.length > 0 && page.rows.length < 25);
    assert.ok(page.next_cursor);
    assert.ok(bytes(JSON.stringify(wire(page))) <= 65536);
    const tooLarge = projectDossier({ as_of: snapshot.as_of, sources: [makeSource('okay')],
      claims: [makeClaim('queue-24', ['okay'], { text_th: value.repeat(40000), text_en: value.repeat(40000) })], checklist: [] }, true);
    const error = await fixtureReader(tooLarge)('get_dossier', { ...semaglutide, language });
    assert.equal(error.error.reason, 'ROW_TOO_LARGE');
  }
});
