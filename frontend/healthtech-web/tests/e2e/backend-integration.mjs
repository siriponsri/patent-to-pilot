// Actual current-backend artifacts -> real browser -> IndexedDB -> edited export.
// HEALTHTECH_BACKEND_CASES points to private output from prepare_ui_integration.py.
// Keep raw downloads private; this script prints only sanitized per-case outcomes.
import assert from 'node:assert/strict';
import { mkdtempSync, readdirSync, existsSync, readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { launch, waitForDownload } from './cdp.mjs';
import { startServer } from '../../serve.mjs';

if (!process.env.HEALTHTECH_BACKEND_CASES) throw new Error('Set HEALTHTECH_BACKEND_CASES to prepared backend outputs');
const input = resolve(process.env.HEALTHTECH_BACKEND_CASES);
const work = mkdtempSync(join(tmpdir(), 'healthtech-backend-browser-'));
const dl = join(work, 'downloads');
mkdirSync(dl);
const cases = readdirSync(input).filter((name) => existsSync(join(input, name, 'dossier.json')));
assert.ok(cases.length, 'no backend cases');
const server = await startServer(0);
let browser;
const results = [];
try {
  browser = await launch(join(work, 'profile'));
  await browser.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dl, eventsEnabled: true });
  const page = await browser.newPage(`http://127.0.0.1:${server.address().port}/`);
  for (const name of cases) {
    const path = join(input, name);
    const original = JSON.parse(readFileSync(join(path, 'dossier.json'), 'utf8'));
    await page.hash('#/import');
    await page.setFiles('#import-file', ['dossier.json', 'manifest.json', 'acquisition_events.jsonl'].map((f) => join(path, f)));
    await page.waitFor('document.getElementById("import-result")?.dataset.result');
    const verdict = await page.eval('({ok:window.__healthtechApp.state.importPreview.ok, errors:window.__healthtechApp.state.importPreview.errors.map(e=>e.code)})');
    assert.ok(verdict.ok, `${name}: ${verdict.errors.join(',')}`);
    await page.click('#import-accept');
    await page.waitFor(`window.__healthtechApp.state.current?.dossier?.query.query_id === ${JSON.stringify(original.query.query_id)}`);
    const pid = await page.eval('window.__healthtechApp.state.current.project.projectId');
    await page.waitFor('!window.__healthtechApp.state.current?.pipe?.running');
    const imported = await page.eval('({mode:window.__healthtechApp.state.current.mode, version:window.__healthtechApp.state.current.dossier.version, candidates:window.__healthtechApp.state.current.dossier.candidates.length})');
    assert.equal(imported.mode, 'imported_public');
    assert.equal(imported.version, 2);
    assert.equal(imported.candidates, original.candidates.length);
    const evidence = original.evidence[0];
    await page.hash(`#/project/${pid}/source/${encodeURIComponent(evidence.source_id)}?evidenceId=${encodeURIComponent(evidence.evidence_id)}`);
    await page.waitFor('document.getElementById("source-field") || document.getElementById("source-span")');
    assert.equal(await page.eval('Boolean(document.getElementById("source-mismatch"))'), false);
    await page.hash(`#/project/${pid}/runs`);
    assert.equal(await page.eval('document.getElementById("run-consistency").dataset.consistent'), 'true');
    await page.hash(`#/project/${pid}`);
    await page.click('#add-note-dossier');
    await page.waitFor('document.activeElement?.tagName === "TEXTAREA"');
    const note = `UI integration ${name}: ขอหลักฐานเพิ่ม / request source evidence`;
    await page.type('textarea:focus', note);
    await page.waitFor('document.getElementById("save-status")?.dataset.state === "saved"');
    await page.goto(`http://127.0.0.1:${server.address().port}/#/project/${pid}`);
    assert.equal(await page.eval('window.__healthtechApp.state.current.dossier.query.query_id'), original.query.query_id);
    assert.ok(await page.eval(`JSON.stringify(window.__healthtechApp.state.current.overlay).includes(${JSON.stringify(note)})`), 'IndexedDB reopen retained note');
    await page.hash(`#/project/${pid}/export`);
    for (const lang of ['th', 'en']) {
      await page.click(`#export-lang-${lang}`);
      await page.click('#export-format-md');
      await page.click('#export-download');
      const fileId = original.query.device_id_canonical.replace(/[^A-Za-z0-9_-]/g, '_');
      const f = await waitForDownload(dl, `${fileId}-${lang}.md`);
      const md = readFileSync(f, 'utf8');
      assert.ok(md.includes(note));
      assert.ok(md.includes(original.user_edits.integration_note));
      for (const c of original.candidates) assert.ok(md.includes(c.patent_id_canonical));
    }
    assert.deepEqual(page.errors, []);
    results.push({query_id: name, result: 'PASS', imported_candidates: imported.candidates, backend_version: imported.version,
      import: 'real-file-input', persistence: 'IndexedDB save and page reload', th_en_export: 'backend edits and UI note retained', page_errors: 0});
  }
  const summary = {status:'PASS_REAL_BACKEND_BROWSER_IMPORT', cases:results, live_search_api:'NOT_IMPLEMENTED', dense_encoding:'NOT_RUN', provider_calls:0, paid_cost_usd:0};
  writeFileSync(join(input, 'browser-summary.json'), JSON.stringify(summary, null, 2)+'\n');
  console.log(JSON.stringify(summary, null, 2));
} finally {
  if (browser) await browser.close();
  server.close();
}
