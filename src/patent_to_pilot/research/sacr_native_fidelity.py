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
    """Run each bound query at most once; never resume an existing directory.

    factory(schema, source, attempt_directory) supplies a fresh per-query grammar
    over the same loaded model. Infra exceptions stop all subsequent calls.
    Completed malformed responses are charged and retained, then continue.
    """
    if len(entries) != 100 or len({q for q, _, _ in entries}) != 100:
        raise InputBoundaryError('complete bound 100-query sample required')
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
    write_new(output / 'reservation.json', {'status': 'RESERVED', 'queries': 100,
        'maximum_calls': 100, 'prompt_sha256': prompt_sha256, 'limits': limits.__dict__,
        'retry': False, 'semantic_status': 'NOT_ASSESSED'})
    completed = []
    try:
        for index, ((q, source, schema), prompt) in enumerate(zip(entries, prompts)):
            check_authorization()
            if remaining_seconds() <= 5:
                raise TimeoutError('fidelity reservation exhausted before next call')
            attempt = output / f'{index:03d}'
            attempt.mkdir(exist_ok=False)
            write_new(attempt / 'input.json', {'query_id': q, 'source_sha256': digest(source.encode()),
                      'schema_sha256': schema_digest(schema), 'prompt': prompt})
            guarded = guarded_model_factory(schema, source, attempt)
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
        summary = {'status': 'PROFILE_BATCH_COMPLETED_FIDELITY_PENDING', 'outcomes': completed,
                   'semantic_status': 'NOT_ASSESSED', 'retry': False}
        write_new(output / 'completion.json', summary)
        return summary
    except BaseException as error:
        write_new(output / 'failure.json', {'status': 'STOPPED_NOT_RESUMABLE',
            'exception_type': type(error).__name__, 'completed_outcomes': completed,
            'incomplete_attempt_cost': 'UNKNOWN_INSPECT_PRIVATE_ATTEMPT_AND_SUPERVISOR', 'retry': False})
        raise
