import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { parseLossless, canonicalDumps, pyFloatRepr, contentHash, stringifyLossless, codePointCompare } from '../../app/src/core/pyjson.js';
import { fixtureDossier } from './helpers.mjs';

test('Python float repr rules (hand-computed)', () => {
  const cases = [[1, '1.0'], [0.1, '0.1'], [100, '100.0'], [0.0001, '0.0001'], [0.00001, '1e-05'], [1e15, '1000000000000000.0'],
    [1e16, '1e+16'], [1.5e16, '1.5e+16'], [123.456, '123.456'], [-0, '-0.0'], [0, '0.0'], [1.5e300, '1.5e+300'], [-2.5e-7, '-2.5e-07']];
  for (const [x, want] of cases) assert.equal(pyFloatRepr(x), want, String(x));
  assert.throws(() => pyFloatRepr(Infinity));
});

test('number lexemes survive: 1.0 stays a float, -0 int becomes 0, big ints exact', () => {
  assert.equal(canonicalDumps(parseLossless('{"a":1.0,"b":1,"c":-0,"d":12345678901234567890}')), '{"a":1.0,"b":1,"c":0,"d":12345678901234567890}');
  assert.equal(stringifyLossless(parseLossless('[1.0, 2e3]'), 0), '[\n1.0,\n2e3\n]');
});

test('keys sort by code point like Python (not UTF-16)', () => {
  // U+FF61 < U+1F600 by code point, but '\uD83D' (first surrogate) < '｡' in UTF-16.
  assert.ok(codePointCompare('｡', '😀') < 0);
  assert.equal(canonicalDumps({ '😀': 1, '｡': 2, a: 3 }), '{"a":3,"｡":2,"😀":1}');
});

test('strings: non-ASCII raw, control chars escaped like ensure_ascii=False', () => {
  assert.equal(canonicalDumps('ก🙂\n\u0001"'), '"ก🙂\\n\\u0001\\""');
});

test('duplicate keys and trailing data are rejected', () => {
  assert.throws(() => parseLossless('{"a":1,"a":2}'), /duplicate key/);
  assert.throws(() => parseLossless('{"a":1} x'), /trailing/);
});

test('fixture source hashes and whole-dossier hash match the Python canonical hash', async () => {
  const d = fixtureDossier();
  for (const s of d.sources) assert.equal(await contentHash(s.payload), s.source.sha256, s.source.source_id);
  // Reference computed with Python: hashlib.sha256(json.dumps(bundle['synthetic_dossier'], ensure_ascii=False,
  // sort_keys=True, separators=(',', ':')).encode()).hexdigest()
  assert.equal(await contentHash(d), '287757968b8d3b879cb64ecd62ec5a9ed28fd2bbdb08d86905cc6aebdd375e50');
});

const py = spawnSync('python', ['-c', 'print(1)'], { encoding: 'utf8' });
test('live cross-check against Python json.dumps', { skip: py.status !== 0 && 'python not available' }, () => {
  const texts = ['{"z":1.0,"a":[1e-5,1e16,0.1,-0,123456789012345678901],"ｂ":"ก🙂","😀":null,"x":{"k":true}}', '[0.30000000000000004, 5e-324, 1.7976931348623157e308]'];
  for (const text of texts) {
    const r = spawnSync('python', ['-c', 'import sys,json;sys.stdout.buffer.write(json.dumps(json.loads(sys.stdin.buffer.read().decode()),ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode())'], { input: text, encoding: 'utf8' });
    assert.equal(r.status, 0, r.stderr);
    assert.equal(canonicalDumps(parseLossless(text)), r.stdout);
  }
});
