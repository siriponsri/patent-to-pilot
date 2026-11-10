import copy
import hashlib
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_generated_view import generated_view_result
from test_sacr_controller import setup, adapter
from test_sacr_profile import SOURCE
from test_sacr_view_controller import metrics


def evidence(controller, kind, *, status='EOS_COMPLETE', text=None):
    text = text if text is not None else json.dumps(
        {'views': [SOURCE]} if kind == 'generic' else {'selective_abstract': SOURCE})
    record = dict(status=status, text=text, model_calls=1, input_tokens=3, output_tokens=2,
                  response_sha256=hashlib.sha256(text.encode()).hexdigest(), retry=False)
    raw = (json.dumps(record, indent=2) + '\n').encode()
    execution = controller.journal.execution
    identity = dict(query_id='q', kind=kind, run_id=execution['run_id'], attempt_id=kind,
                    source_sha256=hashlib.sha256(SOURCE.encode()).hexdigest(),
                    generator_manifest_sha256=execution['identities']['generator_manifest'],
                    prompt_manifest_sha256=execution['identities']['prompt_manifest'],
                    artifact_sha256=hashlib.sha256(raw).hexdigest())
    costs = metrics()
    costs.update(model_calls=1, input_tokens=3, output_tokens=2)
    return raw, identity, costs


def prepared(tmp_path):
    controller = setup(tmp_path)
    controller.profile('q', adapter)
    return controller


def test_two_arms_bind_original_artifact_and_replay_without_calls(tmp_path):
    controller = prepared(tmp_path)
    for kind in ('generic', 'selective'):
        original = evidence(controller, kind)
        def work(*args):
            assert len(args) == (2 if kind == 'generic' else 3)
            assert args[:2] == ('q', SOURCE)
            return original
        result = controller.generated_views('q', kind, work)
        assert result['format'] == 'sacr-view-stage-v3'
        assert result['generation_artifact_utf8'].encode() == original[0]
        assert result['generation']['record']['model_calls'] == 1
        with pytest.raises(FileExistsError):
            controller.generated_views('q', kind, lambda *_: pytest.fail('repeat call'))
    first = controller.embedding_inputs('q')
    assert first == controller.embedding_inputs('q')
    assert all(arm['views'][0] == SOURCE for arm in first['arms'].values())


@pytest.mark.parametrize('field', ['query_id', 'kind', 'run_id', 'attempt_id', 'source_sha256',
                                  'generator_manifest_sha256', 'prompt_manifest_sha256', 'artifact_sha256'])
def test_wrong_binding_fails_inside_reserved_attempt(tmp_path, field):
    controller = prepared(tmp_path)
    raw, identity, costs = evidence(controller, 'generic')
    identity[field] = 'wrong'
    with pytest.raises(InputBoundaryError):
        controller.generated_views('q', 'generic', lambda *_: (raw, identity, costs))
    receipt, _ = controller.journal.read_terminal_attempt('generic')
    assert receipt['status'] == 'FAILED'
    assert not (controller.journal.destination / digest('embedding')).exists()


@pytest.mark.parametrize('kind', ['generic', 'selective'])
@pytest.mark.parametrize('case', ['non_eos', 'malformed', 'cost_mismatch', 'infrastructure'])
def test_unusable_generation_never_becomes_successful_empty_view(tmp_path, kind, case):
    controller = prepared(tmp_path)
    raw, identity, costs = evidence(controller, kind, status='NO_EOS' if case == 'non_eos' else 'EOS_COMPLETE',
                                    text='{bad' if case == 'malformed' else None)
    if case == 'cost_mismatch':
        costs['model_calls'] = 0
    def work(*_):
        if case == 'infrastructure':
            raise RuntimeError('authored failure')
        return raw, identity, costs
    with pytest.raises(RuntimeError if case == 'infrastructure' else InputBoundaryError):
        controller.generated_views('q', kind, work)
    receipt, output = controller.journal.read_terminal_attempt(kind)
    assert receipt['status'] == 'FAILED' and output is None
    with pytest.raises(InputBoundaryError):
        controller.embedding_inputs('q')


def test_sealed_output_cannot_disagree_with_sealed_cost_event(tmp_path):
    controller = prepared(tmp_path)
    profile = controller.journal.read_completed_output('profile')
    raw, identity, costs = evidence(controller, 'generic')
    expected = {key: value for key, value in identity.items() if key != 'artifact_sha256'}
    output = generated_view_result(raw, identity, expected_identity=expected, metrics=costs,
                                   profile_output=profile, limits=controller.journal.execution['limits'])
    wrong = copy.deepcopy(costs)
    wrong['input_tokens'] += 1
    controller.journal.execute('generic', lambda: (output, wrong))
    controller.generated_views('q', 'selective', lambda *_: evidence(controller, 'selective'))
    with pytest.raises(InputBoundaryError, match='costs disagree'):
        controller.embedding_inputs('q')


def test_event_byte_mutation_blocks_replay(tmp_path):
    controller = prepared(tmp_path)
    for kind in ('generic', 'selective'):
        controller.generated_views('q', kind, lambda *_: evidence(controller, kind))
    path = controller.journal.destination / digest('generic') / 'event.json'
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(InputBoundaryError, match='event differs'):
        controller.embedding_inputs('q')
