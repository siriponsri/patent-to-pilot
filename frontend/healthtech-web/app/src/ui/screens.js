// Screen renderers (SCR-01 … SCR-11). Pure DOM construction from app state.
import { h, field, copyButton, download, uid, fmtTime } from './dom.js';
import { THEME_KEYS } from '../core/tokens.js';
import { newId, overlayDiff, MARKERS } from '../core/overlay.js';
import { integrityLabel } from '../core/export.js';
import { summarizeRun, costView } from '../core/run.js';
import { listErrors, draftToQuery } from '../core/brief.js';
import { searchCatalog } from '../adapters.js';
import { sliceCodePoints, parseLocator } from '../core/locator.js';
import { nodeForView } from '../core/pipeline.js';
import { renderWorkspace, workspaceCanvas, resetWorkspace } from './workspace.js';
import { draggable, fileDropZone } from './dnd.js';
import { journeyState } from '../core/journey.js';
import { startTour, tourSeen } from './tour.js';
import { openTutorial } from './tutorial.js';

const VIEW_TITLE = { overview: 'nav.overview', brief: 'nav.overview', evidence: 'nav.evidence', source: 'source.title', runs: 'nav.runs', history: 'nav.history', requests: 'nav.requests', export: 'nav.export', checks: 'checks.title', sources: 'sources.title', agent: 'node.agent' };

function journeyBar(app) {
  const t = app.t;
  const c = app.state.current;
  const route = app.state.route.name;
  const pid = enc(c.project.projectId);
  const j = journeyState(c, route);
  const fill = h('span', { class: 'journey-fill' });
  fill.style.width = `${Math.round(j.progress * 100)}%`;
  const crumbs = h('nav', { class: 'breadcrumb', 'aria-label': t('nav.breadcrumb') },
    h('ol', {},
      h('li', {}, h('a', { href: '#/' }, t('nav.home'))),
      h('li', {}, h('a', { href: `#/project/${pid}` }, c.dossier.query.device_id_canonical)),
      h('li', { 'aria-current': 'page' }, t(VIEW_TITLE[route] || 'nav.overview'))));
  const steps = h('nav', { class: 'journey', 'aria-label': t('journey.label') },
    h('div', { class: 'journey-track', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': String(j.steps.length), 'aria-valuenow': String(j.doneCount), 'aria-label': t('journey.progress', { n: j.doneCount, total: j.steps.length }) }, fill),
    h('ol', {}, j.steps.map((s, i) => h('li', {},
      h('a', { class: 'jstep', href: `#/project/${pid}/${s.view}`, id: `jstep-${s.id}`, 'data-done': String(s.done), 'aria-current': s.current ? 'step' : null },
        h('span', { class: 'jnum', 'aria-hidden': 'true' }, s.done ? '✓' : String(i + 1)),
        h('span', { class: 'jtext' }, h('span', { class: 'jlabel' }, t(`journey.${s.id}`)), h('span', { class: 'visually-hidden' }, ` — ${t(s.done ? 'journey.done' : 'journey.todo')}`)))))));
  const actions = h('div', { class: 'journey-actions' },
    h('button', { type: 'button', class: `btn btn-small${tourSeen() ? '' : ' btn-glow'}`, id: 'tour-start', title: t('tour.prompt'), onClick: (e) => startTour(app, e.currentTarget) }, `🧭 ${t(tourSeen() ? 'tour.start' : 'tour.prompt')}`),
    h('button', { type: 'button', class: 'btn btn-small', id: 'tutorial-open', onClick: (e) => openTutorial(app, e.currentTarget) }, `🎬 ${t('tutorial.open')}`),
    j.next ? h('a', { class: 'btn btn-small btn-primary', id: 'journey-next', href: `#/project/${pid}/${j.next.view}` }, `${t('journey.next')}: ${t(`journey.${j.next.id}`)} →`) : h('span', { class: 'badge badge-success' }, `✓ ${t('journey.complete')}`));
  return h('div', { class: 'journey-bar' }, crumbs, steps, actions);
}

const MODE_KEY = { synthetic_demo: 'mode.synthetic', imported_public: 'mode.public', simulation: 'mode.simulation', draft: 'mode.draft' };
const enc = encodeURIComponent;

// ------------------------------------------------------------------ shared components
function badge(text, kind = 'neutral', extra = {}) {
  return h('span', { class: `badge badge-${kind}`, ...extra }, text);
}

function modeBadge(t, mode) {
  const kind = mode === 'imported_public' ? 'info' : mode === 'draft' ? 'neutral' : 'synthetic';
  return badge(t(MODE_KEY[mode] || 'value.unknown'), kind, { 'data-mode': mode });
}

function callout(kind, title, ...body) {
  return h('div', { class: `callout callout-${kind}`, role: kind === 'danger' ? 'alert' : null },
    title ? h('p', { class: 'callout-title' }, title) : null, ...body);
}

/** CMP-10: action / target / outcome / preserved / next / diagnostic ID. */
function errorBanner(t, e) {
  return callout('danger', e.title,
    h('dl', { class: 'kv' },
      e.action ? [h('dt', {}, t('error.action')), h('dd', {}, e.action)] : null,
      e.target ? [h('dt', {}, t('error.target')), h('dd', {}, e.target)] : null,
      [h('dt', {}, t('error.outcome')), h('dd', {}, e.outcome || t('error.notExecuted'))],
      e.preserved ? [h('dt', {}, t('error.preserved')), h('dd', {}, e.preserved)] : null,
      e.next ? [h('dt', {}, t('error.next')), h('dd', {}, e.next)] : null,
      e.diag ? [h('dt', {}, t('error.diag')), h('dd', { class: 'mono' }, e.diag)] : null));
}

function tableWrap(label, table) {
  return h('div', { class: 'table-wrap', role: 'region', 'aria-label': label, tabindex: '0' }, table);
}

function kv(rows) {
  return h('dl', { class: 'kv' }, rows.filter(Boolean).map(([k, v]) => [h('dt', {}, k), h('dd', {}, v)]));
}

function known(t, kv) {
  return kv.status === 'known' ? String(kv.value) : `${t('value.unknown')} (${kv.reason})`;
}

function basisKey(e) {
  return e.evidence_kind === 'system_inference' ? 'basis.inference' : e.evidence_kind === 'unresolved' ? 'basis.unresolved'
    : e.evidence_kind === 'patent_disclosure' ? 'basis.reported' : 'basis.fact';
}

/** Short integrity badge; the full limitation is stated once per section (integrity.note). */
function integrityBadge(t, status) {
  const key = { exact_span_checked: 'badge.spanMatch', field_value_checked: 'badge.fieldMatch', not_independently_validated: 'badge.notValidated' }[status] || 'badge.notChecked';
  const matched = status === 'exact_span_checked' || status === 'field_value_checked';
  return badge(`${matched ? '✓ ' : ''}${t(key)}`, matched ? 'info' : 'neutral', { 'data-integrity': status, title: integrityLabel(t, status) });
}

function relationBadge(t, c) {
  return c.association_status === 'disclosed_link' ? badge(t('patent.disclosed'), 'info', { 'data-status': c.association_status })
    : badge(t('patent.candidate'), 'warning', { 'data-status': c.association_status });
}

function relationExplain(t, c) {
  return t(c.association_status === 'disclosed_link' ? 'patent.disclosed.explain' : 'patent.candidate.explain');
}

/** Top-bar popover that stays open across re-renders (e.g. while switching language). */
function menuDetails(app, id, summary, ...content) {
  const menus = app.state.openMenus || (app.state.openMenus = {});
  return h('details', { class: 'tech ws-tech', id, open: menus[id] || null, onToggle: (e) => { menus[id] = e.currentTarget.open; } }, summary, ...content);
}

/** Mark an element as a drop target; `fn(item)` performs the same action as its button alternative. */
function dropOn(el, fn) {
  el.ondropitem = fn;
  return el;
}

function panel(title, ...children) {
  return h('section', { class: 'panel' }, title ? h('h2', {}, title) : null, ...children);
}

function capabilityPanel(app) {
  const t = app.t;
  const caps = app.caps();
  const row = (label, available, reasonKey) => h('li', {}, badge(available ? t('cap.available') : t('cap.unavailable'), available ? 'success' : 'neutral'), ' ', label,
    !available && reasonKey ? h('span', { class: 'muted' }, ` — ${t(reasonKey)}`) : null);
  return h('details', { class: 'disclosure', id: 'capabilities' },
    h('summary', {}, t('cap.title')),
    h('p', { class: 'muted' }, `${t('cap.adapter')}: ${caps.adapterId} ${caps.adapterVersion}`),
    h('ul', { class: 'cap-list' },
      row(t('cap.localDrafts'), caps.localDrafts.available, caps.localDrafts.reason),
      row(t('cap.recoveryJson'), caps.export.recoveryJson),
      row(t('cap.editedMarkdown'), caps.export.editedMarkdown),
      row(t('cap.runStart'), caps.runStart.available, caps.runStart.reason),
      row(t('cap.runControl'), caps.runControl.cancel, caps.runControl.reason),
      row(t('cap.backendHistory'), caps.backendHistory.available, caps.backendHistory.reason),
      row(t('cap.pdf'), caps.export.pdf, 'cap.reason.pdf'),
      row(t('cap.collaboration'), caps.collaboration.available, caps.collaboration.reason),
      row(t('cap.analytics'), caps.analytics.available, caps.analytics.reason)));
}

function storageInfo(app) {
  const t = app.t;
  return h('details', { class: 'disclosure', id: 'storage-info' },
    h('summary', {}, t('storage.title')),
    h('p', {}, app.state.storageScope === 'indexeddb' ? t('storage.idb') : t('storage.memory')),
    h('p', {}, t('privacy.scope')));
}

// ------------------------------------------------------------------ shell
function prefsControls(app) {
  const t = app.t;
  const s = app.state;
  return h('div', { class: 'prefs' },
    field(t('pref.language'), h('select', { id: 'pref-locale', onChange: (e) => app.setLocale(e.target.value) },
      h('option', { value: 'th', selected: s.locale === 'th', lang: 'th' }, 'ไทย'), h('option', { value: 'en', selected: s.locale === 'en', lang: 'en' }, 'English'))),
    field(t('pref.theme'), h('select', { id: 'pref-theme', onChange: (e) => app.setTheme(e.target.value) },
      THEME_KEYS.map((k) => h('option', { value: k, selected: s.theme === k }, t(`theme.${k}`))))),
    field(t('pref.motion'), h('select', { id: 'pref-motion', onChange: (e) => app.setMotion(e.target.value) },
      ['full', 'reduced'].map((k) => h('option', { value: k, selected: s.motion === k }, t(`motion.${k}`))))));
}

function globalBanners(app) {
  const t = app.t;
  const s = app.state;
  const banners = [];
  if (s.simulate) banners.push(callout('warning', `${t('mode.simulation')} — ?simulate=${s.simulate}`, h('p', {}, 'Fault injection for acceptance tests (FX-07 / FX-09).')));
  if (s.storageError) {
    banners.push(errorBanner(t, { title: t('save.memory'), action: 'open IndexedDB', target: 'this browser profile', outcome: `${s.storageError.code}: ${s.storageError.message}`, preserved: t('storage.scope.memory'), next: t('save.recovery'), diag: s.storageError.diag }));
  }
  if (s.notice) {
    banners.push(s.notice.kind === 'error' ? errorBanner(t, { title: s.notice.text, action: s.notice.action, outcome: s.notice.code, diag: s.notice.diag })
      : h('div', { class: 'callout callout-info', role: 'status' }, s.notice.text));
    s.notice = null;
  }
  return banners;
}

export function renderApp(app, opts = {}) {
  const s = app.state;
  if (opts.importPipeOnly) {
    const old = document.getElementById('import-pipe');
    if (old) old.replaceWith(importPipe(app));
    return;
  }
  if (!s.booting && s.route.project && s.current?.kind === 'dossier') {
    if (opts.pipeOnly && !workspaceCanvas()) return;
    renderWorkspace(app, workspaceParts(app, opts));
    return;
  }
  if (opts.pipeOnly) return;
  resetWorkspace();
  renderPage(app, opts);
}

function renderPage(app, opts) {
  const t = app.t;
  const s = app.state;
  const root = document.getElementById('app');
  const header = h('header', { class: 'topbar' },
    h('a', { class: 'brand', href: '#/' }, h('span', { class: 'brand-mark', 'aria-hidden': 'true' }, '◆'), t('app.name')), prefsControls(app));
  const banners = globalBanners(app);
  if (s.simulate) banners.push(callout('warning', `${t('mode.simulation')} — ?simulate=${s.simulate}`, h('p', {}, 'Fault injection for acceptance tests (FX-07 / FX-09).')));
  if (s.storageError) {
    banners.push(errorBanner(t, { title: t('save.memory'), action: 'open IndexedDB', target: 'this browser profile', outcome: `${s.storageError.code}: ${s.storageError.message}`, preserved: t('storage.scope.memory'), next: t('save.recovery'), diag: s.storageError.diag }));
  }
  if (s.notice) {
    banners.push(s.notice.kind === 'error' ? errorBanner(t, { title: s.notice.text, action: s.notice.action, outcome: s.notice.code, diag: s.notice.diag })
      : h('div', { class: 'callout callout-info', role: 'status' }, s.notice.text));
    s.notice = null;
  }
  const main = h('main', { id: 'main', tabindex: '-1' });
  let content;
  if (s.booting) content = h('p', { role: 'status' }, t('home.loading'));
  else if (s.staticError && s.route.name !== 'home') content = errorBanner(t, { title: 'Static data failed to load', action: 'load fixtures/schemas', outcome: s.staticError.message, next: 'Restart the local server (npm start) and reload.', diag: s.staticError.diag });
  else if (s.route.project) content = projectShell(app);
  else content = ({ home: homeScreen, device: deviceScreen, brief: briefScreen, import: importScreen }[s.route.name] || notFound)(app);
  main.append(...banners, content);
  const footer = h('footer', { class: 'footer' }, h('p', {}, t('scope.help')), h('p', {}, t('privacy.scope')));
  root.replaceChildren(h('a', { class: 'skip-link', href: '#main', onClick: (e) => { e.preventDefault(); main.focus(); } }, t('nav.skip')), header, main, footer);
  void opts;
}

function notFound(app) {
  return h('section', {}, h('h1', { tabindex: '-1' }, '404'), h('p', {}, h('a', { href: '#/' }, app.t('nav.home'))));
}

// ------------------------------------------------------------------ SCR-01 home
function homeScreen(app) {
  const t = app.t;
  const s = app.state;
  const starts = h('ul', { class: 'start-actions' },
    h('li', {}, h('a', { class: 'card-action', href: '#/new/device', id: 'start-device' }, h('strong', {}, t('start.namedDevice')), h('span', {}, t('start.namedDevice.help')))),
    h('li', {}, h('a', { class: 'card-action', href: '#/import', id: 'start-import' }, h('strong', {}, t('start.import')), h('span', {}, t('start.import.help')))),
    h('li', {}, h('button', { type: 'button', class: 'card-action card-synthetic', id: 'start-demo', disabled: !s.staticData, onClick: () => app.startDemo('synthetic_dossier') },
      h('strong', {}, t('start.demo')), h('span', {}, t('start.demo.help')), badge(t('mode.synthetic'), 'synthetic'))),
    h('li', {}, h('button', { type: 'button', class: 'card-action card-synthetic', id: 'start-demo-empty', disabled: !s.staticData, onClick: () => app.startDemo('empty_corpus_dossier') },
      h('strong', {}, `${t('start.demo')} — FX-02`), h('span', {}, t('candidate.emptyCorpus')), badge(t('mode.synthetic'), 'synthetic'))));
  const list = s.projects.length ? h('ul', { class: 'project-list' }, s.projects.map((p) => projectCard(app, p))) : h('p', { class: 'empty' }, t('home.none'));
  return h('section', { class: 'home' },
    h('h1', { tabindex: '-1' }, t('app.name')),
    h('p', { class: 'lede' }, t('app.tagline')),
    h('section', { class: 'how', 'aria-labelledby': 'how-title' },
      h('h2', { id: 'how-title' }, t('how.title')),
      h('ol', { class: 'how-steps' }, ['how.1', 'how.2', 'how.3', 'how.4'].map((k) => h('li', {}, t(k)))),
      h('div', { class: 'actions' },
        h('button', { type: 'button', class: 'btn btn-primary btn-glow', id: 'tutorial-open-home', onClick: (e) => openTutorial(app, e.currentTarget) }, `🎬 ${t('tutorial.openLong')}`))),
    s.staticError ? errorBanner(t, { title: 'Catalog and demo unavailable', action: 'load fixtures/schemas', outcome: s.staticError.message, preserved: t('storage.scope.idb'), next: 'Restart the local server and reload.', diag: s.staticError.diag }) : null,
    starts,
    h('h2', {}, t('home.recent')),
    list,
    storageInfo(app),
    capabilityPanel(app));
}

function projectCard(app, p) {
  const t = app.t;
  const problem = app.state.projectProblems[p.projectId];
  const confirming = app.state.pendingDelete === p.projectId;
  const name = p.title || p.projectId;
  return h('li', { class: `project-card${p.mode === 'synthetic_demo' ? ' card-synthetic' : ''}` },
    h('h3', {}, h('a', { href: `#/project/${enc(p.projectId)}`, id: `open-${p.projectId}` }, name)),
    h('p', {}, modeBadge(t, p.mode), problem ? [' ', badge(t('home.corrupt'), 'danger')] : null),
    kv([
      p.deviceIdCanonical ? [t('overview.device'), `${p.deviceIdRaw} / ${p.deviceIdCanonical}`] : null,
      [t('home.lastOpened'), fmtTime(app.state.locale, p.lastOpenedAt) || t('value.unknown')],
      [t('home.storage'), t(app.state.storageScope === 'indexeddb' ? 'storage.scope.idb' : 'storage.scope.memory')],
    ]),
    confirming
      ? h('div', { class: 'callout callout-warning', role: 'group', 'aria-label': t('home.delete') },
        h('p', { id: `del-msg-${p.projectId}` }, t('home.deleteConfirm', { name, count: p.snapshotCount ?? '?' })),
        h('div', { class: 'actions' },
          h('button', { type: 'button', class: 'btn', onClick: async () => { await app.openProject(p.projectId); app.downloadRecovery(); } }, t('save.recovery')),
          h('button', { type: 'button', class: 'btn btn-danger', id: `del-confirm-${p.projectId}`, onClick: () => { app.state.pendingDelete = null; app.deleteProject(p.projectId); } }, t('home.delete')),
          h('button', { type: 'button', class: 'btn', onClick: () => { app.state.pendingDelete = null; app.render(); document.getElementById(`del-${p.projectId}`)?.focus(); } }, t('common.cancel'))))
      : h('div', { class: 'actions' },
        h('a', { class: 'btn', href: `#/project/${enc(p.projectId)}` }, t('home.open')),
        h('button', { type: 'button', class: 'btn btn-quiet', id: `del-${p.projectId}`, onClick: () => { app.state.pendingDelete = p.projectId; app.render(); document.getElementById(`del-confirm-${p.projectId}`)?.focus(); } }, t('home.delete'))));
}

// ------------------------------------------------------------------ SCR-02 device selection
function deviceScreen(app) {
  const t = app.t;
  const s = app.state;
  const text = s.deviceSearch ?? '';
  const results = searchCatalog(s.catalog, text);
  const sources = [...new Set(s.catalog.map((c) => (c.synthetic ? 'synthetic' : 'public')))].join(' + ');
  const resultRegion = h('div', { id: 'device-results', 'aria-live': 'polite' },
    h('p', { class: 'muted' }, t('device.results', { count: results.length })),
    results.length ? h('ul', { class: 'device-list' }, results.map((e, i) => h('li', { class: `device-card${e.synthetic ? ' card-synthetic' : ''}` },
      h('h3', {}, e.deviceName || e.deviceId, ' ', e.synthetic ? badge(t('source.synthetic'), 'synthetic') : badge(t('source.public'), 'info')),
      kv([
        ['ID', h('span', { class: 'mono' }, e.deviceId)],
        [t('device.applicant'), e.applicant || t('evidence.notSupplied')],
        [t('device.sourceType'), e.sourceType], [t('device.jurisdiction'), e.jurisdiction], [t('device.snapshot'), e.sourceDate],
        [t('device.revision'), `${e.sourceId} @ ${e.revision}`],
        [t('device.hash'), h('span', { class: 'mono wrap' }, e.sha256)],
        ['Origin', e.origin],
      ]),
      h('button', { type: 'button', class: 'btn btn-primary', id: `use-device-${i}`, onClick: () => app.newDraft(e, text) }, t('device.select')))))
      : h('div', { class: 'callout callout-info' }, h('p', { class: 'callout-title' }, t('device.none')), h('p', {}, t('device.noneHelp')),
        h('div', { class: 'actions' }, h('a', { class: 'btn', href: '#/import' }, t('start.import')),
          h('button', { type: 'button', class: 'btn', onClick: () => app.newDraft(null, text) }, t('device.ideaOnly')))));
  const input = h('input', { type: 'search', id: 'device-search', value: text, autocomplete: 'off', onInput: (e) => { s.deviceSearch = e.target.value; app.render({ keepFocus: true }); const el = document.getElementById('device-search'); el.setSelectionRange(el.value.length, el.value.length); } });
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('device.title')),
    field(t('device.search'), input, t('device.scope', { count: s.catalog.length, sources })),
    resultRegion,
    h('p', {}, h('button', { type: 'button', class: 'btn btn-quiet', onClick: () => app.newDraft(null, text) }, t('device.ideaOnly'))));
}

