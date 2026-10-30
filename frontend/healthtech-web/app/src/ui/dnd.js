// Pointer-based drag and drop (mouse, pen and touch) following the Eleken
// guidance: visible handle, lift + ghost while moving, valid targets light up,
// invalid ones dim, a landing highlight, a confirmation bounce on drop, a
// fly-back on cancel (Escape or empty drop), and live-region announcements.
// Every drag also has a button/keyboard alternative in the UI that uses it.
import { animate, pop } from './motion.js';

let active = null;
const THRESHOLD = 5;

/**
 * Make `handle` start a drag of `source` carrying {type, payload, label}.
 * Drop targets are elements with data-drop="typeA typeB" and an `ondropitem`
 * property: (item, target) => boolean|Promise<boolean>.
 */
export function draggable(handle, source, item, announce) {
  handle.classList.add('drag-handle');
  handle.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    const start = { x: e.clientX, y: e.clientY };
    let started = false;
    handle.setPointerCapture(e.pointerId);
    const move = (ev) => {
      if (!started && Math.hypot(ev.clientX - start.x, ev.clientY - start.y) > THRESHOLD) {
        started = true;
        begin(source, item, ev, announce);
      }
      if (started) update(ev);
    };
    const up = async (ev) => {
      handle.removeEventListener('pointermove', move);
      handle.removeEventListener('pointerup', up);
      handle.removeEventListener('pointercancel', up);
      if (started) await finish(ev.type === 'pointercancel');
    };
    handle.addEventListener('pointermove', move);
    handle.addEventListener('pointerup', up);
    handle.addEventListener('pointercancel', up);
  });
}

function targetsFor(type) {
  return [...document.querySelectorAll('[data-drop]')].filter((t) => t.dataset.drop.split(' ').includes(type));
}

function begin(source, item, ev, announce) {
  const rect = source.getBoundingClientRect();
  const ghost = source.cloneNode(true);
  ghost.removeAttribute('id');
  ghost.querySelectorAll('[id]').forEach((n) => n.removeAttribute('id'));
  ghost.className += ' drag-ghost';
  ghost.setAttribute('aria-hidden', 'true');
  Object.assign(ghost.style, { width: `${rect.width}px`, left: `${rect.left}px`, top: `${rect.top}px` });
  document.body.append(ghost);
  source.classList.add('drag-source');
  document.body.classList.add('is-dragging');
  document.body.dataset.dragType = item.type;
  const valid = targetsFor(item.type);
  valid.forEach((t) => t.classList.add('drop-valid'));
  active = { source, item, ghost, offset: { x: ev.clientX - rect.left, y: ev.clientY - rect.top }, origin: rect, valid, over: null, announce };
  animate(ghost, [{ transform: 'scale(1) rotate(0deg)' }, { transform: 'scale(1.04) rotate(-1.5deg)' }], { duration: 160, fill: 'forwards' });
  announce?.(`${item.label} — ${document.documentElement.lang === 'th' ? 'หยิบแล้ว ลากไปวางที่เป้าหมายที่ไฮไลต์ หรือกด Escape เพื่อยกเลิก' : 'picked up. Drop on a highlighted target, or press Escape to cancel.'}`);
  window.addEventListener('keydown', onKey);
}

function onKey(e) { if (e.key === 'Escape' && active) { e.preventDefault(); finish(true); } }

function update(ev) {
  const a = active;
  if (!a) return;
  a.ghost.style.left = `${ev.clientX - a.offset.x}px`;
  a.ghost.style.top = `${ev.clientY - a.offset.y}px`;
  a.ghost.style.pointerEvents = 'none';
  // Nearest ancestor that accepts this item type (a card inside a list may accept other types).
  let over = null;
  for (let n = document.elementFromPoint(ev.clientX, ev.clientY); n; n = n.parentElement) {
    if (a.valid.includes(n)) { over = n; break; }
  }
  if (over !== a.over) {
    a.over?.classList.remove('drop-over');
    over?.classList.add('drop-over');
    a.over = over;
  }
}

async function finish(cancel) {
  const a = active;
  if (!a) return;
  active = null;
  window.removeEventListener('keydown', onKey);
  const cleanup = () => {
    a.ghost.remove();
    a.source.classList.remove('drag-source');
    document.body.classList.remove('is-dragging');
    delete document.body.dataset.dragType;
    a.valid.forEach((t) => t.classList.remove('drop-valid', 'drop-over'));
  };
  const th = document.documentElement.lang === 'th';
  if (!cancel && a.over) {
    const target = a.over;
    const ok = await target.ondropitem?.(a.item, target);
    cleanup();
    if (ok !== false) {
      pop(target);
      a.announce?.(`${a.item.label} → ${target.dataset.dropLabel || ''} ${th ? 'วางแล้ว' : 'dropped'}`);
      return;
    }
  }
  // Fly back to where it came from.
  const anim = animate(a.ghost, [
    { left: a.ghost.style.left, top: a.ghost.style.top, opacity: 1 },
    { left: `${a.origin.left}px`, top: `${a.origin.top}px`, opacity: 0.2 },
  ], { duration: 260 });
  if (anim) await anim.finished.catch(() => {});
  cleanup();
  a.announce?.(th ? 'ยกเลิกการลาก ไม่มีอะไรเปลี่ยน' : 'Drag cancelled; nothing changed.');
}

/** Native file drops (from the operating system) onto `zone`. */
export function fileDropZone(zone, onFiles) {
  zone.addEventListener('dragover', (e) => { if ([...e.dataTransfer.types].includes('Files')) { e.preventDefault(); zone.classList.add('drop-over'); } });
  zone.addEventListener('dragleave', () => zone.classList.remove('drop-over'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drop-over');
    if (e.dataTransfer.files.length) onFiles([...e.dataTransfer.files]);
  });
}
