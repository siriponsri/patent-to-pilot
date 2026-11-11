import hashlib
import json
import pytest
from test_sacr_controller import setup
from test_sacr_generated_view_controller import evidence
from test_sacr_profile import SOURCE
from patent_to_pilot.research.sacr_evidence_v3 import VERSION
from patent_to_pilot.research.sacr_evidence_prompt_v3 import build_messages
from patent_to_pilot.research.sacr_generated_evidence_v3 import CONTRACT, generated_evidence_result, replay_generated_evidence
from patent_to_pilot.research.sacr_generated_view import GenerationEvidenceFailure
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def inputs(tmp_path,status='EOS_COMPLETE',bad=False):
    controller=setup(tmp_path)
    proposal={'version':VERSION,'query_id':'q','source_sha256':hashlib.sha256(SOURCE.encode()).hexdigest(),'blocks':[]}
    raw,identity,costs=evidence(controller,'profile',status=status,text='{' if bad else json.dumps(proposal))
    execution=dict(controller.journal.execution);execution['profile_contract']=CONTRACT
    reservation={'status':'RESERVED','retry':False,'limits':{k:execution['limits'][k] for k in
                ('input_tokens','output_tokens','context_tokens','response_bytes')},
                'messages_sha256':hashlib.sha256(json.dumps(build_messages(SOURCE,'q'),ensure_ascii=False,sort_keys=True).encode()).hexdigest()}
    return raw,identity,dict(execution=execution,attempt_id='profile',query_id='q',source=SOURCE,metrics=costs,reservation=reservation)


def test_bound_abstention_and_replay(tmp_path):
    raw,identity,args=inputs(tmp_path)
    out=generated_evidence_result(raw,identity,**args)
    assert out['prepared']['compiled']['anchor_fallback_required']
    assert not out['semantic_pass'] and out['generation']['record']['model_calls']==1
    replay_args={k:v for k,v in args.items() if k!='reservation'}
    assert replay_generated_evidence(out,**replay_args)==out
    out['retrieval_ready']=True
    with pytest.raises(InputBoundaryError): replay_generated_evidence(out,**replay_args)


@pytest.mark.parametrize('status,bad',[('NO_EOS',False),('EOS_COMPLETE',True)])
def test_rejected_output_retains_cost_and_bytes(tmp_path,status,bad):
    raw,identity,args=inputs(tmp_path,status,bad)
    with pytest.raises(GenerationEvidenceFailure) as error: generated_evidence_result(raw,identity,**args)
    assert error.value.output['generation_artifact_utf8'].encode()==raw
    assert error.value.metrics==args['metrics']


@pytest.mark.parametrize('fault',['request','artifact','cost'])
def test_unbound_evidence_stops(tmp_path,fault):
    raw,identity,args=inputs(tmp_path)
    if fault=='request':args['reservation']['messages_sha256']='0'*64
    if fault=='artifact':identity['artifact_sha256']='0'*64
    if fault=='cost':args['metrics']['input_tokens']+=1
    with pytest.raises(InputBoundaryError):generated_evidence_result(raw,identity,**args)
