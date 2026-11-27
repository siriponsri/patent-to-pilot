"""Synthetic and hand-calculated checks for T4b."""
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

    def test_variance_check_detects_a_single_underdispersed_contrast(self):
        baseline = np.arange(10, dtype=float)[:, None] * np.ones((1, 3))
        observed = power.variance_report(baseline, baseline * [1.25, .74, .75])
        self.assertEqual([item["pass"] for item in observed.values()], [True, False, True])
        self.assertAlmostEqual(observed["M3_minus_M1"]["ratio"], .74)

    def test_validation_draws_preserve_panel_structure_and_seed(self):
        profile = small_profile()
        panel = (np.array([0, 0, 1, 2, 2, 3]), np.array([1, 1, 0, 2, 2, 0]),
                 np.array([False, True, False, False, True, False]))
        ids, error, score, labels = power.validation_score_panel(profile, 0, panel,
                                                                 np.random.default_rng(21))
        np.testing.assert_array_equal(ids, panel[0])
        np.testing.assert_array_equal(labels, panel[2])
        np.testing.assert_array_equal(error, labels)
        settings = power.fit_rank_settings(error, score, [0., 0.])
        settings["skills"]["development"] = [.5, .75, 1.]
        args = (profile, 0, panel, settings, 991, 30)
        a = power.validation_draws(*args)
        np.testing.assert_array_equal(a, power.validation_draws(*args))
        self.assertGreater(np.std(a[:, 0]), 0)
        np.testing.assert_allclose(a[:, 0] - a[:, 1], a[:, 2])

    def test_feature_roster_starts_and_full_followup(self):
        scenario = power.Scenario("fixed", 10, 2, 4, 0, arrivals=(6, 1, 1, 2))
        ids, cutoffs, _, labels = power.histories(small_profile(), scenario, np.random.default_rng(1))
        np.testing.assert_array_equal(np.bincount(cutoffs), [6, 7, 8, 10, 12])
        self.assertEqual(len(set(ids[cutoffs < 4])), 10)
        self.assertFalse(labels.any())

    def test_exact_null_bootstrap_matches_its_paired_subset_at_2000_draws(self):
        profile = small_profile()
        scenario = power.Scenario("fixture", 30, 2, 4, 6, arrivals=(19, 4, 4, 3))
        settings = power.test_rank_settings(profile, scenario, np.random.default_rng(51), 12,
                                            {"null": 0., "useful": .010})
        result = power.bootstrap_experiment(profile, scenario, settings, 910, 6, 2000, "null",
                                            exact_subset=3, h1_only=True)
        bounds, subset, _, _ = result
        np.testing.assert_array_equal(bounds[:3], subset)
        self.assertTrue(np.all(bounds[:, 1, 0] >= bounds[:, 0, 0]))
        self.assertTrue(np.isnan(bounds[:, :, 1:]).all())


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
        encoded = json.dumps({"application_number": "ANDA000001", "submissions": submissions,
                              "products": [{"product_number": "001"}, {
                                  "product_number": "002", "approval_date": "20180202",
                                  "brand_name": "PROTECTED_PRODUCT"}],
                              "application_docs": ["PROTECTED_DOCUMENT"]}).encode()
        decoder = json.loads

        def checked(payload):
            for original in submissions:
                if original["submission_status_date"] != "20121114":
                    self.assertNotIn(original["submission_status_date"].encode(), payload)
            self.assertNotIn(b"PROTECTED", payload)
            return decoder(payload)

        with patch.object(json, "loads", checked):
            projected = self.script.project_development_anda(encoded)
        self.assertEqual(projected["submissions"], [{"submission_type": "ORIG", "submission_status": "AP",
                                                    "submission_status_date": "20121114"}])
        self.assertEqual(projected["products"], [{"product_number": "001"}])
        future_submissions = [dict(submissions[0], nested=item("20121114")), submissions[1]]
        future = json.dumps({"application_number": "ANDA000002", "submissions": future_submissions}).encode()
        with patch.object(json, "loads", side_effect=AssertionError("future outcome reached decoder")):
            self.assertIsNone(self.script.project_development_anda(future))

    def test_grouped_orange_book_filter_excludes_protected_products_before_decoding(self):
        source = {"approval_date": "20150304", "products": [
            {"application_type": "A", "application_number": "001234", "product_number": "001"},
            {"application_type": "A", "application_number": "001234", "product_number": "002",
             "approval_date": "20171002", "brand_name": "PROTECTED"},
            {"application_type": "N", "application_number": "000123", "product_number": "001"},
        ]}
        encoded = json.dumps(source).encode()
        decoder = json.loads

        def checked(payload):
            self.assertNotIn(b"PROTECTED", payload)
            self.assertNotIn(b"20171002", payload)
            return decoder(payload)

        with patch.object(json, "loads", checked):
            generic = self.script.project_orange(encoded, nda=False)
            branded = self.script.project_orange(encoded, nda=True)
        self.assertEqual([p["approval_date"] for p in generic["products"]], ["20150304"])
        self.assertEqual([p["application_type"] for p in branded["products"]], ["N"])

    def test_empirical_bootstrap_agrees_with_e7b_draw_indices_and_coverage(self):
        y = [1, 1, 0, 1, 0, 0, 1]
        keys = ["a", "a", "b", "c", "d", "e", "e"]
        rows = [dict(y=label, key=key) for label, key in zip(y, keys, strict=True)]
        scores = [[.1, .1, .3, .4, .04, .9, .9], [.2, .1, .15, .09, .5, .7, .7],
                  [.1, .2, .4, .4, .07, .1, .7]]
        arms = [[t2.Prediction(p, graph.PREDICT_ENTRY if p >= .5 else graph.PREDICT_NO_ENTRY)
                 for p in arm] for arm in scores]
        arms[2][2] = t2.Prediction(.4, graph.ABSTAIN)
        with patch.object(t2, "BOOTSTRAP_DRAWS", 100):
            draws = self.script.empirical_bootstrap(rows, arms)
        for i, (left, right) in enumerate(power.ARM_PAIRS):
            lo, hi, invalid = t2.paired_cluster_bootstrap_ci(
                t2._aurc80, arms[left], arms[right], y, keys, n_boot=100, seed=t2.BOOTSTRAP_SEED)
            finite = np.sort(draws[np.isfinite(draws[:, i]), i])
            self.assertEqual(len(finite), 100 - invalid)
            np.testing.assert_allclose(finite[[int(.025 * len(finite)), int(.975 * len(finite))]],
                                       [lo, hi], atol=1e-12)

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
