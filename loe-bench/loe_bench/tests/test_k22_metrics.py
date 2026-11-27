import unittest

import numpy as np

from loe_bench.review_metrics import ReviewQueue


class ReviewQueueTests(unittest.TestCase):
    def test_per_cutoff_capacity_boundary_ties_and_distinct_drug_capture(self):
        scores = [1, 1, 0, 0, 0, 1, 1, 0, 0, 0]
        labels = np.array([1, 0, 0, 0, 0, 1, 0, 1, 0, 0])
        ids = np.array([0, 1, 2, 3, 4, 0, 5, 6, 7, 8])
        losses = np.array([0.5, 1, 0, 0, 0, 0.5, 0, 10, 0, 0])
        queue = ReviewQueue(scores, [1] * 5 + [2] * 5)
        weights = np.ones(10)
        np.testing.assert_allclose(queue.measure(labels, losses, weights), [1 / 3, 0.5, 1.3 / 3, 1.2])
        self.assertEqual(queue.distinct_event_drugs(labels, ids, weights), 0.75)

        # Resample the repeated event drug twice. Both cutoff capacities remain one,
        # with 2/3 expected event capture from each boundary tie block.
        weights[ids == 0] = 2
        recall, precision, _, _ = queue.measure(labels, losses, weights)
        self.assertAlmostEqual(recall, 4 / 15)
        self.assertAlmostEqual(precision, 2 / 3)
