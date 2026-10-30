import { test } from 'node:test';
import assert from 'node:assert/strict';
import { journeyState, JOURNEY } from '../../app/src/core/journey.js';
import { emptyOverlay } from '../../app/src/core/overlay.js';

const base = () => ({ dossier: {}, overlay: emptyOverlay(), pipe: { lastResult: null }, exportStarted: null });

test('fresh project: only "load" is done; next step after the current view is suggested', () => {
  const j = journeyState(base(), 'overview');
  assert.deepEqual(j.steps.map((s) => s.done), [true, false, false, false, false]);
  assert.equal(j.steps.find((s) => s.current).id, 'review');
  assert.equal(j.next.id, 'ask');
  assert.equal(j.progress, 0.2);
});

test('done comes from real state, not from visiting', () => {
  const c = base();
  c.pipe.lastResult = { ok: false, errors: 2 };
  c.overlay.notes.push({ noteId: 'n', targetRef: 'x', baseDossierVersion: 1, text: '   ', basis: 'user_note', reviewMarker: 'none' });
  let j = journeyState(c, 'checks');
  assert.equal(j.steps[1].done, false, 'failed checks are not done');
  assert.equal(j.steps[2].done, false, 'blank note is not done');
  c.pipe.lastResult = { ok: true, errors: 0 };
  c.overlay.notes[0].text = 'real note';
  c.overlay.requestDrafts.push({ requestId: 'r', question: 'Q?', evidenceRefs: [], priority: 'normal', status: 'draft' });
  c.exportStarted = 'file.md';
  j = journeyState(c, 'export');
  assert.equal(j.doneCount, JOURNEY.length);
  assert.equal(j.next, null);
});
