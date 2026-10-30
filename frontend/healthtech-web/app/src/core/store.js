// Browser-local project snapshots with expected-parent compare-and-swap.
//
// One IndexedDB readwrite transaction covers {projects, snapshots, ops}, so the
// head check and the snapshot/head write are atomic across tabs of the same
// profile. "Saved" is reported only from transaction.oncomplete (strict
// durability). Local snapshot IDs are a separate namespace from backend
// DossierVersion numbers, which are never changed here.

export const DB_NAME = 'p2p-healthtech-ux';
export const DB_VERSION = 1;

const ok = (value) => ({ ok: true, value });
const fail = (code, message, extra = {}) => ({ ok: false, code, message, ...extra });

function storageCode(error) {
  const name = error?.name || '';
  if (name === 'QuotaExceededError') return 'quota';
  if (name === 'SecurityError' || name === 'InvalidStateError' || name === 'NotAllowedError') return 'storage_denied';
  return 'storage_failed';
}

/** Validate one project's snapshot chain; returns a reason string or null. */
export function chainProblem(project, snapshots) {
  const byId = new Map(snapshots.map((s) => [s.snapshotId, s]));
  if (byId.size !== snapshots.length) return 'duplicate snapshot IDs';
  const roots = snapshots.filter((s) => s.parentSnapshotId === null);
  if (snapshots.length && roots.length !== 1) return `expected one root snapshot, found ${roots.length}`;
  for (const s of snapshots) {
    if (s.projectId !== project.projectId) return `snapshot ${s.snapshotId} belongs to another project`;
    if (s.parentSnapshotId !== null && !byId.has(s.parentSnapshotId)) return `snapshot ${s.snapshotId} cites missing parent ${s.parentSnapshotId}`;
    if (!s.overlay || typeof s.overlay !== 'object') return `snapshot ${s.snapshotId} has no overlay`;
  }
  if (!byId.has(project.headSnapshotId)) return `head ${project.headSnapshotId} is missing`;
  let cur = project.headSnapshotId;
  const seen = new Set();
  while (cur !== null) {
    if (seen.has(cur)) return 'parent cycle';
    seen.add(cur);
    cur = byId.get(cur)?.parentSnapshotId ?? null;
  }
  return null;
}

export function lineage(snapshots, headId) {
  const byId = new Map(snapshots.map((s) => [s.snapshotId, s]));
  const out = [];
  let cur = headId;
  while (cur && byId.has(cur) && !out.includes(cur)) { out.push(cur); cur = byId.get(cur).parentSnapshotId; }
  return out;
}

function req(r) {
  return new Promise((resolve, reject) => { r.onsuccess = () => resolve(r.result); r.onerror = () => reject(r.error); });
}

export class IdbDraftStore {
  constructor({ faults = {}, idb = globalThis.indexedDB } = {}) {
    this.scope = 'indexeddb';
    this.faults = faults;
    this.idb = idb;
    this.db = null;
  }

  async open() {
    try {
      if (this.faults.denyOpen) throw new DOMException('Simulated: storage access denied', 'SecurityError');
      if (!this.idb) throw new DOMException('IndexedDB is not available', 'NotAllowedError');
      this.db = await new Promise((resolve, reject) => {
        const r = this.idb.open(DB_NAME, DB_VERSION);
        r.onupgradeneeded = () => {
          const db = r.result;
          db.createObjectStore('projects', { keyPath: 'projectId' });
          db.createObjectStore('snapshots', { keyPath: 'snapshotId' }).createIndex('projectId', 'projectId');
          db.createObjectStore('ops', { keyPath: 'opId' });
        };
        r.onsuccess = () => resolve(r.result);
        r.onerror = () => reject(r.error);
        r.onblocked = () => reject(new DOMException('database upgrade blocked by another tab', 'InvalidStateError'));
      });
      // Another tab upgrading the schema must not leave us writing to a closed handle.
      this.db.onversionchange = () => { this.db.close(); this.db = null; };
      return ok(true);
    } catch (e) {
      return fail(storageCode(e), e.message);
    }
  }

