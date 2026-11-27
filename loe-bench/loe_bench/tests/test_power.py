"""Synthetic and hand-calculated checks for T4; never load protected rows."""
import importlib.util
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("T4 simulation requires optional NumPy") from exc

from loe_bench import evidence_graph as graph, power, t2


def small_profile():
    correlation = np.full((3, 3), 0.65)
    np.fill_diagonal(correlation, 1)
    return power.Profile(
        non_events=np.array([[3, 0, 0], [6, 1, 0], [15, 2, 0], [4, 3, 0]]),
        events=np.array([[7, 0, 1], [12, 0, 3], [4, 2, 2], [5, 3, 1]]),
        extra_arrivals=np.array([[1, 3, 0]]),
        years=4, age_edges=np.array([5, 10]), age_means=np.array([[.4, .1, -.2]] * 2),
        skill=np.array([.15, .1]), arm_correlations=np.array([correlation] * 2),
        cluster_correlation=np.array([.5, .5]), abstention=np.array([[.02, .06]] * 2),
        call_entry=np.zeros((2, 2)),
    )


class PowerTests(unittest.TestCase):
    def test_weighted_ties_fractional_boundary_and_coverage_match_reference(self):
        # Weights duplicate the entire first drug, including both of its rows.
        ranks = [0, 1, 1, 2, 2, 3]
        labels = [1, 1, 0, 1, 0, 0]
        for sampled in ([0, 1, 0, 1, 2, 3, 4, 5], [2, 3, 4, 5, 5]):
            for abstain_rank in (3, 4):
                kept = [i for i in sampled if ranks[i] < abstain_rank]
                counts = np.bincount([ranks[i] for i in kept], minlength=4)
                errors = np.bincount([ranks[i] for i in kept], weights=[labels[i] for i in kept], minlength=4)
                predictions = [t2.Prediction(ranks[i] / 10, graph.PREDICT_NO_ENTRY
                                             if ranks[i] < abstain_rank else graph.ABSTAIN) for i in sampled]
                expected = t2._aurc80(predictions, [labels[i] for i in sampled])
                actual = power.area(counts, errors, len(sampled), power.harmonic_numbers(len(sampled)))
                if np.isnan(expected):
                    self.assertTrue(np.isnan(actual))
                else:
                    self.assertAlmostEqual(actual, expected, places=13)

    def test_horizon_labels_are_nested_and_event_clusters_fixed(self):
        profile = small_profile()
        scenario = power.Scenario("fixture", 120, 5, 8, 24)
        ids, cutoffs, _, labels = power.histories(profile, scenario, np.random.default_rng(43))
        self.assertFalse(np.any(labels[:, 1] & ~labels[:, 0]))
        self.assertEqual(len(set(ids[(cutoffs < 8) & labels[:, 0]])), 24)
        self.assertEqual(len(set(ids[cutoffs < 8])), 120)
        self.assertEqual(len(set(ids)), 125)

    def test_generator_hits_independent_population_targets(self):
        profile = small_profile()
        scenario = power.Scenario("fixture", 200, 8, 8, 38)
        settings = power.calibration(profile, scenario, np.random.default_rng(21), 80)
        for name, target in (("null", 0), ("useful", -.010)):
            population = power.verify_population(profile, scenario, settings,
                                                 np.random.default_rng(91), 480, name)
            np.testing.assert_allclose(population["delta"], target, atol=.0012)

    def test_small_null_type_i_and_fixed_seed(self):
        profile = small_profile()
        scenario = power.Scenario("fixture", 120, 5, 8, 24)
        settings = power.calibration(profile, scenario, np.random.default_rng(21), 18)
        args = (profile, scenario, settings, 101, 320, 120, "null")
        result = power.simulate(*args)
        self.assertEqual(result, power.simulate(*args))
        rate = result["rates"]["H1"]["overall"]
        # A fast stochastic sanity check, not evidence for alpha control.
        self.assertGreater(rate["n"], 0)
        self.assertLess(rate["rate"], .06)
        self.assertLessEqual(result["rates"]["H3"]["overall"]["n"], result["rates"]["H2"]["overall"]["n"])

    def test_fixed_sequence_and_invalid_denominators(self):
        upper = np.array([[-1., -1., -1.], [0., -1., -1.], [-1., np.nan, -1.]])
        rates = power.operating_rates(upper)
        self.assertEqual(rates["H2"]["conditional"]["denominator"], 2)
        self.assertEqual(rates["H3"]["conditional"]["denominator"], 1)
        self.assertEqual(rates["H3"]["overall"]["n"], 1)
        self.assertIsNone(power.operating_rates(np.zeros((2, 3)))["H2"]["conditional"]["rate"])


class InputBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scripts = Path(__file__).resolve().parents[2] / "scripts"
        spec = importlib.util.spec_from_file_location("loe_t4_test_script", scripts / "t4_power.py")
        cls.script = importlib.util.module_from_spec(spec)
        with patch.object(sys, "path", [str(scripts), *sys.path]), patch.dict("os.environ"):
            spec.loader.exec_module(cls.script)

    def test_mixed_source_projection_admits_only_closed_development_events(self):
        def item(when, status="AP"):
            return {"submission_type": "ORIG", "submission_status": status, "submission_status_date": when,
                    "submission_property_type": [{"description": "nested [brackets]"}]}

        submissions = [item("20170101"), item("20160102"), item("20160101"),
                       item("20030101", "TA"), item("20121114")]
        encoded = json.dumps({"application_number": "ANDAfixture", "submissions": submissions,
                              "products": [{"product_number": "001"}]}).encode()
        decoder = json.loads

        def checked(payload):
            for original in submissions:
                self.assertNotIn(original["submission_status_date"].encode(), payload)
            return decoder(payload)

        with patch.object(json, "loads", checked):
            projected = self.script.project_development_anda(encoded)
        self.assertEqual(projected["submissions"], [{"submission_type": "ORIG", "submission_status": "AP",
                                                    "submission_status_date": "20121114"}])
        self.assertIsNone(self.script.project_development_anda(
            json.dumps({"submissions": submissions[:2]}).encode()))

    def test_feature_counts_use_availability_and_never_use_event_attributes(self):
        class Feature:
            nda_first = date(2016, 1, 1)

            def flag_at(self, flag, cutoff):
                return cutoff.year >= 2018

            @property
            def anda_first(self):
                raise AssertionError("test-period outcome access")

        counts = self.script.candidate_counts({"one": Feature()}, date(2026, 11, 27))
        self.assertEqual(counts["24"]["by_cutoff"]["2017-01-01"]["rows"], 0)
        self.assertEqual(list(counts["24"]["by_cutoff"])[-1], "2024-01-01")
        self.assertEqual(counts["24"]["drug_clusters"], 1)
        self.assertEqual(counts["12"]["rows"], counts["24"]["rows"] + 1)


if __name__ == "__main__":
    unittest.main()