// ------------------------------------------------------------------ SCR-03 brief
function briefScreen(app, projectDraft) {
  const t = app.t;
  const s = app.state;
  const saved = Boolean(projectDraft);
  const d = saved ? app.state.current.overlay.draft : s.draft;
  if (!d) return h('section', {}, h('h1', { tabindex: '-1' }, t('brief.title')), callout('info', t('device.chooseComparator'), h('p', {}, h('a', { href: '#/new/device' }, t('start.namedDevice')))));
  const readOnly = saved && app.state.current.corrupt;
  const set = (k, v) => { if (saved) app.edit((o) => { o.draft[k] = v; }); else d[k] = v; };
  const c = d.comparator;
  const check = s.briefCheck && s.briefCheck.for === d ? s.briefCheck : null;
  const input = (k, attrs = {}) => h('input', { id: `brief-${k}`, value: d[k], disabled: readOnly, onInput: (e) => set(k, e.target.value), ...attrs });
  const area = (k) => h('textarea', { id: `brief-${k}`, rows: 3, disabled: readOnly, onInput: (e) => set(k, e.target.value) }, d[k]);
  const comparatorBlock = c
    ? h('div', { class: `device-card${c.synthetic ? ' card-synthetic' : ''}` },
      h('h3', {}, c.deviceName || c.deviceId, ' ', c.synthetic ? badge(t('source.synthetic'), 'synthetic') : badge(t('source.public'), 'info')),
      kv([['ID', c.deviceId], [t('device.revision'), `${c.sourceId} @ ${c.revision}`], [t('device.hash'), h('span', { class: 'mono wrap' }, c.sha256)], [t('device.snapshot'), c.sourceDate], [t('brief.rawInput'), d.rawInput || '—']]),
      saved ? null : h('a', { href: '#/new/device', class: 'btn btn-quiet' }, t('brief.change')))
    : callout('warning', t('brief.missingComparator'), h('p', {}, t('brief.rawInput'), ': ', d.rawInput || '—'), h('a', { href: '#/new/device' }, t('device.chooseComparator')));
  const cutoffConflict = c && d.cutoff && c.sourceDate > d.cutoff ? h('p', { class: 'field-error', id: 'cutoff-error' }, t('brief.cutoffConflict', { date: c.sourceDate, cutoff: d.cutoff })) : null;
  const onContinue = async () => {
    const f = listErrors(d.featuresText), q = listErrors(d.questionsText);
    const pid = saved ? app.state.current.project.projectId : 'unsaved';
    s.briefCheck = { for: d, featureBlank: f.blank, questionBlank: q.blank, query: draftToQuery({ ...d, language: s.locale, theme: s.theme }, pid.replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 80)) };
    app.render();
    document.getElementById('brief-result')?.focus();
  };
  const onSave = async () => {
    if (saved) { await app.saveNow(); return; }
    const id = await app.saveDraftProject();
    if (id) app.go(`#/project/${enc(id)}/brief`);
  };
  let result = null;
  if (check) {
    const errs = [...check.featureBlank.map((n) => `${t('brief.features')}: ${t('brief.blank', { n })}`), ...check.questionBlank.map((n) => `${t('brief.questions')}: ${t('brief.blank', { n })}`)];
    const existing = app.existingDossierFor(c);
    const backendInput = check.query.ok ? app.backendInputFor(check.query.value) : null;
    const backend = s.backend;
    const backendJob = s.backendJob;
    const providers = backend?.providerCatalog?.providers || [];
    const active = ['queued', 'running', 'cancel_requested'].includes(backendJob?.state);
    const backendPanel = backend ? h('section', { class: 'callout callout-info', id: 'backend-run', 'data-state': backendJob?.state || 'ready' },
      h('h3', {}, t('backend.title')),
      field(t('backend.provider'), h('select', { id: 'backend-provider', disabled: active }, providers.map((p) => h('option', { value: p.id, disabled: !p.available, selected: p.id === 'local' }, `${p.label} — ${p.available ? t('cap.available') : t('cap.unavailable')}`)))),
      h('p', { id: 'backend-status' }, `${t('backend.status')}: ${backendJob?.state || 'ready'}`),
      backendJob?.cost ? h('p', { class: 'muted' }, t('backend.cost', { usd: backendJob.cost.actual_usd ?? 'unknown', seconds: backendJob.cost.local_elapsed_seconds ?? 'unknown' })) : null,
      !backendInput ? h('p', { class: 'muted' }, t('backend.unavailable')) : null,
      h('div', { class: 'actions' },
        !active && (!backendJob || ['unavailable', 'failed', 'cancelled'].includes(backendJob.state))
          ? h('button', { type: 'button', class: 'btn btn-primary', id: 'backend-start', disabled: !backendInput, onClick: () => ['failed', 'cancelled'].includes(backendJob?.state) ? app.resumeBackendJob() : app.startBackendJob(check.query.value) }, ['failed', 'cancelled'].includes(backendJob?.state) ? t('backend.resume') : t('backend.start'))
          : null,
        active ? h('button', { type: 'button', class: 'btn', id: 'backend-cancel', onClick: () => app.cancelBackendJob() }, t('backend.cancel')) : null))
      : callout('info', t('cap.runStart'), h('p', { id: 'run-unavailable' }, t('brief.runUnavailable')),
        h('div', { class: 'actions' },
          existing?.projectId ? h('a', { class: 'btn btn-primary', href: `#/project/${enc(existing.projectId)}` }, t('brief.openExisting')) : null,
          existing?.demo ? h('button', { type: 'button', class: 'btn btn-primary', onClick: () => app.startDemo(existing.demo) }, t('brief.openExisting')) : null,
          h('a', { class: 'btn', href: '#/import' }, t('start.import'))));
    result = h('div', { id: 'brief-result', tabindex: '-1', class: 'stack' },
      errs.length ? callout('danger', t('brief.queryInvalid', { reason: check.query.reason || '' }), h('ul', {}, errs.map((e) => h('li', {}, e)))) : null,
      !c ? callout('warning', t('brief.missingComparator')) : null,
      check.query.ok
        ? h('details', { class: 'disclosure', open: true }, h('summary', {}, t('brief.queryPreview')), h('pre', { class: 'code', id: 'query-preview' }, JSON.stringify(check.query.value, null, 2)))
        : (!errs.length ? callout('danger', t('brief.queryInvalid', { reason: check.query.reason })) : null),
      backendPanel);
  }
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('brief.title'), ' ', modeBadge(t, 'draft')),
    h('h2', {}, t('brief.comparator')), comparatorBlock,
    h('form', { class: 'form', onSubmit: (e) => { e.preventDefault(); onContinue(); } },
      field(t('brief.title.optional'), input('title')),
      field(t('brief.objective'), area('objective')),
      field(t('brief.audience'), h('select', { id: 'brief-audience', disabled: readOnly, onChange: (e) => set('audience', e.target.value) },
        ['entrepreneur', 'investor', 'researcher'].map((a) => h('option', { value: a, selected: d.audience === a }, t(`brief.audience.${a}`))))),
      field(t('brief.features'), area('featuresText')),
      field(t('brief.questions'), area('questionsText')),
      field(t('brief.jurisdiction'), input('jurisdiction')),
      h('div', {}, field(t('brief.cutoff'), input('cutoff', { type: 'date', 'aria-describedby': cutoffConflict ? 'cutoff-error' : null, onChange: () => app.render({ keepFocus: true }) })), cutoffConflict),
      h('details', { class: 'disclosure' }, h('summary', {}, t('brief.budget')),
        field(t('brief.calls'), input('maxCalls', { type: 'number', min: 0, max: 100 })),
        field(t('brief.candidates'), input('maxCandidates', { type: 'number', min: 0, max: 10000 }))),
      h('div', { class: 'actions' },
        h('button', { type: 'button', class: 'btn', id: 'brief-save', disabled: readOnly, onClick: onSave }, t('brief.saveDraft')),
        h('button', { type: 'submit', class: 'btn btn-primary', id: 'brief-continue' }, t('brief.continue')))),
    result);
}

