// Browser acceptance scenarios for the HealthTech web frontend.
// Real headless Chrome, real IndexedDB in a persistent temporary profile, real
// downloads and real <input type=file> imports. Writes evidence (results.json,
// screenshots, synthetic-only downloads) to docs/healthtech/ux/implementation/evidence/e2e/.
import { mkdtempSync, mkdirSync, rmSync, readFileSync, writeFileSync, existsSync, renameSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import { launch, waitForDownload, sleep } from './cdp.mjs';
import { startServer } from '../../serve.mjs';
import { parseLossless, stringifyLossless } from '../../app/src/core/pyjson.js';

const here = dirname(fileURLToPath(import.meta.url));
const WEB = resolve(here, '../..');
const REPO = resolve(WEB, '../..');
const OUT = process.env.HEALTHTECH_E2E_OUT
  ? resolve(process.env.HEALTHTECH_E2E_OUT)
  : resolve(REPO, 'docs/healthtech/audits', `web-e2e-${new Date().toISOString().replace(/[:.]/g, '-')}`);
const SHOTS = join(OUT, 'screenshots');
const DL = join(OUT, 'downloads');
// Evidence is immutable: never erase the previous branch's acceptance record.
mkdirSync(OUT, { recursive: true });
if (readdirSync(OUT).length) throw new Error(`Evidence destination is not empty: ${OUT}`);
mkdirSync(SHOTS, { recursive: true });
mkdirSync(DL, { recursive: true });
const WORK = mkdtempSync(join(tmpdir(), 'healthtech-web-e2e-'));
const PUBLIC_DIR = process.env.HEALTHTECH_PUBLIC_RUN_DIR || resolve(REPO, '../../patent-to-pilot/results/healthtech/public-dossiers-20261027-r3/K190167');

const TH_NOTE = 'บันทึกผู้ใช้ทดสอบ: ต้องขอเอกสารเปิดเผยที่ลงวันที่จริง 🙂';
const EN_NOTE = 'User test note: need a dated real disclosure';
const EVIL = '<img src=x onerror="window.__pwned=1"><script>window.__pwned=2</script> [x](javascript:alert(1))';

const results = [];
let server, base;

function record(id, stories, fn, dl = '') { return { id, stories, fn, dl }; }
function grab(path, newName) { const p = join(dirname(path), newName); renameSync(path, p); return p; }
const assert = (cond, msg) => { if (!cond) throw new Error(`assertion failed: ${msg}`); };

function git(cmd) { try { return execSync(`git ${cmd}`, { cwd: REPO, encoding: 'utf8' }).trim(); } catch { return null; } }

async function allowDownloads(browser, dir) {
  mkdirSync(dir, { recursive: true });
  await browser.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dir, eventsEnabled: true });
}

async function a11yAudit(page, label) {
  // Let the real pipeline run and its decorative animations settle first.
  await page.waitFor('!window.__healthtechApp.state.current?.pipe?.running && document.getAnimations().filter((a) => a.playState === "running").length === 0', 12000);
  await textAudit(page, label);
  const r = await page.eval(`(() => {
    const issues = [];
    document.querySelectorAll('input, select, textarea').forEach((el) => {
      if (el.type === 'hidden' || el.hidden) return;
      const named = el.labels?.length || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
      if (!named) issues.push('unlabelled ' + el.tagName + '#' + el.id);
    });
    document.querySelectorAll('button, a[href]').forEach((el) => { if (!el.textContent.trim() && !el.getAttribute('aria-label')) issues.push('unnamed ' + el.tagName); });
    const h1 = document.querySelectorAll('main h1').length;
    if (h1 !== 1) issues.push('h1 count ' + h1);
    const ids = [...document.querySelectorAll('[id]')].map((e) => e.id); const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
    if (dup.length) issues.push('duplicate ids ' + [...new Set(dup)].join(','));
    if (document.documentElement.scrollWidth > document.documentElement.clientWidth + 1) issues.push('horizontal overflow ' + document.documentElement.scrollWidth + '>' + document.documentElement.clientWidth + ' by ' + [...document.querySelectorAll('body *')].filter((e) => e.getBoundingClientRect().right > document.documentElement.clientWidth + 1 && e.getBoundingClientRect().width > 0).slice(-4).map((e) => e.tagName + '.' + String(e.className).slice(0, 24) + '#' + e.id + '[' + e.textContent.trim().slice(0, 24) + ']').join(' | '));
    if (document.getAnimations().length) issues.push('animations running');
    return { issues, lang: document.documentElement.lang, theme: document.documentElement.dataset.theme };
  })()`);
  assert(!r.issues.length, `${label}: ${r.issues.join('; ')}`);
  return r;
}

/** Text fit: no mid-word break rules, nothing clipped, short labels stay within their line budget. */
async function textAudit(page, label) {
  const r = await page.eval(`(() => {
    const issues = [];
    const visible = (el) => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
    for (const el of document.querySelectorAll('body *')) {
      if (!visible(el) || el.closest('pre, .wrap, .mono, code')) continue;
      const cs = getComputedStyle(el);
      if (cs.overflowWrap === 'anywhere' || cs.wordBreak === 'break-all') issues.push('mid-word break rule on ' + el.tagName + '.' + el.className);
    }
    for (const el of document.querySelectorAll('.btn, [role=tab], .badge, .save-status, .tab-count, .ws-tech summary')) {
      if (visible(el) && el.scrollWidth > el.clientWidth + 1) issues.push('clipped: ' + el.textContent.trim().slice(0, 40));
    }
    for (const el of document.querySelectorAll('.node-title, .node-summary')) {
      if (visible(el) && el.scrollHeight > el.clientHeight + 1) issues.push('node text cut: ' + el.textContent.trim().slice(0, 40));
    }
    for (const el of document.querySelectorAll('.tile-label, .panel-tabs [role=tab], .btn')) {
      if (!visible(el)) continue;
      const lh = parseFloat(getComputedStyle(el).lineHeight) || 24;
      if (el.getBoundingClientRect().height > lh * 2.3 + 20) issues.push('too many lines: ' + el.textContent.trim().slice(0, 40));
    }
    return [...new Set(issues)];
  })()`);
  assert(!r.length, `${label} text audit: ${r.slice(0, 6).join('; ')}`);
  return r;
}

async function projectIdOf(page) { return page.eval('window.__healthtechApp.state.current?.project.projectId'); }
async function saveState(page) { return page.eval('document.getElementById("save-status")?.dataset.state'); }
async function waitSaved(page, state = 'saved') { await page.waitFor(`document.getElementById("save-status")?.dataset.state === ${JSON.stringify(state)}`, 8000); }
async function storeHead(page, pid) {
  return page.eval(`(async () => { const r = await window.__healthtechApp.state.store.loadProject(${JSON.stringify(pid)}); return { head: r.value.project.headSnapshotId, count: r.value.snapshots.length, snaps: r.value.snapshots.map(s => ({ id: s.snapshotId, parent: s.parentSnapshotId, texts: s.overlay.notes.map(n => n.text) })) }; })()`);
}
async function addNoteOnOverview(page, text) {
  await page.click('[id="add-note-dossier"]');
  await page.waitFor('document.activeElement?.tagName === "TEXTAREA"');
  await page.send('Input.insertText', { text });
  return page.eval('document.activeElement.id');
}

