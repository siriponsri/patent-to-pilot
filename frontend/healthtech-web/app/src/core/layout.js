// Dockable workspace layout model (pure data). The canvas is fixed in the
// centre; panels live in the left/right/bottom zones (tabbed when several share
// a zone) or float as free windows. Stored per browser as a convenience only.

export const PANELS = ['library', 'inspector', 'timeline'];
export const ZONES = ['left', 'right', 'bottom'];
export const LIMITS = { left: [200, 640], right: [320, 1100], bottom: [120, 560] };
export const FLOAT_MIN = { w: 260, h: 160 };

export function defaultLayout() {
  return {
    version: 1,
    zones: {
      left: { panels: ['library'], active: 'library', size: 250 },
      right: { panels: ['inspector'], active: 'inspector', size: 460 },
      bottom: { panels: ['timeline'], active: 'timeline', size: 220 },
    },
    floating: {},
    collapsed: { left: false, right: false, bottom: false },
  };
}

const clamp = (v, [lo, hi]) => Math.min(hi, Math.max(lo, v));

/** Where a panel currently lives: a zone name or 'float'. */
export function locate(layout, panel) {
  if (layout.floating[panel]) return 'float';
  return ZONES.find((z) => layout.zones[z].panels.includes(panel)) || null;
}

function detach(l, panel) {
  for (const z of ZONES) {
    const zone = l.zones[z];
    zone.panels = zone.panels.filter((p) => p !== panel);
    if (zone.active === panel) zone.active = zone.panels[0] || null;
  }
  delete l.floating[panel];
}

/** Move a panel to a zone or to a floating window. Returns a new layout. */
export function movePanel(layout, panel, target, rect) {
  if (!PANELS.includes(panel)) throw new Error(`unknown panel ${panel}`);
  const l = structuredClone(layout);
  detach(l, panel);
  if (target === 'float') {
    l.floating[panel] = normalizeRect(rect || { x: 80, y: 80, w: 420, h: 320 });
  } else {
    if (!ZONES.includes(target)) throw new Error(`unknown zone ${target}`);
    l.zones[target].panels.push(panel);
    l.zones[target].active = panel;
    l.collapsed[target] = false;
  }
  return l;
}

export function resizeZone(layout, zone, size) {
  const l = structuredClone(layout);
  l.zones[zone].size = Math.round(clamp(size, LIMITS[zone]));
  return l;
}

export function setActive(layout, zone, panel) {
  const l = structuredClone(layout);
  if (l.zones[zone].panels.includes(panel)) l.zones[zone].active = panel;
  return l;
}

export function toggleCollapsed(layout, zone) {
  const l = structuredClone(layout);
  l.collapsed[zone] = !l.collapsed[zone];
  return l;
}

export function normalizeRect(r, viewport = { w: 1e5, h: 1e5 }) {
  const w = Math.max(FLOAT_MIN.w, Math.round(Number(r.w) || FLOAT_MIN.w));
  const h = Math.max(FLOAT_MIN.h, Math.round(Number(r.h) || FLOAT_MIN.h));
  // Keep at least the header reachable inside the viewport.
  const x = Math.min(Math.max(0, Math.round(Number(r.x) || 0)), Math.max(0, viewport.w - 120));
  const y = Math.min(Math.max(0, Math.round(Number(r.y) || 0)), Math.max(0, viewport.h - 48));
  return { x, y, w, h };
}

export function setFloatRect(layout, panel, rect, viewport) {
  const l = structuredClone(layout);
  if (l.floating[panel]) l.floating[panel] = normalizeRect(rect, viewport);
  return l;
}

/** Accept a stored layout only if it is complete and consistent; else the default. */
export function normalizeLayout(raw) {
  try {
    if (!raw || raw.version !== 1) return defaultLayout();
    const l = defaultLayout();
    const seen = new Set();
    for (const z of ZONES) {
      const zone = raw.zones?.[z];
      if (!zone || !Array.isArray(zone.panels)) return defaultLayout();
      const panels = zone.panels.filter((p) => PANELS.includes(p) && !seen.has(p));
      panels.forEach((p) => seen.add(p));
      l.zones[z] = { panels, active: panels.includes(zone.active) ? zone.active : panels[0] || null, size: Math.round(clamp(Number(zone.size) || defaultLayout().zones[z].size, LIMITS[z])) };
      l.collapsed[z] = Boolean(raw.collapsed?.[z]);
    }
    for (const [p, rect] of Object.entries(raw.floating || {})) {
      if (PANELS.includes(p) && !seen.has(p)) { l.floating[p] = normalizeRect(rect); seen.add(p); }
    }
    // Every panel must be somewhere; a missing one goes back to its default zone.
    for (const p of PANELS) if (!seen.has(p)) {
      const home = ZONES.find((z) => defaultLayout().zones[z].panels.includes(p));
      l.zones[home].panels.push(p);
      l.zones[home].active ||= p;
    }
    return l;
  } catch {
    return defaultLayout();
  }
}
