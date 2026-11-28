import { createMcpHandler } from 'agents/mcp/server';
import { createServer } from './server.js';
import { createRoutes } from './routes.js';
import { INPUT_BYTES } from './registry.js';
import { release } from './release.js';
import type { Observation } from './read.js';

const observe = (summary: Observation) => console.info(JSON.stringify(summary));
const mcp = createMcpHandler(() => createServer(release, observe), {
  route: '/mcp', corsOptions: false, allowedOriginHostnames: '*', legacy: 'stateless',
  maxRequestBodySize: INPUT_BYTES + 8192,
});
export default { fetch: createRoutes(request => mcp.fetch(request), release, observe) };
