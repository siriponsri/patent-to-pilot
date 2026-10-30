// Local adapters. FixtureAdapter serves authored synthetic data; file import is
// handled in the UI with core/validate.js. No adapter performs network requests
// beyond same-origin static files, and no run service exists.
import { parseLossless, toPlain, contentHash } from './core/pyjson.js';

export const ADAPTER = { id: 'healthtech-web-local', version: '0.1.0' };

/** Static capability manifest for this build; localDrafts is decided at runtime. */
export function capabilities(storageScope) {
  return {
    adapterId: ADAPTER.id,
    adapterVersion: ADAPTER.version,
    deviceCatalog: { available: true, scope: 'local authored synthetic catalog + comparators of imported local projects' },
    packageImport: { available: true },
    sourceInspect: { available: true },
    runStart: { available: false, reason: 'cap.reason.runStart' },
    runControl: { cancel: false, resume: false, retry: false, reason: 'cap.reason.runStart' },
    localDrafts: storageScope === 'indexeddb' ? { available: true, scope: 'indexeddb' } : { available: false, reason: 'cap.reason.localDrafts', scope: 'memory' },
    backendHistory: { available: false, reason: 'cap.reason.backendHistory' },
    export: { recoveryJson: true, editedMarkdown: true, legacyBackendMarkdown: false, pdf: false, docx: false },
    collaboration: { available: false, reason: 'cap.reason.collaboration' },
    analytics: { available: false, reason: 'cap.reason.analytics' },
  };
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
