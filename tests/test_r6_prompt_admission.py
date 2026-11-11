"""Causal removal of unused R4 branches; preserve admitted R6 request bytes."""
from copy import deepcopy
import json
import pytest
from patent_to_pilot.research import sacr_r6_candidate as r6
from patent_to_pilot.research import sacr_r6_prompt as direct
from patent_to_pilot.research.sacr_evidence_prompt_v4 import contexts as old_contexts
from patent_to_pilot.research.sacr_evidence_prompt_v5 import proposal_schema as old_schema, build_messages as old_messages
from patent_to_pilot.research.sacr_token_profile import source_catalogue
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


@pytest.mark.parametrize('count',[1,2,16])
def test_same_schema_messages_and_condition_contexts_for_previously_admitted(count):
    source=' '.join(['The pump transfers water at 5 bar.']*count)
    n=len(source_catalogue(source)['tokens'])
    expected=deepcopy(old_schema(source,'q'))
    expected['properties']['blocks']['items']=next(v for v in expected['properties']['blocks']['items']['anyOf']
        if v['properties']['evidence']['items']['properties']['start_token']['enum']==[0]
        and v['properties']['evidence']['items']['properties']['end_token']['enum']==[n])
    assert r6.proposal_schema(source,'q')==expected
    previous=old_messages(source,'q'); current=r6.build_messages(source,'q')
    assert current[0]['content']==previous[0]['content']+(
        ' Across all nonempty blocks the evidence contexts MUST cover every source token. '
        'Context inclusion does not assert that background text is an invention function. Do not invent roles for background text. '
        'Use the full-source context if needed; empty blocks remain abstention. The selective view still requires complete semantic fidelity.')
    payload=json.loads(previous[1]['content']); payload['configuration']=r6.VERSION
    payload['context_choices']=[{'start_token':0,'end_token':n}]
    assert current[1]['content']==json.dumps(payload,ensure_ascii=False,separators=(',',':'))
    assert direct.contexts(source)==old_contexts(source)


@pytest.mark.parametrize('count',[17,32])
def test_full_source_grammar_no_longer_enumerates_unused_sentence_branches(count):
    source=' '.join(['The pump transfers water.']*count)
    with pytest.raises(InputBoundaryError):old_schema(source,'q')
    schema=r6.proposal_schema(source,'q'); messages=r6.build_messages(source,'q')
    assert 'anyOf' not in schema['properties']['blocks']['items']
    assert len(json.loads(messages[1]['content'])['context_choices'])==1
    cat=source_catalogue(source); n=len(cat['tokens'])
    ref={'field':'allowed_query','start_token':0,'end_token':n}
    proposal={'version':'sacr-evidence-roles-v3','query_id':'q','source_sha256':cat['source_sha256'],
        'blocks':[{'id':'b','evidence':[ref],'roles':{},'conditions':[],'abstraction':None}]}
    rendered=r6.render_views(proposal,source=source,query_id='q')
    assert rendered['compact']==source and rendered['selective']==source
    assert rendered['coverage']['complete_context'] and rendered['retrieval_ready'] is False
