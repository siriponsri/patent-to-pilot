// Five-step user journey shown as a stepper. A step is "done" only from real
// state (a passed local check, a saved note, a request draft, a started export),
// never from merely visiting a screen.

export const JOURNEY = [
  { id: 'load', view: 'sources', views: ['sources'] },
  { id: 'verify', view: 'checks', views: ['checks', 'runs', 'agent'] },
  { id: 'review', view: 'evidence', views: ['overview', 'evidence', 'source', 'brief'] },
  { id: 'ask', view: 'requests', views: ['requests'] },
  { id: 'export', view: 'export', views: ['export', 'history'] },
];

export function stepDone(id, c) {
  switch (id) {
    case 'load': return Boolean(c.dossier);
    case 'verify': return c.pipe?.lastResult?.ok === true;
    case 'review': return c.overlay.notes.some((n) => n.text.trim()) || c.overlay.featureLinks.some((l) => l.evidenceIds.length > 0);
    case 'ask': return c.overlay.requestDrafts.some((r) => r.question.trim());
    case 'export': return Boolean(c.exportStarted);
    default: return false;
  }
}

/** Steps with done/current flags, the suggested next step and progress (0..1). */
export function journeyState(c, routeView) {
  const steps = JOURNEY.map((s) => ({ ...s, done: stepDone(s.id, c), current: s.views.includes(routeView) }));
  const doneCount = steps.filter((s) => s.done).length;
  const currentIndex = steps.findIndex((s) => s.current);
  const after = steps.slice(currentIndex + 1).find((s) => !s.done);
  const next = after || steps.find((s) => !s.done && !s.current) || null;
  return { steps, next, progress: doneCount / steps.length, doneCount };
}
