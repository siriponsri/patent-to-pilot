// Build the step-by-step tutorial videos from the REAL app.
//
// 1. Drive the app in headless Chrome (synthetic demo dossier only) and capture
//    each step's actual screen plus the on-screen rectangle of the thing to look at.
// 2. Write one HyperFrames project per locale (out/<locale>/) whose scenes push in
//    on those screenshots with a highlight ring, a cursor and a short caption.
// 3. `node tutorial-video/build.mjs --render` also renders both projects and writes
//    app/media/{tutorial-th.mp4, tutorial-en.mp4, tutorial.json, *.chapters.vtt, posters}.
//
// No narration; the composition has a named <audio> slot for a licensed music bed.
import { mkdirSync, writeFileSync, rmSync, copyFileSync, existsSync, readdirSync } from 'node:fs';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { launch, sleep } from '../tests/e2e/cdp.mjs';
import { startServer } from '../serve.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const WEB = resolve(here, '..');
const OUT = join(here, 'out');
const MEDIA = join(WEB, 'app/media');
const W = 1600, H = 900, DSF = 1.2; // screenshots are 1920x1080 device pixels
const LOCALES = (process.env.TUTORIAL_LOCALES || 'th,en').split(',').filter((l) => ['th', 'en'].includes(l));

const COPY = {
  th: {
    introTitle: 'Patent-to-Pilot HealthTech', introSub: 'แฟ้มหลักฐานอุปกรณ์การแพทย์ ทำครบใน 5 ขั้น',
    steps: ['โหลด', 'ตรวจ', 'ทบทวน', 'ถามต่อ', 'ส่งออก'],
    s1: ['เปิดแฟ้มตัวอย่าง', 'กดเปิดตัวอย่าง ระบบเริ่มตรวจทีละขั้นทันที'],
    s2: ['ดูการตรวจทำงานจริง', 'ทุกโหนดตรวจ hash และตำแหน่งอ้างอิงในเครื่องคุณ'],
    s3: ['ลากหลักฐานไปจดบันทึก', 'วางการ์ดบนโหนดการทบทวน แล้วเขียนข้อสังเกต'],
    s4: ['เตรียมคำถามที่ต้องขอเพิ่ม', 'ลากประเด็นที่ยังค้างไปวางที่คำขอข้อมูล'],
    s5: ['ส่งออกรายงานไทยหรืออังกฤษ', 'รายงานรวมบันทึกของคุณ พร้อมไฟล์กู้คืน'],
    outro: ['ตรวจที่มาได้ทุกขั้น', 'ข้อสรุปยังเป็นของคุณ'], note: 'ข้อมูลในวิดีโอเป็นข้อมูลสมมติ ไม่ใช่หลักฐานจริง',
    chapterBodies: ['เปิดแฟ้มตัวอย่างแล้วดูระบบเริ่มตรวจ', 'โหนดแต่ละขั้นตรวจ hash และตำแหน่งอ้างอิงจริง', 'ลากการ์ดหลักฐานไปที่การทบทวนแล้วจดบันทึก', 'ลากประเด็นที่ยังค้างไปเป็นคำขอข้อมูล', 'ดูตัวอย่างแล้วดาวน์โหลดรายงาน'],
  },
  en: {
    introTitle: 'Patent-to-Pilot HealthTech', introSub: 'A device evidence dossier in five steps',
    steps: ['Load', 'Check', 'Review', 'Ask', 'Export'],
    s1: ['Open the demo dossier', 'Checks start one step at a time'],
    s2: ['Watch real checks run', 'Each node verifies hashes and locators locally'],
    s3: ['Drag evidence into a note', 'Drop a card on Review, then write'],
    s4: ['Draft what to ask next', 'Drag an open issue onto Requests'],
    s5: ['Export a Thai or English report', 'Your notes included, plus a recovery file'],
    outro: ['Every step is traceable', 'The conclusion stays yours'], note: 'Synthetic demo data. Not real evidence.',
    chapterBodies: ['Open the demo and watch checks start', 'Each node verifies hashes and locators for real', 'Drag an evidence card to Review and write a note', 'Turn an open issue into an information request', 'Preview and download the report'],
  },
};

