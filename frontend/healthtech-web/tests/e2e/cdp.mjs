// Minimal Chrome DevTools Protocol driver (Node >= 22 global WebSocket). No dependencies.
import { spawn } from 'node:child_process';
import { existsSync, readdirSync, statSync } from 'node:fs';

const CANDIDATES = [
  process.env.CHROME_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].filter(Boolean);

export function chromePath() {
  const found = CANDIDATES.find((p) => existsSync(p));
  if (!found) throw new Error('No Chrome/Edge found; set CHROME_PATH');
  return found;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function launch(profileDir) {
  const exe = chromePath();
  const proc = spawn(exe, [
    '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profileDir}`, '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--disable-component-update', '--disable-sync', '--disable-extensions', '--disable-default-apps',
    '--disable-features=Translate,OptimizationHints,MediaRouter,AutofillServerCommunication', '--metrics-recording-only', '--window-size=1280,900', 'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] });
  const wsUrl = await new Promise((resolve, reject) => {
    let buf = '';
    const timer = setTimeout(() => reject(new Error(`Chrome did not start: ${buf}`)), 20000);
    proc.stderr.on('data', (d) => {
      buf += d;
      const m = /DevTools listening on (ws:\/\/\S+)/.exec(buf);
      if (m) { clearTimeout(timer); resolve(m[1]); }
    });
    proc.on('exit', (code) => reject(new Error(`Chrome exited ${code}: ${buf}`)));
  });
  const browser = new Browser(proc, exe);
  await browser.connect(wsUrl);
  return browser;
}

export class Browser {
  constructor(proc, exe) { this.proc = proc; this.exe = exe; this.id = 0; this.pending = new Map(); this.listeners = []; }

  connect(url) {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(url);
      this.ws.onopen = () => resolve();
      this.ws.onerror = (e) => reject(e);
      this.ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve: ok, reject: bad } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          if (msg.error) bad(new Error(`${msg.error.message} ${msg.error.data || ''}`)); else ok(msg.result);
        } else if (msg.method) {
          for (const l of this.listeners) l(msg);
        }
      };
    });
  }

  send(method, params = {}, sessionId) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params, sessionId }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }

  async version() { return this.send('Browser.getVersion'); }

  async newPage(url) {
    const { targetId } = await this.send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await this.send('Target.attachToTarget', { targetId, flatten: true });
    const page = new Page(this, sessionId, targetId);
    await page.send('Page.enable');
    await page.send('Runtime.enable');
    const errors = page.errors;
    this.listeners.push((m) => {
      if (m.sessionId !== sessionId) return;
      if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
      if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map((a) => a.value ?? a.description).join(' '));
    });
    if (url) await page.goto(url);
    return page;
  }

  async close() {
    try { await this.send('Browser.close'); } catch { /* already closing */ }
    await new Promise((r) => { if (this.proc.exitCode !== null) r(); else { this.proc.on('exit', r); setTimeout(r, 5000); } });
    try { this.ws.close(); } catch { /* ignore */ }
  }
}

export class Page {
  constructor(browser, sessionId, targetId) { this.browser = browser; this.sessionId = sessionId; this.targetId = targetId; this.errors = []; }
  send(method, params) { return this.browser.send(method, params, this.sessionId); }

  /** Full document load (a fragment-only change would not reload the app). */
  async goto(url) {
    await this.send('Page.navigate', { url: 'about:blank' });
    await this.waitFor('location.href === "about:blank"', 5000);
    await this.send('Page.navigate', { url });
    await this.waitFor('document.readyState === "complete" && window.__healthtechApp && !window.__healthtechApp.state.booting', 15000);
  }

  async eval(expression) {
    const r = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true, userGesture: true });
    if (r.exceptionDetails) throw new Error(`eval failed: ${r.exceptionDetails.exception?.description || r.exceptionDetails.text}\n${expression.slice(0, 200)}`);
    return r.result.value;
  }

  async waitFor(expression, timeout = 8000) {
    const end = Date.now() + timeout;
    let last;
    while (Date.now() < end) {
      try { last = await this.eval(`(() => { try { return Boolean(${expression}); } catch { return false; } })()`); } catch (e) { last = e.message; }
      if (last === true) return true;
      await sleep(100);
    }
    throw new Error(`timeout waiting for: ${expression} (last=${last})`);
  }

  async hash(h) {
    await this.eval(`location.hash = ${JSON.stringify(h)}`);
    await sleep(150);
    await this.waitFor('document.querySelector("main h1")');
  }

  click(selector) { return this.eval(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el) throw new Error('no element ${selector.replace(/'/g, '')}'); el.click(); return true; })()`); }

  /** Focus a field and insert text through the input pipeline (fires real input events). */
  async type(selector, text, { replace = true } = {}) {
    await this.eval(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); el.focus(); if (${replace}) el.select?.(); return true; })()`);
    if (replace) await this.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Delete', code: 'Delete', windowsVirtualKeyCode: 46 }).then(() => this.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Delete', code: 'Delete', windowsVirtualKeyCode: 46 }));
    await this.send('Input.insertText', { text });
  }

  async key(key, code = key, vk = { Tab: 9, Enter: 13, Escape: 27, ' ': 32 }[key], modifiers = 0) {
    await this.send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key, code, windowsVirtualKeyCode: vk, modifiers, text: key === 'Enter' ? '\r' : undefined });
    if (key === 'Enter' || key === ' ') await this.send('Input.dispatchKeyEvent', { type: 'char', key, text: key === 'Enter' ? '\r' : ' ', modifiers });
    await this.send('Input.dispatchKeyEvent', { type: 'keyUp', key, code, windowsVirtualKeyCode: vk, modifiers });
    await sleep(40);
  }

  async setViewport(width, height = 900) {
    await this.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 600 });
    await sleep(150);
  }

  async screenshot(file) {
    const { data } = await this.send('Page.captureScreenshot', { format: 'jpeg', quality: 72, captureBeyondViewport: true });
    const { writeFileSync } = await import('node:fs');
    writeFileSync(file, Buffer.from(data, 'base64'));
    return file;
  }

  async setFiles(selector, files) {
    const { root } = await this.send('DOM.getDocument', { depth: 1 });
    const { nodeId } = await this.send('DOM.querySelector', { nodeId: root.nodeId, selector });
    await this.send('DOM.setFileInputFiles', { nodeId, files });
  }

  async close() { await this.browser.send('Target.closeTarget', { targetId: this.targetId }); }
}

export async function waitForDownload(dir, name, timeout = 10000) {
  const end = Date.now() + timeout;
  let lastSize = -1;
  while (Date.now() < end) {
    const files = existsSync(dir) ? readdirSync(dir) : [];
    if (files.includes(name) && !files.some((f) => f.endsWith('.crdownload'))) {
      // Wait until the file is non-empty and its size is stable across two polls.
      const size = statSync(`${dir}/${name}`).size;
      if (size > 0 && size === lastSize) return `${dir}/${name}`;
      lastSize = size;
    }
    await sleep(100);
  }
  throw new Error(`download not found: ${name} in ${dir}`);
}

export { sleep };
