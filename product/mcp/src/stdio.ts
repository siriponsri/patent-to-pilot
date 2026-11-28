import { serveStdio, StdioServerTransport } from '@modelcontextprotocol/server/stdio';
import { INPUT_BYTES } from './registry.js';
import { createServer } from './server.js';

serveStdio(() => createServer(), {
  legacy: 'serve',
  transport: new StdioServerTransport(process.stdin, process.stdout, { maxBufferSize: INPUT_BYTES + 8192 }),
  onerror: () => { process.stderr.write('MWD MCP protocol error.\n'); },
});