// Scene plan: id, seconds, screenshots and what to point at.
const SCENES = [
  { id: 'intro', dur: 4 },
  { id: 's1', dur: 9, step: 0, shots: ['home', 'running'] },
  { id: 's2', dur: 9, step: 1, shots: ['checked', 'checks'] },
  { id: 's3', dur: 11, step: 2, shots: ['drag-review', 'note'] },
  { id: 's4', dur: 9, step: 3, shots: ['drag-request', 'requests'] },
  { id: 's5', dur: 9, step: 4, shots: ['export'] },
  { id: 'outro', dur: 5, shots: ['done'] },
];

async function rectOf(page, selector) {
  const r = await page.eval(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el) return null; el.scrollIntoView({ block: 'nearest' }); const b = el.getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height }; })()`);
  if (!r) throw new Error(`no element for ${selector}`);
  return { x: Math.round(r.x * DSF), y: Math.round(r.y * DSF), w: Math.round(r.w * DSF), h: Math.round(r.h * DSF) };
}

async function shot(page, dir, name, focusSel) {
  console.log('shot', name);
  const focus = focusSel ? await rectOf(page, focusSel) : null;
  await sleep(250);
  await page.screenshot(join(dir, `${name}.jpg`), { full: false, quality: 90 });
  return { name, focus };
}

async function mouse(page, type, x, y) {
  await page.send('Input.dispatchMouseEvent', { type, x, y, button: 'left', buttons: type === 'mouseReleased' ? 0 : 1, clickCount: type === 'mouseMoved' ? 0 : 1 });
}

/** Real pointer drag from one element to another; screenshot while hovering the target. */
async function dragShot(page, dir, name, fromSel, toSel) {
  const from = await page.eval(`(() => { const el = document.querySelector(${JSON.stringify(fromSel)}); el.scrollIntoView({ block: 'center' }); const b = el.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; })()`);
  const to = await page.eval(`(() => { const b = document.querySelector(${JSON.stringify(toSel)}).getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; })()`);
  await mouse(page, 'mousePressed', from.x, from.y);
  for (let i = 1; i <= 16; i++) { await mouse(page, 'mouseMoved', from.x + ((to.x - from.x) * i) / 16, from.y + ((to.y - from.y) * i) / 16); await sleep(16); }
  await sleep(200);
  const s = await shot(page, dir, name, toSel);
  s.from = { x: Math.round(from.x * DSF), y: Math.round(from.y * DSF) };
  await mouse(page, 'mouseReleased', to.x, to.y);
  await sleep(500);
  return s;
}

async function capture(base, locale) {
  const dir = join(OUT, locale, 'assets', 'shots');
  mkdirSync(dir, { recursive: true });
  const browser = await launch(mkdtempSync(join(tmpdir(), 'tutorial-')));
  const page = await browser.newPage();
  await page.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: DSF, mobile: false });
  await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
  await page.goto(`${base}/`);
  await page.eval(`localStorage.setItem('p2p-healthtech-ux-prefs', JSON.stringify({ locale: '${locale}', theme: 'formal-dark', motion: 'full' })); localStorage.setItem('p2p-healthtech-ux-tour-seen', '1')`);
  await page.goto(`${base}/`);
  const shots = {};
  shots.home = await shot(page, dir, 'home', '#start-demo');
  await page.eval('document.getElementById("start-demo").click()');
  await page.waitFor('window.__healthtechApp.state.current?.pipe?.states?.evidence === "running"', 15000);
  shots.running = await shot(page, dir, 'running', '#node-evidence');
  await page.waitFor('window.__healthtechApp.state.current?.pipe?.lastResult', 15000);
  await sleep(1200);
  shots.checked = await shot(page, dir, 'checked', '#node-candidates');
  await page.eval(`location.hash = '#/project/' + encodeURIComponent(window.__healthtechApp.state.current.project.projectId) + '/checks'`);
  await page.waitFor('document.getElementById("checks-table")');
  shots.checks = await shot(page, dir, 'checks', '#checks-table');
  await page.eval(`location.hash = '#/project/' + encodeURIComponent(window.__healthtechApp.state.current.project.projectId)`);
  await page.waitFor('document.querySelector(".lib-card[data-evidence=ux-e-unicode] .lib-handle")');
  await sleep(400);
  shots['drag-review'] = await dragShot(page, dir, 'drag-review', '.lib-card[data-evidence=ux-e-unicode] .lib-handle', '#node-review');
  await page.waitFor('document.activeElement?.tagName === "TEXTAREA"', 8000);
  await page.send('Input.insertText', { text: locale === 'th' ? 'ต้องขอแหล่งที่ลงวันที่จริงก่อนสรุป' : 'Need a dated real source before concluding' });
  await page.eval('window.__healthtechApp.saveNow()');
  await sleep(600);
  shots.note = await shot(page, dir, 'note', '.note-editor .note:last-of-type textarea');
  await page.eval(`location.hash = '#/project/' + encodeURIComponent(window.__healthtechApp.state.current.project.projectId)`);
  await page.waitFor('document.querySelector(".lib-card.lib-gap .lib-handle")');
  await sleep(400);
  shots['drag-request'] = await dragShot(page, dir, 'drag-request', '.lib-card.lib-gap .lib-handle', '#node-requests');
  await page.eval(`location.hash = '#/project/' + encodeURIComponent(window.__healthtechApp.state.current.project.projectId) + '/requests'`);
  await page.waitFor('document.querySelector(".request-list li:last-child")');
  await sleep(400);
  shots.requests = await shot(page, dir, 'requests', '.request-list li:last-child');
  await page.eval(`location.hash = '#/project/' + encodeURIComponent(window.__healthtechApp.state.current.project.projectId) + '/export'`);
  await page.waitFor('document.getElementById("export-preview")');
  await page.eval(`document.getElementById('export-lang-${locale}').click(); document.getElementById('export-format-md').click();`);
  await page.eval('document.getElementById("export-preview").click()');
  await page.waitFor('document.getElementById("export-preview-text")');
  await page.send('Browser.setDownloadBehavior', { behavior: 'deny' });
  await page.eval('document.getElementById("export-download").click()');
  await sleep(500);
  shots.export = await shot(page, dir, 'export', '#export-download');
  await page.eval('document.querySelectorAll("#toasts .toast").forEach((t) => t.remove())');
  await sleep(300);
  shots.done = await shot(page, dir, 'done', '.journey');
  if (page.errors.length) console.warn('page errors', page.errors);
  await browser.close();
  return shots;
}

// ------------------------------------------------------------------ HyperFrames project writer
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const BASE_CSS = `
  @font-face { font-family: 'UIThai'; src: local('Leelawadee UI'); font-weight: 400; }
  @font-face { font-family: 'UIThai'; src: local('Leelawadee UI Bold'), local('Leelawadee UI'); font-weight: 700; }
  #root { position: absolute; inset: 0; overflow: hidden; background: #070b16; font-family: 'UIThai', 'Inter', sans-serif; color: #f4f7ff; }`;

