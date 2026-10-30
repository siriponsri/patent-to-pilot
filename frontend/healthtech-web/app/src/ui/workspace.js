// Dockable workspace shell. Mounts once per project and then updates in place,
// so the canvas (pan/zoom/animations) and panel frames survive re-renders.
// Content builders (inspector views, library, timeline) come from screens.js.
import { h } from './dom.js';
import { createCanvas } from './canvas.js';
import { draggable } from './dnd.js';
import { movePanel, resizeZone, setActive, toggleCollapsed, setFloatRect, locate, ZONES, PANELS, LIMITS } from '../core/layout.js';

let ws = null;

export function workspaceCanvas() { return ws?.canvas || null; }

/**
 * parts: { topbar(), modeStrip(), inspector(), library(), timeline(), statusbar(),
 *          onCanvas(canvas), selectedNode, pipe }
 */
export function renderWorkspace(app, parts) {
  const root = document.getElementById('app');
  const pid = app.state.current.project.projectId;
  if (!ws || ws.projectId !== pid || !root.contains(ws.root)) mount(app, parts, root, pid);
  else if (parts.pipeOnly) {
    // Live progress: canvas, journey and timeline only. Inspector/library keep focus and caret.
    ws.canvas.update(parts.pipe, parts.selectedNode);
    ws.journeySlot.replaceChildren(parts.journey());
    ws.bodies.timeline.replaceChildren(parts.timeline());
    const tl = ws.bodies.timeline.querySelector('.timeline');
    if (tl) tl.scrollTop = tl.scrollHeight;
    ws.bodies.timeline.scrollTop = ws.bodies.timeline.scrollHeight;
    return;
  }
  const t = app.t;
  ws.topSlot.replaceChildren(parts.topbar());
  ws.journeySlot.replaceChildren(parts.journey());
  ws.modeSlot.replaceChildren(parts.modeStrip());
  ws.statusSlot.replaceChildren(parts.statusbar());
  ws.bodies.inspector.replaceChildren(...parts.inspector());
  ws.bodies.library.replaceChildren(parts.library());
  ws.bodies.timeline.replaceChildren(parts.timeline());
  ws.skip.textContent = t('nav.skip');
  ws.canvas.update(parts.pipe, parts.selectedNode);
  renderFrames(app);
  // After re-attaching panel bodies: keep the newest activity in view.
  const list = ws.bodies.timeline.querySelector('.timeline');
  if (list) list.scrollTop = list.scrollHeight;
  ws.bodies.timeline.scrollTop = ws.bodies.timeline.scrollHeight;
}

function mount(app, parts, root, pid) {
  const canvas = createCanvas(app);
  const bodies = Object.fromEntries(PANELS.map((p) => [p, h('div', { class: `panel-body panel-${p}`, id: `panel-body-${p}` })]));
  const zones = Object.fromEntries(ZONES.map((z) => [z, h('div', { class: `zone zone-${z}`, 'data-zone': z })]));
  const splitters = Object.fromEntries(ZONES.map((z) => [z, splitter(app, z)]));
  const dockTargets = ['left', 'right', 'bottom', 'float'].map((d) => {
    const el = h('div', { class: `dock-target dock-${d}`, 'data-drop': 'panel', 'data-dock': d }, h('span', {}));
    el.ondropitem = (item) => {
      const rect = d === 'float' ? { x: 120, y: 90, w: 460, h: 360 } : undefined;
      app.setLayout(movePanel(app.layout, item.payload, d, rect));
      return true;
    };
    return el;
  });
  const grid = h('main', { id: 'main', class: 'ws-grid', tabindex: '-1' },
    zones.left, splitters.left, h('div', { class: 'ws-canvas' }, canvas.el), splitters.right, zones.right, splitters.bottom, zones.bottom, ...dockTargets);
  const floatLayer = h('div', { class: 'float-layer' });
  const skip = h('a', { class: 'skip-link', href: '#main', onClick: (e) => { e.preventDefault(); grid.focus(); } });
  const topSlot = h('div', { class: 'ws-top-slot' });
  const modeSlot = h('div', { class: 'ws-mode-slot' });
  const journeySlot = h('div', { class: 'ws-journey-slot' });
  const statusSlot = h('div', { class: 'ws-status-slot' });
  const rootEl = h('div', { class: 'ws', 'data-project': pid }, topSlot, modeSlot, journeySlot, grid, statusSlot, floatLayer);
  root.replaceChildren(skip, rootEl);
  ws = { root: rootEl, projectId: pid, canvas, bodies, zones, splitters, grid, floatLayer, topSlot, modeSlot, journeySlot, statusSlot, skip, frames: {} };
  canvas.build(pid);
  parts.onCanvas?.(canvas);
}

function panelTitle(app, p) { return app.t(`panel.${p}`); }

