import copy

import numpy as np
import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import bind_component_vectors, compile_components, vector_digest
from patent_to_pilot.research.sacr_factorial import compare_factorial
from test_sacr_factorial import fixture as factorial_fixture
from test_sacr_profile import SOURCE, fixture


def compile(profile=None):
    return compile_components(profile or fixture(), source=SOURCE, query_id='q1', input_kind='MTM_P')


def binding():
    plan = compile()
    vectors = np.eye(3, dtype=np.float32)
    receipt = {'format': 'sacr-component-vectors-v1', 'plan_sha256': plan['plan_sha256'],
               'encoder_sha256': 'a' * 64, 'row_ids': [r['row_id'] for r in plan['rows']],
               'vectors_sha256': vector_digest(vectors)}
    return dict(plan=plan, vectors=vectors, receipt=receipt, expected_plan_sha256=plan['plan_sha256'],
                expected_encoder_sha256='a' * 64)


def test_raw_source_components_and_determinism():
    p = fixture()
    before = copy.deepcopy(p)
    plan = compile(p)
    assert p == before and plan == compile(p)
    assert [r['text'] for r in plan['rows']] == ['Reduce reverse flow of liquid', 'low pressure',
                                                'without external electrical power']
    assert plan['blocks'] == [{'block_id': 'b1', 'start': 0, 'end': 3}]
    assert plan['semantic_status'] == 'unknown' and plan['fidelity_review'] == 'REQUIRED'


def test_uncertain_conditions_not_conjoined_and_condition_free_kept():
    p = fixture()
    for c in p['blocks'][0]['attached_conditions']:
        c['relation_to_block'] = 'uncertain'
    plan = compile(p)
    assert len(plan['rows']) == 1 and plan['excluded_uncertain_conditions'] == 2


@pytest.mark.parametrize('case', ['failed', 'empty', 'normalization'])
def test_failed_or_review_flagged_plans_do_not_embed(case):
    p = fixture()
    if case == 'failed':
        p.update(extraction_status='failed', failure_reasons=['authored failure'])
    elif case == 'empty':
        p['blocks'] = []
    else:
        p['blocks'][0]['attached_conditions'][0]['normalized_text'] = '5 kPa'
    plan = compile(p)
    assert not plan['rows']
    args = binding()
    args.update(plan=plan, expected_plan_sha256=plan['plan_sha256'])
    with pytest.raises(InputBoundaryError):
        bind_component_vectors(**args)


def test_embedding_binding_detaches_and_preserves_rows():
    args = binding()
    blocks = bind_component_vectors(**args)
    args['vectors'][:] = 0
    np.testing.assert_array_equal(blocks[0], np.eye(3))
    assert not blocks[0].flags.writeable


def test_compiled_rows_bind_into_factorial_without_semantic_certification():
    args = binding()
    args['vectors'] = np.array([[1, 0], [0, 1], [0, 1]], dtype=np.float32)
    args['receipt']['vectors_sha256'] = vector_digest(args['vectors'])
    inputs = factorial_fixture()
    inputs['component_blocks'] = bind_component_vectors(**args)
    result = compare_factorial(**inputs)
    assert result['accounting']['component_rows'] == 3
    assert result['accounting']['actual_component_passage_dot_products'] == 9
    assert result['semantic_status'] == 'unknown'


@pytest.mark.parametrize('case', ['plan', 'row_order', 'vectors', 'encoder', 'nonunit', 'nan'])
def test_swaps_mutation_and_identity_fail_closed(case):
    args = binding()
    if case == 'plan':
        args['plan']['rows'][0]['text'] = 'changed'
    elif case == 'row_order':
        args['receipt']['row_ids'].reverse()
    elif case == 'vectors':
        args['vectors'] = args['vectors'][::-1].copy()
    elif case == 'encoder':
        args['expected_encoder_sha256'] = 'b' * 64
    elif case == 'nonunit':
        args['vectors'][0] *= 2
    else:
        args['vectors'][0, 0] = np.nan
    with pytest.raises(InputBoundaryError):
        bind_component_vectors(**args)
