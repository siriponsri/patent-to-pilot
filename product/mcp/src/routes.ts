import { INPUT_BYTES, isName } from './registry.js';
import { openApi, placeholderOrigin } from './openapi.js';
import { reader, type Observation } from './read.js';
import { release, sha256, type Release } from './release.js';

type RateLimit = { limit(options: { key: string }): Promise<{ success: boolean }> };
export type Env = { ALLOWED_ORIGINS?: string; PUBLIC_ORIGIN?: string; CALLER_LIMIT: RateLimit; LOCATION_LIMIT: RateLimit };
type McpHandler = (request: Request) => Promise<Response>;
type Observe = (observation: Observation) => void;

function problem(status: number, reason: string, headers?: HeadersInit) {
  return Response.json({ reason }, { status, headers });
}
class BodyError extends Error {
  constructor(readonly status: number, readonly reason: string) { super(reason); }
}
async function readJson(request: Request) {
  if (request.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') {
    throw new BodyError(415, 'JSON_REQUIRED');
  }
  if (Number(request.headers.get('content-length')) > INPUT_BYTES) throw new BodyError(413, 'INPUT_TOO_LARGE');
  const stream = request.body?.getReader();
  if (!stream) throw new BodyError(400, 'INVALID_JSON');
  const buffer = new Uint8Array(INPUT_BYTES);
  let offset = 0;
  try {
    for (;;) {
      const { value, done } = await stream.read();
      if (done) break;
      if (offset + value.length > buffer.length) {
        await stream.cancel();
        throw new BodyError(413, 'INPUT_TOO_LARGE');
      }
      buffer.set(value, offset);
      offset += value.length;
    }
    return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(buffer.subarray(0, offset))) as unknown;
  } catch (error) {
    if (error instanceof BodyError) throw error;
    throw new BodyError(400, 'INVALID_JSON');
  } finally {
    stream.releaseLock();
  }
}

export function createRoutes(mcp: McpHandler, data: Release = release, observe?: Observe) {
  const read = reader(data, observe);
  return async function route(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin');
    const publicOrigin = env.PUBLIC_ORIGIN || placeholderOrigin;
    const allowed = (env.ALLOWED_ORIGINS ?? '').split(',').map(item => item.trim()).filter(Boolean);
    if (origin !== null && origin !== publicOrigin && !allowed.includes(origin)) return problem(403, 'ORIGIN_REJECTED');

    const name = url.pathname.startsWith('/v1/') ? url.pathname.slice(4) : '';
    const isMcp = url.pathname === '/mcp';
    const isSpec = url.pathname === '/openapi.json';
    if (!isSpec && !isMcp && !isName(name)) return problem(404, 'ROUTE_NOT_FOUND');
    const method = isSpec ? 'GET' : 'POST';
    const respond = (response: Response) => {
      const headers = new Headers(response.headers);
      headers.set('Cache-Control', 'no-store');
      headers.append('Vary', 'Origin');
      if (origin !== null) {
        headers.set('Access-Control-Allow-Origin', origin);
        headers.set('Access-Control-Expose-Headers', 'Retry-After, MCP-Protocol-Version');
      }
      return new Response(response.body, { status: response.status, headers });
    };
    if (request.method === 'OPTIONS' && origin !== null) {
      return respond(new Response(null, { status: 204, headers: {
        'Access-Control-Allow-Methods': method,
        'Access-Control-Allow-Headers': 'Content-Type, Accept, MCP-Protocol-Version, Mcp-Method, Mcp-Name',
        'Access-Control-Max-Age': '600',
      } }));
    }
    if (request.method !== method) return respond(problem(405, 'METHOD_NOT_ALLOWED', { Allow: method }));
    if (url.search) return respond(problem(400, 'QUERY_STRING_UNSUPPORTED'));
    if (isMcp && Number(request.headers.get('content-length')) > INPUT_BYTES + 8192) {
      return respond(problem(413, 'INPUT_TOO_LARGE'));
    }
    try {
      const ip = request.headers.get('CF-Connecting-IP');
      // Use the Cloudflare-supplied address only to derive the transient rate key.
      const bucket = ip ? await sha256('mwd-limit-v1:' + Math.floor(Date.now() / 60000) + ':' + ip) : 'unidentified';
      const caller = await env.CALLER_LIMIT.limit({ key: bucket });
      if (!caller.success || !(await env.LOCATION_LIMIT.limit({ key: 'public-read' })).success) {
        return respond(problem(429, 'RATE_LIMITED', { 'Retry-After': '60' }));
      }
      if (isSpec) return respond(Response.json(openApi(publicOrigin)));
      if (isMcp) return respond(await mcp(request));
      if (!isName(name)) return respond(problem(404, 'ROUTE_NOT_FOUND'));
      return respond(Response.json(await read(name, await readJson(request))));
    } catch (error) {
      if (error instanceof BodyError) return respond(problem(error.status, error.reason));
      return respond(problem(503, 'UNAVAILABLE'));
    }
  };
}
