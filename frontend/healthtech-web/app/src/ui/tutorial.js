// Step-by-step tutorial video in a native <dialog>: chapter buttons seek the
// video, the current chapter is highlighted, and a text transcript sits beside
// it. Nothing autoplays; the viewer presses play.
import { h } from './dom.js';
import { loadTutorialManifest } from '../adapters.js';

export async function openTutorial(app, opener) {
  const t = app.t;
  const locale = app.state.locale;
  let manifest = null;
  try { manifest = await loadTutorialManifest(); } catch { manifest = null; }
  const chapters = manifest?.chapters || [];
  const fileFor = (m) => m?.videos?.[locale] || m?.videos?.en;
  const video = fileFor(manifest)
    ? h('video', { id: 'tutorial-video', controls: true, preload: 'metadata', playsinline: true, poster: manifest.posters?.[locale] || null, src: fileFor(manifest) },
      manifest.chapterTracks?.[locale] ? h('track', { kind: 'chapters', srclang: locale, label: t('tutorial.chapters'), src: manifest.chapterTracks[locale], default: true }) : null)
    : null;
  const list = h('ol', { class: 'tutorial-chapters' }, chapters.map((c, i) => h('li', {},
    h('button', { type: 'button', class: 'chapter', id: `chapter-${c.id}`, 'data-start': String(c.start), disabled: !video,
      onClick: () => { if (!video) return; video.currentTime = c.start; video.play().catch(() => {}); } },
    h('span', { class: 'chapter-n' }, String(i + 1)),
    h('span', { class: 'chapter-text' }, h('strong', {}, c[locale]?.title || c.en.title), h('span', { class: 'muted' }, c[locale]?.body || c.en.body)),
    h('span', { class: 'chapter-time mono' }, `${Math.floor(c.start / 60)}:${String(Math.floor(c.start % 60)).padStart(2, '0')}`)))));
  if (video) {
    video.addEventListener('timeupdate', () => {
      let cur = 0;
      chapters.forEach((c, i) => { if (video.currentTime >= c.start - 0.05) cur = i; });
      list.querySelectorAll('.chapter').forEach((b, i) => b.setAttribute('aria-current', i === cur ? 'step' : 'false'));
    });
  }
  const dialog = h('dialog', { class: 'tutorial', 'aria-labelledby': 'tutorial-title' },
    h('div', { class: 'tutorial-head' },
      h('h2', { id: 'tutorial-title' }, `🎬 ${t('tutorial.title')}`),
      h('button', { type: 'button', class: 'tour-close', id: 'tutorial-close', 'aria-label': t('common.close'), onClick: () => dialog.close() }, '×')),
    h('div', { class: 'tutorial-body' },
      h('div', { class: 'tutorial-player' },
        video || h('div', { class: 'callout callout-info', id: 'tutorial-missing' }, t('tutorial.missing')),
        h('p', { class: 'muted tutorial-note' }, manifest?.note?.[locale] || t('tutorial.note'))),
      h('div', { class: 'tutorial-side' }, h('h3', {}, t('tutorial.chapters')), list)));
  dialog.addEventListener('close', () => {
    video?.pause();
    dialog.remove();
    const target = opener?.isConnected ? opener : (opener?.id ? document.getElementById(opener.id) : null);
    target?.focus?.();
  });
  document.body.append(dialog);
  dialog.showModal();
  dialog.querySelector('#tutorial-title').setAttribute('tabindex', '-1');
  dialog.querySelector('#tutorial-title').focus();
  return dialog;
}