const state = {};

const scenarios = [
  record('E01-home-capabilities', ['US-01', 'US-26', 'US-28'], async ({ page }) => {
    await page.goto(`${base}/`);
    const r = await page.eval(`({
      starts: ['start-device','start-import','start-demo'].every((id) => document.getElementById(id)),
      email: document.querySelectorAll('input[type=email], input[type=password]').length,
      caps: document.getElementById('capabilities').textContent,
      scope: window.__healthtechApp.state.storageScope, lang: document.documentElement.lang })`);
    assert(r.starts && r.email === 0, 'three start actions, no email/password field');
    assert(r.scope === 'indexeddb', 'durable IndexedDB storage available');
    assert(/ยังใช้ไม่ได้/.test(r.caps), 'unavailable capabilities listed');
    await a11yAudit(page, 'home');
    await page.screenshot(join(SHOTS, 'E01-home-th-1280.jpg'));
    return r;
  }),

  record('E02-demo-overview', ['US-11', 'US-15', 'US-26'], async ({ page }) => {
    await page.click('#start-demo');
    await page.waitFor('location.hash.startsWith("#/project/") && document.getElementById("save-status")');
    state.pid = await projectIdOf(page);
    const r = await page.eval(`({
      mode: document.querySelector('.mode-banner').dataset.mode,
      banner: document.querySelector('.mode-banner').textContent,
      statuses: [...document.querySelectorAll('[data-status]')].map(e => e.dataset.status),
      approved: /FDA approved|อนุมัติ/i.test(document.body.textContent) })`);
    assert(r.mode === 'synthetic_demo' && /ข้อมูลสมมติ/.test(r.banner), 'synthetic label persists');
    assert(r.statuses.includes('retrieved_candidate') && r.statuses.includes('disclosed_link'), 'candidate vs disclosed shown separately');
    assert(!r.approved, 'no approval claim');
    await waitSaved(page);
    await a11yAudit(page, 'overview');
    await page.screenshot(join(SHOTS, 'E02-overview-th-1280.jpg'));
    return { projectId: state.pid, ...r };
  }),

  record('E03-source-viewer-locators', ['US-14', 'US-15', 'US-25'], async ({ page }) => {
    await page.hash(`#/project/${state.pid}/source/ux-synthetic-unicode?evidenceId=ux-e-unicode`);
    await page.waitFor('document.getElementById("source-span")');
    const ok = await page.eval(`({ span: document.getElementById('source-span').textContent, codepoints: document.querySelector('.source-view').textContent.includes('1–2') })`);
    assert(ok.span === '🙂', 'emoji span highlighted by code point');
    await page.screenshot(join(SHOTS, 'E03-source-emoji-span.jpg'));
    await page.hash(`#/project/${state.pid}/source/ux-synthetic-unicode?evidenceId=ux-e-unicode&sim=fx12`);
    await page.waitFor('document.getElementById("source-mismatch")');
    const bad = await page.eval(`({ code: document.getElementById('source-mismatch').dataset.code, span: !!document.getElementById('source-span'), matched: !!document.querySelector('.source-view [data-integrity="exact_span_checked"]'), locatorKept: document.getElementById('source-mismatch').textContent.includes('chars:1000:2000') })`);
    assert(bad.code === 'span_mismatch' && !bad.span && !bad.matched && bad.locatorKept, 'FX-12 withholds badge and keeps raw locator');
    await page.screenshot(join(SHOTS, 'E03-source-fx12-mismatch.jpg'));
    await page.hash(`#/project/${state.pid}/source/ux-synthetic-device?evidenceId=ux-e-device`);
    await page.waitFor('document.getElementById("source-field")');
    const field = await page.eval('document.getElementById("source-field").textContent');
    assert(field === '"SYNTHETIC demonstration comparator"', 'typed field value shown');
    await page.hash(`#/project/${state.pid}/evidence`);
    // ARIA tabs: arrow key moves selection and focus to the candidates tab.
    await page.eval('document.getElementById("tab-evidence").focus()');
    await page.key('ArrowRight', 'ArrowRight', 39);
    const tabState = await page.eval(`({ selected: document.querySelector('.tablist [role=tab][aria-selected=true]').id, focus: document.activeElement.id,
      panel: document.querySelector('.tabpanel[role=tabpanel]').getAttribute('aria-labelledby'), stops: [...document.querySelectorAll('.tablist [role=tab]')].filter(t => t.tabIndex === 0).length })`);
    assert(tabState.selected === 'tab-candidates' && tabState.focus === 'tab-candidates' && tabState.panel === 'tab-candidates' && tabState.stops === 1, `tabs keyboard: ${JSON.stringify(tabState)}`);
    await page.click('[id="cmp-US99000002B2"]');
    await page.waitFor('document.getElementById("compare-table")');
    const discHref = await page.eval('[...document.querySelectorAll("#compare-table a")].map(a => a.getAttribute("href"))[0]');
    assert(discHref.includes('ux-synthetic-independent-disclosure') && discHref.includes('ux-e-disclosure'), 'disclosed link opens separate disclosure evidence');
    await page.eval('document.getElementById("cand-filter").value = "99000001"; document.getElementById("cand-filter").dispatchEvent(new Event("input"))');
    const hidden = await page.eval('document.body.textContent.includes("US99000002B2: เลือกไว้แต่ถูกซ่อนด้วยตัวกรองปัจจุบัน")');
    assert(hidden, 'selection kept with hidden-by-filter explanation');
    await a11yAudit(page, 'evidence');
    await page.screenshot(join(SHOTS, 'E03-evidence-compare.jpg'));
    // US-13: unlinked feature is unresolved (not zero); a local link is labelled user-authored.
    await page.click('#tab-features');
    const featBefore = await page.eval('document.querySelector(".feature .badge").textContent');
    await page.click('[id="fl-0-ux-e-device"]');
    await page.waitFor('document.querySelector(".feature .badge")?.textContent !== ' + JSON.stringify(featBefore));
    const featAfter = await page.eval('({ badge: document.querySelector(".feature .badge").textContent, links: window.__healthtechApp.state.current.overlay.featureLinks })');
    assert(/ยังหาข้อสรุปไม่ได้|Unresolved/.test(featBefore) && /เชื่อมโยงโดยคุณ|Linked by you/.test(featAfter.badge) && featAfter.links[0].basis === 'user_authored', 'feature link is a labelled user annotation');
    return { ...ok, fx12: bad, field, discHref, tabState, feature: { before: featBefore, after: featAfter.badge } };
  }),

  record('E04-save-close-reopen', ['US-16', 'US-17', 'US-19', 'US-20'], async (ctx) => {
    const { page } = ctx;
    await page.hash(`#/project/${state.pid}`);
    const before = await storeHead(page, state.pid);
    const hashBefore = await page.eval('window.__healthtechApp.state.current.dossierHash');
    state.noteFieldId = await addNoteOnOverview(page, TH_NOTE);
    const sawUnsaved = await saveState(page);
    // US-16: "reviewed by me" is a user marker only; it never promotes a candidate.
    await page.eval(`(() => { const s = document.getElementById(${JSON.stringify(state.noteFieldId.replace(/^note-/, 'marker-'))}); s.value = 'reviewed_by_user'; s.dispatchEvent(new Event('change')); })()`);
    await waitSaved(page);
    const after = await storeHead(page, state.pid);
    assert(['unsaved', 'saving'].includes(sawUnsaved), `not shown as saved before acknowledgement (was ${sawUnsaved})`);
    assert(after.count === before.count + 1 && after.snaps.find((s) => s.id === after.head).parent === before.head, 'one new snapshot citing previous head');
    state.savedSnapshot = after.head;
    await ctx.restart();
    const page2 = ctx.page;
    await page2.goto(`${base}/#/project/${state.pid}`);
    await page2.waitFor(`document.getElementById(${JSON.stringify(state.noteFieldId)})`);
    const r = await page2.eval(`({ text: document.getElementById(${JSON.stringify(state.noteFieldId)}).value, snap: document.getElementById('save-snapshot').textContent,
      status: document.getElementById('save-status').dataset.state, hash: window.__healthtechApp.state.current.dossierHash,
      backendVersion: window.__healthtechApp.state.current.dossier.version, srcPayload: window.__healthtechApp.state.current.dossier.sources[0].payload.device_name })`);
    assert(r.text === TH_NOTE, 'note retained after browser restart');
    assert(r.snap === state.savedSnapshot && r.status === 'saved', 'same acknowledged snapshot');
    assert(r.hash === hashBefore && r.backendVersion === 1 && r.srcPayload === 'SYNTHETIC demonstration comparator', 'source facts and backend version unchanged');
    const review = await page2.eval(`({ marker: window.__healthtechApp.state.current.overlay.notes.find(n => n.text === ${JSON.stringify(TH_NOTE)}).reviewMarker,
      statuses: window.__healthtechApp.state.current.dossier.candidates.map(c => c.association_status) })`);
    assert(review.marker === 'reviewed_by_user' && review.statuses.join() === 'retrieved_candidate,disclosed_link', 'review marker saved; candidate status unchanged');
    await page2.screenshot(join(SHOTS, 'E04-reopened-after-restart.jpg'));
    return { before: before.head, saved: state.savedSnapshot, reopened: r };
  }),

  record('E05-two-writer-conflict', ['US-18', 'US-19'], async (ctx) => {
    const a = ctx.page;
    const b = await ctx.browser.newPage(`${base}/#/project/${state.pid}`);
    await b.waitFor(`document.getElementById(${JSON.stringify(state.noteFieldId)})`);
    const base0 = await storeHead(a, state.pid);
    await a.type(`[id="${state.noteFieldId}"]`, 'EDIT_FROM_TAB_A');
    await b.type(`[id="${state.noteFieldId}"]`, 'EDIT_FROM_TAB_B');
    await a.click('#save-now');
    await waitSaved(a);
    await b.click('#save-now');
    await b.waitFor('document.getElementById("conflict-panel")');
    const mid = await storeHead(a, state.pid);
    const panel = await b.eval(`({ status: document.getElementById('save-status').dataset.state, base: document.getElementById('conflict-base').textContent,
      theirs: document.getElementById('conflict-theirs').textContent, yours: document.getElementById('conflict-yours').textContent,
      field: document.getElementById(${JSON.stringify(state.noteFieldId)}).value })`);
    assert(mid.count === base0.count + 1, 'exactly one of the two writes committed');
    assert(panel.status === 'conflict' && (await saveState(a)) === 'saved', 'A saved, B conflict — no false dual success');
    assert(panel.base.includes(TH_NOTE) && panel.theirs.includes('EDIT_FROM_TAB_A') && panel.yours.includes('EDIT_FROM_TAB_B') && panel.field === 'EDIT_FROM_TAB_B', 'base/theirs/yours all retained');
    await b.screenshot(join(SHOTS, 'E05-conflict-panel.jpg'));
    await b.click('#conflict-reapply');
    await waitSaved(b);
    const end = await storeHead(a, state.pid);
    const headSnap = end.snaps.find((s) => s.id === end.head);
    assert(headSnap.texts.includes('EDIT_FROM_TAB_A') && headSnap.texts.includes('EDIT_FROM_TAB_B') && headSnap.parent === mid.head, 'reapply keeps both texts on top of the newer version');
    await a.waitFor(`document.body.textContent.length && [...document.querySelectorAll('textarea')].some(t => t.value === 'EDIT_FROM_TAB_B')`, 8000);
    // Race: both tabs commit at once from the same acknowledged base.
    await a.type(`[id="${state.noteFieldId}"]`, 'RACE_A');
    await b.type(`[id="${state.noteFieldId}"]`, 'RACE_B');
    const raceBase = await storeHead(a, state.pid);
    await Promise.all([a.eval('window.__healthtechApp.saveNow()'), b.eval('window.__healthtechApp.saveNow()')]);
    await sleep(300);
    const states = [await saveState(a), await saveState(b)].sort();
    const raceEnd = await storeHead(a, state.pid);
    assert(states.join() === 'conflict,saved' && raceEnd.count === raceBase.count + 1, `simultaneous commits: one saved, one conflict (${states})`);
    const loser = (await saveState(a)) === 'conflict' ? a : b;
    const loserText = await loser.eval(`document.getElementById(${JSON.stringify(state.noteFieldId)}).value`);
    await loser.click('#conflict-reapply');
    await waitSaved(loser);
    const final = await storeHead(a, state.pid);
    const finalTexts = final.snaps.find((s) => s.id === final.head).texts;
    assert(finalTexts.includes('RACE_A') && finalTexts.includes('RACE_B') && finalTexts.includes('EDIT_FROM_TAB_B'), 'race texts and earlier merge preserved');
    assert(finalTexts.includes(loserText), 'losing writer text recovered after reapply');
    await b.close();
    return { firstConflict: { before: base0.head, winner: mid.head, merged: end.head }, race: { states, before: raceBase.head, after: raceEnd.head, finalTexts } };
  }),

  record('E06-requests-and-locale-theme', ['US-23', 'US-27', 'US-20'], async ({ page }) => {
    await page.hash(`#/project/${state.pid}/requests`);
    await page.click('#add-request');
    await page.waitFor('document.activeElement?.id?.startsWith("req-q-")');
    await page.send('Input.insertText', { text: 'ขอเอกสารเปิดเผยที่ลงวันที่ / Request a dated disclosure' });
    const reqId = await page.eval('document.activeElement.id');
    // Switch locale and every theme while the text is still unsaved: text and focus must survive.
    await page.eval('document.getElementById("layout-menu")?.setAttribute("open", ""); window.__healthtechApp.state.openMenus = { "layout-menu": true }; document.getElementById("pref-locale").focus()');
    await page.eval('var s = document.getElementById("pref-locale"); s.value = "en"; s.dispatchEvent(new Event("change"))');
    const afterLocale = await page.eval(`({ lang: document.documentElement.lang, focus: document.activeElement.id, text: document.getElementById(${JSON.stringify(reqId)}).value, h1: document.querySelector('main h1').textContent })`);
    assert(afterLocale.lang === 'en' && afterLocale.focus === 'pref-locale' && afterLocale.text.startsWith('ขอเอกสาร') && afterLocale.h1 === 'Next information requests', 'locale switch keeps unsaved text and focus; quotes not translated');
    const themes = [];
    for (const theme of ['formal-dark', 'kmitl-inspired', 'ict-inspired', 'formal-light']) {
      await page.eval(`var s = document.getElementById("pref-theme"); s.value = ${JSON.stringify(theme)}; s.dispatchEvent(new Event("change"))`);
      themes.push(await page.eval(`({ theme: document.documentElement.dataset.theme, bg: getComputedStyle(document.body).backgroundColor, text: document.getElementById(${JSON.stringify(reqId)}).value.length })`));
    }
    assert(themes.every((t) => t.text > 0) && new Set(themes.map((t) => t.bg)).size === 4, 'four themes applied, text intact');
    await waitSaved(page);
    return { afterLocale, themes };
  }),

  record('E07-export-th-en-and-recovery-roundtrip', ['US-21', 'US-22', 'US-24'], async (ctx) => {
    const { page } = ctx;
    await page.hash(`#/project/${state.pid}/export`);
    const pick = async (id) => { await page.click(`#${id}`); await sleep(80); };
    const files = {};
    for (const lang of ['th', 'en']) {
      await pick(`export-lang-${lang}`);
      await pick('export-format-md');
      await page.click('#export-download');
      files[lang] = readFileSync(grab(await waitForDownload(DL, `UX-DEMO-001-${lang}.md`), `E07-UX-DEMO-001-${lang}.md`), 'utf8');
    }
    await pick('export-format-recovery');
    await page.click('#export-preview');
    await page.waitFor('document.getElementById("export-preview-text")');
    await page.click('#export-download');
    const status = await page.eval('document.getElementById("export-status")?.textContent');
    const toast = await page.eval('[...document.querySelectorAll("#toasts .toast")].map(t => ({ role: t.getAttribute("role"), text: t.textContent, close: !!t.querySelector("button[aria-label]") }))');
    assert(toast.length >= 1 && toast.length <= 2 && toast.every((x) => x.role === 'status' && x.close), `toast: ${JSON.stringify(toast)}`);
    const recoveryPath = grab(await waitForDownload(DL, 'UX-DEMO-001-recovery.json'), 'E07-UX-DEMO-001-recovery.json');
    const recovery = readFileSync(recoveryPath, 'utf8');
    for (const [lang, md] of Object.entries(files)) {
      for (const s of ['EDIT_FROM_TAB_B', 'RACE_A', 'ขอเอกสารเปิดเผยที่ลงวันที่ / Request a dated disclosure', 'ux-e-unicode', '🙂', 'US 99000001 A1', 'healthtech-web-markdown']) assert(md.includes(s), `${lang} md missing ${s}`);
    }
    assert(files.th.includes('ตัวอย่างข้อมูลสมมติสำหรับตรวจการทำงานของระบบ') && files.en.includes('Synthetic engineering example'), 'mode label in both exports');
    assert(/Download started|เริ่มดาวน์โหลดแล้ว/.test(status), 'honest download message');
    // Reimport the recovery file through the real file input.
    await page.hash('#/import');
    const before = await page.eval('window.__healthtechApp.state.projects.length');
    await page.setFiles('#import-file', [recoveryPath]);
    await page.waitFor('document.getElementById("import-result")?.dataset.result');
    assert((await page.eval('document.getElementById("import-result").dataset.result')) === 'accepted', 'recovery accepted');
    await page.click('#import-accept');
    await page.waitFor('location.hash.startsWith("#/project/") && document.getElementById("save-status")?.dataset.state === "saved"');
    const newPid = await projectIdOf(page);
    const texts = await page.eval('[...document.querySelectorAll("textarea")].map(t => t.value)');
    assert(newPid !== state.pid && texts.some((t) => t.includes('RACE_')), 'reimported copy restores notes');
    assert((await page.eval('window.__healthtechApp.state.projects.length')) === before + 1, 'one new project');
    // Export again from the reimported copy (TH) and compare note presence.
    await page.hash(`#/project/${newPid}/export`);
    await pick('export-lang-th');
    await pick('export-format-md');
    await page.click('#export-download');
    const again = readFileSync(grab(await waitForDownload(DL, 'UX-DEMO-001-th.md'), 'E07-UX-DEMO-001-th.after-reimport.md'), 'utf8');
    assert(again.includes('EDIT_FROM_TAB_B') && again.includes('ขอเอกสารเปิดเผยที่ลงวันที่'), 'notes survive reimport → export');
    await page.screenshot(join(SHOTS, 'E07-export.jpg'));
    state.recoveryPath = recoveryPath;
    return { status, mdBytes: { th: files.th.length, en: files.en.length }, recoveryBytes: recovery.length, reimportedProject: newPid };
  }),

  record('E08-safe-rendering', ['US-22', 'US-25'], async ({ page }) => {
    await page.hash(`#/project/${state.pid}`);
    await addNoteOnOverview(page, EVIL);
    await waitSaved(page);
    await page.hash(`#/project/${state.pid}/export`);
    await page.click('#export-format-md');
    await page.click('#export-preview');
    await page.waitFor('document.getElementById("export-preview-text")');
    const r = await page.eval(`({ pwned: window.__pwned ?? null, scripts: document.querySelectorAll('main script, main img').length,
      preview: document.getElementById('export-preview-text').textContent.includes('&lt;script&gt;'),
      noteInert: [...document.querySelectorAll('textarea')].length >= 0 })`);
    assert(r.pwned === null && r.scripts === 0 && r.preview, 'note HTML stays inert in app and Markdown');
    return r;
  }),

  record('E09-import-negatives-and-public', ['US-05', 'US-06', 'US-25', 'US-08', 'US-11'], async ({ page }) => {
    const fx = parseLossless(readFileSync(resolve(REPO, 'docs/healthtech/ux/fixtures/ui-fixtures.json'), 'utf8'));
    const dir = join(WORK, 'imports');
    mkdirSync(dir, { recursive: true });
    const write = (name, mutate) => { const d = parseLossless(stringifyLossless(fx.synthetic_dossier)); mutate?.(d); const p = join(dir, name); writeFileSync(p, stringifyLossless(d)); return p; };
    const recovery = parseLossless(readFileSync(state.recoveryPath, 'utf8'));
    recovery.mode = 'imported_public';
    writeFileSync(join(dir, 'wrong-mode-recovery.json'), stringifyLossless(recovery));
    writeFileSync(join(dir, 'unsupported.json'), '{"hello":"world"}');
    writeFileSync(join(dir, 'notes.txt'), 'private text must not be read');
    writeFileSync(join(dir, 'big.json'), `"${'x'.repeat(5 * 1024 * 1024 + 10)}"`);
    const cases = [
      ['hash mismatch', [write('hash.json', (d) => { d.sources[0].payload.device_name = 'changed'; })], 'source_hash_mismatch'],
      ['FX-06 missing comparator source', [write('fx06.json', (d) => { d.sources.splice(0, 1); })], 'dangling_source'],
      ['missing disclosure', [write('disc.json', (d) => { d.candidates[1].disclosure_evidence_id = null; })], 'missing_disclosure'],
      ['late source', [write('late.json', (d) => { d.query.evidence_cutoff = '2026-10-26'; })], 'late_source'],
      ['synthetic as public (mixed)', [write('mixed.json', (d) => { d.query.brief.data_class = 'public'; })], 'synthetic_in_public'],
      ['wrong mode recovery', [join(dir, 'wrong-mode-recovery.json')], 'wrong_mode'],
      ['unsupported schema', [join(dir, 'unsupported.json')], 'unsupported_schema'],
      ['unsupported type', [join(dir, 'notes.txt')], 'unsupported_type'],
      ['too large', [join(dir, 'big.json')], 'too_large'],
    ];
    await page.hash(`#/project/${state.pid}`);
    const before = await page.eval('({ n: window.__healthtechApp.state.projects.length, head: window.__healthtechApp.state.current.project.headSnapshotId })');
    const rows = [];
    for (const [name, files, code] of cases) {
      await page.hash('#/import');
      await page.eval('window.__healthtechApp.state.importPreview = null');
      await page.setFiles('#import-file', files);
      await page.waitFor('document.getElementById("import-result")?.dataset.result');
      const r = await page.eval(`({ result: document.getElementById('import-result').dataset.result, codes: [...document.querySelectorAll('[data-code]')].map(e => e.dataset.code), leaked: document.body.textContent.includes('private text must not be read') })`);
      assert(r.result === 'rejected' && r.codes.includes(code) && !r.leaked, `${name}: expected ${code}, got ${r.result} ${r.codes}`);
      rows.push({ name, expected: code, result: r.result, codes: r.codes });
    }
    await page.screenshot(join(SHOTS, 'E09-import-rejected.jpg'));
    await page.hash(`#/project/${state.pid}`);
    const after = await page.eval('({ n: window.__healthtechApp.state.projects.length, head: window.__healthtechApp.state.current.project.headSnapshotId })');
    assert(after.n === before.n && after.head === before.head, 'rejections changed nothing');
    let publicRun = 'NOT_AVAILABLE';
    if (existsSync(join(PUBLIC_DIR, 'dossier.json'))) {
      await page.hash('#/import');
      await page.eval('window.__healthtechApp.state.importPreview = null');
      await page.setFiles('#import-file', ['dossier.json', 'manifest.json', 'acquisition_events.jsonl'].map((f) => join(PUBLIC_DIR, f)));
      await page.waitFor('document.getElementById("import-result")?.dataset.result');
      assert((await page.eval('document.getElementById("import-result").dataset.result')) === 'accepted', 'public run accepted');
      await page.click('#import-accept');
      await page.waitFor('document.getElementById("candidate-scope")');
      const pub = await page.eval(`({ mode: document.querySelector('.mode-banner').dataset.mode, scope: document.getElementById('candidate-scope').dataset.scope, text: document.querySelector('main').textContent })`);
      assert(pub.mode === 'imported_public' && pub.scope === 'empty_corpus' && (pub.text.includes('รอบงานที่นำเข้านี้ไม่มีชุดข้อมูลสิทธิบัตร') || pub.text.includes('This imported run included no patent corpus. Patent coverage is unknown.')), 'public empty corpus explained');
      const pid = await projectIdOf(page);
      await page.hash(`#/project/${pid}/runs`);
      const run = await page.eval(`({ consistent: document.getElementById('run-consistency').dataset.consistent, text: document.getElementById('run-receipt').textContent, simButtons: !!document.getElementById("sim-cancel-state") || !!document.getElementById('sim-loading'), startButtons: [...document.querySelectorAll('button')].filter(b => /start|เริ่มการค้น|cancel|หยุด/i.test(b.textContent)).length })`);
      assert(run.consistent === 'true' && /\$0/.test(run.text) && !run.simButtons && run.startButtons === 0, 'public receipt: consistent, scoped $0, no run controls or simulations');
      await page.screenshot(join(SHOTS, 'E09-public-K190167-runs.jpg'));
      publicRun = { projectId: pid, ...pub, text: undefined, run: { ...run, text: undefined } };
    }
    return { rejected: rows, publicRun };
  }),

  record('E10-brief-flow', ['US-02', 'US-03', 'US-04'], async ({ page }) => {
    await page.hash('#/new/device');
    await page.type('#device-search', 'SYNTHETIC demonstration comparator');
    const results = await page.eval('[...document.querySelectorAll(".device-card .kv")].map(k => k.textContent)');
    const ids = new Set(results.map((r) => /UX-DEMO-00\d/.exec(r)?.[0]));
    assert(['UX-DEMO-001', 'UX-DEMO-002', 'UX-DEMO-003'].every((x) => ids.has(x)) && results.every((r) => /UX-DEMO-00\d/.test(r) && /2026-10-\d\d/.test(r)), 'similar names disambiguated by ID/applicant/date');
    await page.type('#device-search', 'zzz-no-match');
    const none = await page.eval(`({ none: document.body.textContent.includes('ไม่พบรายการที่ตรงกันในชุดข้อมูลนี้') || document.body.textContent.includes('No matching record'), kept: document.getElementById('device-search').value })`);
    assert(none.none && none.kept === 'zzz-no-match', 'no match keeps input, no invented recommendation');
    await page.type('#device-search', 'UX-DEMO-003');
    await page.click('#use-device-0');
    await page.waitFor('document.getElementById("brief-objective")');
    await page.eval('var c = document.getElementById("brief-cutoff"); c.value = "2026-10-27"; c.dispatchEvent(new Event("input")); c.dispatchEvent(new Event("change"))');
    const conflict = await page.eval('document.getElementById("cutoff-error")?.textContent || ""');
    assert(conflict.includes('2026-10-29'), 'cutoff conflict explained inline');
    await page.type('#brief-featuresText', 'sensor\n\nballoon');
    await page.click('#brief-continue');
    await page.waitFor('document.getElementById("brief-result")');
    const blank = await page.eval('document.getElementById("brief-result").textContent');
    assert(/2/.test(blank) && (await page.eval('document.getElementById("brief-objective").value')).length > 0, 'blank line rejected, other fields kept');
    await page.type('#brief-featuresText', 'sensor\nballoon');
    await page.eval('var c = document.getElementById("brief-cutoff"); c.value = "2026-10-30"; c.dispatchEvent(new Event("input"))');
    await page.click('#brief-continue');
    await page.waitFor('document.getElementById("query-preview")');
    const q = JSON.parse(await page.eval('document.getElementById("query-preview").textContent'));
    assert(q.device_id_canonical === 'UX-DEMO-003' && q.device_id_raw === 'UX-DEMO-003' && q.features_of_interest.length === 2 && q.acquisition_budget.accounting === 'offline_counts', 'query preview pins comparator');
    assert(await page.eval('!!document.getElementById("run-unavailable")'), 'run start explained as unavailable');
    await page.click('#brief-save');
    await page.waitFor('location.hash.endsWith("/brief") && document.getElementById("save-status")');
    const draftPid = await projectIdOf(page);
    await page.goto(`${base}/#/project/${draftPid}/brief`);
    const persisted = await page.eval('document.getElementById("brief-featuresText").value');
    assert(persisted === 'sensor\nballoon', 'draft persisted across reload');
    await page.hash('#/new/device');
    await page.type('#device-search', 'my idea');
    await page.eval('[...document.querySelectorAll("button")].find(b => /แค่แนวคิด|idea-only/.test(b.textContent)).click()');
    await page.waitFor('document.getElementById("brief-continue")');
    await page.click('#brief-continue');
    await page.waitFor('document.getElementById("brief-result")');
    const idea = await page.eval('({ text: document.getElementById("brief-result").textContent, preview: !!document.getElementById("query-preview") })');
    assert(!idea.preview && /missing comparator|ยังไม่มีอุปกรณ์อ้างอิง|no comparator/i.test(idea.text), 'idea-only draft cannot become a query');
    await a11yAudit(page, 'brief');
    return { results: results.length, query: q.query_id, draftPid };
  }),

  record('E11-runs-simulation', ['US-07', 'US-08', 'US-09', 'US-10'], async ({ page }) => {
    await page.hash(`#/project/${state.pid}/runs`);
    const r0 = await page.eval(`({ receipt: document.querySelector('main').textContent.includes('ไม่ได้นำเข้าบันทึกรอบงาน') || document.querySelector('main').textContent.includes('No run receipt'), sim: !!document.getElementById('sim-title') })`);
    assert(r0.receipt && r0.sim, 'demo has no receipt (nothing inferred) and labelled simulations');
    await page.click('#sim-cancel');
    await page.click('#sim-cancel-btn');
    const pending = await page.eval('document.getElementById("sim-cancel-state").dataset.state');
    await page.waitFor('document.getElementById("sim-cancel-state")?.dataset.state === "acknowledged"', 4000);
    await page.click('#sim-billing');
    const billing = await page.eval('document.querySelector(".sim").textContent');
    assert(pending === 'pending' && /pending reconciliation|รอกระทบยอด/i.test(billing) && !/\$0|0\.0/.test(billing), 'cancel pending→acknowledged; billing unknown, not zero');
    await page.click('#sim-partial');
    await page.hash(`#/project/${state.pid}`);
    const partial = await page.eval('document.querySelector("main").textContent.includes("ux-synthetic-patent-source-unavailable")');
    assert(partial, 'FX-04 partial banner on overview while facts remain');
    await page.screenshot(join(SHOTS, 'E11-partial-overview.jpg'));
    return { pending, partial };
  }),

  record('E12-keyboard-path', ['US-27', 'US-14', 'US-21'], async ({ page }) => {
    await page.goto(`${base}/`);
    const tabTo = async (pred, max = 250, back = false) => {
      for (let i = 0; i < max; i++) {
        await page.key('Tab', 'Tab', 9, back ? 8 : 0);
        if (await page.eval(`(() => { const el = document.activeElement; return ${pred}; })()`)) return true;
      }
      throw new Error(`keyboard focus never reached ${pred}`);
    };
    const firstStop = await (async () => { await page.key('Tab'); return page.eval('document.activeElement.className'); })();
    assert(firstStop === 'skip-link', 'skip link is first tab stop');
    await tabTo('el.id === "start-demo"');
    const outline = await page.eval('getComputedStyle(document.activeElement).outlineStyle');
    await page.key('Enter');
    await page.waitFor('location.hash.startsWith("#/project/")');
    await tabTo('el.getAttribute("href")?.endsWith("/evidence") && el.closest("nav")');
    await page.key('Enter');
    await page.waitFor('document.getElementById("inspect-ux-e-unicode")');
    await tabTo('el.id === "inspect-ux-e-unicode"');
    await page.key('Enter');
    await page.waitFor('document.getElementById("source-span")');
    await tabTo('el.id === "add-note-ux-e-unicode"');
    await page.key('Enter');
    await page.waitFor('document.activeElement?.tagName === "TEXTAREA"');
    await page.send('Input.insertText', { text: EN_NOTE });
    await tabTo('el.id === "save-now"', 250, true);
    await page.key('Enter');
    await waitSaved(page);
    await tabTo('el.id === "source-back"', 250, true);
    await page.key('Enter');
    await page.waitFor('document.activeElement?.id === "row-ux-e-unicode"');
    await tabTo('el.getAttribute("href")?.endsWith("/export") && el.closest("nav")');
    await page.key('Enter');
    await page.waitFor('document.getElementById("export-download")');
    await tabTo('el.id === "export-download"');
    await page.key('Enter');
    await page.waitFor('document.getElementById("export-status")');
    return { firstStop, focusOutline: outline, focusRestoredTo: 'row-ux-e-unicode' };
  }),

  record('E13-responsive-themes-screens', ['US-27'], async ({ page }) => {
    const shots = [];
    const routes = [['overview', ''], ['evidence', '/evidence'], ['source', '/source/ux-synthetic-unicode?evidenceId=ux-e-unicode'], ['history', '/history'], ['export', '/export']];
    for (const width of [320, 768, 1280]) {
      await page.setViewport(width);
      for (const [name, path] of routes) {
        await page.hash(`#/project/${state.pid}${path}`);
        await a11yAudit(page, `${name}@${width}`);
      }
    }
    for (const locale of ['th', 'en']) {
      await page.eval(`var s = document.getElementById("pref-locale"); s.value = ${JSON.stringify(locale)}; s.dispatchEvent(new Event("change"))`);
      for (const theme of ['formal-light', 'formal-dark', 'kmitl-inspired', 'ict-inspired']) {
        await page.eval(`var s = document.getElementById("pref-theme"); s.value = ${JSON.stringify(theme)}; s.dispatchEvent(new Event("change"))`);
        for (const width of [320, 1280]) {
          await page.setViewport(width);
          await page.hash(`#/project/${state.pid}/evidence`);
          shots.push(await page.screenshot(join(SHOTS, `E13-evidence-${locale}-${theme}-${width}.jpg`)));
        }
      }
    }
    await page.setViewport(768);
    await page.hash(`#/project/${state.pid}/history`);
    shots.push(await page.screenshot(join(SHOTS, 'E13-history-en-768.jpg')));
    await page.setViewport(1280);
    return { screenshots: shots.length, widths: [320, 768, 1280], note: '320 CSS px approximates 400% zoom of 1280; 640 is not separately measured' };
  }),

  record('E14-corrupt-history-and-delete', ['US-19', 'US-28'], async (ctx) => {
    const { page } = ctx;
    await page.goto(`${base}/`);
    await page.click('#start-demo-empty');
    await page.waitFor('document.getElementById("candidate-scope")');
    const emptyScope = await page.eval('document.getElementById("candidate-scope").dataset.scope');
    const pid = await projectIdOf(page);
    await page.eval(`(async () => {
      const db = await new Promise((ok, bad) => { const r = indexedDB.open('p2p-healthtech-ux'); r.onsuccess = () => ok(r.result); r.onerror = () => bad(r.error); });
      const tx = db.transaction(['projects', 'snapshots'], 'readwrite');
      const p = await new Promise((ok) => { const r = tx.objectStore('projects').get(${JSON.stringify(pid)}); r.onsuccess = () => ok(r.result); });
      tx.objectStore('snapshots').put({ snapshotId: 'snap-corrupt', projectId: p.projectId, parentSnapshotId: 'snap-missing', savedAt: '2026-10-30T00:00:00Z', overlay: { notes: [], featureLinks: [], requestDrafts: [] } });
      tx.objectStore('projects').put({ ...p, headSnapshotId: 'snap-corrupt' });
      await new Promise((ok) => { tx.oncomplete = ok; }); db.close(); return true; })()`);
    await page.goto(`${base}/#/project/${pid}`);
    await page.waitFor('document.getElementById("corrupt-panel")');
    const r = await page.eval(`({ status: document.getElementById('save-status').dataset.state, disabled: [...document.querySelectorAll('main textarea, #add-note-dossier')].every(e => e.disabled), text: document.getElementById('corrupt-panel').textContent })`);
    assert(r.status === 'readonly' && r.disabled && r.text.includes('snap-missing'), 'FX-13 quarantined read-only, reason shown, no repair');
    await page.click('#download-recovery');
    const rec = JSON.parse(readFileSync(grab(await waitForDownload(DL, 'UX-DEMO-001-recovery.json'), 'E14-corrupt-recovery.json'), 'utf8'));
    await page.screenshot(join(SHOTS, 'E14-corrupt-readonly.jpg'));
    await page.goto(`${base}/`);
    const count = await page.eval('window.__healthtechApp.state.projects.length');
    await page.click(`[id="del-${pid}"]`);
    const msg = await page.eval(`document.getElementById('del-msg-${pid}').textContent`);
    await page.click(`[id="del-confirm-${pid}"]`);
    await page.waitFor(`window.__healthtechApp.state.projects.length === ${count - 1}`);
    const remaining = await page.eval('window.__healthtechApp.state.projects.map(p => p.projectId)');
    assert(!remaining.includes(pid) && remaining.includes(state.pid), 'only the selected local project deleted');
    return { emptyScope, corrupt: r.status, recoveryOmissions: rec.omissions ?? null, deleteMessage: msg, remaining: remaining.length };
  }),
];

