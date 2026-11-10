import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from test_sacr_controller import setup
from test_sacr_embedding_controller import fake_encoder
from test_sacr_generated_view_controller import evidence
from test_sacr_quote_profile import proposal
from test_sacr_retrieval_controller import index_inputs, make_index


def profile_evidence(controller, *, state='ready'):
    p = proposal()
    p['query_id'] = 'q'
    if state == 'review':
        p['unknowns'] = [{'description': 'authored uncertainty', 'reason': 'ambiguity'}]
    if state == 'empty':
        p['blocks'] = []
    if state == 'failed':
        p.update(blocks=[], extraction_status='failed', failure_reasons=['authored abstention'])
    text = '{bad' if state == 'malformed' else json.dumps(p)
    raw, identity, costs = evidence(controller, 'profile', text=text,
                                    status='NO_EOS' if state == 'non_eos' else 'EOS_COMPLETE')
    return raw, identity, costs


def test_generated_profile_through_complete_six_stage_finalization(tmp_path):
    p, raw = index_inputs()
    controller = setup(tmp_path, index_manifest=raw)
    index = make_index(p, raw)
    supplied = profile_evidence(controller)
    output = controller.generated_profile('q', lambda *_: supplied)
    assert output['format'] == 'sacr-profile-stage-v2'
    assert output['alignment']['resolved_references'] == 3
    assert output['generation_artifact_utf8'].encode() == supplied[0]
    for kind in ('generic', 'selective'):
        controller.generated_views('q', kind, lambda *_: evidence(controller, kind))
    controller.embed('q', fake_encoder)
    controller.acquire('q', index, p['eligible'])
    controller.select('q', index, p['eligible'])
    report = controller.finalize_mixed(index, {'q': p['eligible']})
    assert report['cohort']['state_counts']['READY'] == 1
    assert report['costs']['metrics']['model_calls']['value'] == 3
    assert report['costs']['metrics']['input_tokens']['value'] == 9
    assert report['costs']['metrics']['output_tokens']['value'] == 6


@pytest.mark.parametrize('state', ['review', 'empty', 'failed'])
def test_valid_stop_profiles_cannot_dispatch_views(tmp_path, state):
    controller = setup(tmp_path)
    output = controller.generated_profile('q', lambda *_: profile_evidence(controller, state=state))
    assert output['decision'] != 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING'
    with pytest.raises(InputBoundaryError):
        controller.generated_views('q', 'generic', lambda *_: pytest.fail('stopped profile dispatched'))
    assert not (controller.journal.destination / digest('generic')).exists()
    if state == 'review':
        for stage in ('generic', 'selective', 'embedding', 'acquisition', 'selection'):
            controller.journal.skip(stage, reason='review required')
        assert not controller.finalize_mixed(None, {'q': None})['cohort']['scorable']


@pytest.mark.parametrize('state', ['malformed', 'non_eos'])
def test_unusable_profile_seals_original_failure_and_costs(tmp_path, state):
    controller = setup(tmp_path)
    supplied = profile_evidence(controller, state=state)
    with pytest.raises(InputBoundaryError):
        controller.generated_profile('q', lambda *_: supplied)
    receipt, output = controller.journal.read_terminal_attempt('profile')
    assert receipt['status'] == 'FAILED'
    assert output['generation_artifact_utf8'].encode() == supplied[0]
    event = json.loads((controller.journal.destination / digest('profile') / 'event.json').read_bytes())
    assert event['metrics']['model_calls'] == 1
    with pytest.raises(FileExistsError):
        controller.generated_profile('q', lambda *_: pytest.fail('retry'))


@pytest.mark.parametrize('changed', ['source', 'artifact', 'alignment', 'cost'])
def test_bound_identity_and_replay_tampering_refused(tmp_path, changed):
    controller = setup(tmp_path)
    raw, identity, costs = profile_evidence(controller)
    if changed in ('source', 'artifact'):
        identity['source_sha256' if changed == 'source' else 'artifact_sha256'] = '0' * 64
        with pytest.raises(InputBoundaryError):
            controller.generated_profile('q', lambda *_: (raw, identity, costs))
        return
    if changed == 'alignment':
        from patent_to_pilot.research.sacr_generated_profile import generated_profile_result
        source = controller._sources['q']
        output = generated_profile_result(raw, identity, execution=controller.journal.execution,
                                          attempt_id='profile', query_id='q', source=source, metrics=costs)
        output['alignment']['resolved_references'] += 1
        controller.journal.execute('profile', lambda: (output, costs))
    else:
        controller.generated_profile('q', lambda *_: (raw, identity, costs))
        path = controller.journal.destination / digest('profile') / 'event.json'
        path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(InputBoundaryError):
        controller.generated_views('q', 'generic', lambda *_: pytest.fail('changed evidence dispatched'))
    assert not (controller.journal.destination / digest('generic')).exists()


def test_missing_source_does_not_dispatch_generated_profile(tmp_path):
    controller = setup(tmp_path, missing=True)
    output = controller.generated_profile('missing', lambda *_: pytest.fail('missing dispatched'))
    assert output['decision'] == 'MISSING_INPUT'
    receipt, _ = controller.journal.read_terminal_attempt('missing-profile')
    assert receipt['status'] == 'SKIPPED'
