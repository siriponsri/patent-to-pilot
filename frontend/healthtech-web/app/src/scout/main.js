// Solution Scout UI. All text goes through text nodes; all network calls go through adapters.js.
import { createScoutAdapter, SCOUT_DEFAULT_BACKEND } from '../adapters.js';
import { h } from '../ui/dom.js';
import {
  SECTIONS, SPLITS, displayTitle, fieldMap, formatMs, parseIpc3, quoteSegments, requestKey, translator,
} from './model.js';

const SVG_NS = 'http://www.w3.org/2000/svg';
const root = document.getElementById('scout');
const live = document.getElementById('scout-live');
const params = new URLSearchParams(location.search);

const state = {
  lang: params.get('lang') === 'th' ? 'th' : 'en',
  text: '',
  own: [],
  split: SPLITS[0],
  info: null,
  infoError: null,
  session: null,
  loading: false,
  error: null,
  active: null,
  decisions: {},
};

let adapter;
try {
  adapter = createScoutAdapter(params.get('backend') || SCOUT_DEFAULT_BACKEND);
} catch (error) {
  state.infoError = error.message;
}

let t = translator(state.lang);
const els = {};

function svg(tag, attrs = {}, ...children) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) el.setAttribute(k, String(v));
  for (const c of children) if (c !== null && c !== undefined) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}

/** Set CSS custom properties through the CSSOM; the page CSP forbids inline style attributes. */
function vars(el, values) {
  for (const [k, v] of Object.entries(values)) el.style.setProperty(`--${k}`, String(v));
  return el;
}

function announce(message) {
  live.textContent = '';
  requestAnimationFrame(() => { live.textContent = message; });
}

function canSearch() {
  return state.text.trim().split(/\s+/).length >= 4 && state.own.length > 0 && !state.loading && adapter && state.info;
}

// ---------- shell ----------
function render() {
  t = translator(state.lang);
  document.documentElement.lang = state.lang;
  document.title = t('scout.name');
  root.replaceChildren(
    h('div', { class: 'shell' },
      h('header', { class: 'top' },
        h('div', { class: 'brand' }, h('span', { class: 'brand-mark', 'aria-hidden': 'true' }), t('scout.name')),
        h('button', { type: 'button', class: 'ghost', onClick: () => { state.lang = state.lang === 'en' ? 'th' : 'en'; render(); } }, t('scout.lang'))),
      h('main', { id: 'main' },
        heroSection(),
        els.results = h('section', { class: 'results', 'aria-live': 'off', hidden: !state.session && !state.loading }),
        h('p', { class: 'about' }, aboutText())),
    ),
    els.receipt = h('div', { class: 'receipt', hidden: !state.session, role: 'contentinfo' }),
    els.scrim = h('div', { class: 'scrim', onClick: closeDrawer }),
    els.drawer = h('aside', { class: 'drawer', 'aria-hidden': 'true', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'drawer-title', tabindex: '-1' }),
  );
  renderChips();
  renderResults();
  renderReceipt();
  if (state.active) openDrawer(state.active, { keepFocus: true });
}

function aboutText() {
  const info = state.info || {};
  return t('scout.about', {
    source: info.source || 'HUPD', licence: info.corpus_licence || 'CC BY-SA 4.0',
    encoderLicence: info.encoder?.licence || 'CC BY-NC-SA 4.0',
  });
}

