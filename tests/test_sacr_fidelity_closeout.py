import importlib.util
import json
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


def test_tampered_assessment_does_not_become_rejected_family(tmp_path):
    state = fixture(tmp_path)
    root = tmp_path / 'out/attempt/profiles/000'
    record = {'status': 'INPUT_LIMIT', 'model_calls': 0, 'input_tokens': 9000,
              'output_tokens': 0, 'text': None, 'retry': False}
    write(root / 'profile/generation.json', record)
    write(root / 'assessment.json', {'generation': {'artifact_sha256': '0' * 64, 'record': record}})
    with pytest.raises(ValueError, match='bound'):
        closeout.summarize(tmp_path, state)
