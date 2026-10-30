// Node canvas (n8n/Make-style). Nodes are links in a <nav> list, so the
// pipeline stays a keyboard- and screen-reader-friendly ordered list; the
// canvas only positions them. Pan: drag empty space or arrow keys on the
// canvas. Zoom: wheel, +/- buttons or keys. Move a node: drag it, or
// Alt+Arrow while it has focus. Positions are a per-browser convenience.
import { h } from './dom.js';
import { NODES, EDGES } from '../core/pipeline.js';
import { animate, pop, burst, shake, travel, enter, motionOn } from './motion.js';

export const NODE_W = 210;
export const NODE_H = 100;
const POS_KEY = 'p2p-healthtech-ux-nodepos';

function loadPositions() {
  try { return JSON.parse(localStorage.getItem(POS_KEY) || '{}') || {}; } catch { return {}; }
}
function savePositions(p) {
  try { localStorage.setItem(POS_KEY, JSON.stringify(p)); } catch { /* convenience only */ }
}

const STATE_ICON = { idle: '○', running: '◌', pass: '✓', fail: '✕', warn: '!', skipped: '–', ready: '●', unavailable: '⊘' };

function edgePath(a, b) {
  const ax = a.x + NODE_W, ay = a.y + NODE_H / 2, bx = b.x, by = b.y + NODE_H / 2;
  const dx = b.x - a.x, dy = b.y - a.y;
  if (Math.abs(dy) > Math.abs(dx) * 0.8) {
    // Mostly vertical: bottom/top ports.
    const sx = a.x + NODE_W / 2, sy = dy > 0 ? a.y + NODE_H : a.y, tx = b.x + NODE_W / 2, ty = dy > 0 ? b.y : b.y + NODE_H;
    const c = Math.max(40, Math.abs(ty - sy) / 2) * Math.sign(dy || 1);
    return `M ${sx} ${sy} C ${sx} ${sy + c}, ${tx} ${ty - c}, ${tx} ${ty}`;
  }
  if (dx < 0) {
    // Right-to-left: leave from the left port into the target's right port.
    const sx = a.x, tx = b.x + NODE_W;
    const c = Math.max(60, Math.abs(tx - sx) / 2);
    return `M ${sx} ${ay} C ${sx - c} ${ay}, ${tx + c} ${by}, ${tx} ${by}`;
  }
  const c = Math.max(60, (bx - ax) / 2);
  return `M ${ax} ${ay} C ${ax + c} ${ay}, ${bx - c} ${by}, ${bx} ${by}`;
}

