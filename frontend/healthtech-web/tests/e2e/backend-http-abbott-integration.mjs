// Named Abbott cases -> browser -> loopback HTTP/vector -> history/export.
// The temporary DossierInput bundle is created outside the repository.
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
const CASE_IDS = ['HT-DEV-MITRACLIP', 'HT-DEV-TENDYNE', 'HT-DEV-TRICLIP'];
const EXTERNAL_BACKEND_URL = process.env.HEALTHTECH_ABBOTT_BACKEND_URL || null;

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required for named Abbott browser acceptance`);
  return value;
}

function waitForBackend(child) {
  return new Promise((resolvePort, reject) => {
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => reject(new Error(`backend did not announce a port: ${stderr.slice(-500)}`)), 30000);
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

const root = mkdtempSync(join(tmpdir(), 'healthtech-abbott-browser-'));
const casesPath = join(root, 'cases.json');
const backendRoot = join(root, 'backend');
const downloads = join(root, 'downloads');
mkdirSync(downloads);

const prep = spawn(PYTHON, [
  '-B', join(REPO, 'scripts/healthtech/prepare_http_browser_cases.py'),
  '--cohort', required('HEALTHTECH_ABBOTT_COHORT'),
  '--rights-matrix', required('HEALTHTECH_ABBOTT_RIGHTS_MATRIX'),
  '--output', casesPath,
], { cwd: REPO, stdio: ['ignore', 'pipe', 'pipe'] });
let prepErr = '';
prep.stderr.on('data', (chunk) => { prepErr += chunk; });
const prepCode = await new Promise((resolveCode) => prep.once('exit', resolveCode));
if (prepCode !== 0) throw new Error(`Abbott browser case preparation failed: ${prepErr.slice(-500)}`);
const cases = JSON.parse(readFileSync(casesPath, 'utf8'));
assert.deepEqual(cases.case_order, CASE_IDS);

function externalBackendUrl() {
  if (!EXTERNAL_BACKEND_URL) return null;
  const url = new URL(EXTERNAL_BACKEND_URL);
  if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1') {
    throw new Error('HEALTHTECH_ABBOTT_BACKEND_URL must be an http://127.0.0.1 loopback URL');
  }
  return url.toString().replace(/\/$/, '');
}

const backendArgs = [
  '-B', join(REPO, 'scripts/healthtech/serve_http.py'),
  '--host', '127.0.0.1', '--port', '0', '--data-dir', backendRoot,
  '--code-commit', process.env.HEALTHTECH_HTTP_COMMIT || 'e2e-abbott-uncommitted',
];
if (!EXTERNAL_BACKEND_URL) {
  backendArgs.push('--vector-config', required('HEALTHTECH_ABBOTT_VECTOR_CONFIG'));
  if (process.env.HEALTHTECH_ABBOTT_GENERATION_CONFIG) {
    backendArgs.push('--generation-config', process.env.HEALTHTECH_ABBOTT_GENERATION_CONFIG);
  }
}
const providerId = process.env.HEALTHTECH_ABBOTT_PROVIDER || 'local-vector';
const backendProcess = EXTERNAL_BACKEND_URL
  ? null
  : spawn(PYTHON, backendArgs, { cwd: REPO, stdio: ['ignore', 'pipe', 'pipe'] });

let webServer;
let browser;
const receipts = [];
try {
  const backendPort = backendProcess ? await waitForBackend(backendProcess) : null;
  webServer = await startServer(0);
  const webPort = webServer.address().port;
  const base = `http://127.0.0.1:${webPort}`;
  const backend = externalBackendUrl() || `http://127.0.0.1:${backendPort}`;
  browser = await launch(join(root, 'profile'));
  await browser.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: downloads, eventsEnabled: true });
  const page = await browser.newPage(`${base}/?backend=${encodeURIComponent(backend)}`);
  await page.waitFor('window.__healthtechApp?.state?.backend?.available === true', 30000);
  assert.deepEqual(page.errors, []);

  for (const caseId of CASE_IDS) {
    const input = cases.cases[caseId];
    await page.eval(`window.__healthtechApp.startBackendInput(${JSON.stringify(input)}, { providerId: ${JSON.stringify(providerId)} })`);
    await page.waitFor('location.hash.startsWith("#/project/") && window.__healthtechApp.state.current?.project?.origin?.type === "backend-http"', 120000);
    const project = await page.eval('({ pid: window.__healthtechApp.state.current.project.projectId, jobId: window.__healthtechApp.state.current.project.backendJobId, sourceId: window.__healthtechApp.state.current.dossier.query.selected_comparator_source_id, evidenceId: window.__healthtechApp.state.current.dossier.evidence.find((item) => item.source_id === window.__healthtechApp.state.current.dossier.query.selected_comparator_source_id)?.evidence_id || window.__healthtechApp.state.current.dossier.evidence[0]?.evidence_id, generation: window.__healthtechApp.state.current.project.backendGeneration, stem: window.__healthtechApp.state.current.dossier.query.device_id_canonical.replace(/[^A-Za-z0-9_-]/g, "_") })');
    assert.equal(project.jobId ? typeof project.jobId : 'missing', 'string');
    if (providerId === 'local-generation') assert.equal(project.generation?.schema_valid, true);

    await page.hash(`#/project/${project.pid}/source/${encodeURIComponent(project.sourceId)}?evidenceId=${encodeURIComponent(project.evidenceId)}`);
    await page.waitFor('document.getElementById("source-field") || document.getElementById("source-span")');
    assert.equal(await page.eval('Boolean(document.getElementById("source-mismatch"))'), false);

    await page.hash(`#/project/${project.pid}/history`);
    await page.waitFor('document.getElementById("backend-history-table")');
    await page.type('#backend-edit-note', `Reviewed ${caseId} through browser HTTP flow`);
    await page.click('#backend-edit');
    await page.waitFor('document.querySelector("#backend-history-table tbody tr[data-backend-version=\\"2\\"]")');

    await page.hash(`#/project/${project.pid}/export`);
    await page.waitFor('document.getElementById("backend-exports")');
    await page.click('#backend-export-json');
    const jsonPath = await waitForDownload(downloads, `${project.stem}-backend-v2-json.json`);
    const json = JSON.parse(readFileSync(jsonPath, 'utf8'));
    assert.equal(json.version, 2);
    assert.equal(json.user_edits.review_note, `Reviewed ${caseId} through browser HTTP flow`);

    receipts.push({
      case_id: caseId,
      job_id: project.jobId,
      provider: providerId,
      generation_schema_valid: project.generation?.schema_valid ?? null,
      source_inspection: 'PASS',
      history_versions: [1, 2],
      export_json_version: json.version,
    });
  }
  assert.deepEqual(page.errors, []);
  console.log(JSON.stringify({
    status: providerId === 'local-generation' ? 'PASS_BROWSER_HTTP_VECTOR_GENERATION_HISTORY_EXPORT' : 'PASS_BROWSER_HTTP_VECTOR_HISTORY_EXPORT',
    cases: receipts,
    provider_calls: 0,
    paid_cost_usd: 0,
  }, null, 2));
} finally {
  if (browser) await browser.close();
  if (webServer) webServer.close();
  if (backendProcess && backendProcess.exitCode === null) {
    backendProcess.kill();
    await new Promise((resolveExit) => backendProcess.once('exit', resolveExit));
  }
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try { rmSync(root, { recursive: true, force: true, maxRetries: 2, retryDelay: 100 }); break; }
    catch (error) {
      if (attempt === 79) console.warn(`test temp cleanup deferred for ${root}: ${error.code || error.message}`);
      else await new Promise((resolveRetry) => setTimeout(resolveRetry, 250));
    }
  }
}
