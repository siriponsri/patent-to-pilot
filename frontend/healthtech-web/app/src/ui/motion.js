// Motion helpers (Web Animations API). Every effect is decorative: state is
// always also shown as text/icon, and all motion stops when the OS asks for
// reduced motion or the user picks "reduced" in the app.

let preference = 'full';

export function setMotionPreference(p) {
  preference = p === 'reduced' ? 'reduced' : 'full';
  document.documentElement.dataset.motion = motionOn() ? 'full' : 'reduced';
}

export function motionOn() {
  return preference === 'full' && !globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Display pacing between real steps; zero when motion is off. */
export function pace(ms) { return motionOn() ? sleep(ms) : Promise.resolve(); }

export function animate(el, keyframes, options) {
  if (!el || !motionOn() || !el.animate) return null;
  return el.animate(keyframes, { easing: 'cubic-bezier(.2,.8,.2,1)', ...options });
}

/** Staggered entrance for a set of elements. */
export function enter(els, { delay = 40, distance = 14 } = {}) {
  [...els].forEach((el, i) => animate(el, [
    { opacity: 0, transform: `translateY(${distance}px) scale(.97)` },
    { opacity: 1, transform: 'none' },
  ], { duration: 420, delay: i * delay, fill: 'backwards' }));
}

export function pop(el) {
  animate(el, [{ transform: 'scale(1)' }, { transform: 'scale(1.08)' }, { transform: 'scale(.98)' }, { transform: 'scale(1)' }], { duration: 480 });
}

export function burst(el, color = 'var(--successText)') {
  animate(el, [
    { boxShadow: `0 0 0 0 color-mix(in srgb, ${color} 55%, transparent)` },
    { boxShadow: `0 0 0 18px color-mix(in srgb, ${color} 0%, transparent)` },
  ], { duration: 700 });
}

export function shake(el) {
  animate(el, [{ transform: 'translateX(0)' }, { transform: 'translateX(-6px)' }, { transform: 'translateX(6px)' }, { transform: 'translateX(-3px)' }, { transform: 'translateX(0)' }], { duration: 420 });
}

/** A glowing particle travelling along an SVG path `d` inside `layer`. */
export function travel(layer, d, { duration = 650, className = 'particle' } = {}) {
  if (!motionOn() || !layer) return Promise.resolve();
  const dot = document.createElement('span');
  dot.className = className;
  dot.style.offsetPath = `path('${d}')`;
  layer.append(dot);
  const a = dot.animate([{ offsetDistance: '0%', opacity: 0 }, { opacity: 1, offset: 0.15 }, { offsetDistance: '100%', opacity: 0.2 }], { duration, easing: 'ease-in-out' });
  return a.finished.catch(() => {}).then(() => dot.remove());
}
