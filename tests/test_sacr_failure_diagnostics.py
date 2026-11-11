import json
import pytest
from patent_to_pilot.research.sacr_failure_diagnostics import AttemptDiagnostics, local_executor
from patent_to_pilot.research.sacr_grammar_guard import CompleteJsonEOSGuard
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from jsonschema import Draft202012Validator
from test_sacr_generation import fake_torch, Tokenizer, Model


def test_backend_failure_keeps_private_details_and_no_retry(tmp_path):
    d = AttemptDiagnostics(tmp_path / 'private')
    class Model:
        def generate(self, **kwargs): raise RuntimeError('private source detail')
    with pytest.raises(RuntimeError) as error: d.call_backend(Model())
    d.failure(error.value, 'backend')
    data = json.loads((d.destination / 'failure-private.json').read_bytes())
    assert data['backend_invocations_observed'] == 1
    assert data['backend_returns_observed'] == 0
    assert data['inference_completed'] == 'UNKNOWN'
    assert data['message'] == 'private source detail'
    with pytest.raises(RuntimeError, match='only once'): d.call_backend(Model())
    with pytest.raises(FileExistsError): AttemptDiagnostics(d.destination)


def test_grammar_error_keeps_bounded_suffix_and_schema_path(tmp_path):
    d = AttemptDiagnostics(tmp_path / 'private')
    validate = d.validator(Draft202012Validator({'type': 'object', 'required': ['wanted']}).validate)
    class Tokenizer:
        def decode(self, *args, **kwargs): return '{}'
    guard = CompleteJsonEOSGuard(prefix_fn=lambda *_: [99], tokenizer=Tokenizer(),
                                prompt_tokens=2, eos_token_ids=[99], validate=validate)
    with pytest.raises(InputBoundaryError):
        d.grammar(guard, 2)(0, [777777, 888888] + [3] * 5000)
    data = json.loads((d.destination / 'failure-private.json').read_bytes())
    assert data['last_schema_rejection']['validator'] == 'required'
    assert len(data['last_generated_prefix']['tail_token_ids']) == 4096
    assert data['last_generated_prefix']['truncated']
    assert 777777 not in data['last_generated_prefix']['tail_token_ids']
    d.failure(RuntimeError('outer'), 'attempt')
    assert json.loads((d.destination / 'failure-private.json').read_bytes()) == data
    assert d.written_bytes < 256 * 1024


def test_factory_failure_known_before_backend(tmp_path):
    def fail(*args): raise ValueError('factory failure')
    invoke = local_executor(tokenizer=None, model_factory=fail, device='cpu',
        eos_token_ids=[9], check_admission=lambda _: None, peak_memory_bytes=lambda: 0)
    with pytest.raises(ValueError): invoke('profile', tmp_path / 'profile', [], {})
    data = json.loads((tmp_path / 'profile-diagnostics-private/failure-private.json').read_bytes())
    assert data['backend_invocations_observed'] == 0
    assert not (tmp_path / 'profile/reservation.json').exists()


def test_successful_backend_return_is_not_validation(tmp_path):
    d = AttemptDiagnostics(tmp_path / 'private')
    class Model:
        def generate(self, **kwargs): return 'opaque result'
    assert d.call_backend(Model()) == 'opaque result'
    assert json.loads((d.destination / 'backend-return.json').read_bytes())['status'] == 'BACKEND_RETURNED_NOT_VALIDATED'


def test_diagnostic_write_failure_preserves_original_exception(tmp_path, monkeypatch):
    d = AttemptDiagnostics(tmp_path / 'private')
    original = InputBoundaryError('original grammar failure')
    def bad_callback(*args): raise original
    def disk_full(*args): raise OSError('disk full')
    monkeypatch.setattr(d, 'write', disk_full)
    with pytest.raises(InputBoundaryError) as observed: d.grammar(bad_callback, 2)(0, [1,2,3])
    assert observed.value is original
    assert d.telemetry_write_error == 'OSError'


def test_successful_callback_does_not_copy_tokens_to_host(tmp_path):
    d = AttemptDiagnostics(tmp_path / 'private')
    class Tokens:
        def __len__(self): return 10
        def __getitem__(self, key): return self
        def __iter__(self): raise AssertionError('scalar synchronization during decoding')
        def detach(self): raise AssertionError('host copy during successful decoding')
    assert d.grammar(lambda *_: [9], 2)(0, Tokens()) == [9]


@pytest.mark.parametrize('failure',[False,True])
def test_executor_binds_backend_entry_and_preserves_attempt_receipts(tmp_path,failure):
    model=Model(error=failure)
    def factory(stage,schema,diagnostics):
        class Wrapped:
            def generate(self,**kwargs):return diagnostics.call_backend(model,**kwargs)
        return Wrapped()
    invoke=local_executor(tokenizer=Tokenizer(),model_factory=factory,device='cpu',eos_token_ids=[9],
                          check_admission=lambda _:None,peak_memory_bytes=lambda:0)
    target=tmp_path/'profile'
    if failure:
        with pytest.raises(RuntimeError,match='private error detail'):invoke('profile',target,[],None)
        assert json.loads((target/'failure.json').read_bytes())['model_calls']=='UNKNOWN'
        detail=json.loads((tmp_path/'profile-diagnostics-private/failure-private.json').read_bytes())
        assert detail['backend_invocations_observed']==1
        assert detail['inference_completed']=='UNKNOWN'
    else:
        result=invoke('profile',target,[],None)
        assert result['model_calls']==1
        assert (target/'generation-binding.json').exists()
    assert model.calls==1
