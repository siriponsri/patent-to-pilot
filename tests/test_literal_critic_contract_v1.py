import hashlib,json
import pytest
from jsonschema import ValidationError
from patent_to_pilot.research.literal_critic_contract_v1 import interpret,messages,schema
from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def response(flag=False):
    return {'query_id':'q','source_sha256':hashlib.sha256(b'A valve reduces pressure.').hexdigest(),
        'dimensions':{d:'uncertain' if flag and d=='roles_direction' else 'supported' for d in DIMENSIONS},
        'findings':[{'dimension':'roles_direction','artifact':'record','source_quote':'valve',
                     'candidate_quote':'pressure','reason':'attachment uncertain'}] if flag else []}


@pytest.mark.parametrize('flag',[False,True])
def test_exact_critic_schema_retains_uncertainty_and_never_passes_fidelity(flag):
    result=interpret(json.dumps(response(flag)).encode(),query_id='q',source='A valve reduces pressure.',artifacts={'record':'reduce pressure'})
    assert result['semantic_pass'] is False
    assert result['status']==('ESCALATE' if flag else 'CRITIC_UNFLAGGED_NOT_FIDELITY_PASS')


@pytest.mark.parametrize('fault',['prefixed-key','invented-quote','missing-finding','wrong-artifact','identity'])
def test_historical_bad_keys_or_ungrounded_findings_never_repaired(fault):
    r=response(True)
    if fault=='prefixed-key':r['findings'][0]['literal_source_quote']=r['findings'][0].pop('source_quote')
    if fault=='invented-quote':r['findings'][0]['source_quote']='invented'
    if fault=='missing-finding':r['findings']=[]
    if fault=='wrong-artifact':r['findings'][0]['artifact']='other'
    if fault=='identity':r['query_id']='other'
    with pytest.raises((ValidationError,InputBoundaryError)):
        interpret(json.dumps(r).encode(),query_id='q',source='A valve reduces pressure.',artifacts={'record':'reduce pressure'})


def test_prompt_declares_exact_contract_as_data():
    m=messages(query_id='q',source='A valve reduces pressure.',artifacts={'record':'reduce pressure'},criteria={},scope={})
    payload=json.loads(m[1]['content'])
    assert payload['output_schema']==schema('q','A valve reduces pressure.',{'record':'reduce pressure'})
    assert 'source_quote' in payload['output_schema']['properties']['findings']['items']['required']
