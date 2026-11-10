import copy

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_outcomes import ARMS, METRICS, finalize_query, summarize_cohort, summarize_costs


def test_failures_and_missing_queries_remain_in_denominator():
    rows = [finalize_query(query_id='q1', state='MISSING_INPUT'),
            finalize_query(query_id='q2', state='PROFILE_FAILED', anchor=['f1']),
            finalize_query(query_id='q3', state='READY', arms={arm: ['f2'] for arm in ARMS})]
    r = summarize_cohort(['q1', 'q2', 'q3'], rows)
    assert r['queries'] == 3 and r['fallback_queries'] == 1 and r['scorable']
    assert rows[0]['rankings']['I/L'] == []
    rows[1]['rankings']['G/G'].append('f3')
    assert rows[1]['rankings']['I/L'] == ['f1']


@pytest.mark.parametrize('state', ['REVIEW_REQUIRED', 'RETRIEVAL_FAILED'])
def test_review_or_retrieval_failure_stops_whole_cohort(state):
    row = finalize_query(query_id='q', state=state)
    assert row['rankings'] is None
    assert not summarize_cohort(['q'], [row])['scorable']
    with pytest.raises(InputBoundaryError):
        finalize_query(query_id='q', state=state, anchor=['f'])


@pytest.mark.parametrize('case', ['missing', 'duplicate', 'foreign', 'flags', 'fallback_differs'])
def test_cohort_completeness_and_consistency(case):
    row = finalize_query(query_id='q', state='PROFILE_EMPTY', anchor=['f'])
    rows = [row]
    if case == 'missing':
        rows = []
    elif case == 'duplicate':
        rows *= 2
    elif case == 'foreign':
        row['query_id'] = 'other'
    elif case == 'flags':
        row['retry'] = True
    else:
        row['rankings']['I/L'] = []
    with pytest.raises(InputBoundaryError):
        summarize_cohort(['q'], rows)


def event(name='e1'):
    return {'event_id': name, 'query_id': 'q', 'stage': 'profile', 'status': 'COMPLETED',
            'metrics': {metric: 0 for metric in METRICS}}


def test_unknown_failed_attempt_cost_is_not_zero_and_peaks_not_added():
    a, b = event(), event('e2')
    a['metrics'].update(model_calls=1, peak_memory_bytes=100)
    b['status'] = 'INTERRUPTED'
    b['metrics'].update(model_calls=None, output_tokens=None, peak_memory_bytes=150)
    r = summarize_costs([a, b])['metrics']
    assert r['model_calls'] == {'value': None, 'observed_lower_bound': 1, 'unknown_events': 1}
    assert r['peak_memory_bytes']['value'] == 150


def test_empty_ledger_is_not_evidence_of_zero_cost():
    r = summarize_costs([])
    assert r['metrics']['model_calls']['value'] is None
    assert r['receipt_completeness'] == 'NO_EVENTS_RECORDED'


@pytest.mark.parametrize('case', ['duplicate', 'negative', 'nan', 'boolean', 'missing_metric'])
def test_bad_cost_receipts_refused(case):
    a = event()
    events = [a]
    if case == 'duplicate':
        events.append(copy.deepcopy(a))
    elif case == 'negative':
        a['metrics']['model_calls'] = -1
    elif case == 'nan':
        a['metrics']['gpu_seconds'] = float('nan')
    elif case == 'boolean':
        a['metrics']['model_calls'] = True
    else:
        del a['metrics']['input_tokens']
    with pytest.raises(InputBoundaryError):
        summarize_costs(events)
