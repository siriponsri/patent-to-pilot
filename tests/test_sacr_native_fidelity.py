import json
import importlib.util
from pathlib import Path
import pytest

from patent_to_pilot.research import sacr_native_fidelity as batch
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_schema import quote_profile_schema
from patent_to_pilot.research.sacr_solo_fidelity import fixed_sample
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'Reduce reverse flow without electrical power.'


def inputs():
    rows = [{'id': f'q{i}', 'text': SOURCE} for i in range(474)]
    raw = ('\n'.join(json.dumps(r) for r in rows) + '\n').encode()
    ids = fixed_sample('DAPFAM', [r['id'] for r in rows])
    entries = [{'query_id': q, 'source_sha256': batch.digest(SOURCE.encode()),
        'schema_sha256': batch.schema_digest(quote_profile_schema(source=SOURCE, query_id=q, input_kind='DAPFAM_TA'))}
        for q in ids]
    sample = {'version': 'sacr-native-fidelity-sample-v1', 'benchmark': 'DAPFAM',
              'population': 474, 'source_sha256': batch.digest(raw), 'entries': entries}
    return raw, sample


def bind(raw, sample):
    sraw = json.dumps(sample).encode()
    return batch.bind_sample(raw, sraw, query_sha256=batch.digest(raw), sample_sha256=batch.digest(sraw))


def test_native_binding_rejects_rehashed_selection_and_schema_changes():
    raw, sample = inputs()
    assert len(bind(raw, sample)) == 100
    sample['entries'].reverse()
    with pytest.raises(InputBoundaryError, match='identity'):
        bind(raw, sample)
    sample['entries'].reverse()
    sample['entries'][0]['schema_sha256'] = '0' * 64
    with pytest.raises(InputBoundaryError, match='identity'):
        bind(raw, sample)


def run(tmp_path, monkeypatch, fail_at=None):
    raw, sample = inputs()
    entries = bind(raw, sample)
    calls = []
    def attempt(destination, **kwargs):
        calls.append(destination)
        destination.mkdir()
        if len(calls) == fail_at:
            raise RuntimeError('infrastructure interrupted')
        record = {'status': 'EOS_COMPLETE', 'model_calls': 1, 'input_tokens': 100,
                  'output_tokens': 2, 'text': '{invalid', 'retry': False,
                  'response_sha256': batch.digest(b'{invalid')}
        batch.write_new(destination / 'generation.json', record)
        return record
    monkeypatch.setattr(batch, 'run_reserved_attempt', attempt)
    prompt_root = ROOT / 'docs/healthtech/research/prompts'
    prompt_sha = batch.build_messages(prompt_root=prompt_root, kind='profile_quotes',
        source=SOURCE, query_id=entries[0][0], input_kind='DAPFAM_TA', prompt_variant='source_order_v2')['prompt_sha256']
    kwargs = dict(entries=entries, output=tmp_path / 'batch', prompt_root=prompt_root,
        prompt_sha256=prompt_sha, tokenizer=None, guarded_model_factory=lambda *args: None,
        device='cuda:0', limits=GenerationLimits(), check_authorization=lambda: None,
        remaining_seconds=lambda: 1000, peak_memory_bytes=lambda: 100)
    return calls, kwargs


def test_rejected_completed_profiles_preserve_costs_and_never_resume(tmp_path, monkeypatch):
    calls, kwargs = run(tmp_path, monkeypatch)
    result = batch.run_profiles(**kwargs)
    assert len(calls) == 100
    assert all(o['status'] == 'REJECTED_GENERATED_FAMILY' for o in result['outcomes'])
    assert sum(o['metrics']['model_calls'] for o in result['outcomes']) == 100
    assert result['semantic_status'] == 'NOT_ASSESSED'
    with pytest.raises(FileExistsError):
        batch.run_profiles(**kwargs)
    assert len(calls) == 100


def test_infrastructure_failure_stops_remaining_queries(tmp_path, monkeypatch):
    calls, kwargs = run(tmp_path, monkeypatch, fail_at=2)
    with pytest.raises(RuntimeError):
        batch.run_profiles(**kwargs)
    assert len(calls) == 2
    failure = json.loads((kwargs['output'] / 'failure.json').read_text())
    assert len(failure['completed_outcomes']) == 1
    assert failure['incomplete_attempt_cost'].startswith('UNKNOWN')
    assert not (kwargs['output'] / 'completion.json').exists()


def test_deadline_prevents_first_model_call(tmp_path, monkeypatch):
    calls, kwargs = run(tmp_path, monkeypatch)
    kwargs['remaining_seconds'] = lambda: 5
    with pytest.raises(TimeoutError):
        batch.run_profiles(**kwargs)
    assert not calls


def test_cli_requires_all_source_pins_and_prompt_agreement():
    spec = importlib.util.spec_from_file_location('native_cli', ROOT / 'scripts/healthtech/run_sacr_native_fidelity.py')
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    with pytest.raises(InputBoundaryError, match='mandatory'):
        cli.validate_code_declaration({'files_sha256': {}}, ROOT)
    hashes = {name: batch.digest((ROOT / name).read_bytes()) for name in cli.REQUIRED_FILES}
    declaration = {'files_sha256': hashes, 'prompt_sha256': '0' * 64}
    with pytest.raises(InputBoundaryError, match='prompt'):
        cli.validate_code_declaration(declaration, ROOT)
    declaration['prompt_sha256'] = hashes['docs/healthtech/research/prompts/sacr_profile_quotes_order_v2.txt']
    cli.validate_code_declaration(declaration, ROOT)
