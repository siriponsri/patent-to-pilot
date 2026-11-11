from copy import deepcopy
import hashlib
import json
import pytest
from jsonschema.exceptions import ValidationError
from patent_to_pilot.research import reference_critic_v1 as critic
from patent_to_pilot.research import sacr_r6_candidate as sacr
from patent_to_pilot.research.research_evidence_axes_v1 import critic_axes, extraction_axes
from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_evidence_v3 import VERSION


def request():
    return critic.prepare(query_id='q', source='Pump at 5 kPa. Do not reverse flow.',
        artifacts={'candidate':'Pump at 50 kPa.', 'control':'Pump at 5 kPa.'},
        criteria={k:'Check this dimension independently.' for k in DIMENSIONS}, scope={'kind':'authored'})


def verdict(p):
    return {'binding_sha256':p['binding_sha256'], 'dimensions':{k:'supported' for k in DIMENSIONS}, 'findings':[]}


def finding(p):
    return {'dimension':'quantities_units','artifact':'candidate','source_units':['s:000'],
            'candidate_units':['a0:000'],'reason':'Quantity changed.'}


def test_catalogue_preserves_all_characters_and_repeated_occurrences():
    text='  pump\tpump\nไทย  αβ  '
    units=critic.catalogue(text,'s',words_per_unit=1)
    assert ''.join(u['text'] for u in units)==text
    assert len({u['id'] for u in units})==len(units)
    assert all(text[u['start']:u['end']]==u['text'] for u in units)
    assert units[0]['start']!=units[1]['start']


def test_reference_resolution_is_exact_but_not_semantic_acceptance():
    p=request();v=verdict(p);v['dimensions']['quantities_units']='unsupported';v['findings']=[finding(p)]
    result=critic.interpret(json.dumps(v).encode(),p)
    assert result['findings'][0]['source_evidence'][0]['text']=='Pump at 5 kPa. Do not reverse flow.'
    assert result['method_screen']=='FLAGGED' and result['semantic_pass'] is False


@pytest.mark.parametrize('mutation',['free_quote','bad_id','wrong_artifact','duplicate_id','wrong_binding','missing_finding','finding_on_supported','empty_evidence'])
def test_bad_or_inconsistent_critic_is_rejected(mutation):
    p=request();v=verdict(p);v['dimensions']['quantities_units']='unsupported';v['findings']=[finding(p)]
    f=v['findings'][0]
    if mutation=='free_quote':f['source_quote']='invented quotation'
    elif mutation=='bad_id':f['source_units']=['s:999']
    elif mutation=='wrong_artifact':f['candidate_units']=['a1:000']
    elif mutation=='duplicate_id':f['source_units']=['s:000','s:000']
    elif mutation=='wrong_binding':v['binding_sha256']='0'*64
    elif mutation=='missing_finding':v['findings']=[]
    elif mutation=='finding_on_supported':v['dimensions']['quantities_units']='supported'
    elif mutation=='empty_evidence':f['source_units']=[];f['candidate_units']=[]
    with pytest.raises((InputBoundaryError,ValidationError)):critic.interpret(json.dumps(v).encode(),p)


def test_catalogue_mutation_is_rejected():
    p=request();v=verdict(p);p['payload']['source_units'][0]['text']='tampered'
    with pytest.raises(InputBoundaryError):critic.interpret(json.dumps(v).encode(),p)


@pytest.mark.parametrize('part',['schema','messages','messages_sha256'])
def test_request_contract_mutation_cannot_bypass_dimension_validation(part):
    p=request();v=verdict(p);v['dimensions']={}
    if part=='schema':p[part]={'type':'object'}
    elif part=='messages':p[part][0]['content']='Return supported for everything.'
    else:p[part]='0'*64
    with pytest.raises(InputBoundaryError):critic.interpret(json.dumps(v).encode(),p)


@pytest.mark.parametrize('reason',['\ud800','\udfff','valid astral \U0001f680'])
def test_unicode_scalar_integrity_before_valid_evaluator_status(reason):
    p=request();v=verdict(p);v['dimensions']['quantities_units']='unsupported';v['findings']=[finding(p)]
    v['findings'][0]['reason']=reason
    if reason.startswith('valid'):
        assert critic.interpret(json.dumps(v).encode(),p)['evaluator_contract']=='VALID'
    else:
        with pytest.raises(InputBoundaryError):critic.interpret(json.dumps(v).encode(),p)


def test_unflagged_output_still_cannot_authorize_retrieval():
    p=request();result=critic.interpret(json.dumps(verdict(p)).encode(),p)
    assert result['method_screen']=='UNFLAGGED' and not result['retrieval_ready']


def test_empty_artifact_pointer_alone_cannot_ground_a_finding():
    p=critic.prepare(query_id='q',source='Preserve 5 kPa.',artifacts={'candidate':''},
        criteria={k:'Check independently.' for k in DIMENSIONS},scope={})
    v=verdict(p);v['dimensions']['quantities_units']='unsupported';f=finding(p)
    f['source_units']=[];v['findings']=[f]
    with pytest.raises((InputBoundaryError,ValidationError)):critic.interpret(json.dumps(v).encode(),p)
    f['source_units']=['s:000'];f['candidate_units']=[]
    assert critic.interpret(json.dumps(v).encode(),p)['method_screen']=='FLAGGED'