function heroSection() {
  const textarea = h('textarea', {
    id: 'brief', rows: '3', placeholder: t('scout.brief.placeholder'), 'aria-describedby': 'brief-hint',
    onInput: (e) => { state.text = e.target.value; updateGo(); },
    onKeydown: (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); search(); } },
  });
  textarea.value = state.text;
  els.textarea = textarea;
  els.chips = h('div', { class: 'chips', role: 'group', 'aria-label': t('scout.own.label') });
  els.go = h('button', { type: 'button', class: 'go', onClick: search }, t('scout.search'), h('kbd', {}, 'Ctrl ↵'));
  els.hint = h('p', { class: 'hint', id: 'brief-hint' });
  const seg = h('div', { class: 'seg', role: 'group', 'aria-label': t('scout.split.label') },
    SPLITS.map((s) => h('button', {
      type: 'button', 'aria-pressed': String(s.key === state.split.key),
      onClick: () => { state.split = s; render(); if (state.session) search(); },
    }, s.key)));
  const demos = (state.info?.demo_briefs || []);
  return h('section', { class: 'hero' },
    h('h1', {}, ...titleParts()),
    h('p', { class: 'lead' }, t('scout.tagline')),
    h('div', { class: 'composer' },
      h('label', { class: 'kicker', for: 'brief' }, t('scout.brief.label')),
      textarea,
      h('div', { class: 'composer-row' },
        h('span', { class: 'kicker', 'aria-hidden': 'true' }, t('scout.own.label')), els.chips,
        h('span', { class: 'spacer' }), seg, els.go)),
    els.hint,
    demos.length ? h('div', { class: 'demos' }, h('span', {}, t('scout.demo.label')),
      demos.map((d) => h('button', {
        type: 'button', class: 'demo', title: d.text,
        onClick: () => { state.text = d.text; state.own = [...d.own_ipc3]; render(); search(); },
      }, d.text))) : null,
  );
}

function titleParts() {
  return state.lang === 'th'
    ? ['ปัญหาของคุณ ', h('em', {}, 'อาจมีคนแก้แล้ว'), ' ในอุตสาหกรรมอื่น']
    : ['Your problem may already be ', h('em', {}, 'solved'), ' in another industry.'];
}

function renderChips() {
  const input = h('input', {
    class: 'chip-input', 'aria-label': t('scout.own.add'), placeholder: t('scout.own.add'),
    onKeydown: (e) => {
      if (e.key !== 'Enter' && e.key !== ',') return;
      e.preventDefault();
      const code = parseIpc3(e.target.value);
      if (!code) { e.target.setAttribute('aria-invalid', 'true'); setHint(t('scout.own.invalid'), true); return; }
      if (!state.own.includes(code)) state.own = [...state.own, code].sort();
      renderChips();
      els.chips.querySelector('input')?.focus();
    },
  });
  els.chips.replaceChildren(
    ...state.own.map((code) => h('span', { class: 'chip' }, code,
      h('button', { type: 'button', 'aria-label': t('scout.own.remove', { code }), onClick: () => { state.own = state.own.filter((c) => c !== code); renderChips(); } }, '×'))),
    input);
  updateGo();
}

function setHint(message, isError = false) {
  if (!els.hint) return;
  els.hint.textContent = message || '';
  els.hint.classList.toggle('err', isError);
}

function updateGo() {
  if (!els.go) return;
  els.go.disabled = !canSearch();
  if (state.infoError) setHint(t('scout.error.backend', { url: adapter?.baseUrl || SCOUT_DEFAULT_BACKEND }), true);
  else if (state.error) setHint(state.error, true);
  else if (state.loading) setHint(t('scout.searching', { n: (state.info?.families || 0).toLocaleString() }));
  else setHint(canSearch() || state.session ? '' : t('scout.need'));
}

// ---------- search ----------
async function search() {
  if (!canSearch()) { updateGo(); return; }
  state.loading = true; state.error = null; state.active = null;
  renderResults(); updateGo(); closeDrawer();
  const brief = { brief_id: 'ui-brief', text: state.text.trim(), own_ipc3: [...state.own].sort(), own_ipc3_basis: 'typed', data_class: state.info.data_class, language: state.lang };
  const split = { n_own: state.split.n_own, n_other: state.split.n_other };
  try {
    const created = await adapter.create(brief, split, await requestKey(brief, split));
    state.session = (await adapter.session(created.session.session_id)).session;
    state.decisions = {};
    const others = state.session.candidates.filter((c) => c.lane === 'other_fields').length;
    announce(`${t('scout.lane.other')}: ${others}`);
  } catch (error) {
    state.error = t('scout.error.generic', { message: error.message });
  } finally {
    state.loading = false;
    renderResults(); renderReceipt(); updateGo();
  }
}

