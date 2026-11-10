"""Read-only aggregate closeout of a terminal native fidelity attempt.

No generation, retry, output repair, query text or identifiers in the report.
The supplied Docker observation must be freshly captured by the operator.
Run with PYTHONPATH pointing to the hash-verified source package from the run.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_generation_receipt import bind_generation_record
from patent_to_pilot.research.mtm_runtime import decode_json


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(job, observed_state, *, output_root=None, selected_indices=None, expected_declaration_sha256=None):
    if observed_state.get('Running') is not False or observed_state.get('Status') not in ('exited', 'dead'):
        raise ValueError('terminal Docker observation required; never summarize a live run as closed')
    job = Path(job)
    terminal_path = job / 'terminal.json'
    terminal = json.loads(terminal_path.read_bytes())
    if terminal['container_state']['Running'] is not False:
        raise ValueError('supervisor did not verify termination')
    if terminal['container_state']['ExitCode'] != observed_state['ExitCode']:
        raise ValueError('terminal observations disagree')
    selected = selected_indices is not None
    indices = list(range(100)) if not selected else list(selected_indices)
    if (not indices or any(type(i) is not int or not 0 <= i < 100 for i in indices) or
            sorted(set(indices)) != indices):
        raise ValueError('invalid declared selection')
    if selected and (any(not observed_state.get(k) or terminal['container_state'].get(k) != observed_state[k]
                         for k in ('StartedAt', 'FinishedAt')) or output_root is None):
        raise ValueError('selected closeout requires matching full terminal identity and output root')
    wall = terminal['wall_seconds']
    if type(wall) not in (int, float) or not 0 <= wall < float('inf'):
        raise ValueError('unknown supervisor cost; cannot reset ledger')
    root = Path(output_root) if selected else job / 'out/attempt'
    if selected and digest(root / 'declaration.json') != expected_declaration_sha256:
        raise ValueError('selected runtime declaration not bound')
    declaration = json.loads((root / 'declaration.json').read_bytes())
    if declaration['maximum_calls'] != len(indices):
        raise ValueError('unexpected native sample contract')
    profile_root = root / 'profiles'
    attempts = sorted(p for p in profile_root.iterdir() if p.is_dir()) if profile_root.exists() else []
    if [p.name for p in attempts] != [f'{i:03d}' for i in indices[:len(attempts)]] or len(attempts) > len(indices):
        raise ValueError('non-prefix or foreign attempt directory')
    states, assessments = Counter(), Counter()
    known_calls = input_tokens = output_tokens = 0
    unknown_execution = unassessed_completed = 0
    for attempt in attempts:
        generated = attempt / 'profile/generation.json'
        assessment = attempt / 'assessment.json'
        reservation = attempt / 'profile/reservation.json'
        if not generated.exists():
            # A reservation is not proof a model call actually began or ended.
            unknown_execution += int(reservation.exists())
            states['RESERVED_UNKNOWN_EXECUTION' if reservation.exists() else 'PREPARATION_ONLY'] += 1
            continue
        raw = generated.read_bytes()
        record = decode_json(raw)
        if selected:
            if not reservation.exists():
                raise ValueError('normal return lacks generation reservation')
            reserved = decode_json(reservation.read_bytes())
            inp = decode_json((attempt / 'input.json').read_bytes())
            messages_sha = hashlib.sha256(json.dumps(inp['prompt']['messages'], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            if (reserved.get('status') != 'RESERVED' or reserved.get('retry') is not False or
                    reserved.get('limits') != GenerationLimits().__dict__ or reserved.get('messages_sha256') != messages_sha):
                raise ValueError('generation reservation disagrees with retained input')
        bind_generation_record(raw, expected_sha256=digest(generated), limits=GenerationLimits(),
            metrics={key: record[key] for key in ('model_calls', 'input_tokens', 'output_tokens')})
        known_calls += record['model_calls']
        input_tokens += record['input_tokens']
        output_tokens += record['output_tokens']
        states[record['status']] += 1
        if not assessment.exists():
            unassessed_completed += 1
            continue
        result = decode_json(assessment.read_bytes())
        if result['generation']['artifact_sha256'] != digest(generated) or result['generation']['record'] != record:
            raise ValueError('assessment not bound to generation bytes')
        if any(result['metrics'][k] != record[k] for k in ('model_calls', 'input_tokens', 'output_tokens')):
            raise ValueError('assessment cost disagreement')
        if result['status'] not in ('REJECTED_GENERATED_FAMILY', 'STRUCTURAL_RESULT_FIDELITY_PENDING', 'STOP_INPUT_LIMIT_NO_MODEL_CALL'):
            raise ValueError('unknown assessment state')
        assessments[result['status']] += 1
    supervisor_complete = ('EXCEPTION_CLOSED_FIDELITY_PENDING' if indices == [45] else
                           'SELECTED_BATCH_CLOSED_COHORT_INCOMPLETE') if selected else 'PROFILE_BATCH_COMPLETE_FIDELITY_PENDING'
    runtime_complete = ('EXCEPTION_STRUCTURAL_RESULT_FIDELITY_PENDING' if indices == [45] else
                        'SELECTED_PROFILE_BATCH_COMPLETED_COHORT_INCOMPLETE') if selected else 'PROFILE_BATCH_COMPLETED_FIDELITY_PENDING'
    complete = (len(attempts) == len(indices) and sum(assessments.values()) == len(indices) and
                not unknown_execution and not unassessed_completed and
                terminal['returncode'] == 0 and observed_state['ExitCode'] == 0 and
                terminal['status'] == supervisor_complete)
    completion = root / 'terminal.json'
    if complete:
        if not completion.exists() or digest(completion) != terminal['completion_sha256']:
            raise ValueError('runtime completion not bound')
        runtime = json.loads(completion.read_bytes())
        if runtime['queries'] != len(indices) or runtime['status'] != runtime_complete:
            raise ValueError('runtime cohort completion mismatch')
    return {'status': ('COMPLETE_SELECTED_PROFILES_COHORT_NOT_ESTABLISHED' if selected else 'COMPLETE_PROFILE_COHORT_FIDELITY_PENDING') if complete else 'INCOMPLETE_PROFILE_COHORT_NO_PASS',
        'original_sample_queries': 100, 'selected_closeout': selected,
        'planned_queries': len(indices), 'attempt_directories': len(attempts), 'not_started': len(indices) - len(attempts),
        'normal_return_states': dict(states), 'assessment_states': dict(assessments),
        'unassessed_normal_returns': unassessed_completed, 'unknown_execution_attempts': unknown_execution,
        'known_model_calls': known_calls, 'known_input_tokens': input_tokens, 'known_output_tokens': output_tokens,
        'cost_counts_are_lower_bounds': bool(unknown_execution), 'gpu_charge_seconds': wall,
        'observed_cgroup_peak_bytes': terminal['observed_cgroup_peak_bytes'],
        'supervisor_terminal_sha256': digest(terminal_path), 'retry': False,
        'semantic_fidelity': 'NOT_ASSESSED', 'protected_test_access': False,
        'limitation': 'Aggregate byte/cost binding only; not independent execution or semantic attestation'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', type=Path, required=True)
    parser.add_argument('--observed-state', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(args.job, json.loads(args.observed_state.read_bytes())), indent=2))


if __name__ == '__main__':
    main()
