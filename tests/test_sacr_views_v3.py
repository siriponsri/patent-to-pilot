import hashlib
from patent_to_pilot.research.sacr_views_v3 import render_views
from patent_to_pilot.research.sacr_evidence_v3 import VERSION
from patent_to_pilot.research.sacr_evidence_review_v3 import review_payload


def ref(a,b): return {'field':'allowed_query','start_token':a,'end_token':b}


def test_occurrence_union_preserves_repetition_and_omission_is_not_hidden():
    source = 'No flow. No flow. Keep temperature below 40 C.'
    p = {'version':VERSION,'query_id':'q','source_sha256':hashlib.sha256(source.encode()).hexdigest(),
         'blocks':[{'id':'b','evidence':[ref(0,2),ref(0,4)],'roles':{},'conditions':[],
                    'abstraction':'Prevent movement.'}]}
    v = render_views(p,source=source,query_id='q')
    assert v['compact'] == 'No flow. No flow.'
    assert v['source_intervals'] == [[0,17]]
    assert '40 C.' in v['source_anchor']
    assert v['selective'] == 'Prevent movement.'
    assert v['omission_review_required'] and not v['retrieval_ready']
    review = review_payload(p,source=source,query_id='q')
    assert review['artifacts']['selective'] == v['selective']
    assert review['artifacts']['source_anchor'] == source


def test_conditions_preserved_as_literals_not_rewritten_by_abstraction():
    source = 'Pump at 5 kPa without power.'
    p = {'version':VERSION,'query_id':'q','source_sha256':hashlib.sha256(source.encode()).hexdigest(),
      'blocks':[{'id':'b','evidence':[ref(0,6)],'roles':{},'abstraction':'Move liquid.',
       'conditions':[{'id':'c','kind':'numeric','attachment':'explicit',
          'evidence':[ref(1,4)],'attachment_evidence':[ref(0,6)]}]}]}
    v=render_views(p,source=source,query_id='q')
    assert v['compact']==source
    assert '5 kPa' in v['selective'] and 'without power.' in v['selective']
    assert v['selective'].count('5') == 1
    assert v['proposed_abstractions']==1 and not v['retrieval_ready']


def test_abstention_never_fabricates_views():
    source='Unknown function.'
    p={'version':VERSION,'query_id':'q','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'blocks':[]}
    v=render_views(p,source=source,query_id='q')
    assert v['compact'] is None and v['selective'] is None
    assert v['source_anchor']==source and v['status']=='ABSTAINED'


def test_shared_condition_references_do_not_duplicate_source_quantity():
    source='Pump at 5 kPa without power.'
    conditions=[{'id':'c'+str(i),'kind':'numeric','attachment':'explicit',
                 'evidence':[ref(1,4)],'attachment_evidence':[ref(0,6)]} for i in range(2)]
    p={'version':VERSION,'query_id':'q','source_sha256':hashlib.sha256(source.encode()).hexdigest(),
       'blocks':[{'id':'b','evidence':[ref(0,6)],'roles':{},'abstraction':None,'conditions':conditions}]}
    v=render_views(p,source=source,query_id='q')
    assert v['selective']==source
    assert v['selective_source_intervals']==[[0,len(source)]]