// ------------------------------------------------------------------ SCR-04 import
function importScreen(app) {
  const t = app.t;
  const p = app.state.importPreview;
  const fileInput = h('input', { type: 'file', id: 'import-file', multiple: true, accept: '.json,.jsonl,application/json', onChange: (e) => app.importFiles([...e.target.files]) });
  let result = null;
  if (p?.loading) result = h('p', { role: 'status', id: 'import-result', tabindex: '-1' }, t('import.validating'));
  else if (p) {
    const files = h('ul', { class: 'mono-list' }, p.files.map((f) => h('li', {}, `${f.name} · ${f.size} B${f.sha256 ? ` · sha256 ${f.sha256}` : ''}`)));
    result = p.ok
      ? h('div', { id: 'import-result', tabindex: '-1', class: 'stack', 'data-result': 'accepted' },
        callout('success', t('import.passed'),
          h('p', {}, modeBadge(t, p.summary.mode), ' ', p.kind === 'recovery' ? t('import.recovery') : null),
          kv([[t('overview.device'), `${p.summary.deviceRaw} / ${p.summary.deviceCanonical}`],
            [t('overview.cutoff'), p.summary.cutoff],
            ['', t('import.counts', { sources: p.summary.sources, evidence: p.summary.evidence, candidates: p.summary.candidates })],
            [t('overview.candidates'), p.summary.candidates ? String(p.summary.candidates) : t({ empty_corpus: 'candidate.emptyCorpus', no_results: 'candidate.noResults' }[p.summary.scope] || 'candidate.unknownScope')],
            [t('device.revision'), h('ul', { class: 'mono-list' }, p.summary.revisions.map((r) => h('li', {}, r)))],
            ['SHA-256', h('span', { class: 'mono wrap' }, p.validation.hash)]]),
          h('h3', {}, t('import.checks')), h('ul', {}, p.checks.map((c) => h('li', {}, `${c.check}: ${c.result}`))),
          files,
          h('p', {}, t('import.destination', { scope: t(app.state.storageScope === 'indexeddb' ? 'storage.scope.idb' : 'storage.scope.memory') }))),
        h('div', { class: 'actions' },
          h('button', { type: 'button', class: 'btn btn-primary', id: 'import-accept', onClick: () => app.acceptImport() }, t('import.accept')),
          h('button', { type: 'button', class: 'btn', onClick: () => { app.state.importPreview = null; app.go('#/'); } }, t('import.cancel'))))
      : h('div', { id: 'import-result', tabindex: '-1', class: 'stack', 'data-result': 'rejected' },
        errorBanner(t, { title: t('import.rejected'), action: t('import.title'), target: p.files.map((f) => f.name).join(', '), outcome: t('error.notExecuted'), preserved: t('import.rejectedHelp'), next: p.errors.some((e) => e.code === 'synthetic_in_public') ? t('import.mixed') : t('import.rejectedHelp'), diag: p.diag }),
        h('h2', {}, t('import.preview')),
        h('ul', { class: 'error-list' }, p.errors.map((e) => h('li', { 'data-code': e.code }, h('code', {}, e.code), ' ', h('span', { class: 'mono' }, e.path || ''), ' — ', e.message))),
        files);
  }
  const zone = h('div', { class: 'dropzone', 'data-drop': 'files' },
    h('span', { class: 'dropzone-icon', 'aria-hidden': 'true' }, '⇣'),
    h('p', { class: 'dropzone-title' }, t('import.drop')),
    field(t('import.pick'), fileInput),
    h('p', { class: 'muted' }, t('import.help', { mb: 5 })));
  fileDropZone(zone, (files) => app.importFiles(files));
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('import.title')),
    zone,
    h('h2', {}, t('import.pipe')),
    importPipe(app),
    h('p', { class: 'muted' }, t('import.notSupported')),
    h('p', { class: 'muted' }, t('privacy.scope')),
    result);
}

// ------------------------------------------------------------------ project shell (CMP-01/02/12)
function projectShell(app) {
  const t = app.t;
  const s = app.state;
  if (!s.current) {
    return h('section', {}, h('h1', { tabindex: '-1' }, t('error.missingProject')),
      errorBanner(t, { action: 'open', target: s.missingProject?.id, outcome: s.missingProject?.code, next: t('error.missingProject'), diag: s.missingProject?.diag }),
      h('div', { class: 'actions' }, h('a', { class: 'btn', href: '#/import' }, t('start.import')), h('a', { class: 'btn', href: '#/' }, t('nav.home'))));
  }
  const c = s.current;
  const pid = enc(c.project.projectId);
  void pid;
  return h('div', {}, saveBar(app), briefScreen(app, true));
}

// ------------------------------------------------------------------ dossier workspace (canvas + dockable panels)
const VIEWS = () => ({ overview: overviewScreen, evidence: evidenceScreen, source: sourceScreen, runs: runsScreen, history: historyScreen, requests: requestsScreen, export: exportScreen, brief: overviewScreen, checks: checksScreen, sources: sourcesScreen, agent: agentScreen });

function workspaceParts(app, opts) {
  const s = app.state;
  const c = s.current;
  const t = app.t;
  const view = VIEWS()[s.route.name] || overviewScreen;
  const selectedNode = nodeForView(s.route.name === 'brief' ? 'overview' : s.route.name, s.route.name === 'evidence' ? c.ui.tab : null);
  return {
    pipeOnly: opts.pipeOnly,
    pipe: c.pipe,
    selectedNode,
    topbar: () => wsTopbar(app),
    modeStrip: () => wsModeStrip(app),
    journey: () => journeyBar(app),
    statusbar: () => h('footer', { class: 'ws-status' }, h('span', {}, t('scope.help')), h('span', {}, t('privacy.scope'))),
    inspector: () => [...globalBanners(app), conflictPanel(app), corruptPanel(app), saveErrorPanel(app), view(app)].filter(Boolean),
    library: () => libraryPanel(app),
    timeline: () => timelinePanel(app),
    onCanvas: (canvas) => {
      canvas.dropTarget('requests', 'evidence gap', t('node.requests'), (item) => app.addRequestFrom(item));
      canvas.dropTarget('review', 'evidence', t('node.review'), (item) => app.addNoteFor(item.payload));
    },
  };
}

function wsTopbar(app) {
  const t = app.t;
  const c = app.state.current;
  const d = c.dossier;
  return h('header', { class: 'ws-top' },
    h('a', { class: 'brand', href: '#/', title: t('nav.home') }, h('span', { class: 'brand-mark', 'aria-hidden': 'true' }, '◆'), h('span', { class: 'brand-text' }, t('app.name'))),
    h('div', { class: 'ws-title' },
      h('span', { class: 'device-name' }, d.query.device_id_raw),
      h('span', { class: 'muted ws-sub' }, [d.query.jurisdiction, `${t('overview.cutoff')} ${d.query.evidence_cutoff}`, t('header.dossierVersion', { v: d.version })].join(' · '))),
    saveBar(app),
    menuDetails(app, 'info-menu', h('summary', {}, 'ⓘ ', t('evidence.detail')),
      h('div', { class: 'ws-pop' }, kv([['device_id_canonical', h('span', { class: 'mono' }, d.query.device_id_canonical)], ['dossier_id', h('span', { class: 'mono' }, d.dossier_id)],
        [t('overview.snapshot'), h('span', { id: 'save-snapshot', class: 'mono' }, c.base.snapshotId || t('value.unknown'))],
        [t('home.storage'), t(c.storageScope === 'indexeddb' ? 'storage.scope.idb' : 'storage.scope.memory')],
        ['SHA-256', h('span', { class: 'mono wrap' }, c.dossierHash)]]))),
    menuDetails(app, 'layout-menu', h('summary', {}, t('layout.title')),
      h('div', { class: 'ws-pop' },
        prefsControls(app),
        h('p', { class: 'help' }, t('layout.help')),
        h('button', { type: 'button', class: 'btn btn-small', id: 'layout-reset', onClick: () => app.resetLayout() }, t('layout.reset')))));
}

