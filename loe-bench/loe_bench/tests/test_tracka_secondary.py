"""Known answers for Track A secondary measures."""

from math import log
import unittest

import numpy as np

from loe_bench.tracka_secondary import ACTIONS, arm_measures

CLEAR, FLAG, REFER = ACTIONS


class SecondaryTest(unittest.TestCase):
    def measures(self, p, labels, actions):
        keys = [f"synthetic-{i}" for i in range(len(p))]
        return arm_measures(keys, p, labels, actions, np.ones((1, len(p)), dtype=int))

    def test_calibration_ties_selective_risk_and_diagnostic_actions(self):
        actions = [(CLEAR, False), (FLAG, False), (CLEAR, False), (REFER, True), (REFER, False)]
        row, levels = self.measures([.875, .875, .25, .5, .5], [1, 0, 0, 1, 0], actions)
        self.assertEqual(row["ece_bin_counts"], [0, 0, 1, 0, 0, 2, 0, 0, 2, 0])
        self.assertAlmostEqual(levels["ece"][0], .2)
        self.assertAlmostEqual(levels["aurc80"][0], 41 / 96)
        self.assertAlmostEqual(levels["e_aurc"][0], 7 / 24)
        self.assertAlmostEqual(levels["mean_decision_loss"][0], 2.4)
        self.assertAlmostEqual(levels["flag_or_referral_rate"][0], .6)
        self.assertAlmostEqual(levels["referral_rate"][0], .4)
        diagnostic = row["diagnostic"]
        self.assertEqual(diagnostic["rows"], {"clear": 2, "flag": 1, "refer": 2})
        self.assertEqual(diagnostic["referred_events"], 1)
        self.assertEqual(diagnostic["conflict_referrals"], 1)
        self.assertEqual(diagnostic["false_flags"], 1)
        self.assertEqual(diagnostic["missed_clear_events"], 1)
        self.assertEqual(diagnostic["missed_clear_rate"], .5)
        lower, upper = diagnostic["missed_clear_ci95"]
        self.assertAlmostEqual(2 * lower - 1 - log(2 * lower), -log(.025))
        self.assertEqual((upper, diagnostic["auto_clear_safety"]), (1, "FAIL"))

    def test_clear_bound_can_fail_with_zero_misses(self):
        for n, expected in ((122, "FAIL"), (123, "PASS")):
            row, _ = self.measures([.1] * n, [0] * n, [(CLEAR, False)] * n)
            diagnostic = row["diagnostic"]
            self.assertEqual(diagnostic["missed_clear_ci95"], [0, -log(.025) / n])
            self.assertEqual(diagnostic["auto_clear_safety"], expected)

    def test_zero_clears_are_unevaluable(self):
        row, levels = self.measures([0, 1], [0, 1], [(REFER, False), (FLAG, False)])
        self.assertEqual(row["ece_bin_counts"], [1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
        self.assertEqual(levels["aurc80"][0], 0)
        self.assertEqual(row["diagnostic"]["auto_clear_safety"], "UNEVALUABLE")
        self.assertIsNone(row["diagnostic"]["missed_clear_ci95"])

    def test_legacy_and_missing_diagnostic_actions_have_explicit_dispositions(self):
        row, levels = self.measures([.3, .7], [0, 1], [(CLEAR, False), (None, None)])
        self.assertEqual(row["legacy_policy_90"]["status"], "NOT_ESTIMABLE")
        self.assertEqual(row["diagnostic"]["status"], "NOT_ESTIMABLE")
        self.assertNotIn("mean_decision_loss", levels)