function panelMenu(app, panel) {
  const t = app.t;
  const where = locate(app.layout, panel);
  const items = [...ZONES, 'float'].filter((d) => d !== where).map((d) =>
    h('button', { type: 'button', class: 'btn btn-small', id: `move-${panel}-${d}`, onClick: () => app.setLayout(movePanel(app.layout, panel, d, d === 'float' ? { x: 120, y: 90, w: 460, h: 360 } : undefined)) }, t(`layout.to.${d}`)));
  return h('details', { class: 'panel-menu' },
    h('summary', { 'aria-label': `${t('layout.menu')}: ${panelTitle(app, panel)}`, title: t('layout.menu') }, '⋯'),
    h('div', { class: 'panel-menu-items', role: 'group', 'aria-label': t('layout.menu') }, items));
}

function grip(app, panel, frame) {
  const g = h('span', { class: 'panel-grip', title: app.t('layout.dragHint'), 'aria-hidden': 'true' }, '⠿');
  draggable(g, frame, { type: 'panel', payload: panel, label: panelTitle(app, panel) }, (m) => app.announce(m));
  return g;
}

function renderFrames(app) {
  const t = app.t;
  const l = app.layout;
  for (const z of ZONES) {
    const zone = l.zones[z];
    const empty = !zone.panels.length;
    const zoneEl = ws.zones[z];
    const frame = h('section', { class: 'panel-frame', 'aria-label': zone.active ? panelTitle(app, zone.active) : '' });
    if (!empty) {
      const tabs = h('div', { class: 'panel-tabs', role: 'tablist', 'aria-label': t(`layout.zone.${z}`) },
        zone.panels.map((p) => h('button', { type: 'button', role: 'tab', id: `ptab-${p}`, 'aria-selected': String(p === zone.active), 'aria-controls': `panel-body-${p}`, tabindex: p === zone.active ? '0' : '-1',
          onClick: () => app.setLayout(setActive(app.layout, z, p)) }, panelTitle(app, p))));
      const head = h('div', { class: 'panel-head' }, grip(app, zone.active, frame), tabs,
        h('button', { type: 'button', class: 'btn btn-small panel-collapse', 'aria-expanded': String(!l.collapsed[z]), 'aria-label': t(l.collapsed[z] ? 'layout.expand' : 'layout.collapse'), title: t(l.collapsed[z] ? 'layout.expand' : 'layout.collapse'), onClick: () => app.setLayout(toggleCollapsed(app.layout, z)) }, l.collapsed[z] ? '▸' : '▾'),
        panelMenu(app, zone.active));
      frame.append(head);
      if (!l.collapsed[z]) {
        const body = ws.bodies[zone.active];
        body.setAttribute('role', 'tabpanel');
        body.setAttribute('aria-labelledby', `ptab-${zone.active}`);
        frame.append(body);
      }
    }
    zoneEl.replaceChildren(...(empty ? [] : [frame]));
    zoneEl.dataset.empty = String(empty);
    zoneEl.dataset.collapsed = String(Boolean(l.collapsed[z]));
    ws.splitters[z].hidden = empty;
    ws.splitters[z].setAttribute('aria-valuenow', String(zone.size));
    ws.splitters[z].setAttribute('aria-label', t(`layout.resize.${z}`));
    const size = empty ? 0 : l.collapsed[z] ? (z === 'bottom' ? 44 : 52) : zone.size;
    ws.grid.style.setProperty(`--${z}`, `${size}px`);
  }
  // Floating windows.
  ws.floatLayer.replaceChildren(...Object.entries(l.floating).map(([p, r]) => floatWindow(app, p, r)));
  ws.grid.querySelectorAll('.dock-target').forEach((d) => {
    d.dataset.dropLabel = t(`layout.to.${d.dataset.dock}`);
    d.firstChild.textContent = t(`layout.to.${d.dataset.dock}`);
  });
}