function wsModeStrip(app) {
  const t = app.t;
  const c = app.state.current;
  return h('div', { class: `mode-banner mode-${c.mode}`, 'data-mode': c.mode, role: 'note' }, modeBadge(t, c.mode),
    c.manifest ? [' ', badge(t('mode.importedRun'), 'neutral')] : null,
    c.mode === 'synthetic_demo' ? h('span', {}, ` ${t('start.demo.help')}`) : null);
}

// ---- library panel: draggable evidence and gaps (each with button alternatives)
function libraryPanel(app) {
  const t = app.t;
  const c = app.state.current;
  const d = c.dossier;
  const pid = enc(c.project.projectId);
  const ro = Boolean(c.corrupt);
  const say = (m) => app.announce(m);
  const evCards = d.evidence.map((e) => {
    const handle = h('span', { class: 'lib-handle', title: t('lib.dragHint'), 'aria-hidden': 'true' }, '⠿');
    const card = h('li', { class: 'lib-card', 'data-evidence': e.evidence_id },
      handle,
      h('div', { class: 'lib-body' },
        h('p', { class: 'lib-title' }, e.statement),
        h('p', { class: 'lib-meta' }, integrityBadge(t, e.verification_status), ' ', h('span', { class: 'mono muted' }, e.source_id)),
        h('div', { class: 'lib-actions' },
          h('a', { class: 'btn btn-tiny', href: `#/project/${pid}/source/${enc(e.source_id)}?evidenceId=${enc(e.evidence_id)}` }, t('overview.inspect')),
          h('button', { type: 'button', class: 'btn btn-tiny', disabled: ro, id: `lib-note-${e.evidence_id}`, onClick: () => app.addNoteFor(e.evidence_id) }, `＋ ${t('lib.note')}`),
          h('button', { type: 'button', class: 'btn btn-tiny', disabled: ro, id: `lib-req-${e.evidence_id}`, onClick: () => app.addRequestFrom({ type: 'evidence', payload: e.evidence_id }) }, `＋ ${t('lib.request')}`))));
    if (!ro) draggable(handle, card, { type: 'evidence', payload: e.evidence_id, label: e.statement }, say);
    return card;
  });
  const gapCards = d.unresolved_items.map((u, i) => {
    const handle = h('span', { class: 'lib-handle', title: t('lib.dragHint'), 'aria-hidden': 'true' }, '⠿');
    const card = h('li', { class: 'lib-card lib-gap', 'data-gap': String(i) },
      handle,
      h('div', { class: 'lib-body' }, h('p', { class: 'lib-title' }, u),
        h('div', { class: 'lib-actions' }, h('button', { type: 'button', class: 'btn btn-tiny', disabled: ro, id: `lib-gap-${i}`, onClick: () => app.addRequestFrom({ type: 'gap', payload: i }) }, `＋ ${t('lib.request')}`))));
    if (!ro) draggable(handle, card, { type: 'gap', payload: i, label: u }, say);
    return card;
  });
  return h('div', { class: 'library' },
    h('p', { class: 'tip' }, h('span', { class: 'tip-icon', 'aria-hidden': 'true' }, '💡'), h('span', {}, t('lib.hint'))),
    h('h2', { class: 'lib-h' }, t('lib.evidence'), ' ', h('span', { class: 'tab-count' }, String(d.evidence.length))),
    h('ul', { class: 'lib-list' }, evCards),
    h('h2', { class: 'lib-h' }, t('lib.gaps'), ' ', h('span', { class: 'tab-count' }, String(d.unresolved_items.length))),
    h('ul', { class: 'lib-list' }, gapCards),
    h('h2', { class: 'lib-h' }, t('lib.sources'), ' ', h('span', { class: 'tab-count' }, String(d.sources.length))),
    h('ul', { class: 'plain-list lib-sources' }, d.sources.map((s) => h('li', {}, h('span', { class: 'mono wrap' }, s.source.source_id), ' ', s.synthetic ? badge(t('source.synthetic'), 'synthetic') : badge(t('source.public'), 'info')))));
}

// ---- timeline panel: what actually ran, with measured durations
function timelinePanel(app) {
  const t = app.t;
  const c = app.state.current;
  const p = c.pipe;
  const time = (iso) => { try { return new Date(iso).toLocaleTimeString(app.state.locale === 'th' ? 'th-TH-u-ca-gregory' : 'en-GB'); } catch { return iso; } };
  return h('div', { class: 'timeline-wrap' },
    h('div', { class: 'timeline-actions' },
      h('button', { type: 'button', class: 'btn btn-small btn-primary', id: 'run-checks', disabled: p.running || Boolean(c.corrupt), onClick: () => app.runPipeline() }, `▶ ${t('tl.run')}`),
      c.events?.length ? h('button', { type: 'button', class: 'btn btn-small', id: 'replay-run', disabled: p.running, onClick: () => app.replayRun() }, `⟲ ${t('tl.replay')}`) : null,
      h('span', { class: 'muted tl-note' }, t('tl.note')),
      h('span', { class: 'tl-status', 'data-running': String(p.running), id: 'pipeline-status' }, p.running ? t('tl.running') : (p.lastResult ? (p.lastResult.ok ? t('tl.doneOk') : t('tl.doneFail', { n: p.lastResult.errors })) : ''))),
    p.timeline.length
      ? h('ol', { class: 'timeline', 'aria-label': t('panel.timeline') }, p.timeline.map((e) => h('li', { class: `tl-item${e.errors ? ' tl-bad' : ''}${e.replay ? ' tl-replay' : ''}`, 'data-node': e.node },
        h('span', { class: 'tl-time mono' }, time(e.at)),
        h('span', { class: 'tl-node' }, t(`node.${e.node}`)),
        h('span', { class: 'tl-text' }, e.replay ? `${t('tl.replayTag')} ` : '', e.text, e.recordedAt ? h('span', { class: 'muted' }, ` · ${t('tl.recordedAt')} ${e.recordedAt}`) : null),
        h('span', { class: 'tl-ms mono muted' }, typeof e.ms === 'number' ? `${e.ms < 1 ? e.ms.toFixed(2) : e.ms.toFixed(1)} ms` : ''))))
      : h('p', { class: 'muted' }, t('tl.empty')));
}

// ---- views opened from nodes that had no screen before
function checksScreen(app) {
  const t = app.t;
  const c = app.state.current;
  const p = c.pipe;
  const rows = ['input', 'schema', 'query', 'sources', 'evidence', 'candidates', 'run'];
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('checks.title')),
    h('p', { class: 'note-line' }, t('checks.help')),
    tableWrap(t('checks.title'), h('table', { id: 'checks-table' },
      h('caption', {}, t('checks.title')),
      h('thead', {}, h('tr', {}, [t('checks.step'), t('checks.result'), t('checks.detail')].map((x) => h('th', { scope: 'col' }, x)))),
      h('tbody', {}, rows.map((id) => h('tr', { 'data-node': id },
        h('th', { scope: 'row' }, t(`node.${id}`), h('span', { class: 'cell-sub' }, t(`node.${id}.desc`))),
        h('td', {}, badge(t(`nstate.${p.states[id]}`), { pass: 'success', fail: 'danger', warn: 'warning', running: 'info' }[p.states[id]] || 'neutral', { 'data-state': p.states[id] })),
        h('td', {}, p.info[id]?.summary || '—')))))),
    c.validation?.checks?.length ? h('p', { class: 'muted' }, c.validation.checks.map((x) => `${x.check}: ${x.result}`).join(' · ')) : null,
    h('p', {}, h('button', { type: 'button', class: 'btn btn-primary', id: 'checks-run', disabled: p.running || Boolean(c.corrupt), onClick: () => app.runPipeline() }, `▶ ${t('tl.run')}`)));
}

function sourcesScreen(app) {
  const t = app.t;
  const c = app.state.current;
  const pid = enc(c.project.projectId);
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('sources.title')),
    h('p', { class: 'note-line' }, t('sources.help')),
    h('ul', { class: 'fact-list' }, c.dossier.sources.map((s) => {
      const ev = c.dossier.evidence.find((e) => e.source_id === s.source.source_id);
      return h('li', {},
        h('p', { class: 'fact-statement' }, h('span', { class: 'mono wrap' }, s.source.source_id), ' ', s.synthetic ? badge(t('source.synthetic'), 'synthetic') : badge(t('source.public'), 'info')),
        h('p', { class: 'fact-meta' }, h('span', { class: 'muted' }, `${s.source.source_type} · ${s.source.version_label} · ${s.jurisdiction} · ${s.source_date}`)),
        h('p', { class: 'muted mono wrap' }, `sha256 ${s.source.sha256}`),
        h('p', { class: 'muted' }, s.source.license_note),
        ev ? h('a', { class: 'btn btn-small', href: `#/project/${pid}/source/${enc(s.source.source_id)}?evidenceId=${enc(ev.evidence_id)}` }, t('overview.inspect')) : null);
    })));
}

function agentScreen(app) {
  const t = app.t;
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('node.agent')),
    callout('info', t('agent.title'), h('p', {}, t('agent.body')), h('p', {}, t('cap.reason.runStart'))),
    h('p', { class: 'muted' }, t('agent.future')));
}

// ---- import page mini pipeline (live)
function importPipe(app) {
  const t = app.t;
  const ip = app.state.importPipe;
  const stages = ['schema', 'query', 'sources', 'evidence', 'candidates'];
  return h('ol', { class: 'mini-pipe', id: 'import-pipe', 'aria-label': t('import.pipe') },
    stages.map((s) => {
      const st = ip?.states[s] || 'idle';
      const info = ip?.info[s];
      return h('li', { class: 'mini-node', 'data-state': st },
        h('span', { class: 'mini-title' }, t(`node.${s}`)),
        h('span', { class: 'mini-state' }, t(`nstate.${st}`)),
        info ? h('span', { class: 'mini-sub muted' }, `${info.ok}/${info.n} · ${info.ms.toFixed(1)} ms`) : null);
    }));
}

export function savedTimeText(app) {
  const c = app.state.current;
  const time = fmtTime(app.state.locale, c.base.savedAt);
  return time ? app.t('header.lastSaved', { time }) : app.t('header.notSavedYet');
}

function saveBar(app) {
  const t = app.t;
  const c = app.state.current;
  return h('div', { class: 'save-bar' },
    h('div', { class: 'save-text' },
      h('span', { id: 'save-status', class: 'save-status', 'data-state': c.saveState }, t(app.saveLabelKey(c))),
      h('span', { id: 'save-time', class: 'muted' }, savedTimeText(app)),
      c.kind === 'draft' ? h('span', { id: 'save-snapshot', class: 'visually-hidden' }, c.base.snapshotId || '') : null),
    h('button', { type: 'button', class: 'btn btn-small', id: 'save-now', disabled: Boolean(c.corrupt) || c.saveState === 'conflict', onClick: () => app.saveNow() }, t('save.now')),
    h('button', { type: 'button', class: 'btn btn-small', id: 'download-recovery', onClick: () => app.downloadRecovery() }, t('save.recovery')));
}

function saveErrorPanel(app) {
  const t = app.t;
  const c = app.state.current;
  if (c.saveState === 'quota') return errorBanner(t, { title: t('save.quota'), action: 'save', target: c.project.projectId, outcome: `${c.saveError?.code}: ${c.saveError?.message}`, preserved: t('storage.scope.memory'), next: t('save.recovery'), diag: c.saveError?.diag });
  if (c.saveState === 'failed') return errorBanner(t, { title: t('save.unsaved'), action: 'save', target: c.project.projectId, outcome: `${c.saveError?.code}: ${c.saveError?.message}`, preserved: t('storage.scope.memory'), next: t('save.recovery'), diag: c.saveError?.diag });
  if (c.storageScope === 'memory') return callout('warning', t('save.memory'), h('p', {}, t('storage.memory')));
  return null;
}

function overlaySummary(t, o) {
  const lines = [];
  for (const n of o.notes) lines.push(`${t('note.basis')} ${n.noteId} (${n.targetRef}): ${n.text}`);
  for (const r of o.requestDrafts) lines.push(`${t('requests.question')} ${r.requestId}: ${r.question}`);
  for (const f of o.featureLinks) lines.push(`${f.feature}: ${f.evidenceIds.join(', ') || '—'}`);
  return lines.join('\n') || '—';
}

