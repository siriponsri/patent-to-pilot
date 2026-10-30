// Controller: state, routing, persistence, import and export orchestration.
import { translator } from '../core/i18n.js';
import { applyTheme, THEME_KEYS } from '../core/tokens.js';
import { parseLossless, stringifyLossless, toPlain, sha256Hex } from '../core/pyjson.js';
import { validateDossier, validateRunArtifacts, checkEvidence } from '../core/validate.js';
import { emptyOverlay, cloneOverlay, overlayDiff, overlayErrors, reapply, newId } from '../core/overlay.js';
import { IdbDraftStore, MemoryDraftStore, lineage } from '../core/store.js';
import { renderMarkdown, buildRecovery, parseRecovery, RECOVERY_FORMAT } from '../core/export.js';
import { candidateScope } from '../core/run.js';
import { emptyDraft } from '../core/brief.js';
import { capabilities, loadStatic, fixtureTree, buildCatalog, comparatorOf } from '../adapters.js';
import { download } from './dom.js';
import { renderApp, savedTimeText } from './screens.js';
import { runDossierStages } from '../core/validate.js';
import { initialStates, STAGE_TO_NODE, stateForStageEvent } from '../core/pipeline.js';
import { normalizeLayout } from '../core/layout.js';
import { summarizeRun } from '../core/run.js';
import { setMotionPreference, pace } from './motion.js';
import { applyLayout, workspaceCanvas } from './workspace.js';

const LAYOUT_KEY = 'p2p-healthtech-ux-layout';
const STAGE_PACE_MS = 420;

export const MAX_FILE_BYTES = 5 * 1024 * 1024;
const AUTOSAVE_MS = 1000;
const PREFS_KEY = 'p2p-healthtech-ux-prefs';
const today = () => new Date().toISOString().slice(0, 10);

function readPrefs() {
  try { return JSON.parse(localStorage.getItem(PREFS_KEY) || '{}'); } catch { return {}; }
}
function writePrefs(p) {
  try { localStorage.setItem(PREFS_KEY, JSON.stringify(p)); } catch { /* preference only */ }
}

