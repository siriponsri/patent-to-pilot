import copy

import numpy as np
import pytest

from patent_to_pilot.research.sacr_acquisition import acquire_union
from patent_to_pilot.research.sacr_selector import select_union


def args():
    return dict(family_ids=['z', 'a', 'b', 'c'], passage_owner=np.array([0, 1, 0, 2, 3]),
                passage_vectors=np.array([[1, 0], [1, 0], [0, 1], [-1, 0], [0, -1]], dtype=np.float32),
                view_ids=['anchor', 'selective'], view_vectors=np.eye(2, dtype=np.float32),
                eligible=np.array([True, True, True, True]), depth=1, chunk_size=2)


def test_global_cutoff_tie_and_cross_chunk_maxp_and_anchor_score_for_rescue():
    result = acquire_union(**args())
    assert result['rankings']['anchor'] == [{'family_id': 'a', 'score': 1.0}]
    assert result['rankings']['selective'] == [{'family_id': 'z', 'score': 1.0}]
    assert result['family_ids'] == ['a', 'z']
    assert result['anchor_scores'] == [1, 1]
    assert result['accounting']['view_passage_dot_products'] == 10


def test_eligibility_precedes_topk_and_empty_universe_is_not_failure():
    p = args()
    p['eligible'][:2] = False
    r = acquire_union(**p)
    assert r['rankings']['anchor'][0]['family_id'] == 'c'
    p['eligible'][:] = False
    r = acquire_union(**p)
    assert r['family_ids'] == r['anchor_scores'] == []
    assert r['accounting']['passages_scanned'] == 5


@pytest.mark.parametrize('chunk', [1, 2, 3, 100])
def test_against_exhaustive_family_reference(chunk):
    rng = np.random.default_rng(123)
    matrix = rng.normal(size=(31, 7)).astype(np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    views = rng.normal(size=(3, 7)).astype(np.float32)
    views /= np.linalg.norm(views, axis=1, keepdims=True)
    owner = np.arange(31) % 9
    ids = [str(i) for i in range(9)]
    mask = np.arange(9) % 3 != 0
    r = acquire_union(family_ids=ids, passage_owner=owner, passage_vectors=matrix,
                      view_ids=['anchor', 'one', 'two'], view_vectors=views,
                      eligible=mask, depth=4, chunk_size=chunk)
    union = set()
    for i, name in enumerate(['anchor', 'one', 'two']):
        scores = {j: max(float(np.dot(views[i], row)) for row in matrix[owner == j]) for j in range(9) if mask[j]}
        expected = sorted(scores, key=lambda j: (-scores[j], ids[j]))[:4]
        assert [x['family_id'] for x in r['rankings'][name]] == [ids[j] for j in expected]
        union.update(ids[j] for j in expected)
    assert r['family_ids'] == sorted(union)


def test_duplicates_counted_without_extra_replacement_views():
    p = args()
    p['view_vectors'][1] = p['view_vectors'][0]
    r = acquire_union(**p)
    assert r['family_ids'] == ['a']
    assert r['accounting']['duplicate_family_occurrences'] == 1


def test_union_and_anchor_scores_feed_existing_selector_without_new_exposure():
    r = acquire_union(**args())
    selected = select_union(r['family_ids'], r['anchor_scores'], [0.2, 0.9], depth=1)
    assert selected[0]['family_id'] == 'z'
    assert selected[0]['semantic_status'] == 'unknown'
    assert {row['family_id'] for row in selected} <= set(r['family_ids'])


@pytest.mark.parametrize('change', ['nan', 'nonunit', 'missing_owner', 'bad_owner', 'float_owner',
                                   'mask_dtype', 'duplicate_id', 'no_anchor', 'too_many', 'depth'])
def test_fail_closed_inputs(change):
    p = copy.deepcopy(args())
    if change == 'nan':
        p['passage_vectors'][-1, 0] = np.nan  # even a late/ineligible passage is checked
    elif change == 'nonunit':
        p['view_vectors'][0] *= 2
    elif change == 'missing_owner':
        p['passage_owner'][-1] = 0
    elif change == 'bad_owner':
        p['passage_owner'][0] = -1
    elif change == 'float_owner':
        p['passage_owner'] = p['passage_owner'].astype(float)
    elif change == 'mask_dtype':
        p['eligible'] = [1] * 4
    elif change == 'duplicate_id':
        p['family_ids'][0] = 'a'
    elif change == 'no_anchor':
        p['view_ids'][0] = 'other'
    elif change == 'too_many':
        p['view_ids'] += ['three', 'four']
    else:
        p['depth'] = 201
    with pytest.raises(ValueError):
        acquire_union(**p)
