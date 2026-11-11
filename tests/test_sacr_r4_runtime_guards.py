import pytest
from patent_to_pilot.research.sacr_r4_runtime_guards import validate_budget
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
def ledger():
    return {'r4_budget_amendment':{'owner_reply':'call_c4ec345a29784975ab45f71412715d87','status':'APPROVED'},
      'gpu_limit_seconds':691200,'gpu_conservative_charged_seconds':9326.788862183224,
      'gpu_remaining_seconds':681873.2111378168,'fidelity_limit_seconds':230400,
      'fidelity_generation_charged_seconds':9047.902037334628,'fidelity_generation_remaining_seconds':221352.09796266537}
def test_amended_budget_keeps_historical_charge():validate_budget(ledger(),1800)
@pytest.mark.parametrize('key,value',[('gpu_limit_seconds',999999),('gpu_conservative_charged_seconds',0),
    ('fidelity_generation_remaining_seconds',230400),('r4_budget_amendment',{}),('gpu_remaining_seconds',float('nan'))])
def test_reset_unapproved_or_inconsistent_budget_rejected(key,value):
    d=ledger();d[key]=value
    with pytest.raises(InputBoundaryError):validate_budget(d,1800)
