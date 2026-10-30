// Project brief drafts. A draft may be incomplete; only a complete draft can be
// shown as a DeviceQuery-shaped preview, and even then nothing is executed.

export function splitLines(text) {
  return String(text ?? '').split(/\r?\n/);
}

/** Lines are optional, but a blank line between entries is rejected (backend rule). */
export function listErrors(text) {
  const lines = splitLines(text);
  if (lines.length === 1 && lines[0].trim() === '') return { items: [], blank: [] };
  // A single trailing newline is tolerated; interior blanks are not.
  const trimmed = lines[lines.length - 1].trim() === '' ? lines.slice(0, -1) : lines;
  const blank = trimmed.map((l, i) => (l.trim() ? null : i + 1)).filter(Boolean);
  return { items: trimmed.filter((l) => l.trim()), blank };
}

export function emptyDraft(today) {
  return {
    rawInput: '', comparator: null, title: '', objective: '', audience: 'entrepreneur',
    featuresText: '', questionsText: '', jurisdiction: 'US', cutoff: today, maxCalls: 3, maxCandidates: 60,
  };
}

/** Build a DeviceQuery-shaped object or explain exactly why not. */
export function draftToQuery(draft, projectId) {
  if (!draft.comparator) return { ok: false, code: 'missing_comparator', reason: 'no comparator selected' };
  const f = listErrors(draft.featuresText);
  const q = listErrors(draft.questionsText);
  if (f.blank.length || q.blank.length) return { ok: false, code: 'blank_item', reason: `blank lines: features ${f.blank.join(',') || '-'}, questions ${q.blank.join(',') || '-'}` };
  if (!String(draft.objective).trim()) return { ok: false, code: 'objective_missing', reason: 'objective is empty' };
  if (!/^\d{4}-\d{2}-\d{2}$/.test(draft.cutoff || '')) return { ok: false, code: 'cutoff_invalid', reason: 'cutoff must be an ISO date' };
  if (draft.comparator.sourceDate > draft.cutoff) return { ok: false, code: 'late_source', reason: `source ${draft.comparator.sourceDate} is after cutoff ${draft.cutoff}` };
  const calls = Number(draft.maxCalls), cands = Number(draft.maxCandidates);
  if (!Number.isInteger(calls) || calls < 0 || calls > 100 || !Number.isInteger(cands) || cands < 0 || cands > 10000) {
    return { ok: false, code: 'budget_invalid', reason: 'search limits out of range (calls 0–100, candidates 0–10000)' };
  }
  const c = draft.comparator;
  return {
    ok: true,
    value: {
      query_id: `WEB-DRAFT-${projectId}`,
      brief: { project_id: projectId, version: 1, objective: draft.objective.trim(), audience: draft.audience, data_class: c.synthetic ? 'synthetic' : 'public', language: draft.language || 'en', theme: draft.theme || 'formal-light' },
      device_id_raw: draft.rawInput.trim() || c.deviceId,
      device_id_canonical: c.deviceId,
      selected_comparator_source_id: c.sourceId,
      technical_description: draft.objective.trim(),
      features_of_interest: f.items,
      user_questions: q.items,
      company_metadata: {},
      company_source_id: null,
      jurisdiction: draft.jurisdiction,
      evidence_cutoff: draft.cutoff,
      permitted_inputs: [c.sourceId],
      acquisition_budget: { max_search_calls: calls, max_returned_candidates: cands, accounting: 'offline_counts' },
    },
  };
}