  _tx(stores, mode) {
    if (!this.db) throw new DOMException('database is not open', 'InvalidStateError');
    return this.db.transaction(stores, mode, mode === 'readwrite' ? { durability: 'strict' } : undefined);
  }

  /** Run fn(tx) in one transaction; resolve only after commit (or report the abort). */
  _write(stores, fn) {
    return new Promise((resolve) => {
      let tx;
      let outcome;
      try { tx = this._tx(stores, 'readwrite'); } catch (e) { resolve(fail(storageCode(e), e.message)); return; }
      tx.oncomplete = () => resolve(outcome?.abort ? outcome.abort : ok(outcome?.value));
      tx.onabort = () => resolve(outcome?.abort || fail(storageCode(tx.error), tx.error?.message || 'transaction aborted'));
      Promise.resolve().then(() => fn(tx)).then((value) => { outcome = value; if (value?.abort) tx.abort(); })
        .catch((e) => { outcome = { abort: fail(storageCode(e), e.message) }; try { tx.abort(); } catch { /* already finished */ } });
    });
  }

  // Simulated quota applies to snapshot commits (edits), so a demo project can still be opened.
  _maybeQuota() {
    if (this.faults.quotaOnCommit) throw new DOMException('Simulated: storage quota exceeded', 'QuotaExceededError');
  }

  async listProjects() {
    try {
      const tx = this._tx(['projects'], 'readonly');
      return ok(await req(tx.objectStore('projects').getAll()));
    } catch (e) { return fail(storageCode(e), e.message); }
  }

  async createProject(project, snapshot, opId) {
    return this._write(['projects', 'snapshots', 'ops'], async (tx) => {
      const existing = await req(tx.objectStore('ops').get(opId));
      if (existing) return { value: { project: await req(tx.objectStore('projects').get(existing.projectId)), duplicate: true } };
      const snap = { ...snapshot, projectId: project.projectId, parentSnapshotId: null, opId, storageScope: this.scope };
      tx.objectStore('snapshots').put(snap);
      const rec = { ...project, headSnapshotId: snap.snapshotId };
      tx.objectStore('projects').put(rec);
      tx.objectStore('ops').put({ opId, projectId: project.projectId, snapshotId: snap.snapshotId });
      return { value: { project: rec, snapshot: snap } };
    });
  }

  async loadProject(projectId) {
    try {
      const tx = this._tx(['projects', 'snapshots'], 'readonly');
      const project = await req(tx.objectStore('projects').get(projectId));
      if (!project) return fail('not_found', `local project ${projectId} not found`);
      const snapshots = await req(tx.objectStore('snapshots').index('projectId').getAll(projectId));
      return ok({ project, snapshots, problem: chainProblem(project, snapshots) });
    } catch (e) { return fail(storageCode(e), e.message); }
  }

  /**
   * Commit a snapshot only if the project head still equals expectedParent.
   * Idempotent per opId: repeating a committed op returns the same snapshot.
   */
  async commit(projectId, expectedParent, snapshot, opId) {
    return this._write(['projects', 'snapshots', 'ops'], async (tx) => {
      const prior = await req(tx.objectStore('ops').get(opId));
      if (prior) return { value: { snapshot: await req(tx.objectStore('snapshots').get(prior.snapshotId)), duplicate: true } };
      const project = await req(tx.objectStore('projects').get(projectId));
      if (!project) return { abort: fail('not_found', `local project ${projectId} not found`) };
      if (project.headSnapshotId !== expectedParent) {
        const theirs = await req(tx.objectStore('snapshots').get(project.headSnapshotId));
        return { abort: fail('conflict', 'a newer local snapshot exists', { theirs, expectedParent, actualParent: project.headSnapshotId }) };
      }
      this._maybeQuota();
      const snap = { ...snapshot, projectId, parentSnapshotId: expectedParent, opId, storageScope: this.scope };
      tx.objectStore('snapshots').put(snap);
      tx.objectStore('projects').put({ ...project, headSnapshotId: snap.snapshotId, lastOpenedAt: snap.savedAt });
      tx.objectStore('ops').put({ opId, projectId, snapshotId: snap.snapshotId });
      return { value: { snapshot: snap } };
    });
  }

