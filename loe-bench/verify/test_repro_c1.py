import numpy as np
import pytest

from repro_c1 import interval, queue_metrics, queue_weights


def test_three_way_boundary_tie_shares_one_remaining_slot():
    scores = np.array([0.9, 0.8, 0.8, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2])
    copies = np.ones(len(scores), dtype=int)

    slots, weights = queue_weights(scores, copies)

    assert slots == 2
    np.testing.assert_array_equal(weights, [1, 1 / 3, 1 / 3, 1 / 3, 0, 0, 0, 0, 0, 0])
    assert weights @ copies == pytest.approx(slots)
    two_tied_positives = np.isin(np.arange(len(scores)), [1, 3])
    metrics = queue_metrics(scores, two_tied_positives, [np.arange(len(scores))], np.arange(len(scores)), copies)
    assert metrics["expected_hits"] == pytest.approx(2 / 3)
    assert metrics["recall"] == pytest.approx(1 / 3)
    assert metrics["precision"] == pytest.approx(1 / 3)


def test_cutoff_floors_capacity_and_rebuilds_tie_after_cluster_resampling():
    scores = np.array([0.99, 0.9, 0.6])
    four_rows = np.array([0, 2, 2])
    five_rows = np.array([0, 2, 3])

    zero_slots, empty_queue = queue_weights(scores, four_rows)
    one_slot, resampled_queue = queue_weights(scores, five_rows)

    assert zero_slots == 0
    np.testing.assert_array_equal(empty_queue, [0, 0, 0])
    assert one_slot == 1
    assert resampled_queue @ five_rows == pytest.approx(one_slot)
    assert resampled_queue[1] == 0.5
    assert resampled_queue[2] == 0.0


def test_pooled_recall_and_distinct_capture_use_different_denominators():
    scores = np.tile([0.9, 0.9, 0.6, 0.5, 0.4], 2)
    drug_index = np.tile(np.arange(5), 2)
    positive = drug_index == 0

    metrics = queue_metrics(
        scores, positive, [np.arange(5), np.arange(5, 10)], drug_index, np.ones(5, dtype=int), capture=True
    )

    assert metrics["slots"] == 2
    assert metrics["event_rows"] == 2
    assert metrics["expected_hits"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["event_drugs"] == 1
    assert metrics["distinct_event_drug_capture"] == 0.75


def test_undefined_bootstrap_draw_invalidates_the_interval():
    assert interval(np.array([0.0, np.nan, 0.6])) == {"ci95": None, "undefined_draws": 1}
