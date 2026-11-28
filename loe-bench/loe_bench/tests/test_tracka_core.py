"""Hand-checkable fixtures for prospective Track A preparation."""
from datetime import date
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import tracka_core as core

from loe_bench.dataset import Entity


class TrackACoreTests(unittest.TestCase):
    def test_schedule_checks_full_maturity_and_edition_availability(self):
        def coverage(_history, day):
            return {"status": "STALE" if day.year == 2011 else "FRESH"}

        with patch.object(core, "edition_coverage", coverage):
            admitted12, audit12 = core.schedule(None, 12)
            admitted24, audit24 = core.schedule(None, 24)

        self.assertEqual(admitted12[-1], date(2025, 1, 1))
        self.assertEqual(admitted24[-1], date(2024, 1, 1))
        self.assertEqual(audit12[date(2011, 1, 1)]["status"], "OB_STALE")
        self.assertEqual(audit24[date(2025, 1, 1)]["status"], "WINDOW_OPEN")

    def test_roster_checks_dated_type1_and_prior_final_anda(self):
        def history(key, type1, anda=None):
            entity = Entity(key, nda_first=date(2000, 1, 1), anda_first=anda)
            if type1:
                entity.record_flag("nme", type1)
            return entity

        entities = {e.key: e for e in (
            history("at_cutoff", core.T0),
            history("prior_anda", core.T0, core.T0),
            history("no_type1", None),
            history("late_type1", date(2026, 11, 28)),
        )}
        rows, audit = core.forecast_roster(entities)
        self.assertEqual([row["key"] for row in rows], ["at_cutoff"])
        self.assertNotIn("y", rows[0])
        self.assertEqual(audit["prior_final_anda"], 1)

    def test_boundary_ties_keep_exact_expected_capacity(self):
        scores = [0.9, 0.8, 0.8, 0.8, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1]
        weights, audit = core.queue_allocation(scores, [core.T0] * len(scores))
        self.assertEqual(weights, [1, 1 / 3, 1 / 3, 1 / 3, 0, 0, 0, 0, 0, 0])
        self.assertEqual(audit["capacity"], 2)
        self.assertEqual(audit["slots_at_boundary"], 1)

    def test_calibration_reuses_frozen_fit_threshold_and_drug_folds(self):
        days = (date(2010, 1, 1), date(2012, 1, 1))
        verdicts = ("OPEN", "BLOCKED", "CONTESTED")
        rows = []
        for day in days:
            for i in range(20):
                x = {name: 0.0 for name in (*core.frozen.MODEL_FEATURES, *core.frozen.CHALLENGE_FEATURES)}
                x["age_years"] = 1 + i
                asof = SimpleNamespace(x=x, verdict=verdicts[i % 3], snapshot={}, challenge=None,
                                       edition_source={"kind": "fda_zip"})
                rows.append({"t": day, "key": f"drug_{i}", "x": x, "asof": asof, "y": int(i % 3 == 0),
                             "breadth": dict.fromkeys(core.devx.BREADTH, 0)})
        reference, ref_policy, ref_inner = core.frozen.inner_fits(rows, 12, core.T0)
        calibrators, policy, inner = core.calibrate(rows, 12)
        self.assertEqual(inner["fold_counts"], ref_inner["fold_counts"])
        for arm in core.t1v3.ARMS:
            self.assertEqual(core.logistic_parameters(calibrators[arm]), core.logistic_parameters(reference[arm]))
            for name in ("lo", "hi", "legacy_90"):
                self.assertEqual(policy[arm][name], ref_policy[arm][name])
            self.assertEqual(policy[arm]["inner_flags"], ref_policy[arm]["inner_policy"]["flag_rows"])
