"""Hand-checkable queue, variance and sealed-input checks for T4c."""
from datetime import date
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("T4 simulation requires optional NumPy") from exc

from loe_bench import power_v3 as v3


class PowerV3Tests(unittest.TestCase):
    def test_queue_bootstrap_reapplies_capacity_and_exact_ties(self):
        panel = v3.Panel(np.r_[np.arange(6), np.arange(1, 7)], np.repeat([0, 1], 6),
                         np.zeros(12), np.array([1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0], dtype=bool), 7)
        clock = np.array([4, 4, 4, 3, 2, 1, 3, 2, 3, 3, 2, 1])
        score = np.column_stack((clock, np.arange(12), -np.arange(12)))
        counts = np.array([[1, 1, 1, 1, 1, 1, 1], [0, 2, 0, 0, 5, 0, 0],
                           [0, 0, 0, 7, 0, 0, 0]], dtype=np.float32)
        got = v3.recalls(panel, score, counts)
        expected = []
        for count in counts:
            weighted_rows = np.repeat(np.arange(len(clock)), count[panel.drug].astype(int))
            by_cutoff = [weighted_rows[panel.cutoff[weighted_rows] == t] for t in (0, 1)]
            n_events = panel.event[weighted_rows].sum()
            expected.append([sum(v3.point_queue(arm[idx], panel.event[idx])[0] for idx in by_cutoff) / n_events
                             if n_events else np.nan for arm in score.T])
        np.testing.assert_allclose(got, expected, equal_nan=True)
        self.assertAlmostEqual(got[0, 0], (2 / 3) / 4)

    def test_queue_anchor_fallback_matches_explicit_resampled_rows(self):
        n = 120
        scores = np.column_stack((np.arange(n), np.arange(n) // 8, -np.arange(n)))
        panel = v3.Panel(np.arange(n), np.zeros(n), np.zeros(n), np.arange(n) % 7 == 0, n)
        counts = np.zeros((1, n), dtype=np.float32)
        counts[0, :16] = 3
        counts[0, 16:30] = 5
        layout = v3.queue_layout(panel, scores)
        design, queues, _ = layout
        self.assertLess((counts @ design)[0, queues[0].anchor_columns[1]], counts.sum() // 5)
        resampled = np.repeat(np.arange(n), counts[0].astype(int))
        expected = [v3.point_queue(arm[resampled], panel.event[resampled])[0] for arm in scores.T]
        np.testing.assert_allclose(v3.queued_events(layout, counts)[0][0], expected)

    def test_determinism_and_undefined_draw_stop(self):
        ids = np.tile(np.arange(40), 2)
        panel = v3.Panel(ids, np.repeat([0, 1], 40), ids % 30, ids % 8 == 0, 40)
        score = np.column_stack((ids % 5, ids ** 2, -ids))
        def simulate():
            return v3.paired_draws(panel, score, np.random.default_rng(741), 200, ((2, 0), (2, 1)))
        np.testing.assert_array_equal(simulate(), simulate())
        bounds = v3.lower_bounds(np.array([[1., 2., -1.], [1., np.nan, 0.]]), .025)
        np.testing.assert_allclose(bounds, [1., np.nan, -1.], equal_nan=True)
        rates = v3.decision_rates(np.array([[1., np.nan, 2.], [0., 1., 1.], [1., 1., 1.]]), (1,))
        self.assertEqual(rates["H2"]["conditional"]["denominator"], 2)
        self.assertEqual(rates["H3"]["conditional"]["denominator"], 1)
        self.assertEqual(rates["full_sequence"]["count"], 1)

    def test_variance_harness_requires_every_contrast(self):
        empirical = np.tile(np.arange(24.)[:, None], (1, 3))
        ratios = [1.24, .76, .74]
        result = v3.variance_report(empirical, empirical * ratios)
        np.testing.assert_allclose([item["ratio"] for item in result.values()], ratios)
        self.assertEqual([item["pass"] for item in result.values()], [True, True, False])

    def test_exact_null_only_reorders_within_native_tie_blocks(self):
        score = np.array([.4, .4, .4, .2, .2, .2, .1, .1, .1, .1])
        ranks = v3.tied_null(score, np.column_stack((np.arange(10), -np.arange(10))))
        self.assertTrue(np.all(ranks[:3].min(axis=0) > ranks[3:6].max(axis=0)))
        self.assertTrue(np.all(ranks[3:6].min(axis=0) > ranks[6:].max(axis=0)))
        self.assertFalse(np.array_equal(np.argsort(ranks[:, 0]), np.argsort(ranks[:, 1])))

    def test_score_shift_breakpoints_match_exact_top_fifth(self):
        scores = np.arange(10, dtype=float)
        y = np.array([1, 0, 1, 0, 0, 0, 0, 0, 1, 0], dtype=bool)
        panel = v3.Panel(np.arange(10), np.zeros(10), np.zeros(10), y, 10)
        thresholds = v3.breakpoints(panel, scores)
        for tilt in (-4.9, .25, 8.1, 20.1):
            expected = v3.point_queue(scores + tilt * y, y)[0]
            self.assertEqual((thresholds < tilt).sum(), expected)


class PowerV3InputTests(unittest.TestCase):
    def test_cp4_replay_paths_filter_outcomes_before_parse(self):
        scripts = Path(__file__).resolve().parents[2] / "scripts"
        spec = importlib.util.spec_from_file_location("loe_t4c_test_script", scripts / "t4c_power.py")
        script = importlib.util.module_from_spec(spec)
        with patch.object(sys, "path", [str(scripts), *sys.path]), patch.dict("os.environ"):
            spec.loader.exec_module(script)
        replay = script.pipeline.replay
        source = {"application_number": "ANDA000007", "submissions": [
            {"submission_type": "ORIG", "submission_status": "AP", "submission_status_date": "20180101"},
            {"submission_type": "ORIG", "submission_status": "AP", "submission_status_date": "20150101"},
        ], "products": [{"product_number": "001", "approval_date": "20180101", "brand_name": "PROTECTED"}]}
        orange = {"products": [{"application_number": "000007", "application_type": "A",
                               "product_number": "001", "approval_date": "20180101", "brand_name": "PROTECTED"}]}
        original = json.loads

        def decoder(payload):
            self.assertNotIn(b"20180101", payload)
            self.assertNotIn(b"PROTECTED", payload)
            return original(payload)

        def inputs(raw, *_dirs):
            for consumer in (replay.development_reader, lambda p: replay.development_reader(p, identity=True),
                             replay.application_identity_reader):
                records = list(consumer(raw / "df_anda.jsonl"))
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]["submissions"][0]["submission_status_date"], "20150101")
            self.assertEqual(list(replay.historical_orange_reader(raw / "ob_anda_2010s.jsonl")), [])

        with TemporaryDirectory() as folder:
            raw = Path(folder)
            (raw / "df_anda.jsonl").write_text(json.dumps(source) + "\n", encoding="utf-8")
            (raw / "ob_anda_2010s.jsonl").write_text(json.dumps(orange) + "\n", encoding="utf-8")
            with patch.object(replay, "inputs", inputs), patch.object(json, "loads", decoder):
                script.development_inputs(raw, raw)
