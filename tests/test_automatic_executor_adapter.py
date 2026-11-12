import hashlib
import json
import pytest
from patent_to_pilot.research.automatic_executor_adapter import adapt_reserved_executor
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_reserved_attempt_bytes_preserved_and_replay_rejected(tmp_path):
    request = {'messages': [{'role': 'user', 'content': 'source'}], 'schema': {}}
    raw = b'{"raw":"unchanged"}'
    def executor(stage, path, messages, schema):
        path.mkdir()
        reservation = {'status': 'RESERVED', 'retry': False, 'limits': GenerationLimits().__dict__,
            'messages_sha256': hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()}
        (path / 'reservation.json').write_text(json.dumps(reservation))
        (path / 'generation.json').write_bytes(raw)
        diagnostics = path.with_name(path.name + '-diagnostics-private')
        diagnostics.mkdir()
        (diagnostics / 'backend-dispatch.json').write_text(json.dumps({'status': 'DISPATCH_INTENT', 'retry': False}))
        (diagnostics / 'backend-return.json').write_text(json.dumps({'status': 'BACKEND_RETURNED_NOT_VALIDATED'}))
        return {'model_calls': 1}
    invoke = adapt_reserved_executor(destination=tmp_path / 'attempts', executor=executor)
    assert invoke('marking', request) == (raw, {'model_calls': 1})
    with pytest.raises(InputBoundaryError): invoke('marking', request)


def test_backend_exception_consumes_stage_without_retry(tmp_path):
    def executor(*args): raise RuntimeError('unknown')
    invoke = adapt_reserved_executor(destination=tmp_path / 'attempts', executor=executor)
    with pytest.raises(RuntimeError): invoke('marking', {'messages': [], 'schema': {}})
    with pytest.raises(InputBoundaryError): invoke('marking', {'messages': [], 'schema': {}})


def test_different_limits_cannot_be_silently_ignored(tmp_path):
    with pytest.raises(InputBoundaryError):
        adapt_reserved_executor(destination=tmp_path / 'attempts', executor=None,
                                limits=GenerationLimits(output_tokens=100))
