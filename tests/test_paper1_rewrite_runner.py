import json
import pytest
from patent_to_pilot.research.paper1_rewrite_runner import run_rewrite, USE, FALLBACK
from patent_to_pilot.research import paper1_rewrite_arms as arms
from patent_to_pilot.research.automatic_executor_adapter import adapt_reserved_executor
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

SRC = 'A pump reduces line pressure below 5 kPa except during cleaning.'


def response(output, status='EOS_COMPLETE'):
    text = json.dumps(output)
    metrics = {'model_calls': 1, 'input_tokens': 10, 'output_tokens': 4096 if status == 'OUTPUT_LIMIT' else 20}
    raw = json.dumps(dict(status=status, text=text, retry=False, response_sha256=arms.sha(text), **metrics)).encode()
    return raw, metrics


def fa(**over):
    out = {'version': arms.FA_VERSION, 'query_id': 'q1', 'source_sha256': arms.sha(SRC), 'function': 'Lowers pressure.',
           'mechanism': 'A pumping element.', 'problem': 'Over-pressure.', 'conditions': 'Below 5 kPa.'}
    out.update(over); return out


def run(tmp_path, arm='FA', output=None, cap=5800, tokens=10, mode='normal'):
    calls = []
    def invoke(stage, request):
        calls.append(stage)
        if mode == 'unknown': raise RuntimeError('backend interrupted')
        return response(output if output is not None else fa())
    result = run_rewrite(destination=tmp_path / 'q1', arm=arm, query_id='q1', source=SRC, invoke=invoke,
                         admit=lambda *a: None, count_tokens=lambda m: tokens, input_token_cap=cap)
    return result, calls


def test_valid_fa_rewrite_is_used_once(tmp_path):
    result, calls = run(tmp_path)
    assert calls == ['rewrite'] and result['action'] == USE and result['text'].split('\n')[3] == 'Below 5 kPa.'
    assert result['lexical_descriptives']['numbers_retained_share'] == 1.0 and not result['semantic_certified']
    with pytest.raises(FileExistsError): run(tmp_path)


def test_blank_or_wrong_output_falls_back_without_retry(tmp_path):
    result, calls = run(tmp_path / 'a', output=fa(function='  '))
    assert calls == ['rewrite'] and result['action'] == FALLBACK and result['reason'] == 'REWRITE_REJECTED'
    result, _ = run(tmp_path / 'b', output={'invalid': True})
    assert result['reason'] == 'REWRITE_REJECTED'


def test_input_cap_falls_back_without_call(tmp_path):
    result, calls = run(tmp_path, cap=1000, tokens=1001)
    assert calls == [] and result['action'] == FALLBACK and result['reason'] == 'INPUT_LIMIT'


def test_output_limit_falls_back(tmp_path):
    def invoke(stage, request): return response(fa(), status='OUTPUT_LIMIT')
    result = run_rewrite(destination=tmp_path / 'q', arm='FA', query_id='q1', source=SRC, invoke=invoke,
                         admit=lambda *a: None, count_tokens=lambda m: 10, input_token_cap=5800)
    assert result['reason'] == 'NORMAL_OUTPUT_LIMIT' and result['action'] == FALLBACK


def test_unknown_backend_is_durable_hold(tmp_path):
    with pytest.raises(RuntimeError): run(tmp_path, mode='unknown')
    failure = json.loads((tmp_path / 'q1' / 'failure.json').read_text())
    assert failure['status'] == 'HOLD' and failure['unresolved_stage'] == 'rewrite'
    assert not (tmp_path / 'q1' / 'result.json').exists()


def test_gr_arm_and_adapter_stage_whitelist(tmp_path):
    out = {'version': arms.GR_VERSION, 'query_id': 'q1', 'source_sha256': arms.sha(SRC), 'abstract': 'A pump.'}
    result, _ = run(tmp_path / 'gr', arm='GR', output=out)
    assert result['action'] == USE and result['text'] == 'A pump.'
    adapted = adapt_reserved_executor(destination=tmp_path / 'ad', executor=lambda *a: None)
    with pytest.raises(InputBoundaryError): adapted('rewrite', {})


from patent_to_pilot.research.paper1_rewrite_runner import GrammarRefusal, classify_grammar_refusal, REFUSAL_MESSAGE


def _diagnostics(path, **over):
    record = {'stage': 'grammar-callback', 'exception_type': 'InputBoundaryError', 'message': REFUSAL_MESSAGE,
              'message_sha256': 'x' * 64, 'backend_invocations_observed': 1, 'backend_returns_observed': 0,
              'last_generated_prefix': {'generated_tokens_seen': 267, 'truncated': False, 'tail_token_ids': [1, 2]}}
    record.update(over); path.mkdir(parents=True); (path / 'failure-private.json').write_text(json.dumps(record))
    return path


def test_classifier_requires_exception_and_diagnostics(tmp_path):
    good = _diagnostics(tmp_path / 'ok')
    refusal = classify_grammar_refusal(InputBoundaryError(REFUSAL_MESSAGE), good)
    assert isinstance(refusal, GrammarRefusal) and refusal.evidence['generated_tokens_seen'] == 267
    assert 'tail_token_ids' not in json.dumps(refusal.evidence)
    assert classify_grammar_refusal(InputBoundaryError('grammar has no continuation'), good) is None
    assert classify_grammar_refusal(RuntimeError(REFUSAL_MESSAGE), good) is None
    assert classify_grammar_refusal(InputBoundaryError(REFUSAL_MESSAGE), tmp_path / 'missing') is None
    for name, over in (('stage', {'stage': 'attempt'}), ('returned', {'backend_returns_observed': 1}),
                       ('message', {'message': 'other'})):
        assert classify_grammar_refusal(InputBoundaryError(REFUSAL_MESSAGE), _diagnostics(tmp_path / name, **over)) is None


def test_verified_refusal_falls_back_and_other_errors_hold(tmp_path):
    good = _diagnostics(tmp_path / 'diag')
    def refused(stage, request): raise classify_grammar_refusal(InputBoundaryError(REFUSAL_MESSAGE), good)
    result = run_rewrite(destination=tmp_path / 'q', arm='FA', query_id='q1', source=SRC, invoke=refused,
                         admit=lambda *a: None, count_tokens=lambda m: 10, input_token_cap=5800)
    assert result['action'] == FALLBACK and result['reason'] == 'GRAMMAR_REFUSED' and result['text'] is None
    assert result['events'][0]['model_calls'] == 1 and not (tmp_path / 'q' / 'failure.json').exists()
    assert json.loads((tmp_path / 'q' / 'rewrite-grammar-refused.json').read_text())['retry'] is False
    def unverified(stage, request): raise InputBoundaryError(REFUSAL_MESSAGE)
    with pytest.raises(InputBoundaryError):
        run_rewrite(destination=tmp_path / 'h', arm='FA', query_id='q1', source=SRC, invoke=unverified,
                    admit=lambda *a: None, count_tokens=lambda m: 10, input_token_cap=5800)
    assert json.loads((tmp_path / 'h' / 'failure.json').read_text())['status'] == 'HOLD'
    def early(*args): raise GrammarRefusal({})
    with pytest.raises(GrammarRefusal):  # refusal before dispatch is not a fallback
        run_rewrite(destination=tmp_path / 'e', arm='FA', query_id='q1', source=SRC, invoke=lambda *a: None,
                    admit=early, count_tokens=lambda m: 10, input_token_cap=5800)
    assert (tmp_path / 'e' / 'failure.json').exists()
