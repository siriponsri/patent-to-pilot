import hashlib
import json
import pytest
from test_sacr_generated_evidence_v3 import inputs
from patent_to_pilot.research.sacr_generated_critic_v3 import generated_critic_result
from patent_to_pilot.research.sacr_evidence_review_v3 import review_payload
from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS
from patent_to_pilot.research.sacr_generated_view import GenerationEvidenceFailure
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def critic_inputs(tmp_path,bad=False,status='EOS_COMPLETE'):
    raw,identity,args=inputs(tmp_path,status=status)
    record=json.loads(raw);proposal=json.loads(record['text'])
    text='{' if bad else json.dumps({'query_id':'q','source_sha256':proposal['source_sha256'],
               'dimensions':{d:'supported' for d in DIMENSIONS},'findings':[]})
    record.update(text=text,response_sha256=hashlib.sha256(text.encode()).hexdigest())
    raw=json.dumps(record).encode();identity.update(kind='critic',artifact_sha256=hashlib.sha256(raw).hexdigest())
    messages=review_payload(proposal,source=args['source'],query_id='q')['messages']
    args['reservation']['messages_sha256']=hashlib.sha256(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    args['proposal']=proposal
    return raw,identity,args


def test_bound_critic_does_not_promote_abstention(tmp_path):
    raw,identity,args=critic_inputs(tmp_path)
    result=generated_critic_result(raw,identity,**args)
    assert result['review']['status']=='ABSTENTION_REQUIRES_POLICY_NOT_FIDELITY_PASS'
    assert not result['semantic_pass'] and result['generation']['record']['model_calls']==1


@pytest.mark.parametrize('bad,status',[(True,'EOS_COMPLETE'),(False,'NO_EOS')])
def test_critic_failure_retains_cost(tmp_path,bad,status):
    raw,identity,args=critic_inputs(tmp_path,bad,status)
    with pytest.raises(GenerationEvidenceFailure) as e:generated_critic_result(raw,identity,**args)
    assert e.value.metrics==args['metrics']
    assert e.value.output['generation_artifact_utf8'].encode()==raw


def test_wrong_reservation_not_treated_as_normal_rejection(tmp_path):
    raw,identity,args=critic_inputs(tmp_path)
    args['reservation']['messages_sha256']='0'*64
    with pytest.raises(InputBoundaryError) as e:generated_critic_result(raw,identity,**args)
    assert not isinstance(e.value,GenerationEvidenceFailure)


def test_generic_control_cannot_be_added_after_critic_request(tmp_path):
    raw,identity,args=critic_inputs(tmp_path)
    args['generic_views']=['A generic mechanism.']
    with pytest.raises(InputBoundaryError): generated_critic_result(raw,identity,**args)


def test_generic_control_receives_lexical_screen(tmp_path):
    from patent_to_pilot.research.sacr_evidence_review_v3 import lexical_screen
    _,_,args=critic_inputs(tmp_path)
    result=lexical_screen(args['proposal'],source=args['source'],query_id='q',
                          maximum_characters=8192,generic_views=['Invented 999999 psi.'])
    assert result['status']=='ESCALATE'
    assert 'numeric_literal_inventory_changed' in result['views']['generic_0']['rejection_reasons']
