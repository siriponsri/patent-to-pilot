"""Known answers for Track A secondary measures."""

from math import log
from datetime import date
from types import SimpleNamespace
import unittest

import numpy as np

from loe_bench import k20t1, t1v3
from loe_bench.tracka_secondary import ACTIONS, arm_measures, legacy_actions, legacy_measures

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

    def test_reconstructs_legacy_actions_at_both_graph_boundaries(self):
        t = date(2026, 11, 27)
        p = [0.25, 0.5, 0.625, 0.75, 0.875] * 2
        rows = [{"t": t, "asof": SimpleNamespace(snapshot=snapshot, challenge=None)}
                for snapshot in ([{}] * 5 + [{"excl_exp": [date(2040, 1, 1)]}] * 5)]
        conflicts = [t1v3.action("M3", row, 12, prob, 0.15, 0.2)[1]
                     for row, prob in zip(rows, p, strict=True)]
        original, _ = k20t1.apply_policy("M3", rows, p, 12, 0.75)
        reconstructed = legacy_actions("M3", p, conflicts, 0.75, 0.2)
        self.assertEqual(reconstructed, [item.action for item in original])
        self.assertEqual(reconstructed, [CLEAR, REFER, REFER, FLAG, FLAG, CLEAR, CLEAR, CLEAR, REFER, REFER])
        for arm in ("B1", "M1"):
            with self.subTest(arm=arm):
                original, _ = k20t1.apply_policy(arm, rows, p, 12, 0.75)
                self.assertEqual(legacy_actions(arm, p, conflicts, 0.75, 0.2), [item.action for item in original])
        self.assertEqual(legacy_actions("B1", [0.5], [False], 0.5, 0.2), [CLEAR])
        with self.assertRaisesRegex(ValueError, "not identifiable"):
            legacy_actions("M3", [0.4], [False], 0.75, 0.5)

    def test_legacy_coverage_gates_use_the_full_roster_and_average_ties(self):
        p, labels = [0.875, 0.125, 0.75, 0.25, 0.5], [1, 1, 0, 0, 1]
        policy = {"hi": 0.2, "legacy_90": {"threshold": 0.75}}
        limited = legacy_measures("B1", p, labels, [False] * 5, policy)
        self.assertEqual((limited["answered"], limited["realized_coverage"]), (4, 0.8))
        self.assertAlmostEqual(limited["aurc80"], 0.5)
        self.assertTrue(limited["aurc80_coverage_met"])
        self.assertFalse(limited["e_aurc_coverage_met"])
        self.assertIsNone(limited["e_aurc"])
        full = legacy_measures("B1", p[:4], labels[:4], [False] * 4, policy)
        self.assertTrue(full["e_aurc_coverage_met"])
        self.assertAlmostEqual(full["e_aurc"], 7 / 24)
        low = legacy_measures("B1", p, labels, [False] * 5, {**policy, "legacy_90": {"threshold": 0.875}})
        self.assertFalse(low["aurc80_coverage_met"])
        self.assertIsNone(low["aurc80"])