scenarios.push(record('E17-navigation-tour-tutorial', ['US-26', 'US-27'], async ({ page }) => {
  await page.setViewport(1280, 900); // independent of any earlier scenario's viewport
  await page.goto(`${base}/#/project/${state.pid}`);
  await page.waitFor('document.querySelector(".journey")');
  await page.waitFor('!window.__healthtechApp.state.current.pipe.running', 15000);
  const j = await page.eval(`({ current: document.querySelector('.jstep[aria-current=step]')?.id, done: [...document.querySelectorAll('.jstep')].map(s => s.dataset.done),
    crumbs: [...document.querySelectorAll('.breadcrumb li')].map(l => l.textContent), next: document.getElementById('journey-next')?.getAttribute('href') })`);
  assert(j.current === 'jstep-review' && j.done[0] === 'true' && j.crumbs.length === 3, `journey: ${JSON.stringify(j)}`);
  // Real pointer drag: open issue → Requests node creates a draft; Esc mid-drag changes nothing.
  const center = (sel) => page.eval(`(() => { const el = document.querySelector(${JSON.stringify(sel)}); el.scrollIntoView({ block: 'center' }); const b = el.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; })()`);
  const mouse = (type, p) => page.send('Input.dispatchMouseEvent', { type, x: p.x, y: p.y, button: 'left', buttons: type === 'mouseReleased' ? 0 : 1, clickCount: type === 'mouseMoved' ? 0 : 1 });
  const drafts = () => page.eval('window.__healthtechApp.state.current.overlay.requestDrafts.length');
  const dragTo = async (fromSel, toSel, cancel = false) => {
    const a = await center(fromSel), b = await center(toSel);
    a.hit = await page.eval(`String(document.elementFromPoint(${a.x}, ${a.y})?.className || 'none') + ' @' + ${Math.round(a.x)} + ',' + ${Math.round(a.y)} + ' vw=' + innerWidth + 'x' + innerHeight`);
    await mouse('mousePressed', a);
    for (let i = 1; i <= 12; i++) await mouse('mouseMoved', { x: a.x + ((b.x - a.x) * i) / 12, y: a.y + ((b.y - a.y) * i) / 12 });
    const hover = await page.eval('({ over: !!document.querySelector(".drop-over"), ghost: !!document.querySelector(".drag-ghost"), valid: document.querySelectorAll(".drop-valid").length })');
    hover.hit = a.hit;
    if (cancel) await page.key('Escape', 'Escape', 27);
    await mouse('mouseReleased', b);
    await sleep(500);
    return hover;
  };
  const d0 = await drafts();
  const cancelled = await dragTo('.lib-card.lib-gap .lib-handle', '#node-requests', true);
  const d1 = await drafts();
  const dropped = await dragTo('.lib-card.lib-gap .lib-handle', '#node-requests');
  const d2 = await drafts();
  assert(cancelled.ghost && cancelled.over && d1 === d0, `Esc cancels drag: ${JSON.stringify({ cancelled, d0, d1 })}`);
  assert(dropped.ghost && dropped.over && dropped.valid >= 1 && d2 === d0 + 1, `pointer drop adds a request: ${JSON.stringify({ dropped, d0, d2 })}`);
  // Panels: keyboard splitter resize, float via menu, dock back.
  const left0 = await page.eval('window.__healthtechApp.layout.zones.left.size');
  await page.eval('document.querySelector(".splitter-left").focus()');
  await page.key('ArrowRight', 'ArrowRight', 39);
  const left1 = await page.eval('window.__healthtechApp.layout.zones.left.size');
  await page.click('#move-timeline-float');
  const floated = await page.eval('({ float: !!window.__healthtechApp.layout.floating.timeline, win: !!document.querySelector(".float-window") })');
  await page.click('#move-timeline-bottom');
  const docked = await page.eval('window.__healthtechApp.layout.zones.bottom.panels.includes("timeline") && !document.querySelector(".float-window")');
  assert(left1 === left0 + 24 && floated.float && floated.win && docked, `panels: ${JSON.stringify({ left0, left1, floated, docked })}`);
  await page.eval('window.__healthtechApp.resetLayout()');
  // Guided tour: keyboard through steps, Esc closes, focus returns to the opener.
  await page.eval('document.getElementById("tour-start").focus()');
  await page.key('Enter');
  await page.waitFor('document.querySelector(".tour-pop")');
  const t1 = await page.eval('({ title: document.getElementById("tour-title").textContent, focus: document.activeElement.id, count: document.querySelector(".tour-count").textContent })');
  await page.key('ArrowRight', 'ArrowRight', 39);
  await page.key('ArrowRight', 'ArrowRight', 39);
  const t3 = await page.eval('({ step: document.querySelector(".tour").dataset.step, spot: (() => { const r = document.querySelector(".tour-spot").getBoundingClientRect(); return r.width > 0 && r.height > 0; })() })');
  await page.screenshot(join(SHOTS, 'E17-tour.jpg'));
  await page.key('Escape', 'Escape', 27);
  const after = await page.eval('({ open: !!document.querySelector(".tour"), focus: document.activeElement.id })');
  assert(t1.focus === 'tour-title' && t1.title && t3.step === 'node' && t3.spot && !after.open && after.focus === 'tour-start', `tour: ${JSON.stringify({ t1, t3, after })}`);
  // Tutorial dialog: opens modally, chapters listed, chapter seeks the video when it exists.
  await page.click('#tutorial-open');
  await page.waitFor('document.querySelector("dialog.tutorial[open]")');
  const tut = await page.eval('({ chapters: document.querySelectorAll(".chapter").length, video: !!document.getElementById("tutorial-video"), missing: !!document.getElementById("tutorial-missing") })');
  assert(tut.chapters === 5 && (tut.video || tut.missing), `tutorial: ${JSON.stringify(tut)}`);
  let seek = null;
  if (tut.video) {
    await page.waitFor('document.getElementById("tutorial-video").readyState >= 1', 10000);
    await page.eval('document.querySelectorAll(".chapter")[2].click(); document.getElementById("tutorial-video").pause()');
    await sleep(300);
    seek = await page.eval('({ t: document.getElementById("tutorial-video").currentTime, start: Number(document.querySelectorAll(".chapter")[2].dataset.start), dur: document.getElementById("tutorial-video").duration })');
    assert(Math.abs(seek.t - seek.start) < 1 && seek.dur > 30, `chapter seek: ${JSON.stringify(seek)}`);
  }
  await page.screenshot(join(SHOTS, 'E17-tutorial.jpg'));
  await page.key('Escape', 'Escape', 27);
  const closed = await page.eval('({ open: !!document.querySelector("dialog.tutorial"), focus: document.activeElement.id })');
  assert(!closed.open && closed.focus === 'tutorial-open', `tutorial close: ${JSON.stringify(closed)}`);
  return { journey: j, tour: { t1, t3, after }, tutorial: { ...tut, seek } };
}));