export function createCanvas(app) {
  const t = () => app.t;
  const pos = Object.fromEntries(NODES.map((n) => [n.id, { x: n.x, y: n.y }]));
  for (const [id, p] of Object.entries(loadPositions())) if (pos[id] && Number.isFinite(p.x) && Number.isFinite(p.y)) pos[id] = { x: p.x, y: p.y };
  const view = { x: 0, y: 0, k: 1 };
  const edgesSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  edgesSvg.setAttribute('class', 'canvas-edges');
  edgesSvg.setAttribute('aria-hidden', 'true');
  const particles = h('div', { class: 'canvas-particles', 'aria-hidden': 'true' });
  const list = h('ol', { class: 'node-list' });
  const nav = h('nav', { class: 'node-nav', 'aria-label': 'pipeline' }, list);
  const world = h('div', { class: 'canvas-world' }, edgesSvg, particles, nav);
  const viewport = h('div', { class: 'canvas-viewport', tabindex: '0', role: 'group' }, world);
  const zoomLabel = h('span', { class: 'zoom-label', 'aria-live': 'off' }, '100%');
  const toolbar = h('div', { class: 'canvas-toolbar', role: 'toolbar' });
  const root = h('section', { class: 'canvas' }, toolbar, viewport);
  const nodeEls = {};
  const edgeEls = [];
  let prevStates = {};
  let pid = null;

  function applyView() {
    world.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.k})`;
    zoomLabel.textContent = `${Math.round(view.k * 100)}%`;
  }

  function layoutEdges() {
    for (const e of edgeEls) e.path.setAttribute('d', edgePath(pos[e.a], pos[e.b]));
  }

  function placeNode(id) {
    nodeEls[id].style.left = `${pos[id].x}px`;
    nodeEls[id].style.top = `${pos[id].y}px`;
  }

  function fit() {
    const r = viewport.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const xs = NODES.map((n) => pos[n.id].x), ys = NODES.map((n) => pos[n.id].y);
    const minX = Math.min(...xs) - 30, minY = Math.min(...ys) - 30, maxX = Math.max(...xs) + NODE_W + 30, maxY = Math.max(...ys) + NODE_H + 30;
    view.k = Math.max(0.35, Math.min(1.15, Math.min(r.width / (maxX - minX), r.height / (maxY - minY))));
    view.x = (r.width - (maxX - minX) * view.k) / 2 - minX * view.k;
    view.y = (r.height - (maxY - minY) * view.k) / 2 - minY * view.k;
    applyView();
  }

  function zoomAt(factor, cx, cy) {
    const k = Math.max(0.3, Math.min(2, view.k * factor));
    view.x = cx - ((cx - view.x) * k) / view.k;
    view.y = cy - ((cy - view.y) * k) / view.k;
    view.k = k;
    applyView();
  }

  // ---- pan / zoom
  viewport.addEventListener('wheel', (e) => {
    e.preventDefault();
    const r = viewport.getBoundingClientRect();
    zoomAt(e.deltaY < 0 ? 1.1 : 1 / 1.1, e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });
  viewport.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.node') || e.button !== 0) return;
    const start = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
    viewport.setPointerCapture(e.pointerId);
    viewport.classList.add('panning');
    const move = (ev) => { view.x = start.vx + ev.clientX - start.x; view.y = start.vy + ev.clientY - start.y; applyView(); };
    const up = () => { viewport.classList.remove('panning'); viewport.removeEventListener('pointermove', move); viewport.removeEventListener('pointerup', up); };
    viewport.addEventListener('pointermove', move);
    viewport.addEventListener('pointerup', up);
  });
  viewport.addEventListener('keydown', (e) => {
    if (e.target !== viewport) return;
    const step = 40;
    const r = viewport.getBoundingClientRect();
    const map = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] };
    if (map[e.key]) { e.preventDefault(); view.x += map[e.key][0]; view.y += map[e.key][1]; applyView(); }
    else if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomAt(1.15, r.width / 2, r.height / 2); }
    else if (e.key === '-') { e.preventDefault(); zoomAt(1 / 1.15, r.width / 2, r.height / 2); }
    else if (e.key === '0') { e.preventDefault(); fit(); }
  });

  // ---- nodes
  function nodeDrag(el, id) {
    let moved = false;
    el.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      moved = false;
      const start = { x: e.clientX, y: e.clientY, nx: pos[id].x, ny: pos[id].y };
      const move = (ev) => {
        const dx = (ev.clientX - start.x) / view.k, dy = (ev.clientY - start.y) / view.k;
        if (!moved && Math.hypot(dx, dy) < 5) return;
        if (!moved) { moved = true; el.setPointerCapture(e.pointerId); el.classList.add('node-moving'); }
        pos[id] = { x: Math.round((start.nx + dx) / 10) * 10, y: Math.round((start.ny + dy) / 10) * 10 }; // snap to 10
        placeNode(id);
        layoutEdges();
      };
      const up = () => {
        el.removeEventListener('pointermove', move);
        el.removeEventListener('pointerup', up);
        el.classList.remove('node-moving');
        if (moved) savePositions(pos);
      };
      el.addEventListener('pointermove', move);
      el.addEventListener('pointerup', up);
    });
    // A drag is not a click.
    el.addEventListener('click', (e) => { if (moved) { e.preventDefault(); moved = false; } });
    el.addEventListener('keydown', (e) => {
      const map = { ArrowLeft: [-20, 0], ArrowRight: [20, 0], ArrowUp: [0, -20], ArrowDown: [0, 20] };
      if (e.altKey && map[e.key]) {
        e.preventDefault();
        pos[id] = { x: pos[id].x + map[e.key][0], y: pos[id].y + map[e.key][1] };
        placeNode(id); layoutEdges(); savePositions(pos);
      }
    });
  }

  function build(projectId) {
    pid = projectId;
    list.replaceChildren();
    edgesSvg.replaceChildren();
    edgeEls.length = 0;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const grad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    grad.setAttribute('id', 'edge-flow');
    [['0%', 'var(--primary)'], ['100%', 'var(--syntheticText)']].forEach(([o, c]) => {
      const s = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
      s.setAttribute('offset', o); s.setAttribute('stop-color', c); grad.append(s);
    });
    defs.append(grad);
    edgesSvg.append(defs);
    for (const [a, b, kind] of EDGES) {
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('class', `edge${kind === 'future' ? ' edge-future' : ''}`);
      edgesSvg.append(path);
      edgeEls.push({ a, b, path, kind });
    }
    for (const n of NODES) {
      const el = h('a', { class: `node node-${n.kind}`, id: `node-${n.id}`, href: `#/project/${encodeURIComponent(projectId)}/${n.view}${n.tab ? `?tab=${n.tab}` : ''}`, 'data-node': n.id, 'data-kind': n.kind, 'data-state': 'idle' },
        h('span', { class: 'node-icon', 'aria-hidden': 'true' }, n.icon),
        h('span', { class: 'node-body' },
          h('span', { class: 'node-title' }),
          h('span', { class: 'node-state' }),
          h('span', { class: 'node-summary' }),
          h('span', { class: 'node-dots', 'aria-hidden': 'true' })),
        h('span', { class: 'node-port in', 'aria-hidden': 'true' }), h('span', { class: 'node-port out', 'aria-hidden': 'true' }));
      nodeEls[n.id] = el;
      nodeDrag(el, n.id);
      list.append(h('li', {}, el));
      placeNode(n.id);
    }
    layoutEdges();
    prevStates = {};
    enter(Object.values(nodeEls), { delay: 45 });
    requestAnimationFrame(fit);
  }

  toolbar.append(
    h('button', { type: 'button', class: 'btn btn-small', id: 'canvas-zoom-out', onClick: () => { const r = viewport.getBoundingClientRect(); zoomAt(1 / 1.15, r.width / 2, r.height / 2); } }, '−'),
    zoomLabel,
    h('button', { type: 'button', class: 'btn btn-small', id: 'canvas-zoom-in', onClick: () => { const r = viewport.getBoundingClientRect(); zoomAt(1.15, r.width / 2, r.height / 2); } }, '+'),
    h('button', { type: 'button', class: 'btn btn-small', id: 'canvas-fit', onClick: fit }, '⤢'),
    h('button', { type: 'button', class: 'btn btn-small', id: 'canvas-reset-nodes', onClick: () => { for (const n of NODES) pos[n.id] = { x: n.x, y: n.y }; NODES.forEach((n) => placeNode(n.id)); layoutEdges(); savePositions({}); fit(); } }, '↺'));

  /** Reflect pipeline state: labels, dots, edge flow and transition effects. */
  function update(pipe, selectedNode) {
    const tr = t();
    viewport.setAttribute('aria-label', tr('canvas.label'));
    nav.setAttribute('aria-label', tr('canvas.steps'));
    toolbar.setAttribute('aria-label', tr('canvas.tools'));
    for (const [id, label] of [['canvas-zoom-out', 'canvas.zoomOut'], ['canvas-zoom-in', 'canvas.zoomIn'], ['canvas-fit', 'canvas.fit'], ['canvas-reset-nodes', 'canvas.resetNodes']]) {
      toolbar.querySelector(`#${id}`)?.setAttribute('aria-label', tr(label));
      toolbar.querySelector(`#${id}`)?.setAttribute('title', tr(label));
    }
    for (const n of NODES) {
      const el = nodeEls[n.id];
      const state = pipe.states[n.id];
      const info = pipe.info[n.id] || {};
      el.dataset.state = state;
      el.querySelector('.node-title').textContent = tr(`node.${n.id}`);
      el.querySelector('.node-state').textContent = `${STATE_ICON[state]} ${tr(`nstate.${state}`)}`;
      el.querySelector('.node-summary').textContent = info.summary || tr(`node.${n.id}.desc`);
      el.title = `${tr(`node.${n.id}`)} — ${info.summary || tr(`node.${n.id}.desc`)}`; // full text when clamped
      const dots = el.querySelector('.node-dots');
      dots.replaceChildren(...(info.items || []).slice(0, 14).map((it) => h('span', { class: `dot ${it.ok ? 'ok' : 'bad'}` })));
      if (selectedNode === n.id) el.setAttribute('aria-current', 'page'); else el.removeAttribute('aria-current');
      const prev = prevStates[n.id];
      if (prev && prev !== state) {
        if (state === 'pass' || state === 'ready') { pop(el); burst(el); }
        else if (state === 'fail') shake(el);
        if (state === 'running') {
          for (const e of edgeEls) if (e.b === n.id && ['pass', 'ready'].includes(pipe.states[e.a])) travel(particles, e.path.getAttribute('d'));
        }
      }
    }
    for (const e of edgeEls) {
      const sa = pipe.states[e.a], sb = pipe.states[e.b];
      e.path.classList.toggle('edge-flow', motionOn() && sb === 'running');
      e.path.classList.toggle('edge-done', ['pass', 'ready'].includes(sa) && ['pass', 'ready', 'warn'].includes(sb));
      e.path.classList.toggle('edge-fail', sa === 'fail' || sb === 'fail');
    }
    prevStates = { ...pipe.states };
  }

  /** Make a node accept dropped items (requests/review). */
  function dropTarget(id, types, label, handler) {
    const el = nodeEls[id];
    el.dataset.drop = types;
    el.dataset.dropLabel = label;
    el.ondropitem = handler;
  }

  function pulse(id) { animate(nodeEls[id], [{ filter: 'brightness(1)' }, { filter: 'brightness(1.35)' }, { filter: 'brightness(1)' }], { duration: 500 }); }

  return { el: root, build, update, fit, dropTarget, pulse, get projectId() { return pid; }, nodeEls };
}
