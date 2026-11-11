import json
import pytest
from test_sacr_r5_bundle_runner import setup as old_setup
from patent_to_pilot.research.sacr_r6_bundle_runner import run_bundle,sha
from patent_to_pilot.research.sacr_r6_candidate import VERSION
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup(tmp_path,mode=None):
    args,calls=old_setup(tmp_path,mode)
    args['execution']['profile_contract']=VERSION
    old=args['invoke'];admissions=[]
    def invoke(stage,path,messages,schema):
        metrics=old(stage,path,messages,schema)
        if stage=='critic':
            assert schema is not None
            if mode!='bad_critic':
                binding=json.loads(messages[1]['content'])['binding_sha256']
                value={'binding_sha256':binding,'dimensions':{k:'supported' for k in schema['properties']['dimensions']['properties']},'findings':[]}
                if mode=='flag':
                    value['dimensions']['essential_coverage']='uncertain'
                    branch=schema['properties']['findings']['items']['anyOf'][0]['properties']
                    value['findings']=[{'dimension':'essential_coverage','artifact':branch['artifact']['enum'][0],
                        'source_units':[branch['source_units']['items']['enum'][0]],'candidate_units':[],'reason':'Authored uncertainty'}]
                text=json.dumps(value)
            else:text='{invalid'
            r=json.loads((path/'generation.json').read_text());r.update(text=text,response_sha256=sha(text.encode()))
            (path/'generation.json').write_text(json.dumps(r))
        if mode=='mutate_request':messages[0]['content']='changed'
        return metrics
    args['invoke']=invoke
    def count(messages):
        stage=['profile','generic','critic'][len(admissions)];admissions.append(stage)
        return 8193 if mode==stage+'_prelimit' else 10
    args['count_tokens']=count
    return args,calls,admissions


def test_actual_three_stage_order_with_guarded_critic_and_no_fidelity_claim(tmp_path):
    args,calls,admissions=setup(tmp_path);r=run_bundle(**args)
    assert calls==admissions==['profile','generic','critic']
    assert r['status']=='AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS'
    assert r['costs']['metrics']['model_calls']['value']==3 and not r['semantic_pass']
    assert all((args['destination']/s/'r6-binding.json').exists() for s in calls)
    with pytest.raises(FileExistsError):run_bundle(**args)


@pytest.mark.parametrize('mode,count',[('bad_profile',1),('abstain',1),('bad_generic',2),('bad_critic',3),
    ('profile_prelimit',0),('generic_prelimit',1),('critic_prelimit',2)])
def test_normal_rejections_and_token_limits_preserve_costs_without_retry(tmp_path,mode,count):
    args,calls,_=setup(tmp_path,mode);r=run_bundle(**args)
    assert r['status']=='UNASSESSABLE' and len(calls)==count
    assert not (args['destination']/'failure.json').exists()
    if count:assert r['costs']['metrics']['model_calls']['value']==count
    if mode=='critic_prelimit':assert (args['destination']/'generic-views.json').exists()


@pytest.mark.parametrize('mode',['infra','wrong_request','mutate_request'])
def test_unknown_or_integrity_fault_stops_dependent_calls(tmp_path,mode):
    args,calls,_=setup(tmp_path,mode)
    with pytest.raises((RuntimeError,InputBoundaryError)):run_bundle(**args)
    failure=json.loads((args['destination']/'failure.json').read_text())
    assert failure['unsettled_attempt_cost']=='UNKNOWN' and 'critic' not in calls
    with pytest.raises(FileExistsError):run_bundle(**args)


def test_valid_critic_flags_remain_separate_from_invalid_evaluator(tmp_path):
    args,calls,_=setup(tmp_path,'flag');r=run_bundle(**args)
    assert r['status']=='AUTOMATIC_METHOD_FLAG' and r['screening']['evaluator_contract']=='VALID'
    assert not r['semantic_pass']


def test_denied_admission_never_invokes_or_tokenizes(tmp_path):
    args,calls,admissions=setup(tmp_path)
    def deny(stage):raise TimeoutError('no budget')
    args['check_admission']=deny
    with pytest.raises(TimeoutError):run_bundle(**args)
    assert calls==admissions==[]


@pytest.mark.parametrize('target',['render_views','review_request'])
def test_deterministic_implementation_fault_is_not_model_rejection(tmp_path,monkeypatch,target):
    from patent_to_pilot.research import sacr_r6_bundle_runner as runner
    args,calls,_=setup(tmp_path)
    def broken(*a,**k):raise KeyError('authored implementation bug')
    monkeypatch.setattr(runner,target,broken)
    with pytest.raises(KeyError):run_bundle(**args)
    assert not (args['destination']/'result.json').exists()
    failure=json.loads((args['destination']/'failure.json').read_text())
    assert failure['unsettled_attempt'] is None
    assert len(calls)==(1 if target=='render_views' else 2)


def test_mutating_token_counter_stops_before_backend(tmp_path):
    args,calls,_=setup(tmp_path)
    def bad(messages):messages[0]['content']='mutated';return 10
    args['count_tokens']=bad
    with pytest.raises(InputBoundaryError,match='token counter'):run_bundle(**args)
    assert calls==[]


def test_completed_cost_not_reclassified_unknown_on_binding_disk_failure(tmp_path,monkeypatch):
    from patent_to_pilot.research import sacr_r6_bundle_runner as runner
    args,calls,_=setup(tmp_path);write=runner.write_new
    def fail(path,value):
        if path.name=='r6-binding.json':raise OSError('authored disk fault')
        return write(path,value)
    monkeypatch.setattr(runner,'write_new',fail)
    with pytest.raises(OSError):run_bundle(**args)
    f=json.loads((args['destination']/'failure.json').read_text())
    assert f['unsettled_attempt'] is None and len(f['events'])==1
    assert f['events'][0]['metrics']['model_calls']==1
