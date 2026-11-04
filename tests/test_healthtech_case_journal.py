import json
import pytest
from patent_to_pilot.providers.case_journal import PrivateCaseJournal
from patent_to_pilot.providers.round1 import Round1ProjectBudget
from patent_to_pilot.healthtech.api_generation import OpenRouterQwenGenerationRunner
from patent_to_pilot.healthtech.b4_live import B4Pricing
from test_healthtech_api_generation import _load_fixture_builder, MockGenerationTransport


@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'state'))
    monkeypatch.setenv('XDG_STATE_HOME',str(tmp_path/'state'))
    return tmp_path


def setup_runner(tmp_path,transport=None):
    pack=_load_fixture_builder()._synthetic_pack(tmp_path)
    pricing=B4Pricing(model='qwen/qwen3-32b',upstream_provider='DeepInfra',snapshot_sha256='a'*64,
        snapshot_utc='2026-10-31T00:00:00Z',prompt_usd_per_million='.08',completion_usd_per_million='.28',max_price_prompt=.08,max_price_completion=.28)
    budget=Round1ProjectBudget(tmp_path/'mock.sqlite3',model_provider_map={pricing.model:pricing.upstream_provider},
        pricing_snapshot_sha256=pricing.snapshot_sha256,pricing_snapshot_utc=pricing.snapshot_utc,namespace='mock')
    runner=OpenRouterQwenGenerationRunner(budget=budget,pricing=pricing,transport_factory=lambda:transport or MockGenerationTransport(),run_id='fixture')
    return pack,budget,runner


def test_outputs_survive_close_and_public_receipt_omits_text(isolated):
    pack,budget,runner=setup_runner(isolated)
    try:
        with PrivateCaseJournal('valid') as private:
            runner.case_observer=private.write
            result=runner.run(pack)
            path=private.path
        saved=[json.loads(line) for line in path.read_text().splitlines()]
        assert len(saved)==4
        assert all('output_text' in row['case'] and row['case']['billing_state']=='settled' for row in saved[1:])
        safe=runner.sanitized_receipt(result)
        assert all('output_text' not in row and 'parsed_output' not in row for row in safe['cases'])
    finally:budget.close()


def test_invalid_generated_json_is_kept_for_review(isolated):
    class Invalid(MockGenerationTransport):
        def send(self,**kwargs):
            response=super().send(**kwargs)
            response.payload['choices'][0]['message']['content']='INVALID SYNTHETIC MODEL OUTPUT'
            return response
    pack,budget,runner=setup_runner(isolated,Invalid())
    try:
        with PrivateCaseJournal('invalid') as private:
            runner.case_observer=private.write;result=runner.run(pack);path=private.path
        cases=[json.loads(line)['case'] for line in path.read_text().splitlines()[1:]]
        assert len(cases)==3 and all(c['status']=='FAILED' for c in cases)
        assert all(c['output_text']=='INVALID SYNTHETIC MODEL OUTPUT' for c in cases)
    finally:budget.close()


def test_sink_failure_stops_before_next_attempt(isolated):
    pack,budget,runner=setup_runner(isolated)
    def fail(case):raise OSError('synthetic disk failure')
    runner.case_observer=fail
    try:
        with pytest.raises(OSError):runner.run(pack)
        assert budget.snapshot()['attempts']==1
        assert budget.db.execute('SELECT state FROM budget_attempts').fetchone()==('settled',)
    finally:budget.close()


def test_existing_run_is_never_overwritten_and_keys_not_written(isolated):
    with PrivateCaseJournal('once') as private:
        private.write({'case_id':'one','output_text':'synthetic','api_key':'FORBIDDEN_SECRET_MARKER','messages':['FORBIDDEN_INPUT_MARKER']})
        path=private.path
        with pytest.raises(FileExistsError):PrivateCaseJournal('once')
    before=path.read_bytes()
    with pytest.raises(FileExistsError):PrivateCaseJournal('once')
    assert path.read_bytes()==before and b'FORBIDDEN' not in before


@pytest.mark.parametrize('run_id',['../escape','a/b','x\\y','', 'a'*81])
def test_bad_run_id_is_rejected_before_creation(isolated,run_id):
    with pytest.raises(ValueError):PrivateCaseJournal(run_id)


def test_interleaved_accounting_does_not_inflate_this_run(isolated):
    pack,budget,runner=setup_runner(isolated)
    def interleaved(case):
        other='other-'+case['attempt_id']
        budget.reserve(attempt_id=other,phase='paired_pilot',model='qwen/qwen3-32b',provider='DeepInfra',
            payload_sha256='e'*64,upper_bound_usd=.02,bound_verified=True,data_class='synthetic')
        budget.settle(other,.02)
    runner.case_observer=interleaved
    try:
        result=runner.run(pack)
        assert result['ledger_snapshot']['attempts']==6
        assert result['ledger_snapshot']['actual_nano_usd']==60_000_000
        assert result['provider_calls']==result['reserved_attempts']==result['transport_invocations']==3
        assert result['known_debit_usd']==0 and result['billing_complete'] is True
    finally:budget.close()
