// Run receipt view model built only from imported artifacts. Missing data stays
// unknown ({status:'unknown'}); it never becomes zero.

export const known = (value) => ({ status: 'known', value });
export const unknown = (reason) => ({ status: 'unknown', reason });

// sha256 of canonical "[]" = content_hash([]) — the corpus hash of an empty patent pool.
export const EMPTY_CORPUS_HASH = '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945';

/**
 * Candidate scope explains an empty candidate list without inventing absence:
 * 'empty_corpus' (manifest proves zero patent input), 'no_results' (corpus was
 * supplied, nothing returned), 'has_candidates', or 'unknown' (no manifest).
 */
export function candidateScope(dossier, manifest) {
  if (dossier.candidates.length) return 'has_candidates';
  if (!manifest) return 'unknown';
  return manifest.corpus_hash === EMPTY_CORPUS_HASH ? 'empty_corpus' : 'no_results';
}

export function summarizeRun(dossier, manifest, events) {
  if (!manifest && !events) {
    return { available: false, reason: 'No manifest or acquisition events were imported with this dossier.' };
  }
  const ev = events || [];
  const sum = (k) => ev.reduce((a, e) => a + Number(e[k] || 0), 0);
  const returnedIds = new Set(ev.flatMap((e) => e.returned_candidate_ids || []));
  const stopEvent = ev.find((e) => e.action_type === 'stop');
  const eventCalls = events ? known(sum('search_calls')) : unknown('events not imported');
  const manifestCalls = manifest ? known(Number(manifest.actual_search_calls)) : unknown('manifest not imported');
  const consistency = [];
  if (manifest && events) {
    consistency.push({ field: 'search_calls', manifest: Number(manifest.actual_search_calls), events: sum('search_calls') });
    consistency.push({ field: 'returned_candidates', manifest: Number(manifest.actual_returned_candidates), events: sum('returned_candidates') });
    if (stopEvent) consistency.push({ field: 'stop_reason', manifest: manifest.stop_reason, events: stopEvent.stop_reason });
  }
  return {
    available: true,
    runId: dossier.run_id,
    policyId: manifest ? manifest.policy_id : (ev[0]?.policy_id ?? null),
    evidenceLevel: manifest ? manifest.evidence_level : null,
    callsUsed: manifest ? manifestCalls : eventCalls,
    callsCap: known(Number(dossier.query.acquisition_budget.max_search_calls)),
    returnedOccurrences: events ? known(sum('returned_candidates')) : (manifest ? known(Number(manifest.actual_returned_candidates)) : unknown('not recorded')),
    uniqueCandidates: known(dossier.candidates.length),
    eventCandidateIds: events ? known(returnedIds.size) : unknown('events not imported'),
    retries: events ? known(sum('retry_count')) : unknown('events not imported'),
    errors: ev.flatMap((e) => e.errors || []),
    failedQueries: manifest ? manifest.failed_query_ids : [],
    completedQueries: manifest ? manifest.completed_query_ids : [],
    stopReason: manifest ? manifest.stop_reason : (stopEvent ? stopEvent.stop_reason : null),
    events: ev.map((e) => ({ stepId: e.step_id, action: e.action_type, calls: e.search_calls, returned: e.returned_candidates, newCount: e.new_candidate_count, startedAt: e.started_at, errors: e.errors || [], stopReason: e.stop_reason })),
    consistency,
    consistent: consistency.every((c) => c.manifest === c.events),
    cost: costView(manifest),
    limitations: manifest ? manifest.limitations : [],
  };
}

/** Cost view: only a source receipt can establish an actual zero. */
export function costView(manifest, simulatedCost) {
  if (simulatedCost) {
    return { accounting: simulatedCost.accounting, actualUsd: simulatedCost.actualUsd === null ? unknown(simulatedCost.reason) : known(simulatedCost.actualUsd), settlement: simulatedCost.settlement, simulated: true };
  }
  if (!manifest) return { accounting: 'not_recorded', actualUsd: unknown('no run manifest imported'), settlement: 'unknown' };
  return {
    accounting: 'offline_counts',
    actualUsd: known(Number(manifest.paid_cost_usd)),
    providerCalls: known(Number(manifest.provider_calls)),
    basis: `manifest ${manifest.cost_accounting_version}: offline run, provider_calls=${manifest.provider_calls}`,
    settlement: 'recorded',
  };
}
