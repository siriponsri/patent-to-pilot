import json
import pytest

from patent_to_pilot.research.sacr_retry_exception import validate_authority, run_authorized_exception, canonical_exception_root
from patent_to_pilot.research.sacr_native_fidelity import digest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from test_sacr_continuation import runner_args
from patent_to_pilot.research.sacr_retry_exception import validate_closed_continuation
from patent_to_pilot.research.sacr_retry_exception import validate_same_contract


def test_new_valid_model_identity_is_not_same_original_model():
    from copy import deepcopy
    d={k:'original' for k in ('identity_sha256','prompt_sha256','lmfe_source_sha256','query_sha256','sample_sha256')}
    d['files_sha256']={'src/patent_to_pilot/research/'+n+'.py':'same' for n in
        ('sacr_schema','sacr_quote_profile','sacr_alphabet','sacr_escape_callback','sacr_grammar_guard')}
    validate_same_contract(d,deepcopy(d))
    original=deepcopy(d);d['identity_sha256']='different-receipt'
    with pytest.raises(InputBoundaryError,match='original model'):validate_same_contract(d,original)


def test_undercharged_or_unbound_continuation_cannot_admit_exception():
    raw=json.dumps({'wall_seconds':1000,'container_state':{'Running':False,'Status':'exited'}}).encode()
    ledger={'fidelity_generation_charged_seconds':1100,'gpu_conservative_charged_seconds':1200,
        'native_unstarted_continuation_reservation':{'status':'CLOSED_COMPLETE','actual_supervisor_seconds':1000,
        'terminal_sha256':digest(raw),'prior_fidelity_charged_seconds':100,'prior_gpu_charged_seconds':200}}
    assert validate_closed_continuation(raw,ledger,digest(raw),minimum_fidelity_charge=100,minimum_gpu_charge=200)['wall_seconds']==1000
    ledger['native_unstarted_continuation_reservation']['actual_supervisor_seconds']=1
    with pytest.raises(InputBoundaryError):validate_closed_continuation(raw,ledger,digest(raw),minimum_fidelity_charge=100,minimum_gpu_charge=200)
    ledger['native_unstarted_continuation_reservation']['actual_supervisor_seconds']=1000
    ledger['fidelity_generation_charged_seconds']=1099
    with pytest.raises(InputBoundaryError):validate_closed_continuation(raw,ledger,digest(raw),minimum_fidelity_charge=100,minimum_gpu_charge=200)
    ledger['native_unstarted_continuation_reservation']['prior_fidelity_charged_seconds']=0
    ledger['fidelity_generation_charged_seconds']=1000
    with pytest.raises(InputBoundaryError):validate_closed_continuation(raw,ledger,digest(raw),minimum_fidelity_charge=100,minimum_gpu_charge=200)


def grant():
    return {'status':'OWNER_APPROVED_NOT_USED','scope':'original fixed-sample index45 only, interrupted prior attempt',
        'maximum_new_calls':1,'whole_supervisor_limit_seconds':1200,'same_source_prompt_model_decoder':True,
        'charge_to_original_fidelity_and_gpu_ledgers':True,'preserve_prior_attempt_and_unknown_costs':True,
        'on_failure':'STOP_CONFIGURATION_NO_FURTHER_RETRY','requires_reviewed_supervisor':True,'one_gpu_job_at_a_time':True}


@pytest.mark.parametrize('change',[{'maximum_new_calls':2},{'status':'PENDING'},{'scope':'all failed queries'},
                                  {'whole_supervisor_limit_seconds':1201}])
def test_no_broadened_grant(change):
    raw=json.dumps({**grant(),**change}).encode()
    with pytest.raises(InputBoundaryError):validate_authority(raw,digest(raw),wall_seconds=1200)


def test_single_authorized_index_with_failed_output_consumes_exception(tmp_path,monkeypatch):
    calls,args=runner_args(tmp_path,monkeypatch,900)
    raw=json.dumps(grant()).encode()
    args.update(output=canonical_exception_root(args['prior_output'])/'profiles',authorization_raw=raw,
                authorization_sha256=digest(raw),wall_seconds=1200)
    out=run_authorized_exception(**args)
    assert calls==[45]
    assert out['status']=='FAIL_STOP_CONFIGURATION_EXCEPTION_UNUSABLE'
    assert out['further_retry_allowed'] is False
    with pytest.raises(FileExistsError):run_authorized_exception(**args)
    args['output']=tmp_path/'fresh'
    with pytest.raises(InputBoundaryError,match='permanent'):run_authorized_exception(**args)
    assert calls==[45]


def test_completed_query_cannot_be_selected_by_exception(tmp_path,monkeypatch):
    calls,args=runner_args(tmp_path,monkeypatch,900)
    args['continuation_manifest']['records'][45]['state']='NORMAL_RETURN_CONSUMED'
    raw=json.dumps(grant()).encode()
    args.update(output=canonical_exception_root(args['prior_output'])/'profiles',authorization_raw=raw,
                authorization_sha256=digest(raw),wall_seconds=1200)
    with pytest.raises(InputBoundaryError,match='sole original interrupted'):run_authorized_exception(**args)
    assert calls==[]
