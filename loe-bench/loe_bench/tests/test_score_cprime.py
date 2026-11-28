"""Outcome-free checks of the confirmatory adapter against the frozen scorer."""

from datetime import date
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import score_cprime as score

import numpy as np


class ScoreCprimeTests(unittest.TestCase):
    def test_shared_draw_intervals_match_freeze(self):
        days = [date(2013, 1, 1), date(2014, 1, 1)]
        rows = [{"key": str(i), "t": day, "y": int(i in (0, 2)),
                 "asof": SimpleNamespace(snapshot={}, verdict="CONTESTED", challenge=None)}
                for day in days for i in range(5)]
        scores = {"B1": [0.5] * 10, "M1": [0.2, 0.1, 0.2, 0.1, 0.1] * 2,
                  "M3": [0.5, 0.4, 0.3, 0.2, 0.1] * 2}
        policies = {arm: {"lo": 0.1, "hi": 0.4, "legacy_90": {"threshold": 0.6}} for arm in scores}
        f = score.frozen
        secondary = {arm: f.Secondary(rows, 24, arm, p, p, policies[arm]) for arm, p in scores.items()}
        with patch.object(f.t2, "BOOTSTRAP_DRAWS", 40), patch.object(score, "DRAWS", 40):
            expected = f.with_intervals(f.t1v3.QueuePanel(rows, days, scores), secondary)
            report, draws = score.score_panel(rows, days, 24, scores, scores, policies, {}, None)
        self.assertEqual(draws.shape, (40, 3, len(f.METRICS)))
        self.assertEqual(report["levels"], expected["levels"])
        self.assertEqual(report["contrasts"], expected["contrasts"])
        self.assertEqual(report["arms"]["B1"]["cutoffs"]["2013-01-01"]["boundary_tie_rows"], 5)

    def test_fixed_sequence_stops_on_exact_zero(self):
        def contrast(estimate, lower):
            return {"recall": {"estimate": estimate, "ci95": [lower, 0.3], "undefined_draws": 0}}

        result = score.primary({"24": {"contrasts": {"M3-B1": contrast(0.10, 0.01),
                                                     "M3-M1": contrast(0.02, 0.00)}},
                                "12": {"contrasts": {"M3-B1": contrast(0.14, 0.01)}}})
        self.assertEqual([x["decision"] for x in result.values()],
                         ["PASS", "FAIL", "NOT_REACHED_DESCRIPTIVE"])
        self.assertTrue(result["H1"]["meets_plus_10pp"])
        self.assertEqual(result["H3"]["one_sided_lower"], 0.01)

    def test_one_undefined_draw_invalidates_interval(self):
        report = score.interval(0.2, np.array([0.1, np.nan, 0.2, 0.3]))
        self.assertEqual(report, {"estimate": 0.2, "ci95": None, "undefined_draws": 1})