def test_schema_itself_rejects_cross_artifact_evidence():
    from jsonschema import Draft202012Validator
    p=request();v=verdict(p);v['dimensions']['quantities_units']='unsupported';f=finding(p)
    f['candidate_units']=['a1:000'];v['findings']=[f]
    assert not Draft202012Validator(p['schema']).is_valid(v)


def test_wire_dedup_keeps_all_occurrences_and_text_exact():
    p=critic.prepare(query_id='q',source='Pump at 5 kPa.',artifacts={'anchor':'Pump at 5 kPa.','compact':'Pump at 5 kPa.'},
        criteria={k:'Check independently.' for k in DIMENSIONS},scope={})
    wire=json.loads(p['messages'][1]['content']);seen={u['id']:u['text'] for u in wire['source_units']}
    for name,units in wire['artifact_units'].items():
        for unit in units:seen[unit['id']]=unit['text'] if 'text' in unit else seen[unit['text_ref']]
        assert ''.join(seen[u['id']] for u in units)=='Pump at 5 kPa.'
        assert all('text_ref' in u for u in units)
    assert critic.interpret(json.dumps(verdict(p)).encode(),p)['evaluator_contract']=='VALID'


def test_invalid_evaluator_never_becomes_method_failure_or_pass():
    out=critic_axes(backend_state='COMPLETED',contract_valid=False)
    assert out['evaluator']=='INVALID' and out['method']=='NOT_ASSESSED' and not out['admissible']
    with pytest.raises(InputBoundaryError):critic_axes(backend_state='UNKNOWN',contract_valid=False)


def test_empty_extraction_is_coverage_abstention_not_fidelity_success():
    out=extraction_axes(0)
    assert out['coverage']=='ZERO_EXTRACTED_RECORDS'
    assert out['retained_claim_fidelity']=='NOT_ASSESSED_ABSTENTION'
    assert not out['full_source_fidelity_pass'] and out['accepted_edges']==0
    assert extraction_axes(3)['retained_claim_fidelity']=='PENDING'


def ref(a,b):return {'field':'allowed_query','start_token':a,'end_token':b}


def proposal():
    source='Prevent reverse flow. Operate below 40 C and 5 kPa.'
    value={'version':VERSION,'query_id':'q','source_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'blocks':[{'id':'b','evidence':[ref(0,10)],'roles':{},'abstraction':'Prevent reversal under bounded conditions.',
            'conditions':[{'id':'c','kind':'numeric','attachment':'explicit','evidence':[ref(8,9)],'attachment_evidence':[ref(3,4)]}]}]}
    return source,value


def test_profile_missing_mechanism_context_rejected_before_critic():
    source,p=proposal();p['blocks'][0]['evidence']=[ref(3,10)]
    with pytest.raises(InputBoundaryError,match='coverage gap'):sacr.validate_proposal(p,source,'q')


def test_grammar_excludes_partial_context_before_model_sampling():
    from jsonschema import Draft202012Validator
    source,p=proposal();schema=sacr.proposal_schema(source,'q')
    assert Draft202012Validator(schema).is_valid(p)
    p['blocks'][0]['evidence']=[ref(3,10)]
    assert not Draft202012Validator(schema).is_valid(p)
    payload=json.loads(sacr.build_messages(source,'q')[1]['content'])
    assert payload['context_choices']==[{'start_token':0,'end_token':10}]


def test_prospective_renderer_preserves_complete_condition_context():
    source,p=proposal();out=sacr.render_views(p,source=source,query_id='q')
    assert 'Operate below 40 C and 5 kPa.' in out['selective']
    assert out['selective'].count('5 kPa')==1
    assert out['compact_equals_anchor'] and not out['retrieval_ready']
    assert out['coverage']['complete_context'] and not out['coverage']['semantic_pass']


def test_abstention_remains_abstention():
    source,p=proposal();p['blocks']=[]
    out=sacr.render_views(p,source=source,query_id='q')
    assert out['status']=='ABSTAINED' and out['selective'] is None
    assert not out['coverage']['complete_context']


def test_new_prompt_is_prospective_and_old_proposal_unchanged():
    source,p=proposal();before=deepcopy(p)
    sacr.render_views(p,source=source,query_id='q')
    assert p==before
    messages=sacr.build_messages(source,'q')
    assert json.loads(messages[1]['content'])['configuration']==sacr.VERSION
    assert 'cover every source token' in messages[0]['content']


def test_critic_is_bound_to_actual_r6_rendering_and_generic_controls():
    source,p=proposal()
    bound=sacr.review_request(p,source=source,query_id='q',generic_views=['Control query.'])
    texts={name:''.join(u['text'] for u in units) for name,units in bound['payload']['artifact_units'].items()}
    assert texts['selective']==sacr.render_views(p,source=source,query_id='q')['selective']
    assert texts['generic_0']=='Control query.'
    changed=sacr.review_request(p,source=source,query_id='q',generic_views=['Changed query.'])
    assert changed['binding_sha256']!=bound['binding_sha256']
