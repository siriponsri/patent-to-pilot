import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from test_sacr_controller import setup, adapter
from test_sacr_embedding_controller import fake_encoder
from test_sacr_generated_view_controller import evidence
from test_sacr_profile import SOURCE
from test_sacr_retrieval_controller import index_inputs, make_index


def prepare(tmp_path, *, missing=False, review=None):
    p, raw = index_inputs()
    index = make_index(p, raw)
    controller = setup(tmp_path, missing=missing, index_manifest=raw)
    controller.profile('q', adapter)
    for kind in ('generic', 'selective'):
        text = None
        if kind == review:
            text = json.dumps({'views': [SOURCE + ' Novelmechanism.']} if kind == 'generic' else
                              {'selective_abstract': SOURCE + ' Novelmechanism.'})
        controller.generated_views('q', kind, lambda *_: evidence(controller, kind, text=text))
    return controller, index, p


def test_v3_ready_and_missing_full_cohort_finalizes(tmp_path):
    controller, index, p = prepare(tmp_path, missing=True)
    controller.embed('q', fake_encoder)
    controller.acquire('q', index, p['eligible'])
    controller.select('q', index, p['eligible'])
    controller.profile('missing', lambda *_: pytest.fail('missing dispatched'))
    for stage in ('generic', 'selective', 'embedding', 'acquisition', 'selection'):
        controller.journal.skip('missing-' + stage, reason='source missing')
    report = controller.finalize_mixed(index, {'q': p['eligible'], 'missing': None})
    assert report['cohort']['queries'] == 2
    assert report['cohort']['state_counts']['READY'] == 1
    assert report['cohort']['state_counts']['MISSING_INPUT'] == 1
    assert report['costs']['metrics']['model_calls']['value'] == 2
    assert report['costs']['metrics']['input_tokens']['value'] == 6
    assert report['costs']['metrics']['output_tokens']['value'] == 4
    assert not report['protected_evaluation_authorized']


@pytest.mark.parametrize('kind', ['generic', 'selective'])
def test_v3_review_stops_whole_cohort(tmp_path, kind):
    controller, _, _ = prepare(tmp_path, review=kind)
    for stage in ('embedding', 'acquisition', 'selection'):
        controller.journal.skip(stage, reason='view requires review')
    report = controller.finalize_mixed(None, {'q': None})
    assert report['cohort']['state_counts']['REVIEW_REQUIRED'] == 1
    assert not report['cohort']['scorable']


def test_v3_retrieval_failure_preserves_unknown_cost(tmp_path):
    controller, _, _ = prepare(tmp_path)
    def fail(*_):
        raise RuntimeError('authored encoder failure')
    with pytest.raises(RuntimeError):
        controller.embed('q', fail)
    for stage in ('acquisition', 'selection'):
        controller.journal.skip(stage, reason='encoder failed')
    report = controller.finalize_mixed(None, {'q': None})
    assert report['cohort']['state_counts']['RETRIEVAL_FAILED'] == 1
    assert not report['cohort']['scorable']
    assert report['costs']['metrics']['model_calls']['value'] is None
    assert report['costs']['metrics']['model_calls']['observed_lower_bound'] == 2


def test_v3_changed_cost_event_cannot_finalize_review(tmp_path):
    controller, _, _ = prepare(tmp_path, review='generic')
    for stage in ('embedding', 'acquisition', 'selection'):
        controller.journal.skip(stage, reason='review required')
    path = controller.journal.destination / digest('generic') / 'event.json'
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(InputBoundaryError, match='event differs'):
        controller.finalize_mixed(None, {'q': None})
    assert not (controller.journal.destination / 'completion.json').exists()
