// Pipeline graph shown on the canvas. Each node is driven by work that really
// happens: a validation stage (validate.js DOSSIER_STAGES), the imported run
// receipt, the user's own edits, or an exporter. The AI agent node is a future
// seam and is always `unavailable` in this build.

export const NODE_STATES = ['idle', 'running', 'pass', 'fail', 'warn', 'skipped', 'ready', 'unavailable'];

// kind: input | check | receipt | human | output | agent. x/y are canvas units.
// Compact zigzag: checks run left→right, evidence work right→left, human work left→right below.
export const NODES = [
  { id: 'input', kind: 'input', view: 'sources', x: 40, y: 40, icon: '⇣' },
  { id: 'schema', kind: 'check', view: 'checks', stage: 'schema', x: 270, y: 40, icon: '{}' },
  { id: 'query', kind: 'check', view: 'checks', stage: 'query', x: 500, y: 40, icon: '◎' },
  { id: 'sources', kind: 'check', view: 'sources', stage: 'sources', x: 730, y: 40, icon: '#' },
  { id: 'evidence', kind: 'check', view: 'evidence', stage: 'evidence', x: 730, y: 200, icon: '❝' },
  { id: 'candidates', kind: 'check', view: 'evidence', tab: 'candidates', stage: 'candidates', x: 500, y: 200, icon: '⚖' },
  { id: 'agent', kind: 'agent', view: 'agent', x: 960, y: 200, icon: '✦' },
  { id: 'run', kind: 'receipt', view: 'runs', x: 270, y: 200, icon: '⟳' },
  { id: 'review', kind: 'human', view: 'overview', x: 500, y: 360, icon: '✎' },
  { id: 'requests', kind: 'human', view: 'requests', x: 270, y: 360, icon: '?' },
  { id: 'history', kind: 'human', view: 'history', x: 730, y: 360, icon: '◷' },
  { id: 'export', kind: 'output', view: 'export', x: 40, y: 360, icon: '⇡' },
];

export const EDGES = [
  ['input', 'schema'], ['schema', 'query'], ['query', 'sources'], ['sources', 'evidence'], ['evidence', 'candidates'],
  ['agent', 'evidence', 'future'], ['run', 'candidates'], ['candidates', 'review'], ['review', 'requests'],
  ['review', 'history'], ['requests', 'export'],
];

export const STAGE_TO_NODE = Object.fromEntries(NODES.filter((n) => n.stage).map((n) => [n.stage, n.id]));

/** Which node a route view highlights. */
export function nodeForView(view, tab) {
  if (view === 'source') return 'evidence';
  if (view === 'evidence' && tab === 'candidates') return 'candidates';
  return (NODES.find((n) => n.view === view && !n.tab) || NODES.find((n) => n.view === view))?.id || null;
}

/** Initial states before any run: checks idle, agent unavailable, human/output ready. */
export function initialStates() {
  return Object.fromEntries(NODES.map((n) => [n.id, n.kind === 'agent' ? 'unavailable' : n.kind === 'check' || n.kind === 'input' || n.kind === 'receipt' ? 'idle' : 'ready']));
}

/** Map a validation stage event to the node state it implies. */
export function stateForStageEvent(ev) {
  if (ev.phase === 'start') return 'running';
  if (ev.phase === 'skipped') return 'skipped';
  return ev.errors.length ? 'fail' : 'pass';
}
