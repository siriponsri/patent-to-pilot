import { Validator, type Schema } from '@cfworker/json-schema';
import { bytes, DEFAULT_ROWS, INPUT_BYTES, isName, names, reasons, registry, RESULT_BYTES, type Name, type Reason } from './registry.js';
import { release, sha256, ReleaseMismatch, type Method, type Release, type Selection, type Snapshot } from './release.js';

type Args = {
  snapshot?: Snapshot; language?: 'th' | 'en'; limit?: number; cursor?: string;
  query?: string; scope?: 'selected' | 'all'; molecule_key?: string;
  section?: string; claim_ids?: string[]; source_ids?: string[]; owner?: string;
};

const validators = Object.fromEntries(names.map(name => [name, new Validator(registry[name].inputSchema as Schema, '2020-12', true)]));
// The pinned modern SDK adds resultType and protocol metadata after the handler.
const SDK_RESULT_HEADROOM = 512;
export type Observation = { tool: Name; reason: Reason | 'OK'; release: string | null; latency_band: string; count: 1 };
type Observer = (observation: Observation) => void;

function envelope(selection: Selection | null, releaseId: string | null, manifestHash: string | null, disclaimer: Release['disclaimer'], language: 'en' | 'th') {
  return {
    api_version: '1.0', release_id: releaseId, manifest_sha256: manifestHash,
    snapshot: selection ? {
      release_id: selection.release_id, mode: selection.mode, as_of: selection.as_of, horizon: selection.horizon,
    } : null,
    as_of: selection?.as_of ?? null, mode: selection?.mode ?? null, horizon: selection?.horizon ?? null,
    status: selection?.status ?? null, jurisdiction: selection?.jurisdiction ?? null, label: selection?.label ?? null,
    freeze_tag: selection?.freeze_tag ?? null, freeze_manifest_sha256: selection?.freeze_manifest_sha256 ?? null,
    disclaimer, language,
  };
}
type Page = ReturnType<typeof envelope> & {
  rows: Record<string, unknown>[]; snapshot_choices: Snapshot[]; next_cursor: string | null;
  queue: { capacity: 0.2; denominator: number; slots: number; window_end: string } | null;
  error: { reason: Reason; retryable: boolean; message: string } | null;
};

export function wire(page: Page) {
  return {
    isError: page.error !== null, structuredContent: page,
    content: [{ type: 'text' as const, text: JSON.stringify(page) }],
  };
}

class ReadError extends Error {
  constructor(readonly reason: Reason) { super(reasons[reason]); }
}

const fold = (value: string) => value.toLowerCase();

function errorPage(meta: ReturnType<typeof envelope>, reason: Reason): Page {
  return {
    ...meta, rows: [], next_cursor: null, snapshot_choices: [], queue: null,
    error: { reason, retryable: reason === 'STALE_CURSOR', message: reasons[reason] },
  };
}

