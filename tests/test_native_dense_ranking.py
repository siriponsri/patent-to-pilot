import numpy as np
import pytest

from patent_to_pilot.research.native_dense_ranking import rank_maxp


def test_boundary_ties_are_global_and_independent_of_family_order():
    # More tied families than available slots, plus two passages for Z.
    result = rank_maxp(np.array([.2, .5, .5, .5, .1]),
                       [0, 0, 1, 2, 3], ["Z", "B", "A", "C"], depth=2)
    assert result == {"families": ["A", "B"], "scores": [.5, .5]}
    permuted = rank_maxp(np.array([.5, .1, .5, .2, .5]),
                         [0, 1, 2, 3, 3], ["A", "C", "B", "Z"], depth=2)
    assert permuted == result


def test_maxp_matches_explicit_reference_including_negative_scores():
    rng = np.random.default_rng(71)
    owners = np.repeat(np.arange(37), 3)
    scores = rng.uniform(-1, 0, len(owners)).astype(np.float32)
    ids = [f"F{i:02}" for i in range(37)]
    expected = sorted([(float(max(scores[owners == i])), f) for i, f in enumerate(ids)],
                      key=lambda x: (-x[0], x[1]))[:20]
    actual = rank_maxp(scores, owners, ids, depth=20)
    assert actual["families"] == [f for _, f in expected]
    assert actual["scores"] == [s for s, _ in expected]


@pytest.mark.parametrize("scores,owners,ids", [
    ([float("nan")], [0], ["A"]), ([float("inf")], [0], ["A"]),
    ([.1], [-1], ["A"]), ([.1], [1], ["A"]),
    ([.1], [0], ["A", "B"]), ([.1, .2], [0, 1], ["A", "A"]),
    ([.1], [.0], ["A"]),
])
def test_invalid_scores_and_incomplete_universe_fail_without_repair(scores, owners, ids):
    with pytest.raises(ValueError):
        rank_maxp(np.array(scores), owners, ids)
