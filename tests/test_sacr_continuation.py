import json
from pathlib import Path
import pytest

from patent_to_pilot.research.sacr_continuation import seal_terminal_history, verify_history_files, canonical_continuation_root
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_native_fidelity import digest, schema_digest
from patent_to_pilot.research import sacr_native_fidelity as batch
from patent_to_pilot.research.sacr_prompts import build_messages
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from test_sacr_native_fidelity import inputs, bind, ROOT


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False))


def history(tmp_path):
    raw, sample = inputs()
    entries = bind(raw, sample)
    sample_sha = digest(json.dumps(sample).encode())
    prompts = ROOT / 'docs/healthtech/research/prompts'
    for i in range(46):
        q, source, schema = entries[i]
        prompt = build_messages(prompt_root=prompts, kind='profile_quotes', query_id=q,
            source=source, input_kind='DAPFAM_TA', prompt_variant='source_order_v2')
        root = tmp_path / f'profiles/{i:03d}'
        write(root / 'input.json', {'query_id': q, 'source_sha256': digest(source.encode()),
                                  'schema_sha256': schema_digest(schema), 'prompt': prompt})
        write(root / 'profile/reservation.json', {'status': 'RESERVED', 'retry': False,
            'limits': GenerationLimits().__dict__, 'messages_sha256': digest(
                json.dumps(prompt['messages'], ensure_ascii=False, sort_keys=True).encode())})
        if i < 45:
            write(root / 'profile/generation.json', {'status': 'EOS_COMPLETE', 'retry': False,
                'model_calls': 1, 'input_tokens': 100, 'output_tokens': 2,
                'text': '{}', 'response_sha256': digest(b'{}')})
    write(tmp_path / 'declaration.json', {'maximum_calls': 100, 'retry': False,
        'sample_sha256': sample_sha, 'query_sha256': digest(raw), 'prompt_sha256': prompt['prompt_sha256']})
    state = {'Running': False, 'Status': 'exited', 'ExitCode': 137,
             'StartedAt': 'start', 'FinishedAt': 'finish'}
    terminal = json.dumps({'container_state': state}).encode()
    return dict(entries=entries, prior_output=tmp_path, terminal_raw=terminal,
                terminal_sha256=digest(terminal), observed_state=state, prompt_root=prompts,
                sample_sha256=sample_sha, query_sha256=digest(raw))


def test_only_never_started_indices_are_selected(tmp_path):
    manifest = seal_terminal_history(**history(tmp_path))
    assert manifest['selected_indices'] == list(range(46, 100))
    assert manifest['blocked_indices'] == [45]
    assert manifest['maximum_new_profile_calls'] == 54 and manifest['retry_authorized'] is False
    assert verify_history_files(tmp_path, manifest)


def test_normal_invalid_output_is_consumed_not_retryable(tmp_path):
    manifest = seal_terminal_history(**history(tmp_path))
    assert all(r['state'] == 'NORMAL_RETURN_CONSUMED' for r in manifest['records'][:45])
    assert manifest['cohort_fidelity'] == 'INCOMPLETE_NO_PASS'


def test_live_or_wrong_terminal_stops_planning(tmp_path):
    args = history(tmp_path)
    for changes in ({'Running': True}, {'FinishedAt': 'other'}):
        with pytest.raises(InputBoundaryError):
            seal_terminal_history(**{**args, 'observed_state': {**args['observed_state'], **changes}})


def test_source_mismatch_or_history_mutation_stops(tmp_path):
    args = history(tmp_path)
    manifest = seal_terminal_history(**args)
    write(tmp_path / 'profiles/045/profile/generation.json', {})
    with pytest.raises(InputBoundaryError, match='file set'):
        verify_history_files(tmp_path, manifest)
    (tmp_path / 'profiles/045/profile/generation.json').unlink()
    path = tmp_path / 'profiles/000/input.json'
    value = json.loads(path.read_text())
    value['source_sha256'] = '0' * 64
    write(path, value)
    with pytest.raises(InputBoundaryError, match='identity'):
        seal_terminal_history(**args)
    with pytest.raises(InputBoundaryError, match='changed'):
        verify_history_files(tmp_path, manifest)


def runner_args(tmp_path, monkeypatch, remaining):
    prior = tmp_path / 'prior'
    args = history(prior)
    manifest = seal_terminal_history(**args)
    calls = []
    def generate(destination, **kwargs):
        calls.append(int(destination.parent.name))
        record = {'status': 'EOS_COMPLETE', 'model_calls': 1, 'input_tokens': 100,
                  'output_tokens': 2, 'text': '{}', 'response_sha256': digest(b'{}'), 'retry': False}
        write(destination / 'generation.json', record)
        return record
    monkeypatch.setattr(batch, 'run_reserved_attempt', generate)
    prompt_sha = json.loads((prior / 'declaration.json').read_text())['prompt_sha256']
    return calls, dict(entries=args['entries'], prior_output=prior, continuation_manifest=manifest,
        output=canonical_continuation_root(prior, manifest) / 'profiles', prompt_root=args['prompt_root'], prompt_sha256=prompt_sha,
        tokenizer=None, guarded_model_factory=lambda *a: None, device='cuda:0',
        limits=GenerationLimits(), check_authorization=lambda: None,
        remaining_seconds=lambda: remaining, peak_memory_bytes=lambda: 100)


def test_selected_batch_never_calls_consumed_or_interrupted_queries(tmp_path, monkeypatch):
    calls, args = runner_args(tmp_path, monkeypatch, 10000)
    report = batch.run_unstarted_profiles(**args)
    assert calls == list(range(46, 100)) and len(report['outcomes']) == 54
    assert report['status'] == 'SELECTED_PROFILE_BATCH_COMPLETED_COHORT_INCOMPLETE'
    assert report['semantic_status'] == 'NOT_ASSESSED'
    with pytest.raises(FileExistsError):
        batch.run_unstarted_profiles(**args)
    args['output'] = tmp_path / 'another'
    with pytest.raises(InputBoundaryError, match='canonical destination'):
        batch.run_unstarted_profiles(**args)
    assert len(calls) == 54


def test_short_remaining_window_defers_without_reserving_an_attempt(tmp_path, monkeypatch):
    calls, args = runner_args(tmp_path, monkeypatch, 1200)
    report = batch.run_unstarted_profiles(**args)
    assert not calls and report['deferred_indices'] == list(range(46, 100))
    assert report['status'] == 'PROFILE_BATCH_DEFERRED_NO_INFLIGHT_CALL'
    assert not (args['output'] / '046').exists()


def test_forged_selection_cannot_include_interrupted_query(tmp_path, monkeypatch):
    calls, args = runner_args(tmp_path, monkeypatch, 10000)
    args['continuation_manifest']['selected_indices'].insert(0, 45)
    with pytest.raises(InputBoundaryError, match='consumed/blocked'):
        batch.run_unstarted_profiles(**args)
    assert not calls and not args['output'].exists()


def test_grammar_preparation_cannot_spend_the_remaining_call_window(tmp_path, monkeypatch):
    calls, args = runner_args(tmp_path, monkeypatch, 10000)
    times = iter([1201, 1200])
    args['remaining_seconds'] = lambda: next(times)
    result = batch.run_unstarted_profiles(**args)
    assert not calls and result['prepared_not_called_indices'] == [46]
    assert (args['output'] / '046/input.json').exists()
    assert not (args['output'] / '046/profile/reservation.json').exists()
