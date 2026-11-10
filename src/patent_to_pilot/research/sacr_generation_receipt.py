"""Bind private terminal generation bytes, limits and reported token costs.

This validates a normally returned generate_once record, not infrastructure
termination or actual model execution. Exceptions/unknown state are not records.
"""
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json, exact_fields
from patent_to_pilot.research.sacr_generation import GenerationLimits


def bind_generation_record(raw, *, expected_sha256, limits, metrics):
    """Keep raw artifact identity; do not parse/salvage generated response JSON.

    The caller must reserve and retain the original private artifact before
    invoking this binder. Cost agreement is not independent provider attestation.
    INPUT_LIMIT counts observed prompt tokens even though no model call occurred.
    """
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise InputBoundaryError('generation artifact bytes mismatch')
    if type(limits) is not GenerationLimits:
        raise InputBoundaryError('explicit generation limits required')
    limits.validate()
    record = decode_json(raw)
    if type(record) is not dict:
        raise InputBoundaryError('generation record must be an object')
    status = record.get('status')
    if status not in ('INPUT_LIMIT', 'EOS_COMPLETE', 'OUTPUT_LIMIT', 'NO_EOS', 'RESPONSE_BYTE_LIMIT'):
        raise InputBoundaryError('normal generation return required; unknown/failure is not rejection')
    fields = {'status', 'model_calls', 'input_tokens', 'output_tokens', 'text', 'retry'}
    exact_fields(record, fields if status == 'INPUT_LIMIT' else fields | {'response_sha256'})
    if record['retry'] is not False:
        raise InputBoundaryError('generation retry is not allowed')
    for key in ('model_calls', 'input_tokens', 'output_tokens'):
        if type(record[key]) is not int or record[key] < 0:
            raise InputBoundaryError('invalid generation count')
        if type(metrics) is not dict or type(metrics.get(key)) is not int or metrics[key] != record[key]:
            raise InputBoundaryError('generation token/call costs disagree')
    if status == 'INPUT_LIMIT':
        if (record['model_calls'] != 0 or record['input_tokens'] <= limits.input_tokens or
                record['output_tokens'] != 0 or record['text'] is not None):
            raise InputBoundaryError('inconsistent input-limit record')
        response_bytes = 0
    else:
        if (record['model_calls'] != 1 or record['input_tokens'] > limits.input_tokens or
                record['output_tokens'] > limits.output_tokens or type(record['text']) is not str):
            raise InputBoundaryError('inconsistent generated record')
        response = record['text'].encode('utf-8')
        response_bytes = len(response)
        if hashlib.sha256(response).hexdigest() != record['response_sha256']:
            raise InputBoundaryError('generation response hash mismatch')
        if (status == 'RESPONSE_BYTE_LIMIT') != (response_bytes > limits.response_bytes):
            raise InputBoundaryError('response byte status disagrees with limit')
        if status == 'EOS_COMPLETE' and record['output_tokens'] == 0:
            raise InputBoundaryError('EOS requires an output token')
        if status == 'OUTPUT_LIMIT' and record['output_tokens'] != limits.output_tokens:
            raise InputBoundaryError('output-limit status requires exhausted cap')
        if status == 'NO_EOS' and record['output_tokens'] >= limits.output_tokens:
            raise InputBoundaryError('non-EOS below-cap status inconsistent')
    return {'format': 'sacr-generation-binding-v1', 'artifact_sha256': expected_sha256,
            'record': record, 'response_bytes': response_bytes,
            'limits': dict(limits.__dict__), 'normally_returned_record': True,
            'execution_attestation': 'REQUIRES_EXTERNAL_VERIFICATION',
            'response_acceptance': 'NOT_EVALUATED', 'semantic_status': 'unknown'}
