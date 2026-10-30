import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { REPO, SCHEMAS } from './helpers.mjs';
import { parseLossless, toPlain } from '../../app/src/core/pyjson.js';
import { validateDossier, validateRunArtifacts } from '../../app/src/core/validate.js';
import { buildRecovery, parseRecovery, renderMarkdown } from '../../app/src/core/export.js';

const generated = parseLossless(execFileSync(process.env.PYTHON || 'python', [
  resolve(REPO, 'frontend/healthtech-web/tests/fixtures/backend_case.py'),
], { cwd: REPO, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 }));
const plain = toPlain(generated);

test('versioned schemas equal the current Python contracts, including rights and vectors', () => {
  assert.deepEqual(plain.schemas, SCHEMAS);
});

test('current backend run and selected edited version import, inspect, and round-trip', async () => {
  const v = await validateDossier(generated.dossier, SCHEMAS.dossier);
  assert.equal(v.ok, true, JSON.stringify(v.errors));
  assert.equal(v.hash, plain.hash, 'canonical hash agrees with Python');
  assert.equal(plain.dossier.version, 2);
  assert.deepEqual(validateRunArtifacts(plain.dossier, plain.manifest, plain.events, SCHEMAS), []);
  const ctx = { dossier: plain.dossier, dossierTree: generated.dossier, dossierHash: v.hash,
    mode: v.mode, projectId: 'backend-case', title: 'Backend contract', storageScope: 'memory',
    manifestTree: generated.manifest, eventTrees: generated.events,
    overlay: { notes: [], featureLinks: [], requestDrafts: [] }, candidateScope: 'has_candidates' };
  for (const lang of ['th', 'en']) {
    assert.ok(plain.exports[lang].includes(plain.dossier.user_edits.review_note));
    assert.ok(renderMarkdown(ctx, lang).includes(plain.dossier.user_edits.review_note));
  }
  const restored = await parseRecovery(buildRecovery(ctx), SCHEMAS);
  assert.equal(restored.ok, true, JSON.stringify(restored.errors));
  assert.equal(restored.validation.hash, v.hash);
});

test('import rejects cross-query, duplicate-event, and mixed-policy run receipts', () => {
  for (const [mutate, code] of [
    [(m, e) => { e[0].query_id = 'other-query'; }, 'query_mismatch'],
    [(m, e) => { m.expected_query_ids = ['other-query']; }, 'query_mismatch'],
    [(m, e) => { e.push(structuredClone(e[0])); }, 'duplicate_step'],
    [(m, e) => { e[0].policy_id = m.policy_id === 'HT-B2' ? 'HT-B0b' : 'HT-B2'; }, 'policy_mismatch'],
  ]) {
    const m = structuredClone(plain.manifest), e = structuredClone(plain.events);
    mutate(m, e);
    assert.ok(validateRunArtifacts(plain.dossier, m, e, SCHEMAS).some((x) => x.code === code), code);
  }
});
