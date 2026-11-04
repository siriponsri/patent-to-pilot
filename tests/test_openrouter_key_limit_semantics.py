import json
from decimal import Decimal
import pytest
from patent_to_pilot.providers import metadata_observation as m

def raw(**changes):
    return dict(limit=None, limit_remaining=None, usage=0, budgets=[], effective_budget=None, **changes)

def test_explicit_null_is_unlimited_but_not_account_credit(monkeypatch):
    monkeypatch.setattr(m, 'endpoint_request', lambda *a: ({'status':'OBSERVED','http_status':200}, raw()))
    result=m.collect('fake-key')
    assert result['format']=='ptp-openrouter-metadata-observation-v2'
    assert result['key_metadata']['key_limit_state']=='UNLIMITED'
    assert result['key_metadata']['field_presence']==dict(limit=True,limit_remaining=True,budgets=True,effective_budget=True)
    assert result['availability']['blocked_prerequisites']==['ACCOUNT_CREDIT_NOT_OBSERVED_BY_THIS_COLLECTOR','ACCOUNT_KEY_BINDING_NOT_RECONCILED']
    assert result['live_admission_enabled'] is False
    assert 'fake-key' not in json.dumps(result)

@pytest.mark.parametrize('missing', ['limit','limit_remaining'])
def test_absent_field_is_not_unlimited(missing):
    data=raw();del data[missing]
    result=m.sanitize_key(data)
    assert result['field_presence'][missing] is False
    assert result['key_limit_state']=='UNAVAILABLE_FIELD_PRESENCE'

def test_legacy_null_cannot_be_relabelled():
    assert m.key_limit_state(dict(limit=None,limit_remaining=None))=='UNAVAILABLE_FIELD_PRESENCE'

@pytest.mark.parametrize('limit,remaining,expected', [(10,2,'LIMITED'),(0,0,'EXHAUSTED'),(10,0,'EXHAUSTED'),(10,-1,'EXHAUSTED'),(None,1,'INCONSISTENT'),(1,None,'INCONSISTENT'),(1,2,'INCONSISTENT')])
def test_finite_exhausted_and_inconsistent(limit,remaining,expected):
    data=raw();data.update(limit=limit,limit_remaining=remaining)
    assert m.sanitize_key(data)['key_limit_state']==expected

def test_unlimited_key_still_has_exhausted_workspace_budget():
    data=raw();data['budgets']=[dict(scope='workspace',limit_usd=10,spend_usd=11,remaining_usd=-1)]
    result=m.availability_summary(dict(key_metadata=m.sanitize_key(data)))
    assert result['key_limit_state']=='UNLIMITED'
    assert result['observed_key_or_budget_remaining_usd']=='-1'
    assert 'APPLICABLE_KEY_OR_BUDGET_EXHAUSTED' in result['blocked_prerequisites']

@pytest.mark.parametrize('field',['budgets','effective_budget'])
def test_missing_budget_fields_stay_unknown(field):
    data=raw();del data[field]
    result=m.availability_summary(dict(key_metadata=m.sanitize_key(data)))
    assert result['applicable_budgets_observed'] is False

def test_effective_budget_can_tighten_key_remaining():
    data=raw();data.update(limit=10,limit_remaining=5,effective_budget=dict(scope='member',limit_usd=2,spend_usd=1,remaining_usd=1))
    result=m.availability_summary(dict(key_metadata=m.sanitize_key(data)))
    assert result['observed_key_or_budget_remaining_usd']=='1'

def test_endpoint_failure_cannot_become_no_limit(monkeypatch):
    monkeypatch.setattr(m,'endpoint_request',lambda *a: ({'status':'HTTP_REJECTED','http_status':401},None))
    result=m.collect('fake-key')
    assert result['availability']['key_limit_state']=='UNAVAILABLE_FIELD_PRESENCE'
    assert result['live_admission_enabled'] is False
