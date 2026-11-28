import data from './generated/release.json' with { type: 'json' };
import pin from './generated/pin.json' with { type: 'json' };

export type Snapshot = { release_id: string; mode: 'track_a_t0' | 'development'; as_of: string; horizon: number };
type Choice = Omit<Snapshot, 'release_id'> & {
  status: string; label: string; jurisdiction: 'US';
  freeze_tag: string | null; freeze_manifest_sha256: string | null; queue: string;
};
export type Selection = Omit<Choice, 'queue'> & { release_id: string };
export type Manifest = {
  release_id: string; choices: Choice[]; disclaimer: { th: string; en: string };
  shards: Record<string, string>;
};
export type Bundle = { manifest: string; texts: Record<string, string> };
type Localized = { th: string; en: string };
type Ref = { id: string; version: string; locator: string; url: string | null };
export type Source = Ref & { issuer: string; title: string; public_date: string | null; sha256: string | null;
  retrieved: string | null; evidence_cutoff: string | null };
type Linked = Localized & { id: string; source_ids: string[] };
type Claim = Linked & { section: string; kind: string; state: string; jurisdiction: string; time_basis: string; horizon: number | null };
type Task = Linked & { owner: string; state: string; agency: string | null; lookup_url: string | null };
export type Dossier = { claims: Claim[]; checklist: Task[]; sources: Record<string, Source> };
export type QueueRow = { key: string; display_name: string; rank: number; score: number; included: boolean;
  inclusion_probability: number | null; dossier: string | null };
export type Queue = { rows: QueueRow[]; search_order: number[]; slots: number; version: string; window_end: string };
export type Method = Localized & { id: string; [key: string]: unknown };

export async function sha256(text: string) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}

export class ReleaseMismatch extends Error {}

export function openRelease(bundle: Bundle = data, expected = pin.manifest_sha256) {
  // Keep large dossier shards as strings until a caller selects a dossier.
  // The immutable build validates every input before either adapter is launched.
  let manifestPromise: Promise<Manifest> | undefined;
  const manifest = () => manifestPromise ??= (async () => {
    if (await sha256(bundle.manifest) !== expected) throw new ReleaseMismatch();
    return JSON.parse(bundle.manifest) as Manifest;
  })();
  const queueCache = new Map<string, Promise<Queue>>();
  async function shard<T>(path: string): Promise<T> {
    const contents = Object.hasOwn(bundle.texts, path) ? bundle.texts[path] : undefined;
    const digest = (await manifest()).shards[path];
    if (contents === undefined || !digest || await sha256(contents) !== digest) throw new ReleaseMismatch();
    return JSON.parse(contents) as T;
  }
  function queue(path: string) {
    let entry = queueCache.get(path);
    if (!entry) {
      entry = shard<Queue>(path);
      queueCache.set(path, entry);
    }
    return entry;
  }
  let lastDossier: { path: string; value: Promise<Dossier> } | undefined;
  function dossier(path: string) {
    if (lastDossier?.path !== path) lastDossier = { path, value: shard<Dossier>(path) };
    return lastDossier.value;
  }
  return { manifest, shard, queue, dossier, manifestSha256: expected, disclaimer: pin.disclaimer };
}
export const release = openRelease();
export type Release = ReturnType<typeof openRelease>;
