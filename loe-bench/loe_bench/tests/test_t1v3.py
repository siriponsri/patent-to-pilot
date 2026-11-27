from datetime import date
from math import log
from types import SimpleNamespace
import unittest

import numpy as np

from loe_bench import evidence_graph as graph, t1v3
from loe_bench.seal import TEST_FIRST, TestSealError as SealError


FIRST = date(2013, 1, 1)
SECOND = date(2014, 1, 1)
EMPTY = date(2015, 1, 1)


def tied_panel():
    rows = [{"key": key, "t": day, "y": int(key == "A")}
            for day in (FIRST, SECOND) for key in "ABCDE"]
    scores = [0.5, 0.5, 0.1, 0.1, 0.1] * 2
    return t1v3.QueuePanel(rows, [FIRST, SECOND, EMPTY], {arm: scores for arm in t1v3.ARMS})


class QueueTests(unittest.TestCase):
    def test_ties_pool_rows_and_count_drug_once_across_cutoffs(self):
        result = tied_panel().evaluate([1, 1, 1, 1, 1])
        self.assertEqual([x["capacity"] for x in result["cutoffs"]], [1, 1, 0])
        self.assertEqual((result["event_rows"], result["event_drugs"]), (2, 1))
        for arm in result["arms"].values():
            self.assertEqual(arm["recall"], 0.5)
            self.assertEqual(arm["precision"], 0.5)
            self.assertEqual(arm["distinct_event_drug_capture"], 0.75)
            self.assertEqual(arm["expected_captured_event_drugs"], 0.75)
            self.assertEqual([x["boundary_tie_rows"] for x in arm["cutoffs"]], [2, 2, 0])

    def test_bootstrap_copies_change_rank_weights_and_capacity(self):
        # Per year, 4 A copies and no B. Two slots from a four-way A tie.
        result = tied_panel().evaluate([4, 0, 2, 2, 2])
        self.assertEqual(result["queue_slots"], 4)
        self.assertEqual((result["event_rows"], result["event_drugs"]), (8, 4))
        arm = result["arms"]["B1"]
        self.assertEqual(arm["expected_queued_events"], 4)
        self.assertEqual(arm["expected_captured_event_drugs"], 3)
        self.assertEqual(arm["precision"], 1)

    def test_undefined_draw_invalidates_interval(self):
        result = t1v3.bootstrap(tied_panel())
        self.assertGreater(result["undefined_draws"], 0)
        self.assertIsNone(result["levels"]["B1"]["recall"]["ci95"])
        contrast = result["contrasts"]["M3-B1"]["recall"]
        self.assertEqual(contrast["estimate"], 0)
        self.assertIsNone(contrast["ci95"])
        self.assertEqual(contrast["undefined_draws"], result["undefined_draws"])
        self.assertEqual(result["contrasts"]["M3-B1"]["precision"]["ci95"], [0, 0])

    def test_no_slots_no_events_and_protected_cutoff(self):
        empty = {arm: [] for arm in t1v3.ARMS}
        panel = t1v3.QueuePanel([], [EMPTY], empty)
        result = panel.evaluate(np.array([], dtype=int))
        self.assertEqual(result["queue_slots"], 0)
        self.assertTrue(all(result["arms"]["B1"][metric] is None for metric in t1v3.METRICS))
        with self.assertRaises(SealError):
            t1v3.QueuePanel([], [TEST_FIRST], empty)


class PolicyTests(unittest.TestCase):
    def test_thresholds_keep_ties_and_choose_largest_safe_clear(self):
        risk = [0.01, 0.02, 0.1, 0.8, 0.8, 0.9]
        labels = [0, 0, 1, 0, 1, 1]
        self.assertEqual(t1v3.choose_thresholds(risk, labels, [False] * 6), (0.02, 0.9))
        self.assertEqual(t1v3.choose_thresholds(risk, labels, [False] * 5 + [True]), (0.02, 0.9))
        self.assertEqual(t1v3.choose_thresholds(risk, labels, [False] * 4 + [True, True]), (0.02, 0.8))
        self.assertEqual(t1v3.choose_thresholds([0.5] * 5, [1] * 5, [False] * 5), (0, 1))

    def test_graph_conflict_and_clear_guard(self):
        evidence = SimpleNamespace(snapshot={"excl_exp": [date(2020, 1, 1)]}, challenge=None)
        row = {"t": FIRST, "asof": evidence}
        actual = [t1v3.action("M3", row, 12, p, 0.1, 0.8) for p in (0.1, 0.5, 0.8)]
        self.assertEqual(actual, [(graph.PREDICT_NO_ENTRY, False),
                                  (graph.ABSTAIN, False), (graph.ABSTAIN, True)])
        self.assertEqual(t1v3.action("M1", row, 12, 0.8, 0.1, 0.8), (graph.PREDICT_ENTRY, False))

    def test_clear_bound_is_positive_at_zero_and_scales_with_cluster_size(self):
        labels = [0] * 200
        targets = (list(range(200)), list(range(100)) * 2)
        for size, groups in enumerate(targets, start=1):
            low, high = t1v3.clear_rate_ci(labels, groups)
            self.assertEqual(low, 0)
            self.assertAlmostEqual(high, -log(0.025) * size / 200)
        low, high = t1v3.clear_rate_ci([1] * 10 + [0] * 190, targets[0])
        self.assertLess(low, 0.05)
        self.assertGreater(high, 0.05)
        self.assertIsNone(t1v3.clear_rate_ci([], []))
