import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { summarizeRun, costView, candidateScope, EMPTY_CORPUS_HASH } from '../../app/src/core/run.js';
import { draftToQuery, listErrors, emptyDraft } from '../../app/src/core/brief.js';
import { schemaErrors, validateDossier, validateRunArtifacts } from '../../app/src/core/validate.js';
import { parseLossless, toPlain } from '../../app/src/core/pyjson.js';
import { FIXTURES, SCHEMAS, read } from './helpers.mjs';

const dossier = FIXTURES.synthetic_dossier;
const budget = (c, r) => ({ max_search_calls: c, max_returned_candidates: r, accounting: 'offline_counts' });
const ev = (step, action, calls, ids, stop = null) => ({ run_id: dossier.run_id, step_id: step, action_type: action, search_calls: calls, returned_candidates: ids.length, returned_candidate_ids: ids, new_candidate_count: ids.length, retry_count: 0, errors: [], stop_reason: stop, started_at: 't', remaining_budget_before: budget(3, 60), remaining_budget_after: budget(3, 60) });
const manifest = { run_id: dossier.run_id, policy_id: 'HT-B2', evidence_level: 'synthetic_engineering', actual_search_calls: 2, actual_returned_candidates: 3, completed_query_ids: ['q'], failed_query_ids: [], stop_reason: 'fixed_schedule_complete', paid_cost_usd: 0, provider_calls: 0, cost_accounting_version: 'ht-offline-v1', corpus_hash: 'a'.repeat(64), limitations: [] };

test('EMPTY_CORPUS_HASH is sha256 of canonical "[]"', () => {
  assert.equal(createHash('sha256').update('[]').digest('hex'), EMPTY_CORPUS_HASH);
});

test('run summary counters come from events and agree with manifest (2 calls, 3 occurrences, 2 unique)', () => {
  const events = [ev('s1', 'technical_search', 1, ['US99000001A1', 'US99000002B2']), ev('s2', 'feature_search', 1, ['US99000001A1']), ev('stop', 'stop', 0, [], 'fixed_schedule_complete')];
  const s = summarizeRun(dossier, manifest, events);
  assert.equal(s.callsUsed.value, 2);
  assert.equal(s.returnedOccurrences.value, 3);
  assert.equal(s.eventCandidateIds.value, 2);
  assert.equal(s.uniqueCandidates.value, 2);
  assert.equal(s.consistent, true);
  assert.equal(s.cost.actualUsd.value, 0);
  assert.match(s.cost.basis, /offline run, provider_calls=0/);
  const bad = summarizeRun(dossier, { ...manifest, actual_search_calls: 5 }, events);
  assert.equal(bad.consistent, false);
});

test('missing receipts and FX-11 billing stay unknown, never zero', () => {
  const none = summarizeRun(dossier, null, null);
  assert.equal(none.available, false);
  const c = costView(null);
  assert.equal(c.actualUsd.status, 'unknown');
  const fx11 = FIXTURES.scenarios.find((x) => x.id === 'FX-11').details.cost;
  const sim = costView(null, fx11);
  assert.deepEqual([sim.actualUsd.status, sim.simulated, sim.settlement], ['unknown', true, 'unknown_pending']);
});

test('candidate scope distinguishes empty corpus, no results and unknown', () => {
  const empty = FIXTURES.empty_corpus_dossier;
  assert.equal(candidateScope(empty, null), 'unknown');
  assert.equal(candidateScope(empty, { corpus_hash: EMPTY_CORPUS_HASH }), 'empty_corpus');
  assert.equal(candidateScope(empty, { corpus_hash: 'b'.repeat(64) }), 'no_results');
  assert.equal(candidateScope(dossier, null), 'has_candidates');
});

const comparator = { deviceId: 'UX-DEMO-001', sourceId: 'ux-synthetic-device', sourceDate: '2026-10-27', synthetic: true };

test('US-03: an idea-only draft cannot become a DeviceQuery', () => {
  const r = draftToQuery({ ...emptyDraft('2026-10-30'), objective: 'x' }, 'p1');
  assert.deepEqual([r.ok, r.code], [false, 'missing_comparator']);
});

test('US-04: blank lines rejected with line numbers; empty lists allowed; late source explained', () => {
  assert.deepEqual(listErrors('a\n\nb').blank, [2]);
  assert.deepEqual(listErrors('a\nb\n').blank, []);
  assert.deepEqual(listErrors('').items, []);
  const d = { ...emptyDraft('2026-10-30'), comparator, objective: 'Inspect', featuresText: 'a\n  \nb' };
  assert.equal(draftToQuery(d, 'p1').code, 'blank_item');
  assert.equal(draftToQuery({ ...d, featuresText: 'a', cutoff: '2026-10-01' }, 'p1').code, 'late_source');
});

test('a complete draft yields a query that passes the DeviceQuery JSON schema', () => {
  const d = { ...emptyDraft('2026-10-30'), comparator, objective: 'Inspect', featuresText: 'sensor', questionsText: 'Which source?', rawInput: 'ux demo' };
  const r = draftToQuery(d, 'proj-1');
  assert.equal(r.ok, true);
  assert.deepEqual(schemaErrors(JSON.parse(read('schemas/healthtech/DeviceQuery.schema.json')), r.value), []);
  assert.equal(r.value.device_id_raw, 'ux demo');
  assert.equal(r.value.brief.data_class, 'synthetic');
});

// Optional: a real public CLI run folder supplied read-only by the owner (not copied into the repo).
const PUBLIC_DIR = process.env.HEALTHTECH_PUBLIC_RUN_DIR || resolve(process.cwd(), '../../../../patent-to-pilot/results/healthtech/public-dossiers-20261027-r3/K190167');
test('imported public K190167 run: valid, zero candidates explained as empty corpus, receipts agree', { skip: !existsSync(resolve(PUBLIC_DIR, 'dossier.json')) && `NOT_AVAILABLE: ${PUBLIC_DIR}` }, async () => {
  const tree = parseLossless(readFileSync(resolve(PUBLIC_DIR, 'dossier.json'), 'utf8'));
  const v = await validateDossier(tree, SCHEMAS.dossier);
  assert.equal(v.ok, true, JSON.stringify(v.errors));
  assert.equal(v.mode, 'imported_public');
  const m = JSON.parse(readFileSync(resolve(PUBLIC_DIR, 'manifest.json'), 'utf8'));
  const events = readFileSync(resolve(PUBLIC_DIR, 'acquisition_events.jsonl'), 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l));
  const d = toPlain(tree);
  assert.deepEqual(validateRunArtifacts(d, m, events, SCHEMAS), []);
  assert.equal(d.candidates.length, 0);
  assert.equal(d.evidence.length, 7);
  assert.equal(candidateScope(d, m), 'empty_corpus');
  const s = summarizeRun(d, m, events);
  assert.equal(s.consistent, true);
  assert.equal(s.stopReason, 'fixed_schedule_complete');
});
