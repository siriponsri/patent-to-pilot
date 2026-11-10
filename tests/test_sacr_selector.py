import numpy as np
import pytest

from patent_to_pilot.research.sacr_selector import local_coverage, ranknorm, select_union


def test_average_ranks_and_degenerate_pools():
    np.testing.assert_allclose(ranknorm([1, 1, 2, 3]), [0, 0, 0.6, 1])
    np.testing.assert_allclose(ranknorm([7, 7]), [0.5, 0.5])
    np.testing.assert_allclose(ranknorm([7]), [1])


def test_locality_cannot_combine_complementary_passages():
    assert local_coverage([[[1, -1], [-1, 1]]]) == pytest.approx(0.25)
    assert local_coverage([[[0.2], [0.2]]]) == pytest.approx(0.6)
    assert local_coverage([[[1, -1], [-1, 1]]], beta=0) == pytest.approx(0.5)


def test_partial_block_match_and_condition_free_block():
    assert local_coverage([[[-1]], [[0.8]]]) == pytest.approx(0.9)
    assert local_coverage([[[0.8]]], beta=0) == local_coverage([[[0.8]]], beta=1)


def test_ties_use_anchor_then_family_id_and_do_not_invent_candidates():
    result = select_union(["z", "a", "b"], [0.2, 0.2, 0.8], [0.9, 0.9, 0.1])
    assert [r["family_id"] for r in result] == ["b", "a", "z"]
    assert all(r["semantic_status"] == "unknown" for r in result)
    assert select_union([], [], []) == []
    assert len(select_union(["a", "b"], [1, 2], [0, 1], depth=1)) == 1


@pytest.mark.parametrize("scores", [[], [np.nan], [np.inf], [[1, 2]]])
def test_bad_rank_inputs(scores):
    with pytest.raises(ValueError):
        ranknorm(scores)


@pytest.mark.parametrize("blocks", [[], [[]], [[[np.nan]]], [[[1.1]]], [[[0]], [[0, 1]]]])
def test_bad_local_inputs(blocks):
    with pytest.raises(ValueError):
        local_coverage(blocks)


def test_union_failures():
    for ids, anchor, coverage in [(["a", "a"], [1, 2], [0, 1]), (["a"], [], [1]),
                                  (["a"], [np.nan], [1]), (["a"], [1], [1.1])]:
        with pytest.raises(ValueError):
            select_union(ids, anchor, coverage)


def test_permutation_invariance_and_global_cutoff_tie():
    ids, anchor, coverage = ["d", "b", "a", "c"], [1]*4, [0.5]*4
    expected = select_union(ids, anchor, coverage, depth=2)
    assert [r["family_id"] for r in expected] == ["a", "b"]
    assert select_union(ids[::-1], anchor, coverage, depth=2) == expected
