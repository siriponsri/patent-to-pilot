import copy

import numpy as np
import pytest

from patent_to_pilot.research.sacr_factorial import compare_factorial, passage_order_digest


def fixture():
    ids = ['split', 'joint', 'outside']
    owner = np.array([0, 0, 1, 2])
    passages = ['p0', 'p1', 'p2', 'p3']
    return dict(family_ids=ids, passage_owner=owner, passage_ids=passages,
                passage_vectors=np.array([[1, 0], [0, 1], [0.6, 0.8], [-1, 0]], dtype=np.float32),
                expected_order_sha256=passage_order_digest(ids, owner, passages),
                eligible=np.array([True, True, False]),
                generic_views=(['anchor', 'generic'], np.eye(2, dtype=np.float32)),
                invariant_views=(['anchor', 'selective'], np.eye(2, dtype=np.float32)),
                component_blocks=[np.eye(2, dtype=np.float32)], depth=2, chunk_size=1)


def test_identical_views_reduce_to_same_arms_and_share_passages():
    r = compare_factorial(**fixture())
    assert r['arms']['G/G'] == r['arms']['I/G']
    assert r['arms']['G/L'] == r['arms']['I/L']
    assert r['candidate_passages']['split']['passage_ids'] == ['p0', 'p1']
    assert 'outside' not in r['candidate_passages']
    scores = {row['family_id']: row['coverage_score'] for row in r['arms']['I/L']}
    assert scores['joint'] > scores['split']  # split passages cannot supply one joint conjunction
    assert scores['split'] == pytest.approx(0.625)
    assert r['accounting']['actual_component_passage_dot_products'] == 6
    assert r['accounting']['actual_acquisition_dot_products'] == 16


def test_different_view_unions_do_not_leak_candidates_between_arms():
    p = fixture()
    p['depth'] = 1
    p['invariant_views'] = (['anchor', 'selective'], np.array([[1, 0], [0.6, 0.8]], dtype=np.float32))
    r = compare_factorial(**p)
    assert r['acquisition']['G']['family_ids'] == ['split']
    assert r['acquisition']['I']['family_ids'] == ['joint', 'split']
    assert {x['family_id'] for x in r['arms']['G/L']} == {'split'}


def test_condition_free_reduces_mean_and_bottleneck_identically():
    p = fixture()
    p['component_blocks'] = [np.array([[1, 0]], dtype=np.float32)]
    r = compare_factorial(**p)
    assert r['arms']['G/G'] == r['arms']['G/L']


def test_empty_eligible_cohort_stays_empty():
    p = fixture()
    p['eligible'][:] = False
    r = compare_factorial(**p)
    assert all(not rows for rows in r['arms'].values())
    assert r['accounting']['actual_component_passage_dot_products'] == 0


def test_bad_binding_fails_before_search(monkeypatch):
    p = fixture()
    p['expected_order_sha256'] = '0' * 64
    def forbidden(**kwargs):
        raise AssertionError('search must not happen')
    monkeypatch.setattr('patent_to_pilot.research.sacr_factorial.acquire_union', forbidden)
    with pytest.raises(ValueError, match='binding mismatch'):
        compare_factorial(**p)


@pytest.mark.parametrize('case', ['order', 'owner', 'anchor', 'nonfinite', 'empty_profile', 'duplicate_passage'])
def test_identity_and_profile_defects_fail(case):
    p = copy.deepcopy(fixture())
    if case == 'order':
        p['passage_ids'].reverse()
    elif case == 'owner':
        p['passage_owner'][0] = 1
    elif case == 'anchor':
        p['invariant_views'][1][0] = [0, 1]
    elif case == 'nonfinite':
        p['component_blocks'][0][0, 0] = np.nan
    elif case == 'empty_profile':
        p['component_blocks'] = []
    else:
        p['passage_ids'][1] = 'p0'
    with pytest.raises(ValueError):
        compare_factorial(**p)
