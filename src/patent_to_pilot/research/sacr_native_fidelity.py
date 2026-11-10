"""Bounded native profile batch; injected guarded runtime, no evaluator access.

This is the production loop, not a semantic acceptance oracle. The outer
supervisor owns GPU reservation, loading, deadline and terminal attestation.
"""
import hashlib
import json
import os
import time
from pathlib import Path

from .mtm_runtime import InputBoundaryError, decode_json
from .sacr_generation import run_reserved_attempt
from .sacr_outcomes import METRICS
from .sacr_prompts import build_messages
from .sacr_rejection_policy import assess_profile_attempt
from .sacr_schema import quote_profile_schema
from .sacr_solo_fidelity import fixed_sample


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def schema_digest(schema):
    return digest(json.dumps(schema, sort_keys=True, separators=(',', ':')).encode())


def write_new(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    with Path(path).open('xb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return digest(raw)


def bind_sample(query_bytes, sample_bytes, *, query_sha256, sample_sha256):
    if digest(query_bytes) != query_sha256 or digest(sample_bytes) != sample_sha256:
        raise InputBoundaryError('native fidelity input hash mismatch')
    sample = decode_json(sample_bytes)
    if (sample.get('version') != 'sacr-native-fidelity-sample-v1' or
            sample.get('benchmark') != 'DAPFAM' or sample.get('population') != 474 or
            sample.get('source_sha256') != query_sha256):
        raise InputBoundaryError('native sample contract mismatch')
    rows = [decode_json(line) for line in query_bytes.splitlines()]
    if len(rows) != 474 or any(type(row) is not dict or set(row) != {'id', 'text'} for row in rows):
        raise InputBoundaryError('native query projection mismatch')
    sources = {row['id']: row['text'] for row in rows}
    expected_ids = fixed_sample('DAPFAM', [row['id'] for row in rows])
    entries = sample.get('entries')
    if type(entries) is not list or len(entries) != 100:
        raise InputBoundaryError('native sample must contain 100 entries')
    result = []
    for q, entry in zip(expected_ids, entries):
        if type(entry) is not dict or set(entry) != {'query_id', 'source_sha256', 'schema_sha256'}:
            raise InputBoundaryError('invalid native sample entry')
        source = sources[q]
        schema = quote_profile_schema(source=source, query_id=q, input_kind='DAPFAM_TA')
        if entry != {'query_id': q, 'source_sha256': digest(source.encode()), 'schema_sha256': schema_digest(schema)}:
            raise InputBoundaryError('sample order/source/schema identity mismatch')
        result.append((q, source, schema))
    return result


def run_profiles(*, entries, output, prompt_root, prompt_sha256, tokenizer,
                 guarded_model_factory, device, limits, check_authorization,
                 remaining_seconds, peak_memory_bytes):
    return _run_profiles(entries=entries, output=output, prompt_root=prompt_root,
        prompt_sha256=prompt_sha256, tokenizer=tokenizer, guarded_model_factory=guarded_model_factory,
        device=device, limits=limits, check_authorization=check_authorization,
        remaining_seconds=remaining_seconds, peak_memory_bytes=peak_memory_bytes)


def run_unstarted_profiles(*, entries, prior_output, continuation_manifest, **kwargs):
    """New output only; consumed and interrupted entries can never be selected."""
    from .sacr_continuation import verify_history_files, canonical_continuation_root
    manifest = continuation_manifest
    if manifest.get('version') != 'sacr-unstarted-continuation-v1' or manifest.get('retry_authorized') is not False:
        raise InputBoundaryError('unstarted-only continuation contract required')
    records = manifest['records']
    if (len(records) != 100 or [r['index'] for r in records] != list(range(100)) or
            [r['query_id'] for r in records] != [q for q, _, _ in entries]):
        raise InputBoundaryError('continuation differs from fixed sample')
    selected = [r['index'] for r in records if r['state'] == 'NEVER_STARTED']
    if (not selected or manifest['selected_indices'] != selected or
            manifest['maximum_new_profile_calls'] != len(selected)):
        raise InputBoundaryError('continuation cannot select consumed/blocked entries')
    verify_history_files(prior_output, manifest)
    if Path(kwargs['output']).resolve() != canonical_continuation_root(prior_output, manifest) / 'profiles':
        raise InputBoundaryError('continuation requires its one canonical destination; no fresh-output replay')
    return _run_profiles(entries=entries, indices=selected, before_call=lambda: verify_history_files(
        prior_output, manifest), minimum_call_window_seconds=1200, **kwargs)


def _run_profiles(*, entries, output, prompt_root, prompt_sha256, tokenizer,
                  guarded_model_factory, device, limits, check_authorization,
                  remaining_seconds, peak_memory_bytes, indices=None, before_call=None,
                  minimum_call_window_seconds=5):
    """Run each bound query at most once; never resume an existing directory.

    factory(schema, source, attempt_directory) supplies a fresh per-query grammar
    over the same loaded model. Infra exceptions stop all subsequent calls.
    Completed malformed responses are charged and retained, then continue.
    """
    if len(entries) != 100 or len({q for q, _, _ in entries}) != 100:
        raise InputBoundaryError('complete bound 100-query sample required')
    continuation = indices is not None
    indices = list(range(100)) if indices is None else indices
    limits.validate()
    prompts = []
    for q, source, schema in entries:
        if schema != quote_profile_schema(source=source, query_id=q, input_kind='DAPFAM_TA'):
            raise InputBoundaryError('per-query grammar identity mismatch')
        prompt = build_messages(prompt_root=prompt_root, kind='profile_quotes', source=source,
                                query_id=q, input_kind='DAPFAM_TA', prompt_variant='source_order_v2')
        if prompt['prompt_sha256'] != prompt_sha256:
            raise InputBoundaryError('profile prompt differs from declaration')
        prompts.append(prompt)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'reservation.json', {'status': 'RESERVED', 'queries': len(indices),
        'maximum_calls': len(indices), 'prompt_sha256': prompt_sha256, 'limits': limits.__dict__,
        'retry': False, 'semantic_status': 'NOT_ASSESSED'})
    completed = []
    try:
        for position, index in enumerate(indices):
            q, source, schema = entries[index]
            prompt = prompts[index]
            check_authorization()
            if before_call is not None:
                before_call()
            remaining = remaining_seconds()
            if continuation and remaining <= minimum_call_window_seconds:
                deferred = {'status': 'PROFILE_BATCH_DEFERRED_NO_INFLIGHT_CALL', 'outcomes': completed,
                    'deferred_indices': indices[position:], 'semantic_status': 'NOT_ASSESSED', 'retry': False}
                write_new(output / 'deferred.json', deferred)
                return deferred
            if remaining <= minimum_call_window_seconds:
                raise TimeoutError('fidelity reservation exhausted before next call')
            attempt = output / f'{index:03d}'
            attempt.mkdir(exist_ok=False)
            write_new(attempt / 'input.json', {'query_id': q, 'source_sha256': digest(source.encode()),
                      'schema_sha256': schema_digest(schema), 'prompt': prompt})
            guarded = guarded_model_factory(schema, source, attempt)
            if continuation:
                check_authorization()
                before_call()
                if remaining_seconds() <= minimum_call_window_seconds:
                    deferred = {'status': 'PROFILE_BATCH_DEFERRED_NO_INFLIGHT_CALL', 'outcomes': completed,
                        'deferred_indices': indices[position:], 'prepared_not_called_indices': [index],
                        'semantic_status': 'NOT_ASSESSED', 'retry': False}
                    write_new(output / 'deferred.json', deferred)
                    return deferred
            start = time.monotonic()
            record = run_reserved_attempt(attempt / 'profile', messages=prompt['messages'],
                tokenizer=tokenizer, model=guarded, device=device, eos_token_ids=[151645, 151643], limits=limits)
            seconds = time.monotonic() - start
            metrics = {key: 0 for key in METRICS}
            metrics.update({key: record[key] for key in ('model_calls', 'input_tokens', 'output_tokens')})
            metrics.update(operation_wall_seconds=seconds, gpu_seconds=seconds,
                           peak_memory_bytes=peak_memory_bytes())
            raw = (attempt / 'profile/generation.json').read_bytes()
            assessment = assess_profile_attempt(raw, expected_sha256=digest(raw), source=source,
                query_id=q, input_kind='DAPFAM_TA', limits=limits, metrics=metrics)
            write_new(attempt / 'assessment.json', assessment)
            completed.append({'index': index, 'status': assessment['status'], 'metrics': metrics,
                              'generation_sha256': digest(raw)})
            if assessment['status'] == 'STOP_INPUT_LIMIT_NO_MODEL_CALL':
                raise InputBoundaryError('input-limit query stops batch without truncation or retry')
        summary = {'status': 'SELECTED_PROFILE_BATCH_COMPLETED_COHORT_INCOMPLETE' if continuation else
                   'PROFILE_BATCH_COMPLETED_FIDELITY_PENDING', 'outcomes': completed,
                   'semantic_status': 'NOT_ASSESSED', 'retry': False}
        write_new(output / 'completion.json', summary)
        return summary
    except BaseException as error:
        write_new(output / 'failure.json', {'status': 'STOPPED_NOT_RESUMABLE',
            'exception_type': type(error).__name__, 'completed_outcomes': completed,
            'incomplete_attempt_cost': 'UNKNOWN_INSPECT_PRIVATE_ATTEMPT_AND_SUPERVISOR', 'retry': False})
        raise
