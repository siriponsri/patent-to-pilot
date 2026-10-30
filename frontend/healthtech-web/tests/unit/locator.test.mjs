import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sliceCodePoints, parseLocator, resolveField } from '../../app/src/core/locator.js';
import { checkEvidence } from '../../app/src/core/validate.js';
import { parseLossless, contentHash } from '../../app/src/core/pyjson.js';
import { fixtureDossier } from './helpers.mjs';

const TEXT = 'ก🙂 ทดลองอ้างอิงภาษาไทย';

test('Thai/emoji spans use Python code points, not UTF-16 units', () => {
  const cut = sliceCodePoints(TEXT, 1, 2);
  assert.equal(cut.span, '🙂');
  assert.equal(cut.before, 'ก');
  assert.notEqual(TEXT.slice(1, 2), '🙂', 'UTF-16 slicing would split the surrogate pair');
  assert.equal(sliceCodePoints(TEXT, 3, 8).span, 'ทดลอง');
  assert.equal(cut.length, 22);
  assert.equal(sliceCodePoints(TEXT, 1000, 2000), null);
  assert.equal(sliceCodePoints(TEXT, 2, 2), null, 'empty range is invalid (start < end)');
});

test('locator parsing', () => {
  assert.deepEqual(parseLocator('chars:1:2'), { kind: 'chars', start: 1, end: 2, raw: 'chars:1:2' });
  assert.equal(parseLocator('chars:a:b').kind, 'invalid');
  assert.deepEqual(parseLocator('field:a.b').path, ['a', 'b']);
  assert.equal(resolveField({ a: { b: 2 } }, ['a', 'b']).value, 2);
  assert.equal(resolveField({ a: [1] }, ['a', '0']).found, false, 'list index is not a field (Python TypeError)');
});

async function srcFor(payloadText) {
  const payload = parseLossless(payloadText);
  return { source: { source_id: 's', version_label: 'r1', sha256: await contentHash(payload) }, payload, jurisdiction: 'US', source_date: '2026-01-01' };
}
const base = (src, over) => ({ source_id: 's', source_version: 'r1', payload_hash: src.source.sha256, jurisdiction: 'US', source_date: '2026-01-01', evidence_kind: 'source_fact', ...over });

test('emoji span evidence from the fixture checks; FX-12 bad locator cannot earn matched status', async () => {
  const d = fixtureDossier();
  const src = d.sources.find((s) => s.source.source_id === 'ux-synthetic-unicode');
  const ev = d.evidence.find((e) => e.evidence_id === 'ux-e-unicode');
  const okRes = await checkEvidence(ev, src);
  assert.equal(okRes.ok, true);
  assert.equal(okRes.status, 'exact_span_checked');
  const bad = await checkEvidence({ ...ev, locator: 'chars:1000:2000' }, src);
  assert.deepEqual([bad.ok, bad.code], [false, 'span_mismatch']);
  const shifted = await checkEvidence({ ...ev, locator: 'chars:2:3' }, src);
  assert.equal(shifted.ok, false, 'UTF-16-style offset must not match');
});

test('typed field check: 1.0 vs 1 differ exactly as in Python content_hash', async () => {
  const src = await srcFor('{"m":{"x":1.0}}');
  const item = (value) => base(src, { locator: 'field:m.x', structured_field: 'm.x', structured_value: value, extraction_method: 'structured_field' });
  assert.equal((await checkEvidence(item(parseLossless('1.0')), src)).ok, true);
  assert.equal((await checkEvidence(item(parseLossless('1')), src)).code, 'field_mismatch');
  assert.equal((await checkEvidence(item('1.0'), src)).code, 'field_mismatch');
  assert.equal((await checkEvidence({ ...item(1), locator: 'field:m.y', structured_field: 'm.y' }, src)).code, 'field_missing');
  assert.equal((await checkEvidence({ ...item(1), locator: 'field:other' }, src)).code, 'locator_invalid');
});

test('hash mismatch withholds the badge', async () => {
  const src = await srcFor('"abc"');
  const r = await checkEvidence(base(src, { payload_hash: '0'.repeat(64), locator: 'chars:0:1', quoted_span: 'a', extraction_method: 'literal_span' }), src);
  assert.equal(r.code, 'hash_mismatch');
});
