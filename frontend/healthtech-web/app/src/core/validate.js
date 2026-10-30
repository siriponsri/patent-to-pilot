// Import validation: generated JSON Schema (closed contracts) + the semantic
// rules of healthtech/contracts.py, provenance.check_evidence and the UX pack's
// validate_docs.py domain checks. Source-integrity only; never a truth check.
import { PyNum, isObj, contentHash, canonicalDumps, toPlain } from './pyjson.js';
import { parseLocator, sliceCodePoints, resolveField } from './locator.js';

// ---------------------------------------------------------------- JSON Schema subset
const DATE = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;
const DATETIME = /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?$/;

function typeOk(type, v) {
  switch (type) {
    case 'null': return v === null;
    case 'boolean': return typeof v === 'boolean';
    case 'string': return typeof v === 'string';
    case 'array': return Array.isArray(v);
    case 'object': return isObj(v);
    case 'number': return v instanceof PyNum || typeof v === 'number';
    case 'integer': return (v instanceof PyNum || typeof v === 'number') && Number.isInteger(Number(v));
    default: return false;
  }
}

/** Validate against the keyword subset used by the generated HealthTech schemas. */
export function schemaErrors(schema, value, root = schema, path = '$', out = []) {
  if (schema === true || schema === undefined) return out;
  if (schema === false) { out.push({ path, message: 'not allowed' }); return out; }
  if (schema.$ref) {
    const name = /^#\/\$defs\/(.+)$/.exec(schema.$ref);
    if (!name || !root.$defs?.[name[1]]) { out.push({ path, message: `unresolvable ${schema.$ref}` }); return out; }
    return schemaErrors(root.$defs[name[1]], value, root, path, out);
  }
  if (schema.anyOf) {
    if (!schema.anyOf.some((s) => schemaErrors(s, value, root, path, []).length === 0)) out.push({ path, message: 'matches no allowed alternative' });
    return out;
  }
  if (schema.type && !(Array.isArray(schema.type) ? schema.type : [schema.type]).some((t) => typeOk(t, value))) {
    out.push({ path, message: `expected ${schema.type}` });
    return out;
  }
  if ('const' in schema && canonicalDumps(value) !== canonicalDumps(schema.const)) out.push({ path, message: `must equal ${JSON.stringify(schema.const)}` });
  if (schema.enum && !schema.enum.some((e) => canonicalDumps(e) === canonicalDumps(value))) out.push({ path, message: `must be one of ${schema.enum.join(', ')}` });
  if (typeof value === 'string') {
    const len = Array.from(value).length;
    if (schema.minLength !== undefined && len < schema.minLength) out.push({ path, message: `shorter than ${schema.minLength}` });
    if (schema.maxLength !== undefined && len > schema.maxLength) out.push({ path, message: `longer than ${schema.maxLength}` });
    if (schema.pattern && !new RegExp(schema.pattern, 'u').test(value)) out.push({ path, message: `does not match ${schema.pattern}` });
    if (schema.format === 'date' && !DATE.test(value)) out.push({ path, message: 'not an ISO date' });
    if (schema.format === 'date-time' && !DATETIME.test(value)) out.push({ path, message: 'not an ISO date-time' });
  }
  if (value instanceof PyNum || typeof value === 'number') {
    const n = Number(value);
    if (schema.minimum !== undefined && n < schema.minimum) out.push({ path, message: `below ${schema.minimum}` });
    if (schema.maximum !== undefined && n > schema.maximum) out.push({ path, message: `above ${schema.maximum}` });
  }
  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) out.push({ path, message: `fewer than ${schema.minItems} items` });
    if (schema.items) value.forEach((v, k) => schemaErrors(schema.items, v, root, `${path}[${k}]`, out));
  }
  if (isObj(value)) {
    for (const req of schema.required || []) if (!(req in value)) out.push({ path: `${path}.${req}`, message: 'required' });
    const props = schema.properties || {};
    for (const key of Object.keys(value)) {
      if (key in props) schemaErrors(props[key], value[key], root, `${path}.${key}`, out);
      else if (schema.additionalProperties === false) out.push({ path: `${path}.${key}`, message: 'unexpected field (closed contract)' });
      else if (isObj(schema.additionalProperties)) schemaErrors(schema.additionalProperties, value[key], root, `${path}.${key}`, out);
    }
  }
  return out;
}

// ---------------------------------------------------------------- backend rules
export function canonicalPatentId(raw) {
  const value = String(raw).replace(/[\s,./-]/g, '').toUpperCase();
  if (!/^[A-Z]{2}[0-9]{4,14}(?:[A-Z][0-9]?)?$/.test(value)) return null;
  return value;
}

