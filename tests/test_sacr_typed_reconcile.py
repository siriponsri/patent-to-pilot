import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_outcomes import METRICS, finalize_query
from test_sacr_controller import setup, adapter


def stopped(tmp_path, kind):
    controller = setup(tmp_path)
    def work(query, source):
        p, metrics = adapter(query, source)
        if kind == 'review':
            p['unknowns'] = [{'description': 'authored uncertainty', 'reason': 'ambiguity'}]
        else:
            p['blocks'] = []
            if kind == 'failed':
                p['extraction_status'] = 'failed'
                p['failure_reasons'] = ['authored extraction failure']
        return p, metrics
    controller.profile('q', work)
    return controller.journal


@pytest.mark.parametrize('kind,state', [('failed', 'PROFILE_FAILED'), ('empty', 'PROFILE_EMPTY'),
                                       ('review', 'REVIEW_REQUIRED')])
def test_completed_transport_reconciles_actual_typed_stop(tmp_path, kind, state):
    journal = stopped(tmp_path, kind)
    for stage in journal.slots:
        if stage != 'profile':
            journal.skip(stage, reason='typed profile stop')
    kwargs = {} if state == 'REVIEW_REQUIRED' else {'anchor': ['authored-family']}
    report = journal.finalize([finalize_query(query_id='q', state=state, **kwargs)])
    assert report['cohort']['state_counts'][state] == 1
    receipt = json.loads((journal.destination / digest('profile') / 'receipt.json').read_text())
    assert receipt['status'] == 'COMPLETED'
    assert report['costs']['metrics']['model_calls']['value'] == 0
    assert not report['protected_evaluation_authorized']


def test_failed_extraction_cannot_be_relabelled_empty(tmp_path):
    journal = stopped(tmp_path, 'failed')
    for stage in journal.slots:
        if stage != 'profile':
            journal.skip(stage, reason='typed profile stop')
    with pytest.raises(InputBoundaryError, match='contradicts typed'):
        journal.finalize([finalize_query(query_id='q', state='PROFILE_EMPTY', anchor=[])])


def test_retrieval_after_review_stop_cannot_reconcile(tmp_path):
    journal = stopped(tmp_path, 'review')
    for stage in journal.slots:
        if stage == 'embedding':
            journal.execute(stage, lambda: ({'authored': True}, {key: 0 for key in METRICS}))
        elif stage != 'profile':
            journal.skip(stage, reason='typed profile stop')
    with pytest.raises(InputBoundaryError, match='stopped profile'):
        journal.finalize([finalize_query(query_id='q', state='REVIEW_REQUIRED')])


def test_modified_typed_output_rejected_by_seal(tmp_path):
    journal = stopped(tmp_path, 'failed')
    for stage in journal.slots:
        if stage != 'profile':
            journal.skip(stage, reason='typed profile stop')
    output_path = journal.destination / digest('profile') / 'output.json'
    output = json.loads(output_path.read_text())
    output['decision'] = 'PROFILE_EMPTY_FALLBACK_REQUIRED'
    output_path.write_text(json.dumps(output))
    with pytest.raises(InputBoundaryError, match='output bytes changed'):
        journal.finalize([finalize_query(query_id='q', state='PROFILE_EMPTY', anchor=[])])
