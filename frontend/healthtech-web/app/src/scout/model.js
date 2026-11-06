// Solution Scout view model: pure functions, no DOM and no network.

export const SECTIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
export const IPC3 = /^[A-H][0-9]{2}$/;

export const SCOUT_DICT = {
  en: {
    'scout.name': 'Solution Scout',
    'scout.tagline': 'Describe a technical problem. See which patents from other industries already solve it.',
    'scout.brief.label': 'Your problem',
    'scout.brief.placeholder': 'e.g. A pump seal leaks after long periods of strong vibration. We need steady contact pressure without a heavy spring or power…',
    'scout.own.label': 'Your field (IPC classes)',
    'scout.own.add': 'Add class, e.g. F16',
    'scout.own.remove': 'Remove {code}',
    'scout.own.invalid': 'Use an IPC class such as F16 or A61.',
    'scout.demo.label': 'Try a recorded example',
    'scout.split.label': 'Shortlist',
    'scout.search': 'Scout',
    'scout.searching': 'Encoding your brief and searching {n} documents…',
    'scout.need': 'Write at least a sentence and add one class of your own field.',
    'scout.lane.own': 'Your field',
    'scout.lane.other': 'Other industries',
    'scout.lane.own.help': 'Shares at least one IPC class with you',
    'scout.lane.other.help': 'Shares no IPC class with you',
    'scout.map.title': 'Where the other-industry results come from',
    'scout.map.note': 'Descriptive only. The map does not change the ranking.',
    'scout.map.you': 'You',
    'scout.card.idea': 'Transfer idea',
    'scout.card.open': 'Open {title}',
    'scout.card.score': 'Similarity',
    'scout.drawer.close': 'Close',
    'scout.drawer.mechanism': 'What might transfer',
    'scout.drawer.what': 'What it does',
    'scout.drawer.quotes': 'Evidence quotes',
    'scout.drawer.source': 'Source text',
    'scout.drawer.loading': 'Loading…',
    'scout.drawer.noIdea': 'No recorded transfer idea for this document. Live LLM rationales need the GPU mode.',
    'scout.quote.matched': 'Found in source',
    'scout.quote.not_found': 'Not found in source',
    'scout.quote.too_short': 'Too short to check',
    'scout.quote.too_long': 'Too long to check',
    'scout.quote.label': 'A literal match is not semantic support. Read the source.',
    'scout.basis': 'System inference by {model}, not a source fact.',
    'scout.decision.accept': 'Useful',
    'scout.decision.reject': 'Not useful',
    'scout.decision.saved': 'Saved: {decision}',
    'scout.receipt.mode': 'Mode',
    'scout.receipt.encode': 'Encode',
    'scout.receipt.search': 'Search',
    'scout.receipt.corpus': 'Corpus',
    'scout.receipt.encoder': 'Encoder',
    'scout.receipt.paid': 'Paid calls',
    'scout.receipt.ideas': 'Ideas',
    'scout.about': 'Research prototype. Corpus: {source} ({licence}), personal names removed. Encoder: PatEmbed-large ({encoderLicence}) — research use only. No relevance judgement is made; unjudged results are not negatives. Not a novelty, validity, infringement or freedom-to-operate opinion.',
    'scout.error.backend': 'The local Scout service is not reachable at {url}. Start it with serve_http.py and reload.',
    'scout.error.generic': 'Something went wrong: {message}',
    'scout.empty': 'No results in this lane.',
    'scout.lang': 'ภาษาไทย',
    'scout.section.A': 'Human necessities', 'scout.section.B': 'Operations & transport', 'scout.section.C': 'Chemistry & metallurgy',
    'scout.section.D': 'Textiles & paper', 'scout.section.E': 'Fixed constructions', 'scout.section.F': 'Mechanical engineering',
    'scout.section.G': 'Physics', 'scout.section.H': 'Electricity',
  },
  th: {
    'scout.name': 'Solution Scout',
    'scout.tagline': 'เล่าปัญหาทางเทคนิคของคุณ แล้วดูว่าสิทธิบัตรจากอุตสาหกรรมไหนเคยแก้ปัญหาแบบนี้มาแล้ว',
    'scout.brief.label': 'ปัญหาของคุณ',
    'scout.brief.placeholder': 'เช่น ซีลปั๊มรั่วหลังสั่นแรงเป็นเวลานาน ต้องการรักษาแรงกดหน้าสัมผัสให้คงที่โดยไม่ใช้สปริงหนักหรือไฟฟ้า…',
    'scout.own.label': 'สาขาของคุณ (คลาส IPC)',
    'scout.own.add': 'เพิ่มคลาส เช่น F16',
    'scout.own.remove': 'ลบ {code}',
    'scout.own.invalid': 'ใช้คลาส IPC เช่น F16 หรือ A61',
    'scout.demo.label': 'ลองตัวอย่างที่บันทึกไว้',
    'scout.split.label': 'รายการสั้น',
    'scout.search': 'ค้นหา',
    'scout.searching': 'กำลังแปลงโจทย์เป็นเวกเตอร์และค้นในเอกสาร {n} รายการ…',
    'scout.need': 'เขียนโจทย์อย่างน้อยหนึ่งประโยค และเพิ่มคลาสของสาขาคุณอย่างน้อยหนึ่งคลาส',
    'scout.lane.own': 'สาขาของคุณ',
    'scout.lane.other': 'อุตสาหกรรมอื่น',
    'scout.lane.own.help': 'มีคลาส IPC ร่วมกับคุณอย่างน้อยหนึ่งคลาส',
    'scout.lane.other.help': 'ไม่มีคลาส IPC ร่วมกับคุณเลย',
    'scout.map.title': 'ผลจากอุตสาหกรรมอื่นมาจากสาขาไหน',
    'scout.map.note': 'แสดงภาพรวมเท่านั้น แผนที่นี้ไม่ได้เปลี่ยนลำดับผลค้น',
    'scout.map.you': 'คุณ',
    'scout.card.idea': 'แนวคิดที่นำไปใช้ได้',
    'scout.card.open': 'เปิด {title}',
    'scout.card.score': 'ความคล้าย',
    'scout.drawer.close': 'ปิด',
    'scout.drawer.mechanism': 'สิ่งที่อาจนำมาใช้ได้',
    'scout.drawer.what': 'สิ่งที่สิทธิบัตรนี้ทำ',
    'scout.drawer.quotes': 'ข้อความอ้างอิง',
    'scout.drawer.source': 'ข้อความต้นฉบับ',
    'scout.drawer.loading': 'กำลังโหลด…',
    'scout.drawer.noIdea': 'ยังไม่มีแนวคิดที่บันทึกไว้สำหรับเอกสารนี้ การให้ LLM เขียนสดต้องใช้โหมด GPU',
    'scout.quote.matched': 'พบในต้นฉบับ',
    'scout.quote.not_found': 'ไม่พบในต้นฉบับ',
    'scout.quote.too_short': 'สั้นเกินกว่าจะตรวจ',
    'scout.quote.too_long': 'ยาวเกินกว่าจะตรวจ',
    'scout.quote.label': 'ข้อความตรงกันตามตัวอักษรไม่ได้แปลว่าเนื้อหาสนับสนุน โปรดอ่านต้นฉบับ',
    'scout.basis': 'เป็นการอนุมานของระบบ ({model}) ไม่ใช่ข้อเท็จจริงจากต้นฉบับ',
    'scout.decision.accept': 'มีประโยชน์',
    'scout.decision.reject': 'ไม่มีประโยชน์',
    'scout.decision.saved': 'บันทึกแล้ว: {decision}',
    'scout.receipt.mode': 'โหมด',
    'scout.receipt.encode': 'แปลงเวกเตอร์',
    'scout.receipt.search': 'ค้นหา',
    'scout.receipt.corpus': 'ฐานข้อมูล',
    'scout.receipt.encoder': 'ตัวเข้ารหัส',
    'scout.receipt.paid': 'การเรียกแบบเสียเงิน',
    'scout.receipt.ideas': 'แนวคิด',
    'scout.about': 'ต้นแบบเพื่อการวิจัย ฐานข้อมูล: {source} ({licence}) ตัดชื่อบุคคลออกแล้ว ตัวเข้ารหัส: PatEmbed-large ({encoderLicence}) ใช้เพื่อการวิจัยเท่านั้น ระบบไม่ได้ตัดสินความเกี่ยวข้อง ผลที่ยังไม่ได้ประเมินไม่ใช่ผลลบ และไม่ใช่ความเห็นเรื่องความใหม่ ความสมบูรณ์ การละเมิด หรือเสรีภาพในการดำเนินการ',
    'scout.error.backend': 'เชื่อมต่อบริการ Scout ในเครื่องที่ {url} ไม่ได้ เปิดด้วย serve_http.py แล้วโหลดหน้าใหม่',
    'scout.error.generic': 'เกิดข้อผิดพลาด: {message}',
    'scout.empty': 'ไม่มีผลในเลนนี้',
    'scout.lang': 'English',
    'scout.section.A': 'ความจำเป็นของมนุษย์', 'scout.section.B': 'การดำเนินการและการขนส่ง', 'scout.section.C': 'เคมีและโลหะวิทยา',
    'scout.section.D': 'สิ่งทอและกระดาษ', 'scout.section.E': 'สิ่งก่อสร้างถาวร', 'scout.section.F': 'วิศวกรรมเครื่องกล',
    'scout.section.G': 'ฟิสิกส์', 'scout.section.H': 'ไฟฟ้า',
  },
};