/** provenance.check_evidence: returns {ok, status} or {ok:false, code, message}. */
export async function checkEvidence(item, source) {
  const rec = source.source;
  const hash = await contentHash(source.payload);
  if (item.source_id !== rec.source_id || item.source_version !== rec.version_label) {
    return { ok: false, code: 'source_revision_mismatch', message: 'evidence source ID/revision does not match the pinned source' };
  }
  if (item.payload_hash !== hash || item.payload_hash !== rec.sha256) {
    return { ok: false, code: 'hash_mismatch', message: 'evidence payload hash does not match the source payload' };
  }
  if (item.jurisdiction !== source.jurisdiction || item.source_date !== source.source_date) {
    return { ok: false, code: 'date_jurisdiction_mismatch', message: 'evidence date/jurisdiction does not match the source' };
  }
  if (item.evidence_kind === 'system_inference' || item.evidence_kind === 'unresolved') {
    return { ok: true, status: item.verification_status };
  }
  const loc = parseLocator(item.locator);
  if (item.extraction_method === 'literal_span') {
    if (loc.kind !== 'chars' || typeof source.payload !== 'string') {
      return { ok: false, code: 'locator_invalid', message: 'literal evidence needs text and a chars:start:end locator' };
    }
    const cut = sliceCodePoints(source.payload, loc.start, loc.end);
    if (!cut || cut.span !== item.quoted_span) return { ok: false, code: 'span_mismatch', message: 'exact quoted span does not match the source text' };
    return { ok: true, status: 'exact_span_checked', span: cut };
  }
  if (item.locator !== `field:${item.structured_field}` || !isObj(source.payload)) {
    return { ok: false, code: 'locator_invalid', message: 'structured evidence needs a field locator and an object payload' };
  }
  const found = resolveField(source.payload, String(item.structured_field).split('.'));
  if (!found.found) return { ok: false, code: 'field_missing', message: 'structured field not present in the source' };
  if ((await contentHash(found.value)) !== (await contentHash(item.structured_value))) {
    return { ok: false, code: 'field_mismatch', message: 'structured field value or type does not match the source' };
  }
  return { ok: true, status: 'field_value_checked', field: found };
}

function err(code, path, message) { return { code, path, message }; }

/**
 * Validation stages, in order. Each stage really performs its checks and
 * records errors plus per-item outcomes, so the UI can show genuine progress
 * (the pipeline canvas) instead of a scripted animation.
 */
