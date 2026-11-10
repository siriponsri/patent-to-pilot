import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_outcomes import METRICS
from test_sacr_controller import setup, adapter
from test_sacr_profile import SOURCE


def metrics():
    return {key: 0 for key in METRICS}


@pytest.mark.parametrize('state', ['unstarted', 'empty', 'failed', 'review', 'exception', 'changed'])
def test_invalid_dependency_stops_before_view_adapter_or_reservation(tmp_path, state):
    controller = setup(tmp_path)
    def work(q, source):
        if state == 'exception':
            raise RuntimeError('authored failure')
        p, costs = adapter(q, source)
        if state in ('empty', 'failed'):
            p['blocks'] = []
            if state == 'failed':
                p['extraction_status'] = 'failed'
                p['failure_reasons'] = ['authored abstention']
        if state == 'review':
            p['unknowns'] = [{'description': 'authored uncertainty', 'reason': 'ambiguity'}]
        return p, costs
    if state == 'exception':
        with pytest.raises(RuntimeError):
            controller.profile('q', work)
    elif state != 'unstarted':
        controller.profile('q', work)
    if state == 'changed':
        path = controller.journal.destination / digest('profile') / 'output.json'
        path.write_bytes(path.read_bytes() + b' ')
    for kind in ('generic', 'selective'):
        with pytest.raises(InputBoundaryError):
            controller.views('q', kind, lambda *_: pytest.fail('dependent adapter called'))
        assert not (controller.journal.destination / digest(kind)).exists()


def test_generic_never_receives_profile_and_keeps_anchor(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    def generic(q, source):
        assert q == 'q' and source == SOURCE
        return json.dumps({'views': [source]}).encode(), metrics()
    result = controller.views('q', 'generic', generic)
    assert result['screened']['views'] == [SOURCE]
    assert result['screened']['proposals'][0]['duplicate']
    assert result['decision'] == 'VIEWS_SCREENED_FIDELITY_PENDING'
    with pytest.raises(FileExistsError):
        controller.views('q', 'generic', generic)


def test_selective_gets_detached_profile_and_compact_proposal(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    def selective(q, source, profile):
        assert profile['query_id'] == q and source == SOURCE
        profile['blocks'].clear()
        return json.dumps({'selective_abstract': source}).encode(), metrics()
    result = controller.views('q', 'selective', selective)
    assert len(result['screened']['proposals']) == 2
    saved = controller.journal.read_completed_output('profile')
    assert len(saved['profile']['blocks']) == 1


def test_novel_vocabulary_remains_review_required(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    result = controller.views('q', 'generic', lambda *_: (
        json.dumps({'views': [SOURCE + ' Novelmechanism.']}).encode(), metrics()))
    assert result['decision'] == 'REVIEW_REQUIRED'
    assert result['screened']['views'] == [SOURCE]
    assert not (controller.journal.destination / digest('embedding')).exists()


def test_malformed_view_is_failed_without_retry(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    with pytest.raises(InputBoundaryError):
        controller.views('q', 'generic', lambda *_: (b'{bad', metrics()))
    path = controller.journal.destination / digest('generic') / 'receipt.json'
    assert json.loads(path.read_text())['status'] == 'FAILED'
