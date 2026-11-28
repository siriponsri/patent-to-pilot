import { performance } from 'node:perf_hooks';
import { isDeepStrictEqual } from 'node:util';
import bundle from './dist/generated/release.json' with { type: 'json' };
import { reader, wire } from './dist/read.js';
import { PROTOCOL } from './dist/registry.js';
import worker from './dist/worker.js';

const manifest = JSON.parse(bundle.manifest);
const release_id = manifest.release_id;
const host = 'mwd-mcp.benchmark.workers.dev';
const env = {
  PUBLIC_ORIGIN: 'https://' + host, ALLOWED_ORIGINS: '',
  CALLER_LIMIT: { limit: async () => ({ success: true }) },
  LOCATION_LIMIT: { limit: async () => ({ success: true }) },
};
const read = reader();
const largest = {};
let scanned = 0;
let oversized = 0;
for (const choice of manifest.choices) {
  const snapshot = { release_id, mode: choice.mode, as_of: choice.as_of, horizon: choice.horizon };
  const supports = JSON.parse(bundle.texts[choice.queue]).rows.filter(row => row.dossier !== null);
  for (const language of ['en', 'th']) {
    const base = { snapshot, limit: 25, language };
    for (const [name, args] of [
      ['get_queue', { ...base, scope: 'all' }], ['get_method_card', base],
      ...supports.flatMap(row => ['get_dossier', 'get_sources', 'get_fto_checklist'].map(name => [
        name, { ...base, molecule_key: row.key },
      ])),
    ]) {
      let cursor;
      do {
        const input = { ...args, ...(cursor ? { cursor } : {}) };
        const page = await read(name, input);
        scanned += 1;
        if (page.error) {
          if (page.error.reason === 'ROW_TOO_LARGE') { oversized += 1; break; }
          throw new Error(page.error.reason);
        }
        const bytes = Buffer.byteLength(JSON.stringify(wire(page)));
        if (bytes > (largest[language]?.bytes ?? 0)) largest[language] = { name, input, bytes, page };
        cursor = page.next_cursor;
      } while (cursor);
    }
  }
}

const originalInfo = console.info;
console.info = () => {};
try {
  for (const [language, { name, input, bytes, page }] of Object.entries(largest)) {
    const request = () => new Request('https://' + host + '/mcp', {
      method: 'POST', headers: {
        Host: host, 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream',
        'MCP-Protocol-Version': PROTOCOL, 'Mcp-Method': 'tools/call', 'Mcp-Name': name,
      },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: {
        name, arguments: input, _meta: {
          'io.modelcontextprotocol/protocolVersion': PROTOCOL,
          'io.modelcontextprotocol/clientInfo': { name: 'benchmark', version: '1' },
          'io.modelcontextprotocol/clientCapabilities': {},
        },
      } }),
    });
    async function measure() {
      const cpuStart = process.cpuUsage();
      const start = performance.now();
      const result = await worker.fetch(request(), env);
      const payload = await result.json();
      if (result.status !== 200 || payload.result?.isError || !payload.result) throw new Error('Worker benchmark read failed');
      const wireBytes = Buffer.byteLength(JSON.stringify(payload.result));
      if (wireBytes > 65536 || !isDeepStrictEqual(payload.result.structuredContent, page)) {
        throw new Error('Worker result differs from scan: ' + JSON.stringify({
          expectedBytes: bytes, wireBytes, fields: Object.keys(payload.result),
        }));
      }
      const cpu = process.cpuUsage(cpuStart);
      return { cpu_ms: (cpu.user + cpu.system) / 1000, wall_ms: performance.now() - start, wire_bytes: wireBytes };
    }
    const first = await measure();
    const samples = [];
    const batchStart = process.cpuUsage();
    for (let index = 0; index < 100; index += 1) samples.push(await measure());
    const batch = process.cpuUsage(batchStart);
    const cpuSamples = samples.map(sample => sample.cpu_ms).sort((a, b) => a - b);
    const wallSamples = samples.map(sample => sample.wall_ms).sort((a, b) => a - b);
    console.log(JSON.stringify({
      language, operation: name, snapshot: input.snapshot, molecule_key: input.molecule_key,
      continuation: Boolean(input.cursor), bytes, first,
      warm_cpu_ms: { mean: (batch.user + batch.system) / 100000, p95: cpuSamples[94], max: cpuSamples[99] },
      warm_wall_ms: { p50: wallSamples[49], p95: wallSamples[94], max: wallSamples[99] },
      pages_scanned: scanned, oversized_pages: oversized,
    }));
  }
} finally {
  console.info = originalInfo;
}