export function translator(lang) {
  const table = SCOUT_DICT[lang] || SCOUT_DICT.en;
  return (key, vars = {}) => String(table[key] ?? SCOUT_DICT.en[key] ?? key)
    .replace(/\{(\w+)\}/g, (_, name) => (vars[name] ?? `{${name}}`));
}

/** Normalise a typed IPC class ('f16 ' -> 'F16'); null when it is not an IPC3 code. */
export function parseIpc3(value) {
  const code = String(value || '').trim().toUpperCase();
  return IPC3.test(code) ? code : null;
}

/** Display title: HUPD titles are upper-case; show sentence case and keep the raw title in the source view. */
export function displayTitle(title) {
  const text = String(title || '').trim();
  if (!text || text !== text.toUpperCase()) return text;
  const lower = text.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** Section of a candidate for the field map: the first IPC section it carries, '?' when it has none. */
export function primarySection(candidate) {
  const codes = (candidate.ipc3 || []).filter((c) => IPC3.test(c)).sort();
  return codes.length ? codes[0][0] : '?';
}

/** Field map: other-field candidates grouped by section, in A–H order, with each group's ranks. */
export function fieldMap(candidates) {
  const groups = Object.fromEntries([...SECTIONS, '?'].map((s) => [s, []]));
  for (const c of candidates) if (c.lane === 'other_fields') groups[primarySection(c)].push(c);
  return [...SECTIONS, '?'].map((section) => ({ section, items: groups[section] })).filter((g) => g.items.length || g.section !== '?');
}

/** Ring layout for the field map: point i of n on a circle, starting at the top, clockwise. */
export function ringPoint(i, n, cx, cy, r) {
  const angle = -Math.PI / 2 + (2 * Math.PI * i) / n;
  return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), angle };
}

