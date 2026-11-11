import importlib.util
import json
import hashlib
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / 'scripts/healthtech/summarize_sacr_fidelity_attempt.py'
spec = importlib.util.spec_from_file_location('fidelity_closeout', PATH)
closeout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closeout)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def fixture(job):
    state = {'Running': False, 'Status': 'exited', 'ExitCode': 137}
    write(job / 'terminal.json', {'container_state': state, 'wall_seconds': 7000,
        'returncode': 137, 'status': 'TIMEOUT', 'observed_cgroup_peak_bytes': 1000})
    write(job / 'out/attempt/declaration.json', {'maximum_calls': 100})
    return state


def test_interrupted_reservation_is_unknown_not_zero_cost(tmp_path):
    state = fixture(tmp_path)
    write(tmp_path / 'out/attempt/profiles/000/profile/reservation.json', {'status': 'RESERVED'})
    result = closeout.summarize(tmp_path, state)
    assert result['status'] == 'INCOMPLETE_PROFILE_COHORT_NO_PASS'
    assert result['unknown_execution_attempts'] == 1 and result['not_started'] == 99
    assert result['cost_counts_are_lower_bounds'] and result['gpu_charge_seconds'] == 7000


def test_live_or_disagreeing_terminal_cannot_close_out(tmp_path):
    state = fixture(tmp_path)
    for override in ({'Running': True}, {'ExitCode': 0}):
        with pytest.raises(ValueError):
            closeout.summarize(tmp_path, {**state, **override})


def test_preparation_without_model_reservation_is_distinct(tmp_path):
    state = fixture(tmp_path)
    write(tmp_path / 'out/attempt/profiles/000/input.json', {})
    result = closeout.summarize(tmp_path, state)
    assert result['normal_return_states'] == {'PREPARATION_ONLY': 1}
    assert result['unknown_execution_attempts'] == 0
    assert result['status'] == 'INCOMPLETE_PROFILE_COHORT_NO_PASS'


def test_selected_closeout_counts_unknown_and_preserves_full_sample(tmp_path):
    state=fixture(tmp_path)
    state.update(StartedAt='start',FinishedAt='finish')
    terminal=json.loads((tmp_path/'terminal.json').read_bytes());terminal['container_state']=state
    write(tmp_path/'terminal.json',terminal)
    root=tmp_path/'canonical/attempt';write(root/'declaration.json',{'maximum_calls':54})
    write(tmp_path/'declaration.json',{'maximum_calls':54})
    write(root/'profiles/046/profile/reservation.json',{'status':'RESERVED'})
    args=dict(output_root=root,selected_indices=list(range(46,100)),expected_declaration_sha256=closeout.digest(root/'declaration.json'))
    result=closeout.summarize(tmp_path,state,**args)
    assert result['unknown_execution_attempts']==1 and result['not_started']==53
    assert result['original_sample_queries']==100 and result['planned_queries']==54
    assert result['gpu_charge_seconds']==7000 and result['cost_counts_are_lower_bounds']
    with pytest.raises(ValueError,match='terminal identity'):
        closeout.summarize(tmp_path,{**state,'FinishedAt':'different'},**args)
    write(root/'profiles/045/input.json',{})
    with pytest.raises(ValueError,match='non-prefix'):
        closeout.summarize(tmp_path,state,**args)


def test_selected_declaration_reserialization_is_bound_by_values_and_original_bytes(tmp_path):
    state=fixture(tmp_path);state.update(StartedAt='start',FinishedAt='finish')
    terminal=json.loads((tmp_path/'terminal.json').read_bytes());terminal['container_state']=state;write(tmp_path/'terminal.json',terminal)
    root=tmp_path/'canonical/attempt';write(root/'declaration.json',{'maximum_calls':54})
    (tmp_path/'declaration.json').write_bytes(b'{\r\n  "maximum_calls": 54\r\n}\r\n')
    args=dict(output_root=root,selected_indices=list(range(46,100)),expected_declaration_sha256=closeout.digest(tmp_path/'declaration.json'))
    result=closeout.summarize(tmp_path,state,**args)
    assert result['runtime_declaration_sha256']!=result['input_declaration_sha256']
    write(root/'declaration.json',{'maximum_calls':53})
    with pytest.raises(ValueError,match='declaration not bound'):closeout.summarize(tmp_path,state,**args)


def test_tampered_assessment_does_not_become_rejected_family(tmp_path):
    state = fixture(tmp_path)
    root = tmp_path / 'out/attempt/profiles/000'
    record = {'status': 'INPUT_LIMIT', 'model_calls': 0, 'input_tokens': 9000,
              'output_tokens': 0, 'text': None, 'retry': False}
    write(root / 'profile/generation.json', record)
    write(root / 'assessment.json', {'generation': {'artifact_sha256': '0' * 64, 'record': record}})
    with pytest.raises(ValueError, match='bound'):
        closeout.summarize(tmp_path, state)


def normal_record(**overrides):
    return {'status': 'EOS_COMPLETE', 'model_calls': 1, 'input_tokens': 100,
            'output_tokens': 2, 'text': '{}', 'retry': False,
            'response_sha256': hashlib.sha256(b'{}').hexdigest(), **overrides}


@pytest.mark.parametrize('overrides', [
    {'output_tokens': 0}, {'status': 'OUTPUT_LIMIT'}, {'input_tokens': 8193},
    {'status': 'RESPONSE_BYTE_LIMIT'}, {'output_tokens': 4097},
])
def test_impossible_normal_records_are_not_counted(tmp_path, overrides):
    state = fixture(tmp_path)
    write(tmp_path / 'out/attempt/profiles/000/profile/generation.json', normal_record(**overrides))
    with pytest.raises(ValueError):
        closeout.summarize(tmp_path, state)


def test_full_cohort_counts_costs_but_never_claims_semantic_pass(tmp_path):
    state = {'Running': False, 'Status': 'exited', 'ExitCode': 0}
    root = tmp_path / 'out/attempt'
    write(root / 'declaration.json', {'maximum_calls': 100})
    record = normal_record()
    for i in range(100):
        attempt = root / f'profiles/{i:03d}'
        generated = attempt / 'profile/generation.json'
        write(generated, record)
        write(attempt / 'assessment.json', {'generation': {
            'artifact_sha256': closeout.digest(generated), 'record': record},
            'metrics': {k: record[k] for k in ('model_calls', 'input_tokens', 'output_tokens')},
            'status': 'REJECTED_GENERATED_FAMILY'})
    write(root / 'terminal.json', {'queries': 100, 'status': 'PROFILE_BATCH_COMPLETED_FIDELITY_PENDING'})
    write(tmp_path / 'terminal.json', {'container_state': state, 'wall_seconds': 6000,
        'returncode': 0, 'status': 'PROFILE_BATCH_COMPLETE_FIDELITY_PENDING',
        'observed_cgroup_peak_bytes': 1000, 'completion_sha256': closeout.digest(root / 'terminal.json')})
    result = closeout.summarize(tmp_path, state)
    assert result['status'] == 'COMPLETE_PROFILE_COHORT_FIDELITY_PENDING'
    assert result['known_model_calls'] == 100 and result['known_input_tokens'] == 10000
    assert result['known_output_tokens'] == 200 and result['not_started'] == 0
    assert result['assessment_states'] == {'REJECTED_GENERATED_FAMILY': 100}
    assert result['semantic_fidelity'] == 'NOT_ASSESSED'
