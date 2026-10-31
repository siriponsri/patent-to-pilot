// Local static server for the HealthTech web frontend. Zero dependencies.
// Binds to 127.0.0.1 only, serves an explicit file allowlist, and sets a CSP
// that forbids inline/remote scripts while permitting the explicitly loopback
// HTTP job adapter used by the local research workflow.
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { dirname, extname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const APP = resolve(here, 'app');
const REPO = resolve(here, '../..');
// Read-only mappings to authored repository files (no copies, so no drift).
const MAPPED = {
  '/fixtures/ui-fixtures.json': join(REPO, 'docs/healthtech/ux/fixtures/ui-fixtures.json'),
  '/schemas/DossierVersion.schema.json': join(REPO, 'schemas/healthtech/DossierVersion.schema.json'),
  '/schemas/RunManifest.schema.json': join(REPO, 'schemas/healthtech/RunManifest.schema.json'),
  '/schemas/AcquisitionEvent.schema.json': join(REPO, 'schemas/healthtech/AcquisitionEvent.schema.json'),
};
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.vtt': 'text/vtt', '.mp4': 'video/mp4', '.jpg': 'image/jpeg', '.png': 'image/png' };
const HEADERS = {
  'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; media-src 'self'; connect-src 'self' http://127.0.0.1:* http://localhost:* http://[::1]:*; font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'Cache-Control': 'no-store',
};

export function resolvePath(urlPath) {
  const path = decodeURIComponent(urlPath.split('?')[0]);
  if (MAPPED[path]) return MAPPED[path];
  const rel = path === '/' ? 'index.html' : path.replace(/^\/+/, '');
  const full = normalize(join(APP, rel));
  if (!full.startsWith(APP + sep) || !TYPES[extname(full)]) return null;
  return full;
}

export function startServer(port = Number(process.env.PORT || 5178), host = '127.0.0.1') {
  const server = createServer(async (req, res) => {
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405, HEADERS).end(); return; }
    let file;
    try { file = resolvePath(req.url); } catch { file = null; }
    if (!file) { res.writeHead(404, HEADERS).end('Not found'); return; }
    try {
      const info = await stat(file);
      if (!info.isFile()) throw new Error('not a file');
      const type = TYPES[extname(file)];
      const textual = /^(text|application\/json)/.test(type);
      const headers = { ...HEADERS, 'Content-Type': textual ? `${type}; charset=utf-8` : type, 'Accept-Ranges': 'bytes' };
      // Byte ranges let the video player seek to a chapter.
      const range = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
      if (range && (range[1] || range[2])) {
        const size = info.size;
        const start = range[1] ? Number(range[1]) : Math.max(0, size - Number(range[2]));
        const end = range[1] && range[2] ? Math.min(Number(range[2]), size - 1) : size - 1;
        if (start >= size || start > end) { res.writeHead(416, { ...headers, 'Content-Range': `bytes */${size}` }).end(); return; }
        res.writeHead(206, { ...headers, 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': String(end - start + 1) });
        if (req.method === 'HEAD') { res.end(); return; }
        createReadStream(file, { start, end }).pipe(res);
        return;
      }
      const body = await readFile(file);
      res.writeHead(200, { ...headers, 'Content-Length': String(body.length) });
      res.end(req.method === 'HEAD' ? undefined : body);
    } catch {
      res.writeHead(404, HEADERS).end('Not found');
    }
  });
  return new Promise((ok) => server.listen(port, host, () => ok(server)));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const server = await startServer();
  const { port } = server.address();
  console.log(`HealthTech web (local only): http://127.0.0.1:${port}/`);
}
