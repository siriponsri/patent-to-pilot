import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_profile_result import profile_result
from test_sacr_anchor import factory
from test_sacr_controller import setup, adapter
from test_sacr_embedding_controller import fake_encoder
from test_sacr_generated_profile_controller import profile_evidence
from test_sacr_generated_view_controller import evidence
from test_sacr_profile import SOURCE
from test_sacr_retrieval_controller import index_inputs, make_index


def required(tmp_path):
    p, raw = index_inputs()
    controller = setup(tmp_path, index_manifest=raw, require_generation=True,
                       anchor_factory=lambda data: factory(data, mask=p['eligible']))
    return controller, make_index(p, raw), p


def test_v3_requires_anchor_before_reserving_run(tmp_path):
    with pytest.raises(InputBoundaryError):
        setup(tmp_path, require_generation=True)
    assert not (tmp_path / 'run').exists()


@pytest.mark.parametrize('stage', ['profile', 'generic', 'selective'])
def test_legacy_adapters_refused_before_reservation(tmp_path, stage):
    controller, _, _ = required(tmp_path)
    if stage != 'profile':
        controller.generated_profile('q', lambda *_: profile_evidence(controller))
    with pytest.raises(InputBoundaryError, match='requires generation evidence adapters'):
        if stage == 'profile':
            controller.profile('q', lambda *_: pytest.fail('legacy dispatched'))
        else:
            controller.views('q', stage, lambda *_: pytest.fail('legacy dispatched'))
    assert not (controller.journal.destination / digest(stage)).exists()


def test_low_level_untyped_completion_cannot_bypass_contract(tmp_path):
    controller, _, _ = required(tmp_path)
    profile, costs = adapter('q', SOURCE)
    output = profile_result(profile, source=SOURCE, query_id='q')
    with pytest.raises(InputBoundaryError, match='requires typed generation evidence'):
        controller.journal.execute('profile', lambda: (output, costs))
    receipt, _ = controller.journal.read_terminal_attempt('profile')
    assert receipt['status'] == 'FAILED'


def test_v3_complete_authored_run_has_no_legacy_generation(tmp_path):
    controller, index, p = required(tmp_path)
    controller.generated_profile('q', lambda *_: profile_evidence(controller))
    for kind in ('generic', 'selective'):
        controller.generated_views('q', kind, lambda *_: evidence(controller, kind))
    controller.embed('q', fake_encoder)
    controller.acquire('q', index, p['eligible'])
    controller.select('q', index, p['eligible'])
    report = controller.finalize_mixed(index, {'q': p['eligible']})
    assert report['costs']['metrics']['model_calls']['value'] == 3
    assert report['cohort']['state_counts']['READY'] == 1
    assert report['anchor_reuse']['queries'] == 0
    assert not report['protected_evaluation_authorized']


@pytest.mark.parametrize('state,expected', [('empty', 'PROFILE_EMPTY'), ('failed', 'PROFILE_FAILED'),
                                         ('malformed', 'PROFILE_FAILED')])
def test_v3_profile_stop_uses_only_bound_original_anchor(tmp_path, state, expected):
    controller, index, p = required(tmp_path)
    if state == 'malformed':
        with pytest.raises(InputBoundaryError):
            controller.generated_profile('q', lambda *_: profile_evidence(controller, state=state))
    else:
        controller.generated_profile('q', lambda *_: profile_evidence(controller, state=state))
    for stage in ('generic', 'selective', 'embedding', 'acquisition', 'selection'):
        controller.journal.skip(stage, reason='profile unusable')
    report = controller.finalize_mixed(index, {'q': p['eligible']})
    assert report['cohort']['state_counts'][expected] == 1
    assert report['anchor_reuse']['queries'] == 1
    assert report['costs']['metrics']['model_calls']['value'] == 1


def test_changed_execution_cannot_downgrade_adapter_requirement(tmp_path):
    controller, _, _ = required(tmp_path)
    controller.journal.execution['format'] = 'sacr-dev-execution-v2'
    with pytest.raises(InputBoundaryError):
        controller.profile('q', lambda *_: pytest.fail('downgraded adapter dispatched'))
    assert not (controller.journal.destination / digest('profile')).exists()