function renderResults() {
  const box = els.results;
  if (!box) return;
  box.hidden = !state.session && !state.loading;
  if (state.loading) {
    box.replaceChildren(h('div', { class: 'lanes' },
      h('div', {}, [0, 1, 2].map(() => h('div', { class: 'skeleton' }))),
      h('div', {}, [0, 1, 2, 3].map(() => h('div', { class: 'skeleton' })))));
    return;
  }
  if (!state.session) { box.replaceChildren(); return; }
  const s = state.session;
  const ideas = new Set(s.rationales_available || []);
  const own = s.candidates.filter((c) => c.lane === 'own_field');
  const other = s.candidates.filter((c) => c.lane === 'other_fields');
  box.replaceChildren(
    mapCard(s, ideas),
    h('div', { class: 'lanes' },
      lane('own', t('scout.lane.own'), t('scout.lane.own.help'), own, ideas),
      lane('other', t('scout.lane.other'), t('scout.lane.other.help'), other, ideas)),
  );
}

function lane(kind, title, help, items, ideas) {
  const scores = items.map((c) => c.score);
  const hi = Math.max(...scores, 0), lo = Math.min(...scores, hi);
  const width = (score) => (hi === lo ? 100 : 35 + (65 * (score - lo)) / (hi - lo));
  return h('section', { class: `lane ${kind}`, 'aria-label': title },
    h('div', { class: 'lane-head' }, h('h3', {}, title), h('span', { class: 'count' }, String(items.length)), h('p', {}, help)),
    items.length ? h('ol', { class: 'cards' }, items.map((c, i) => card(c, i, width(c.score), ideas.has(c.family_id))))
      : h('p', { class: 'empty' }, t('scout.empty')));
}

function card(c, i, width, hasIdea) {
  const title = displayTitle(c.title) || c.family_id;
  const open = () => openDrawer(c.family_id);
  return vars(h('li', {
    class: `card${state.active === c.family_id ? ' active' : ''}`, tabindex: '0', role: 'button',
    'data-family': c.family_id, 'aria-label': t('scout.card.open', { title }),
    onClick: open, onKeydown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } },
    onMouseenter: () => highlightDot(c.family_id, true), onMouseleave: () => highlightDot(c.family_id, false),
  },
  h('span', { class: 'card-rank' }, `#${c.rank_in_lane}`),
  h('p', { class: 'card-title' }, title),
  h('div', { class: 'meta' },
    h('span', {}, c.representative_canonical || c.family_id),
    c.publication_date ? h('span', {}, c.publication_date) : null,
    (c.ipc3 || []).slice(0, 4).map((code) => h('span', { class: 'ipc' }, code)),
    hasIdea ? h('span', { class: 'idea' }, '✦ ', t('scout.card.idea')) : null),
  h('div', { class: 'bar', title: `${t('scout.card.score')} ${c.score.toFixed(3)}` }, vars(h('i'), { w: `${width.toFixed(1)}%` }))),
  { d: `${Math.min(i, 12) * 45}ms` });
}

