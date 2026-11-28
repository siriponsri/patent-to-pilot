import type { JSONObject, Tool } from '@modelcontextprotocol/server';

export const INPUT_BYTES = 16 * 1024;
export const RESULT_BYTES = 64 * 1024;
export const DEFAULT_ROWS = 10;
export const MAX_ROWS = 25;
export const PROTOCOL = '2026-07-28';
export const LEGACY = '2025-11-25';
export const sectionIds = ['decision', 'market', 'competition', 'patents', 'thai_asean', 'handoff', 'references'] as const;
export const owners = ['BD', 'R&D', 'FTO evaluator'] as const;

const str = (maxLength = 2048) => ({ type: 'string' as const, minLength: 1, maxLength });
const enumOf = (...values: string[]) => ({ type: 'string' as const, enum: values });
const numeric = (type: 'number' | 'integer' = 'number') => ({ type });
const nullable = (schema: JSONObject) => ({ anyOf: [schema, { type: 'null' }] });
const array = (items: JSONObject, maxItems?: number) => ({ type: 'array' as const, items, ...(maxItems === undefined ? {} : { maxItems }) });
const closed = <P extends Record<string, JSONObject>>(properties: P, required = Object.keys(properties)) =>
  ({ type: 'object' as const, additionalProperties: false, properties, required });
const digest = { type: 'string' as const, pattern: '^[0-9a-f]{64}$' };
const date = { type: 'string' as const, pattern: '^\\d{4}-\\d{2}-\\d{2}$' };
const horizon = { type: 'integer' as const, enum: [12, 24] };
const mode = enumOf('track_a_t0', 'development');
const status = enumOf('TRACK_A_FROZEN', 'DEVELOPMENT_ONLY');
const lang = enumOf('th', 'en');
const id = str(160);
const key = str(256);
const snapshot = closed({ release_id: id, mode, as_of: date, horizon: numeric('integer') });
const selection = closed({ release_id: id, mode, as_of: date, horizon });
const pageInputs = {
  language: { ...lang, default: 'en' },
  limit: { type: 'integer', minimum: 1, maximum: MAX_ROWS, default: DEFAULT_ROWS },
  cursor: { type: 'string', pattern: '^[A-Za-z0-9_-]{1,128}$' },
};
const ids = { ...array(id, 20), minItems: 1, uniqueItems: true };
const evidence = closed({
  id, version: str(), locator: str(), artifact_sha256: digest, url: nullable(str()),
});
const source = closed({
  id, issuer: str(), title: str(), version: str(), public_date: nullable(date), locator: str(),
  url: nullable(str()), sha256: nullable(digest), retrieved: nullable(str()), evidence_cutoff: nullable(date),
  artifact_sha256: digest,
});
const references = array(evidence);
const queueEvidence = closed({
  key, display_name: str(), dossier_available: { type: 'boolean' }, evidence,
});

export const reasons = {
  INVALID_ARGUMENTS: 'Arguments do not match the tool schema.',
  INPUT_TOO_LARGE: 'Arguments exceed the byte limit.',
  RELEASE_MISMATCH: 'The requested release or its data is unavailable.',
  SNAPSHOT_UNAVAILABLE: 'This snapshot is unavailable. Use search_drugs to discover available snapshots.',
  UNSUPPORTED_HORIZON: 'Use a published horizon of 12 or 24 months.',
  STALE_CURSOR: 'Start a new page sequence using the same published snapshot and filters.',
  UNKNOWN_MOLECULE: 'The molecule key is unknown for this snapshot.',
  DOSSIER_UNAVAILABLE: 'This snapshot has a queue entry without a released dossier.',
  UNKNOWN_CLAIM: 'A requested claim is unavailable for this dossier view.',
  UNKNOWN_SOURCE: 'A requested source is unavailable for this dossier view.',
  ROW_TOO_LARGE: 'An individual record exceeds the result byte limit.',
} as const;

export type Reason = keyof typeof reasons;

