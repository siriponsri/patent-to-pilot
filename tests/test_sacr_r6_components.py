from copy import deepcopy
import pytest
from patent_to_pilot.research.sacr_r6_components import compile_components,prepare_embedding
from patent_to_pilot.research.sacr_token_profile import source_catalogue
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

SOURCE='The pump moves water at 5 bar and 10 litres per second.'


def fixture():
    cat=source_catalogue(SOURCE)
    def ref(a,b):return {'field':'allowed_query','start_token':a,'end_token':b}
    p={'version':'sacr-evidence-roles-v3','query_id':'q','source_sha256':cat['source_sha256'],'blocks':[
        {'id':'b1','evidence':[ref(0,len(cat['tokens']))],'roles':{},'conditions':[
            {'id':'c1','kind':'numeric','attachment':'explicit','evidence':[ref(5,7),ref(8,10)],
                'attachment_evidence':[ref(0,7)]}],'abstraction':None}]}
    return p


def compile(p):return compile_components(p,source=SOURCE,query_id='q',configuration_sha256='a'*64)


def test_exact_literal_projection_and_duplicate_positions():
    p=fixture();b=deepcopy(p['blocks'][0]);b['id']='b2';b['conditions']=[];p['blocks'].append(b)
    r=compile(p)
    assert [x['text'] for x in r['rows']]==[SOURCE,'5 bar\n10 litres',SOURCE]
    assert r['duplicate_relation_positions']==1
    assert r['blocks']==[{'block_id':'b1','start':0,'end':2},{'block_id':'b2','start':2,'end':3}]
    assert len({x['row_id'] for x in r['rows']})==3


def test_overlap_merged_and_uncertain_not_silently_excluded():
    p=fixture();p['blocks'][0]['conditions'][0]['evidence'][1]['start_token']=6
    assert compile(p)['rows'][1]['text']=='5 bar and 10 litres'
    p['blocks'][0]['conditions'][0]['attachment']='uncertain'
    r=compile(p);assert r['status']=='REVIEW_REQUIRED' and not r['rows']
    with pytest.raises(InputBoundaryError):prepare_embedding(p,source=SOURCE,query_id='q',generic_views=[SOURCE],configuration_sha256='a'*64)


def test_anchor_compact_and_relation_share_one_encoder_text():
    p=fixture();r=prepare_embedding(p,source=SOURCE,query_id='q',generic_views=[SOURCE],configuration_sha256='a'*64)
    plan=r['embedding_plan'];anchor=plan['view_rows']['generic'][0]
    assert plan['view_rows']['selective'][0:2]==[anchor,anchor]
    assert plan['component_rows'][0]==anchor
    assert r['compact_equals_anchor'] and not r['dispatch_authorized']


def test_changed_source_hash_rejected_and_proposal_change_changes_identity():
    p=fixture();first=compile(p);p['blocks'][0]['abstraction']='A pump moves fluid.'
    assert compile(p)['plan_sha256']!=first['plan_sha256']
    p['source_sha256']='0'*64
    with pytest.raises(InputBoundaryError):compile(p)


def test_maximum72_components77_positions_before_dedup():
    p=fixture();template=p['blocks'][0];blocks=[]
    for i in range(8):
        b=deepcopy(template);b['id']=f'b{i}';b['conditions']=[]
        for j in range(8):
            c=deepcopy(template['conditions'][0]);c['id']=f'c{i}_{j}';b['conditions'].append(c)
        blocks.append(b)
    p['blocks']=blocks
    r=prepare_embedding(p,source=SOURCE,query_id='q',generic_views=[SOURCE,'An authored generic view.'],configuration_sha256='a'*64)
    assert len(r['prepared']['components']['rows'])==72 and r['planned_positions']==77
    assert len(r['embedding_plan']['component_rows'])==72 and r['unique_text_rows']<77
