// Local adapters. FixtureAdapter serves authored synthetic data; file import is
// handled in the UI with core/validate.js. No adapter performs network requests
// beyond same-origin static files, and no run service exists.
import { parseLossless, toPlain, contentHash } from './core/pyjson.js';

export const ADAPTER = { id: 'healthtech-web-local', version: '0.1.0' };
export const HTTP_ADAPTER = { id: 'healthtech-local-http-v1', version: '0.1.0' };

/** Static capability manifest for this build; localDrafts is decided at runtime. */
export function capabilities(storageScope, backend = null) {
  const connected = Boolean(backend?.available);
  return {
    adapterId: ADAPTER.id,
    adapterVersion: ADAPTER.version,
    deviceCatalog: { available: true, scope: 'local authored synthetic catalog + comparators of imported local projects' },
    packageImport: { available: true },
    sourceInspect: { available: true },
    runStart: { available: connected, reason: connected ? null : 'cap.reason.runStart' },
    runControl: { cancel: connected, resume: connected, retry: connected, reason: connected ? null : 'cap.reason.runStart' },
    localDrafts: storageScope === 'indexeddb' ? { available: true, scope: 'indexeddb' } : { available: false, reason: 'cap.reason.localDrafts', scope: 'memory' },
    backendHistory: { available: connected, reason: connected ? null : 'cap.reason.backendHistory' },
    export: { recoveryJson: true, editedMarkdown: true, legacyBackendMarkdown: connected, pdf: false, docx: false },
    collaboration: { available: false, reason: 'cap.reason.collaboration' },
    analytics: { available: false, reason: 'cap.reason.analytics' },
  };
}

function loopbackUrl(value) {
  const url = new URL(value, globalThis.location?.origin || 'http://127.0.0.1');
  const host = url.hostname.toLowerCase();
  if (!['http:', 'https:'].includes(url.protocol) || !['127.0.0.1', 'localhost', '[::1]', '::1'].includes(host)) {
    throw new Error('backend URL must point to loopback');
  }
  url.pathname = `${url.pathname.replace(/\/$/, '')}/`;
  url.search = '';
  url.hash = '';
  return url;
}

function jobPath(jobId, suffix = '') {
  return `/jobs/${encodeURIComponent(jobId)}${suffix}`;
}

/**
 * Versioned loopback adapter. It never accepts an output path or arbitrary
 * command; the backend owns storage and the paid-provider gate.
 */
