// Locators follow backend provenance.check_evidence semantics:
// `chars:start:end` is a Python code-point slice; `field:a.b` is a dot path.
import { isObj } from './pyjson.js';

export function parseLocator(locator) {
  if (typeof locator !== 'string') return { kind: 'invalid', raw: locator };
  const chars = /^chars:(\d+):(\d+)$/.exec(locator);
  if (chars) return { kind: 'chars', start: Number(chars[1]), end: Number(chars[2]), raw: locator };
  if (locator.startsWith('field:') && locator.length > 6) return { kind: 'field', path: locator.slice(6).split('.'), raw: locator };
  return { kind: 'invalid', raw: locator };
}

/** Split text by code points: returns {before, span, after} or null when out of range. */
export function sliceCodePoints(text, start, end) {
  const cps = Array.from(text);
  if (!(start >= 0 && start < end && end <= cps.length)) return null;
  return { before: cps.slice(0, start).join(''), span: cps.slice(start, end).join(''), after: cps.slice(end).join(''), length: cps.length };
}

/** Resolve a dot path inside an object payload (lossless or plain); undefined when absent. */
export function resolveField(payload, path) {
  let value = payload;
  for (const part of path) {
    if (!isObj(value) || !Object.prototype.hasOwnProperty.call(value, part)) return { found: false };
    value = value[part];
  }
  return { found: true, value };
}
