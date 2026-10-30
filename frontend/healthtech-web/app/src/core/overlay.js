// User overlay: notes, local feature links and request drafts. It lives beside
// the immutable dossier and never rewrites source facts or relationship status.

export const MARKERS = ['none', 'needs_clarification', 'reviewed_by_user'];
export const PRIORITIES = ['normal', 'high'];
export const REQUEST_STATUS = ['draft', 'done_by_user'];

export function emptyOverlay() {
  return { notes: [], featureLinks: [], requestDrafts: [] };
}

export function cloneOverlay(o) {
  return JSON.parse(JSON.stringify(o || emptyOverlay()));
}

export function newId(prefix) {
  const rand = globalThis.crypto.getRandomValues(new Uint32Array(2));
  return `${prefix}-${Date.now().toString(36)}-${rand[0].toString(36)}${rand[1].toString(36)}`;
}

const str = (v) => typeof v === 'string';
const strList = (v) => Array.isArray(v) && v.every(str);

/** Validate an overlay read from storage or a recovery file. Returns error strings. */
export function overlayErrors(o) {
  const errors = [];
  if (!o || typeof o !== 'object' || Array.isArray(o)) return ['overlay must be an object'];
  const allowed = new Set(['notes', 'featureLinks', 'requestDrafts', 'draft']);
  for (const k of Object.keys(o)) if (!allowed.has(k)) errors.push(`unexpected overlay field ${k}`);
  if (!Array.isArray(o.notes) || !Array.isArray(o.featureLinks) || !Array.isArray(o.requestDrafts)) return [...errors, 'overlay lists missing'];
  const ids = new Set();
  o.notes.forEach((n, i) => {
    if (!str(n.noteId) || !str(n.targetRef) || !str(n.text)) errors.push(`notes[${i}] needs noteId/targetRef/text`);
    if (n.basis !== 'user_note') errors.push(`notes[${i}].basis must be user_note`);
    if (!MARKERS.includes(n.reviewMarker)) errors.push(`notes[${i}].reviewMarker invalid`);
    if (ids.has(n.noteId)) errors.push(`duplicate note ${n.noteId}`);
    ids.add(n.noteId);
  });
  o.featureLinks.forEach((f, i) => {
    if (!str(f.feature) || !strList(f.evidenceIds) || f.basis !== 'user_authored') errors.push(`featureLinks[${i}] invalid`);
  });
  o.requestDrafts.forEach((r, i) => {
    if (!str(r.requestId) || !str(r.question) || !strList(r.evidenceRefs)) errors.push(`requestDrafts[${i}] needs requestId/question/evidenceRefs`);
    if (!PRIORITIES.includes(r.priority) || !REQUEST_STATUS.includes(r.status)) errors.push(`requestDrafts[${i}] priority/status invalid`);
    if (r.intendedRole !== undefined && r.intendedRole !== null && !str(r.intendedRole)) errors.push(`requestDrafts[${i}].intendedRole invalid`);
  });
  return errors;
}

function keyed(o) {
  const m = new Map();
  for (const n of o.notes) m.set(`note:${n.noteId}`, n);
  for (const f of o.featureLinks) m.set(`featureLink:${f.feature}`, f);
  for (const r of o.requestDrafts) m.set(`request:${r.requestId}`, r);
  if (o.draft) m.set('draft', o.draft);
  return m;
}

/** Keys whose values differ between two overlays (added, removed or changed). */
export function overlayDiff(a, b) {
  const A = keyed(a || emptyOverlay());
  const B = keyed(b || emptyOverlay());
  const keys = new Set([...A.keys(), ...B.keys()]);
  return [...keys].filter((k) => JSON.stringify(A.get(k)) !== JSON.stringify(B.get(k))).sort();
}

/**
 * Reapply "yours" (changes relative to base) onto "theirs". When both sides
 * changed the same item, both survive: theirs keeps its ID and yours is added
 * as a new item that cites the original. Nothing is silently dropped.
 */
export function reapply(base, theirs, yours) {
  const out = cloneOverlay(theirs);
  const theirsChanged = new Set(overlayDiff(base, theirs));
  const Y = keyed(yours), T = keyed(theirs);
  const kept = [];
  for (const key of overlayDiff(base, yours)) {
    const mine = Y.get(key);
    const [kind] = key.split(':');
    const both = theirsChanged.has(key) && JSON.stringify(T.get(key)) !== JSON.stringify(mine);
    if (kind === 'note') {
      if (!mine) { if (!both) out.notes = out.notes.filter((n) => `note:${n.noteId}` !== key); continue; }
      if (both && T.get(key)) {
        out.notes.push({ ...mine, noteId: newId('note'), text: mine.text });
        kept.push(key);
      } else {
        const idx = out.notes.findIndex((n) => `note:${n.noteId}` === key);
        if (idx >= 0) out.notes[idx] = { ...mine }; else out.notes.push({ ...mine });
      }
    } else if (kind === 'request') {
      if (!mine) { if (!both) out.requestDrafts = out.requestDrafts.filter((r) => `request:${r.requestId}` !== key); continue; }
      if (both && T.get(key)) {
        out.requestDrafts.push({ ...mine, requestId: newId('request') });
        kept.push(key);
      } else {
        const idx = out.requestDrafts.findIndex((r) => `request:${r.requestId}` === key);
        if (idx >= 0) out.requestDrafts[idx] = { ...mine }; else out.requestDrafts.push({ ...mine });
      }
    } else if (kind === 'featureLink') {
      const t = out.featureLinks.find((f) => `featureLink:${f.feature}` === key);
      if (!mine) continue;
      if (t) t.evidenceIds = [...new Set([...t.evidenceIds, ...mine.evidenceIds])];
      else out.featureLinks.push({ ...mine });
    } else if (key === 'draft' && mine) {
      out.draft = both ? { ...T.get('draft'), ...mine } : mine;
    }
  }
  return { overlay: out, bothChanged: kept };
}

/** Text of every user-authored string, for "nothing lost" assertions. */
export function overlayTexts(o) {
  return [...o.notes.map((n) => n.text), ...o.requestDrafts.map((r) => r.question)];
}
