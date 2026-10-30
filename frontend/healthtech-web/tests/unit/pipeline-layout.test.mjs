import { test } from 'node:test';
import assert from 'node:assert/strict';
import { NODES, EDGES, STAGE_TO_NODE, initialStates, nodeForView, stateForStageEvent } from '../../app/src/core/pipeline.js';
import { DOSSIER_STAGES, runDossierStages, validateDossier } from '../../app/src/core/validate.js';
import { defaultLayout, movePanel, resizeZone, normalizeLayout, locate, setFloatRect, PANELS } from '../../app/src/core/layout.js';
import { SCHEMAS, fixtureDossier, mutated } from './helpers.mjs';

test('graph: unique nodes, valid edges, every validation stage drives a node', () => {
  const ids = NODES.map((n) => n.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const [a, b] of EDGES) assert.ok(ids.includes(a) && ids.includes(b), `${a}->${b}`);
  for (const s of DOSSIER_STAGES) assert.ok(STAGE_TO_NODE[s.id], `stage ${s.id} has no node`);
  assert.equal(initialStates().agent, 'unavailable', 'agent node is never shown as available');
  assert.equal(nodeForView('source'), 'evidence');
  assert.equal(nodeForView('evidence', 'candidates'), 'candidates');
});

test('stage events are real: order, per-stage errors and totals equal validateDossier', async () => {
  for (const [name, mutate] of [['positive', () => {}], ['bad locator', (d) => { d.evidence[2].locator = 'chars:0:1'; }], ['missing disclosure', (d) => { d.candidates[1].disclosure_evidence_id = null; }]]) {
    const events = [];
    const staged = await runDossierStages(mutated(mutate), SCHEMAS.dossier, { onStage: (e) => events.push(e) });
    const whole = await validateDossier(mutated(mutate), SCHEMAS.dossier);
    assert.deepEqual(staged.errors, whole.errors, name);
    const ends = events.filter((e) => e.phase === 'end');
    assert.deepEqual(ends.map((e) => e.stage), DOSSIER_STAGES.map((s) => s.id), name);
    assert.equal(ends.reduce((n, e) => n + e.errors.length, 0), whole.errors.length, name);
    assert.ok(ends.every((e) => typeof e.ms === 'number' && e.ms >= 0));
  }
  const events = [];
  await runDossierStages(mutated((d) => { d.evidence[2].locator = 'chars:0:1'; }), SCHEMAS.dossier, { onStage: (e) => events.push(e) });
  const ev = events.find((e) => e.stage === 'evidence' && e.phase === 'end');
  assert.deepEqual(ev.items.map((i) => i.ok), [true, true, false], 'the failing evidence item is the one that was patched');
  assert.equal(stateForStageEvent(ev), 'fail');
});

test('schema failure stops later stages and marks them skipped', async () => {
  const events = [];
  const r = await runDossierStages(mutated((d) => { d.version = 'x'; }), SCHEMAS.dossier, { onStage: (e) => events.push(e) });
  assert.equal(r.ok, false);
  assert.deepEqual(events.filter((e) => e.phase === 'skipped').map((e) => e.stage), ['query', 'sources', 'evidence', 'candidates']);
  assert.ok(fixtureDossier());
});

test('layout: move, resize clamp, float, and every panel always placed once', () => {
  let l = defaultLayout();
  l = movePanel(l, 'timeline', 'right');
  assert.deepEqual(l.zones.right.panels, ['inspector', 'timeline']);
  assert.equal(l.zones.right.active, 'timeline');
  l = movePanel(l, 'library', 'float', { x: -50, y: 10, w: 100, h: 50 });
  assert.equal(locate(l, 'library'), 'float');
  assert.deepEqual(l.floating.library, { x: 0, y: 10, w: 260, h: 160 }, 'clamped to minimum size and on-screen');
  l = setFloatRect(l, 'library', { x: 5000, y: 5000, w: 300, h: 200 }, { w: 1280, h: 800 });
  assert.deepEqual(l.floating.library, { x: 1160, y: 752, w: 300, h: 200 });
  assert.equal(resizeZone(l, 'left', 10).zones.left.size, 200);
  assert.equal(resizeZone(l, 'left', 9999).zones.left.size, 640);
  const placed = PANELS.map((p) => locate(l, p));
  assert.ok(placed.every(Boolean));
});

test('layout: corrupted or partial stored layouts fall back safely', () => {
  assert.deepEqual(normalizeLayout(null), defaultLayout());
  assert.deepEqual(normalizeLayout({ version: 2 }), defaultLayout());
  const partial = normalizeLayout({ version: 1, zones: { left: { panels: ['library', 'library', 'nope'] }, right: { panels: [] }, bottom: { panels: [] } } });
  assert.deepEqual(PANELS.map((p) => locate(partial, p)).sort(), ['bottom', 'left', 'right'], 'duplicates/unknowns removed, missing panels restored');
});