export const app = {
  state: {
    locale: 'th', theme: 'formal-light', booting: true, staticError: null, staticData: null,
    store: null, storageScope: 'indexeddb', storageError: null, simulate: null,
    projects: [], projectProblems: {}, catalog: [], current: null, importPreview: null,
    draft: null, notice: null, route: { name: 'home', params: {}, query: {} },
  },
  t: translator('th'),

  // ------------------------------------------------------------------ boot
  async init() {
    const prefs = readPrefs();
    const params = new URLSearchParams(location.search);
    this.state.locale = prefs.locale === 'en' ? 'en' : 'th';
    this.state.theme = THEME_KEYS.includes(prefs.theme) ? prefs.theme : 'formal-light';
    this.state.motion = prefs.motion === 'reduced' ? 'reduced' : 'full';
    try { this.layout = normalizeLayout(JSON.parse(localStorage.getItem(LAYOUT_KEY) || 'null')); } catch { this.layout = normalizeLayout(null); }
    // Explicit, labelled fault simulation for acceptance tests (FX-07 / FX-09).
    this.state.simulate = ['storage-denied', 'quota'].includes(params.get('simulate')) ? params.get('simulate') : null;
    this.applyPrefs();
    window.addEventListener('hashchange', () => this.route());
    window.addEventListener('beforeunload', (e) => {
      const c = this.state.current;
      if (c && (c.dirty || (c.storageScope === 'memory' && c.overlayTouched))) { e.preventDefault(); e.returnValue = ''; }
    });
    try { this.state.staticData = await loadStatic(); } catch (e) { this.state.staticError = { diag: newId('diag'), message: e.message }; }
    await this.openStore();
    if ('BroadcastChannel' in window) {
      this.channel = new BroadcastChannel('p2p-healthtech-ux');
      this.channel.onmessage = (ev) => this.onPeerCommit(ev.data);
    }
    this.state.booting = false;
    await this.refreshProjects();
    await this.route();
  },

  async openStore() {
    const faults = { denyOpen: this.state.simulate === 'storage-denied', quotaOnCommit: this.state.simulate === 'quota' };
    let store = new IdbDraftStore({ faults });
    let res = await store.open();
    if (!res.ok) {
      this.state.storageError = { code: res.code, message: res.message, diag: newId('diag') };
      store = new MemoryDraftStore();
      await store.open();
    }
    this.state.store = store;
    this.state.storageScope = store.scope;
  },

  caps() { return capabilities(this.state.storageScope); },

  applyPrefs() {
    this.t = translator(this.state.locale);
    document.documentElement.lang = this.state.locale;
    applyTheme(document.documentElement, this.state.theme);
    setMotionPreference(this.state.motion);
    writePrefs({ locale: this.state.locale, theme: this.state.theme, motion: this.state.motion });
  },
  setLocale(locale) { this.state.locale = locale; this.applyPrefs(); this.render({ keepFocus: true }); },
  setTheme(theme) { this.state.theme = theme; this.applyPrefs(); this.render({ keepFocus: true }); },
  setMotion(motion) { this.state.motion = motion; this.applyPrefs(); this.render({ keepFocus: true }); },

  /** Workspace layout is a per-browser convenience; storage failure only loses the preference. */
  setLayout(layout) {
    this.layout = layout;
    try { localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout)); } catch { /* preference only */ }
    applyLayout(this);
  },
  resetLayout() { this.setLayout(normalizeLayout(null)); this.announce(this.t('layout.resetDone'), { toast: true }); },

  /**
   * Status message. `toast` is for explicit user actions (download, copy): a
   * dismissible role=status note, bottom-right, auto-hidden after 5 s, at most 2.
   * Background transitions (autosave) use only the polite live region.
   */
  announce(msg, { toast = false } = {}) {
    if (toast) { this.toast(msg); return; }
    const live = document.getElementById('live');
    if (!live) return;
    live.textContent = '';
    setTimeout(() => { live.textContent = msg; }, 30);
  },

  toast(msg) {
    const box = document.getElementById('toasts');
    if (!box) return;
    while (box.children.length >= 2) box.firstElementChild.remove();
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'toast-close';
    close.setAttribute('aria-label', this.t('common.close'));
    close.textContent = '×';
    const item = document.createElement('div');
    item.className = 'toast';
    item.setAttribute('role', 'status');
    item.append(document.createTextNode(msg), close);
    close.addEventListener('click', () => item.remove());
    box.append(item);
    setTimeout(() => item.remove(), 5000);
  },

  // ------------------------------------------------------------------ routing
  parseHash() {
    const raw = location.hash.replace(/^#/, '') || '/';
    const [path, qs] = raw.split('?');
    const query = Object.fromEntries(new URLSearchParams(qs || ''));
    const parts = path.split('/').filter(Boolean).map(decodeURIComponent);
    if (!parts.length) return { name: 'home', params: {}, query };
    if (parts[0] === 'new' && parts[1] === 'device') return { name: 'device', params: {}, query };
    if (parts[0] === 'new' && parts[1] === 'brief') return { name: 'brief', params: {}, query };
    if (parts[0] === 'import') return { name: 'import', params: {}, query };
    if (parts[0] === 'project' && parts[1]) {
      const id = parts[1];
      const sub = parts[2] || 'overview';
      if (sub === 'source' && parts[3]) return { name: 'source', params: { id, sourceId: parts[3] }, query };
      if (['overview', 'evidence', 'runs', 'history', 'requests', 'export', 'brief', 'checks', 'sources', 'agent'].includes(sub)) return { name: sub, params: { id }, query, project: true };
    }
    return { name: 'notfound', params: {}, query };
  },

  async route() {
    const prev = this.state.route;
    const r = this.parseHash();
    r.project = Boolean(r.params.id);
    this.state.route = r;
    if (r.project && this.state.current?.project.projectId !== r.params.id) {
      await this.openProject(r.params.id);
    }
    if (r.name === 'source') await this.prepareSource(r);
    if (r.query.tab && this.state.current?.ui) this.state.current.ui.tab = r.query.tab;
    const c = this.state.current;
    if (r.project && c?.kind === 'dossier' && !c.corrupt && !c.pipe.started) {
      c.pipe.started = true;
      // Render first so the canvas exists, then run the real checks step by step.
      this.render({ routeChanged: true });
      this.runPipeline();
      return;
    }
    this.render({ routeChanged: prev.name !== r.name || prev.params.id !== r.params.id || prev.params.sourceId !== r.params.sourceId });
  },

  go(hash) { if (location.hash === hash) this.route(); else location.hash = hash; },

  render(opts = {}) {
    const focusId = opts.keepFocus ? document.activeElement?.id : null;
    renderApp(this, opts);
    if (this.state.focusAfter && document.getElementById(this.state.focusAfter)) {
      document.getElementById(this.state.focusAfter).focus();
      this.state.focusAfter = null;
    } else if (focusId && document.getElementById(focusId)) {
      if (document.activeElement?.id !== focusId) document.getElementById(focusId).focus({ preventScroll: true });
    } else if (opts.routeChanged) {
      const target = this.state.route.query.focus && document.getElementById(`row-${this.state.route.query.focus}`);
      (target || document.querySelector('main h1'))?.focus();
    }
  },

  // ------------------------------------------------------------------ projects
  async refreshProjects() {
    const res = await this.state.store.listProjects();
    this.state.projects = res.ok ? res.value.sort((a, b) => String(b.lastOpenedAt).localeCompare(String(a.lastOpenedAt))) : [];
    const problems = {};
    for (const p of this.state.projects) {
      const loaded = await this.state.store.loadProject(p.projectId);
      if (loaded.ok && loaded.value.problem) problems[p.projectId] = loaded.value.problem;
      if (loaded.ok) p.snapshotCount = loaded.value.snapshots.length;
    }
    this.state.projectProblems = problems;
    if (this.state.staticData) this.state.catalog = await buildCatalog(this.state.staticData, this.state.projects);
  },

  async openProject(projectId) {
    const res = await this.state.store.loadProject(projectId);
    if (!res.ok) { this.state.current = null; this.state.missingProject = { id: projectId, code: res.code, diag: newId('diag') }; return; }
    this.state.missingProject = null;
    const { project, snapshots } = res.value;
    let problem = res.value.problem;
    const head = snapshots.find((s) => s.snapshotId === project.headSnapshotId);
    const cur = {
      project, snapshots, kind: project.kind, mode: project.mode, storageScope: this.state.store.scope,
      dirty: false, overlayTouched: false, counter: 0, saveState: this.state.store.scope === 'memory' ? 'memory' : 'saved',
      conflict: null, corrupt: null, pendingOp: null, sim: {},
    };
    if (!problem && head) {
      const oErr = overlayErrors(head.overlay);
      if (oErr.length) problem = `head overlay invalid: ${oErr[0]}`;
    }
    if (project.kind === 'dossier') {
      try {
        cur.dossierTree = parseLossless(project.dossierText);
        cur.dossier = toPlain(cur.dossierTree);
        const v = await validateDossier(cur.dossierTree, this.state.staticData.schemas.dossier);
        if (!v.ok) problem = problem || `stored dossier no longer validates: ${v.errors[0].code}`;
        cur.validation = v;
        cur.dossierHash = v.hash;
        cur.manifestTree = project.manifestText ? parseLossless(project.manifestText) : null;
        cur.eventTrees = project.eventsText ? parseLossless(project.eventsText) : null;
        cur.manifest = cur.manifestTree && toPlain(cur.manifestTree);
        cur.events = cur.eventTrees && toPlain(cur.eventTrees);
        cur.candidateScope = candidateScope(cur.dossier, cur.manifest);
      } catch (e) {
        problem = problem || `stored dossier unreadable: ${e.message}`;
      }
    }
    if (problem) {
      cur.corrupt = { reason: problem, diag: newId('diag') };
      cur.saveState = 'readonly';
      const usable = snapshots.filter((s) => !overlayErrors(s.overlay).length).sort((a, b) => String(b.savedAt).localeCompare(String(a.savedAt)));
      cur.base = usable[0] ? { snapshotId: usable[0].snapshotId, overlay: cloneOverlay(usable[0].overlay), savedAt: usable[0].savedAt } : { snapshotId: null, overlay: emptyOverlay() };
    } else {
      cur.base = { snapshotId: head.snapshotId, overlay: cloneOverlay(head.overlay), savedAt: head.savedAt };
    }
    cur.overlay = cloneOverlay(cur.base.overlay);
    cur.ui = { filter: '', sort: 'imported', compare: [], tab: 'evidence' };
    cur.pipe = { states: initialStates(), info: {}, timeline: [], running: false, started: false };
    if (cur.corrupt) cur.pipe.states = { ...cur.pipe.states, input: 'fail' };
    this.state.current = cur;
    if (!problem) await this.state.store.touch(projectId, new Date().toISOString());
  },

  async createProject({ kind, dossierTree, validation, manifestTree, eventTrees, overlay, origin, title }) {
    const now = new Date().toISOString();
    const projectId = newId('proj');
    const dossier = dossierTree ? toPlain(dossierTree) : null;
    const record = {
      projectId, kind, title: title || (dossier ? `${dossier.query.device_id_canonical}` : ''), createdAt: now, lastOpenedAt: now, origin,
      mode: kind === 'draft' ? 'draft' : validation.mode,
    };
    if (kind === 'dossier') {
      Object.assign(record, {
        deviceIdRaw: dossier.query.device_id_raw, deviceIdCanonical: dossier.query.device_id_canonical,
        comparator: comparatorOf(dossier), dossierHash: validation.hash, backendDossierVersion: dossier.version,
        dossierText: stringifyLossless(dossierTree), manifestText: manifestTree ? stringifyLossless(manifestTree) : null,
        eventsText: eventTrees ? stringifyLossless(eventTrees) : null,
      });
    }
    const snapshot = {
      snapshotId: newId('snap'), savedAt: now, overlay: cloneOverlay(overlay), sourceDossierHash: record.dossierHash || null,
      backendDossierVersion: record.backendDossierVersion ?? null, changedKeys: overlayDiff(emptyOverlay(), overlay),
    };
    const res = await this.state.store.createProject(record, snapshot, newId('op'));
    if (res.ok) {
      await this.refreshProjects();
      this.broadcast(projectId);
    }
    return res.ok ? { ok: true, projectId: res.value.project.projectId } : res;
  },

  async startDemo(key = 'synthetic_dossier') {
    const existing = this.state.projects.find((p) => p.origin?.type === 'demo' && p.origin.fixture === key);
    if (existing) { this.go(`#/project/${encodeURIComponent(existing.projectId)}`); return; }
    const tree = fixtureTree(this.state.staticData.fixtureText, key);
    const validation = await validateDossier(tree, this.state.staticData.schemas.dossier);
    if (!validation.ok) { this.state.notice = { kind: 'error', text: `fixture ${key} failed validation`, diag: newId('diag') }; this.render(); return; }
    const overlay = key === 'synthetic_dossier' ? cloneOverlay(this.state.staticData.fixtures.overlay) : emptyOverlay();
    const res = await this.createProject({ kind: 'dossier', dossierTree: tree, validation, overlay, origin: { type: 'demo', fixture: key }, title: key === 'synthetic_dossier' ? 'UX-DEMO-001 (synthetic)' : 'UX-DEMO-001 empty corpus (synthetic)' });
    if (res.ok) this.go(`#/project/${encodeURIComponent(res.projectId)}`);
    else this.storageFailure('create', res);
  },

  storageFailure(action, res) {
    this.state.notice = { kind: 'error', action, code: res.code, text: res.message, diag: newId('diag') };
    this.render();
  },

  // ------------------------------------------------------------------ editing and saving
  edit(mutator, { rerender = false } = {}) {
    const c = this.state.current;
    if (!c || c.corrupt) return;
    mutator(c.overlay);
    c.dirty = true;
    c.overlayTouched = true;
    c.counter += 1;
    if (c.saveState !== 'conflict') {
      c.saveState = c.saveState === 'quota' ? 'quota' : 'unsaved';
      clearTimeout(this.saveTimer);
      this.saveTimer = setTimeout(() => this.save(), AUTOSAVE_MS);
    }
    this.updateSaveIndicator();
    if (c.kind === 'dossier') this.updateHumanNodes(c);
    if (rerender) this.render({ keepFocus: true });
    else if (c.kind === 'dossier') this.refreshPipe();
  },

  // ------------------------------------------------------------------ pipeline: real local work, shown step by step
  log(c, node, text, extra = {}) {
    c.pipe.timeline.push({ at: new Date().toISOString(), node, text, ...extra });
    if (c.pipe.timeline.length > 300) c.pipe.timeline.shift();
  },

  /** Update the canvas and timeline only; inspector content and focus are untouched. */
  refreshPipe() {
    if (this.state.route.project && this.state.current?.kind === 'dossier') renderApp(this, { pipeOnly: true });
  },

  stageSummary(stage, ev, c) {
    const t = this.t;
    const ok = ev.items.filter((i) => i.ok).length;
    const n = ev.items.length;
    if (stage === 'schema') return ev.errors.length ? t('nsum.schemaFail', { n: ev.errors.length }) : t('nsum.schema');
    if (stage === 'query') return t('nsum.query', { device: c.dossier.query.device_id_canonical, cutoff: c.dossier.query.evidence_cutoff });
    if (stage === 'sources') return t('nsum.sources', { ok, n });
    if (stage === 'evidence') return t('nsum.evidence', { ok, n });
    if (!n) return t(c.candidateScope === 'empty_corpus' ? 'nsum.candidatesEmpty' : 'nsum.candidatesNone');
    return t('nsum.candidates', { n, linked: c.dossier.candidates.filter((x) => x.association_status === 'disclosed_link').length });
  },

  updateHumanNodes(c) {
    const t = this.t;
    const p = c.pipe;
    p.info.review = { summary: t('nsum.review', { n: c.overlay.notes.length }) };
    p.info.requests = { summary: t('nsum.requests', { n: c.overlay.requestDrafts.length, m: c.dossier.next_information_requests.length }) };
    p.info.history = { summary: t('nsum.history', { n: c.snapshots.length }) };
    p.info.export = { summary: t('nsum.export') };
    p.info.agent = { summary: t('nsum.agent') };
    if (c.corrupt) for (const k of ['review', 'requests', 'history']) p.states[k] = 'warn';
  },

  async runPipeline() {
    const c = this.state.current;
    if (!c || c.kind !== 'dossier' || c.pipe.running || !this.state.staticData) return;
    const t = this.t;
    const p = c.pipe;
    p.running = true;
    for (const k of ['input', 'schema', 'query', 'sources', 'evidence', 'candidates', 'run']) p.states[k] = 'idle';
    p.info = {};
    this.updateHumanNodes(c);
    this.log(c, 'input', t('tl.start'));
    p.states.input = 'running';
    this.refreshPipe();
    await pace(STAGE_PACE_MS);
    const t0 = performance.now();
    let tree;
    try { tree = parseLossless(c.project.dossierText); } catch (e) {
      p.states.input = 'fail';
      this.log(c, 'input', e.message, { errors: 1 });
      p.running = false;
      this.refreshPipe();
      return;
    }
    p.states.input = 'pass';
    p.info.input = { summary: t('nsum.input', { n: tree.sources.length, kb: (c.project.dossierText.length / 1024).toFixed(1) }) };
    this.log(c, 'input', p.info.input.summary, { ms: performance.now() - t0 });
    this.refreshPipe();
    const result = await runDossierStages(tree, this.state.staticData.schemas.dossier, {
      onStage: (ev) => {
        const node = STAGE_TO_NODE[ev.stage];
        p.states[node] = stateForStageEvent(ev);
        if (ev.phase === 'end') {
          p.info[node] = { items: ev.items, summary: this.stageSummary(ev.stage, ev, c) };
          this.log(c, node, ev.errors.length ? `${p.info[node].summary} — ${[...new Set(ev.errors.map((e) => e.code))].join(', ')}` : p.info[node].summary, { ms: ev.ms, errors: ev.errors.length });
        } else if (ev.phase === 'skipped') this.log(c, node, t('tl.skipped'));
        this.refreshPipe();
      },
      pace: () => pace(STAGE_PACE_MS),
    });
    // Run receipt: only recorded artifacts, never inferred.
    let sumStop = null;
    p.states.run = 'running';
    this.refreshPipe();
    await pace(STAGE_PACE_MS);
    if (c.manifest || c.events) {
      const sum = summarizeRun(c.dossier, c.manifest, c.events);
      sumStop = sum.stopReason;
      const errs = validateRunArtifacts(c.dossier, c.manifest, c.events, this.state.staticData.schemas);
      p.states.run = errs.length ? 'fail' : sum.consistent ? 'pass' : 'warn';
      p.info.run = { summary: t('nsum.run', { calls: sum.callsUsed.status === 'known' ? sum.callsUsed.value : '?', cap: sum.callsCap.value, stop: sum.stopReason || t('value.unknown') }), items: sum.events.map((e) => ({ id: e.stepId, ok: !e.errors.length })) };
    } else {
      p.states.run = 'skipped';
      p.info.run = { summary: t('nsum.runNone') };
    }
    this.log(c, 'run', sumStop ? `${p.info.run.summary} · stop: ${sumStop}` : p.info.run.summary);
    p.running = false;
    p.lastResult = { ok: result.ok, errors: result.errors.length };
    const done = result.ok ? t('tl.doneOk') : t('tl.doneFail', { n: result.errors.length });
    this.log(c, 'export', done);
    this.announce(done);
    this.refreshPipe();
  },

  /** Replay a completed CLI run's recorded events; labelled, timestamps are the recorded ones. */
  async replayRun() {
    const c = this.state.current;
    if (!c?.events?.length || c.pipe.running) return;
    const t = this.t;
    const p = c.pipe;
    const before = p.states.run;
    p.running = true;
    p.states.run = 'running';
    this.log(c, 'run', t('tl.replayStart'), { replay: true });
    this.refreshPipe();
    for (const e of c.events) {
      await pace(650);
      this.log(c, 'run', t('tl.replayEvent', { step: e.step_id, action: e.action_type, calls: e.search_calls, returned: e.returned_candidates, stop: e.stop_reason || '—' }), { replay: true, recordedAt: e.started_at });
      workspaceCanvas()?.pulse('run');
      this.refreshPipe();
    }
    p.states.run = before === 'running' ? 'pass' : before;
    p.running = false;
    this.log(c, 'run', t('tl.replayEnd'), { replay: true });
    this.refreshPipe();
  },

  // ------------------------------------------------------------------ drop actions (each also has a button)
  addNoteFor(evidenceId) {
    const c = this.state.current;
    const ev = c?.dossier.evidence.find((e) => e.evidence_id === evidenceId);
    if (!ev || c.corrupt) return false;
    const noteId = newId('note');
    this.edit((o) => o.notes.push({ noteId, targetRef: evidenceId, baseDossierVersion: c.dossier.version, text: '', basis: 'user_note', reviewMarker: 'none' }));
    this.state.focusAfter = `note-${noteId}`;
    this.go(`#/project/${encodeURIComponent(c.project.projectId)}/source/${encodeURIComponent(ev.source_id)}?evidenceId=${encodeURIComponent(evidenceId)}`);
    return true;
  },

  addRequestFrom(item) {
    const c = this.state.current;
    if (!c || c.corrupt) return false;
    let question, refs;
    if (item.type === 'evidence') {
      const ev = c.dossier.evidence.find((e) => e.evidence_id === item.payload);
      if (!ev) return false;
      question = this.t('req.fromEvidence', { statement: ev.statement });
      refs = [ev.evidence_id];
    } else if (item.type === 'gap') {
      question = c.dossier.unresolved_items[item.payload];
      refs = [`unresolved:${item.payload}`];
    } else return false;
    const requestId = newId('request');
    this.edit((o) => o.requestDrafts.push({ requestId, question, evidenceRefs: refs, priority: 'normal', intendedRole: null, status: 'draft' }), { rerender: true });
    workspaceCanvas()?.pulse('requests');
    this.announce(this.t('req.added'), { toast: true });
    return true;
  },

  linkFeature(feature, evidenceId) {
    const c = this.state.current;
    if (!c || c.corrupt || !c.dossier.evidence.some((e) => e.evidence_id === evidenceId)) return false;
    this.edit((o) => {
      let l = o.featureLinks.find((x) => x.feature === feature);
      if (!l) { l = { feature, evidenceIds: [], basis: 'user_authored' }; o.featureLinks.push(l); }
      l.evidenceIds = [...new Set([...l.evidenceIds, evidenceId])];
    }, { rerender: true });
    return true;
  },

  moveRequest(requestId, toIndex) {
    const c = this.state.current;
    if (!c || c.corrupt) return false;
    this.edit((o) => {
      const from = o.requestDrafts.findIndex((r) => r.requestId === requestId);
      if (from < 0) return;
      const [r] = o.requestDrafts.splice(from, 1);
      o.requestDrafts.splice(Math.max(0, Math.min(toIndex, o.requestDrafts.length)), 0, r);
    }, { rerender: true });
    return true;
  },

  async save() {
    const c = this.state.current;
    if (!c || c.corrupt || c.saveState === 'conflict' || !c.dirty) return;
    if (this.saving) { this.saveAgain = true; return; }
    this.saving = true;
    clearTimeout(this.saveTimer);
    const counterAtStart = c.counter;
    // Reuse the op ID while the same content is retried, so a repeated click cannot double-commit.
    if (!c.pendingOp || c.pendingOp.counter !== counterAtStart) {
      const snapshot = {
        snapshotId: newId('snap'), savedAt: new Date().toISOString(), overlay: cloneOverlay(c.overlay),
        sourceDossierHash: c.dossierHash || null, backendDossierVersion: c.dossier?.version ?? null,
        changedKeys: overlayDiff(c.base.overlay, c.overlay), restoredFrom: c.restoredFrom || null,
      };
      c.restoredFrom = null;
      c.pendingOp = { opId: newId('op'), counter: counterAtStart, snapshot, expectedParent: c.base.snapshotId };
    }
    c.saveState = 'saving';
    this.updateSaveIndicator();
    const op = c.pendingOp;
    const res = await this.state.store.commit(c.project.projectId, op.expectedParent, op.snapshot, op.opId);
    this.saving = false;
    if (this.state.current !== c) return;
    if (res.ok) {
      const snap = res.value.snapshot;
      c.pendingOp = null;
      c.base = { snapshotId: snap.snapshotId, overlay: cloneOverlay(snap.overlay), savedAt: snap.savedAt };
      c.snapshots = [...c.snapshots.filter((s) => s.snapshotId !== snap.snapshotId), snap];
      c.project.headSnapshotId = snap.snapshotId;
      c.dirty = c.counter !== counterAtStart;
      c.saveState = c.dirty ? 'unsaved' : (c.storageScope === 'memory' ? 'memory' : 'saved');
      this.updateSaveIndicator(true);
      if (c.kind === 'dossier') { this.updateHumanNodes(c); this.refreshPipe(); }
      this.broadcast(c.project.projectId);
      if (c.dirty || this.saveAgain) { this.saveAgain = false; this.saveTimer = setTimeout(() => this.save(), AUTOSAVE_MS); }
    } else if (res.code === 'conflict') {
      c.pendingOp = null;
      c.saveState = 'conflict';
      c.conflict = { base: { snapshotId: c.base.snapshotId, overlay: cloneOverlay(c.base.overlay) }, theirs: res.theirs, diag: newId('diag') };
      this.updateSaveIndicator(true);
      this.render({ keepFocus: true });
    } else {
      // Known failure (quota/denied/failed): keep the op for an idempotent retry and keep the text.
      c.saveState = res.code === 'quota' ? 'quota' : 'failed';
      c.saveError = { code: res.code, message: res.message, diag: newId('diag') };
      this.updateSaveIndicator(true);
      this.render({ keepFocus: true });
    }
  },

  saveNow() { clearTimeout(this.saveTimer); return this.save(); },

  saveLabelKey(c) {
    return { saved: 'save.local', saving: 'save.saving', unsaved: 'save.unsaved', memory: 'save.memory', conflict: 'save.conflict', quota: 'save.quota', failed: 'save.unsaved', readonly: 'save.readonly' }[c.saveState];
  },

  updateSaveIndicator(announce = false) {
    const c = this.state.current;
    const el = document.getElementById('save-status');
    if (!c || !el) return;
    const text = this.t(this.saveLabelKey(c));
    el.textContent = text;
    el.dataset.state = c.saveState;
    const snap = document.getElementById('save-snapshot');
    if (snap) snap.textContent = c.base.snapshotId || this.t('value.unknown');
    const time = document.getElementById('save-time');
    if (time) time.textContent = savedTimeText(this);
    if (announce) this.announce(text);
  },

  broadcast(projectId) {
    try { this.channel?.postMessage({ projectId }); } catch { /* notification only */ }
  },

  async onPeerCommit(msg) {
    // Notification only; the expected-parent transaction is the concurrency control.
    const c = this.state.current;
    if (!c || c.project.projectId !== msg?.projectId || c.dirty || this.saving || c.corrupt) { await this.refreshProjects(); if (this.state.route.name === 'home') this.render(); return; }
    await this.openProject(c.project.projectId);
    this.render({ keepFocus: true });
  },

  // ------------------------------------------------------------------ conflict resolution
  async resolveConflict(choice) {
    const c = this.state.current;
    if (!c?.conflict) return;
    const { base, theirs } = c.conflict;
    if (choice === 'reapply') {
      const merged = reapply(base.overlay, theirs.overlay, c.overlay);
      c.base = { snapshotId: theirs.snapshotId, overlay: cloneOverlay(theirs.overlay), savedAt: theirs.savedAt };
      c.overlay = merged.overlay;
      c.conflict = null;
      c.dirty = true;
      c.counter += 1;
      c.saveState = 'unsaved';
      await this.save();
    } else if (choice === 'copy') {
      const res = await this.createProject({
        kind: c.kind, dossierTree: c.dossierTree, validation: c.validation, manifestTree: c.manifestTree, eventTrees: c.eventTrees,
        overlay: c.overlay, origin: { type: 'conflict_copy', fromProject: c.project.projectId, fromSnapshot: base.snapshotId }, title: `${c.project.title} (copy)`,
      });
      if (res.ok) { c.dirty = false; this.go(`#/project/${encodeURIComponent(res.projectId)}/history`); } else this.storageFailure('copy', res);
      return;
    } else if (choice === 'theirs') {
      c.base = { snapshotId: theirs.snapshotId, overlay: cloneOverlay(theirs.overlay), savedAt: theirs.savedAt };
      c.overlay = cloneOverlay(theirs.overlay);
      c.conflict = null;
      c.dirty = false;
      c.saveState = c.storageScope === 'memory' ? 'memory' : 'saved';
      await this.openProject(c.project.projectId);
    }
    this.render({ keepFocus: true });
  },

  conflictBundle() {
    const c = this.state.current;
    return JSON.stringify({ format: 'p2p-healthtech-ux-conflict', projectId: c.project.projectId, base: c.conflict.base, theirs: c.conflict.theirs, yours: { overlay: c.overlay } }, null, 2);
  },

  async restore(snapshotId) {
    const c = this.state.current;
    const old = c.snapshots.find((s) => s.snapshotId === snapshotId);
    if (!old || c.dirty || c.corrupt) return;
    c.overlay = cloneOverlay(old.overlay);
    c.dirty = true;
    c.counter += 1;
    c.restoredFrom = snapshotId;
    await this.save();
    this.state.notice = { kind: 'info', text: this.t('history.restored', { id: snapshotId }) };
    this.render({ keepFocus: true });
  },

  async deleteProject(projectId) {
    const p = this.state.projects.find((x) => x.projectId === projectId);
    const res = await this.state.store.deleteProject(projectId);
    if (this.state.current?.project.projectId === projectId) this.state.current = null;
    await this.refreshProjects();
    this.state.notice = res.ok ? { kind: 'info', text: this.t('home.deleted', { name: p?.title || projectId }) } : { kind: 'error', text: res.message, diag: newId('diag') };
    this.render();
  },

  // ------------------------------------------------------------------ exports
  exportContext(snapshotChoice) {
    const c = this.state.current;
    const snap = snapshotChoice && snapshotChoice !== 'current' ? c.snapshots.find((s) => s.snapshotId === snapshotChoice) : null;
    const acknowledged = snap ? true : (!c.dirty && c.saveState === 'saved');
    const snapshotId = snap ? snap.snapshotId : c.base.snapshotId;
    return {
      projectId: c.project.projectId, title: c.project.title, storageScope: c.storageScope, mode: c.mode,
      dossier: c.dossier, dossierTree: c.dossierTree, dossierHash: c.dossierHash, manifestTree: c.manifestTree, eventTrees: c.eventTrees,
      candidateScope: c.candidateScope, overlay: snap ? snap.overlay : c.overlay,
      snapshot: { snapshotId: c.dirty && !snap ? null : snapshotId, parentSnapshotId: snap ? snap.parentSnapshotId : (c.dirty ? c.base.snapshotId : c.snapshots.find((s) => s.snapshotId === snapshotId)?.parentSnapshotId ?? null), savedAt: snap ? snap.savedAt : (c.dirty ? null : c.base.savedAt), acknowledged },
      lineage: c.corrupt ? [] : lineage(c.snapshots, snapshotId),
    };
  },

  render_markdown(snapshotChoice, lang) { return renderMarkdown(this.exportContext(snapshotChoice), lang); },
  render_recovery(snapshotChoice) {
    const ctx = this.exportContext(snapshotChoice);
    let text = buildRecovery(ctx);
    if (this.state.current.corrupt) {
      const env = parseLossless(text);
      env.omissions = [`history_corrupt: ${this.state.current.corrupt.reason}; snapshot lineage omitted`];
      text = `${stringifyLossless(env)}\n`;
    }
    return text;
  },

  dossierOnlyText() { return `${stringifyLossless(this.state.current.dossierTree)}\n`; },

  /** Recompute the citation check for the source viewer (FX-12 tampers a copy only). */
  async prepareSource(r) {
    this.state.sourceView = null;
    const c = this.state.current;
    if (!c?.dossierTree) return;
    const src = c.dossierTree.sources.find((s) => s.source.source_id === r.params.sourceId);
    const evTree = c.dossierTree.evidence.find((e) => e.evidence_id === r.query.evidenceId);
    if (!src || !evTree) return;
    const item = r.query.sim === 'fx12' && c.mode === 'synthetic_demo'
      ? { ...toPlain(evTree), locator: 'chars:1000:2000', structured_value: evTree.structured_value }
      : { ...toPlain(evTree), structured_value: evTree.structured_value };
    const check = await checkEvidence(item, src);
    this.state.sourceView = { evidence: toPlain(item), check: check.ok && check.field ? { ...check, field: { found: true, value: toPlain(check.field.value) } } : check };
  },

  fileStem() {
    const c = this.state.current;
    return `${(c.dossier?.query.device_id_canonical || c.project.projectId).replace(/[^A-Za-z0-9_-]/g, '_')}`;
  },

  downloadRecovery() {
    const c = this.state.current;
    if (!c) return;
    if (c.kind === 'draft') download(`${this.fileStem()}-draft-recovery.json`, JSON.stringify({ format: 'p2p-healthtech-ux-draft', project: { ...c.project }, overlay: c.overlay }, null, 2));
    else download(`${this.fileStem()}-recovery.json`, this.render_recovery('current'));
    this.announce(this.t('export.started'), { toast: true });
  },

  // ------------------------------------------------------------------ import
  /** Validation with live per-stage display on the import page (same checks as validateDossier). */
  async stagedImportCheck(tree, schema) {
    const ip = { states: { schema: 'idle', query: 'idle', sources: 'idle', evidence: 'idle', candidates: 'idle' }, info: {} };
    this.state.importPipe = ip;
    return runDossierStages(tree, schema, {
      onStage: (ev) => {
        ip.states[ev.stage] = stateForStageEvent(ev);
        if (ev.phase === 'end') ip.info[ev.stage] = { ok: ev.items.filter((i) => i.ok).length, n: ev.items.length, errors: ev.errors.length, ms: ev.ms };
        renderApp(this, { importPipeOnly: true });
      },
      pace: () => pace(260),
    });
  },

  async importFiles(files) {
    const preview = { files: [], errors: [], checks: [], kind: null, ok: false, diag: newId('diag') };
    this.state.importPipe = null;
    this.state.importPreview = { loading: true };
    this.render();
    const parsed = { dossier: [], manifest: [], events: [], recovery: [] };
    for (const f of files) {
      const entry = { name: f.name, size: f.size };
      preview.files.push(entry);
      if (f.size > MAX_FILE_BYTES) { preview.errors.push({ code: 'too_large', path: f.name, message: this.t('import.tooLarge', { name: f.name, mb: 5 }) }); continue; }
      if (!/\.(json|jsonl)$/i.test(f.name)) { preview.errors.push({ code: 'unsupported_type', path: f.name, message: this.t('import.unsupported', { name: f.name }) }); continue; }
      const text = await f.text();
      entry.sha256 = await sha256Hex(text);
      try {
        if (/\.jsonl$/i.test(f.name)) {
          parsed.events.push({ name: f.name, trees: text.split(/\r?\n/).filter((l) => l.trim()).map((l) => parseLossless(l)) });
          continue;
        }
        const tree = parseLossless(text);
        if (tree && tree.format === RECOVERY_FORMAT) parsed.recovery.push({ name: f.name, text });
        else if (tree && 'dossier_id' in tree && 'evidence' in tree) parsed.dossier.push({ name: f.name, tree });
        else if (tree && 'policy_id' in tree && 'expected_query_ids' in tree) parsed.manifest.push({ name: f.name, tree });
        else preview.errors.push({ code: 'unsupported_schema', path: f.name, message: this.t('import.unsupported', { name: f.name }) });
      } catch (e) {
        // Report position only; never echo file contents.
        preview.errors.push({ code: 'json_parse', path: f.name, message: `${f.name}: invalid JSON (${e.message})` });
      }
    }
    const schemas = this.state.staticData.schemas;
    if (!preview.errors.length) {
      if (parsed.recovery.length === 1 && !parsed.dossier.length && !parsed.manifest.length && !parsed.events.length) {
        // Show the embedded dossier's stages live; the verdict still comes from parseRecovery.
        const embedded = parseLossless(parsed.recovery[0].text).dossier;
        if (embedded) await this.stagedImportCheck(embedded, schemas.dossier);
        const r = await parseRecovery(parsed.recovery[0].text, schemas);
        preview.kind = 'recovery';
        if (r.ok) Object.assign(preview, { ok: true, dossierTree: r.dossierTree, validation: r.validation, manifestTree: r.manifestTree, eventTrees: r.eventTrees, overlay: r.overlay, recoveredSnapshot: r.snapshot, checks: r.validation.checks });
        else preview.errors.push(...r.errors);
      } else if (parsed.dossier.length === 1 && !parsed.recovery.length && parsed.manifest.length <= 1 && parsed.events.length <= 1) {
        preview.kind = 'dossier';
        const v = await this.stagedImportCheck(parsed.dossier[0].tree, schemas.dossier);
        preview.checks = v.checks;
        if (!v.ok) preview.errors.push(...v.errors);
        else {
          const manifestTree = parsed.manifest[0]?.tree ?? null;
          const eventTrees = parsed.events[0]?.trees ?? null;
          const runErrors = validateRunArtifacts(toPlain(parsed.dossier[0].tree), manifestTree && toPlain(manifestTree), eventTrees && toPlain(eventTrees), schemas);
          if (runErrors.length) preview.errors.push(...runErrors);
          else Object.assign(preview, { ok: true, dossierTree: parsed.dossier[0].tree, validation: v, manifestTree, eventTrees, overlay: emptyOverlay() });
        }
      } else {
        preview.errors.push({ code: 'unsupported_combination', path: '$', message: 'Select exactly one dossier.json (optionally with its manifest.json and acquisition_events.jsonl), or exactly one recovery file.' });
      }
    }
    if (preview.ok) {
      const d = toPlain(preview.dossierTree);
      preview.summary = { deviceRaw: d.query.device_id_raw, deviceCanonical: d.query.device_id_canonical, mode: preview.validation.mode, sources: d.sources.length, evidence: d.evidence.length, candidates: d.candidates.length, scope: candidateScope(d, preview.manifestTree && toPlain(preview.manifestTree)), revisions: d.sources.map((s) => `${s.source.source_id} @ ${s.source.version_label}`), cutoff: d.query.evidence_cutoff };
    }
    this.state.importPreview = preview;
    this.render();
    document.getElementById('import-result')?.focus();
  },

  async acceptImport() {
    const p = this.state.importPreview;
    if (!p?.ok) return;
    const origin = p.kind === 'recovery'
      ? { type: 'recovery', recoveredSnapshot: p.recoveredSnapshot?.snapshotId ?? null, recoveredLineage: p.recoveredSnapshot?.lineage ?? [], files: p.files }
      : { type: 'import', files: p.files };
    const res = await this.createProject({ kind: 'dossier', dossierTree: p.dossierTree, validation: p.validation, manifestTree: p.manifestTree, eventTrees: p.eventTrees, overlay: p.overlay, origin });
    if (res.ok) { this.state.importPreview = null; this.go(`#/project/${encodeURIComponent(res.projectId)}`); } else this.storageFailure('import', res);
  },

  // ------------------------------------------------------------------ brief drafts
  newDraft(comparator, rawInput) {
    this.state.draft = { ...emptyDraft(today()), comparator: comparator || null, rawInput: rawInput || '', objective: this.t('brief.objectiveDefault'), cutoff: today() };
    this.go('#/new/brief');
  },

  async saveDraftProject() {
    const d = this.state.draft;
    if (!d) return null;
    const res = await this.createProject({ kind: 'draft', overlay: { ...emptyOverlay(), draft: { ...d } }, origin: { type: 'brief' }, title: d.title || (d.comparator ? d.comparator.deviceId : d.rawInput || 'idea') });
    if (!res.ok) { this.storageFailure('save-draft', res); return null; }
    this.state.draft = null;
    return res.projectId;
  },

  existingDossierFor(comparator) {
    if (!comparator) return null;
    if (comparator.projectId) return { projectId: comparator.projectId };
    if (comparator.demoFixture) return { demo: comparator.demoFixture };
    return null;
  },
};

export { download };
