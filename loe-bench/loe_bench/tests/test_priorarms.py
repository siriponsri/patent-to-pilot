from datetime import date
from importlib.util import find_spec
import json
from math import exp
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import warnings

import numpy as np

from loe_bench import priorarms as arms
from loe_bench.review_metrics import ReviewQueue


class PriorArmsFixtures(unittest.TestCase):
    def test_horizon_boundary_and_censoring(self):
        row = {"t": date(2019, 11, 27), "t_end": date(2020, 11, 27), "y": 1}
        self.assertEqual(arms.survival_target(row, row["t_end"]), (True, 366))
        self.assertEqual(arms.survival_target(row, date(2019, 11, 28)), (True, 1))
        with self.assertRaises(ValueError):
            arms.survival_target(row, row["t"])
        row["y"] = 0
        for day in (None, date(2020, 11, 28)):
            self.assertEqual(arms.survival_target(row, day), (False, 366))

    def test_frozen_missingness_bits_and_dated_feature_order(self):
        x = {"age_years": 10, "oral": 1, "injectable": 0, "nce_remaining_years": 0,
             "years_to_last_patent_expiry": 0, "nce_remaining_years_missing": 0,
             "years_to_last_patent_expiry_missing": 1, "orphan": 1,
             "challenge_present": 0, "challenge_missing": 1}
        row = {"t": date(2010, 1, 1), "asof": SimpleNamespace(x=x)}
        self.assertEqual(arms.predictors(row, date(2000, 1, 1)),
                         {arms.P1: [10, 1, 0, 0, 0, 0, 1], arms.P2: [10, 1, 1, 0, 0, 1, 2000]})

    def test_fractional_ties_and_rebuilt_capacity(self):
        queue = ReviewQueue([0.8, 0.8, 0.7, 0.5, 0.1], [0] * 5)
        labels = np.array([1, 0, 0, 0, 0])
        self.assertEqual(arms.recall(queue, labels, np.ones(5, dtype=int)), (0.5, 1))
        self.assertEqual(arms.recall(queue, labels, np.array([1, 3, 2, 2, 2])), (0.5, 2))
        self.assertEqual(arms.recall(queue, labels, np.array([1, 3, 0, 0, 0])), (0, 0))

    def test_concordance_equal_times_censor_and_cutoffs(self):
        self.assertEqual(arms.concordance([.6, .7, .6, .1, .3, .1], [1, 1, 0, 1, 0, 0],
                                          [10, 20, 20, 20, 19, 20], [0, 0, 0, 0, 0, 1]),
                         {"estimate": .625, "comparable_pairs": 4})
        self.assertEqual(arms.concordance([.8, .2], [1, 0], [20, 20], [0, 0]),
                         {"estimate": None, "comparable_pairs": 0})

    def test_half_probability_is_positive(self):
        self.assertEqual(arms.classification([.5, .5, .1, .1], [1, 0, 1, 0]),
                         {"accuracy": .5, "tp": 1, "fp": 1, "tn": 1, "fn": 1,
                          "always_negative_accuracy": .5})


@unittest.skipUnless(find_spec("sksurv"), "requires the isolated PRIORARMS venv")
class PriorArmsSurvivalFixtures(unittest.TestCase):
    def test_offline_worker_entrypoint(self):
        train = {arms.P1: [[i, 0, 1, 0, 0, 0, 1] for i in range(20)],
                 arms.P2: [[i, 0, 1, 0, 0, 0, 2000 - i] for i in range(20)]}
        probe = {arm: values[:2] for arm, values in train.items()}
        target = [(bool(i % 2), 0.5 if i % 2 else 1) for i in range(20)]
        result = subprocess.run([sys.executable, "-B", "-m", "loe_bench.priorarms_survival"],
                                input=json.dumps({"train": train, "predict": probe, "target": target}),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({arm: fit["status"] for arm, fit in json.loads(result.stdout)["arms"].items()},
                         {arms.P1: "PASS", arms.P2: "PASS"})

    def test_train_only_cox_scaling_and_zero_variance_drop(self):
        from loe_bench.priorarms_survival import cox_inputs, runtime

        runtime()
        train = np.array([[1, 0, 1, 0, 0, 1, 2000], [3, 1, 1, 0, 0, 1, 2002]], dtype=float)
        probe = np.array([[4, 1, 0, 1, 1, 0, 2005]], dtype=float)
        x, p, audit = cox_inputs(train, probe)
        self.assertEqual(x.tolist(), [[-1, 0, -1], [1, 1, 1]])
        self.assertEqual(p.tolist(), [[2, 1, 4]])
        self.assertEqual(audit["zero_variance_dropped"],
                         ["oral", "injectable", "challenge_present", "challenge_missing"])

    def test_cox_analytic_breslow_probability_and_exact_repeat(self):
        from sksurv.util import Surv
        from loe_bench.priorarms_survival import fit_arm

        train = [[age, 0, 1, 0, 0, 0, year] for age, year in [(1, 2002), (3, 2000)] * 4]
        target = Surv.from_arrays([1, 1, 1, 1, 0, 0, 0, 0], [.25, .25, 1, 1, 1, 1, 1, 1])
        result = fit_arm(arms.P2, train, train, target)
        for score in result["scores"]:
            self.assertAlmostEqual(score, 1 - exp(-(2 / 8 + 2 / 6)))
        self.assertEqual(result["model"]["repeat_fit"], "PASS_EXACT")
        self.assertEqual(result["model"]["convergence"], "PASS")

    def test_cox_convergence_warning_fails(self):
        from sklearn.exceptions import ConvergenceWarning
        from sksurv.linear_model import CoxPHSurvivalAnalysis
        from loe_bench.priorarms_survival import fit_once

        train = np.arange(14, dtype=float).reshape(2, 7)

        def no_convergence(*_):
            warnings.warn("fixture optimizer limit", ConvergenceWarning)

        with patch.object(CoxPHSurvivalAnalysis, "fit", no_convergence):
            with self.assertRaises(ConvergenceWarning):
                fit_once(arms.P2, train, train, None)

    def test_forest_exact_repeat_and_survival_not_generic_risk(self):
        from sksurv.ensemble import RandomSurvivalForest
        from sksurv.util import Surv
        from loe_bench.priorarms_survival import fit_arm

        train = [[i, 0, 1, 0, 0, 0, 1] for i in range(30)]
        target = Surv.from_arrays([i % 2 for i in range(30)], [.5, .75, 1, 1, 1, 1] * 5)
        with patch.object(RandomSurvivalForest, "predict", side_effect=AssertionError("generic RSF score")):
            result = fit_arm(arms.P1, train, train, target)
        self.assertEqual(result["model"]["fitted_trees"], 500)
        self.assertEqual(result["model"]["repeat_fit"], "PASS_EXACT")
        self.assertTrue(all(0 <= score <= 1 for score in result["scores"]))
