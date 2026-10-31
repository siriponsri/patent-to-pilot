import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createBackendAdapter, createBackendAdapterFromLocation, capabilities } from '../../app/src/adapters.js';

function response(value, status = 200, type = 'application/json') {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (name) => name.toLowerCase() === 'content-type' ? `${type}; charset=utf-8` : null },
    json: async () => value,
    text: async () => String(value),
  };
}

test('loopback backend adapter maps jobs, history, source and export routes', async () => {
  const calls = [];
  const fetchImpl = async (url, init) => {
    calls.push({ url: String(url), init });
    if (url.pathname === '/providers') return response({ providers: [{ id: 'local', available: true }] });
    if (url.pathname === '/jobs') return response({ job: { job_id: 'a'.repeat(32), state: 'queued' } }, 202);
    if (url.pathname.endsWith('/export')) return response('# exported', 200, 'text/markdown');
    if (url.pathname.endsWith('/generation')) return response({ generation: { status: 'PASS_TEST_GENERATION' } });
    return response({ job: { job_id: 'a'.repeat(32), state: 'succeeded' } });
  };
  const adapter = createBackendAdapter('http://127.0.0.1:8787', fetchImpl);
  const providers = await adapter.providers();
  assert.equal(providers.providers[0].id, 'local');
  await adapter.submit({ query_id: 'q' }, { idempotencyKey: 'case-1' });
  await adapter.status('a'.repeat(32));
  await adapter.history('a'.repeat(32));
  await adapter.result('a'.repeat(32));
  await adapter.source('a'.repeat(32), 'source-1', { version: 2, field: 'device_name' });
  assert.equal(await adapter.export('a'.repeat(32), { version: 2, format: 'markdown', language: 'th' }), '# exported');
  assert.equal((await adapter.generation('a'.repeat(32))).generation.status, 'PASS_TEST_GENERATION');
  assert.equal(calls[1].init.headers['Idempotency-Key'], 'case-1');
  assert.match(calls[5].url, /source\/source-1\?version=2&field=device_name/);
  assert.equal(capabilities('indexeddb', adapter).runStart.available, true);
  assert.equal(capabilities('indexeddb').runStart.available, false);
});

test('backend adapter rejects non-loopback URLs and exposes optional query wiring', () => {
  assert.throws(() => createBackendAdapter('https://example.invalid'), /loopback/);
  assert.equal(createBackendAdapterFromLocation({ search: '' }), null);
  const adapter = createBackendAdapterFromLocation({ search: '?backend=http%3A%2F%2F127.0.0.1%3A8787' }, async () => response({}));
  assert.equal(adapter.baseUrl, 'http://127.0.0.1:8787');
});
