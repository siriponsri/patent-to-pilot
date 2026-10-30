import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateDossier, schemaErrors, canonicalPatentId } from '../../app/src/core/validate.js';
import { PyNum, canonicalDumps } from '../../app/src/core/pyjson.js';
import { SCHEMAS, fixtureDossier, mutated, FIXTURES } from './helpers.mjs';

test('authored positive dossiers are accepted with reproducible badges', async () => {
  for (const key of ['synthetic_dossier', 'empty_corpus_dossier']) {
    const v = await validateDossier(fixtureDossier(key), SCHEMAS.dossier);
    assert.equal(v.ok, true, JSON.stringify(v.errors));
    assert.equal(v.mode, 'synthetic_demo');
  }
});

// Mirrors docs/healthtech/ux/validate_docs.py negatives plus FX-06 and import-safety cases.
const NEGATIVES = {
  payload_hash_mismatch: [(d) => { d.sources[0].payload = { device_name: 'changed' }; }, 'source_hash_mismatch'],
  locator_mismatch: [(d) => { d.evidence[2].locator = 'chars:0:1'; }, 'span_mismatch'],
  source_revision_mismatch: [(d) => { d.evidence[0].source_version = 'wrong-revision'; }, 'source_revision_mismatch'],
  dangling_evidence_source: [(d) => { d.evidence[0].source_id = 'missing'; }, 'dangling_source'],
  missing_disclosure: [(d) => { d.candidates[1].disclosure_evidence_id = null; }, 'missing_disclosure'],
  raw_canonical_mismatch: [(d) => { d.candidates[0].patent_id_canonical = 'US99000001B2'; }, 'raw_canonical_mismatch'],
  synthetic_presented_as_public: [(d) => { d.query.brief.data_class = 'public'; }, 'synthetic_in_public'],
  source_after_cutoff: [(d) => { d.query.evidence_cutoff = '2026-10-26'; }, 'late_source'],
  candidate_revision_mismatch: [(d) => { d.candidates[0].source_revision = 'wrong'; }, 'candidate_revision_mismatch'],
  unsourced_family: [(d) => { d.candidates[0].family_id = 'invented-family'; }, 'unsourced_family'],
  fx06_missing_comparator_source: [(d) => { d.sources.splice(0, 1); }, 'dangling_source'],
  private_data_class: [(d) => { d.query.brief.data_class = 'private'; }, 'private_data'],
  unsupported_extra_field: [(d) => { d.gold_labels = { forbidden: 'evaluator data' }; }, 'schema'],
  wrong_type_version: [(d) => { d.version = '1'; }, 'schema'],
  bad_hash_pattern: [(d) => { d.evidence[0].payload_hash = 'XYZ'; }, 'schema'],
  disclosure_from_candidate_document: [(d) => { d.evidence[1].source_id = 'ux-synthetic-patent-b'; }, 'hash_mismatch'],
  promoted_inference: [(d) => { Object.assign(d.evidence[0], { evidence_kind: 'system_inference' }); }, 'evidence_basis'],
  structured_value_type_changed: [(d) => { d.evidence[0].structured_value = ['SYNTHETIC demonstration comparator']; }, 'field_mismatch'],
  recorded_badge_not_reproducible: [(d) => { d.evidence[0].verification_status = 'not_checked'; }, 'badge_not_reproducible'],
};

for (const [name, [mutate, code]] of Object.entries(NEGATIVES)) {
  test(`negative import rejected: ${name} → ${code}`, async () => {
    const before = canonicalDumps(fixtureDossier());
    const v = await validateDossier(mutated(mutate), SCHEMAS.dossier);
    assert.equal(v.ok, false);
    assert.ok(v.errors.some((e) => e.code === code), `expected ${code}, got ${v.errors.map((e) => e.code).join(',')}`);
    assert.equal(canonicalDumps(fixtureDossier()), before, 'original fixture must stay unchanged');
  });
}

test('canonical patent ID keeps jurisdiction/kind, fails closed on unknown syntax', () => {
  assert.equal(canonicalPatentId('US 99000002 B2'), 'US99000002B2');
  assert.equal(canonicalPatentId('ep-1.234.567 a1'), 'EP1234567A1');
  assert.equal(canonicalPatentId('not a patent'), null);
});

test('schema subset: integer accepts 1 and 1.0, rejects "1"; closed objects reject extras', () => {
  const s = { type: 'object', additionalProperties: false, properties: { n: { type: 'integer', minimum: 1 } }, required: ['n'] };
  assert.deepEqual(schemaErrors(s, { n: new PyNum('1') }), []);
  assert.deepEqual(schemaErrors(s, { n: new PyNum('1.0') }), []);
  assert.equal(schemaErrors(s, { n: '1' }).length, 1);
  assert.equal(schemaErrors(s, { n: new PyNum('0') }).length, 1);
  assert.equal(schemaErrors(s, { n: new PyNum('2'), x: 1 }).length, 1);
  assert.equal(schemaErrors(s, {}).length, 1);
});

test('fixture capabilities are authored scenario data, not this app\'s capabilities', () => {
  // ui-fixtures.json says localDrafts=false/editedMarkdown=false for the *fixture adapter*; the app
  // derives its own manifest in adapters.js and must not copy these booleans.
  assert.equal(FIXTURES.capabilities.adapterId, 'authored-fixture-v1');
  assert.equal(FIXTURES.capabilities.runStart, false);
});