// ---------- field map (the constellation) ----------
function mapCard(s, ideas) {
  const W = 920, H = 340, cx = W / 2, cy = H / 2 + 4, rx = 330, ry = 122;
  const groups = Object.fromEntries(fieldMap(s.candidates).map((g) => [g.section, g.items]));
  const own = new Set(s.brief.own_ipc3.map((c) => c[0]));
  const nodes = SECTIONS.map((section, i) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * i) / SECTIONS.length;
    return { section, x: cx + rx * Math.cos(angle), y: cy + ry * Math.sin(angle), angle, items: groups[section] || [] };
  });
  const map = svg('svg', { class: 'map', viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': t('scout.map.title') });
  map.append(svg('ellipse', { class: 'ring', cx, cy, rx, ry }));
  nodes.forEach((n, i) => {
    if (!n.items.length) return;
    const len = Math.hypot(n.x - cx, n.y - cy);
    map.append(vars(svg('line', { class: 'spoke', x1: cx, y1: cy, x2: n.x, y2: n.y, 'stroke-width': 1 + Math.min(n.items.length, 8) }),
      { len: len.toFixed(0), d: `${i * 70}ms` }));
  });
  nodes.forEach((n, i) => {
    const hit = n.items.length > 0;
    const right = Math.cos(n.angle) > 0.2, left = Math.cos(n.angle) < -0.2;
    const lx = n.x + (right ? 30 : left ? -30 : 0), ly = n.y + (right || left ? 0 : Math.sin(n.angle) > 0 ? 38 : -34);
    const anchor = right ? 'start' : left ? 'end' : 'middle';
    map.append(
      svg('circle', { class: `node${hit ? ' hit' : ''}${own.has(n.section) ? ' own' : ''}`, cx: n.x, cy: n.y, r: 18 }),
      svg('text', { class: 'node-letter', x: n.x, y: n.y }, n.section),
      svg('text', { class: 'node-label', x: lx, y: ly, 'text-anchor': anchor, 'dominant-baseline': 'central' },
        t(`scout.section.${n.section}`), hit ? svg('tspan', { class: 'node-count', dx: 6 }, `${n.items.length}`) : null),
    );
    n.items.forEach((c, k) => {
      const a = n.angle + Math.PI + (k - (n.items.length - 1) / 2) * 0.55;
      const r = 30 + 9 * Math.floor(k / 6);
      const dot = svg('circle', {
        class: `dot${ideas.has(c.family_id) ? ' idea' : ''}`, cx: n.x + r * Math.cos(a) * 0.9, cy: n.y + r * Math.sin(a) * 0.9, r: 5,
        'data-family': c.family_id,
      }, svg('title', {}, `${displayTitle(c.title)} (${c.representative_canonical || c.family_id})`));
      vars(dot, { d: `${400 + i * 70 + k * 40}ms` });
      dot.addEventListener('click', () => openDrawer(c.family_id));
      dot.addEventListener('mouseenter', () => highlightCard(c.family_id, true));
      dot.addEventListener('mouseleave', () => highlightCard(c.family_id, false));
      map.append(dot);
    });
  });
  map.append(
    svg('circle', { class: 'hub', cx, cy, r: 36 }),
    svg('text', { class: 'hub-label', x: cx, y: cy - 5 }, t('scout.map.you')),
    svg('text', { class: 'hub-sub', x: cx, y: cy + 12, fill: 'currentColor' }, s.brief.own_ipc3.join(' · ')),
  );
  return h('div', { class: 'map-card' },
    h('div', { class: 'map-head' }, h('h2', {}, t('scout.map.title')), h('p', {}, t('scout.map.note'))),
    map);
}

function highlightDot(familyId, on) {
  els.results?.querySelectorAll('.dot').forEach((d) => { if (d.dataset.family === familyId) d.classList.toggle('active', on); });
}
function highlightCard(familyId, on) {
  els.results?.querySelectorAll('.card').forEach((c) => { if (c.dataset.family === familyId) c.classList.toggle('active', on || state.active === familyId); });
}

// ---------- drawer ----------
let lastFocus = null;

async function openDrawer(familyId, { keepFocus = false } = {}) {
  const s = state.session;
  const c = s?.candidates.find((x) => x.family_id === familyId);
  if (!c) return;
  if (!keepFocus) lastFocus = document.activeElement;
  state.active = familyId;
  highlightCard(familyId, true);
  const body = h('div', { class: 'drawer-body' }, h('p', { class: 'basis' }, t('scout.drawer.loading')));
  els.drawer.replaceChildren(
    h('div', { class: 'drawer-head' },
      h('button', { type: 'button', class: 'ghost drawer-close', onClick: closeDrawer }, t('scout.drawer.close')),
      h('span', { class: 'kicker' }, c.lane === 'other_fields' ? t('scout.lane.other') : t('scout.lane.own')),
      h('h2', { id: 'drawer-title' }, displayTitle(c.title) || c.family_id),
      h('div', { class: 'meta' }, h('span', {}, c.representative_canonical || c.family_id),
        c.publication_date ? h('span', {}, c.publication_date) : null, (c.ipc3 || []).map((code) => h('span', { class: 'ipc' }, code)))),
    body);
  els.drawer.classList.add('open'); els.drawer.setAttribute('aria-hidden', 'false'); els.scrim.classList.add('open');
  if (!keepFocus) els.drawer.focus();
  const hasIdea = (s.rationales_available || []).includes(familyId);
  try {
    const [family, idea] = await Promise.all([
      adapter.family(s.session_id, familyId),
      hasIdea ? adapter.rationale(s.session_id, familyId) : Promise.resolve(null),
    ]);
    if (state.active !== familyId) return;
    body.replaceChildren(...drawerContent(c, family, idea?.rationale || null));
    if (idea) renderReceipt();
  } catch (error) {
    body.replaceChildren(h('p', { class: 'hint err' }, t('scout.error.generic', { message: error.message })));
  }
}

function drawerContent(c, family, r) {
  const blocks = [];
  if (r) {
    const decision = state.decisions[c.family_id] || r.decision;
    blocks.push(
      h('div', { class: 'block' }, h('h4', {}, t('scout.drawer.mechanism')), h('p', { class: 'mechanism' }, r.transferable_mechanism),
        h('p', { class: 'basis' }, t('scout.basis', { model: r.model }))),
      h('div', { class: 'block' }, h('h4', {}, t('scout.drawer.what')), h('p', {}, r.what_it_does)),
      h('div', { class: 'block' }, h('h4', {}, t('scout.drawer.quotes')),
        r.quotes.map((q) => h('blockquote', { class: `quote ${q.status}` },
          h('span', { class: `badge ${q.status}` }, t(`scout.quote.${q.status}`)), h('div', {}, `“${q.quote}”`))),
        h('p', { class: 'label-note' }, t('scout.quote.label'))),
      h('div', { class: 'block decide' },
        ['accepted', 'rejected'].map((d) => h('button', {
          type: 'button', class: 'ghost', 'aria-pressed': String(decision === d),
          onClick: async () => {
            try {
              await adapter.decide(state.session.session_id, c.family_id, d);
              state.decisions[c.family_id] = d;
              announce(t('scout.decision.saved', { decision: t(d === 'accepted' ? 'scout.decision.accept' : 'scout.decision.reject') }));
              openDrawer(c.family_id, { keepFocus: true });
            } catch (error) { announce(error.message); }
          },
        }, t(d === 'accepted' ? 'scout.decision.accept' : 'scout.decision.reject')))),
    );
  } else {
    blocks.push(h('p', { class: 'label-note block' }, t('scout.drawer.noIdea')));
  }
  const segments = quoteSegments(family.source_text, r ? r.quotes.filter((q) => q.status === 'matched') : []);
  blocks.push(h('div', { class: 'block' }, h('h4', {}, t('scout.drawer.source')),
    h('div', { class: 'source', lang: 'en' }, segments.map((seg) => (seg.mark ? h('mark', {}, seg.text) : seg.text)))));
  return blocks;
}

function closeDrawer() {
  if (!els.drawer) return;
  const was = state.active;
  state.active = null;
  els.drawer.classList.remove('open'); els.drawer.setAttribute('aria-hidden', 'true'); els.scrim?.classList.remove('open');
  if (was) highlightCard(was, false);
  if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
  lastFocus = null;
}

document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && state.active) closeDrawer(); });