function conflictPanel(app) {
  const t = app.t;
  const c = app.state.current;
  if (!c.conflict) return null;
  // Readable texts first; IDs and the full technical summary stay in a disclosure.
  const texts = (o) => [...o.notes.map((n) => n.text), ...o.requestDrafts.map((r) => r.question)].filter((x) => x.trim());
  const col = (title, id, o) => h('div', { class: 'conflict-col' }, h('h3', {}, title),
    h('ul', { class: 'plain-list', id }, texts(o).length ? texts(o).map((x) => h('li', {}, x)) : h('li', { class: 'muted' }, t('conflict.empty'))),
    copyButton(overlaySummary(t, o), t));
  return h('section', { class: 'callout callout-danger conflict', id: 'conflict-panel', role: 'alert', 'aria-labelledby': 'conflict-title' },
    h('h2', { id: 'conflict-title' }, t('conflict.title')),
    h('p', {}, t('save.conflict'), ' ', t('conflict.help')),
    h('p', { class: 'next-title' }, t('conflict.textsOnly')),
    h('div', { class: 'conflict-grid' },
      col(t('conflict.base'), 'conflict-base', c.conflict.base.overlay),
      col(t('conflict.theirs'), 'conflict-theirs', c.conflict.theirs.overlay),
      col(t('conflict.yours'), 'conflict-yours', c.overlay)),
    h('details', { class: 'tech' }, h('summary', {}, t('common.details')),
      h('p', { class: 'mono' }, `expectedParent=${c.conflict.base.snapshotId} · actualParent=${c.conflict.theirs?.snapshotId} · ${c.conflict.diag}`),
      h('p', { class: 'mono' }, `changed: ${overlayDiff(c.conflict.base.overlay, c.overlay).join(', ') || '—'}`)),
    h('div', { class: 'actions' },
      h('button', { type: 'button', class: 'btn btn-primary', id: 'conflict-reapply', onClick: () => app.resolveConflict('reapply') }, t('conflict.reapply')),
      h('button', { type: 'button', class: 'btn', id: 'conflict-copy', onClick: () => app.resolveConflict('copy') }, t('conflict.copy')),
      h('button', { type: 'button', class: 'btn', id: 'conflict-download', onClick: () => { download(`${app.fileStem()}-conflict.json`, app.conflictBundle()); app.announce(t('export.started'), { toast: true }); } }, t('conflict.download')),
      h('button', { type: 'button', class: 'btn btn-quiet', id: 'conflict-theirs-btn', onClick: () => { if (confirm(`${t('conflict.loadTheirs')}?`)) app.resolveConflict('theirs'); } }, t('conflict.loadTheirs'))));
}

function corruptPanel(app) {
  const t = app.t;
  const c = app.state.current;
  if (!c.corrupt) return null;
  return h('section', { class: 'callout callout-danger', id: 'corrupt-panel', role: 'alert' },
    h('h2', {}, t('corrupt.title')), h('p', {}, t('corrupt.help', { reason: c.corrupt.reason })),
    h('p', { class: 'mono muted' }, c.corrupt.diag),
    h('div', { class: 'actions' },
      h('button', { type: 'button', class: 'btn btn-primary', onClick: () => app.downloadRecovery() }, t('save.recovery')),
      h('button', { type: 'button', class: 'btn', onClick: () => { download(`${app.fileStem()}-stored-records.json`, JSON.stringify({ project: c.project, snapshots: c.snapshots }, null, 2)); app.announce(t('export.started'), { toast: true }); } }, 'Download raw stored records')));
}

// ------------------------------------------------------------------ CMP-11 note editor
function noteEditor(app, targetRef, label) {
  const t = app.t;
  const c = app.state.current;
  const ro = Boolean(c.corrupt);
  const notes = c.overlay.notes.filter((n) => n.targetRef === targetRef);
  const upd = (id, k, v, rerender = false) => app.edit((o) => { const n = o.notes.find((x) => x.noteId === id); if (n) n[k] = v; }, { rerender });
  return h('div', { class: 'note-editor', 'data-target': targetRef },
    h('p', { class: 'note-line' }, t('note.help')),
    notes.map((n) => h('div', { class: 'note', 'data-note': n.noteId },
      field(t('note.short'),
        h('textarea', { id: `note-${n.noteId}`, rows: 3, disabled: ro, lang: '', onInput: (e) => upd(n.noteId, 'text', e.target.value) }, n.text),
        `${t('note.target')}: ${label || targetRef}`),
      field(t('note.marker'), h('select', { id: `marker-${n.noteId}`, disabled: ro, onChange: (e) => upd(n.noteId, 'reviewMarker', e.target.value) },
        MARKERS.map((m) => h('option', { value: m, selected: n.reviewMarker === m }, t(`note.marker.${m}`)))), t('note.reviewLimit')),
      h('div', { class: 'actions' },
        h('button', { type: 'button', class: 'btn btn-small', disabled: ro, onClick: () => {
          const requestId = newId('request');
          app.edit((o) => o.requestDrafts.push({ requestId, question: n.text, evidenceRefs: [targetRef], priority: 'normal', intendedRole: null, status: 'draft' }));
          app.go(`#/project/${enc(c.project.projectId)}/requests?focus=${requestId}`);
        } }, t('note.toRequest')),
        h('button', { type: 'button', class: 'btn btn-small btn-quiet', disabled: ro, onClick: () => app.edit((o) => { o.notes = o.notes.filter((x) => x.noteId !== n.noteId); }, { rerender: true }) }, t('note.delete'))))),
    h('button', { type: 'button', class: 'btn btn-small', id: `add-note-${targetRef}`, disabled: ro, onClick: () => {
      const noteId = newId('note');
      app.edit((o) => o.notes.push({ noteId, targetRef, baseDossierVersion: c.dossier.version, text: '', basis: 'user_note', reviewMarker: 'none' }), { rerender: true });
      document.getElementById(`note-${noteId}`)?.focus();
    } }, t('note.add')));
}

// ------------------------------------------------------------------ SCR-06 overview
function candidateScopeText(t, c) {
  return t({ empty_corpus: 'candidate.emptyCorpus', no_results: 'candidate.noResults' }[c.candidateScope] || 'candidate.unknownScope');
}

function overviewScreen(app) {
  const t = app.t;
  const c = app.state.current;
  const d = c.dossier;
  const pid = enc(c.project.projectId);
  const facts = d.evidence.filter((e) => ['source_fact', 'regulatory_record', 'trial_record', 'reported_experiment'].includes(e.evidence_kind));
  const partial = c.sim.partial ? callout('warning', t('state.partial'), h('p', {}, t('overview.partial')),
    h('p', { class: 'mono' }, 'failedSource=ux-synthetic-patent-source-unavailable · outcome=not_executed'), badge(t('mode.simulation'), 'synthetic')) : null;
  const edits = Object.entries(d.user_edits || {});
  const linked = d.candidates.filter((x) => x.association_status === 'disclosed_link').length;
  const requestCount = d.next_information_requests.length + c.overlay.requestDrafts.length;
  // Counts are navigation aids (how much is here), never quality scores.
  // In-page targets move focus instead of changing the hash (the hash is the router).
  const tile = (label, value, target, sub) => h('li', {}, h('a', {
    class: 'tile', href: target.startsWith('#/') ? target : `#/project/${pid}`,
    onClick: target.startsWith('#/') ? null : (e) => { e.preventDefault(); const el = document.getElementById(target.slice(1)); el?.scrollIntoView({ block: 'start' }); el?.focus({ preventScroll: true }); },
  }, h('span', { class: 'tile-value' }, String(value)), h('span', { class: 'tile-label' }, label), sub ? h('span', { class: 'tile-sub' }, sub) : null));
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('nav.overview')),
    partial,
    h('h2', { class: 'visually-hidden' }, t('summary.title')),
    h('ul', { class: 'tiles', 'aria-label': t('summary.title') },
      tile(t('summary.facts'), facts.length, '#facts'),
      tile(t('summary.candidates'), d.candidates.length, '#candidates', d.candidates.length ? t('summary.linked', { n: linked }) : null),
      tile(t('summary.unresolved'), d.unresolved_items.length, '#unresolved'),
      tile(t('summary.requests'), requestCount, `#/project/${pid}/requests`),
      tile(t('summary.notes'), c.overlay.notes.length, '#notes')),
    h('nav', { class: 'next-steps', 'aria-label': t('next.title') },
      h('p', { class: 'next-title' }, t('next.title')),
      h('ol', {},
        h('li', {}, h('a', { href: `#/project/${pid}/evidence` }, t('next.evidence'))),
        h('li', {}, h('a', { href: `#/project/${pid}/requests` }, t('next.requests'))),
        h('li', {}, h('a', { href: `#/project/${pid}/export` }, t('next.export'))))),
    h('section', { class: 'panel', id: 'facts', tabindex: '-1' },
      h('h2', {}, t('overview.facts')),
      h('p', { class: 'note-line' }, t('integrity.note')),
      h('ul', { class: 'fact-list' }, facts.map((e) => h('li', {},
        h('p', { class: 'fact-statement' }, e.statement),
        h('p', { class: 'fact-meta' }, integrityBadge(t, e.verification_status), ' ', h('span', { class: 'muted' }, `${t('source.from')}: ${e.source_id} · ${e.source_date}`), ' ',
          h('a', { href: `#/project/${pid}/source/${enc(e.source_id)}?evidenceId=${enc(e.evidence_id)}` }, t('overview.inspect')))))),
      d.sources.some((s) => /decision/.test(JSON.stringify(s.payload))) ? h('p', { class: 'muted' }, t('overview.decisionCode')) : null),
    h('section', { class: 'panel', id: 'candidates', tabindex: '-1' },
      h('h2', {}, t('overview.candidates')),
      d.candidates.length
        ? h('div', {},
          h('ul', { class: 'fact-list' }, d.candidates.map((x) => h('li', {},
            h('p', { class: 'fact-statement' }, h('span', { class: 'mono' }, x.patent_id_canonical), ' ', relationBadge(t, x)),
            h('p', { class: 'muted' }, relationExplain(t, x))))),
          h('p', { class: 'note-line' }, t('patent.notLegal')))
        : callout('info', candidateScopeText(t, c), h('p', { class: 'mono muted', id: 'candidate-scope', 'data-scope': c.candidateScope }, `scope=${c.candidateScope}`))),
    h('section', { class: 'panel', id: 'unresolved', tabindex: '-1' },
      h('h2', {}, t('overview.unresolved')),
      h('ul', { class: 'plain-list' }, d.unresolved_items.map((u) => h('li', {}, u)))),
    h('section', { class: 'panel' },
      h('h2', {}, t('overview.requests')),
      h('ul', { class: 'plain-list' }, d.next_information_requests.map((r) => h('li', {}, r))),
      h('a', { class: 'btn', href: `#/project/${pid}/requests` }, t('overview.addQuestion'))),
    edits.length ? panel(t('overview.importedEdits'), kv(edits.map(([k, v]) => [k, v]))) : null,
    h('section', { class: 'panel', id: 'notes', tabindex: '-1' },
      h('h2', {}, t('overview.notes')),
      noteEditor(app, 'dossier', d.dossier_id)));
}

// ------------------------------------------------------------------ SCR-07 evidence and compare
function kindCode(canonical) {
  const m = /^([A-Z]{2})(\d+)([A-Z]\d?)?$/.exec(canonical);
  return m ? { jurisdiction: m[1], kind: m[3] || null } : { jurisdiction: null, kind: null };
}

