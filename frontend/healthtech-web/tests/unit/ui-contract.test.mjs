import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { DICT } from '../../app/src/core/i18n.js';
import { THEMES, THEME_KEYS, USED_PAIRS, contrast } from '../../app/src/core/tokens.js';
import { resolvePath, startServer } from '../../serve.mjs';
import { read, SCHEMAS } from './helpers.mjs';

const APP = resolve(dirname(fileURLToPath(import.meta.url)), '../../app');

test('TH and EN dictionaries have identical, non-empty key sets', () => {
  const en = Object.keys(DICT.en).sort(), th = Object.keys(DICT.th).sort();
  assert.deepEqual(th, en);
  for (const l of ['en', 'th']) for (const [k, v] of Object.entries(DICT[l])) assert.ok(v.trim(), `${l}.${k} empty`);
});

test('specified microcopy keys from 03_SCREENS_DESIGN.md are used verbatim', () => {
  const rows = read('docs/healthtech/ux/03_SCREENS_DESIGN.md').split('\n').filter((l) => /^\| [a-z]+\.[A-Za-z.]+ \|/.test(l));
  assert.ok(rows.length >= 35, `parsed ${rows.length} rows`);
  for (const row of rows) {
    const [key, en, th] = row.split('|').slice(1, 4).map((s) => s.trim());
    assert.equal(DICT.en[key], en, `en ${key}`);
    assert.equal(DICT.th[key], th, `th ${key}`);
  }
});

test('theme keys equal the ProjectBrief enum; every used colour pair meets WCAG minimum', () => {
  assert.deepEqual([...THEME_KEYS].sort(), [...SCHEMAS.dossier.$defs.ProjectBrief.properties.theme.enum].sort());
  for (const key of THEME_KEYS) for (const [fg, bg, min] of USED_PAIRS) {
    const r = contrast(THEMES[key][fg], THEMES[key][bg]);
    assert.ok(r >= min, `${key} ${fg}/${bg} = ${r.toFixed(2)} < ${min}`);
  }
});

function walk(dir) {
  return readdirSync(dir).flatMap((f) => (statSync(join(dir, f)).isDirectory() ? walk(join(dir, f)) : [join(dir, f)]));
}

test('static safety: no innerHTML/eval/remote URLs/telemetry in app source', () => {
  for (const file of walk(join(APP, 'src')).filter((f) => f.endsWith('.js'))) {
    const src = readFileSync(file, 'utf8');
    assert.ok(!/\.innerHTML\s*=|insertAdjacentHTML|outerHTML\s*=|document\.write|\beval\(|new Function\(/.test(src), `${file}: unsafe DOM/eval`);
    assert.ok(!/https?:\/\/(?!127\.0\.0\.1)/.test(src.replace(/\/\/.*$/gm, '')), `${file}: remote URL`);
    assert.ok(!/sendBeacon|XMLHttpRequest|WebSocket/.test(src), `${file}: network/telemetry API`);
    if (!file.endsWith('adapters.js')) assert.ok(!/\bfetch\(/.test(src), `${file}: fetch outside adapters`);
  }
  const html = readFileSync(join(APP, 'index.html'), 'utf8');
  assert.ok(!/<script(?![^>]*src="src\/main\.js")/.test(html), 'inline script in index.html');
});

test('implementation docs: every relative Markdown link resolves', () => {
  const docs = [resolve(APP, '../README.md'), resolve(APP, '../../../docs/healthtech/ux/implementation/README.md')];
  for (const doc of docs) {
    const text = readFileSync(doc, 'utf8');
    for (const [, target] of text.matchAll(/\]\(([^)\s]+)\)/g)) {
      if (/^(https?:|#)/.test(target)) continue;
      const path = resolve(dirname(doc), decodeURIComponent(target.split('#')[0]));
      assert.ok(statSync(path, { throwIfNoEntry: false }), `${doc}: broken link ${target}`);
    }
  }
});

test('server allowlist: no traversal, no non-app files, mapped authored files only', () => {
  assert.equal(resolvePath('/../../.env'), null);
  assert.equal(resolvePath('/%2e%2e/%2e%2e/GOAL.md'), null);
  assert.equal(resolvePath('/src/../../serve.mjs'), null);
  assert.equal(resolvePath('/README.md'), null);
  assert.ok(resolvePath('/fixtures/ui-fixtures.json').endsWith(join('ux', 'fixtures', 'ui-fixtures.json')));
  assert.ok(resolvePath('/src/main.js').endsWith(join('src', 'main.js')));
});

test('server sends CSP/no-store headers and binds to loopback', async () => {
  const server = await startServer(0);
  try {
    const { address, port } = server.address();
    assert.equal(address, '127.0.0.1');
    const res = await fetch(`http://127.0.0.1:${port}/`);
    assert.equal(res.status, 200);
    assert.match(res.headers.get('content-security-policy'), /connect-src 'self'/);
    assert.match(res.headers.get('content-security-policy'), /http:\/\/127\.0\.0\.1:\*/);
    assert.match(res.headers.get('content-security-policy'), /script-src 'self'/);
    assert.equal((await fetch(`http://127.0.0.1:${port}/../GOAL.md`)).status, 404);
    // Byte ranges (video chapter seeking): exact slice, correct headers, 416 past the end.
    const full = await (await fetch(`http://127.0.0.1:${port}/styles.css`)).text();
    const part = await fetch(`http://127.0.0.1:${port}/styles.css`, { headers: { Range: 'bytes=0-9' } });
    assert.equal(part.status, 206);
    assert.equal(part.headers.get('content-range'), `bytes 0-9/${Buffer.byteLength(full)}`);
    assert.equal(await part.text(), full.slice(0, 10));
    assert.equal((await fetch(`http://127.0.0.1:${port}/styles.css`, { headers: { Range: 'bytes=99999999-' } })).status, 416);
  } finally { server.close(); }
});
