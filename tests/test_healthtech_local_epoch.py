"""Synthetic fixture tests: never contact a provider or use the owner's journal."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import hashlib
import json
import sqlite3

import pytest

from patent_to_pilot.providers import local_epoch as epoch
from patent_to_pilot.providers.project_budget import BudgetedTransport
from patent_to_pilot.providers.round1 import Round1ProjectBudget, build_round1_config, request_payload_hash
from patent_to_pilot.providers import BudgetExceededError, ProviderRequest, MockHTTPResponse

MODEL='qwen/qwen3-32b'
ROUTE='deepinfra'
KEY_SCOPE='sha256:'+'e'*64


@pytest.fixture
def setup_epoch(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'appdata'))
    monkeypatch.setenv('XDG_STATE_HOME',str(tmp_path/'appdata'))
    hashes={}
    legacy=tmp_path/'legacy';legacy.mkdir()
    for name in ('live.sqlite3','paired-revalidation-1.sqlite3'):
        path=legacy/name
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE meta(mode TEXT)');db.execute("INSERT INTO meta VALUES('live')")
            db.execute('CREATE TABLE attempts(seq INTEGER,reservation TEXT,finished INTEGER)')
            for seq,cost in enumerate((0.0000132,0.00006),1):
                db.execute('INSERT INTO attempts VALUES(?,?,1)',(seq,json.dumps({'reservation_status':'settled','status':'success','fixture_source':name,'reserved_cost_usd':0.01,'observed_cost_usd':cost})))
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(epoch,'LEGACY_HASHES',hashes)
    args=dict(legacy_directory=legacy,key_scope=KEY_SCOPE,owner_decision=epoch.OWNER_DECISION,
        model_provider_map={MODEL:ROUTE},pricing_snapshot_sha256='a'*64,
        pricing_snapshot_utc=datetime.now(timezone.utc).isoformat())
    epoch.initialize(**args)
    return args


def open_budget(args,**changes):
    selected={k:args[k] for k in ('model_provider_map','pricing_snapshot_sha256','pricing_snapshot_utc')}
    selected.update(changes)
    return Round1ProjectBudget(**selected)


def credit(**changes):
    result=dict(format='ptp-openrouter-credit-snapshot-v2',provider='openrouter',source='owner_sanitized_snapshot',
        as_of_utc=datetime.now(timezone.utc).isoformat(),remaining_credits_usd=1,
        authorization_id=epoch.AUTHORIZATION_ID,account_scope='synthetic-account',key_scope=KEY_SCOPE,
        currency='USD',key_remaining_usd=None,key_limit_unlimited=True)
    result.update(changes);return result


def reserve(budget,attempt='one',amount=.01,**changes):
    args=dict(attempt_id=attempt,phase='canary',model=MODEL,provider=ROUTE,payload_sha256='b'*64,
        upper_bound_usd=amount,bound_verified=True,data_class='public',credit_snapshot=credit())
    args.update(changes);return budget.reserve(**args)


def test_init_preserves_legacy_and_cannot_refresh_allowance(setup_epoch):
    b=open_budget(setup_epoch)
    reserve(b);b.settle('one',.005);b.close()
    again=epoch.initialize(**setup_epoch)
    assert again['attempts']==1 and again['actual_nano_usd']==5_146_400
    assert again['historical_carryover_nano_usd']==146400
    assert again['uncertainty_buffer_nano_usd']==98_999_853_600
    assert again['remaining_to_admission_nano_usd']==995_000_000
    assert again['lifetime_cap_guaranteed'] is False
    assert again['history_completeness']=='UNKNOWN_OWNER_ACCEPTED_CUTOVER'
    with pytest.raises(ValueError,match='cannot reset'):
        epoch.initialize(**(setup_epoch|{'key_scope':'sha256:'+'d'*64}))


def test_new_pricing_keeps_same_ledger_and_spend(setup_epoch):
    b=open_budget(setup_epoch);reserve(b);b.settle('one',.005);path=b.path;b.close()
    b=open_budget(setup_epoch,pricing_snapshot_sha256='c'*64,pricing_snapshot_utc=datetime.now(timezone.utc).isoformat())
    assert b.path==path and b.snapshot()['attempts']==1
    b.close()


@pytest.mark.parametrize('observation',[None,credit(key_scope='sha256:'+'f'*64),credit(as_of_utc='2000-01-01T00:00:00Z'),credit(remaining_credits_usd=0)])
def test_bad_credit_consumes_no_attempt_or_scope(setup_epoch,observation):
    b=open_budget(setup_epoch)
    with pytest.raises((ValueError,BudgetExceededError)):
        reserve(b,credit_snapshot=observation)
    assert b.snapshot()['attempts']==0
    assert b.db.execute('SELECT COUNT(*) FROM budget_epoch_scope').fetchone()[0]==0
    b.close()


def test_pending_recovery_blocks_replay_and_new_dispatch(setup_epoch):
    b=open_budget(setup_epoch);reserve(b);b.settle('one',None);b.close()
    b=open_budget(setup_epoch)
    assert b.snapshot()['unknown_or_pending']==['one']
    for attempt in ('one','two'):
        with pytest.raises(BudgetExceededError):reserve(b,attempt)
    with sqlite3.connect(b.path.with_name('project-api.recovery.sqlite3')) as copy:
        assert copy.execute('SELECT state FROM budget_attempts').fetchone()==('unknown_pending',)
    b.close()


def test_account_is_bound_and_costs_do_not_repeat(setup_epoch):
    b=open_budget(setup_epoch);reserve(b);b.settle('one',.005);b.settle('one',.005)
    assert b.snapshot()['actual_nano_usd']==5_146_400
    with pytest.raises(ValueError,match='conflicting'):b.settle('one',0)
    with pytest.raises(ValueError,match='immutable'):reserve(b,'two',credit_snapshot=credit(account_scope='different-account'))
    b.close()


def test_credit_not_reused_between_settled_calls(setup_epoch):
    b=open_budget(setup_epoch);c=credit(remaining_credits_usd=.015)
    reserve(b,credit_snapshot=c);b.settle('one',.005)
    with pytest.raises(BudgetExceededError):reserve(b,'two',credit_snapshot=c)
    b.close()


def test_overrun_is_preserved_and_blocks_future(setup_epoch):
    b=open_budget(setup_epoch);reserve(b)
    with pytest.raises(BudgetExceededError):b.settle('one',.02)
    assert b.snapshot()['actual_nano_usd']==20_146_400
    with pytest.raises(BudgetExceededError):reserve(b,'two')
    b.close()


def test_two_writers_one_pending_slot_and_consistent_backup(setup_epoch):
    def run(index):
        b=open_budget(setup_epoch)
        try:reserve(b,'parallel-'+str(index));return 'reserved'
        except BudgetExceededError:return 'blocked'
        finally:b.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run,range(2)))==['blocked','reserved']
    b=open_budget(setup_epoch)
    with sqlite3.connect(b.path.with_name('project-api.recovery.sqlite3')) as copy:
        assert copy.execute('SELECT COUNT(*) FROM budget_attempts').fetchone()[0]==1
    b.close()


def test_copy_and_changed_legacy_fail_closed(setup_epoch,tmp_path):
    import shutil
    copy=tmp_path/'copy.sqlite3';shutil.copyfile(epoch.ledger_path(),copy)
    with pytest.raises(Exception,match='not the registered canonical'):
        open_budget(setup_epoch,path=copy)
    source=setup_epoch['legacy_directory']/'live.sqlite3'
    with sqlite3.connect(source) as db:db.execute("UPDATE meta SET mode='mock'")
    with pytest.raises(ValueError,match='changed'):epoch.initialize(**setup_epoch)


def test_live_binding_uses_epoch_and_reserves_before_fake_transport(setup_epoch):
    b=open_budget(setup_epoch)
    cfg=build_round1_config(b.policy,phase='canary',model=MODEL,max_price={'prompt':.08,'completion':.28},live_enabled=True)
    req=ProviderRequest(prompt='synthetic-secret-marker-never-persist',input_tokens_estimate=10,max_output_tokens=10,cost_upper_bound_usd=.01)
    class Fake:
        is_mock=False
        def send(self,**kwargs):
            with sqlite3.connect(b.path) as other:
                assert other.execute('SELECT state FROM budget_attempts').fetchone()==('pending',)
            return MockHTTPResponse(200,{'id':'generation-synthetic','usage':{'cost':.005}})
    wrapped=BudgetedTransport(Fake(),b,dict(attempt_id='transport',phase='canary',payload_sha256=request_payload_hash(cfg,req),
        upper_bound_usd=.01,bound_verified=True,data_class='synthetic',credit_snapshot=credit()))
    wrapped.send(config=cfg,request=req)
    assert b.snapshot()['attempts']==1
    assert b.db.execute('SELECT provider_generation_id FROM budget_attempt_context').fetchone()==('generation-synthetic',)
    assert b'synthetic-secret-marker-never-persist' not in b.path.read_bytes()
    b.close()


def test_phase_limit_prevents_consuming_uncertainty_buffer(setup_epoch):
    b=open_budget(setup_epoch)
    with pytest.raises(BudgetExceededError):reserve(b,amount=.251)
    assert b.snapshot()['attempts']==0
    b.close()