function evidenceScreen(app) {
  const t = app.t;
  const c = app.state.current;
  const d = c.dossier;
  const pid = enc(c.project.projectId);
  c.ui = c.ui || { filter: '', sort: 'imported', compare: [] };
  const ui = c.ui;
  const evTable = h('table', {},
    h('caption', {}, t('evidence.tabEvidence')),
    h('thead', {}, h('tr', {}, [t('evidence.statement'), t('evidence.check'), t('source.from'), ''].map((x) => h('th', { scope: 'col' }, x)))),
    h('tbody', {}, d.evidence.map((e) => h('tr', { id: `row-${e.evidence_id}`, tabindex: '-1' },
      h('th', { scope: 'row' }, h('span', { class: 'fact-statement' }, e.statement),
        h('span', { class: 'cell-sub' }, `${t(`kind.${e.evidence_kind}`)} · ${t(basisKey(e))}`)),
      h('td', {}, integrityBadge(t, e.verification_status)),
      h('td', {}, h('span', { class: 'mono wrap' }, e.source_id), h('span', { class: 'cell-sub' }, `${e.source_date} · ${t('evidence.locator')} `, h('span', { class: 'mono' }, e.locator))),
      h('td', {}, h('a', { class: 'btn btn-small', id: `inspect-${e.evidence_id}`, href: `#/project/${pid}/source/${enc(e.source_id)}?evidenceId=${enc(e.evidence_id)}` }, t('overview.inspect')))))));
  const needle = ui.filter.trim().toLowerCase();
  const cands = d.candidates.map((x, i) => ({ ...x, _i: i }));
  const visible = cands.filter((x) => !needle || [x.patent_id_raw, x.patent_id_canonical, x.source_id, x.association_status].some((v) => v.toLowerCase().includes(needle)));
  if (ui.sort === 'id') visible.sort((a, b) => a.patent_id_canonical.localeCompare(b.patent_id_canonical));
  const selected = cands.filter((x) => ui.compare.includes(x.patent_id_canonical));
  const toggle = (id, on) => {
    if (on && ui.compare.length >= 3) { app.announce(t('evidence.compareMax')); app.render({ keepFocus: true }); return; }
    ui.compare = on ? [...ui.compare, id] : ui.compare.filter((x) => x !== id);
    app.render({ keepFocus: true });
  };
  const candRegion = d.candidates.length
    ? h('div', {},
      h('div', { class: 'filters' },
        field(t('evidence.filter'), h('input', { type: 'search', id: 'cand-filter', value: ui.filter, onInput: (e) => { ui.filter = e.target.value; app.render({ keepFocus: true }); } })),
        field(t('evidence.sort'), h('select', { id: 'cand-sort', onChange: (e) => { ui.sort = e.target.value; app.render({ keepFocus: true }); } },
          h('option', { value: 'imported', selected: ui.sort === 'imported' }, t('evidence.sortImported')), h('option', { value: 'id', selected: ui.sort === 'id' }, t('evidence.sortId'))))),
      h('p', { 'aria-live': 'polite', id: 'compare-count' }, t('evidence.showing', { shown: visible.length, total: d.candidates.length }), ' · ', t('evidence.compareSelected', { n: ui.compare.length })),
      h('ul', { class: 'cand-list' }, visible.map((x) => h('li', { class: 'cand-row' },
        h('input', { type: 'checkbox', id: `cmp-${x.patent_id_canonical}`, checked: ui.compare.includes(x.patent_id_canonical), onChange: (e) => toggle(x.patent_id_canonical, e.target.checked) }),
        h('label', { for: `cmp-${x.patent_id_canonical}` }, `${t('evidence.compare')}: `, h('span', { class: 'mono' }, x.patent_id_canonical)),
        ' ', relationBadge(t, x)))),
      selected.filter((x) => !visible.some((v) => v.patent_id_canonical === x.patent_id_canonical)).map((x) => h('p', { class: 'muted' }, `${x.patent_id_canonical}: ${t('evidence.hiddenByFilter')}`)),
      selected.length ? tableWrap(t('evidence.compare'), compareTable(app, selected)) : null,
      h('p', { class: 'muted' }, t('evidence.familyNone'), ' ', t('patent.notLegal')))
    : callout('info', candidateScopeText(t, c));
  const features = d.query.features_of_interest;
  const featRegion = h('div', {},
    h('p', { class: 'muted' }, t('evidence.featureNone')),
    features.length ? h('ul', { class: 'feature-list' }, features.map((f, fi) => {
      const link = c.overlay.featureLinks.find((x) => x.feature === f);
      const ids = link?.evidenceIds || [];
      return dropOn(h('li', { class: 'feature', 'data-drop': 'evidence', 'data-drop-label': f },
        h('h3', {}, f),
        h('p', { class: 'drop-hint muted' }, t('lib.dropFeature')),
        ids.length ? h('p', {}, badge(t('evidence.userLinked'), 'synthetic'), ' ', ids.join(', ')) : h('p', {}, badge(t('evidence.featureUnresolved'), 'warning')),
        h('fieldset', { class: 'checks' }, h('legend', {}, t('evidence.featureLink')),
          d.evidence.map((e) => h('div', {}, h('input', { type: 'checkbox', id: `fl-${fi}-${e.evidence_id}`, checked: ids.includes(e.evidence_id), disabled: Boolean(c.corrupt),
            onChange: (ev) => app.edit((o) => {
              let l = o.featureLinks.find((x) => x.feature === f);
              if (!l) { l = { feature: f, evidenceIds: [], basis: 'user_authored' }; o.featureLinks.push(l); }
              l.evidenceIds = ev.target.checked ? [...new Set([...l.evidenceIds, e.evidence_id])] : l.evidenceIds.filter((x) => x !== e.evidence_id);
            }, { rerender: true }) }), h('label', { for: `fl-${fi}-${e.evidence_id}` }, e.evidence_id))))), (item) => app.linkFeature(f, item.payload));
    })) : h('p', {}, t('evidence.notSupplied')));
  // WAI-ARIA tabs: one tab stop, arrow/Home/End move between tabs, panels labelled by their tab.
  const tabs = [['evidence', t('evidence.tabEvidence'), d.evidence.length], ['candidates', t('evidence.tabCandidates'), d.candidates.length], ['features', t('evidence.tabFeatures'), features.length]];
  const active = tabs.some(([k]) => k === ui.tab) ? ui.tab : 'evidence';
  const select = (k) => { ui.tab = k; app.render(); document.getElementById(`tab-${k}`)?.focus(); };
  const onKey = (e) => {
    const i = tabs.findIndex(([k]) => k === active);
    const next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
    if (next === undefined) return;
    e.preventDefault();
    select(tabs[(next + tabs.length) % tabs.length][0]);
  };
  const body = { evidence: [h('p', { class: 'note-line' }, t('integrity.note')), tableWrap(t('evidence.tabEvidence'), evTable)], candidates: candRegion, features: featRegion }[active];
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('evidence.title')),
    h('div', { class: 'tablist', role: 'tablist', 'aria-label': t('evidence.title'), onKeydown: onKey },
      tabs.map(([k, label, n]) => h('button', { type: 'button', role: 'tab', id: `tab-${k}`, 'aria-selected': String(k === active), 'aria-controls': `panel-${k}`, tabindex: k === active ? '0' : '-1', onClick: () => select(k) },
        label, ' ', h('span', { class: 'tab-count' }, String(n))))),
    h('div', { role: 'tabpanel', id: `panel-${active}`, 'aria-labelledby': `tab-${active}`, tabindex: '0', class: 'tabpanel' }, body));
}

function compareTable(app, selected) {
  const t = app.t;
  const pid = enc(app.state.current.project.projectId);
  const rows = [
    ['Raw ID', (x) => x.patent_id_raw], ['Canonical ID', (x) => x.patent_id_canonical],
    [t('device.jurisdiction'), (x) => kindCode(x.patent_id_canonical).jurisdiction || t('evidence.notSupplied')],
    ['Kind code', (x) => kindCode(x.patent_id_canonical).kind || t('evidence.notSupplied')],
    [t('evidence.source'), (x) => `${x.source_id} / ${x.source_revision}`],
    ['association_status', (x) => relationBadge(t, x)],
    [t('evidence.disclosure'), (x) => (x.disclosure_evidence_id ? h('a', { href: `#/project/${pid}/source/${enc(app.state.current.dossier.evidence.find((e) => e.evidence_id === x.disclosure_evidence_id)?.source_id || '')}?evidenceId=${enc(x.disclosure_evidence_id)}` }, x.disclosure_evidence_id) : t('evidence.notSupplied'))],
    [t('evidence.scores'), (x) => Object.entries(x.scores).map(([k, v]) => `${k}=${v}`).join('; ') || t('evidence.notSupplied')],
    [t('evidence.family'), (x) => (x.family_id ? `${x.family_id} (${x.family_source_id})` : t('evidence.notSupplied'))],
  ];
  return h('table', { id: 'compare-table' }, h('caption', {}, t('evidence.compare')),
    h('thead', {}, h('tr', {}, h('td', {}), selected.map((x) => h('th', { scope: 'col', class: 'mono' }, x.patent_id_canonical)))),
    h('tbody', {}, rows.map(([label, fn]) => h('tr', {}, h('th', { scope: 'row' }, label), selected.map((x) => h('td', {}, fn(x)))))));
}

// ------------------------------------------------------------------ SCR-08 source viewer
function sourceScreen(app) {
  const t = app.t;
  const c = app.state.current;
  const sv = app.state.sourceView;
  const q = app.state.route.query;
  const pid = enc(c.project.projectId);
  const src = c.dossier.sources.find((s) => s.source.source_id === app.state.route.params.sourceId);
  const back = h('a', { class: 'btn', id: 'source-back', href: `#/project/${pid}/evidence${q.evidenceId ? `?focus=${enc(q.evidenceId)}` : ''}` }, `← ${t('source.back')}`);
  if (!src) return h('section', {}, h('h1', { tabindex: '-1' }, t('source.title')), errorBanner(t, { action: 'inspect source', target: app.state.route.params.sourceId, outcome: 'not in this pinned dossier', next: t('import.rejectedHelp') }), back);
  const r = src.source;
  const ev = sv?.evidence;
  const check = sv?.check;
  let exact = null;
  if (ev && check) {
    if (!check.ok) {
      exact = h('div', { id: 'source-mismatch', 'data-code': check.code },
        errorBanner(t, { title: t('source.mismatch'), action: 'check citation', target: `${ev.evidence_id} · ${ev.locator}`, outcome: `${check.code}: ${check.message}`, preserved: `${t('evidence.locator')}: ${ev.locator} · payload_hash ${ev.payload_hash}`, next: t('source.mismatchHelp') }));
    } else if (check.span) {
      const loc = parseLocator(ev.locator);
      exact = h('div', {},
        h('p', {}, integrityBadge(t, check.status), ' ', h('span', { class: 'muted' }, t('source.codepoints', { start: loc.start, end: loc.end, len: check.span.length }))),
        h('pre', { class: 'payload', id: 'source-text' }, check.span.before, h('mark', { id: 'source-span' }, check.span.span), check.span.after));
    } else if (check.field) {
      exact = h('div', {},
        h('p', {}, integrityBadge(t, check.status)),
        kv([[ev.structured_field, h('mark', { id: 'source-field', class: 'mono' }, JSON.stringify(check.field.value))], ['type', Array.isArray(check.field.value) ? 'array' : check.field.value === null ? 'null' : typeof check.field.value]]));
    }
  }
  const simLinks = c.mode === 'synthetic_demo' && ev ? h('p', { class: 'actions' },
    h('a', { class: 'btn btn-small', href: `#/project/${pid}/source/${enc(r.source_id)}?evidenceId=${enc(ev.evidence_id)}&sim=fx12` }, t('source.simulateBad')),
    h('a', { class: 'btn btn-small', href: `#/project/${pid}/source/${enc(r.source_id)}?evidenceId=${enc(ev.evidence_id)}&sim=fx14` }, t('source.simulateStale'))) : null;
  return h('section', { class: 'source-view' },
    h('h1', { tabindex: '-1' }, t('source.title')),
    back,
    q.sim ? badge(`${t('mode.simulation')} — ${q.sim.toUpperCase()}`, 'synthetic') : null,
    q.sim === 'fx14' ? callout('warning', t('source.stale', { available: 'ux-authored-v2', pinned: r.version_label }), h('p', { class: 'mono' }, 'autoRebind=false')) : null,
    ev ? [h('h2', {}, t('source.cited')), kv([[t('evidence.statement'), ev.statement], ['support_basis', ev.support_basis], [t('evidence.kind'), `${t(`kind.${ev.evidence_kind}`)} — ${t(basisKey(ev))}`], [t('evidence.locator'), h('span', { class: 'mono' }, ev.locator)]])] : null,
    ev ? [h('h2', {}, t('source.exact')), exact, h('p', { class: 'muted' }, t('integrity.limit'))] : null,
    h('h2', {}, t('source.identity')),
    kv([
      ['source_id', h('span', {}, h('span', { class: 'mono wrap' }, r.source_id), ' ', copyButton(r.source_id, t))],
      ['source_type', r.source_type],
      [t('device.revision'), h('span', {}, h('span', { class: 'mono' }, r.version_label), ' ', copyButton(r.version_label, t))],
      ['sha256', h('span', {}, h('span', { class: 'mono wrap' }, r.sha256), ' ', copyButton(r.sha256, t))],
      [t('device.jurisdiction'), src.jurisdiction], ['source_date', src.source_date],
      ['retrieved_at', r.retrieved_at || t('value.unknown')],
      ['', src.synthetic ? badge(t('source.synthetic'), 'synthetic') : badge(t('source.public'), 'info')],
      [t('source.uri'), h('span', {}, h('span', { class: 'mono wrap', id: 'source-uri' }, r.uri), ' ', copyButton(r.uri, t))],
      [t('source.rights'), h('span', {}, r.license_note, h('br'), h('span', { class: 'muted' }, t('source.rightsUnresolved')))],
    ]),
    h('details', { class: 'disclosure' }, h('summary', {}, t('source.payload')),
      h('p', { class: 'muted' }, t('source.inert')),
      h('pre', { class: 'payload', id: 'source-payload' }, typeof src.payload === 'string' ? src.payload : JSON.stringify(src.payload, null, 2))),
    simLinks,
    ev ? [h('h2', {}, t('overview.notes')), noteEditor(app, ev.evidence_id, ev.evidence_id)] : null);
}

