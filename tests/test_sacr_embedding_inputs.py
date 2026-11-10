import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_view_result import view_result
from test_sacr_controller import setup, adapter
from test_sacr_profile import SOURCE
from test_sacr_view_controller import metrics


def generated(controller, kind, text=SOURCE):
    response = {'views': [text]} if kind == 'generic' else {'selective_abstract': text}
    return controller.views('q', kind, lambda *_: (json.dumps(response).encode(), metrics()))


def test_both_arms_replayed_and_degenerate_generation_disclosed(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    for kind in ('generic', 'selective'):
        generated(controller, kind)
    result = controller.embedding_inputs('q')
    for arm in result['arms'].values():
        assert arm['views'][0] == SOURCE
        assert arm['no_generated_view_retained']  # duplicate source, not a new useful view
    assert result['fidelity_review'] == 'REQUIRED'
    result['components']['rows'].clear()
    assert controller.embedding_inputs('q')['components']['rows']
    assert not (controller.journal.destination / digest('embedding')).exists()


@pytest.mark.parametrize('case', ['unstarted', 'review', 'failed', 'changed'])
def test_incomplete_or_unusable_views_cannot_prepare_embedding(case, tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    generated(controller, 'generic')
    if case == 'review':
        generated(controller, 'selective', SOURCE + ' Novelmechanism.')
    elif case == 'failed':
        with pytest.raises(InputBoundaryError):
            controller.views('q', 'selective', lambda *_: (b'invalid', metrics()))
    elif case == 'changed':
        generated(controller, 'selective')
        path = controller.journal.destination / digest('generic') / 'output.json'
        path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(InputBoundaryError):
        controller.embedding_inputs('q')
    assert not (controller.journal.destination / digest('embedding')).exists()


def test_even_sealed_invented_screening_decision_fails_replay(tmp_path):
    controller = setup(tmp_path)
    profile = controller.profile('q', adapter)
    generated(controller, 'selective')
    fake = view_result(json.dumps({'views': [SOURCE + ' Novelmechanism.']}).encode(),
                       kind='generic', profile_output=profile, maximum_bytes=65536, maximum_views=3)
    fake['decision'] = 'VIEWS_SCREENED_FIDELITY_PENDING'
    controller.journal.execute('generic', lambda: (fake, metrics()))
    with pytest.raises(InputBoundaryError, match='evidence changed'):
        controller.embedding_inputs('q')


def test_rejected_proposal_retained_in_private_evidence_but_not_views(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    output = generated(controller, 'generic', 'Reduce reverse flow of liquid.')
    generated(controller, 'selective')
    assert output['screened']['proposals'][0]['status'] == 'REJECTED'
    assert 'Reduce reverse flow of liquid.' in output['response_utf8']
    result = controller.embedding_inputs('q')
    assert result['arms']['generic']['views'] == (SOURCE,)
    assert result['arms']['generic']['no_generated_view_retained']