function stepsStrip(id, labels, current) {
  return `<div id="${id}-steps" class="steps">${labels.map((l, i) => `<div id="${id}-step${i}" class="step${i < current ? ' done' : ''}${i === current ? ' now' : ''}"><span class="num">${i < current ? '✓' : i + 1}</span><span class="lbl">${esc(l)}</span></div>`).join('')}</div>`;
}

function sceneHtml(scene, copy, shots) {
  const { id, dur } = scene;
  const css = `${BASE_CSS}
  #${id}-stage { position: absolute; inset: 0; }
  #${id}-cam { position: absolute; inset: 0; }
  .shot { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
  .ring { position: absolute; border-radius: 16px; border: 5px solid #7cc4ff; box-shadow: 0 0 0 6px rgba(124,196,255,.25), 0 0 60px 10px rgba(124,196,255,.45); }
  .dim { position: absolute; inset: 0; background: radial-gradient(60% 60% at 50% 40%, rgba(7,11,22,0) 0%, rgba(7,11,22,.55) 100%); }
  .cursor { position: absolute; left: 0; top: 0; width: 46px; height: 46px; }
  .cap { position: absolute; left: 192px; right: 192px; bottom: 96px; padding: 26px 40px 30px; border-radius: 26px; background: rgba(9,14,28,.86); border: 1px solid rgba(157,198,240,.35); box-shadow: 0 30px 80px rgba(0,0,0,.5); }
  .cap .chip { display: inline-block; font-size: 30px; font-weight: 700; color: #0b1220; background: linear-gradient(90deg,#9dc6f0,#dcc2ff); padding: 6px 18px; border-radius: 999px; }
  .cap h2 { margin: 14px 0 6px; font-size: 64px; line-height: 1.15; font-weight: 700; }
  .cap p { margin: 0; font-size: 36px; line-height: 1.45; color: #c9d6ea; }
  .steps { position: absolute; left: 192px; right: 192px; top: 54px; display: flex; justify-content: space-between; padding: 14px 30px; border-radius: 999px; background: rgba(9,14,28,.8); border: 1px solid rgba(157,198,240,.3); }
  .step { display: flex; align-items: center; gap: 14px; font-size: 28px; color: #8fa3bf; font-weight: 700; }
  .step .num { width: 48px; height: 48px; border-radius: 50%; display: grid; place-items: center; border: 3px solid #4a5b78; }
  .step.done .num { border-color: #9be3b4; color: #9be3b4; }
  .step.now { color: #fff; }
  .step.now .num { background: #9dc6f0; border-color: #9dc6f0; color: #0b1220; }
  .title { position: absolute; left: 192px; right: 192px; top: 330px; text-align: center; }
  .title h1 { margin: 0; font-size: 104px; line-height: 1.1; letter-spacing: -1px; background: linear-gradient(90deg,#9dc6f0,#dcc2ff); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .title p { margin: 22px 0 0; font-size: 46px; color: #c9d6ea; }
  .note { position: absolute; left: 192px; right: 192px; bottom: 60px; text-align: center; font-size: 30px; color: #8fa3bf; }`;
  const parts = [];
  const tl = [];
  if (id === 'intro') {
    parts.push(`<img id="${id}-bg" class="shot" src="assets/shots/checked.jpg" alt="">`, `<div id="${id}-veil" class="dim"></div>`);
    parts.push(`<div id="${id}-title" class="title"><h1 id="${id}-h1">${esc(copy.introTitle)}</h1><p id="${id}-sub">${esc(copy.introSub)}</p></div>`);
    parts.push(stepsStrip(id, copy.steps, -1));
    tl.push(`tl.fromTo('#${id}-bg', { opacity: .3, scale: 1.12, filter: 'blur(14px)' }, { opacity: .35, scale: 1.04, filter: 'blur(10px)', duration: 3.6, ease: 'power2.out' }, 0);`);
    tl.push(`tl.fromTo('#${id}-h1', { opacity: 1, y: 24 }, { opacity: 1, y: 0, duration: .8, ease: 'power3.out' }, 0);`);
    tl.push(`tl.fromTo('#${id}-sub', { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: .7, ease: 'power3.out' }, .8);`);
    copy.steps.forEach((_, i) => tl.push(`tl.fromTo('#${id}-step${i}', { opacity: 0, y: -16 }, { opacity: 1, y: 0, duration: .4, ease: 'back.out(2)' }, ${(1.4 + i * 0.25).toFixed(2)});`));
  } else if (id === 'outro') {
    parts.push(`<img id="${id}-bg" class="shot" src="assets/shots/done.jpg" alt="">`, `<div id="${id}-veil" class="dim"></div>`);
    parts.push(stepsStrip(id, copy.steps, 5));
    parts.push(`<div id="${id}-title" class="title"><h1 id="${id}-h1">${esc(copy.outro[0])}</h1><p id="${id}-sub">${esc(copy.outro[1])}</p></div>`);
    parts.push(`<p id="${id}-note" class="note">${esc(copy.note)}</p>`);
    tl.push(`tl.fromTo('#${id}-bg', { opacity: 1, filter: 'blur(0px)' }, { opacity: .3, filter: 'blur(8px)', duration: 1.2, ease: 'power2.inOut' }, 0);`);
    tl.push(`tl.fromTo('#${id}-h1', { opacity: 0, scale: .92 }, { opacity: 1, scale: 1, duration: .8, ease: 'power3.out' }, .6);`);
    tl.push(`tl.fromTo('#${id}-sub', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: .6, ease: 'power3.out' }, 1.1);`);
    tl.push(`tl.fromTo('#${id}-note', { opacity: 0 }, { opacity: 1, duration: .5 }, 1.6);`);
  } else {
    const [a, b] = scene.shots.map((s) => shots[s]);
    const [title, sub] = copy[id];
    const focusA = a.focus, focusB = b?.focus;
    const ox = (f) => `${f.x + f.w / 2}px ${f.y + f.h / 2}px`;
    parts.push(`<div id="${id}-cam"><img id="${id}-a" class="shot" src="assets/shots/${a.name}.jpg" alt="">${b ? `<img id="${id}-b" class="shot" src="assets/shots/${b.name}.jpg" alt="">` : ''}`
      + `<div id="${id}-ringa" class="ring" style="left:${focusA.x - 10}px;top:${focusA.y - 10}px;width:${focusA.w + 20}px;height:${focusA.h + 20}px"></div>`
      + (focusB ? `<div id="${id}-ringb" class="ring" style="left:${focusB.x - 10}px;top:${focusB.y - 10}px;width:${focusB.w + 20}px;height:${focusB.h + 20}px"></div>` : '')
      + `</div>`);
    parts.push(`<div id="${id}-veil" class="dim"></div>`);
    parts.push(`<svg id="${id}-cursor" class="cursor" viewBox="0 0 24 24"><path d="M4 2 L20 12 L12.5 13.5 L9 21 Z" fill="#fff" stroke="#0b1220" stroke-width="1.5" stroke-linejoin="round"/></svg>`);
    parts.push(stepsStrip(id, copy.steps, scene.step));
    parts.push(`<div id="${id}-cap" class="cap"><span id="${id}-chip" class="chip">${scene.step + 1} / 5 · ${esc(copy.steps[scene.step])}</span><h2 id="${id}-h2">${esc(title)}</h2><p id="${id}-p">${esc(sub)}</p></div>`);
    const half = b ? dur * 0.5 : dur;
    const startPt = a.from || { x: 960, y: 760 };
    tl.push(`tl.fromTo('#${id}-cam', { opacity: 0, scale: 1.0, transformOrigin: '${ox(focusA)}' }, { opacity: 1, scale: 1.06, duration: ${half.toFixed(2)}, ease: 'none' }, 0);`);
    tl.push(`tl.fromTo('#${id}-cap', { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: .55, ease: 'power3.out' }, .25);`);
    tl.push(`tl.fromTo('#${id}-cursor', { x: ${startPt.x}, y: ${startPt.y}, opacity: 0 }, { x: ${focusA.x + focusA.w / 2}, y: ${focusA.y + focusA.h / 2}, opacity: 1, duration: 1.1, ease: 'power2.inOut' }, .6);`);
    tl.push(`tl.fromTo('#${id}-ringa', { opacity: 0, scale: 1.25 }, { opacity: 1, scale: 1, duration: .45, ease: 'back.out(2)' }, 1.7);`);
    tl.push(`tl.fromTo('#${id}-ringa', { boxShadow: '0 0 0 6px rgba(124,196,255,.25), 0 0 60px 10px rgba(124,196,255,.45)' }, { boxShadow: '0 0 0 16px rgba(124,196,255,0), 0 0 90px 20px rgba(124,196,255,.65)', duration: .7, ease: 'sine.inOut', repeat: 3, yoyo: true, immediateRender: false }, 2.2);`);
    if (b) {
      tl.push(`tl.fromTo('#${id}-ringa', { opacity: 1 }, { opacity: 0, duration: .3, immediateRender: false }, ${(half - 0.3).toFixed(2)});`);
      tl.push(`tl.fromTo('#${id}-b', { opacity: 0 }, { opacity: 1, duration: .6, ease: 'power2.inOut' }, ${half.toFixed(2)});`);
      tl.push(`tl.fromTo('#${id}-cam', { scale: 1.06, transformOrigin: '${ox(focusB)}' }, { scale: 1.1, duration: ${(dur - half).toFixed(2)}, ease: 'none', immediateRender: false }, ${half.toFixed(2)});`);
      tl.push(`tl.fromTo('#${id}-cursor', { x: ${focusA.x + focusA.w / 2}, y: ${focusA.y + focusA.h / 2} }, { x: ${focusB.x + focusB.w / 2}, y: ${focusB.y + focusB.h / 2}, duration: 1, ease: 'power2.inOut', immediateRender: false }, ${(half + 0.2).toFixed(2)});`);
      tl.push(`tl.fromTo('#${id}-ringb', { opacity: 0, scale: 1.25 }, { opacity: 1, scale: 1, duration: .45, ease: 'back.out(2)' }, ${(half + 1.1).toFixed(2)});`);
    }
  }
  return `<template>
  <style>${css}
  </style>
  <div id="root" data-composition-id="${id}" data-width="1920" data-height="1080">
    <div id="${id}-stage" class="clip" data-start="0" data-duration="${dur}">
      ${parts.join('\n      ')}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    ${tl.join('\n    ')}
    window.__timelines["${id}"] = tl;
  </script>
</template>
`;
}

