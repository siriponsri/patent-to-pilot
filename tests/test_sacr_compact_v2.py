import hashlib
from patent_to_pilot.research.sacr_compact_v2 import compact_view_v2
from patent_to_pilot.research.sacr_views import compact_view, NUMBERS
from test_sacr_profile import fixture, SOURCE, span


def render(p, source=SOURCE):
    return compact_view_v2(p, source=source, query_id='q1', input_kind='MTM_P')


def test_nested_condition_is_not_serialized_twice_and_r1_is_unchanged():
    p=fixture();p['blocks'][0]['relation_text']=SOURCE
    old=compact_view(p,source=SOURCE,query_id='q1',input_kind='MTM_P')
    assert old['text'].count('without')==2
    new=render(p)
    assert new['text']==SOURCE and new['merged_intervals']==1
    assert new['semantic_status']=='unknown'


def test_distinct_identical_occurrences_are_not_string_deduplicated():
    clause='A works at 5 Pa.';source=clause+' '+clause;p=fixture()
    p['source_sha256']=hashlib.sha256(source.encode()).hexdigest()
    p['blocks']=[{'block_id':'b'+str(i),'relation_text':clause,'source_spans':[
        {'field':'allowed_query','start':start,'end':start+len(clause),'text':clause}],
        'attached_conditions':[]} for i,start in enumerate((0,len(clause)+1))]
    out=render(p,source)
    assert NUMBERS.findall(out['text'])==['5','5']
    assert out['text']==clause+'\n'+clause and out['merged_intervals']==2


def test_explicit_retained_context_is_included_and_unresolved_abstains():
    source=SOURCE+' In a vascular graft.';p=fixture(source)
    p['context_items']=[{'raw_text':'In a vascular graft.','action':'retain','reason':'explicit context',
                         'source_spans':[span('In a vascular graft.',source)]}]
    assert 'vascular graft' in render(p,source)['text']
    p['context_items'][0]['action']='unresolved'
    assert render(p,source)['text'] is None


def test_ambiguous_occurrence_is_not_resolved_by_arbitrary_first_match():
    source='A works. A works.';p=fixture()
    p['source_sha256']=hashlib.sha256(source.encode()).hexdigest()
    p['blocks']=[{'block_id':'b1','relation_text':'A works.','source_spans':[span(source,source)],'attached_conditions':[]}]
    assert render(p,source)['reason']=='AMBIGUOUS_TEXT_OCCURRENCE'


def test_partial_or_uncertain_profile_is_not_promoted():
    p=fixture();p['extraction_status']='partial'
    assert render(p)['status']=='REVIEW_REQUIRED'
    p=fixture();p['blocks'][0]['attached_conditions'][0]['relation_to_block']='uncertain'
    assert render(p)['text'] is None