export const DOSSIER_STAGES = [
  { id: 'schema', run: async (ctx) => {
    const problems = schemaErrors(ctx.schema, ctx.raw);
    problems.forEach((p) => ctx.errors.push(err('schema', p.path, p.message)));
    if (!problems.length) ctx.checks.push({ check: 'closed_schema', result: 'pass' });
    return { stop: problems.length > 0, items: [] };
  } },
  { id: 'query', run: async (ctx) => {
    const d = ctx.raw, q = d.query, brief = q.brief;
    const before = ctx.errors.length;
    if (brief.data_class === 'private') ctx.errors.push(err('private_data', '$.query.brief.data_class', 'private inputs are not accepted by this local public/synthetic workflow'));
    if (d.project_id !== brief.project_id) ctx.errors.push(err('project_mismatch', '$.project_id', 'project_id differs from query.brief.project_id'));
    const version = Number(d.version);
    const parent = d.parent_version === null ? null : Number(d.parent_version);
    if ((version === 1) !== (parent === null) || (parent !== null && parent !== version - 1)) {
      ctx.errors.push(err('version_chain', '$.parent_version', 'initial version has no parent; later versions require the preceding one'));
    }
    const required = new Set([q.selected_comparator_source_id]);
    if (Object.keys(q.company_metadata).length) {
      if (!q.company_source_id) ctx.errors.push(err('company_basis', '$.query.company_source_id', 'company metadata requires a source basis'));
      else required.add(q.company_source_id);
    }
    for (const r of required) if (!q.permitted_inputs.includes(r)) ctx.errors.push(err('comparator_not_permitted', '$.query.permitted_inputs', `${r} must be a permitted input`));
    [...q.features_of_interest, ...q.user_questions].forEach((s, k) => { if (!s.trim()) ctx.errors.push(err('blank_item', `$.query[${k}]`, 'features/questions must not be blank')); });
    return { items: [{ id: q.device_id_canonical, ok: ctx.errors.length === before }] };
  } },
  { id: 'sources', run: async (ctx) => {
    const d = ctx.raw, q = d.query, brief = q.brief;
    const items = [];
    for (const [k, s] of d.sources.entries()) {
      const before = ctx.errors.length;
      const id = s.source.source_id;
      if (ctx.sources.has(id)) ctx.errors.push(err('duplicate_ids', `$.sources[${k}]`, `duplicate source ID ${id}`));
      ctx.sources.set(id, s);
      const h = await contentHash(s.payload);
      if (s.source.sha256 !== h) ctx.errors.push(err('source_hash_mismatch', `$.sources[${k}].source.sha256`, `payload hash ${h} does not match recorded ${s.source.sha256}`));
      if (s.source_date > q.evidence_cutoff) ctx.errors.push(err('late_source', `$.sources[${k}].source_date`, `source date ${s.source_date} is after evidence cutoff ${q.evidence_cutoff}`));
      const looksSynthetic = s.synthetic === true || String(s.source.uri).startsWith('urn:synthetic:');
      if (brief.data_class === 'public' && looksSynthetic) ctx.errors.push(err('synthetic_in_public', `$.sources[${k}].synthetic`, 'synthetic source cannot be presented as public evidence'));
      if (brief.data_class === 'synthetic' && !s.synthetic) ctx.errors.push(err('public_in_synthetic', `$.sources[${k}].synthetic`, 'a synthetic dossier may not carry unlabelled real sources'));
      items.push({ id, ok: ctx.errors.length === before });
    }
    ctx.checks.push({ check: 'source_payload_hashes', result: ctx.errors.some((e) => e.code === 'source_hash_mismatch') ? 'fail' : 'pass' });
    if (!ctx.sources.has(q.selected_comparator_source_id)) ctx.errors.push(err('dangling_source', '$.query.selected_comparator_source_id', 'comparator source is missing from the package'));
    return { items };
  } },
  { id: 'evidence', run: async (ctx) => {
    const items = [];
    for (const [k, e] of ctx.raw.evidence.entries()) {
      const before = ctx.errors.length;
      const p = `$.evidence[${k}]`;
      if (ctx.evidence.has(e.evidence_id)) ctx.errors.push(err('duplicate_ids', p, `duplicate evidence ID ${e.evidence_id}`));
      ctx.evidence.set(e.evidence_id, e);
      if (e.extraction_method === 'literal_span' && (!e.quoted_span || e.structured_field)) ctx.errors.push(err('evidence_basis', p, 'literal evidence needs only a nonempty quoted span'));
      if (e.extraction_method === 'structured_field' && (!e.structured_field || e.quoted_span)) ctx.errors.push(err('evidence_basis', p, 'field evidence needs only a field path'));
      if (e.evidence_kind === 'system_inference' || e.evidence_kind === 'unresolved') {
        if (e.verification_status !== 'not_independently_validated') ctx.errors.push(err('evidence_basis', p, 'inferences/unknowns cannot be promoted by exact-source checks'));
      } else if (e.extraction_method === 'authored_inference') ctx.errors.push(err('evidence_basis', p, 'authored inference cannot be a source fact'));
      const src = ctx.sources.get(e.source_id);
      if (!src) ctx.errors.push(err('dangling_source', `${p}.source_id`, `evidence cites missing source ${e.source_id}`));
      else {
        const res = await checkEvidence(e, src);
        if (!res.ok) ctx.errors.push(err(res.code, p, `${e.evidence_id}: ${res.message}`));
        else if (res.status !== e.verification_status) ctx.errors.push(err('badge_not_reproducible', `${p}.verification_status`, `recorded ${e.verification_status} but recomputed ${res.status}`));
      }
      items.push({ id: e.evidence_id, ok: ctx.errors.length === before });
    }
    ctx.checks.push({ check: 'evidence_integrity', result: ctx.errors.some((e) => e.path?.startsWith('$.evidence')) ? 'fail' : 'pass' });
    return { items };
  } },
  { id: 'candidates', run: async (ctx) => {
    const items = [];
    for (const [k, c] of ctx.raw.candidates.entries()) {
      const before = ctx.errors.length;
      const p = `$.candidates[${k}]`;
      if (canonicalPatentId(c.patent_id_raw) !== c.patent_id_canonical) ctx.errors.push(err('raw_canonical_mismatch', p, `raw ${c.patent_id_raw} does not normalize to ${c.patent_id_canonical}`));
      if (c.family_id && !c.family_source_id) ctx.errors.push(err('unsourced_family', p, 'family identity requires provenance'));
      const src = ctx.sources.get(c.source_id);
      if (!src) ctx.errors.push(err('dangling_source', `${p}.source_id`, `candidate cites missing source ${c.source_id}`));
      else if (c.source_revision !== src.source.version_label) ctx.errors.push(err('candidate_revision_mismatch', p, 'candidate revision differs from the pinned source revision'));
      if (c.association_status === 'disclosed_link') {
        const e = c.disclosure_evidence_id ? ctx.evidence.get(c.disclosure_evidence_id) : undefined;
        if (!e || e.evidence_kind !== 'patent_disclosure') ctx.errors.push(err('missing_disclosure', p, 'a disclosed link needs source-backed patent_disclosure evidence'));
        else if (e.source_id === c.source_id || ctx.sources.get(e.source_id)?.source.source_type !== 'independent_disclosure') {
          ctx.errors.push(err('disclosure_not_independent', p, 'disclosure must come from an independent_disclosure source'));
        }
      }
      items.push({ id: c.patent_id_canonical, ok: ctx.errors.length === before });
    }
    ctx.checks.push({ check: 'candidate_identity_and_disclosure', result: ctx.errors.some((e) => e.path?.startsWith('$.candidates')) ? 'fail' : 'pass' });
    return { items };
  } },
];

