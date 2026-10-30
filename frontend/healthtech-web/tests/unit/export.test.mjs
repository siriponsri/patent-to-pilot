import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderMarkdown, buildRecovery, parseRecovery, mdText, MARKDOWN_EXPORTER } from '../../app/src/core/export.js';
import { toPlain, contentHash, parseLossless, stringifyLossless } from '../../app/src/core/pyjson.js';
import { cloneOverlay } from '../../app/src/core/overlay.js';
import { SCHEMAS, FIXTURES, fixtureDossier } from './helpers.mjs';

const TH_NOTE = 'หมายเหตุผู้ใช้: ต้องขอเอกสารเปิดเผยที่ลงวันที่จริง';
const EN_NOTE = 'User note: need a dated real disclosure';
const EVIL = '<script>alert(1)</script> [click](javascript:alert(1)) ![img](http://example.invalid/x.png) =HYPERLINK("http://x") | pipe';

async function ctx({ notes = [TH_NOTE, EN_NOTE], key = 'synthetic_dossier', candidateScope = 'has_candidates' } = {}) {
  const tree = fixtureDossier(key);
  const overlay = cloneOverlay(FIXTURES.overlay);
  notes.forEach((text, i) => overlay.notes.push({ noteId: `note-test-${i}`, targetRef: 'ux-e-unicode', baseDossierVersion: 1, text, basis: 'user_note', reviewMarker: 'needs_clarification' }));
  return {
    projectId: 'proj-test', title: 't', storageScope: 'indexeddb', mode: 'synthetic_demo', dossierTree: tree, dossier: toPlain(tree),
    dossierHash: await contentHash(tree), candidateScope, overlay,
    snapshot: { snapshotId: 'snap-test-2', parentSnapshotId: 'snap-test-1', savedAt: '2026-10-30T00:00:00Z', acknowledged: true }, lineage: ['snap-test-2', 'snap-test-1'],
  };
}

for (const lang of ['th', 'en']) {
  test(`edited Markdown (${lang}) keeps both user notes, IDs, quotes, unknowns and mode`, async () => {
    const c = await ctx();
    const md = renderMarkdown(c, lang);
    for (const s of [TH_NOTE, EN_NOTE, 'ux-e-unicode', 'chars:1:2', '🙂', 'US 99000001 A1', 'US99000002B2', 'disclosed_link', 'retrieved_candidate', 'snap-test-2',
      'SYNTHETIC example only; real evidence and coverage are unknown.', 'What dated source supports this association?', MARKDOWN_EXPORTER.id,
      'ข้อความทดสอบการส่งออก / User note must survive export', c.dossierHash, 'ยังต้องขอหลักฐานเพิ่มเติม / Request more evidence']) {
      assert.ok(md.includes(s), `${lang} markdown missing ${s}`);
    }
    assert.ok(md.includes(lang === 'th' ? 'ตัวอย่างข้อมูลสมมติสำหรับตรวจการทำงานของระบบ' : 'Synthetic engineering example'));
    assert.ok(md.includes(lang === 'th' ? 'บันทึกของผู้ใช้' : 'User notes (user-authored'));
  });
}

test('note HTML/links/images are inert in Markdown', async () => {
  const md = renderMarkdown(await ctx({ notes: [EVIL] }), 'en');
  assert.ok(!md.includes('<script'), 'raw script tag');
  assert.ok(!/(^|[^\\])\]\(/.test(md), 'unescaped link syntax');
  assert.ok(md.includes('&lt;script&gt;alert(1)&lt;/script&gt;'));
  assert.ok(md.includes('!\\[img\\](http://example.invalid/x.png)'));
  assert.equal(mdText('a\\[b'), 'a\\\\\\[b');
});

test('empty candidate list never reads as "no patents exist"', async () => {
  const en = renderMarkdown(await ctx({ key: 'empty_corpus_dossier', candidateScope: 'empty_corpus' }), 'en');
  assert.ok(en.includes('This imported run included no patent corpus. Patent coverage is unknown.'));
  const unknownScope = renderMarkdown(await ctx({ key: 'empty_corpus_dossier', candidateScope: 'unknown' }), 'th');
  assert.ok(unknownScope.includes('ไม่ทราบว่ามีการค้นชุดข้อมูลสิทธิบัตรหรือไม่'));
});

test('recovery JSON round-trip is lossless: overlay, IDs, 1.0 scores and hash survive', async () => {
  const c = await ctx();
  const text = buildRecovery(c);
  assert.ok(text.includes('"authored_demo_rank": 1.0'), 'float lexeme preserved');
  const r = await parseRecovery(text, SCHEMAS);
  assert.equal(r.ok, true, JSON.stringify(r.errors));
  assert.deepEqual(r.overlay, c.overlay);
  assert.equal(r.validation.hash, c.dossierHash);
  assert.deepEqual(r.snapshot.lineage, ['snap-test-2', 'snap-test-1']);
  assert.ok(r.overlay.notes.some((n) => n.text === TH_NOTE) && r.overlay.notes.some((n) => n.text === EN_NOTE));
  // Re-exporting the reimport gives the same dossier bytes and the same Markdown notes.
  const again = buildRecovery({ ...c, dossierTree: r.dossierTree, overlay: r.overlay });
  assert.equal(stringifyLossless(parseLossless(again).dossier), stringifyLossless(parseLossless(text).dossier));
});

test('tampered recovery files are rejected', async () => {
  const c = await ctx();
  const env = () => parseLossless(buildRecovery(c));
  const cases = {
    hash_mismatch: (e) => { e.sourceDossierSha256 = '0'.repeat(64); },
    wrong_mode: (e) => { e.mode = 'imported_public'; },
    overlay_invalid: (e) => { e.overlay.notes[0].basis = 'source_fact'; },
    unsupported_version: (e) => { e.formatVersion = 2; },
    unsupported_field: (e) => { e.extra = true; },
    source_hash_mismatch: (e) => { e.dossier.sources[0].payload.device_name = 'tampered'; },
  };
  for (const [code, mutate] of Object.entries(cases)) {
    const e = env();
    mutate(e);
    const r = await parseRecovery(stringifyLossless(e), SCHEMAS);
    assert.equal(r.ok, false, code);
    assert.ok(r.errors.some((x) => x.code === code), `${code}: ${JSON.stringify(r.errors)}`);
  }
});
