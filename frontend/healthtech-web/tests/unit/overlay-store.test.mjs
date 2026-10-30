import { test } from 'node:test';
import assert from 'node:assert/strict';
import { emptyOverlay, overlayDiff, reapply, overlayErrors, overlayTexts, cloneOverlay } from '../../app/src/core/overlay.js';
import { MemoryDraftStore, chainProblem, lineage } from '../../app/src/core/store.js';
import { FIXTURES } from './helpers.mjs';

const note = (id, text) => ({ noteId: id, targetRef: 'ux-e-device', baseDossierVersion: 1, text, basis: 'user_note', reviewMarker: 'none' });

test('fixture overlay is valid; malformed overlays are rejected', () => {
  assert.deepEqual(overlayErrors(FIXTURES.overlay), []);
  assert.ok(overlayErrors({ ...emptyOverlay(), notes: [{ ...note('n', 'x'), basis: 'source_fact' }] }).length);
  assert.ok(overlayErrors({ ...emptyOverlay(), extra: 1 }).length);
  assert.ok(overlayErrors({ ...emptyOverlay(), requestDrafts: [{ requestId: 'r', question: 'q', evidenceRefs: [], priority: 'urgent', status: 'draft' }] }).length);
});

test('FX-08: both tabs edit the same note from one base → reapply keeps BASE-derived theirs and yours', () => {
  const base = { ...emptyOverlay(), notes: [note('n1', 'BASE')] };
  const theirs = { ...emptyOverlay(), notes: [note('n1', 'EDIT_FROM_TAB_A')] };
  const yours = { ...emptyOverlay(), notes: [note('n1', 'EDIT_FROM_TAB_B')] };
  assert.deepEqual(overlayDiff(base, yours), ['note:n1']);
  const { overlay, bothChanged } = reapply(base, theirs, yours);
  const texts = overlayTexts(overlay);
  assert.ok(texts.includes('EDIT_FROM_TAB_A') && texts.includes('EDIT_FROM_TAB_B'), JSON.stringify(texts));
  assert.deepEqual(bothChanged, ['note:n1']);
  assert.deepEqual(overlayErrors(overlay), []);
});

test('reapply: independent edits merge; my deletion applies only where theirs did not change', () => {
  const base = { ...emptyOverlay(), notes: [note('n1', 'one'), note('n2', 'two')] };
  const theirs = { ...emptyOverlay(), notes: [note('n1', 'one'), note('n2', 'two'), note('n3', 'three')] };
  const yours = { ...emptyOverlay(), notes: [note('n2', 'two!')] };
  const { overlay } = reapply(base, theirs, yours);
  assert.deepEqual(overlay.notes.map((n) => `${n.noteId}:${n.text}`).sort(), ['n2:two!', 'n3:three']);
});

test('memory store: expected-parent CAS, no false dual success, idempotent op IDs', async () => {
  const s = new MemoryDraftStore();
  const created = await s.createProject({ projectId: 'p' }, { snapshotId: 's1', savedAt: '1', overlay: emptyOverlay() }, 'op-0');
  assert.ok(created.ok);
  const a = await s.commit('p', 's1', { snapshotId: 's2', savedAt: '2', overlay: { ...emptyOverlay(), notes: [note('n', 'A')] } }, 'op-a');
  const b = await s.commit('p', 's1', { snapshotId: 's3', savedAt: '3', overlay: { ...emptyOverlay(), notes: [note('n', 'B')] } }, 'op-b');
  assert.equal(a.ok, true);
  assert.deepEqual([b.ok, b.code, b.theirs.snapshotId], [false, 'conflict', 's2']);
  const again = await s.commit('p', 's1', { snapshotId: 's2-dup', savedAt: '4', overlay: emptyOverlay() }, 'op-a');
  assert.equal(again.value.duplicate, true);
  assert.equal(again.value.snapshot.snapshotId, 's2');
  const loaded = (await s.loadProject('p')).value;
  assert.equal(loaded.project.headSnapshotId, 's2');
  assert.equal(loaded.snapshots.length, 2);
  assert.equal(loaded.problem, null);
  assert.deepEqual(lineage(loaded.snapshots, 's2'), ['s2', 's1']);
});

test('FX-13 corrupt chains are detected, never repaired', () => {
  const p = { projectId: 'p', headSnapshotId: 's3' };
  const snap = (id, parent) => ({ snapshotId: id, projectId: 'p', parentSnapshotId: parent, overlay: emptyOverlay() });
  assert.match(chainProblem(p, [snap('s1', null), snap('s3', 's2')]), /missing parent s2/);
  assert.match(chainProblem(p, [snap('s1', null), snap('s3', null)]), /one root/);
  assert.match(chainProblem({ ...p, headSnapshotId: 'zz' }, [snap('s1', null)]), /head zz is missing/);
  assert.equal(chainProblem({ ...p, headSnapshotId: 's1' }, [snap('s1', null)]), null);
  const cloned = cloneOverlay(FIXTURES.overlay);
  assert.notEqual(cloned, FIXTURES.overlay);
});

test('delete targets only the selected local project', async () => {
  const s = new MemoryDraftStore();
  await s.createProject({ projectId: 'keep' }, { snapshotId: 'k1', savedAt: '1', overlay: emptyOverlay() }, 'op-k');
  await s.createProject({ projectId: 'drop' }, { snapshotId: 'd1', savedAt: '1', overlay: emptyOverlay() }, 'op-d');
  const r = await s.deleteProject('drop');
  assert.deepEqual(r.value, { snapshots: 1, ops: 1 });
  assert.deepEqual((await s.listProjects()).value.map((p) => p.projectId), ['keep']);
  assert.equal((await s.loadProject('keep')).ok, true);
});