// ------------------------------------------------------------------ SCR-05 run receipt
function runsScreen(app) {
  const t = app.t;
  const c = app.state.current;
  const sum = summarizeRun(c.dossier, c.manifest, c.events);
  const sim = c.sim;
  const receipt = sum.available
    ? h('div', { id: 'run-receipt' },
      h('p', {}, badge(t('mode.importedRun'), 'neutral'), ' ', t('run.scopeComplete')),
      kv([
        [t('runs.policy'), `${sum.policyId} (${sum.evidenceLevel || t('value.unknown')})`],
        [t('runs.calls'), `${known(t, sum.callsUsed)} / ${known(t, sum.callsCap)}`],
        [t('runs.unique'), known(t, sum.uniqueCandidates)],
        [t('runs.returned'), known(t, sum.returnedOccurrences)],
        [t('runs.retries'), known(t, sum.retries)],
        [t('runs.stop'), sum.stopReason || t('value.unknown')],
        [t('runs.completed'), sum.completedQueries.join(', ') || '—'],
        [t('runs.failed'), sum.failedQueries.join(', ') || '—'],
        [t('runs.cost'), sum.cost.actualUsd.status === 'known' ? t('runs.costZero', { basis: sum.cost.basis }) : `${t('value.unknown')} (${sum.cost.actualUsd.reason})`],
        [t('budget.offline'), ''],
      ]),
      h('p', { id: 'run-consistency', 'data-consistent': String(sum.consistent) }, sum.consistent ? t('runs.consistent') : t('runs.inconsistent')),
      h('details', { class: 'disclosure' }, h('summary', {}, t('common.details')),
        tableWrap(t('runs.events'), h('table', {}, h('caption', {}, t('runs.events')),
          h('thead', {}, h('tr', {}, ['step_id', 'action', 'calls', 'returned', 'new', 'started_at', 'stop_reason', 'errors'].map((x) => h('th', { scope: 'col' }, x)))),
          h('tbody', {}, sum.events.map((e) => h('tr', {}, h('th', { scope: 'row', class: 'mono' }, e.stepId), h('td', {}, e.action), h('td', {}, e.calls), h('td', {}, e.returned), h('td', {}, e.newCount), h('td', { class: 'mono' }, e.startedAt), h('td', {}, e.stopReason || '—'), h('td', {}, e.errors.join('; ') || '—')))))),
        h('ul', {}, sum.limitations.map((l) => h('li', {}, l)))))
    : callout('info', t('runs.none'), h('p', {}, t('runs.calls'), ': ', t('value.unknown'), ' · ', t('runs.cost'), ': ', t('value.unknown')));
  let simView = null;
  if (c.mode === 'synthetic_demo') {
    const set = (patch) => { Object.assign(sim, patch); app.render({ keepFocus: true }); };
    const stages = ['technical_search', 'feature_search', 'stop'];
    let body = null;
    if (sim.scenario === 'loading') {
      body = h('div', { role: 'status' }, h('p', {}, t('run.loadingSim', { n: (sim.stage || 0) + 1 })), h('ol', {}, stages.map((s, i) => h('li', { 'aria-current': i === (sim.stage || 0) ? 'step' : null }, s, i < (sim.stage || 0) ? ' ✓' : ''))),
        h('button', { type: 'button', class: 'btn btn-small', onClick: () => set({ stage: Math.min((sim.stage || 0) + 1, stages.length - 1) }) }, '→'));
    } else if (sim.scenario === 'partial') {
      body = callout('warning', t('state.partial'), h('p', {}, 'failedSource=ux-synthetic-patent-source-unavailable · outcome=not_executed · preservedEvidence=ux-e-device'), h('p', {}, t('runs.noStart')));
    } else if (sim.scenario === 'blocked') {
      body = callout('info', t('cap.runStart'), h('p', {}, t('cap.reason.runStart')), h('div', { class: 'actions' }, h('a', { class: 'btn', href: '#/import' }, t('start.import'))));
    } else if (sim.scenario === 'cancel') {
      body = h('div', { role: 'status', id: 'sim-cancel-state', 'data-state': sim.cancel || 'running' },
        !sim.cancel ? h('button', { type: 'button', class: 'btn', id: 'sim-cancel-btn', onClick: () => { set({ cancel: 'pending' }); setTimeout(() => { if (sim.cancel === 'pending') set({ cancel: 'acknowledged' }); }, 1200); } }, t('run.requestCancel')) : null,
        sim.cancel === 'pending' ? h('p', {}, t('run.cancelPending')) : null,
        sim.cancel === 'acknowledged' ? h('p', {}, t('run.cancelled', { steps: 'ux-simulated-step-1' })) : null);
    } else if (sim.scenario === 'billing') {
      const cost = costView(null, app.state.staticData.fixtures.scenarios.find((s) => s.id === 'FX-11').details.cost);
      body = kv([[t('runs.cost'), cost.actualUsd.status === 'known' ? String(cost.actualUsd.value) : `${t('cost.pending')} — ${t('value.unknown')} (${cost.actualUsd.reason})`], ['settlement', cost.settlement], ['accounting', cost.accounting]]);
    }
    simView = h('section', { class: 'sim', 'aria-labelledby': 'sim-title' },
      h('h2', { id: 'sim-title' }, t('runs.simulate')), badge(t('mode.simulation'), 'synthetic'),
      h('div', { class: 'actions' }, [['loading', 'runs.sim.loading'], ['partial', 'runs.sim.partial'], ['blocked', 'runs.sim.blocked'], ['cancel', 'runs.sim.cancel'], ['billing', 'runs.sim.billing']]
        .map(([k, label]) => h('button', { type: 'button', class: 'btn btn-small', 'aria-pressed': String(sim.scenario === k), id: `sim-${k}`, onClick: () => set({ scenario: k, stage: 0, cancel: null, partial: k === 'partial' }) }, t(label)))),
      body);
  }
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('runs.title')),
    callout('info', null, h('p', {}, t('runs.noStart')), h('p', { class: 'muted' }, t('cap.reason.runStart'))),
    receipt, simView);
}

// ------------------------------------------------------------------ SCR-09 history
function historyScreen(app) {
  const t = app.t;
  const c = app.state.current;
  const snaps = [...c.snapshots].sort((a, b) => String(b.savedAt).localeCompare(String(a.savedAt)));
  const byId = new Map(c.snapshots.map((s) => [s.snapshotId, s]));
  const backendVersions = c.backendHistory?.history?.versions || [];
  let backendBody;
  if (!app.state.backend) {
    backendBody = h('p', { id: 'backend-history-unavailable', class: 'muted' }, t('backend.noConnection'));
  } else if (c.backendHistoryLoading) {
    backendBody = h('p', { id: 'backend-history-loading', role: 'status' }, t('backend.historyLoading'));
  } else if (c.backendHistoryError) {
    backendBody = callout('danger', t('backend.historyTitle'), h('p', { id: 'backend-history-error' }, t('backend.historyError', { message: c.backendHistoryError.message })));
  } else {
    const rows = backendVersions.map((v) => h('tr', { 'data-backend-version': String(v.version) },
      h('th', { scope: 'row', class: 'mono' }, v.version, c.backendSelectedVersion === v.version ? [' ', badge('selected', 'info')] : null),
      h('td', { class: 'mono' }, v.parent_version === null ? '—' : String(v.parent_version)),
      h('td', {}, h('button', { type: 'button', class: 'btn btn-small', id: `backend-open-${v.version}`, onClick: () => app.openBackendVersion(v.version) }, t('backend.openVersion', { v: v.version })))));
    backendBody = h('div', { class: 'stack' },
      backendVersions.length ? tableWrap(t('backend.historyTitle'), h('table', { id: 'backend-history-table' },
        h('caption', {}, t('backend.historyTitle')),
        h('thead', {}, h('tr', {}, ['Version', t('history.parent'), ''].map((x) => h('th', { scope: 'col' }, x)))),
        h('tbody', {}, rows))) : h('p', {}, t('history.none')),
      c.backendVersionView ? h('div', { class: 'stack' },
        h('p', { id: 'backend-selected-version' }, t('backend.selectedVersion', { v: c.backendSelectedVersion })),
        h('pre', { id: 'backend-version-view', class: 'payload', tabindex: '0' }, JSON.stringify(c.backendVersionView, null, 2)),
        field(t('backend.editLabel'), h('input', { id: 'backend-edit-note', value: c.backendEditNote || '', placeholder: t('backend.editPlaceholder'), onInput: (e) => { c.backendEditNote = e.target.value; app.render({ keepFocus: true }); } })),
        h('button', { type: 'button', class: 'btn btn-primary', id: 'backend-edit', disabled: !String(c.backendEditNote || '').trim(), onClick: () => app.editBackendVersion() }, t('backend.saveEdit')))
        : null);
  }
  const backendPanel = c.project.backendJobId ? h('section', { id: 'backend-history-panel' }, h('h2', {}, t('backend.historyTitle')), backendBody) : null;
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('history.title')),
    backendPanel || h('div', {}, h('h2', {}, t('history.backend')),
      kv([['dossier_id', c.dossier.dossier_id], ['version', String(c.dossier.version)], ['parent_version', c.dossier.parent_version === null ? 'null' : String(c.dossier.parent_version)], ['sha256 (canonical)', h('span', { class: 'mono wrap' }, c.dossierHash)], [t('cap.backendHistory'), `${t('cap.unavailable')} — ${t('cap.reason.backendHistory')}`]])),
    h('h2', {}, t('history.local')),
    h('p', { class: 'muted' }, t('history.author'), ' ', t('history.limit')),
    c.project.origin?.type === 'recovery' ? h('p', { class: 'muted' }, `Recovered from snapshot ${c.project.origin.recoveredSnapshot || '—'} (lineage ${c.project.origin.recoveredLineage?.join(' ← ') || '—'})`) : null,
    snaps.length ? tableWrap(t('history.local'), h('table', { id: 'history-table' },
      h('caption', {}, t('history.local')),
      h('thead', {}, h('tr', {}, ['ID', t('history.parent'), t('history.time'), t('history.changed'), t('home.storage'), 'sourceDossierHash', ''].map((x) => h('th', { scope: 'col' }, x)))),
      h('tbody', {}, snaps.map((s) => h('tr', { 'data-snapshot': s.snapshotId },
        h('th', { scope: 'row', class: 'mono' }, s.snapshotId, s.snapshotId === c.project.headSnapshotId ? [' ', badge('head', 'info')] : null),
        h('td', { class: 'mono' }, s.parentSnapshotId || '—'),
        h('td', { class: 'mono' }, s.savedAt),
        h('td', {}, (s.changedKeys || overlayDiff(byId.get(s.parentSnapshotId)?.overlay, s.overlay)).join(', ') || '—', s.restoredFrom ? h('div', { class: 'muted' }, t('history.restored', { id: s.restoredFrom })) : null),
        h('td', {}, s.storageScope),
        h('td', { class: 'mono wrap' }, s.sourceDossierHash || '—'),
        h('td', {}, h('details', {}, h('summary', {}, t('history.compare')), h('pre', { class: 'code' }, overlaySummary(t, s.overlay))),
          s.snapshotId !== c.project.headSnapshotId ? h('button', { type: 'button', class: 'btn btn-small', disabled: c.dirty || Boolean(c.corrupt), onClick: () => app.restore(s.snapshotId) }, t('history.restore')) : null)))))) : h('p', {}, t('history.none')));
}

// ------------------------------------------------------------------ SCR-11 requests
function requestsText(app) {
  const t = app.t;
  const c = app.state.current;
  const lines = [`${t('requests.imported')}:`, ...c.dossier.next_information_requests.map((r) => `- [dossier] ${r}`), '', `${t('requests.local')} (${t('note.basis')}):`];
  for (const r of c.overlay.requestDrafts) lines.push(`- [user] ${r.question} | refs: ${r.evidenceRefs.join(', ') || '—'} | ${r.intendedRole || '—'} | ${r.priority} | ${r.status}`);
  return lines.join('\n');
}

