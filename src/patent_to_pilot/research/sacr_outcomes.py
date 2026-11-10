"""Prospective cohort completeness and cost accounting, never relevance scoring."""
from collections import Counter
import math

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields, identifier

ARMS = ('G/G', 'G/L', 'I/G', 'I/L')
COUNTS = ('model_calls', 'input_tokens', 'output_tokens', 'embedding_texts',
          'index_dot_products', 'candidate_dot_products', 'peak_memory_bytes')
METRICS = COUNTS + ('operation_wall_seconds', 'gpu_seconds')
STATES = ('MISSING_INPUT', 'PROFILE_FAILED', 'PROFILE_EMPTY', 'REVIEW_REQUIRED',
          'READY', 'RETRIEVAL_FAILED')


def _ranking(value):
    if type(value) is not list or len(value) > 200 or len(set(value)) != len(value):
        raise InputBoundaryError('invalid outcome ranking')
    for family in value:
        identifier(family)
    return list(value)


def finalize_query(*, query_id, state, anchor=None, arms=None):
    """No retry or human per-view filtering. Caller retains original evidence.

    REVIEW_REQUIRED and RETRIEVAL_FAILED stop scoring of the whole cohort. They
    cannot be converted into empty rankings or anchor fallback by this function.
    The standalone generic multi-query baseline is not one of these four arms.
    """
    identifier(query_id)
    if state not in STATES:
        raise InputBoundaryError('unknown query state')
    if state == 'READY':
        if type(arms) is not dict or set(arms) != set(ARMS) or anchor is not None:
            raise InputBoundaryError('ready query requires exactly four arm outputs')
        rankings = {arm: _ranking(arms[arm]) for arm in ARMS}
    elif state in ('PROFILE_FAILED', 'PROFILE_EMPTY'):
        if arms is not None or anchor is None:
            raise InputBoundaryError('failed profile requires verified anchor output')
        rankings = {arm: _ranking(anchor) for arm in ARMS}
    else:
        if anchor is not None or arms is not None:
            raise InputBoundaryError('missing or stopped query cannot carry rankings')
        rankings = {arm: [] for arm in ARMS} if state == 'MISSING_INPUT' else None
    return {'query_id': query_id, 'state': state, 'rankings': rankings,
            'anchor_fallback': state in ('PROFILE_FAILED', 'PROFILE_EMPTY'),
            'scorable': rankings is not None, 'retry': False, 'semantic_status': 'unknown'}


def summarize_cohort(expected_query_ids, outcomes):
    if (type(expected_query_ids) is not list or not expected_query_ids or
            len(set(expected_query_ids)) != len(expected_query_ids)):
        raise InputBoundaryError('invalid expected cohort')
    for query in expected_query_ids:
        identifier(query)
    seen = set()
    checked = []
    for item in outcomes:
        exact_fields(item, {'query_id', 'state', 'rankings', 'anchor_fallback', 'scorable', 'retry', 'semantic_status'})
        if any(type(item[key]) is not bool for key in ('anchor_fallback', 'scorable', 'retry')):
            raise InputBoundaryError('outcome flags must be explicit booleans')
        query, state = item['query_id'], item['state']
        if query in seen or query not in expected_query_ids:
            raise InputBoundaryError('duplicate or foreign query outcome')
        seen.add(query)
        kwargs = {}
        if state == 'READY':
            kwargs['arms'] = item['rankings']
        elif state in ('PROFILE_FAILED', 'PROFILE_EMPTY'):
            if type(item['rankings']) is not dict or set(item['rankings']) != set(ARMS):
                raise InputBoundaryError('fallback arm set mismatch')
            kwargs['anchor'] = item['rankings']['G/G']
        canonical = finalize_query(query_id=query, state=state, **kwargs)
        if item != canonical:
            raise InputBoundaryError('outcome flags or fallback rankings inconsistent')
        checked.append(canonical)
    if seen != set(expected_query_ids):
        raise InputBoundaryError('cohort is incomplete; do not silently drop queries')
    counts = Counter(item['state'] for item in checked)
    return {'queries': len(checked), 'state_counts': {s: counts[s] for s in STATES},
            'fallback_queries': sum(item['anchor_fallback'] for item in checked),
            'scorable': all(item['scorable'] for item in checked),
            'semantic_status': 'unknown', 'relevance_metrics': 'NOT_COMPUTED'}


def summarize_costs(events):
    """Sum actual non-overlapping operation events; shared work appears once.

    Unknown stays null, with an explicitly labelled observed lower bound. Peak
    memory uses max, not sum. Operation-wall sum is NOT end-to-end elapsed time.
    Caller must reconcile events with durable attempt records, including failures.
    """
    values = {metric: [] for metric in METRICS}
    seen = set()
    for event in events:
        exact_fields(event, {'event_id', 'query_id', 'stage', 'status', 'metrics'})
        for key in ('event_id', 'query_id', 'stage'):
            identifier(event[key])
        if event['event_id'] in seen or event['status'] not in ('COMPLETED', 'FAILED', 'INTERRUPTED'):
            raise InputBoundaryError('duplicate cost event or invalid attempt status')
        seen.add(event['event_id'])
        exact_fields(event['metrics'], set(METRICS))
        for metric in METRICS:
            value = event['metrics'][metric]
            if value is not None:
                valid_type = type(value) is int if metric in COUNTS else type(value) in (int, float)
                if not valid_type or not math.isfinite(value) or value < 0:
                    raise InputBoundaryError('invalid measured cost')
            values[metric].append(value)
    summary = {}
    for metric, entries in values.items():
        observed = [v for v in entries if v is not None]
        lower = max(observed, default=0) if metric == 'peak_memory_bytes' else sum(observed)
        unknown = sum(v is None for v in entries)
        summary[metric] = {'value': None if unknown or not entries else lower,
                           'observed_lower_bound': lower, 'unknown_events': unknown}
    return {'events': len(seen), 'metrics': summary,
            'end_to_end_elapsed_seconds': None, 'standalone_arm_costs': 'NOT_DERIVED',
            'receipt_completeness': 'REQUIRES_EXTERNAL_ATTEMPT_RECONCILIATION' if seen else 'NO_EVENTS_RECORDED'}
