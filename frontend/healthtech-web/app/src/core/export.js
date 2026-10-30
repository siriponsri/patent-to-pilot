// Frontend exporters. The backend export_markdown() omits user_edits (audit F4),
// so edited exports are rendered here, with an explicit exporter ID/version.
import { stringifyLossless, parseLossless, toPlain, isObj } from './pyjson.js';
import { validateDossier, validateRunArtifacts } from './validate.js';
import { overlayErrors } from './overlay.js';
import { translator } from './i18n.js';

export const MARKDOWN_EXPORTER = { id: 'healthtech-web-markdown', version: '1.0.0' };
export const RECOVERY_EXPORTER = { id: 'healthtech-web-recovery', version: '1.0.0' };
export const RECOVERY_FORMAT = 'p2p-healthtech-ux-recovery';

/** Inert Markdown text: HTML is escaped and link/image/code syntax is neutralised. */
export function mdText(value) {
  return String(value)
    .replace(/\\/g, '\\\\')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
    .replace(/([[\]`])/g, '\\$1');
}

export function mdCell(value) {
  return mdText(value).replace(/\|/g, '&#124;').replace(/\r?\n|\r/g, ' ');
}

const MODE_KEY = { synthetic_demo: 'mode.synthetic', imported_public: 'mode.public', simulation: 'mode.simulation' };

const H = {
  en: {
    title: 'HealthTech evidence dossier — edited export', field: 'Field', value: 'Value', device: 'Device (raw / canonical)',
    dossier: 'Dossier ID / backend version', snapshot: 'Local snapshot', ack: 'acknowledged save in this browser', unsaved: 'working copy — not yet saved',
    mode: 'Mode', cutoff: 'Evidence cutoff', jurisdiction: 'Jurisdiction', run: 'Run', hash: 'Dossier SHA-256 (canonical)', exporter: 'Exporter',
    exporterNote: 'frontend renderer; not the backend dossier.md exporter', evidence: 'Source evidence',
    evCols: ['Evidence ID', 'Statement', 'Kind / basis', 'Source / revision', 'Locator', 'Quote or field value', 'Integrity check'],
    candidates: 'Patent candidates', cCols: ['Raw ID', 'Canonical ID', 'Association status', 'Source / revision', 'Disclosure evidence', 'Named scores'],
    unresolved: 'Unresolved items', requests: 'Next information requests (from the dossier)', drafts: 'Local request drafts (user-authored)',
    rCols: ['Question', 'References', 'Intended role', 'Priority', 'Status'], links: 'Feature links (user-authored, not machine-verified)',
    imported: 'Edits stored inside the imported dossier (user_edits)', notes: 'User notes (user-authored; source facts unchanged)',
    about: 'about', marker: 'review marker', manifest: 'Source manifest', synthetic: 'synthetic', public: 'public', rights: 'rights note',
    scope: 'Export scope', included: 'Included', omitted: 'Omitted', none: 'None.',
    includedText: 'source facts with locators, candidates and status, unresolved items, dossier requests, local request drafts, feature links, imported user_edits and local user notes.',
    omittedText: 'full source payloads and run events (use the recovery JSON for a lossless copy).',
  },
  th: {
    title: 'แฟ้มหลักฐาน HealthTech — ฉบับส่งออกที่รวมข้อความที่แก้', field: 'รายการ', value: 'ค่า', device: 'อุปกรณ์ (รหัสดิบ / รหัสมาตรฐาน)',
    dossier: 'รหัสแฟ้มหลักฐาน / เวอร์ชันฝั่งระบบหลัก', snapshot: 'สแนปช็อตในเครื่อง', ack: 'บันทึกยืนยันแล้วในเบราว์เซอร์นี้', unsaved: 'สำเนาที่กำลังทำงาน ยังไม่บันทึก',
    mode: 'โหมด', cutoff: 'วันตัดหลักฐาน', jurisdiction: 'เขตอำนาจ', run: 'รอบงาน', hash: 'SHA-256 ของแฟ้มหลักฐาน (canonical)', exporter: 'ตัวส่งออก',
    exporterNote: 'ตัวแปลงฝั่งหน้าเว็บ ไม่ใช่ตัวส่งออก dossier.md ของระบบหลัก', evidence: 'หลักฐานจากต้นทาง',
    evCols: ['รหัสหลักฐาน', 'ข้อความ', 'ประเภท / ฐาน', 'แหล่ง / ฉบับ', 'ตำแหน่งอ้างอิง', 'ข้อความอ้างหรือค่าฟิลด์', 'การตรวจความตรงกับแหล่ง'],
    candidates: 'สิทธิบัตรที่เป็นรายการเบื้องต้น', cCols: ['รหัสดิบ', 'รหัสมาตรฐาน', 'สถานะความเชื่อมโยง', 'แหล่ง / ฉบับ', 'หลักฐานการเปิดเผย', 'คะแนนตามชื่อ'],
    unresolved: 'ประเด็นที่ยังหาข้อสรุปไม่ได้', requests: 'ข้อมูลที่ควรขอเพิ่ม (จากแฟ้มหลักฐาน)', drafts: 'ฉบับร่างคำขอข้อมูลในเครื่อง (ผู้ใช้เขียนเอง)',
    rCols: ['คำถาม', 'อ้างอิง', 'บทบาทผู้ที่ควรถาม', 'ลำดับความสำคัญ', 'สถานะ'], links: 'การเชื่อมโยงคุณลักษณะ (ผู้ใช้เขียนเอง ระบบไม่ได้ตรวจยืนยัน)',
    imported: 'ข้อความแก้ไขที่อยู่ในแฟ้มที่นำเข้า (user_edits)', notes: 'บันทึกของผู้ใช้ (ผู้ใช้เขียนเอง ข้อเท็จจริงจากแหล่งไม่เปลี่ยน)',
    about: 'เกี่ยวกับ', marker: 'สถานะการทบทวน', manifest: 'รายการแหล่งข้อมูล', synthetic: 'ข้อมูลสมมติ', public: 'ข้อมูลสาธารณะ', rights: 'หมายเหตุสิทธิ์',
    scope: 'ขอบเขตการส่งออก', included: 'รวมไว้', omitted: 'ไม่รวม', none: 'ไม่มี',
    includedText: 'ข้อเท็จจริงจากแหล่งพร้อมตำแหน่งอ้างอิง รายการเบื้องต้นและสถานะ ประเด็นที่ยังไม่มีข้อสรุป คำขอข้อมูลจากแฟ้ม ฉบับร่างคำขอในเครื่อง การเชื่อมโยงคุณลักษณะ user_edits ที่นำเข้า และบันทึกของผู้ใช้',
    omittedText: 'ข้อมูลต้นฉบับทั้งหมดของแหล่งและเหตุการณ์ของรอบงาน (ใช้ JSON กู้คืนหากต้องการสำเนาที่ไม่สูญหาย)',
  },
};

function kindBasis(t, e) {
  const basis = e.evidence_kind === 'system_inference' ? 'basis.inference'
    : e.evidence_kind === 'unresolved' ? 'basis.unresolved'
      : e.evidence_kind === 'patent_disclosure' ? 'basis.reported' : 'basis.fact';
  return `${t(`kind.${e.evidence_kind}`)} / ${t(basis)}`;
}

export function integrityLabel(t, status) {
  return {
    exact_span_checked: `${t('integrity.span')} — ${t('integrity.limit')}`,
    field_value_checked: `${t('integrity.field')} — ${t('integrity.limit')}`,
    not_independently_validated: t('integrity.notValidated'),
    not_checked: t('integrity.notChecked'),
  }[status] || t('integrity.notChecked');
}

/**
 * Render an edited Markdown report. ctx: {dossier (plain), dossierHash, mode,
 * overlay, snapshot:{snapshotId, acknowledged}, candidateScope}.
 */
export function renderMarkdown(ctx, language) {
  if (language !== 'en' && language !== 'th') throw new Error('language must be en or th');
  const t = translator(language);
  const h = H[language];
  const d = ctx.dossier;
  const q = d.query;
  const L = [];
  const row = (cells) => L.push(`| ${cells.map(mdCell).join(' | ')} |`);
  L.push(`# ${h.title}`, '', `**${mdText(t(MODE_KEY[ctx.mode]))}**`, '', `> ${mdText(t('scope.help'))}`, '');
  L.push(`| ${h.field} | ${h.value} |`, '|---|---|');
  row([h.device, `${q.device_id_raw} / ${q.device_id_canonical}`]);
  row([h.dossier, `${d.dossier_id} / ${d.version}`]);
  row([h.snapshot, ctx.snapshot?.snapshotId ? `${ctx.snapshot.snapshotId} (${ctx.snapshot.acknowledged ? h.ack : h.unsaved})` : `${t('value.unknown')} (${h.unsaved})`]);
  row([h.mode, `${ctx.mode} — ${t(MODE_KEY[ctx.mode])}`]);
  row([h.cutoff, q.evidence_cutoff]);
  row([h.jurisdiction, q.jurisdiction]);
  row([h.run, d.run_id]);
  row([h.hash, ctx.dossierHash]);
  row([h.exporter, `${MARKDOWN_EXPORTER.id} ${MARKDOWN_EXPORTER.version} (${h.exporterNote})`]);

  L.push('', `## ${h.evidence}`, '', `| ${h.evCols.join(' | ')} |`, `|${'---|'.repeat(h.evCols.length)}`);
  for (const e of d.evidence) {
    const value = e.extraction_method === 'literal_span' ? e.quoted_span
      : e.extraction_method === 'structured_field' ? `${e.structured_field} = ${JSON.stringify(e.structured_value)}` : t('value.unknown');
    row([e.evidence_id, e.statement, kindBasis(t, e), `${e.source_id} / ${e.source_version}`, e.locator, value, integrityLabel(t, e.verification_status)]);
  }

  L.push('', `## ${h.candidates}`, '');
  if (d.candidates.length) {
    L.push(`| ${h.cCols.join(' | ')} |`, `|${'---|'.repeat(h.cCols.length)}`);
    for (const c of d.candidates) {
      const status = c.association_status === 'disclosed_link' ? t('patent.disclosed') : t('patent.candidate');
      const scores = Object.entries(c.scores).map(([k, v]) => `${k}=${v}`).join('; ') || t('evidence.notSupplied');
      row([c.patent_id_raw, c.patent_id_canonical, `${c.association_status} — ${status}`, `${c.source_id} / ${c.source_revision}`, c.disclosure_evidence_id || t('evidence.notSupplied'), scores]);
    }
    L.push('', `_${mdText(t('patent.notLegal'))}_`);
  } else {
    const key = { empty_corpus: 'candidate.emptyCorpus', no_results: 'candidate.noResults' }[ctx.candidateScope] || 'candidate.unknownScope';
    L.push(mdText(t(key)));
  }

  L.push('', `## ${h.unresolved}`, '');
  L.push(...(d.unresolved_items.length ? d.unresolved_items.map((s) => `- ${mdCell(s)}`) : [h.none]));
  L.push('', `## ${h.requests}`, '');
  L.push(...(d.next_information_requests.length ? d.next_information_requests.map((s) => `- ${mdCell(s)}`) : [h.none]));

  const o = ctx.overlay;
  L.push('', `## ${h.drafts}`, '');
  if (o.requestDrafts.length) {
    L.push(`| ${h.rCols.join(' | ')} |`, `|${'---|'.repeat(h.rCols.length)}`);
    for (const r of o.requestDrafts) row([r.question, r.evidenceRefs.join(', ') || t('evidence.notSupplied'), r.intendedRole || t('evidence.notSupplied'), t(`requests.priority.${r.priority}`), t(`requests.status.${r.status}`)]);
  } else L.push(h.none);

  L.push('', `## ${h.links}`, '');
  L.push(...(o.featureLinks.length ? o.featureLinks.map((f) => `- ${mdCell(f.feature)}: ${f.evidenceIds.length ? mdCell(f.evidenceIds.join(', ')) : mdText(t('evidence.featureUnresolved'))}`) : [h.none]));

  L.push('', `## ${h.imported}`, '');
  const edits = Object.entries(d.user_edits || {});
  L.push(...(edits.length ? edits.map(([k, v]) => `- ${mdCell(k)}: ${mdCell(v)}`) : [h.none]));

  L.push('', `## ${h.notes}`, '');
  if (o.notes.length) {
    for (const n of o.notes) {
      L.push(`### ${mdCell(n.noteId)} — ${h.about} ${mdCell(n.targetRef)} (${h.marker}: ${mdCell(t(`note.marker.${n.reviewMarker}`))})`, '');
      for (const line of String(n.text).split(/\r?\n/)) L.push(`> ${mdText(line)}`);
      L.push('');
    }
  } else L.push(h.none, '');

  L.push(`## ${h.manifest}`, '');
  for (const s of d.sources) {
    const r = s.source;
    L.push(`- ${mdCell(r.source_id)}: ${mdCell(r.uri)}; revision ${mdCell(r.version_label)}; ${mdCell(s.jurisdiction)}; ${s.source_date}; sha256 ${r.sha256}; ${s.synthetic ? h.synthetic : h.public}; ${h.rights}: ${mdCell(r.license_note)}`);
  }
  L.push('', `## ${h.scope}`, '', `- ${h.included}: ${h.includedText}`, `- ${h.omitted}: ${h.omittedText}`);
  return `${L.join('\n')}\n`;
}

/** Lossless recovery envelope: one validated dossier plus a separate overlay. */
export function buildRecovery(ctx) {
  const env = {
    format: RECOVERY_FORMAT,
    formatVersion: 1,
    exporter: { ...RECOVERY_EXPORTER },
    generatedAt: new Date().toISOString(),
    mode: ctx.mode,
    project: { localProjectId: ctx.projectId, title: ctx.title || '', storageScope: ctx.storageScope },
    snapshot: {
      snapshotId: ctx.snapshot?.snapshotId ?? null,
      parentSnapshotId: ctx.snapshot?.parentSnapshotId ?? null,
      savedAt: ctx.snapshot?.savedAt ?? null,
      acknowledged: Boolean(ctx.snapshot?.acknowledged),
      lineage: ctx.lineage || [],
    },
    backendDossierVersion: ctx.dossier.version,
    sourceDossierSha256: ctx.dossierHash,
    dossier: ctx.dossierTree,
    runArtifacts: { manifest: ctx.manifestTree ?? null, events: ctx.eventTrees ?? null },
    overlay: ctx.overlay,
    omissions: [],
  };
  return `${stringifyLossless(env)}\n`;
}

const RECOVERY_KEYS = ['format', 'formatVersion', 'exporter', 'generatedAt', 'mode', 'project', 'snapshot', 'backendDossierVersion', 'sourceDossierSha256', 'dossier', 'runArtifacts', 'overlay', 'omissions'];

/** Parse and validate a recovery file; never trusts its own claims. */
export async function parseRecovery(text, schemas) {
  const tree = parseLossless(text);
  const fail = (code, message) => ({ ok: false, errors: [{ code, path: '$', message }] });
  if (!isObj(tree) || tree.format !== RECOVERY_FORMAT) return fail('unsupported_format', 'not a recovery file of this app');
  if (Number(tree.formatVersion) !== 1) return fail('unsupported_version', `recovery formatVersion ${tree.formatVersion} is not supported`);
  for (const k of Object.keys(tree)) if (!RECOVERY_KEYS.includes(k)) return fail('unsupported_field', `unexpected field ${k}`);
  const v = await validateDossier(tree.dossier, schemas.dossier);
  if (!v.ok) return v;
  if (tree.sourceDossierSha256 !== v.hash) return fail('hash_mismatch', `dossier hash ${v.hash} does not match recorded ${tree.sourceDossierSha256}`);
  if (tree.mode !== v.mode) return fail('wrong_mode', `declared mode ${tree.mode} does not match the dossier data class (${v.mode})`);
  const overlay = toPlain(tree.overlay);
  const oErr = overlayErrors(overlay);
  if (oErr.length) return { ok: false, errors: oErr.map((m) => ({ code: 'overlay_invalid', path: '$.overlay', message: m })) };
  const manifestTree = tree.runArtifacts?.manifest ?? null;
  const eventTrees = tree.runArtifacts?.events ?? null;
  const runErrors = validateRunArtifacts(toPlain(tree.dossier), manifestTree && toPlain(manifestTree), eventTrees && toPlain(eventTrees), schemas);
  if (runErrors.length) return { ok: false, errors: runErrors };
  return { ok: true, validation: v, dossierTree: tree.dossier, manifestTree, eventTrees, overlay, snapshot: toPlain(tree.snapshot), project: toPlain(tree.project), mode: v.mode };
}