/** Reorderable request card: drag handle + up/down buttons; dropping another request moves it here. */
function requestCard(app, r, index, ro, li) {
  const t = app.t;
  const count = app.state.current.overlay.requestDrafts.length;
  const handle = h('span', { class: 'lib-handle', title: t('lib.dragHint'), 'aria-hidden': 'true' }, '⠿');
  li.dataset.drop = 'request';
  li.dataset.dropLabel = `#${index + 1}`;
  li.ondropitem = (item) => (item.payload === r.requestId ? false : app.moveRequest(item.payload, index));
  li.prepend(h('div', { class: 'request-head' }, handle, h('span', { class: 'muted' }, `#${index + 1}`),
    h('button', { type: 'button', class: 'btn btn-tiny', id: `req-up-${r.requestId}`, disabled: ro || index === 0, 'aria-label': t('requests.moveUp'), title: t('requests.moveUp'), onClick: () => { app.moveRequest(r.requestId, index - 1); app.announce(t('requests.moved', { n: index }), { toast: true }); } }, '↑'),
    h('button', { type: 'button', class: 'btn btn-tiny', id: `req-down-${r.requestId}`, disabled: ro || index === count - 1, 'aria-label': t('requests.moveDown'), title: t('requests.moveDown'), onClick: () => { app.moveRequest(r.requestId, index + 1); app.announce(t('requests.moved', { n: index + 2 }), { toast: true }); } }, '↓')));
  if (!ro) draggable(handle, li, { type: 'request', payload: r.requestId, label: r.question || `#${index + 1}` }, (m) => app.announce(m));
  return li;
}

function requestsScreen(app) {
  const t = app.t;
  const c = app.state.current;
  const ro = Boolean(c.corrupt);
  const d = c.dossier;
  const refs = [...d.evidence.map((e) => e.evidence_id), ...d.unresolved_items.map((_, i) => `unresolved:${i}`)];
  const upd = (id, k, v, rerender = false) => app.edit((o) => { const r = o.requestDrafts.find((x) => x.requestId === id); if (r) r[k] = v; }, { rerender });
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('requests.title')),
    callout('info', null, h('p', {}, t('requests.noSend'))),
    h('h2', {}, t('requests.imported')),
    h('ul', {}, d.next_information_requests.map((r) => h('li', {}, r))),
    h('h2', {}, t('requests.local')),
    h('p', { class: 'note-line' }, t('lib.dropRequests')),
    c.overlay.requestDrafts.length ? dropOn(h('ul', { class: 'request-list', 'data-drop': 'evidence gap', 'data-drop-label': t('requests.local') }, c.overlay.requestDrafts.map((r, ri) => requestCard(app, r, ri, ro, h('li', { class: 'request', id: `row-${r.requestId}`, tabindex: '-1' },
      field(t('requests.question'), h('textarea', { id: `req-q-${r.requestId}`, rows: 2, disabled: ro, onInput: (e) => upd(r.requestId, 'question', e.target.value) }, r.question)),
      field(t('requests.role'), h('input', { id: `req-role-${r.requestId}`, value: r.intendedRole || '', disabled: ro, onInput: (e) => upd(r.requestId, 'intendedRole', e.target.value || null) })),
      field(t('requests.priority'), h('select', { id: `req-p-${r.requestId}`, disabled: ro, onChange: (e) => upd(r.requestId, 'priority', e.target.value) }, ['normal', 'high'].map((p) => h('option', { value: p, selected: r.priority === p }, t(`requests.priority.${p}`))))),
      field(t('requests.status'), h('select', { id: `req-s-${r.requestId}`, disabled: ro, onChange: (e) => upd(r.requestId, 'status', e.target.value) }, ['draft', 'done_by_user'].map((p) => h('option', { value: p, selected: r.status === p }, t(`requests.status.${p}`)))), t('requests.doneHelp')),
      h('fieldset', { class: 'checks' }, h('legend', {}, t('requests.refs')), refs.map((ref) => h('div', {},
        h('input', { type: 'checkbox', id: `req-ref-${r.requestId}-${ref}`, checked: r.evidenceRefs.includes(ref), disabled: ro, onChange: (e) => upd(r.requestId, 'evidenceRefs', e.target.checked ? [...r.evidenceRefs, ref] : r.evidenceRefs.filter((x) => x !== ref)) }),
        h('label', { for: `req-ref-${r.requestId}-${ref}`, class: 'mono' }, ref)))),
      h('button', { type: 'button', class: 'btn btn-small btn-quiet', disabled: ro, onClick: () => app.edit((o) => { o.requestDrafts = o.requestDrafts.filter((x) => x.requestId !== r.requestId); }, { rerender: true }) }, t('note.delete')))))), (item) => app.addRequestFrom(item))
      : dropOn(h('p', { class: 'drop-empty', 'data-drop': 'evidence gap', 'data-drop-label': t('requests.local') }, t('requests.empty')), (item) => app.addRequestFrom(item)),
    h('div', { class: 'actions' },
      h('button', { type: 'button', class: 'btn', id: 'add-request', disabled: ro, onClick: () => {
        const requestId = newId('request');
        app.edit((o) => o.requestDrafts.push({ requestId, question: '', evidenceRefs: [], priority: 'normal', intendedRole: null, status: 'draft' }), { rerender: true });
        document.getElementById(`req-q-${requestId}`)?.focus();
      } }, t('requests.add')),
      h('button', { type: 'button', class: 'btn', id: 'copy-requests', onClick: async (e) => {
        const text = requestsText(app);
        try { await navigator.clipboard.writeText(text); app.announce(t('source.copied'), { toast: true }); } catch { const ta = document.getElementById('requests-text'); ta.hidden = false; ta.select(); }
        e.target.focus();
      } }, t('request.copy'))),
    h('textarea', { id: 'requests-text', readonly: true, hidden: true, rows: 6, 'aria-label': t('request.copy') }, requestsText(app)));
}

// ------------------------------------------------------------------ SCR-10 export
function exportScreen(app) {
  const t = app.t;
  const c = app.state.current;
  c.exportSel = c.exportSel || { snapshot: 'current', lang: app.state.locale, format: 'md' };
  const sel = c.exportSel;
  const ackSnaps = [...c.snapshots].sort((a, b) => String(b.savedAt).localeCompare(String(a.savedAt)));
  const stateText = t(app.saveLabelKey(c));
  const make = () => {
    if (sel.format === 'md') return { text: app.render_markdown(sel.snapshot, sel.lang), name: `${app.fileStem()}-${sel.lang}.md`, type: 'text/markdown', exporter: 'healthtech-web-markdown 1.0.0', omits: [t('export.backendNote')] };
    if (sel.format === 'recovery') return { text: app.render_recovery(sel.snapshot), name: `${app.fileStem()}-recovery.json`, type: 'application/json', exporter: 'healthtech-web-recovery 1.0.0', omits: [] };
    return { text: `${app.dossierOnlyText()}`, name: `${app.fileStem()}-dossier.json`, type: 'application/json', exporter: 'lossless dossier passthrough', omits: [t('export.omitsEdits')] };
  };
  const doPreview = () => {
    try { c.exportPreview = { ...make(), sel: { ...sel } }; c.exportError = null; } catch (e) { c.exportPreview = null; c.exportError = { message: e.message, diag: newId('diag') }; }
    app.render({ keepFocus: true });
  };
  const doDownload = () => {
    try { const f = make(); download(f.name, f.text, f.type); c.exportStarted = f.name; c.exportError = null; app.announce(t('export.started'), { toast: true }); } catch (e) { c.exportError = { message: e.message, diag: newId('diag') }; }
    app.render({ keepFocus: true });
  };
  const backendVersions = c.backendHistory?.history?.versions || [];
  const backendExport = c.project.backendJobId
    ? h('section', { id: 'backend-exports', class: 'callout callout-info' },
      h('h2', {}, t('backend.exportTitle')),
      !app.state.backend ? h('p', { id: 'backend-export-unavailable' }, t('backend.noConnection'))
        : c.backendHistoryLoading ? h('p', { id: 'backend-export-loading', role: 'status' }, t('backend.historyLoading'))
          : c.backendHistoryError ? h('p', { id: 'backend-export-error', class: 'field-error' }, t('backend.historyError', { message: c.backendHistoryError.message }))
            : h('div', { class: 'stack' },
              field(t('backend.exportVersion'), h('select', { id: 'backend-export-version', value: String(c.backendSelectedVersion || c.dossier.version), onChange: (e) => app.openBackendVersion(Number(e.target.value)) }, backendVersions.map((v) => h('option', { value: String(v.version), selected: c.backendSelectedVersion === v.version }, String(v.version))))),
              h('div', { class: 'actions' },
                h('button', { type: 'button', class: 'btn', id: 'backend-export-json', onClick: () => app.downloadBackendExport('json') }, t('backend.exportJson')),
                h('button', { type: 'button', class: 'btn', id: 'backend-export-th', onClick: () => app.downloadBackendExport('markdown', 'th') }, t('backend.exportTh')),
                h('button', { type: 'button', class: 'btn', id: 'backend-export-en', onClick: () => app.downloadBackendExport('markdown', 'en') }, t('backend.exportEn'))),
              c.backendExportStatus ? h('p', { id: 'backend-export-status', role: 'status' }, c.backendExportStatus) : null,
              c.backendExportError ? h('p', { id: 'backend-export-error', class: 'field-error' }, c.backendExportError.message) : null))
    : null;
  const radio = (name, value, label, cur, onPick) => h('div', {}, h('input', { type: 'radio', name, id: `${name}-${value}`, value, checked: cur === value, onChange: () => { onPick(value); c.exportPreview = null; app.render({ keepFocus: true }); } }), h('label', { for: `${name}-${value}` }, label));
  const p = c.exportPreview;
  return h('section', {},
    h('h1', { tabindex: '-1' }, t('export.title')),
    backendExport,
    callout('info', null, h('p', {}, t('export.backendNote')), h('p', {}, t('export.noPdf'))),
    field(t('export.snapshot'), h('select', { id: 'export-snapshot', onChange: (e) => { sel.snapshot = e.target.value; c.exportPreview = null; app.render({ keepFocus: true }); } },
      h('option', { value: 'current', selected: sel.snapshot === 'current' }, t('export.current', { state: stateText })),
      ackSnaps.map((s) => h('option', { value: s.snapshotId, selected: sel.snapshot === s.snapshotId }, `${s.snapshotId} · ${s.savedAt}`)))),
    h('fieldset', { class: 'radios' }, h('legend', {}, t('export.language')),
      radio('export-lang', 'th', 'ไทย', sel.lang, (v) => { sel.lang = v; }), radio('export-lang', 'en', 'English', sel.lang, (v) => { sel.lang = v; })),
    h('fieldset', { class: 'radios' }, h('legend', {}, t('export.format')),
      radio('export-format', 'md', t('export.md'), sel.format, (v) => { sel.format = v; }),
      radio('export-format', 'recovery', t('export.recovery'), sel.format, (v) => { sel.format = v; }),
      radio('export-format', 'dossier', t('export.dossierOnly'), sel.format, (v) => { sel.format = v; })),
    h('div', { class: 'actions' },
      h('button', { type: 'button', class: 'btn', id: 'export-preview', onClick: doPreview }, t('export.preview')),
      h('button', { type: 'button', class: 'btn btn-primary', id: 'export-download', onClick: doDownload }, t('export.download'))),
    c.exportStarted ? h('p', { role: 'status', id: 'export-status' }, `${t('export.started')}: ${c.exportStarted}`) : null,
    c.exportError ? errorBanner(t, { title: t('export.fail'), action: 'render export', outcome: c.exportError.message, preserved: c.project.projectId, next: t('export.recovery'), diag: c.exportError.diag }) : null,
    p ? h('section', { 'aria-labelledby': 'export-preview-title' },
      h('h2', { id: 'export-preview-title' }, t('export.preview')),
      kv([[t('export.exporter'), p.exporter], [t('export.omits'), p.omits.length ? h('ul', {}, p.omits.map((o) => h('li', {}, o))) : t('export.omitsNone')]]),
      h('p', { class: 'muted' }, t('export.previewText')),
      h('pre', { class: 'payload', id: 'export-preview-text', tabindex: '0' }, p.text)) : null);
}

export { uid };