function indexHtml(locale) {
  let t = 0;
  const hosts = SCENES.map((s, i) => {
    const html = `    <div id="${s.id}" data-composition-id="${s.id}" data-composition-src="compositions/${s.id}.html" data-start="${t}" data-duration="${s.dur}" data-track-index="${i + 1}" data-track-kind="graphics" data-width="1920" data-height="1080"></div>`;
    t += s.dur;
    return html;
  });
  return `<!doctype html>
<html lang="${locale}">
  <head>
    <meta charset="utf-8">
    <script src="assets/gsap.min.js"></script>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${t}" data-width="1920" data-height="1080">
${hosts.join('\n')}
      <!-- Music slot: add a licensed track as assets/music.mp3 and an <audio id="bgm" class="clip" data-start="0" data-duration="${t}" data-volume="0.35" src="assets/music.mp3"></audio> here, then re-render. -->
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({ paused: true });
    </script>
  </body>
</html>
`;
}

function chapters() {
  let t = 0;
  const starts = {};
  for (const s of SCENES) { starts[s.id] = t; t += s.dur; }
  return { total: t, list: ['s1', 's2', 's3', 's4', 's5'].map((id, i) => ({ id: `step${i + 1}`, start: i === 0 ? 0 : starts[id], end: (id === 's5' ? t : starts[`s${i + 2}`]) })) };
}