// ---------- receipt ----------
async function renderReceipt() {
  const box = els.receipt;
  if (!box) return;
  const s = state.session;
  box.hidden = !s;
  if (!s) return;
  let ideas = 0;
  try { ideas = (await adapter.receipt(s.session_id)).rationales.count; } catch { /* receipt is informative only */ }
  const r = s.receipt;
  const item = (label, value) => h('span', {}, h('b', {}, label), value);
  box.replaceChildren(
    item(t('scout.receipt.mode'), r.mode),
    item(t('scout.receipt.encode'), formatMs(r.encode_ms)),
    item(t('scout.receipt.search'), formatMs(r.search_ms)),
    item(t('scout.receipt.corpus'), `${(state.info?.families || 0).toLocaleString()} · ${r.corpus_bundle_sha256.slice(0, 8)}`),
    item(t('scout.receipt.encoder'), r.encoder.split('/').pop()),
    item(t('scout.receipt.ideas'), `${ideas}/${(s.rationales_available || []).length}`),
    item(t('scout.receipt.paid'), String(r.paid_calls)),
  );
}

// ---------- boot ----------
async function boot() {
  render();
  if (!adapter) { updateGo(); return; }
  try {
    state.info = await adapter.info();
    state.infoError = null;
  } catch (error) {
    state.infoError = error.message;
  }
  render();
  els.textarea?.focus();
}

boot();
