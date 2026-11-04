from datetime import datetime, timezone, timedelta
import hashlib, json
import pytest
from patent_to_pilot.providers import metadata_observation as m
from patent_to_pilot.providers.credit_from_metadata import credit_from_metadata
from patent_to_pilot.providers.credit import FORMAT

def signed(meta):
    raw={k:v for k,v in meta.items() if k!='receipt_sha256'}
    return raw|{'receipt_sha256':hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()}

@pytest.fixture
def observations(monkeypatch):
    monkeypatch.setattr(m,'endpoint_request',lambda *a: ({'status':'OBSERVED','http_status':200},dict(limit=None,limit_remaining=None,usage=0,budgets=[],effective_budget=None)))
    meta=m.collect('fake-only')
    now=datetime.now(timezone.utc)
    account=dict(format=FORMAT,provider='openrouter',currency='USD',source='owner_sanitized_snapshot',
                 authorization_id='test-authority',account_scope='test-account',key_scope=meta['key_scope'],
                 as_of_utc=now.isoformat(),remaining_credits_usd='0.5')
    return meta,account,now

def test_unlimited_key_keeps_observed_account_cap(observations):
    meta,account,now=observations
    result=credit_from_metadata(meta,account,now=now)
    assert result['key_limit_unlimited'] is True and result['key_remaining_usd'] is None
    assert result['remaining_credits_usd']==.5
    assert result['as_of_utc']==meta['started_at_utc']

def test_workspace_budget_tightens_unlimited_key(observations):
    meta,account,now=observations
    meta['key_metadata']['budgets']=[dict(scope='workspace',limit_usd='1',spend_usd='.9',remaining_usd='.1')]
    result=credit_from_metadata(signed(meta),account,now=now)
    assert result['key_remaining_usd']==.1 and result['key_limit_unlimited'] is False

@pytest.mark.parametrize('change',['wrong_key','old_key','old_account','future_account','bad_hash','legacy','exhausted','missing_budget'])
def test_incomplete_or_conflicting_observations_rejected(observations,change):
    meta,account,now=observations
    if change=='wrong_key':account['key_scope']='different'
    if change=='old_key':meta['started_at_utc']=(now-timedelta(seconds=301)).isoformat();meta=signed(meta)
    if change=='old_account':account['as_of_utc']=(now-timedelta(seconds=301)).isoformat()
    if change=='future_account':account['as_of_utc']=(now+timedelta(seconds=1)).isoformat()
    if change=='bad_hash':meta['key_metadata']['usage']='1'
    if change=='legacy':meta['format']='ptp-openrouter-metadata-observation-v1';meta=signed(meta)
    if change=='exhausted':meta['key_metadata']['budgets']=[dict(scope='workspace',remaining_usd='0')];meta=signed(meta)
    if change=='missing_budget':meta['key_metadata']['field_presence']['budgets']=False;meta=signed(meta)
    with pytest.raises(ValueError):credit_from_metadata(meta,account,now=now)

def test_cli_exclusive_write_and_allowlisted_output(observations,monkeypatch,tmp_path):
    from patent_to_pilot.providers.credit_from_metadata import main
    import sys
    meta,account,now=observations
    account['secret_extra']='DO_NOT_COPY'
    mp=tmp_path/'key.json';ap=tmp_path/'account.json';out=tmp_path/'joined.json'
    mp.write_text(json.dumps(meta));ap.write_text(json.dumps(account))
    monkeypatch.setattr(sys,'argv',['join','--key-observation',str(mp),'--account-observation',str(ap),'--output',str(out)])
    main()
    before=out.read_bytes()
    assert b'DO_NOT_COPY' not in before
    with pytest.raises(SystemExit,match='CREDIT_JOIN_FAILED_NO_RAW_DETAILS'):main()
    assert out.read_bytes()==before


def test_equivalent_local_offset_preserves_instant_and_freshness(observations):
    meta,account,now=observations
    original=datetime.fromisoformat(meta['started_at_utc'])
    meta['started_at_utc']=original.astimezone(timezone(timedelta(hours=7))).isoformat()
    meta=signed(meta)
    result=credit_from_metadata(meta,account,now=now)
    assert result['as_of_utc']==original.astimezone(timezone.utc).isoformat()
    with pytest.raises(ValueError,match='stale'):
        credit_from_metadata(meta,account,now=now+timedelta(seconds=301))

def test_naive_metadata_timestamp_remains_rejected(observations):
    meta,account,now=observations
    meta['started_at_utc']=now.replace(tzinfo=None).isoformat()
    with pytest.raises(ValueError,match='timezone'):
        credit_from_metadata(signed(meta),account,now=now)
