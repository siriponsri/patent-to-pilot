import json
import pytest
from test_sacr_r2_bundle_runner import harness, digest
from patent_to_pilot.research.sacr_r3_bundle_runner import run_bundle
from patent_to_pilot.research.sacr_generated_evidence_v3 import CONTRACT
from patent_to_pilot.research.sacr_evidence_v3 import VERSION
from patent_to_pilot.research.sacr_token_profile import source_catalogue
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup(tmp_path,mode=None):
    old,calls=harness(tmp_path,mode)
    executor=old['invoke']
    def invoke(stage,path,messages,schema):
        metrics=executor(stage,path,messages,schema)
        if stage=='profile' and mode not in ('bad_profile','wrong_request','profile_input_limit'):
            source=old['source']
            p={'version':VERSION,'query_id':'q1','source_sha256':digest(source.encode()),'blocks':[
                {'id':'b','evidence':[{'field':'allowed_query','start_token':0,
                 'end_token':len(source_catalogue(source)['tokens'])}], 'roles':{},'conditions':[],'abstraction':None}]}
            if mode=='abstain':p['blocks']=[]
            record=json.loads((path/'generation.json').read_text());text=json.dumps(p)
            record.update(text=text,response_sha256=digest(text.encode()))
            (path/'generation.json').write_text(json.dumps(record))
        return metrics
    args={k:old[k] for k in ('destination','source','query_id','execution','prompt_root','check_admission','maximum_characters')}
    args['execution']['profile_contract']=CONTRACT
    args.update(invoke=invoke,generic_prompt_sha256=old['expected_prompt_hashes']['generic'])
    return args,calls


def test_three_stage_bundle_retains_costs_and_no_semantic_pass(tmp_path):
    args,calls=setup(tmp_path);r=run_bundle(**args)
    assert calls==['profile','generic','critic']
    assert r['costs']['metrics']['model_calls']['value']==3
    assert not r['semantic_pass'] and not r['retrieval_ready']
    with pytest.raises(FileExistsError):run_bundle(**args)


@pytest.mark.parametrize('mode,count',[('bad_profile',1),('abstain',1),('bad_generic',2)])
def test_rejection_preserves_prior_results(tmp_path,mode,count):
    args,calls=setup(tmp_path,mode);r=run_bundle(**args)
    assert r['status']=='UNASSESSABLE' and len(calls)==count
    assert r['costs']['metrics']['model_calls']['value']==count


def test_interrupted_stage_has_unknown_cost_no_retry(tmp_path):
    args,calls=setup(tmp_path,'infra')
    with pytest.raises(RuntimeError):run_bundle(**args)
    failure=json.loads((args['destination']/'failure.json').read_text())
    assert failure['unsettled_attempt']=='generic' and failure['unsettled_attempt_cost']=='UNKNOWN'
    assert calls==['profile','generic']


@pytest.mark.parametrize('stage,expected_calls',[('profile',0),('generic',1),('critic',2)])
def test_input_limit_keeps_zero_call_stage_and_prior_costs(tmp_path,stage,expected_calls):
    args,calls=setup(tmp_path,stage+'_input_limit')
    result=run_bundle(**args)
    assert result['status']=='UNASSESSABLE'
    assert result['costs']['metrics']['model_calls']['value']==expected_calls
    assert len(calls)==expected_calls+1
    assert result['events'][-1]['metrics']['input_tokens']==8193


def test_wrong_request_stops_with_unknown_cost(tmp_path):
    args,calls=setup(tmp_path,'wrong_request')
    with pytest.raises(InputBoundaryError):run_bundle(**args)
    failure=json.loads((args['destination']/'failure.json').read_text())
    assert failure['unsettled_attempt']=='profile' and failure['unsettled_attempt_cost']=='UNKNOWN'
    assert calls==['profile']


def test_denied_admission_does_not_invoke_model(tmp_path):
    args,calls=setup(tmp_path)
    def deny(stage):raise TimeoutError('no budget')
    args['check_admission']=deny
    with pytest.raises(TimeoutError):run_bundle(**args)
    assert calls==[]
    failure=json.loads((args['destination']/'failure.json').read_text())
    assert failure['unsettled_attempt'] is None


@pytest.mark.parametrize('fault',['contract','prompt','limit'])
def test_invalid_preflight_never_creates_attempt(tmp_path,fault):
    args,calls=setup(tmp_path)
    if fault=='contract':args['execution']['profile_contract']='legacy'
    if fault=='prompt':args['generic_prompt_sha256']='0'*64
    if fault=='limit':args['maximum_characters']=True
    with pytest.raises(InputBoundaryError):run_bundle(**args)
    assert calls==[] and not args['destination'].exists()
