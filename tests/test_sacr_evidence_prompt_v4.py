from copy import deepcopy
import hashlib,json
import pytest
from jsonschema import Draft202012Validator,ValidationError
from patent_to_pilot.research.sacr_evidence_prompt_v4 import contexts,proposal_schema,validate_proposal,build_messages
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

SOURCE='A valve stops reverse flow. It operates below 40 C without power.'
def ref(s,e):return {'field':'allowed_query','start_token':s,'end_token':e}
def proposal():
    return {'version':'sacr-evidence-roles-v3','query_id':'q','source_sha256':hashlib.sha256(SOURCE.encode()).hexdigest(),
            'blocks':[{'id':'b','evidence':[ref(0,5)],'roles':{'action':[ref(2,3)]},'conditions':[],
                       'abstraction':'A passive flow-control mechanism.'}]}

def test_role_outside_selected_context_is_schema_rejected():
    p=proposal();p['blocks'][0]['roles']['quantity']=[ref(8,9)]
    with pytest.raises(ValidationError):Draft202012Validator(proposal_schema(SOURCE,'q')).validate(p)
    with pytest.raises(InputBoundaryError):validate_proposal(p,SOURCE,'q')

def test_full_context_role_is_only_structural_not_semantic_pass():
    p=proposal();p['blocks'][0]['evidence']=[ref(0,12)]
    p['blocks'][0]['roles']['quantity']=[ref(8,9)]
    result=validate_proposal(p,SOURCE,'q')
    assert not result['automatic_fidelity_pass'] and not result['retrieval_ready']
    assert p['blocks'][0]['abstraction']==result['blocks'][0]['abstraction_proposal']

def test_per_word_context_fragmentation_rejected():
    p=proposal();p['blocks'][0]['evidence']=[ref(i,i+1) for i in range(5)]
    with pytest.raises(InputBoundaryError):validate_proposal(p,SOURCE,'q')

def test_decimal_unicode_repeated_occurrences_and_source_retention():
    s='วาล์ว  5.5 kPa.\nวาล์ว  5.5 kPa.'
    assert contexts(s)==[{'start_token':0,'end_token':3},{'start_token':0,'end_token':6},{'start_token':3,'end_token':6}]
    payload=json.loads(build_messages(s,'q')[1]['content'])
    assert payload['source']==s and 'schema' not in payload

def test_reversed_role_range_still_rejected_by_compiler():
    p=proposal();p['blocks'][0]['roles']={'action':[ref(3,2)]}
    with pytest.raises(InputBoundaryError):validate_proposal(p,SOURCE,'q')

def test_limit_never_truncates_source():
    with pytest.raises(InputBoundaryError,match='do not truncate'):contexts(' '.join(['Sentence.']*17))

def test_abstention_is_not_fidelity_pass():
    p=proposal();p['blocks']=[]
    result=validate_proposal(p,SOURCE,'q')
    assert result['anchor_fallback_required'] and not result['retrieval_ready']

def test_missing_conditions_field_rejected():
    p=proposal();del p['blocks'][0]['conditions']
    with pytest.raises(InputBoundaryError):validate_proposal(p,SOURCE,'q')
