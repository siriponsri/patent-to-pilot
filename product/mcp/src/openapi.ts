import { names, registry, INPUT_BYTES, RESULT_BYTES } from './registry.js';

export const placeholderOrigin = 'https://mwd-mcp.replace-with-owner-subdomain.workers.dev';

export function openApi(origin: string) {
  return {
    openapi: '3.1.0',
    info: { title: 'Market Window Dossier', version: '1.0.0',
      description: 'Read a pinned public evidence release for decision support and qualified FTO review.' },
    servers: [{ url: origin }],
    paths: Object.fromEntries(names.map(name => {
      const tool = registry[name];
      return ['/v1/' + name, { post: {
        operationId: name, description: tool.description,
        requestBody: { required: true, content: { 'application/json': { schema: { $ref: '#/components/schemas/' + name + '_input' } } } },
        responses: {
          '200': { description: 'Evidence page or typed application error. Check the error field.',
            content: { 'application/json': { schema: { $ref: '#/components/schemas/' + name + '_output' } } } },
          '400': { description: 'Malformed JSON' },
          '403': { description: 'Origin rejected' },
          '413': { description: 'Request body exceeds the transport limit' },
          '415': { description: 'Expected application/json' },
          '429': { description: 'Rate limit exceeded', headers: { 'Retry-After': { schema: { type: 'integer' } } } },
          '503': { description: 'Service unavailable' },
        },
      } }];
    })),
    components: { schemas: Object.fromEntries(names.flatMap(name => [
      [name + '_input', registry[name].inputSchema], [name + '_output', registry[name].outputSchema],
    ])) },
    'x-max-input-bytes': INPUT_BYTES,
    'x-max-result-bytes': RESULT_BYTES,
  };
}
