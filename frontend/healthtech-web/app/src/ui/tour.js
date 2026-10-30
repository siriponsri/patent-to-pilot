// Guided tour: spotlights one part of the workspace at a time with a short
// explanation. Non-modal (the page stays usable), keyboard operable
// (←/→, Enter, Esc) and it returns focus to the button that opened it.
import { h } from './dom.js';

export const TOUR_STEPS = [
  { sel: '.journey', key: 'journey' },
  { sel: '.canvas', key: 'canvas' },
  { sel: '#node-evidence', key: 'node' },
  { sel: '#panel-body-library .lib-card', key: 'drag' },
  { sel: '#panel-body-inspector', key: 'inspector' },
  { sel: '#panel-body-timeline', key: 'timeline' },
  { sel: '.ws-top .save-bar', key: 'save' },
  { sel: '#layout-menu', key: 'layout' },
  { sel: '#tutorial-open', key: 'video' },
];
const SEEN_KEY = 'p2p-healthtech-ux-tour-seen';

export function tourSeen() { try { return localStorage.getItem(SEEN_KEY) === '1'; } catch { return true; } }
function markSeen() { try { localStorage.setItem(SEEN_KEY, '1'); } catch { /* convenience only */ } }

let active = null;

export function startTour(app, opener) {
  endTour();
  const t = app.t;
  const steps = TOUR_STEPS.filter((s) => document.querySelector(s.sel));
  if (!steps.length) return;
  const spot = h('div', { class: 'tour-spot', 'aria-hidden': 'true' });
  const counter = h('p', { class: 'tour-count' });
  const title = h('h2', { class: 'tour-title', id: 'tour-title', tabindex: '-1' });
  const body = h('p', { class: 'tour-body' });
  const back = h('button', { type: 'button', class: 'btn btn-small', id: 'tour-back' });
  const next = h('button', { type: 'button', class: 'btn btn-small btn-primary', id: 'tour-next' });
  const close = h('button', { type: 'button', class: 'tour-close', id: 'tour-close', 'aria-label': t('common.close') }, '×');
  const pop = h('section', { class: 'tour-pop', role: 'dialog', 'aria-modal': 'false', 'aria-labelledby': 'tour-title' }, close, counter, title, body, h('div', { class: 'actions' }, back, next));
  const layer = h('div', { class: 'tour', 'data-tour': 'on' }, spot, pop);
  document.body.append(layer);
  let i = 0;

  const place = () => {
    const target = document.querySelector(steps[i].sel);
    if (!target) return;
    const r = target.getBoundingClientRect();
    const pad = 6;
    Object.assign(spot.style, { left: `${r.left - pad}px`, top: `${r.top - pad}px`, width: `${r.width + pad * 2}px`, height: `${r.height + pad * 2}px` });
    const pw = Math.min(380, window.innerWidth - 24);
    pop.style.width = `${pw}px`;
    const ph = pop.offsetHeight || 200;
    const below = r.bottom + 14 + ph < window.innerHeight;
    const above = r.top - 14 - ph > 0;
    let top = below ? r.bottom + 14 : above ? r.top - 14 - ph : Math.max(12, (window.innerHeight - ph) / 2);
    let left = Math.min(Math.max(12, r.left), window.innerWidth - pw - 12);
    if (!below && !above && r.right + pw + 24 < window.innerWidth) { left = r.right + 14; top = Math.max(12, Math.min(r.top, window.innerHeight - ph - 12)); }
    Object.assign(pop.style, { left: `${left}px`, top: `${top}px` });
  };

  const show = (n) => {
    i = Math.max(0, Math.min(steps.length - 1, n));
    const s = steps[i];
    document.querySelector(s.sel)?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    counter.textContent = t('tour.count', { n: i + 1, total: steps.length });
    title.textContent = t(`tour.${s.key}.title`);
    body.textContent = t(`tour.${s.key}.body`);
    back.textContent = `← ${t('tour.back')}`;
    back.disabled = i === 0;
    next.textContent = i === steps.length - 1 ? t('tour.done') : `${t('tour.next')} →`;
    layer.dataset.step = s.key;
    requestAnimationFrame(place);
    title.focus({ preventScroll: true });
    app.announce(`${counter.textContent}: ${title.textContent}`);
  };

  const onKey = (e) => {
    if (e.key === 'Escape') { e.preventDefault(); endTour(); }
    else if (e.key === 'ArrowRight' && !e.target.closest('input, textarea, select')) { e.preventDefault(); next.click(); }
    else if (e.key === 'ArrowLeft' && !e.target.closest('input, textarea, select')) { e.preventDefault(); if (i > 0) show(i - 1); }
  };
  back.addEventListener('click', () => show(i - 1));
  next.addEventListener('click', () => (i === steps.length - 1 ? endTour() : show(i + 1)));
  close.addEventListener('click', () => endTour());
  window.addEventListener('keydown', onKey);
  window.addEventListener('resize', place);
  active = { layer, onKey, place, opener };
  markSeen();
  show(0);
}

export function endTour() {
  if (!active) return;
  const { layer, onKey, place, opener } = active;
  active = null;
  window.removeEventListener('keydown', onKey);
  window.removeEventListener('resize', place);
  layer.remove();
  // The opener may have been re-rendered while the tour ran; fall back to its id.
  const target = opener?.isConnected ? opener : (opener?.id ? document.getElementById(opener.id) : null);
  target?.focus?.();
}
