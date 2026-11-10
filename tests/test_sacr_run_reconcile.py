import copy

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_outcomes import ARMS, METRICS, finalize_query
from patent_to_pilot.research.sacr_run_reconcile import STAGES, reconcile_run


def fixture():
    slots = [{'attempt_id': stage, 'query_id': 'q', 'stage': stage} for stage in sorted(STAGES)]
    manifest = {'format': 'sacr-dev-attempt-plan-v1', 'split': 'dev', 'run_id': 'run1',
                'query_ids': ['q'], 'slots': slots}
    attempts = [{**s, 'status': 'COMPLETED', 'receipt_sha256': 'a' * 64, 'reason': None} for s in slots]
    events = [{'event_id': s['attempt_id'], 'query_id': 'q', 'stage': s['stage'],
               'status': 'COMPLETED', 'metrics': {k: 0 for k in METRICS}} for s in slots]
    outcomes = [finalize_query(query_id='q', state='READY', arms={a: ['f'] for a in ARMS})]
    return dict(manifest=manifest, attempts=attempts, events=events, outcomes=outcomes,
                expected_manifest_sha256=digest(manifest))


def test_complete_records_reconcile_without_granting_test_access():
    r = reconcile_run(**fixture())
    assert r['attempts'] == 6 and r['cohort']['scorable']
    assert not r['protected_evaluation_authorized']


def test_missing_input_requires_explicit_skip_receipts_not_missing_records():
    p = fixture()
    p['outcomes'] = [finalize_query(query_id='q', state='MISSING_INPUT')]
    for a in p['attempts']:
        a.update(status='SKIPPED', reason='missing input')
    p['events'] = []
    r = reconcile_run(**p)
    assert r['skipped'] == 6
    assert r['costs']['metrics']['model_calls']['value'] is None


@pytest.mark.parametrize('case', ['test', 'changed_manifest', 'missing_attempt', 'missing_cost',
                                  'duplicate', 'running', 'wrong_cost_stage', 'false_ready',
                                  'missing_receipt', 'retry_slot'])
def test_inconsistent_run_records_fail_closed(case):
    p = copy.deepcopy(fixture())
    if case == 'test':
        p['manifest']['split'] = 'test'
        p['expected_manifest_sha256'] = digest(p['manifest'])
    elif case == 'changed_manifest':
        p['manifest']['run_id'] = 'changed'
    elif case == 'missing_attempt':
        p['attempts'].pop()
    elif case == 'missing_cost':
        p['events'].pop()
    elif case == 'duplicate':
        p['attempts'].append(copy.deepcopy(p['attempts'][0]))
    elif case == 'running':
        p['attempts'][0]['status'] = 'RUNNING'
    elif case == 'wrong_cost_stage':
        p['events'][0]['stage'] = 'other'
    elif case == 'false_ready':
        for a in p['attempts']:
            if a['stage'] == 'selection':
                a.update(status='SKIPPED', reason='never executed')
        p['events'] = [e for e in p['events'] if e['stage'] != 'selection']
    elif case == 'missing_receipt':
        p['attempts'][0]['receipt_sha256'] = None
    else:
        p['manifest']['slots'].append({**p['manifest']['slots'][0], 'attempt_id': 'retry'})
        p['expected_manifest_sha256'] = digest(p['manifest'])
    with pytest.raises(InputBoundaryError):
        reconcile_run(**p)
