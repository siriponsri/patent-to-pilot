import hashlib
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_generation_receipt import bind_generation_record


def record(status='EOS_COMPLETE', text='not valid JSON'):
    value = dict(status=status, model_calls=1, input_tokens=3, output_tokens=2,
                 text=text, response_sha256=hashlib.sha256(text.encode()).hexdigest(), retry=False)
    if status == 'INPUT_LIMIT':
        value = dict(status=status, model_calls=0, input_tokens=5, output_tokens=0, text=None, retry=False)
    if status == 'NO_EOS':
        value['output_tokens'] = 1
    return value


def bind(value, *, metrics=None, pin=None, raw=None):
    raw = raw if raw is not None else json.dumps(value).encode()
    metrics = metrics if metrics is not None else {k: value[k] for k in ('model_calls', 'input_tokens', 'output_tokens')}
    return bind_generation_record(raw, expected_sha256=pin or hashlib.sha256(raw).hexdigest(),
                                  limits=GenerationLimits(4, 2, 6, 32), metrics=metrics)


@pytest.mark.parametrize('status', ['EOS_COMPLETE', 'INPUT_LIMIT', 'OUTPUT_LIMIT', 'NO_EOS', 'RESPONSE_BYTE_LIMIT'])
def test_normal_return_preserves_status_without_response_acceptance(status):
    value = record(status, text='x' * 33 if status == 'RESPONSE_BYTE_LIMIT' else 'invalid JSON')
    result = bind(value)
    assert result['record'] == value
    assert result['response_acceptance'] == 'NOT_EVALUATED'
    assert result['execution_attestation'] == 'REQUIRES_EXTERNAL_VERIFICATION'
    value['status'] = 'mutated'
    assert result['record']['status'] == status


@pytest.mark.parametrize('key,value', [
    ('status', 'FAILED'), ('status', 'INTERRUPTED'), ('status', 'RUNNING'),
    ('model_calls', 0), ('model_calls', True), ('input_tokens', 5),
    ('input_tokens', -1), ('output_tokens', 3), ('output_tokens', 0),
    ('retry', True), ('retry', 0), ('response_sha256', '0' * 64), ('text', None),
])
def test_inconsistent_or_nonterminal_record_refused(key, value):
    data = record()
    data[key] = value
    with pytest.raises(InputBoundaryError):
        bind(data)


@pytest.mark.parametrize('status,key,value', [
    ('INPUT_LIMIT', 'input_tokens', 4), ('INPUT_LIMIT', 'model_calls', 1),
    ('INPUT_LIMIT', 'output_tokens', 1), ('INPUT_LIMIT', 'text', ''),
    ('OUTPUT_LIMIT', 'output_tokens', 1), ('NO_EOS', 'output_tokens', 2),
    ('RESPONSE_BYTE_LIMIT', 'text', 'short'),
])
def test_status_limit_consistency(status, key, value):
    data = record(status)
    data[key] = value
    with pytest.raises(InputBoundaryError):
        bind(data)


def test_oversize_eos_cannot_hide_byte_failure():
    with pytest.raises(InputBoundaryError):
        bind(record(text='x' * 33))


@pytest.mark.parametrize('value', [None, True, 2])
def test_unknown_or_disagreeing_cost_not_silently_zeroed(value):
    costs = dict(model_calls=value, input_tokens=3, output_tokens=2)
    with pytest.raises(InputBoundaryError):
        bind(record(), metrics=costs)


def test_raw_artifact_and_exact_schema_binding():
    data = record()
    with pytest.raises(InputBoundaryError):
        bind(data, pin='0' * 64)
    data['inferred_success'] = True
    with pytest.raises(InputBoundaryError):
        bind(data)
    with pytest.raises(InputBoundaryError):
        bind(record(), raw=b'[]')