/**
 * Split source text into plain and highlighted segments for matched quotes. Offsets come from the
 * server's literal check; overlapping ranges are merged; anything out of range is ignored.
 */
export function quoteSegments(text, quotes) {
  const ranges = (quotes || [])
    .map((q, index) => ({ start: q.start, end: q.end, index }))
    .filter((r) => Number.isInteger(r.start) && Number.isInteger(r.end) && r.start >= 0 && r.end <= text.length && r.end > r.start)
    .sort((a, b) => a.start - b.start);
  const merged = [];
  for (const r of ranges) {
    const last = merged[merged.length - 1];
    if (last && r.start <= last.end) { last.end = Math.max(last.end, r.end); last.indexes.push(r.index); }
    else merged.push({ start: r.start, end: r.end, indexes: [r.index] });
  }
  const out = [];
  let at = 0;
  for (const r of merged) {
    if (r.start > at) out.push({ text: text.slice(at, r.start), mark: false });
    out.push({ text: text.slice(r.start, r.end), mark: true, quotes: r.indexes });
    at = r.end;
  }
  if (at < text.length) out.push({ text: text.slice(at), mark: false });
  return out;
}

export const SPLITS = [
  { key: '10+10', n_own: 10, n_other: 10 },
  { key: '5+15', n_own: 5, n_other: 15 },
  { key: '0+20', n_own: 0, n_other: 20 },
];

export function formatMs(ms) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${Math.round(ms)} ms`;
}

/** A stable idempotency key for one brief + split, so a double click never creates two sessions. */
export async function requestKey(brief, split, digest = globalThis.crypto?.subtle) {
  const payload = JSON.stringify({ t: brief.text, o: brief.own_ipc3, s: split });
  if (!digest) return `scout-${payload.length}-${Date.now()}`;
  const bytes = new Uint8Array(await digest.digest('SHA-256', new TextEncoder().encode(payload)));
  return `scout-${Array.from(bytes.slice(0, 12), (b) => b.toString(16).padStart(2, '0')).join('')}`;
}
