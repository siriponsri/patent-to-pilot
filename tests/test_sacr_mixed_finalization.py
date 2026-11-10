import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from test_sacr_controller import setup, adapter
from test_sacr_embedding_inputs import generated
from test_sacr_embedding_controller import fake_encoder
from test_sacr_retrieval_controller import index_inputs, make_index


def test_ready_and_missing_remain_in_same_denominator(tmp_path):
    p, raw = index_inputs()
    index = make_index(p, raw)
    controller = setup(tmp_path, missing=True, index_manifest=raw)
    controller.profile('q', adapter)
    for kind in ('generic', 'selective'):
        generated(controller, kind)
    controller.embed('q', fake_encoder)
    controller.acquire('q', index, p['eligible'])
    controller.select('q', index, p['eligible'])
    controller.profile('missing', lambda *_: pytest.fail('missing profile dispatched'))
    for stage in ('generic', 'selective', 'embedding', 'acquisition', 'selection'):
        controller.journal.skip('missing-' + stage, reason='bound source missing')
    report = controller.finalize_mixed(index, {'q': p['eligible'], 'missing': None})
    assert report['cohort']['queries'] == 2
    assert report['cohort']['state_counts']['READY'] == 1
    assert report['cohort']['state_counts']['MISSING_INPUT'] == 1
    outcomes = json.loads((controller.journal.destination / 'outcomes.json').read_text())
    assert outcomes[1]['rankings'] == {arm: [] for arm in ('G/G', 'G/L', 'I/G', 'I/L')}


def test_profile_review_makes_entire_cohort_unscorable(tmp_path):
    controller = setup(tmp_path)
    def work(q, source):
        profile, metrics = adapter(q, source)
        profile['unknowns'] = [{'description': 'authored uncertainty', 'reason': 'ambiguity'}]
        return profile, metrics
    controller.profile('q', work)
    for stage in ('generic', 'selective', 'embedding', 'acquisition', 'selection'):
        controller.journal.skip(stage, reason='profile review required')
    report = controller.finalize_mixed(None, {'q': None})
    assert not report['cohort']['scorable']
    assert report['cohort']['state_counts']['REVIEW_REQUIRED'] == 1


def test_embedding_failure_kept_with_unknown_costs(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    for kind in ('generic', 'selective'):
        generated(controller, kind)
    def fail(*_):
        raise RuntimeError('authored encoder failure')
    with pytest.raises(RuntimeError):
        controller.embed('q', fail)
    for stage in ('acquisition', 'selection'):
        controller.journal.skip(stage, reason='embedding failed')
    report = controller.finalize_mixed(None, {'q': None})
    assert not report['cohort']['scorable']
    assert report['cohort']['state_counts']['RETRIEVAL_FAILED'] == 1
    assert report['costs']['metrics']['embedding_texts']['value'] is None


def test_unsealed_attempt_never_assumed_failed(tmp_path):
    controller = setup(tmp_path)
    controller.journal._reserve('profile')
    with pytest.raises(InputBoundaryError, match='unsealed'):
        controller.finalize_mixed(None, {'q': None})
    assert not (controller.journal.destination / digest('profile') / 'receipt.json').exists()


def test_no_invented_anchor_for_completed_extraction_failure(tmp_path):
    controller = setup(tmp_path)
    def fail(q, source):
        profile, metrics = adapter(q, source)
        profile.update(blocks=[], extraction_status='failed', failure_reasons=['authored abstention'])
        return profile, metrics
    controller.profile('q', fail)
    for stage in ('generic', 'selective', 'embedding', 'acquisition', 'selection'):
        controller.journal.skip(stage, reason='profile unusable')
    with pytest.raises(InputBoundaryError, match='bound original anchor'):
        controller.finalize_mixed(None, {'q': None})
    assert not (controller.journal.destination / 'outcomes.json').exists()
