import { METHOD_NOT_FOUND, ProtocolError, Server } from '@modelcontextprotocol/server';
import { isName, LEGACY, names, PROTOCOL, registry } from './registry.js';
import { reader, wire, type Observation } from './read.js';
import { release, type Release } from './release.js';

export function createServer(data: Release = release, observe?: (observation: Observation) => void) {
  const server = new Server({ name: 'Market Window Dossier', version: '1.0.0' }, {
    capabilities: { tools: {} }, supportedProtocolVersions: [PROTOCOL, LEGACY],
  });
  const read = reader(data, observe);
  server.setRequestHandler('tools/list', () => ({ tools: names.map(name => registry[name]) }));
  server.setRequestHandler('tools/call', async ({ params }) => {
    if (!isName(params.name)) throw new ProtocolError(METHOD_NOT_FOUND, 'Unknown tool');
    return wire(await read(params.name, params.arguments ?? {}));
  });
  return server;
}