function floatWindow(app, panel, rect) {
  const t = app.t;
  const win = h('section', { class: 'float-window', 'aria-label': panelTitle(app, panel) });
  const place = (r) => Object.assign(win.style, { left: `${r.x}px`, top: `${r.y}px`, width: `${r.w}px`, height: `${r.h}px` });
  place(rect);
  const viewport = () => ({ w: window.innerWidth, h: window.innerHeight });
  const head = h('div', { class: 'panel-head float-head', tabindex: '0', title: t('layout.floatKeys'), 'aria-label': `${panelTitle(app, panel)} — ${t('layout.floatKeys')}` },
    grip(app, panel, win), h('span', { class: 'float-title' }, panelTitle(app, panel)), panelMenu(app, panel));
  // Move by dragging the header (not the grip, which re-docks).
  head.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.panel-grip, .panel-menu, button') || e.button !== 0) return;
    const s = { x: e.clientX, y: e.clientY, r: { ...rect } };
    head.setPointerCapture(e.pointerId);
    const move = (ev) => place({ ...s.r, x: s.r.x + ev.clientX - s.x, y: s.r.y + ev.clientY - s.y });
    const up = (ev) => {
      head.removeEventListener('pointermove', move); head.removeEventListener('pointerup', up);
      app.setLayout(setFloatRect(app.layout, panel, { ...s.r, x: s.r.x + ev.clientX - s.x, y: s.r.y + ev.clientY - s.y }, viewport()));
    };
    head.addEventListener('pointermove', move); head.addEventListener('pointerup', up);
  });
  // Keyboard: arrows move, Shift+arrows resize.
  head.addEventListener('keydown', (e) => {
    const d = { ArrowLeft: [-20, 0], ArrowRight: [20, 0], ArrowUp: [0, -20], ArrowDown: [0, 20] }[e.key];
    if (!d || e.target !== head) return;
    e.preventDefault();
    const r = e.shiftKey ? { ...rect, w: rect.w + d[0], h: rect.h + d[1] } : { ...rect, x: rect.x + d[0], y: rect.y + d[1] };
    app.setLayout(setFloatRect(app.layout, panel, r, viewport()));
    document.querySelector(`.float-window[aria-label="${CSS.escape(panelTitle(app, panel))}"] .float-head`)?.focus();
  });
  const resize = h('span', { class: 'float-resize', 'aria-hidden': 'true' });
  resize.addEventListener('pointerdown', (e) => {
    const s = { x: e.clientX, y: e.clientY, r: { ...rect } };
    resize.setPointerCapture(e.pointerId);
    const move = (ev) => place({ ...s.r, w: Math.max(260, s.r.w + ev.clientX - s.x), h: Math.max(160, s.r.h + ev.clientY - s.y) });
    const up = (ev) => {
      resize.removeEventListener('pointermove', move); resize.removeEventListener('pointerup', up);
      app.setLayout(setFloatRect(app.layout, panel, { ...s.r, w: s.r.w + ev.clientX - s.x, h: s.r.h + ev.clientY - s.y }, viewport()));
    };
    resize.addEventListener('pointermove', move); resize.addEventListener('pointerup', up);
  });
  const body = ws.bodies[panel];
  body.setAttribute('role', 'region');
  body.removeAttribute('aria-labelledby');
  win.append(head, body, resize);
  return win;
}

function splitter(app, zone) {
  const vertical = zone !== 'bottom';
  const el = h('div', { class: `splitter splitter-${zone}`, role: 'separator', tabindex: '0', 'aria-orientation': vertical ? 'vertical' : 'horizontal',
    'aria-valuemin': String(LIMITS[zone][0]), 'aria-valuemax': String(LIMITS[zone][1]), 'data-zone': zone });
  const sign = zone === 'left' ? 1 : -1;
  el.addEventListener('pointerdown', (e) => {
    const start = { x: e.clientX, y: e.clientY, size: app.layout.zones[zone].size };
    el.setPointerCapture(e.pointerId);
    el.classList.add('active');
    const move = (ev) => {
      const delta = vertical ? (ev.clientX - start.x) * sign : (start.y - ev.clientY);
      const size = Math.min(LIMITS[zone][1], Math.max(LIMITS[zone][0], start.size + delta));
      ws.grid.style.setProperty(`--${zone}`, `${size}px`);
      el.setAttribute('aria-valuenow', String(Math.round(size)));
    };
    const up = (ev) => {
      el.classList.remove('active');
      el.removeEventListener('pointermove', move); el.removeEventListener('pointerup', up);
      const delta = vertical ? (ev.clientX - start.x) * sign : (start.y - ev.clientY);
      app.setLayout(resizeZone(app.layout, zone, start.size + delta));
    };
    el.addEventListener('pointermove', move); el.addEventListener('pointerup', up);
  });
  el.addEventListener('dblclick', () => app.setLayout(toggleCollapsed(app.layout, zone)));
  el.addEventListener('keydown', (e) => {
    const grow = { left: 'ArrowRight', right: 'ArrowLeft', bottom: 'ArrowUp' }[zone];
    const shrink = { left: 'ArrowLeft', right: 'ArrowRight', bottom: 'ArrowDown' }[zone];
    if (e.key === grow || e.key === shrink) {
      e.preventDefault();
      app.setLayout(resizeZone(app.layout, zone, app.layout.zones[zone].size + (e.key === grow ? 24 : -24)));
      ws.splitters[zone].focus();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      app.setLayout(toggleCollapsed(app.layout, zone));
      ws.splitters[zone].focus();
    }
  });
  return el;
}

/** Re-apply the layout after a change without rebuilding content. */
export function applyLayout(app) { if (ws && document.body.contains(ws.root)) renderFrames(app); }

export function resetWorkspace() { ws = null; }
