import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { openApi, placeholderOrigin } from './openapi.js';
import { registry } from './registry.js';

const pin = JSON.parse(readFileSync(new URL('../release-lock.json', import.meta.url), 'utf8'));
const catalogDigest = createHash('sha256').update(JSON.stringify(Object.values(registry))).digest('hex');
if (catalogDigest !== pin.catalog_sha256) throw new Error('Tool catalog differs from the release lock: ' + catalogDigest);
const origin = new URL(process.argv[2] ?? placeholderOrigin);
if (origin.protocol !== 'https:' || !origin.hostname.endsWith('.workers.dev') || origin.href !== origin.origin + '/') {
  throw new Error('Use the HTTPS Worker origin with no path.');
}
writeFileSync(new URL('./openapi.json', import.meta.url), JSON.stringify(openApi(origin.origin), null, 2) + '\n');
