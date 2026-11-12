import hashlib
import json
import pytest
from patent_to_pilot.research.sacr_automatic_runner import run_query
from patent_to_pilot.research.patent_structure_marking import VERSION, sha
from patent_to_pilot.research.km_automatic_review import CHECKS


def response(output):
    text = json.dumps(output)
    metrics = {'model_calls': 1, 'input_tokens': 10, 'output_tokens': 20}
    raw = json.dumps(dict(status='EOS_COMPLETE', text=text, retry=False,
                         response_sha256=sha(text), **metrics)).encode()
    return raw, metrics


def run(tmp_path, mode):
    source = 'The pump reduces pressure.'; calls = []
    def invoke(stage, request):
        calls.append(stage)
        if mode == 'unknown': raise RuntimeError('backend interrupted')
        if stage == 'marking':
            if mode == 'bad': return response({'invalid': True})
            return response({'version': VERSION, 'query_id': 'q1', 'source_sha256': sha(source),
                'marks': [{'role': 'action', 'start_token': 2, 'end_token': 3, 'attachment': 'explicit'}],
                'abstraction': source})
        return response({'binding_sha256': request['binding_sha256'], 'checks': {
            k: {'status': 'screened', 'source_quote': '', 'candidate_quote': '', 'reason': 'No issue detected.'}
            for k in CHECKS}})
    result = run_query(destination=tmp_path / 'q1', query_id='q1', source=source,
                       km_text='Preserve constraints.', km_sha256=sha('Preserve constraints.'),
                       invoke=invoke, admit=lambda *args: None, count_tokens=lambda messages: 10)
    return result, calls


def test_two_call_pipeline_preserves_terminal_artifacts(tmp_path):
    result, calls = run(tmp_path, 'normal')
    assert calls == ['marking', 'review']
    assert result['decision']['action'] == 'USE_SCREENED_CANDIDATE'
    assert not result['decision']['semantic_certified']
    assert (tmp_path / 'q1' / 'review-generation.json').exists()
    with pytest.raises(FileExistsError): run(tmp_path, 'normal')


def test_invalid_marking_falls_back_without_review_or_retry(tmp_path):
    result, calls = run(tmp_path, 'bad')
    assert calls == ['marking']
    assert result['decision']['action'] == 'ORIGINAL_QUERY_FALLBACK'
    assert len(result['events']) == 1


def test_unknown_execution_is_durable_hold(tmp_path):
    with pytest.raises(RuntimeError): run(tmp_path, 'unknown')
    failure = json.loads((tmp_path / 'q1' / 'failure.json').read_text())
    assert failure['status'] == 'HOLD' and failure['unresolved_stage'] == 'marking'
    assert not (tmp_path / 'q1' / 'result.json').exists()
