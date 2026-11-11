from copy import deepcopy
import numpy as np
import pytest

from test_sacr_r6_components import fixture,SOURCE
from test_sacr_factorial import fixture as corpus_fixture
from patent_to_pilot.research.sacr_r6_components import prepare_embedding
from patent_to_pilot.research.sacr_r6_factorial import compare_r6
from patent_to_pilot.research.sacr_components import vector_digest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def inputs():
    proposal=fixture();generic=['Authored generic water movement.']
    prepared=prepare_embedding(proposal,source=SOURCE,query_id='q',generic_views=generic,configuration_sha256='a'*64)
    plan=prepared['embedding_plan']
    table={SOURCE:[1,0],'5 bar\n10 litres':[0,1],generic[0]:[0,1]}
    for text in prepared['prepared']['arms']['selective']['views']:
        if text not in table:table[text]=[0,1]
    vectors=np.array([table[row['text']] for row in plan['rows']],dtype=np.float32)
    receipt={'format':'sacr-query-embeddings-v1','plan_sha256':plan['plan_sha256'],'encoder_sha256':'b'*64,
             'row_ids':[row['row_id'] for row in plan['rows']],'vectors_sha256':vector_digest(vectors)}
    corpus=corpus_fixture()
    for key in ['generic_views','invariant_views','component_blocks']:del corpus[key]
    args=dict(proposal=proposal,source=SOURCE,query_id='q',generic_views=generic,configuration_sha256='a'*64,
        vectors=vectors,embedding_receipt=receipt,expected_plan_sha256=plan['plan_sha256'],
        expected_encoder_sha256='b'*64,corpus=corpus)
    return args,plan


def test_actual_r6_text_embedding_rows_to_factorial_ranking():
    args,plan=inputs();result=compare_r6(**args);r=result['factorial']
    anchor=plan['view_rows']['generic'][0]
    assert plan['view_rows']['selective'][:2]==[anchor,anchor] and plan['component_rows'][0]==anchor
    assert np.array_equal(args['vectors'][plan['component_rows']],np.eye(2,dtype=np.float32))
    for arm in ['G/G','I/G','G/L','I/L']:
        assert [row['family_id'] for row in r['arms'][arm]]==['split','joint']
        scores={row['family_id']:row['coverage_score'] for row in r['arms'][arm]}
        assert scores==pytest.approx({'split':.75,'joint':.85} if arm.endswith('/G') else {'split':.625,'joint':.825})
    assert 'outside' not in r['candidate_passages']
    assert r['accounting']['actual_component_passage_dot_products']==6
    assert r['accounting']['actual_acquisition_dot_products']==4*sum(len(v) for v in plan['view_rows'].values())
    assert result['compact_equals_anchor'] and not result['semantic_pass']


@pytest.mark.parametrize('fault',['encoder','row_order','plan','configuration'])
def test_binding_failure_prevents_factorial_retrieval(monkeypatch,fault):
    args,_=inputs()
    if fault=='encoder':args['embedding_receipt']['encoder_sha256']='c'*64
    if fault=='row_order':args['embedding_receipt']['row_ids'].reverse()
    if fault=='plan':args['expected_plan_sha256']='c'*64
    if fault=='configuration':args['configuration_sha256']='c'*64
    monkeypatch.setattr('patent_to_pilot.research.sacr_r6_factorial.compare_factorial',lambda **kwargs:pytest.fail('retrieval before binding'))
    with pytest.raises(InputBoundaryError):compare_r6(**args)
