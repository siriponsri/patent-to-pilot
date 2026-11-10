"""Reconcile supplied dev run records; never infer that a live attempt stopped."""
from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields, identifier
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_outcomes import summarize_cohort, summarize_costs

STAGES = {'profile', 'generic', 'selective', 'embedding', 'acquisition', 'selection'}


def validate_plan(manifest, *, expected_manifest_sha256):
    """One predeclared slot per query/stage; no automatic retries or skipped costs.

    Hashes attest record consistency only. A trusted controller must create the
    manifest/reservations before execution and bind receipt bytes independently.
    This reader neither grants isolation nor proves actual execution/authorization.
    """
    exact_fields(manifest, {'format', 'split', 'run_id', 'query_ids', 'slots'})
    if (manifest['format'] != 'sacr-dev-attempt-plan-v1' or manifest['split'] != 'dev' or
            digest(manifest) != expected_manifest_sha256):
        raise InputBoundaryError('wrong run plan identity or non-dev split')
    identifier(manifest['run_id'])
    slots, pairs = {}, set()
    for slot in manifest['slots']:
        exact_fields(slot, {'attempt_id', 'query_id', 'stage'})
        identifier(slot['attempt_id'])
        pair = (slot['query_id'], slot['stage'])
        if (slot['attempt_id'] in slots or pair in pairs or
                slot['query_id'] not in manifest['query_ids'] or slot['stage'] not in STAGES):
            raise InputBoundaryError('invalid or duplicate planned attempt')
        slots[slot['attempt_id']] = slot
        pairs.add(pair)
    if any((q, stage) not in pairs for q in manifest['query_ids'] for stage in STAGES):
        raise InputBoundaryError('every query needs all six explicit stage slots')
    return slots


def reconcile_run(manifest, attempts, events, outcomes, *, expected_manifest_sha256):
    slots = validate_plan(manifest, expected_manifest_sha256=expected_manifest_sha256)
    cohort = summarize_cohort(manifest['query_ids'], outcomes)
    records = {}
    for attempt in attempts:
        exact_fields(attempt, {'attempt_id', 'query_id', 'stage', 'status', 'receipt_sha256', 'reason'})
        key = attempt['attempt_id']
        if key not in slots or key in records or any(attempt[k] != slots[key][k] for k in ('query_id', 'stage')):
            raise InputBoundaryError('foreign, duplicate or mismatched attempt')
        if attempt['status'] in ('PLANNED', 'RESERVED', 'RUNNING'):
            raise InputBoundaryError('nonterminal attempt; verify live process instead of inferring interruption')
        if attempt['status'] not in ('COMPLETED', 'FAILED', 'INTERRUPTED', 'SKIPPED'):
            raise InputBoundaryError('invalid attempt status')
        sha = attempt['receipt_sha256']
        if type(sha) is not str or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise InputBoundaryError('terminal or skip receipt digest required')
        if attempt['status'] != 'COMPLETED' and (type(attempt['reason']) is not str or not attempt['reason'].strip()):
            raise InputBoundaryError('failed or skipped attempt needs reason')
        records[key] = attempt
    if set(records) != set(slots):
        raise InputBoundaryError('planned attempt missing from journal')
    costs = summarize_costs(events)
    expected_events = {key for key, record in records.items() if record['status'] != 'SKIPPED'}
    if {e['event_id'] for e in events} != expected_events:
        raise InputBoundaryError('every started attempt needs exactly one actual cost event')
    for event in events:
        record = records[event['event_id']]
        if any(event[k] != record[k] for k in ('query_id', 'stage', 'status')):
            raise InputBoundaryError('cost event does not describe its attempt')
    states = {(record['query_id'], record['stage']): record['status'] for record in records.values()}
    for outcome in outcomes:
        q, state = outcome['query_id'], outcome['state']
        if state == 'MISSING_INPUT' and any(states[q, stage] != 'SKIPPED' for stage in STAGES):
            raise InputBoundaryError('missing input cannot have executed stages')
        if state == 'PROFILE_FAILED' and states[q, 'profile'] not in ('FAILED', 'INTERRUPTED'):
            raise InputBoundaryError('profile fallback contradicts attempt journal')
        if state in ('PROFILE_EMPTY', 'REVIEW_REQUIRED', 'READY') and states[q, 'profile'] != 'COMPLETED':
            raise InputBoundaryError('profile outcome requires completed profile attempt')
        if state == 'READY' and any(states[q, stage] != 'COMPLETED' for stage in ('embedding', 'acquisition', 'selection')):
            raise InputBoundaryError('ready outcome requires completed retrieval stages')
        if state == 'RETRIEVAL_FAILED' and not any(states[q, stage] in ('FAILED', 'INTERRUPTED')
                                                  for stage in ('embedding', 'acquisition', 'selection')):
            raise InputBoundaryError('retrieval failure contradicts attempt journal')
    return {'status': 'RECORDS_RECONCILED_NOT_EXECUTION_PROOF', 'manifest_sha256': expected_manifest_sha256,
            'attempts': len(records), 'skipped': len(records) - len(expected_events),
            'cohort': cohort, 'costs': costs, 'protected_evaluation_authorized': False}
