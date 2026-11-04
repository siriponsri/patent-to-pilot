from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import pytest
from patent_to_pilot.providers import metadata_observation as m
from patent_to_pilot.providers.owner_credit_capture import capture

def setup(monkeypatch):
    monkeypatch.setattr(m,'endpoint_request',lambda *a: ({'status':'OBSERVED','http_status':200},dict(limit=None,limit_remaining=None,usage=0,budgets=[],effective_budget=None)))
    meta=m.collect('FAKE_ONLY')
    calls=[]
    def observer(key_file,path):
        calls.append(str(path));Path(path).write_text(json.dumps(meta));return 'OBSERVED'
    binding={'key_scope':meta['key_scope'],'account_scope':'owner-test-account'}
    return meta,calls,observer,binding

def test_owner_input_yields_scoped_snapshot_no_secret(monkeypatch,tmp_path):
    meta,calls,observer,binding=setup(monkeypatch)
    answers=iter(['SAME ACCOUNT','0.5'])
    output=capture('fake.env',tmp_path/'new',binding,ask=lambda p:next(answers),observer=observer)
    result=json.loads(output.read_text())
    assert result['source']=='owner_sanitized_snapshot' and result['remaining_credits_usd']==.5
    assert result['key_limit_unlimited'] and len(calls)==1
    assert 'FAKE_ONLY' not in ''.join(p.read_text() for p in output.parent.glob('*.json'))
    assert json.loads((output.parent/'owner-attestation.json').read_text())['automated_balance_verification'] is False

@pytest.mark.parametrize('answers',[[''],['no'],['SAME ACCOUNT','nan'],['SAME ACCOUNT','-1'],['SAME ACCOUNT','sk-or-fake'],['SAME ACCOUNT','1,000']])
def test_missing_confirmation_or_bad_balance_stops_before_request(monkeypatch,tmp_path,answers):
    meta,calls,observer,binding=setup(monkeypatch)
    answers=iter(answers)
    with pytest.raises(ValueError):capture('fake',tmp_path/'new',binding,ask=lambda p:next(answers),observer=observer)
    assert not calls and not (tmp_path/'new').exists()

def test_existing_dir_not_overwritten(monkeypatch,tmp_path):
    meta,calls,observer,binding=setup(monkeypatch)
    answers=iter(['SAME ACCOUNT','1'])
    with pytest.raises(FileExistsError):capture('fake',tmp_path,binding,ask=lambda p:next(answers),observer=observer)
    assert not calls

def test_wrong_dispatch_key_retains_receipts_but_no_snapshot(monkeypatch,tmp_path):
    meta,calls,observer,binding=setup(monkeypatch);binding['key_scope']='different'
    answers=iter(['SAME ACCOUNT','1'])
    with pytest.raises(ValueError):capture('fake',tmp_path/'new',binding,ask=lambda p:next(answers),observer=observer)
    assert len(calls)==1 and (tmp_path/'new/key-observation.json').exists()
    assert not (tmp_path/'new/credit-snapshot.json').exists()

def test_stale_human_input_prevents_request(monkeypatch,tmp_path):
    meta,calls,observer,binding=setup(monkeypatch)
    now=datetime.now(timezone.utc);times=iter([now,now+timedelta(seconds=301)])
    answers=iter(['SAME ACCOUNT','1'])
    with pytest.raises(ValueError):capture('fake',tmp_path/'new',binding,ask=lambda p:next(answers),clock=lambda:next(times),observer=observer)
    assert not calls

def test_failed_observer_not_retried(monkeypatch,tmp_path):
    meta,calls,observer,binding=setup(monkeypatch)
    def failed(*args):calls.append(1);return 'HTTP_REJECTED'
    answers=iter(['SAME ACCOUNT','1'])
    with pytest.raises(ValueError):capture('fake',tmp_path/'new',binding,ask=lambda p:next(answers),observer=failed)
    assert len(calls)==1 and not (tmp_path/'new/credit-snapshot.json').exists()

@pytest.mark.parametrize('existing',[False,True])
def test_read_binding_does_not_write_and_reuses_existing_alias(monkeypatch,tmp_path,existing):
    import sqlite3,hashlib
    from patent_to_pilot.providers import owner_credit_capture as module
    path=tmp_path/'ledger.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE budget_epoch_scope(singleton INTEGER,account_scope TEXT,key_scope TEXT)')
        if existing:db.execute("INSERT INTO budget_epoch_scope VALUES(1,'previous-account','sha256:abc')")
    monkeypatch.setattr(module,'read_epoch',lambda db:{'key_scope':'sha256:abc'})
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    result=module.read_binding(path)
    assert result['account_scope']==('previous-account' if existing else 'owner-asserted-account:abc')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before

def test_read_binding_never_creates_missing_ledger(tmp_path):
    import sqlite3
    from patent_to_pilot.providers.owner_credit_capture import read_binding
    path=tmp_path/'missing.db'
    with pytest.raises(sqlite3.OperationalError):read_binding(path)
    assert not path.exists()