// Fault-injection scenarios use their own clean profiles.
const isolated = [
  record('E15-storage-denied-FX07', ['US-17', 'US-28', 'US-25'], async ({ page }) => {
    await page.goto(`${base}/?simulate=storage-denied#/`);
    const scope = await page.eval('window.__healthtechApp.state.storageScope');
    await page.click('#start-demo');
    await page.waitFor('document.getElementById("save-status")');
    await addNoteOnOverview(page, 'LOCAL_UNSAVED_NOTE');
    await page.click('#save-now');
    await page.waitFor('document.getElementById("save-status").dataset.state === "memory"');
    const label = await page.eval('document.getElementById("save-status").textContent');
    await page.click('#download-recovery');
    const rec = readFileSync(await waitForDownload(join(DL, 'fx07'), 'UX-DEMO-001-recovery.json'), 'utf8');
    await page.hash(`#/project/${await projectIdOf(page)}/source/ux-synthetic-unicode?evidenceId=ux-e-unicode`);
    const src = await page.eval('document.getElementById("source-span")?.textContent');
    assert(scope === 'memory' && !/Saved in this browser|บันทึกในเบราว์เซอร์นี้แล้ว/.test(label) && rec.includes('LOCAL_UNSAVED_NOTE') && src === '🙂', 'memory-only label, recovery has text, source inspection works');
    await page.screenshot(join(SHOTS, 'E15-storage-denied.jpg'));
    return { scope, label };
  }, 'fx07'),

  record('E16-quota-FX09', ['US-28', 'US-17', 'US-25'], async ({ page }) => {
    await page.goto(`${base}/?simulate=quota#/`);
    await page.click('#start-demo');
    await page.waitFor('document.getElementById("save-status")?.dataset.state === "saved"');
    const fieldId = await addNoteOnOverview(page, 'QUOTA_RECOVERY_NOTE');
    await page.click('#save-now');
    await page.waitFor('document.getElementById("save-status").dataset.state === "quota"');
    const text = await page.eval(`document.getElementById(${JSON.stringify(fieldId)}).value`);
    await page.click('#download-recovery');
    const rec = readFileSync(await waitForDownload(join(DL, 'fx09'), 'UX-DEMO-001-recovery.json'), 'utf8');
    const head = await page.eval('window.__healthtechApp.state.current.project.headSnapshotId');
    const stored = await storeHead(page, await projectIdOf(page));
    assert(text === 'QUOTA_RECOVERY_NOTE' && rec.includes('QUOTA_RECOVERY_NOTE') && stored.head === head && !stored.snaps.some((s) => s.texts.includes('QUOTA_RECOVERY_NOTE')), 'quota: text kept in tab + recovery, nothing falsely committed');
    await page.screenshot(join(SHOTS, 'E16-quota.jpg'));
    return { state: 'quota', storedSnapshots: stored.count };
  }, 'fx09'),
];

