import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const root = new URL('../../', import.meta.url);
const out = new URL('./src/generated/', import.meta.url);
const base = '7cb1c92ea09ebe03d50aa11c09b6473e7b33001b';
export const freeze = '8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d';
const freezeTag = 'loe-track-a-freeze-20261127';
export const hash = text => createHash('sha256').update(text).digest('hex');
const encode = data => JSON.stringify(data);
const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;
const dayPattern = /^\d{4}-\d{2}-\d{2}$/;
const digestPattern = /^[0-9a-f]{64}$/;
const reviewedClaims = /^(?:queue(?:-12|-24)?|entry(?:-12|-24)?|approved-applicants|at-risk|piv-coverage|challenge-(?:\d+|unknown)|forms|ob-approval-\d+|protection-gaps|patent-\d+|exclusivity-\d+|family-\d+|th-(?:patent|fda)-status|thai-status|fto-scope|reproduce)$/;
const revealed = /outcome[_ -]?reveal|reveal[_ -]?only|retrospective[_ -]?outcome|supported[_ -]?event|false[_ -]?alarm|first_final_anda_date/i;
const omittedIds = /^(?:outcome|reveal|first-generic)(?:[-_]|$)/i;
const cleanText = value => typeof value === 'string' && value.length > 0 && !revealed.test(value);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function safeLink(value) {
  if (typeof value !== 'string' || revealed.test(value)) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password) return null;
    if (/(?:^|[?&#/])(?:reveal|outcome)(?:[=/&#]|$)/i.test(decodeURIComponent(url.pathname + url.search + url.hash))) return null;
    return value;
  } catch {
    return null;
  }
}

function sourceView(source, day, revealIds) {
  if (revealIds.has(source.id) || source.reveal_only === true || omittedIds.test(source.id) ||
      ![source.id, source.issuer, source.title, source.version, source.locator].every(cleanText) ||
      (source.public_date != null && (!dayPattern.test(source.public_date) || source.public_date > day)) ||
      (source.evidence_cutoff != null && (!dayPattern.test(source.evidence_cutoff) || source.evidence_cutoff > day))) return null;
  const url = safeLink(source.url);
  if (source.url && !url) return null;
  return {
    id: source.id, issuer: source.issuer, title: source.title, version: source.version,
    public_date: source.public_date ?? null, locator: source.locator, url,
    sha256: digestPattern.test(source.sha256 ?? '') ? source.sha256 : null,
    retrieved: source.retrieved ?? null, evidence_cutoff: source.evidence_cutoff ?? null,
  };
}

export function projectDossier(dossier, current) {
  const revealIds = new Set(dossier.outcome_reveal?.source_ids ?? []);
  const sources = Object.fromEntries(dossier.sources.flatMap(source => {
    const projected = sourceView(source, dossier.as_of, revealIds);
    return projected ? [[projected.id, projected]] : [];
  }));
  const validRefs = item => item.source_ids?.length > 0 &&
    item.source_ids.every(id => Object.hasOwn(sources, id));
  const visibleText = item => [item.text_th, item.text_en].every(cleanText);
  const claims = dossier.claims.filter(item => reviewedClaims.test(item.id) && !item.time_basis && item.reveal_only !== true &&
    validRefs(item) && visibleText(item)).map(item => ({
    id: item.id, section: item.section, th: item.text_th, en: item.text_en,
    state: item.state, kind: item.kind, source_ids: item.source_ids,
    jurisdiction: item.section === 'thai_asean' ? 'TH' : item.section === 'handoff' ? 'target_country' : 'US',
    time_basis: item.section === 'thai_asean' ? 'verification_required' : 'as_of',
    horizon: current ? Number(/^(?:queue|entry)-(12|24)$/.exec(item.id)?.[1]) || null : dossier.forecast.horizon_months,
  }));
  const checklist = dossier.checklist.filter(item => cleanText(item.id) && !omittedIds.test(item.id) &&
    item.reveal_only !== true && !item.time_basis &&
    (!item.lookup_url || safeLink(item.lookup_url)) && validRefs(item) && visibleText(item)).map(item => ({
    id: item.id, th: item.text_th, en: item.text_en, owner: item.owner, state: 'unknown',
    agency: cleanText(item.agency) ? item.agency : null, lookup_url: safeLink(item.lookup_url),
    source_ids: item.source_ids,
  }));
  const referenced = new Set([...claims, ...checklist].flatMap(item => item.source_ids));
  return { claims, checklist, sources: Object.fromEntries(Object.entries(sources).filter(([id]) => referenced.has(id))) };
}

export function projectQueue(queue) {
  return queue.ranked_rows.map(row => ({
    key: row.key, display_name: row.display_name, rank: row.m3_rank, score: row.m3_p,
    included: row.in_queue, inclusion_probability: row.queue_inclusion_probability ?? null,
  }));
}

function build() {
  const inputHashes = {};
  const read = path => {
    const text = readFileSync(new URL(path, root), 'utf8').replace(/\r\n/g, '\n');
    inputHashes[path] = hash(text);
    return text;
  };
  const readJson = path => JSON.parse(read(path));
  const freezeManifest = 'loe-bench/data/TRACKA_FREEZE_MANIFEST.json';
  read(freezeManifest);
  assert(inputHashes[freezeManifest] === freeze, 'Track A freeze digest differs');
  const endpoint = 'docs/loe-bench/ENDGAME-PLAN.md';
  const thai = read(endpoint).match(/the same text on screen and in the PDF:\*\* "([^"]+)"/)?.[1];
  assert(thai, 'Canonical Thai notice missing');

  const texts = Object.create(null);
  const add = (name, data) => {
    assert(!Object.hasOwn(texts, name), 'Duplicate shard');
    texts[name] = encode(data);
    return name;
  };
  const choices = [];
  let disclaimer;
  for (const current of [true, false]) {
    const dir = 'product/demo/data/' + (current ? 'current/' : '');
    const index = readJson(dir + 'index.json');
    const status = current ? 'TRACK_A_FROZEN' : 'DEVELOPMENT_ONLY';
    const verify = doc => !current || (doc.version?.freeze === 'verified' &&
      doc.version?.manifest_sha256 === freeze && doc.version?.tag === freezeTag);
    assert(index.schema === 'mwd.index.v1' && index.status === status && !index.fixture && verify(index), 'Release index differs');
    if (current) {
      disclaimer = index.disclaimer;
      assert(disclaimer.th === thai && cleanText(disclaimer.en), 'Release notice differs');
    }
    const dossiers = new Map();
    for (const entry of index.dossiers) {
      assert(/^dossier-[A-Z0-9-]+\.json$/i.test(entry.path), 'Invalid dossier path');
      const dossier = readJson(dir + entry.path);
      assert(dossier.schema_version === 'mwd.dossier.v1' && verify(dossier) &&
        dossier.molecule.key === entry.key && dossier.as_of === (entry.as_of ?? index.as_of) &&
        dossier.forecast.status === status && dossier.jurisdiction === 'US', 'Dossier identity differs');
      const shard = add(dir + entry.path, projectDossier(dossier, current));
      for (const horizon of entry.horizons ?? [entry.horizon_months]) {
        const key = encode([dossier.as_of, horizon, entry.key]);
        assert(!dossiers.has(key), 'Duplicate dossier identity');
        dossiers.set(key, shard);
      }
    }
    for (const entry of index.queues) {
      assert(/^queue-\d{4}-\d{2}-\d{2}-(12|24)m\.json$/.test(entry.path), 'Invalid queue path');
      const queue = readJson(dir + entry.path);
      const horizon = entry.horizon_months;
      const day = entry.as_of;
      assert(queue.schema_version === 'mwd.queue.v1' && queue.status === status && verify(queue) &&
        queue.as_of === day && queue.horizon_months === horizon && digestPattern.test(queue.score_export_sha256),
        'Queue identity differs');
      const rows = projectQueue(queue).map(row => ({
        ...row, dossier: dossiers.get(encode([day, horizon, row.key])) ?? null,
      }));
      const search_order = rows.map((_, i) => i).sort((a, b) =>
        compare(rows[a].display_name.toLowerCase(), rows[b].display_name.toLowerCase()) || compare(rows[a].key, rows[b].key));
      const mode = current ? 'track_a_t0' : 'development';
      choices.push({
        mode, as_of: day, horizon, status, jurisdiction: 'US',
        label: current ? 'Track A t0 forecast, outcome pending' : 'Development data',
        freeze_tag: current ? freezeTag : null, freeze_manifest_sha256: current ? freeze : null,
        queue: add(dir + entry.path, {
          rows, search_order, slots: queue.queue_size, version: queue.score_export_sha256, window_end: queue.window_end,
        }),
      });
    }
  }
  const methods = JSON.parse(read('product/mcp/method-card.json'));
  for (const row of methods) {
    const path = 'docs/loe-bench/receipts/' + row.receipt + '.md';
    read(path);
    row.evidence = {
      id: row.receipt, version: base, locator: row.locator,
      artifact_sha256: inputHashes[path],
      url: 'https://github.com/siriponsri/patent-to-pilot/blob/' + base + '/' + path + '#' + row.anchor,
    };
    delete row.receipt;
    delete row.locator;
    delete row.anchor;
  }
  add('method-card.json', methods);
  const inventory = Object.fromEntries(Object.entries(inputHashes).sort(([a], [b]) => compare(a, b)));
  const inventoryHash = hash(encode(inventory));
  const pin = JSON.parse(readFileSync(new URL('./release-lock.json', import.meta.url), 'utf8'));
  const manifest = encode({
    release_id: 'mwd-b5-20261128.1', upstream_commit: base, input_inventory_sha256: inventoryHash,
    freeze_manifest_sha256: freeze, choices, disclaimer,
    shards: Object.fromEntries(Object.entries(texts).map(([name, text]) => [name, hash(text)])),
  });
  const manifestHash = hash(manifest);
  if (process.argv.includes('--print-digests')) {
    console.log(JSON.stringify({ inputs_sha256: inventoryHash, manifest_sha256: manifestHash }, null, 2));
    return;
  }
  assert(pin.inputs_sha256 === inventoryHash && pin.manifest_sha256 === manifestHash, 'Release lock mismatch');
  mkdirSync(new URL('shards/', out), { recursive: true });
  for (const [name, text] of Object.entries(texts)) {
    const target = new URL('shards/' + name, out);
    mkdirSync(new URL('./', target), { recursive: true });
    writeFileSync(target, text);
  }
  writeFileSync(new URL('manifest.json', out), manifest);
  writeFileSync(new URL('pin.json', out), encode({ manifest_sha256: manifestHash, disclaimer }));
  writeFileSync(new URL('release.json', out), encode({ manifest, texts }));
  console.log(encode({ release_id: 'mwd-b5-20261128.1', manifest_sha256: manifestHash, shards: Object.keys(texts).length }));
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) build();
