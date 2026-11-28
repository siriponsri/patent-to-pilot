"""Hand-check C4 v2 aggregation, lag, queues and paired scoring."""

import csv
import json
import tempfile
import unittest
import zipfile
from datetime import date
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

from loe_bench import c4, c4b
from loe_bench.tests.test_c4 import product


def queue_rows():
    return [{"cutoff": "2013-01-01", "key": key,
             "B1": int(key == "B"), "M3": int(key == "A")}
            for key in "ABCDE"]


def write_sdud(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow((*c4.FIELDS, c4.REIMBURSEMENT_FIELD))
        writer.writerows(rows)


class MedicaidReimbursementTests(unittest.TestCase):
    def test_national_amount_suppression_duplicates_and_coverage(self):
        a, b, unresolved = "00000111101", "00000111102", "00000111103"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv"
            write_sdud(path, [
                ("XX", a, 2009, 1, "FFSU", "false", 3, "6.01"),
                ("NY", a, 2009, 1, "FFSU", "false", 4, "70.99"),
                ("XX", b, 2009, 1, "FFSU", "false", 5, "6.03"),
                ("XX", b, 2009, 1, "FFSU", "false", 5, "6.03"),
                ("XX", unresolved, 2009, 1, "FFSU", "true", "*", "99.99"),
            ])
            period = c4.quarter(2009, 1)
            raw = c4.read_sdud(path, 2009, include_reimbursement=True)[period]
        self.assertIsNone(raw[b].reimbursed_cents["FFSU"])
        self.assertNotIn("FFSU", raw[unresolved].reimbursed_cents)
        walk = c4.build_crosswalk([product("00000-1111-01", "A", "B"),
                                   product("00000-1111-02", "B")])
        result = c4.aggregate(period, raw, walk, include_reimbursement=True)
        self.assertEqual(result.counts, {"A": 3, "B": None})
        self.assertEqual(result.reimbursed_cents, {"A": 601, "B": None})
        info = c4b.window_coverage(range(period, period + 1), {period: result})
        self.assertAlmostEqual(info["frame"]["mapped_identity_share"], 2 / 3)
        self.assertEqual(info["ingredients"]["B"], {
            "mapped_package_quarters": 2, "count_complete_share": .5, "amount_complete_share": .5,
            "joint_complete_share": .5, "full_ingredient_identity_share": None,
        })

    def test_q4_ratio_uses_sixth_step_and_only_q4_observation(self):
        anchor = c4.quarter(2016, 2)
        origin = date(2016, 12, 31)
        training = {anchor - 7 + i: c4.IngredientQuarter(
            counts={"A": 2, "ZERO": 0}, reimbursed_cents={"A": 200 * (10 + i), "ZERO": 0})
            for i in range(8)}
        q4 = c4.quarter(2017, 4)
        target = {q4: c4.IngredientQuarter(counts={"A": 2}, reimbursed_cents={"A": 4200})}
        _, _, results = c4b.score_origin(origin, anchor, training, target)
        ratio = results["reimbursement_per_prescription_q4"]
        self.assertEqual(ratio["mapped"], [c4b.Forecast("A", 21, {"carry_forward": 17, "drift": 23})])
        self.assertEqual(ratio["exclusions"]["incomplete_history"], 1)
        self.assertEqual(results["annual_reimbursement"]["mapped"], [])
        with self.assertRaisesRegex(ValueError, "must precede"):
            c4b.score_origin(date(2017, 3, 31), anchor, None, None)


class QueueTests(unittest.TestCase):
    cutoff = date(2013, 1, 1)
    sizes = {"2013-01-01": 5}

    def test_queue_budget_and_oracle_free_arms(self):
        queue = c4b.build_queues(queue_rows(), self.sizes, 42)[self.cutoff]
        self.assertEqual(queue.selected, {"B1": {"B"}, "M3": {"A"}})
        rows = [c4b.Forecast(name, 15, {"carry_forward": 20, "drift": 25}) for name in "ABCFX"]
        linked = {name: name for name in "ABCF"}
        adjusted, linkage = c4b.apply_queue(rows, linked, queue, 0.465)
        self.assertEqual(linkage, {"matched_rows": 3, "unresolved_moiety": 1,
                                  "outside_roster": 1, "B1_triggers": 1, "M3_triggers": 1})
        for name, b1, m3 in (("A", 20, 9.3), ("B", 9.3, 20), ("C", 20, 20)):
            row = next(value for value in adjusted if value.ingredient == name)
            self.assertEqual((row.predictions["B1_adjusted"], row.predictions["M3_adjusted"]), (b1, m3))

    def test_ties_are_stable_and_protected_or_bad_exports_fail_closed(self):
        tied = [{**row, "B1": 1, "M3": 1} for row in queue_rows()]
        queue = c4b.build_queues(tied, self.sizes, 42)[self.cutoff]
        self.assertEqual(queue.selected["B1"], queue.selected["M3"])
        self.assertEqual(len(queue.selected["B1"]), 1)
        self.assertEqual(c4b.build_queues(reversed(tied), self.sizes, 42)[self.cutoff], queue)
        for bad in ({"cutoff": "2017-01-01"}, {"M3": float("nan")}, {"label": 1}):
            with self.assertRaises(ValueError):
                c4b.build_queues([{**tied[0], **bad}, *tied[1:]], self.sizes, 42)
        with self.assertRaisesRegex(ValueError, "roster size"):
            c4b.build_queues(tied[:4], self.sizes, 42)

    def test_missing_and_24_month_exports_remain_pending(self):
        policy = {"rows_by_cutoff": self.sizes, "config_sha256": "digest", "tie_seed": 42}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical, twelve = root / "FREEZE_dev_scores.json", root / "FREEZE_dev_scores_12m.json"
            self.assertEqual(c4b.load_queues([canonical], policy)[1]["status"], c4b.PENDING)
            data = {"status": c4b.SCOPE, "prediction_horizon_months": 24,
                    "frozen_config_sha256": "digest", "rows": []}
            canonical.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(c4b.load_queues([canonical], policy)[1]["status"], c4b.PENDING)
            data.update(prediction_horizon_months=12, rows=queue_rows())
            twelve.write_text(json.dumps(data), encoding="utf-8")
            policy["export_sha256"] = "wrong"
            with self.assertRaisesRegex(ValueError, "export SHA-256 mismatch"):
                c4b.load_queues([twelve], policy)
            policy["export_sha256"] = sha256(twelve.read_bytes()).hexdigest()
            queues, provenance = c4b.load_queues([canonical, twelve], policy)
            self.assertIn(self.cutoff, queues)
            self.assertEqual(provenance["sha256"], sha256(twelve.read_bytes()).hexdigest())


class MetricsTests(unittest.TestCase):
    def test_bootstrap_resamples_whole_ingredients_and_paired_errors(self):
        rows = [c4b.Forecast("A", 10, {"carry": 20, "drift": 10}),
                c4b.Forecast("A", 10, {"carry": 0, "drift": 10}),
                c4b.Forecast("B", 10, {"carry": 10, "drift": 22})]
        summary = c4b.metrics(rows, draws=2000, seed=42)
        self.assertEqual((summary["paired_rows"], summary["ingredients"]), (3, 2))
        self.assertAlmostEqual(summary["estimates"]["drift_minus_carry_mae"], -8 / 3)
        self.assertEqual(summary["ci95"]["carry_bias"], [0, 0])
        self.assertEqual(summary["ci95"]["drift_minus_carry_mae"], [-10, 12])

    def test_end_to_end_with_locked_synthetic_sdud_and_nonoverlapping_queues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            walk_path = root / "walk.zip"
            with zipfile.ZipFile(walk_path, "w") as archive:
                archive.writestr("walk.json", json.dumps({"meta": {"last_updated": "fixture"},
                    "results": [product("00000-1111-01", "A"), product("00000-1111-02", "B")]}))
            files = {"walk": {"file": walk_path.name, "sha256": sha256(walk_path.read_bytes()).hexdigest(),
                              "member": "walk.json", "vintage": "fixture"}}
            for year in range(2010, 2014):
                path = root / f"{year}.csv"
                rows = [("XX", f"0000011110{i}", year, q, kind, "false", 5,
                         "40.00" if year == 2013 and i == 1 else "100.00")
                        for q in range(1, 5) for kind in c4.TYPES for i in (1, 2)]
                if year == 2013:
                    rows.append(("XX", "00000111103", year, 4, "FFSU", "false", 5, "100.00"))
                write_sdud(path, rows)
                files[str(year)] = {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest(), "year": year}
            manifest = {"origins": [{"origin": "2012-12-31", "verdict": c4.RETROSPECTIVE,
                        "last_fit_quarter": [2012, 2], "crosswalk": "walk",
                        "training_files": {str(year): str(year) for year in range(2010, 2013)}}],
                        "files": files, "outcome_freeze": {"crosswalk": "walk", "files": {"2013": "2013"}}}
            spec = {"development_origins": ["2012-12-31"], "entry_policy": {"factor": 0.465},
                    "metrics": {"bootstrap": {"draws": 2000, "seed": 42}}}
            queues = c4b.build_queues(queue_rows(), QueueTests.sizes, 42)
            registry = SimpleNamespace(composition=lambda names: SimpleNamespace(
                parts=names, key=names[0], low_confidence=False))
            result = c4b.run(spec, manifest, root, registry, queues, {"status": "AVAILABLE"})
        self.assertEqual(result["scope"], c4b.SCOPE)
        self.assertEqual(result["vintage_label"], c4b.VINTAGE_LABEL)
        ratio = result["pooled"]["reimbursement_per_prescription_q4"]
        annual = result["pooled"]["annual_reimbursement"]
        self.assertEqual(ratio["full_national"]["status"], "NOT_ESTIMABLE")
        self.assertEqual(ratio["mapped_baselines"]["estimates"]["carry_forward_mae"], 6)
        self.assertAlmostEqual(ratio["entry_adjusted"]["estimates"]["M3_adjusted_mae"], .65)
        self.assertAlmostEqual(ratio["entry_adjusted"]["estimates"]["B1_adjusted_mae"], 11.35)
        self.assertEqual(annual["entry_adjusted"]["evaluable_origins"], 1)
        self.assertAlmostEqual(annual["entry_adjusted"]["estimates"]["M3_adjusted_mae"], 26)


if __name__ == "__main__":
    unittest.main()