function output(row: JSONObject) {
  return closed({
    api_version: enumOf('1.0'), release_id: nullable(id), manifest_sha256: nullable(digest),
    snapshot: nullable(selection), as_of: nullable(date), mode: nullable(mode), horizon: nullable(horizon),
    status: nullable(status), jurisdiction: nullable(enumOf('US')), label: nullable(str()),
    freeze_tag: nullable(id), freeze_manifest_sha256: nullable(digest),
    disclaimer: closed({ th: str(), en: str() }), language: lang,
    rows: array(row, MAX_ROWS), next_cursor: nullable(str(128)),
    snapshot_choices: array(selection, 25),
    queue: nullable(closed({ capacity: { const: 0.2 }, denominator: numeric('integer'), slots: numeric('integer'), window_end: date })),
    error: nullable(closed({
      reason: enumOf(...Object.keys(reasons)), retryable: { type: 'boolean' }, message: str(),
    })),
  });
}

const notice = ' Decision support only. Consult a qualified expert for legal and FTO review.';
const annotations = { readOnlyHint: true, openWorldHint: false, destructiveHint: false, idempotentHint: true };
function operation(name: string, description: string, inputSchema: Tool['inputSchema'], row: JSONObject): Tool {
  return { name, description: description + notice, inputSchema, outputSchema: output(row), annotations };
}

export const registry = {
  search_drugs: operation('search_drugs',
    'Search literal English names or molecule keys. Without a snapshot, use Track A t0 as of 2026-11-27 at 24 months. The response lists the exact released snapshot choices.',
    closed({ snapshot, query: str(128), ...pageInputs }, ['query']), queueEvidence),
  get_queue: operation('get_queue', 'Read a published M3 queue at capacity 0.20. Scope defaults to selected.',
    closed({ snapshot, capacity: { const: 0.2 }, scope: { ...enumOf('selected', 'all'), default: 'selected' }, ...pageInputs }, ['snapshot']),
    closed({ ...queueEvidence.properties, rank: numeric('integer'), score: numeric(), included: { type: 'boolean' }, inclusion_probability: nullable(numeric()) })),
  get_dossier: operation('get_dossier', 'Read released claims with dated references. Claim IDs are scoped to the release, snapshot and molecule.',
    closed({ snapshot, molecule_key: key, section: enumOf(...sectionIds), claim_ids: ids, ...pageInputs }, ['snapshot', 'molecule_key']),
    closed({ id, section: enumOf(...sectionIds), text: str(65536), state: enumOf('known', 'unknown', 'conflicting'),
      kind: enumOf('observed', 'estimate', 'assumption'), jurisdiction: enumOf('US', 'TH', 'target_country'),
      time_basis: enumOf('as_of', 'verification_required'), evidence: references })),
  get_sources: operation('get_sources', 'Read sources reachable from visible claims or checklist tasks. A missing upstream digest is null.',
    closed({ snapshot, molecule_key: key, source_ids: ids, ...pageInputs }, ['snapshot', 'molecule_key']), source),
  get_fto_checklist: operation('get_fto_checklist', 'Read verification tasks and their sources for the selected dossier.',
    closed({ snapshot, molecule_key: key, owner: enumOf(...owners), ...pageInputs }, ['snapshot', 'molecule_key']),
    closed({ id, owner: enumOf(...owners), next_question: str(65536), agency: nullable(str()),
      lookup_url: nullable(str()), state: enumOf('unknown'), evidence: references })),
  get_method_card: operation('get_method_card', 'Read registered historical results and the separately labelled Track A t0 status.',
    closed({ snapshot, ...pageInputs }, ['snapshot']),
    closed({ id, horizon: nullable(horizon), status: str(), endpoint: str(), unit: str(), numerator: nullable(numeric()),
      denominator: numeric('integer'), difference_pp: nullable(numeric()), ci95_pp: nullable(array(numeric(), 2)),
      text: str(), capacity: { const: 0.2 }, receipt_date: date, evidence })),
};
export type Name = keyof typeof registry;
export const names = Object.keys(registry) as Name[];
export const isName = (name: string): name is Name => Object.hasOwn(registry, name);
const utf8 = new TextEncoder();
export const bytes = (text: string) => utf8.encode(text).byteLength;