export function createBackendAdapter(baseUrl, fetchImpl = globalThis.fetch) {
  const root = loopbackUrl(baseUrl);
  if (typeof fetchImpl !== 'function') throw new Error('fetch is unavailable');
  const request = async (path, options = {}) => {
    const url = new URL(path.replace(/^\//, ''), root);
    const init = { method: options.method || 'GET', headers: { Accept: 'application/json', ...(options.headers || {}) } };
    if (options.body !== undefined) { init.headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(options.body); }
    const response = await fetchImpl(url, init);
    const contentType = response.headers?.get?.('content-type') || '';
    const value = contentType.includes('json') ? await response.json() : await response.text();
    if (!response.ok) {
      const error = new Error(value?.error?.message || `backend HTTP ${response.status}`);
      error.code = value?.error?.code || 'backend_error';
      error.status = response.status;
      error.details = value?.error?.details;
      throw error;
    }
    return value;
  };
  return {
    ...HTTP_ADAPTER,
    available: true,
    baseUrl: root.toString().replace(/\/$/, ''),
    health: () => request('/healthz'),
    providers: () => request('/providers'),
    submit: (input, { idempotencyKey, provider = { id: 'local' } } = {}) => request('/jobs', {
      method: 'POST', body: { input, provider }, headers: { 'Idempotency-Key': idempotencyKey },
    }),
    status: (jobId) => request(jobPath(jobId)),
    cancel: (jobId) => request(jobPath(jobId, '/cancel'), { method: 'POST', body: {} }),
    resume: (jobId) => request(jobPath(jobId, '/resume'), { method: 'POST', body: {} }),
    history: (jobId) => request(jobPath(jobId, '/history')),
    result: (jobId) => request(jobPath(jobId, '/result')),
    version: (jobId, version) => request(jobPath(jobId, `/history/${encodeURIComponent(version)}`)),
    edit: (jobId, version, edits) => request(jobPath(jobId, `/history/${encodeURIComponent(version)}/edits`), {
      method: 'POST', body: { edits, expected_parent_version: version },
    }),
    source: (jobId, sourceId, { version, field } = {}) => {
      const query = new URLSearchParams();
      if (version !== undefined) query.set('version', String(version));
      if (field) query.set('field', field);
      return request(jobPath(jobId, `/source/${encodeURIComponent(sourceId)}${query.toString() ? `?${query}` : ''}`));
    },
    export: (jobId, { version, format = 'json', language = 'auto', purpose = 'local_research' } = {}) => {
      const query = new URLSearchParams({ format, language, purpose });
      if (version !== undefined) query.set('version', String(version));
      return request(jobPath(jobId, `/export?${query}`));
    },
    async waitForTerminal(jobId, { pollMs = 250, signal } = {}) {
      for (;;) {
        if (signal?.aborted) throw new DOMException('backend wait aborted', 'AbortError');
        const value = await request(jobPath(jobId));
        const state = value?.job?.state;
        if (['succeeded', 'failed', 'cancelled'].includes(state)) return value;
        await new Promise((resolve) => setTimeout(resolve, pollMs));
      }
    },
  };
}

/** Read an optional loopback backend from the page query without enabling it by default. */
export function createBackendAdapterFromLocation(locationLike = globalThis.location, fetchImpl = globalThis.fetch) {
  const raw = new URLSearchParams(locationLike?.search || '').get('backend');
  return raw ? createBackendAdapter(raw, fetchImpl) : null;
}

async function getText(path) {
  const res = await fetch(path, { cache: 'no-store' });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.text();
}

export async function loadStatic() {
  const [fixtureText, catalogText, dossier, manifest, event] = await Promise.all([
    getText('fixtures/ui-fixtures.json'), getText('fixtures/synthetic-catalog.json'),
    getText('schemas/DossierVersion.schema.json'), getText('schemas/RunManifest.schema.json'), getText('schemas/AcquisitionEvent.schema.json'),
  ]);
  return {
    fixtureText,
    fixtures: JSON.parse(fixtureText),
    catalogFile: JSON.parse(catalogText),
    schemas: { dossier: JSON.parse(dossier), manifest: JSON.parse(manifest), event: JSON.parse(event) },
  };
}

/** Tutorial video manifest (chapters, files, captions); null-safe when not yet rendered. */
export async function loadTutorialManifest() {
  return JSON.parse(await getText('media/tutorial.json'));
}

/** Lossless subtree of the authored fixture bundle (fresh copy each call). */
export function fixtureTree(fixtureText, key) {
  return parseLossless(fixtureText)[key];
}

function entryFromSource(s, extra) {
  const p = s.payload || {};
  return {
    deviceId: p.device_id || p.k_number || s.source?.source_id,
    deviceName: p.device_name || '',
    applicant: p.applicant || null,
    jurisdiction: s.jurisdiction,
    sourceType: s.source.source_type,
    sourceDate: s.source_date,
    sourceId: s.source.source_id,
    revision: s.source.version_label,
    sha256: s.source.sha256,
    synthetic: Boolean(s.synthetic),
    ...extra,
  };
}

/** Catalog = authored synthetic records + comparators of local dossier projects. */
export async function buildCatalog(staticData, projects) {
  const out = [];
  const demo = staticData.fixtures.synthetic_dossier;
  const demoSource = demo.sources.find((s) => s.source.source_id === demo.query.selected_comparator_source_id);
  out.push(entryFromSource(demoSource, { origin: 'authored fixture (ui-fixtures.json)', demoFixture: 'synthetic_dossier' }));
  for (const r of staticData.catalogFile.records) {
    const sha256 = await contentHash(r.payload);
    out.push(entryFromSource({ payload: r.payload, jurisdiction: r.jurisdiction, source_date: r.source_date, synthetic: true,
      source: { source_id: r.source_id, source_type: r.source_type, version_label: r.version_label, sha256, uri: r.uri } },
    { origin: 'authored catalog (synthetic-catalog.json)' }));
  }
  for (const p of projects) {
    if (p.kind !== 'dossier' || !p.comparator) continue;
    out.push({ ...p.comparator, origin: `local project ${p.title || p.projectId}`, projectId: p.projectId });
  }
  return out;
}

export function searchCatalog(catalog, text) {
  const needle = String(text).trim().toLowerCase();
  if (!needle) return catalog;
  return catalog.filter((e) => [e.deviceId, e.deviceName, e.applicant, e.sourceId].some((v) => v && String(v).toLowerCase().includes(needle)));
}

export function comparatorOf(dossierPlain) {
  const s = dossierPlain.sources.find((x) => x.source.source_id === dossierPlain.query.selected_comparator_source_id);
  return s ? entryFromSource(s, {}) : null;
}

export { toPlain };
