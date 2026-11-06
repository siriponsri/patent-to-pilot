import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  SCOUT_DICT, displayTitle, fieldMap, formatMs, parseIpc3, primarySection, quoteSegments, requestKey, translator,
} from '../../app/src/scout/model.js';
import { createScoutAdapter } from '../../app/src/adapters.js';
import { resolvePath } from '../../serve.mjs';

const APP = resolve(dirname(fileURLToPath(import.meta.url)), '../../app');

test('scout TH and EN dictionaries have identical, non-empty key sets', () => {
  const en = Object.keys(SCOUT_DICT.en).sort(), th = Object.keys(SCOUT_DICT.th).sort();
  assert.deepEqual(th, en);
  for (const l of ['en', 'th']) for (const [k, v] of Object.entries(SCOUT_DICT[l])) assert.ok(v.trim(), `${l}.${k} empty`);
  assert.equal(translator('th')('scout.own.remove', { code: 'F16' }), 'ลบ F16');
  assert.equal(translator('xx')('scout.search'), 'Scout');
});

test('IPC parsing, titles and sections', () => {
  assert.equal(parseIpc3(' f16 '), 'F16');
  assert.equal(parseIpc3('F1'), null);
  assert.equal(parseIpc3('Z99'), null);
  assert.equal(displayTitle('SYSTEMS AND METHODS FOR SEALING'), 'Systems and methods for sealing');
  assert.equal(displayTitle('Mixed Case Title'), 'Mixed Case Title');
  assert.equal(primarySection({ ipc3: ['H01', 'B60'] }), 'B');
  assert.equal(primarySection({ ipc3: [] }), '?');
});

test('field map groups only the other-fields lane, A–H, and keeps unclassified only when present', () => {
  const groups = fieldMap([
    { lane: 'own_field', ipc3: ['F16'] },
    { lane: 'other_fields', ipc3: ['A61'], family_id: 'a' },
    { lane: 'other_fields', ipc3: ['H01', 'A47'], family_id: 'b' },
    { lane: 'other_fields', ipc3: ['G01'], family_id: 'c' },
  ]);
  assert.deepEqual(groups.map((g) => g.section), ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']);
  assert.deepEqual(groups.find((g) => g.section === 'A').items.map((c) => c.family_id), ['a', 'b']);
  assert.equal(groups.find((g) => g.section === 'F').items.length, 0);
  assert.equal(fieldMap([{ lane: 'other_fields', ipc3: [] }]).at(-1).section, '?');
});

test('quote segments mark exact server offsets, merge overlaps and ignore bad ranges', () => {
  const text = 'abcdefghij';
  assert.deepEqual(quoteSegments(text, [{ start: 2, end: 4 }, { start: 3, end: 6 }, { start: 8, end: 99 }, { start: null, end: 1 }]), [
    { text: 'ab', mark: false }, { text: 'cdef', mark: true, quotes: [0, 1] }, { text: 'ghij', mark: false },
  ]);
  assert.deepEqual(quoteSegments(text, []), [{ text, mark: false }]);
});

test('formatting and stable request keys', async () => {
  assert.equal(formatMs(512.4), '512 ms');
  assert.equal(formatMs(1530), '1.5 s');
  const brief = { text: 'x y z w', own_ipc3: ['F16'] };
  const a = await requestKey(brief, { n_own: 10, n_other: 10 });
  assert.equal(a, await requestKey(brief, { n_own: 10, n_other: 10 }));
  assert.notEqual(a, await requestKey(brief, { n_own: 5, n_other: 15 }));
  assert.match(a, /^scout-[0-9a-f]{24}$/);
});

test('scout adapter is loopback-only and sends the idempotency header', async () => {
  assert.throws(() => createScoutAdapter('http://example.com:8787'), /loopback/);
  const calls = [];
  const fakeFetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return { ok: true, status: 200, headers: { get: () => 'application/json' }, json: async () => ({ ok: true }) };
  };
  const scout = createScoutAdapter('http://127.0.0.1:8787', fakeFetch);
  await scout.info();
  await scout.create({ text: 't' }, { n_own: 1, n_other: 1 }, 'k-1');
  await scout.rationale('abc', 'US 1/2');
  assert.equal(calls[0].url, 'http://127.0.0.1:8787/scout/info');
  assert.equal(calls[1].init.method, 'POST');
  assert.equal(calls[1].init.headers['Idempotency-Key'], 'k-1');
  assert.equal(calls[2].url, 'http://127.0.0.1:8787/scout-sessions/abc/rationales/US%201%2F2');
});

test('scout dossier keeps facts, inference and unresolved apart; unjudged is not negative', async () => {
  const { scoutDossier, scoutDossierMarkdown } = await import('../../app/src/scout/model.js');
  const session = {
    session_id: 'abcdef1234567890', brief: { text: 'SYNTHETIC brief', own_ipc3: ['F16'] }, split: { n_own: 1, n_other: 1 },
    receipt: { mode: 'live', encode_ms: 900, search_ms: 140, corpus_bundle_sha256: 'c'.repeat(64), encoder: 'datalyes/patembed-large', paid_calls: 0 },
    candidates: [
      { lane: 'own_field', rank_in_lane: 1, family_id: 'US1', representative_canonical: 'US1', score: 0.81, ipc3: ['F16'], title: 'Seal | gasket' },
      { lane: 'other_fields', rank_in_lane: 1, family_id: 'US2', representative_canonical: 'US2', score: 0.74, ipc3: ['A61'], title: 'Stent' },
    ],
  };
  const rationales = { US2: {
    family_id: 'US2', basis: 'system_inference', model: 'Qwen/Qwen3-8B', model_revision: 'b968826d9c46', prompt_version: 'v0',
    what_it_does: 'Holds force.', transferable_mechanism: 'Shape recovery.', quote_status: 'some_unmatched', decision: 'accepted',
    quotes: [{ quote: 'a b c d e', status: 'matched', start: 0, end: 9 }, { quote: 'x y z w v', status: 'not_found' }], source_sha256: 's'.repeat(64),
  } };
  const d = scoutDossier(session, rationales, { source: 'HUPD', corpus_licence: 'CC BY-SA 4.0', encoder: { licence: 'CC BY-NC-SA 4.0' } }, 'now');
  assert.equal(d.source_facts.length, 2);
  assert.equal(d.system_inference[0].basis, 'system_inference');
  assert.deepEqual(d.unresolved, [{ family_id: 'US1', status: 'not_judged' }]);
  assert.equal(d.receipt.paid_calls, 0);
  const md = scoutDossierMarkdown(d);
  assert.match(md, /## System inference \(not source facts\)/);
  assert.match(md, /Seal \\\| gasket/);
  assert.match(md, /\[not_found\] "x y z w v"/);
  assert.match(md, /1 candidates are not judged \(not negatives\)/);
  assert.match(md, /CC BY-NC-SA 4\.0/);
});

test('scout page is served from the app allowlist with only its module script', () => {
  assert.ok(resolvePath('/scout.html').endsWith('scout.html'));
  assert.ok(resolvePath('/src/scout/main.js').endsWith('main.js'));
  const html = readFileSync(resolve(APP, 'scout.html'), 'utf8');
  assert.ok(!/<script(?![^>]*src="src\/scout\/main\.js")/.test(html), 'inline script in scout.html');
  assert.ok(!/style="/.test(html), 'inline style attribute in scout.html');
  const js = readFileSync(resolve(APP, 'src/scout/main.js'), 'utf8');
  assert.ok(!/style:\s*[`'"]/.test(js), 'inline style attribute in scout UI (CSP forbids it)');
});
