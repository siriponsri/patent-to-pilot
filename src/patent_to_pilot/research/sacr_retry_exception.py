"""Exactly one owner-approved exception for original interrupted sample index45.

This is not an automatic retry policy. Fixed host output mapping, terminated
prior job and remaining charged budget must be enforced by the supervisor.
"""
import json
import math
from pathlib import Path

from .mtm_runtime import InputBoundaryError
from .sacr_native_fidelity import digest, _run_profiles
from .sacr_continuation import verify_history_files

INDEX = 45


def validate_same_contract(declaration, original):
    keys = ('identity_sha256', 'prompt_sha256', 'lmfe_source_sha256', 'query_sha256', 'sample_sha256')
    if any(k not in declaration or k not in original or declaration[k] != original[k] for k in keys):
        raise InputBoundaryError('exception changed original model/source/prompt/grammar contract')
    for name in ('sacr_schema', 'sacr_quote_profile', 'sacr_alphabet', 'sacr_escape_callback', 'sacr_grammar_guard'):
        key = 'src/patent_to_pilot/research/' + name + '.py'
        if key not in declaration['files_sha256'] or declaration['files_sha256'][key] != original['files_sha256'].get(key):
            raise InputBoundaryError('exception changed original schema or decoding implementation')


def validate_closed_continuation(terminal_raw, ledger, expected_sha256, *, minimum_fidelity_charge, minimum_gpu_charge):
    terminal = json.loads(terminal_raw)
    closed = ledger.get('native_unstarted_continuation_reservation', {})
    wall = terminal.get('wall_seconds')
    state = terminal.get('container_state', {})
    if (digest(terminal_raw) != expected_sha256 or closed.get('terminal_sha256') != expected_sha256 or
            state.get('Running') is not False or state.get('Status') not in ('exited', 'dead') or
            type(wall) not in (int, float) or not math.isfinite(wall) or wall < 0 or
            not str(closed.get('status', '')).startswith('CLOSED_') or
            closed.get('actual_supervisor_seconds') != wall):
        raise InputBoundaryError('continuation terminal and charged closure disagree')
    for total, prior, minimum in (('fidelity_generation_charged_seconds', 'prior_fidelity_charged_seconds', minimum_fidelity_charge),
                         ('gpu_conservative_charged_seconds', 'prior_gpu_charged_seconds', minimum_gpu_charge)):
        if (type(ledger.get(total)) not in (int, float) or type(closed.get(prior)) not in (int, float) or
                not math.isfinite(ledger[total]) or not math.isfinite(closed[prior]) or
                type(minimum) not in (int, float) or not math.isfinite(minimum) or minimum < 0 or
                closed[prior] < minimum or ledger[total] < closed[prior] + wall):
            raise InputBoundaryError('actual continuation wall not fully charged')
    return terminal


def validate_authority(raw, expected_sha256, *, wall_seconds):
    if digest(raw) != expected_sha256:
        raise InputBoundaryError('owner exception receipt mismatch')
    grant = json.loads(raw)
    if (grant.get('status') != 'OWNER_APPROVED_NOT_USED' or
            grant.get('scope') != 'original fixed-sample index45 only, interrupted prior attempt' or
            grant.get('maximum_new_calls') != 1 or grant.get('whole_supervisor_limit_seconds') != 1200 or
            grant.get('same_source_prompt_model_decoder') is not True or
            grant.get('charge_to_original_fidelity_and_gpu_ledgers') is not True or
            grant.get('preserve_prior_attempt_and_unknown_costs') is not True or
            grant.get('on_failure') != 'STOP_CONFIGURATION_NO_FURTHER_RETRY' or
            grant.get('requires_reviewed_supervisor') is not True or
            grant.get('one_gpu_job_at_a_time') is not True or
            type(wall_seconds) is not int or not 60 <= wall_seconds <= 1200):
        raise InputBoundaryError('not the approved single interrupted-query exception')
    return grant


def canonical_exception_root(prior_output):
    # Independent of authorization serialization or job name: no fresh-folder
    # replay by changing metadata/hash. Supervisor fixes this on the real host.
    return Path(prior_output).resolve(strict=True).parent / 'exception-index045-v1' / 'attempt'


def run_authorized_exception(*, entries, prior_output, continuation_manifest,
                             authorization_raw, authorization_sha256, wall_seconds, **kwargs):
    validate_authority(authorization_raw, authorization_sha256, wall_seconds=wall_seconds)
    manifest = continuation_manifest
    records = manifest.get('records', [])
    if (len(entries) != 100 or len(records) != 100 or
            [r['index'] for r in records] != list(range(100)) or
            [r['query_id'] for r in records] != [q for q, _, _ in entries] or
            records[INDEX]['state'] != 'INTERRUPTED_OR_PREPARED_BLOCKED' or
            manifest.get('blocked_indices') != [INDEX]):
        raise InputBoundaryError('exception does not identify the sole original interrupted query')
    verify_history_files(prior_output, manifest)
    if Path(kwargs['output']).resolve() != canonical_exception_root(prior_output) / 'profiles':
        raise InputBoundaryError('exception must use its permanent one-use destination')
    result = _run_profiles(entries=entries, indices=[INDEX], before_call=lambda: verify_history_files(
        prior_output, manifest), minimum_call_window_seconds=60, **kwargs)
    # Retain the underlying batch receipt, but never imply the one-call
    # exception establishes cohort or semantic acceptance.
    success = (len(result['outcomes']) == 1 and
               result['outcomes'][0]['status'] == 'STRUCTURAL_RESULT_FIDELITY_PENDING')
    return {**result, 'status': 'EXCEPTION_STRUCTURAL_RESULT_FIDELITY_PENDING' if success else
            'FAIL_STOP_CONFIGURATION_EXCEPTION_UNUSABLE', 'exception_index': INDEX,
            'further_retry_allowed': False, 'semantic_status': 'NOT_ASSESSED'}
