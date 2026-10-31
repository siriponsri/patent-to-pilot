// Real browser -> static frontend -> loopback HTTP backend acceptance.
// Uses only the authored synthetic fixture and a temporary backend root.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { launch, waitForDownload } from './cdp.mjs';
import { startServer } from '../../serve.mjs';

const here = fileURLToPath(new URL('.', import.meta.url));
const WEB = resolve(here, '../..');
const REPO = resolve(WEB, '../..');
const PYTHON = process.env.PYTHON || 'python';

function waitForBackend(child) {
  return new Promise((resolvePort, reject) => {
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => reject(new Error(`backend did not announce a port: ${stderr.slice(-500)}`)), 15000);
    child.stdout.on('data', (chunk) => {
      stdout += chunk;
      const match = /listening on http:\/\/127\.0\.0\.1:(\d+)/.exec(stdout);
      if (match) { clearTimeout(timer); resolvePort(Number(match[1])); }
    });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.once('exit', (code) => {
      if (!stdout.includes('listening on')) reject(new Error(`backend exited ${code}: ${stderr.slice(-500)}`));
    });
  });
}

const root = mkdtempSync(join(tmpdir(), 'healthtech-http-browser-'));
const backendRoot = join(root, 'backend');
const downloads = join(root, 'downloads');
mkdirSync(downloads);
const backendProcess = spawn(PYTHON, [
  '-B', join(REPO, 'scripts/healthtech/serve_http.py'),
  '--host', '127.0.0.1', '--port', '0', '--data-dir', backendRoot, '--delay-ms', '250',
  '--code-commit', process.env.HEALTHTECH_HTTP_COMMIT || 'e2e-uncommitted',
], { cwd: REPO, stdio: ['ignore', 'pipe', 'pipe'] });