/** Render-time GSAP, pinned and cached locally so rendering never fetches from a CDN. */
function gsapFile() {
  const cache = join(here, '.cache');
  const file = join(cache, 'package', 'dist', 'gsap.min.js');
  if (!existsSync(file)) {
    mkdirSync(cache, { recursive: true });
    execFileSync('npm', ['pack', 'gsap@3.13.0', '--silent'], { cwd: cache, shell: true });
    execFileSync('tar', ['-xzf', 'gsap-3.13.0.tgz', 'package/dist/gsap.min.js', 'package/package.json'], { cwd: cache });
  }
  return file;
}

const vttTime = (s) => `00:${String(Math.floor(s / 60)).padStart(2, '0')}:${(s % 60).toFixed(3).padStart(6, '0')}`;

async function main() {
  const render = process.argv.includes('--render');
  mkdirSync(OUT, { recursive: true });
  for (const f of readdirSync(OUT)) rmSync(join(OUT, f), { recursive: true, force: true });
  const server = await startServer(0);
  const base = `http://127.0.0.1:${server.address().port}`;
  const ch = chapters();
  for (const locale of LOCALES) {
    const shots = await capture(base, locale);
    const proj = join(OUT, locale);
    mkdirSync(join(proj, 'compositions'), { recursive: true });
    writeFileSync(join(proj, 'index.html'), indexHtml(locale));
    for (const s of SCENES) writeFileSync(join(proj, 'compositions', `${s.id}.html`), sceneHtml(s, COPY[locale], shots));
    writeFileSync(join(proj, 'shots.json'), JSON.stringify(shots, null, 2));
    copyFileSync(gsapFile(), join(proj, 'assets', 'gsap.min.js'));
    console.log(`project written: ${proj}`);
  }
  server.close();
  mkdirSync(MEDIA, { recursive: true });
  const manifest = {
    format: 'healthtech-web-tutorial', version: 1, durationSec: ch.total,
    videos: Object.fromEntries(['th', 'en'].map((l) => [l, `media/tutorial-${l}.mp4`])),
    posters: Object.fromEntries(['th', 'en'].map((l) => [l, `media/tutorial-${l}.jpg`])),
    chapterTracks: Object.fromEntries(['th', 'en'].map((l) => [l, `media/tutorial-${l}.chapters.vtt`])),
    note: { th: COPY.th.note + ' · ไม่มีเสียงบรรยาย', en: COPY.en.note + ' · No narration' },
    chapters: ch.list.map((c, i) => ({ id: c.id, start: c.start, end: c.end,
      th: { title: `${COPY.th.steps[i]} — ${COPY.th[`s${i + 1}`][0]}`, body: COPY.th.chapterBodies[i] },
      en: { title: `${COPY.en.steps[i]} — ${COPY.en[`s${i + 1}`][0]}`, body: COPY.en.chapterBodies[i] } })),
  };
  for (const l of LOCALES) {
    writeFileSync(join(MEDIA, `tutorial-${l}.chapters.vtt`), `WEBVTT\n\n${manifest.chapters.map((c, i) => `${i + 1}\n${vttTime(c.start)} --> ${vttTime(c.end)}\n${c[l].title}\n`).join('\n')}`);
    copyFileSync(join(OUT, l, 'assets/shots/checked.jpg'), join(MEDIA, `tutorial-${l}.jpg`));
  }
  writeFileSync(join(MEDIA, 'tutorial.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  if (render) {
    for (const l of LOCALES) {
      // Delivery master (~55 MB) stays in the ignored out/; the app gets a web encode (~7 MB, faststart, no audio track).
      const master = join(OUT, `tutorial-${l}.master.mp4`);
      const out = join(MEDIA, `tutorial-${l}.mp4`);
      execFileSync('npx', ['-y', 'hyperframes@0.8.221', 'render', '--quality', 'delivery', '--output', master], { cwd: join(OUT, l), stdio: 'inherit', shell: true });
      if (!existsSync(master)) throw new Error(`render failed for ${l}`);
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', master, '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', out], { stdio: 'inherit' });
    }
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
