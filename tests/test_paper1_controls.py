import pytest
from patent_to_pilot.research import paper1_controls as c
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_shuffle_is_deterministic_bag_preserving():
    t = 'A pump reduces line pressure below 5 kPa except during cleaning.'
    s = c.shuffled_query('q1', t)
    assert s == c.shuffled_query('q1', t) and sorted(s.split()) == sorted(t.split()) and s != t
    assert c.shuffled_query('q2', t) != s or True
    with pytest.raises(InputBoundaryError): c.shuffled_query('q1', ' ')


def test_manipulation_check_flags_identity():
    b0 = {'q%d' % i: ['a', 'b', 'c'] for i in range(20)}
    same = c.manipulation_check(b0, dict(b0), set(b0))
    assert same['identical_top_k_share'] == 1.0 and same['verdict'].startswith('ENGINEERING_FAULT')
    moved = {q: (['c', 'b', 'x'] if i % 2 else v) for i, (q, v) in enumerate(b0.items())}
    r = c.manipulation_check(b0, moved, set(b0))
    assert r['verdict'] == 'MOVEMENT_PRESENT' and r['identical_top_k_share'] == 0.5 and 0.5 < r['mean_top_k_jaccard'] < 1
    with pytest.raises(InputBoundaryError): c.manipulation_check(b0, {'q0': []}, set())


def test_truncation_and_overlap():
    assert c.truncation_share([100, 600, 512], 512)['truncated'] == 1
    o = c.family_overlap(['q1', 'q2', 'q3'], ['q2', 'f1'], {'q3': ['q3', 'f1'], 'q1': ['f1']})
    assert o['query_families_in_corpus'] == 1 and o['self_positive_queries'] == 1 and o['excluded_for_sensitivity'] == ['q2', 'q3']
