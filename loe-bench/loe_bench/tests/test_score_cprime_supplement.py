"""Hand-checkable fixtures for the export-only C-prime supplement."""

from datetime import date
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import score_cprime_supplement as supplement


class SupplementTests(unittest.TestCase):
    def test_pooled_auc_with_ties(self):
        # The two event rows beat 1.5 and 2 of the three non-event rows.
        self.assertEqual(supplement.pooled_auc([0.2, 0.5, 0.1, 0.2, 0.9], [1, 1, 0, 0, 0]), 3.5 / 6)

    def test_single_class_auc(self):
        for labels in ([0, 0], [1, 1]):
            self.assertEqual(supplement.pooled_auc([0.1, 0.2], labels), "NOT_ESTIMABLE")

    def test_original_calibrator_clips_and_standardizes_score(self):
        parameters = {"intercept": -0.5, "weight": 2.0, "mean": 1.0, "scale": 4.0}
        native = [0.0, 0.5, 1.0]
        clipped = [1e-8, 0.5, 1 - 1e-8]
        expected = [1 / (1 + math.exp(1 - 0.5 * math.log(p / (1 - p)))) for p in clipped]
        for actual, target in zip(supplement.frozen_probabilities(native, parameters), expected, strict=True):
            self.assertAlmostEqual(actual, target, places=15)

    def test_summary_uses_inclusive_calibrated_threshold_and_transcribed_brier(self):
        rows = [{"key": f"fixture-{i}", "cutoff": "2017-01-01", "y": label,
                 **dict.fromkeys(supplement.ARMS, score)}
                for i, (score, label) in enumerate([(0.5, 1), (0.6, 0), (0.1, 1), (0.2, 0), (0.3, 0)])]
        identity = {"calibrator": {"intercept": 0.0, "weight": 1.0, "mean": 0.0, "scale": 1.0}}
        reverse = {"calibrator": {**identity["calibrator"], "weight": -1.0}}
        settings = {"B1": reverse, "M1": identity, "M3": identity}
        panel = supplement.summarize_panel(rows, 12, settings)
        self.assertEqual((panel["rows"], panel["unique_drugs"], panel["event_rows"], panel["prevalence"]),
                         (5, 5, 2, 0.4))
        m1 = panel["arms"]["M1"]
        self.assertEqual((m1["tp"], m1["fp"], m1["tn"], m1["fn"]), (1, 1, 2, 1))
        self.assertEqual((m1["accuracy"], m1["always_negative_accuracy"]), (0.6, 0.6))
        self.assertEqual(panel["arms"]["B1"]["roc_auc"], m1["roc_auc"])
        self.assertEqual(panel["arms"]["B1"]["tp"], 2)
        self.assertEqual([a["brier_from_score"] for a in panel["arms"].values()], [0.0373, 0.0354, 0.0352])
        self.assertEqual(m1["c_index"], {"estimate": "NOT_ESTIMABLE", "comparable_pairs": None})

    def test_concordance_applies_horizon_censoring_and_strict_within_cutoff_order(self):
        cutoff = date(2020, 1, 1)
        early, horizon_end, after = date(2020, 6, 1), date(2021, 1, 1), date(2021, 1, 2)
        events = [early, early, horizon_end, None, after, None]
        cutoffs = [cutoff] * 5 + [date(2019, 1, 1)]
        scores = [0.6, 0.9, 0.6, 0.5, 0.8, 0.0]
        # Only the two early events compare to the three observations at horizon end.
        self.assertEqual(supplement.within_cutoff_c_index(scores, [1, 1, 1, 0, 0, 0], cutoffs, 12, events),
                         {"estimate": 4.5 / 6, "comparable_pairs": 6})
        self.assertEqual(supplement.within_cutoff_c_index([0.6, 0.2], [1, 0], [cutoff] * 2, 12,
                                                         [horizon_end, None]),
                         {"estimate": "NOT_ESTIMABLE", "comparable_pairs": 0})
        with self.assertRaises(ValueError):
            supplement.within_cutoff_c_index([0.6], [1], [cutoff], 12, [cutoff])

    def test_validate_registered_panel_and_reject_invalid_fields(self):
        rows = [{"key": "same-drug", "cutoff": f"{year}-01-01", "y": 0, **dict.fromkeys(supplement.ARMS, 0.4)}
                for year in range(2017, 2026)]
        export = {"status": "AUTHORIZED_CPRIME", "prediction_horizon_months": 12,
                  "frozen_config_sha256": supplement.FROZEN_CONFIG_SHA256, "implementation_sha": "fixture",
                  "rows": rows}
        with patch.dict(supplement.PANEL_ROWS, {12: len(rows)}):
            self.assertEqual(supplement.validate_panel(export, 12, "fixture"), rows)
            with self.assertRaisesRegex(ValueError, "metadata"):
                supplement.validate_panel({**export, "prediction_horizon_months": 24}, 12, "fixture")
            invalid_rows = [
                (rows[1], "Duplicate"),
                ({**rows[0], "cutoff": "2016-01-01"}, "cutoff"),
                ({**rows[0], "y": True}, "Nonbinary"),
                ({**rows[0], "M1": math.nan}, "native probability"),
                ({**rows[0], "event_date": "2017-02-01"}, "row fields"),
            ]
            for invalid, error in invalid_rows:
                with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                    supplement.validate_panel({**export, "rows": [invalid, *rows[1:]]}, 12, "fixture")

    def test_run_checks_both_digests_before_decoding_either_private_export(self):
        invalid_json = b"unparseable synthetic private bytes\n"
        config = json.dumps({"code_commit_sha": "fixture"}).encode()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data" / "FROZEN_CONFIG.json").write_bytes(config)
            (root / "C1_scores_12m.json").write_bytes(invalid_json)
            (root / "C1_scores_24m.json").write_bytes(b"different bytes")
            digest = sha256(invalid_json).hexdigest()
            with (patch.object(supplement, "ROOT", root), patch.object(supplement, "PRIVATE", root),
                  patch.object(supplement, "FROZEN_CONFIG_SHA256", sha256(config).hexdigest()),
                  patch.dict(supplement.EXPORT_SHA256, {12: digest, 24: digest})):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch for C1_scores_24m.json"):
                    supplement.run()
