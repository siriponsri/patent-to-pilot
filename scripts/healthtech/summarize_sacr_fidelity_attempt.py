"""Read-only aggregate closeout of a terminal native fidelity attempt.

No generation, retry, output repair, query text or identifiers in the report.
The supplied Docker observation must be freshly captured by the operator.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(job, observed_state):
    if observed_state.get('Running') is not False or observed_state.get('Status') not in ('exited', 'dead'):
        raise ValueError('terminal Docker observation required; never summarize a live run as closed')
    job = Path(job)
    terminal_path = job / 'terminal.json'
    terminal = json.loads(terminal_path.read_bytes())
    if terminal['container_state']['Running'] is not False:
        raise ValueError('supervisor did not verify termination')
    if terminal['container_state']['ExitCode'] != observed_state['ExitCode']:
        raise ValueError('terminal observations disagree')
    wall = terminal['wall_seconds']
    if type(wall) not in (int, float) or not 0 <= wall < float('inf'):
        raise ValueError('unknown supervisor cost; cannot reset ledger')
    root = job / 'out/attempt'
    declaration = json.loads((root / 'declaration.json').read_bytes())
    if declaration['maximum_calls'] != 100:
        raise ValueError('unexpected native sample contract')
    profile_root = root / 'profiles'
    attempts = sorted(p for p in profile_root.iterdir() if p.is_dir()) if profile_root.exists() else []
    if [p.name for p in attempts] != [f'{i:03d}' for i in range(len(attempts))] or len(attempts) > 100:
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
        record = json.loads(generated.read_bytes())
        if record['status'] not in ('EOS_COMPLETE', 'NO_EOS', 'OUTPUT_LIMIT', 'RESPONSE_BYTE_LIMIT', 'INPUT_LIMIT'):
            raise ValueError('not a normally returned generation record')
        if any(type(record[k]) is not int or record[k] < 0 for k in ('model_calls', 'input_tokens', 'output_tokens')):
            raise ValueError('invalid observed costs')
        if record['retry'] is not False:
            raise ValueError('retry present')
        if record['status'] == 'INPUT_LIMIT':
            if record['model_calls'] != 0 or record['output_tokens'] != 0 or record['text'] is not None:
                raise ValueError('inconsistent input limit')
        elif record['model_calls'] != 1 or hashlib.sha256(record['text'].encode()).hexdigest() != record['response_sha256']:
            raise ValueError('generated response identity/call count mismatch')
        known_calls += record['model_calls']
        input_tokens += record['input_tokens']
        output_tokens += record['output_tokens']
        states[record['status']] += 1
        if not assessment.exists():
            unassessed_completed += 1
            continue
        result = json.loads(assessment.read_bytes())
        if result['generation']['artifact_sha256'] != digest(generated) or result['generation']['record'] != record:
            raise ValueError('assessment not bound to generation bytes')
        if any(result['metrics'][k] != record[k] for k in ('model_calls', 'input_tokens', 'output_tokens')):
            raise ValueError('assessment cost disagreement')
        if result['status'] not in ('REJECTED_GENERATED_FAMILY', 'STRUCTURAL_RESULT_FIDELITY_PENDING', 'STOP_INPUT_LIMIT_NO_MODEL_CALL'):
            raise ValueError('unknown assessment state')
        assessments[result['status']] += 1
    complete = (len(attempts) == 100 and sum(assessments.values()) == 100 and
                not unknown_execution and not unassessed_completed and
                terminal['returncode'] == 0 and observed_state['ExitCode'] == 0 and
                terminal['status'] == 'PROFILE_BATCH_COMPLETE_FIDELITY_PENDING')
    completion = root / 'terminal.json'
    if complete:
        if not completion.exists() or digest(completion) != terminal['completion_sha256']:
            raise ValueError('runtime completion not bound')
        runtime = json.loads(completion.read_bytes())
        if runtime['queries'] != 100 or runtime['status'] != 'PROFILE_BATCH_COMPLETED_FIDELITY_PENDING':
            raise ValueError('runtime cohort completion mismatch')
    return {'status': 'COMPLETE_PROFILE_COHORT_FIDELITY_PENDING' if complete else 'INCOMPLETE_PROFILE_COHORT_NO_PASS',
        'planned_queries': 100, 'attempt_directories': len(attempts), 'not_started': 100 - len(attempts),
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
