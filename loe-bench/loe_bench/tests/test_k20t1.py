from datetime import date
from math import nextafter
from types import SimpleNamespace
import unittest

from loe_bench import evidence_graph as graph, k20t1
from loe_bench.ob_history import EditionSource, OBHistory
from loe_bench.t2_features import AsOfBuilder


def evidence(blocked=False):
    snapshot = {"excl_exp": [date(2020, 1, 1)]} if blocked else {}
    return {"t": date(2010, 1, 1), "asof": SimpleNamespace(snapshot=snapshot, challenge=None)}


class K20T1Tests(unittest.TestCase):
    def test_m1_ties_are_never_split(self):
        p = [0.2, 0.2, 0.2, 0.4]
        point = k20t1.choose_operating_points("M1", p, ["CONTESTED"] * 4)[0]
        self.assertEqual(point["threshold"], 0.8)
        self.assertEqual(point["inner_answered"], 3)
        self.assertFalse(point["inner_within_tolerance"])

    def test_m3_unreachable_when_probabilities_are_at_midpoint(self):
        points = k20t1.choose_operating_points("M3", [0.5] * 5, ["OPEN"] * 5)
        self.assertTrue(all(point["inner_max_coverage"] == 0 for point in points))
        self.assertTrue(all(not point["inner_target_reachable"] for point in points))

    def test_m3_conflict_refers_on_the_boundary(self):
        rows = [evidence(blocked=True), evidence()]
        answered, conflicts = k20t1.apply_policy("M3", rows, [0.8, 0.8], 24, 0.8)
        self.assertEqual([item.action for item in answered], [graph.ABSTAIN, graph.PREDICT_ENTRY])
        self.assertEqual(conflicts, 1)
        answered, conflicts = k20t1.apply_policy("M3", rows, [0.8, 0.8], 24, nextafter(0.8, 1))
        self.assertEqual([item.action for item in answered], [graph.PREDICT_NO_ENTRY, graph.ABSTAIN])
        self.assertEqual(conflicts, 0)

    def test_enumeration_agrees_with_graph_at_all_boundaries(self):
        probabilities = [0, 0.2, 0.25, 0.3, nextafter(0.5, 0), 0.5, 0.6, 0.6, 0.9, 1]
        rows = [evidence(blocked=i % 3 == 0) for i in range(len(probabilities))]
        verdicts = ["BLOCKED" if i % 3 == 0 else "CONTESTED" for i in range(len(rows))]
        for hi, count in k20t1.coverage_options("M3", probabilities, verdicts):
            predictions, _ = k20t1.apply_policy("M3", rows, probabilities, 24, hi)
            self.assertEqual(count, sum(item.action != graph.ABSTAIN for item in predictions))

    def test_metrics_keep_referrals_out_of_class_error_denominator(self):
        rows = [evidence()] * 5
        predictions, conflicts = k20t1.apply_policy("M1", rows, [0.9, 0.1, 0.9, 0.45, 0.55], 24, 0.7)
        result = k20t1.policy_metrics(predictions, [0, 1, 1, 1, 0], 0.6, conflicts)
        self.assertEqual(result["class_wise"]["0"], {"rows": 2, "answered": 1, "errors": 1,
                                                    "referrals": 1, "error_rate": 1})
        self.assertEqual(result["class_wise"]["1"]["error_rate"], 0.5)
        self.assertTrue(result["within_tolerance"])
        self.assertFalse(result["aurc80_reachable"])

    def test_fresh_zip_precedes_available_annual_fallback(self):
        zip_date = date(2009, 12, 1)
        fda = EditionSource(zip_date, lambda: None, {"kind": "fda_zip"}, ({"date": "2009-12-02"},))
        annual = EditionSource(date(2009, 12, 31), lambda: None,
                               {"kind": "nber_annual", "edition_year": 2009}, ({"date": "2010-01-01"},))
        builder = k20t1.AnnualTrainingBuilder(AsOfBuilder(OBHistory([fda])), OBHistory([annual]))
        self.assertIs(builder.select_edition(date(2010, 1, 1))[0], fda)
        self.assertIs(builder.select_edition(date(2011, 1, 1))[0], annual)
        self.assertIsNone(builder.select_edition(date(2009, 12, 1))[0])
        self.assertEqual(k20t1.edition_features(annual, date(2010, 1, 1))["edition_staleness_days"], 366)


if __name__ == "__main__":
    unittest.main()
