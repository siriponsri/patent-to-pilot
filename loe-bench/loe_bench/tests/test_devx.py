import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from loe_bench import devx, evidence_graph as graph, t2
from loe_bench.kleene import T3
from loe_bench.ob_history import parse_products
from loe_bench.seal import TEST_FIRST, TestSealError


class DevxTechniques(unittest.TestCase):
    def test_k07_strengths_preserve_units_forms_and_combination_order(self):
        products = parse_products(
            "Appl_No~Product_No~Appl_Type~DF;Route~Strength~Approval_Date\n"
            "1~1~N~TABLET;ORAL~5.00 mg;10 MG~Jan 01, 2010\n"
            "1~2~N~tablet ; oral~5MG; 10MG~Jan 01, 2010\n"
            "1~3~N~TABLET;ORAL~10MG;5MG~Jan 01, 2010\n"
            "1~4~N~SOLUTION;ORAL~5MG;10MG~Jan 01, 2010\n"
            "1~5~N~TABLET;ORAL~5G;10MG~Approved Prior to Jan 1, 1982\n"
            "1~6~N~TABLET;ORAL~NA~Jan 01, 2010\n"
            "1~7~N~INJECTABLE;INTRAVENOUS~5MG~Jan 02, 2010\n"
        )
        self.assertEqual(devx.presentation_breadth(products, date(2010, 1, 1)),
                         dict(strength_count=4, form_route_count=2, strength_missing=1,
                              form_route_missing=0))

    def test_k07_conflicting_and_undated_products_flag_unknown(self):
        products = parse_products(
            "Appl_No~Product_No~Appl_Type~DF;Route~Strength~Approval_Date\n"
            "1~1~N~TABLET;ORAL~.50 MG~Jan 01, 2010\n"
            "1~1~N~TABLET;ORAL~.60 MG~Jan 01, 2010\n"
            "1~2~N~TABLET;ORAL~.60 MG~\n"
        )
        empty = dict(strength_count=0, form_route_count=0, strength_missing=1, form_route_missing=1)
        self.assertEqual(devx.presentation_breadth(products, date(2010, 1, 1)), empty)
        self.assertEqual(devx.presentation_breadth([], date(2010, 1, 1)), empty)

    def test_k09_at_risk_intervals_and_censoring(self):
        start = date(2010, 1, 1)
        year_one, year_two = date(2011, 1, 1), date(2012, 1, 1)
        early_censor = date(2011, 6, 1)
        self.assertEqual(list(devx.annual_targets(start, year_two, year_one)), [(0, 1)])
        self.assertEqual(list(devx.annual_targets(start, year_two, year_two)), [(0, 0), (1, 1)])
        self.assertEqual(list(devx.annual_targets(start, early_censor, None)), [(0, 0)])
        self.assertEqual(list(devx.annual_targets(start, early_censor, early_censor)), [(0, 0), (1, 1)])
        self.assertEqual(list(devx.annual_targets(start, date(2010, 12, 31), year_one)), [])
        self.assertAlmostEqual(devx.cumulative_hazard(0.2, 0.25), 0.4)

    def test_k10_beta_is_monotone_and_preserves_single_class_fallback(self):
        grid = [0, 0.1, 0.5, 0.8, 1]
        values = devx.beta_calibration([(0.01, 0), (0.25, 0), (0.35, 1), (0.65, 1)], grid)
        self.assertEqual(values, sorted(values))
        self.assertTrue(all(0 <= p <= 1 for p in values))
        self.assertGreater(values[-1], values[0])
        self.assertEqual(devx.beta_calibration([(0.25, 0)], grid), grid)

    def test_k08_ranks_emitted_action_error_and_skips_referrals(self):
        wrong = t2.Prediction(0.9, graph.PREDICT_NO_ENTRY)
        right = t2.Prediction(0.1, graph.PREDICT_NO_ENTRY)
        abstain = t2.Prediction(0.5, graph.ABSTAIN)
        self.assertAlmostEqual(devx.selector_input(wrong, 0.1)["x"]["confidence"], 0.1)
        self.assertAlmostEqual(devx.selector_input(wrong, 0.1)["x"]["age_disagreement"], 0.8)
        training = [dict(devx.selector_input(pred, 0.1), y=error)
                    for pred, error in zip((wrong, right), (1, 0), strict=True)]
        predictions = [wrong, right, abstain]
        devx.select_errors(training, predictions, [0.1] * 3, [0, 1, 2])
        self.assertLess(predictions[0].score, predictions[1].score)
        self.assertEqual([p.action for p in predictions], [wrong.action, right.action, abstain.action])
        self.assertEqual([p.probability for p in predictions], [0.9, 0.1, 0.5])
        self.assertIs(predictions[2], abstain)

    def test_k08_nested_selector_does_not_use_outer_drug_labels(self):
        key_by_fold = {}
        for i in range(100):
            key_by_fold.setdefault(t2._fold(str(i)), str(i))
        keys = [key_by_fold[i] for i in range(3)]
        train = [{"key": key, "x": {"age_years": 1}, "y": y}
                 for key in keys for y in (0, 1)]
        rows = [{"key": key, "x": {"age_years": 1}, "y": y, "t": date(2013, 1, 1),
                 "asof": SimpleNamespace(snapshot={}, challenge=None)}
                for key in keys for y in (0, 1)]
        observed = date(2012, 12, 31)

        def run():
            predictions = {arm: [t2.Prediction(0.1, graph.PREDICT_NO_ENTRY)] * len(rows) for arm in devx.ARMS}

            def raw(subset, validation, *args):
                self.assertEqual(len({r["key"] for r in subset}), 1)
                return {arm: [0.1] * len(validation) for arm in devx.ARMS}, [0.2] * len(validation)

            # These calibrated fixture scores answer all inner rows. The
            # calibration fixture checks each fit sees only the remaining fold.
            def calibration(raw, validation, fit, held, beta):
                self.assertEqual(len({validation[i]["key"] for i in fit}), 1)
                self.assertTrue({validation[i]["key"] for i in fit}.isdisjoint(
                    validation[i]["key"] for i in held))
                return [0.1] * len(held)

            with patch.object(devx, "raw_predictions", side_effect=raw), patch.object(
                    devx, "calibrate", side_effect=calibration):
                diagnostics = devx.nested_selector(predictions, train, rows, 12, ("K08",), observed)
            self.assertTrue(all(not info["fallback"] for info in diagnostics))
            return {arm: predictions[arm][0].score for arm in devx.ARMS}

        original = run()
        for row in (*train, *rows):
            if row["key"] == keys[0]:
                row["y"] = 1 - row["y"]
        self.assertEqual(run(), original)

    def test_k06_graph_checks_joint_completions_and_keeps_actions(self):
        inputs = {"L_excl": T3.FALSE, "L_pat": T3.UNKNOWN, "L_challenge": T3.UNKNOWN}
        item = t2.Prediction(0.2, graph.PREDICT_NO_ENTRY)
        self.assertIs(devx.discounted(item, inputs, "M3"), item)
        self.assertAlmostEqual(devx.discounted(item, inputs, "M1").score, 0.75)
        inputs["L_excl"] = T3.UNKNOWN
        modified = devx.discounted(item, inputs, "M3")
        self.assertAlmostEqual(modified.score, 0.75)
        self.assertEqual((modified.probability, modified.action), (item.probability, item.action))
        referral = t2.Prediction(0.5, graph.ABSTAIN)
        self.assertIs(devx.discounted(referral, inputs, "M3"), referral)

    def test_protected_cutoff_is_refused_before_fitting(self):
        with self.assertRaises(TestSealError):
            devx.predict([], [{"t": TEST_FIRST}], 12, ())