  async touch(projectId, at) {
    return this._write(['projects'], async (tx) => {
      const p = await req(tx.objectStore('projects').get(projectId));
      if (p) tx.objectStore('projects').put({ ...p, lastOpenedAt: at });
      return { value: Boolean(p) };
    });
  }

  /** Delete exactly one local project and its snapshots/ops; returns counts. */
  async deleteProject(projectId) {
    return this._write(['projects', 'snapshots', 'ops'], async (tx) => {
      const snaps = await req(tx.objectStore('snapshots').index('projectId').getAll(projectId));
      for (const s of snaps) tx.objectStore('snapshots').delete(s.snapshotId);
      const ops = await req(tx.objectStore('ops').getAll());
      const doomed = ops.filter((o) => o.projectId === projectId);
      for (const o of doomed) tx.objectStore('ops').delete(o.opId);
      tx.objectStore('projects').delete(projectId);
      return { value: { snapshots: snaps.length, ops: doomed.length } };
    });
  }
}

/** Same contract in memory: used when durable storage is denied (ST-07). */
export class MemoryDraftStore {
  constructor() {
    this.scope = 'memory';
    this.projects = new Map();
    this.snapshots = new Map();
    this.ops = new Map();
  }
  async open() { return ok(true); }
  async listProjects() { return ok([...this.projects.values()].map((p) => ({ ...p }))); }
  async createProject(project, snapshot, opId) {
    if (this.ops.has(opId)) return ok({ project: this.projects.get(this.ops.get(opId).projectId), duplicate: true });
    const snap = structuredClone({ ...snapshot, projectId: project.projectId, parentSnapshotId: null, opId, storageScope: this.scope });
    const rec = structuredClone({ ...project, headSnapshotId: snap.snapshotId });
    this.snapshots.set(snap.snapshotId, snap);
    this.projects.set(rec.projectId, rec);
    this.ops.set(opId, { opId, projectId: rec.projectId, snapshotId: snap.snapshotId });
    return ok({ project: rec, snapshot: snap });
  }
  async loadProject(projectId) {
    const project = this.projects.get(projectId);
    if (!project) return fail('not_found', `local project ${projectId} not found`);
    const snapshots = [...this.snapshots.values()].filter((s) => s.projectId === projectId).map((s) => structuredClone(s));
    return ok({ project: structuredClone(project), snapshots, problem: chainProblem(project, snapshots) });
  }
  async commit(projectId, expectedParent, snapshot, opId) {
    if (this.ops.has(opId)) return ok({ snapshot: this.snapshots.get(this.ops.get(opId).snapshotId), duplicate: true });
    const project = this.projects.get(projectId);
    if (!project) return fail('not_found', `local project ${projectId} not found`);
    if (project.headSnapshotId !== expectedParent) {
      return fail('conflict', 'a newer local snapshot exists', { theirs: structuredClone(this.snapshots.get(project.headSnapshotId)), expectedParent, actualParent: project.headSnapshotId });
    }
    const snap = structuredClone({ ...snapshot, projectId, parentSnapshotId: expectedParent, opId, storageScope: this.scope });
    this.snapshots.set(snap.snapshotId, snap);
    project.headSnapshotId = snap.snapshotId;
    project.lastOpenedAt = snap.savedAt;
    this.ops.set(opId, { opId, projectId, snapshotId: snap.snapshotId });
    return ok({ snapshot: snap });
  }
  async touch(projectId, at) { const p = this.projects.get(projectId); if (p) p.lastOpenedAt = at; return ok(Boolean(p)); }
  async deleteProject(projectId) {
    const snaps = [...this.snapshots.values()].filter((s) => s.projectId === projectId);
    snaps.forEach((s) => this.snapshots.delete(s.snapshotId));
    const ops = [...this.ops.values()].filter((o) => o.projectId === projectId);
    ops.forEach((o) => this.ops.delete(o.opId));
    this.projects.delete(projectId);
    return ok({ snapshots: snaps.length, ops: ops.length });
  }
}
