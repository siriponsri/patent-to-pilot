// Lossless JSON for provenance work.
//
// JSON.parse turns `1.0` into `1`, which changes the Python canonical hash
// (`json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`)
// that the backend uses as the source payload hash. This module keeps number
// lexemes, reproduces Python's canonical form and hashes it with SHA-256.

export class PyNum {
  constructor(raw) {
    this.raw = raw;
    this.isFloat = /[.eE]/.test(raw);
  }
  valueOf() { return Number(this.raw); }
}

export class LosslessParseError extends Error {
  constructor(message, offset) {
    super(`${message} at offset ${offset}`);
    this.code = 'json_parse';
    this.offset = offset;
  }
}

/** Parse JSON text into a tree whose numbers are PyNum and objects are null-prototype. */
export function parseLossless(text) {
  let i = 0;
  const ws = () => { while (i < text.length && ' \t\n\r'.includes(text[i])) i++; };
  const fail = (msg) => { throw new LosslessParseError(msg, i); };
  function value() {
    ws();
    const c = text[i];
    if (c === '{') return object();
    if (c === '[') return array();
    if (c === '"') return string();
    if (c === 't' && text.startsWith('true', i)) { i += 4; return true; }
    if (c === 'f' && text.startsWith('false', i)) { i += 5; return false; }
    if (c === 'n' && text.startsWith('null', i)) { i += 4; return null; }
    if (c === '-' || (c >= '0' && c <= '9')) return number();
    return fail('unexpected token');
  }
  function object() {
    i++;
    const out = Object.create(null);
    ws();
    if (text[i] === '}') { i++; return out; }
    for (;;) {
      ws();
      if (text[i] !== '"') fail('expected object key');
      const key = string();
      // Duplicate keys are ambiguous for provenance; refuse rather than pick one.
      if (Object.prototype.hasOwnProperty.call(out, key)) fail(`duplicate key ${JSON.stringify(key)}`);
      ws();
      if (text[i] !== ':') fail('expected colon');
      i++;
      out[key] = value();
      ws();
      if (text[i] === ',') { i++; continue; }
      if (text[i] === '}') { i++; return out; }
      fail('expected comma or closing brace');
    }
  }
  function array() {
    i++;
    const out = [];
    ws();
    if (text[i] === ']') { i++; return out; }
    for (;;) {
      out.push(value());
      ws();
      if (text[i] === ',') { i++; continue; }
      if (text[i] === ']') { i++; return out; }
      fail('expected comma or closing bracket');
    }
  }
  function string() {
    const start = i;
    i++;
    while (i < text.length) {
      const c = text[i];
      if (c === '"') { i++; return JSON.parse(text.slice(start, i)); }
      if (c === '\\') { i += 2; continue; }
      if (c < ' ') fail('control character in string');
      i++;
    }
    return fail('unterminated string');
  }
  function number() {
    const m = /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(text.slice(i));
    if (!m) fail('bad number');
    i += m[0].length;
    return new PyNum(m[0]);
  }
  const result = value();
  ws();
  if (i !== text.length) fail('trailing data');
  return result;
}

/** Python repr() of a float, given as a JS number. */
export function pyFloatRepr(x) {
  if (!Number.isFinite(x)) throw new Error('NaN/Infinity are not allowed (allow_nan=False)');
  if (x === 0) return Object.is(x, -0) ? '-0.0' : '0.0';
  const sign = x < 0 ? '-' : '';
  // toExponential() with no argument yields the shortest round-trip digits.
  const [mant, expStr] = Math.abs(x).toExponential().split('e');
  const digits = mant.replace('.', '');
  const exp = Number(expStr);
  if (exp < -4 || exp >= 16) {
    const frac = digits.slice(1);
    const e = Math.abs(exp) < 10 ? `0${Math.abs(exp)}` : String(Math.abs(exp));
    return `${sign}${digits[0]}${frac ? '.' + frac : ''}e${exp < 0 ? '-' : '+'}${e}`;
  }
  if (exp < 0) return `${sign}0.${'0'.repeat(-exp - 1)}${digits}`;
  const intPart = digits.slice(0, exp + 1).padEnd(exp + 1, '0');
  const fracPart = digits.slice(exp + 1);
  return `${sign}${intPart}.${fracPart || '0'}`;
}

function pyIntRepr(raw) {
  const neg = raw.startsWith('-');
  const body = neg ? raw.slice(1) : raw;
  return body === '0' ? '0' : (neg ? '-' : '') + body;
}

/** Python sorts dict keys by code point; JS sort compares UTF-16 units. */
export function codePointCompare(a, b) {
  const A = Array.from(a, (ch) => ch.codePointAt(0));
  const B = Array.from(b, (ch) => ch.codePointAt(0));
  for (let k = 0; k < Math.min(A.length, B.length); k++) if (A[k] !== B[k]) return A[k] - B[k];
  return A.length - B.length;
}

/** Python `json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)`. */
export function canonicalDumps(v) {
  if (v === null) return 'null';
  if (v === true) return 'true';
  if (v === false) return 'false';
  if (v instanceof PyNum) return v.isFloat ? pyFloatRepr(Number(v.raw)) : pyIntRepr(v.raw);
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : pyFloatRepr(v);
  if (typeof v === 'string') return JSON.stringify(v);
  if (Array.isArray(v)) return `[${v.map(canonicalDumps).join(',')}]`;
  if (typeof v === 'object') {
    const keys = Object.keys(v).sort(codePointCompare);
    return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalDumps(v[k])}`).join(',')}}`;
  }
  throw new Error(`unsupported value type ${typeof v}`);
}

/** Pretty serialization that preserves number lexemes and key order (for lossless export). */
export function stringifyLossless(v, indent = 2, depth = 0) {
  const pad = ' '.repeat(indent * (depth + 1));
  const end = ' '.repeat(indent * depth);
  if (v instanceof PyNum) return v.raw;
  if (v === null || typeof v !== 'object') return JSON.stringify(v);
  if (Array.isArray(v)) {
    if (!v.length) return '[]';
    return `[\n${v.map((x) => pad + stringifyLossless(x, indent, depth + 1)).join(',\n')}\n${end}]`;
  }
  const keys = Object.keys(v);
  if (!keys.length) return '{}';
  return `{\n${keys.map((k) => `${pad}${JSON.stringify(k)}: ${stringifyLossless(v[k], indent, depth + 1)}`).join(',\n')}\n${end}}`;
}

/** Convert a lossless tree into ordinary JS values for display. */
export function toPlain(v) {
  if (v instanceof PyNum) return Number(v.raw);
  if (Array.isArray(v)) return v.map(toPlain);
  if (v && typeof v === 'object') {
    const out = {};
    for (const k of Object.keys(v)) Object.defineProperty(out, k, { value: toPlain(v[k]), enumerable: true, writable: true, configurable: true });
    return out;
  }
  return v;
}

export async function sha256Hex(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('');
}

/** Backend `content_hash`. */
export function contentHash(v) {
  return sha256Hex(canonicalDumps(v));
}

export function isObj(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v) && !(v instanceof PyNum);
}