export function reader(data: Release = release, observe?: Observer) {
  return async function read(name: Name, raw: unknown): Promise<Page> {
    if (!isName(name)) throw new Error('Unregistered operation');
    const started = performance.now();
    const language = (raw as Args | null)?.language === 'th' ? 'th' : 'en';
    let meta = envelope(null, null, null, data.disclaimer, language);
    let outcome: Reason | 'OK' = 'OK';
    try {
      const manifest = await data.manifest();
      meta = envelope(null, manifest.release_id, data.manifestSha256, data.disclaimer, language);
      const choices = manifest.choices.map(({ mode, as_of, horizon }) => ({ mode, as_of, horizon, release_id: manifest.release_id }));
      const defaultChoice = manifest.choices.find(choice => choice.mode === 'track_a_t0' && choice.horizon === 24);
      if (!defaultChoice) throw new ReleaseMismatch();
      const requested = (raw as Args | null)?.snapshot;
      const choice = requested === undefined && name === 'search_drugs' ? defaultChoice :
        manifest.choices.find(entry => requested?.release_id === manifest.release_id &&
          requested.mode === entry.mode && requested.as_of === entry.as_of && requested.horizon === entry.horizon);
      if (choice) {
        const { queue, ...selection } = choice;
        meta = envelope({ ...selection, release_id: manifest.release_id }, manifest.release_id, data.manifestSha256, data.disclaimer, language);
      }
      if (bytes(JSON.stringify(raw ?? {})) > INPUT_BYTES) throw new ReadError('INPUT_TOO_LARGE');
      if (!validators[name].validate(raw).valid) throw new ReadError('INVALID_ARGUMENTS');
      const args = raw as Args;
      if (requested && requested.release_id !== manifest.release_id) throw new ReadError('RELEASE_MISMATCH');
      if (requested && requested.horizon !== 12 && requested.horizon !== 24) throw new ReadError('UNSUPPORTED_HORIZON');
      if (!choice || !meta.snapshot) throw new ReadError('SNAPSHOT_UNAVAILABLE');

      const scope = args.scope ?? 'selected';
      const query = fold(args.query ?? '');
      const limit = args.limit ?? DEFAULT_ROWS;
      const binding = await sha256(JSON.stringify([
        data.manifestSha256, choice.queue, name, language, limit, query, scope, args.molecule_key ?? null,
        args.section ?? null, args.claim_ids ?? null, args.source_ids ?? null, args.owner ?? null,
      ]));
      const cursorFor = async (index: number) => (await sha256(binding + ':' + index)) + '_' + index.toString(36);
      const offset = args.cursor ? Number.parseInt(args.cursor.slice(65), 36) : 0;
      if (args.cursor && (!Number.isSafeInteger(offset) || offset < 1 || args.cursor !== await cursorFor(offset))) {
        throw new ReadError('STALE_CURSOR');
      }

      const page: Page = { ...meta, rows: [], next_cursor: null, error: null, queue: null,
        snapshot_choices: name === 'search_drugs' ? choices : [] };
      // A future B2 operation can be registered here and use the same snapshot and claim reader.
      let rows: Record<string, unknown>[];
      if (name === 'get_method_card') {
        rows = (await data.shard<Method[]>('method-card.json')).map(({ th, en, ...row }) => ({ ...row, text: language === 'th' ? th : en }));
      } else {
        const queue = await data.queue(choice.queue);
        const artifact = manifest.shards[choice.queue];
        if (name === 'search_drugs' || name === 'get_queue') {
          const queueRef = (row: typeof queue.rows[number]) => ({
            key: row.key, display_name: row.display_name, dossier_available: row.dossier !== null,
            evidence: { id: 'queue-row', version: queue.version,
              locator: 'rows[rank=' + row.rank + ']', artifact_sha256: artifact, url: null },
          });
          if (name === 'search_drugs') {
            rows = queue.search_order.map(index => queue.rows[index])
              .filter(row => fold(row.display_name).includes(query) || fold(row.key).includes(query)).map(queueRef);
          } else {
            page.queue = { capacity: 0.2, denominator: queue.rows.length, slots: queue.slots, window_end: queue.window_end };
            rows = queue.rows.filter(row => scope === 'all' || row.included).map(row => ({
              ...queueRef(row), rank: row.rank, score: row.score, included: row.included, inclusion_probability: row.inclusion_probability,
            }));
          }
        } else {
          const row = queue.rows.find(entry => entry.key === args.molecule_key);
          if (!row) throw new ReadError('UNKNOWN_MOLECULE');
          if (!row.dossier) throw new ReadError('DOSSIER_UNAVAILABLE');
          const dossier = await data.dossier(row.dossier);
          const artifact_sha256 = manifest.shards[row.dossier];
          const claims = dossier.claims.filter(claim => claim.horizon === null || claim.horizon === choice.horizon);
          const localRef = (id: string) => {
            const { version, locator, url } = dossier.sources[id];
            return { id, version, locator, url, artifact_sha256 };
          };
          if (name === 'get_dossier') {
            const section = claims.filter(claim => !args.section || claim.section === args.section);
            if (args.claim_ids?.some(id => !section.some(claim => claim.id === id))) throw new ReadError('UNKNOWN_CLAIM');
            rows = section.filter(claim => !args.claim_ids || args.claim_ids.includes(claim.id)).map(claim => ({
              id: claim.id, section: claim.section, text: claim[language], kind: claim.kind, state: claim.state,
              jurisdiction: claim.jurisdiction, time_basis: claim.time_basis, evidence: claim.source_ids.map(localRef),
            }));
          } else if (name === 'get_fto_checklist') {
            rows = dossier.checklist.filter(task => !args.owner || task.owner === args.owner).map(task => ({
              id: task.id, owner: task.owner, next_question: task[language], agency: task.agency, lookup_url: task.lookup_url,
              state: task.state, evidence: task.source_ids.map(localRef),
            }));
          } else {
            const visible = new Set([...claims, ...dossier.checklist].flatMap(item => item.source_ids));
            if (args.source_ids?.some(id => !visible.has(id))) throw new ReadError('UNKNOWN_SOURCE');
            rows = Object.values(dossier.sources).filter(source => visible.has(source.id) &&
              (!args.source_ids || args.source_ids.includes(source.id))).map(source => ({ ...source, artifact_sha256 }));
          }
        }
      }

      if (args.cursor && offset >= rows.length) throw new ReadError('STALE_CURSOR');
      const end = Math.min(rows.length, offset + limit);
      // Reserve a cursor of the longest required width. The base envelope has
      // empty arrays in both structured content and text. Add each record's
      // exact cost in both, including the extra JSON escaping in the text copy.
      page.next_cursor = binding + '_' + end.toString(36);
      let length = bytes(JSON.stringify(wire(page)));
      for (const row of rows.slice(offset, end)) {
        const json = JSON.stringify(row);
        length += bytes(json) + bytes(JSON.stringify(json)) - 2;
        if (page.rows.length) length += 2;
        if (length > RESULT_BYTES - SDK_RESULT_HEADROOM) break;
        page.rows.push(row);
      }
      if (!page.rows.length && offset < rows.length) throw new ReadError('ROW_TOO_LARGE');
      const next = offset + page.rows.length;
      page.next_cursor = next < rows.length ? await cursorFor(next) : null;
      return page;
    } catch (error) {
      if (error instanceof ReleaseMismatch) outcome = 'RELEASE_MISMATCH';
      else if (error instanceof ReadError) outcome = error.reason;
      else throw error;
      return errorPage(meta, outcome);
    } finally {
      const elapsed = performance.now() - started;
      observe?.({ tool: name, reason: outcome, release: meta.release_id, latency_band: elapsed < 2 ? '<2ms' : elapsed < 10 ? '2–10ms' : '>=10ms', count: 1 });
    }
  };
}