/**
 * Run the stages in order. onStage(event) receives {stage, phase:'start'|'end'|'skipped',
 * errors (this stage's only), items, ms (measured)}. Optional `pace` lets the UI slow
 * the *display* between stages; it never changes results.
 */
export async function runDossierStages(raw, schema, { onStage, pace } = {}) {
  const ctx = { raw, schema, errors: [], checks: [], sources: new Map(), evidence: new Map() };
  for (const [i, stage] of DOSSIER_STAGES.entries()) {
    await onStage?.({ stage: stage.id, phase: 'start' });
    // Display pacing sits between "start" and the work so a running step is visible;
    // the measured duration below covers only the real checks.
    if (pace) await pace(stage.id);
    const before = ctx.errors.length;
    const t0 = globalThis.performance.now();
    const out = await stage.run(ctx);
    const ms = globalThis.performance.now() - t0;
    await onStage?.({ stage: stage.id, phase: 'end', errors: ctx.errors.slice(before), items: out.items, ms });
    if (out.stop) {
      for (const rest of DOSSIER_STAGES.slice(i + 1)) await onStage?.({ stage: rest.id, phase: 'skipped' });
      return { ok: false, errors: ctx.errors, checks: ctx.checks };
    }
  }
  const mode = raw.query.brief.data_class === 'synthetic' ? 'synthetic_demo' : 'imported_public';
  return { ok: ctx.errors.length === 0, errors: ctx.errors, checks: ctx.checks, mode, hash: await contentHash(raw) };
}

/**
 * Full import validation of a lossless DossierVersion tree.
 * Returns {ok, errors[], checks[], mode, hash}. Never mutates `raw`.
 */
export async function validateDossier(raw, schema) {
  return runDossierStages(raw, schema);
}

/** Light consistency checks for completed CLI run artifacts. */
export function validateRunArtifacts(dossier, manifest, events, schemas) {
  const errors = [];
  if (manifest) {
    for (const p of schemaErrors(schemas.manifest, manifest)) errors.push(err('manifest_schema', p.path, p.message));
    if (manifest.run_id !== dossier.run_id) errors.push(err('run_mismatch', '$.manifest.run_id', 'manifest run_id differs from dossier run_id'));
    if (manifest.input_hash !== dossier.input_hash) errors.push(err('run_mismatch', '$.manifest.input_hash', 'manifest input_hash differs from dossier input_hash'));
    if (manifest.expected_query_ids?.length !== 1 || manifest.expected_query_ids[0] !== dossier.query.query_id) errors.push(err('query_mismatch', '$.manifest.expected_query_ids', 'this dossier needs a manifest for its single query'));
  }
  const steps = new Set();
  for (const [k, e] of (events || []).entries()) {
    for (const p of schemaErrors(schemas.event, e)) errors.push(err('event_schema', `$.events[${k}]${p.path.slice(1)}`, p.message));
    if (e.run_id !== dossier.run_id) errors.push(err('run_mismatch', `$.events[${k}].run_id`, 'event run_id differs from dossier run_id'));
    if (e.query_id !== dossier.query.query_id) errors.push(err('query_mismatch', `$.events[${k}].query_id`, 'event query_id differs from dossier query_id'));
    if (steps.has(e.step_id)) errors.push(err('duplicate_step', `$.events[${k}].step_id`, 'duplicate event step would double-count resource use'));
    steps.add(e.step_id);
    if (manifest && e.policy_id !== manifest.policy_id) errors.push(err('policy_mismatch', `$.events[${k}].policy_id`, 'event policy differs from the manifest'));
  }
  return errors;
}

export { toPlain };