async function main() {
  server = await startServer(0);
  base = `http://127.0.0.1:${server.address().port}`;
  const profile = join(WORK, 'profile-main');
  const ctx = {};
  ctx.browser = await launch(profile);
  await allowDownloads(ctx.browser, DL);
  ctx.page = await ctx.browser.newPage();
  const version = await ctx.browser.version();
  ctx.restart = async () => {
    await ctx.browser.close();
    ctx.browser = await launch(profile);
    await allowDownloads(ctx.browser, DL);
    ctx.page = await ctx.browser.newPage();
  };
  const run = async (s, c) => {
    const started = Date.now();
    try {
      const details = await s.fn(c);
      results.push({ id: s.id, stories: s.stories, result: 'PASS', ms: Date.now() - started, details, pageErrors: c.page.errors.splice(0) });
    } catch (e) {
      const shot = join(SHOTS, `${s.id}-FAILURE.jpg`);
      try { await c.page.screenshot(shot); } catch { /* ignore */ }
      results.push({ id: s.id, stories: s.stories, result: 'FAIL', ms: Date.now() - started, error: e.message, pageErrors: c.page.errors.splice(0) });
    }
    console.log(`${results.at(-1).result}  ${s.id}${results.at(-1).error ? `  — ${results.at(-1).error}` : ''}`);
  };
  for (const s of scenarios) await run(s, ctx);
  await ctx.browser.close();
  for (const s of isolated) {
    const b = await launch(join(WORK, `profile-${s.id}`));
    await allowDownloads(b, join(DL, s.dl));
    const c = { browser: b, page: await b.newPage() };
    await run(s, c);
    await b.close();
  }
  server.close();
  const summary = {
    generatedAt: new Date().toISOString(),
    command: 'npm run test:e2e (frontend/healthtech-web)',
    candidate: { branch: git('rev-parse --abbrev-ref HEAD'), head: git('rev-parse HEAD'), dirtyFrontend: Boolean(git('status --porcelain -- frontend')) },
    browser: { product: version.product, executable: ctx.browser.exe, headless: true },
    node: process.version,
    profile: 'fresh temporary Chrome profile (deleted after run); real IndexedDB',
    publicRunDir: existsSync(join(PUBLIC_DIR, 'dossier.json')) ? PUBLIC_DIR : 'NOT_AVAILABLE',
    totals: { pass: results.filter((r) => r.result === 'PASS').length, fail: results.filter((r) => r.result === 'FAIL').length },
    results,
  };
  writeFileSync(join(OUT, 'results.json'), `${JSON.stringify(summary, null, 2)}\n`);
  rmSync(WORK, { recursive: true, force: true });
  console.log(`\n${summary.totals.pass} passed, ${summary.totals.fail} failed → ${join(OUT, 'results.json')}`);
  process.exitCode = summary.totals.fail ? 1 : 0;
}

main().catch((e) => { console.error(e); process.exitCode = 2; });