let webServer;
let browser;
try {
  const backendPort = await waitForBackend(backendProcess);
  webServer = await startServer(0);
  const webPort = webServer.address().port;
  const base = `http://127.0.0.1:${webPort}`;
  const backend = `http://127.0.0.1:${backendPort}`;
  browser = await launch(join(root, 'profile'));
  await browser.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: downloads, eventsEnabled: true });
  const page = await browser.newPage(`${base}/?backend=${encodeURIComponent(backend)}`);
  await page.waitFor('window.__healthtechApp?.state?.backend?.available === true');
  assert.deepEqual(page.errors, []);

  await page.click('#start-device');
  await page.waitFor('document.querySelector(".device-card.card-synthetic")');
  await page.click('#use-device-0');
  await page.waitFor('document.getElementById("brief-continue")');
  await page.type('#brief-objective', 'Screen the named comparator against the local evidence corpus');
  await page.click('#brief-continue');
  await page.waitFor('document.getElementById("backend-run")');
  assert.equal(await page.eval('document.getElementById("backend-provider").value'), 'local');
  assert.equal(await page.eval('document.querySelector("#backend-provider option[value=openrouter]").disabled'), true);
  assert.equal(await page.eval('document.querySelector("#backend-provider option[value=local-generation]").disabled'), true);

  await page.click('#backend-start');
  await page.waitFor('window.__healthtechApp.state.backendJob?.job_id');
  await page.waitFor('document.getElementById("backend-cancel")');
  await page.click('#backend-cancel');
  await page.waitFor('window.__healthtechApp.state.backendJob?.state === "cancelled"', 20000);
  await page.waitFor('document.getElementById("backend-start")');
  await page.click('#backend-start');
  await page.waitFor('location.hash.startsWith("#/project/") && window.__healthtechApp.state.current?.project?.origin?.type === "backend-http"', 20000);
  const project = await page.eval('({ pid: window.__healthtechApp.state.current.project.projectId, jobId: window.__healthtechApp.state.current.project.backendJobId, sourceId: window.__healthtechApp.state.current.dossier.evidence[0].source_id, evidenceId: window.__healthtechApp.state.current.dossier.evidence[0].evidence_id, stem: window.__healthtechApp.state.current.dossier.query.device_id_canonical.replace(/[^A-Za-z0-9_-]/g, "_") })');

  await page.hash(`#/project/${project.pid}/source/${encodeURIComponent(project.sourceId)}?evidenceId=${encodeURIComponent(project.evidenceId)}`);
  await page.waitFor('document.getElementById("source-field") || document.getElementById("source-span")');
  assert.equal(await page.eval('Boolean(document.getElementById("source-mismatch"))'), false);

  await page.hash(`#/project/${project.pid}/history`);
  await page.waitFor('document.getElementById("backend-history-table")');
  await page.waitFor('document.getElementById("backend-version-view")');
  assert.equal(await page.eval('document.querySelectorAll("#backend-history-table tbody tr").length'), 1);
  await page.type('#backend-edit-note', 'Reviewed through the real loopback browser flow');
  const editControl = await page.eval('({ value: document.getElementById("backend-edit-note").value, disabled: document.getElementById("backend-edit").disabled, version: window.__healthtechApp.state.current.backendSelectedVersion })');
  assert.equal(editControl.disabled, false, JSON.stringify(editControl));
  await page.click('#backend-edit');
  try {
    await page.waitFor('document.querySelector("#backend-history-table tbody tr[data-backend-version=\\"2\\"]")');
  } catch (error) {
    const debug = await page.eval('({ history: window.__healthtechApp.state.current.backendHistory, loading: window.__healthtechApp.state.current.backendHistoryLoading, error: window.__healthtechApp.state.current.backendHistoryError, selected: window.__healthtechApp.state.current.backendSelectedVersion, note: window.__healthtechApp.state.current.backendEditNote })');
    throw new Error(`${error.message}; editControl=${JSON.stringify(editControl)}; debug=${JSON.stringify(debug)}`);
  }
  await page.waitFor('document.getElementById("backend-version-view").textContent.includes("Reviewed through the real loopback browser flow")');

  await page.hash(`#/project/${project.pid}/export`);
  await page.waitFor('document.getElementById("backend-exports")');
  await page.waitFor('document.getElementById("backend-export-version").value === "2"');
  await page.click('#backend-export-json');
  const jsonPath = await waitForDownload(downloads, `${project.stem}-backend-v2-json.json`);
  const json = JSON.parse(readFileSync(jsonPath, 'utf8'));
  assert.equal(json.version, 2);
  assert.equal(json.user_edits.review_note, 'Reviewed through the real loopback browser flow');
  await page.click('#backend-export-th');
  const thPath = await waitForDownload(downloads, `${project.stem}-backend-v2-th.md`);
  assert.match(readFileSync(thPath, 'utf8'), /แฟ้มหลักฐาน HealthTech/);
  await page.click('#backend-export-en');
  const enPath = await waitForDownload(downloads, `${project.stem}-backend-v2-en.md`);
  assert.match(readFileSync(enPath, 'utf8'), /HealthTech evidence dossier/);

  await page.goto(`${base}/?backend=${encodeURIComponent(backend)}#/project/${project.pid}/history`);
  await page.waitFor('document.getElementById("backend-history-table")');
  await page.waitFor('document.getElementById("backend-version-view").textContent.includes("Reviewed through the real loopback browser flow")');
  assert.deepEqual(page.errors, []);
  console.log(JSON.stringify({
    status: 'PASS_BROWSER_HTTP_BACKEND_HISTORY_EXPORT',
    job_id: project.jobId,
    backend_origin: 'loopback',
    source_inspection: 'PASS',
    history_versions: [1, 2],
    edit: 'PASS',
    exports: ['json', 'th', 'en'],
    provider_calls: 0,
    paid_cost_usd: 0,
  }, null, 2));
} finally {
  if (browser) await browser.close();
  if (webServer) webServer.close();
  if (backendProcess.exitCode === null) {
    backendProcess.kill();
    await new Promise((resolveExit) => backendProcess.once('exit', resolveExit));
  }
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try { rmSync(root, { recursive: true, force: true, maxRetries: 2, retryDelay: 100 }); break; }
    catch (error) {
      if (attempt === 79) {
        console.warn(`test temp cleanup deferred for ${root}: ${error.code || error.message}`);
        break;
      }
      await new Promise((resolveRetry) => setTimeout(resolveRetry, 250));
    }
  }
}
