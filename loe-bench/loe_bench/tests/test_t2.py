import math
import unittest
from datetime import date
from unittest.mock import patch

from loe_bench import evidence_graph as graph, seal, t2
from loe_bench.dataset import Entity, features_at
from loe_bench.ob_history import Edition, EditionSource, OBHistory
from loe_bench.t2_features import AsOfBuilder, OB_FEATURES, edition_coverage


T = date(2014, 1, 1)
ED = date(2013, 7, 1)


def product(number, approved=date(2003, 1, 1)):
    return dict(appl_no="000001", product_no=number, ingredient_key="DRUG", appl_type="N", approval_date=approved)


def patent(product_no, patent_no, expiry, submission=None):
    return dict(appl_no="000001", product_no=product_no, patent_no=patent_no, expiry=expiry, submission_date=submission)


def exclusivity(product_no, code, expiry):
    return dict(appl_no="000001", product_no=product_no, code=code, expiry=expiry)


def history(products, patents, exclusivities, later=()):
    source = EditionSource(ED, lambda: Edition(ED, products, patents, exclusivities),
                           availability=({"date": ED.isoformat()},))
    return OBHistory([source, *later])


def manifest_entry(when, timestamp, token):
    return dict(edition_date=when, wayback_ts=timestamp, file=f"{token}.zip", sha256=token * 64,
                source_url="https://www.fda.gov/ob.zip", wayback_url="https://web.archive.org/ob.zip")


def features(archive, key="DRUG"):
    entity = Entity(key, nda_first=date(2003, 1, 1))
    return AsOfBuilder(archive).build(key, T, 24, features_at(entity, T))


class AsOfTests(unittest.TestCase):
    def test_fresh_boundary_features_and_verdict(self):
        inputs = history([product("001"), product("002")],
                         [patent("001", "A", date(2015, 1, 1), date(2012, 1, 1)),
                          patent("002", "A", date(2015, 1, 1))],
                         [exclusivity("001", "NCE", date(2015, 1, 1)),
                          exclusivity("001", "I-1", date(2013, 1, 1))])
        row = features(inputs)
        self.assertEqual(row.edition_status, "FRESH")
        self.assertEqual(row.verdict, "OPEN")
        self.assertAlmostEqual(row.x["age_years"], 11, delta=0.01)
        self.assertAlmostEqual(row.x["nce_remaining_years"], 1, delta=0.01)
        self.assertEqual(row.x["other_exclusivity_remaining_years"], 0)
        self.assertEqual(row.x["listed_patent_count"], 1)
        self.assertAlmostEqual(row.x["years_to_last_patent_expiry"], 1, delta=0.01)
        self.assertAlmostEqual(row.x["years_since_earliest_patent_submission"], 2, delta=0.01)
        self.assertTrue(all(row.x[f"{f}_missing"] == 0 for f in OB_FEATURES))

    def test_later_edition_and_later_dated_records_leave_row_unchanged(self):
        products = [product("001")]
        patents = [patent("001", "A", date(2015, 1, 1))]
        exclusivities = [exclusivity("001", "NCE", date(2015, 1, 1))]
        base = features(history(products, patents, exclusivities))
        later = date(2014, 1, 2)

        def refuse_load():
            self.fail("a later edition was loaded")

        extended = history(products + [product("002", later)],
                           patents + [patent("001", "B", date(2030, 1, 1), later),
                                      patent("002", "C", date(2030, 1, 1))],
                           exclusivities + [exclusivity("002", "NCE", date(2030, 1, 1))],
                           [EditionSource(later, refuse_load, availability=({"date": T.isoformat()},))])
        self.assertEqual(features(extended), base)

    def test_stale_missing_and_unlisted_are_unknown(self):
        stale = OBHistory([EditionSource(date(2013, 6, 30), lambda: self.fail("stale edition was loaded"),
                                         availability=({"date": "2013-07-01"},))])
        for archive, status in ((stale, "STALE"), (OBHistory([]), "MISSING"),
                                (history([], [], []), "NOT_LISTED")):
            with self.subTest(status=status):
                row = features(archive)
                self.assertEqual(row.edition_status, status)
                self.assertEqual(row.verdict, "CONTESTED")
                self.assertTrue(all(row.x[f"{f}_missing"] == 1 for f in OB_FEATURES))
        self.assertEqual(edition_coverage(stale, T)["freshness_floor"], ED.isoformat())
        self.assertIsNone(edition_coverage(stale, T)["chosen_edition"])

    def test_dated_but_captured_after_cutoff_is_never_loaded(self):
        timely = manifest_entry("2013-07-01", "20140101235959", "a")
        late = manifest_entry("2013-12-31", "20140102000000", "b")
        archive = OBHistory.from_records({"editions": [late, timely]}, "")
        with patch("loe_bench.ob_history.load_edition", return_value=Edition(ED, [product("001")], [], [])) as load:
            self.assertEqual(features(archive).edition_status, "FRESH")
            load.assert_called_once_with("a.zip", ED)
        coverage = edition_coverage(archive, T)
        self.assertEqual(coverage["chosen_edition"], ED.isoformat())
        self.assertEqual(coverage["availability_proof"]["wayback_ts"], timely["wayback_ts"])
        late_only = OBHistory.from_records({"editions": [late]}, "")
        with patch("loe_bench.ob_history.load_edition", side_effect=AssertionError):
            row = features(late_only)
        self.assertEqual(row.edition_status, "MISSING")
        self.assertEqual(row.verdict, "CONTESTED")
        self.assertTrue(all(row.x[f"{f}_missing"] == 1 for f in OB_FEATURES))

    def test_fda_publication_requires_exact_zip_link_and_timely_date(self):
        entry = manifest_entry("2013-12-30", "20140102000000", "a")
        record = dict(source_url="https://www.fda.gov/edition", html_sha256="c" * 64, locator="Versioned release")
        for sha, published, expected in ((None, "2013-12-31", "MISSING"),
                                         (entry["sha256"], "2014-01-02", "MISSING"),
                                         (entry["sha256"], "2014-01-01", "FRESH")):
            with self.subTest(sha=sha, published=published):
                records = {"editions": [entry], "e2b": {"fda_publication_records": [
                    dict(record, edition_sha256=sha, publication_date=published)]}}
                coverage = edition_coverage(OBHistory.from_records(records), T)
                self.assertEqual(coverage["status"], expected)
                if expected == "FRESH":
                    self.assertEqual(coverage["availability_proof"]["kind"], "fda_publication")
                    self.assertEqual(coverage["availability_proof"]["locator"], record["locator"])

    def test_additional_capture_uses_exact_hash_even_with_same_date_editions(self):
        timely = manifest_entry("2013-12-30", "20140103000000", "a")
        dubious = manifest_entry("2013-12-30", "20140105000000", "b")
        capture = {"wayback_ts": "20131231000000", "wayback_url": "https://web.archive.org/earlier"}
        archive = OBHistory.from_records({"editions": [timely, dubious], "e2b": {
            "additional_captures": {timely["sha256"]: [capture]}}}, "")
        coverage = edition_coverage(archive, T)
        self.assertEqual(coverage["availability_proof"]["wayback_ts"], capture["wayback_ts"])
        self.assertEqual(coverage["source"]["sha256"], timely["sha256"])
        with patch("loe_bench.ob_history.load_edition", return_value=Edition(ED, [], [], [])) as load:
            archive.edition_asof(T)
            features(archive)
            self.assertEqual([call.args[0] for call in load.call_args_list], ["b.zip", "a.zip"])

    def test_no_record_and_incomplete_expiry_have_distinct_missingness(self):
        empty = features(history([product("001")], [], []))
        incomplete = features(history([product("001")], [patent("001", "A", None)],
                                      [exclusivity("001", "NCE", None)]))
        self.assertEqual(empty.x["listed_patent_count"], 0)
        self.assertEqual(empty.x["listed_patent_count_missing"], 0)
        self.assertEqual(empty.x["nce_remaining_years_missing"], 0)
        self.assertEqual(incomplete.x["listed_patent_count"], 1)
        self.assertEqual(incomplete.x["years_to_last_patent_expiry_missing"], 1)
        self.assertEqual(incomplete.x["nce_remaining_years_missing"], 1)
        self.assertEqual(incomplete.verdict, "CONTESTED")

    def test_exclusivity_beyond_horizon_blocks(self):
        row = features(history([product("001")], [], [exclusivity("001", "NCE", date(2016, 1, 2))]))
        self.assertEqual(row.verdict, "BLOCKED")


class DevelopmentTests(unittest.TestCase):
    def test_strict_splits_maximize_validation(self):
        for horizon, train, validation in ((12, [2010], [2012, 2013, 2014, 2015]),
                                           (24, [2010], [2013, 2014]), (36, [], [])):
            left, right = t2.development_split(horizon)
            self.assertEqual([d.year for d in left], train)
            self.assertEqual([d.year for d in right], validation)

    def test_aurc_clips_partial_interval_and_requires_coverage(self):
        predictions = [t2.Prediction(p, graph.PREDICT_ENTRY) for p in (0.99, 0.9, 0.8)]
        labels = [1, 0, 0]
        self.assertAlmostEqual(t2._aurc80(predictions, labels), ((1 / 3) * 0.5 + (0.8 - 2 / 3) * (2 / 3)) / 0.8)
        predictions[-1] = t2.Prediction(0.5, graph.ABSTAIN)
        self.assertTrue(math.isnan(t2._aurc80(predictions, labels)))

    def test_evaluation_rejects_protected_before_fitting(self):
        with patch.object(type(seal.LOCK_PATH), "read_text", side_effect=AssertionError), patch.object(
            t2, "Logistic", side_effect=AssertionError
        ), self.assertRaises(seal.TestSealError):
            t2.evaluate([], [{"t": seal.TEST_FIRST}], 24)

    def test_cross_calibration_never_uses_held_drug_labels(self):
        keys = [str(i) for i in range(20)]
        held_fold = t2._fold(keys[0])
        asof = features(OBHistory([]))
        rows = [{"key": key, "y": i % 2, "asof": asof} for i, key in enumerate(keys)]
        probabilities = [0.05 + i / 24 for i in range(len(rows))]
        before = t2._cross_calibrate(rows, probabilities, probabilities)
        for row in rows:
            if t2._fold(row["key"]) == held_fold:
                row["y"] = 1 - row["y"]
        after = t2._cross_calibrate(rows, probabilities, probabilities)
        for arm in before:
            for i, key in enumerate(keys):
                if t2._fold(key) == held_fold:
                    self.assertEqual(before[arm][i], after[arm][i])

    def test_verdict_actions_and_coverage_gate_use_same_validation_rows(self):
        open_row = features(history([product("001")], [patent("001", "A", date(2015, 1, 1))],
                                    [exclusivity("001", "NCE", date(2015, 1, 1))]))
        blocked_row = features(history([product("001")], [], [exclusivity("001", "NCE", date(2020, 1, 1))]))
        contested_row = features(OBHistory([]))
        train = [{"t": date(2010, 1, 1), "x": contested_row.x, "asof": contested_row, "y": 0}]
        validation = [{"key": str(i), "t": T, "x": row.x, "asof": row, "y": i % 2}
                      for i, row in enumerate((open_row, blocked_row, contested_row))]
        probabilities = {"M1": [0.1, 0.2, 0.4], "M2": [0.1, 0.2, 0.4], "M3": [0.1, 0.8, 0.1]}
        with patch.object(t2, "_cross_calibrate", return_value=probabilities), patch.object(
            t2, "paired_cluster_bootstrap_ci", side_effect=AssertionError
        ), patch.object(t2, "_inputs", wraps=t2._inputs) as inputs:
            result = t2.evaluate(train, validation, 24)
        for arm in ("M1", "M3"):
            self.assertEqual(result["tuning"][arm]["configurations_tried"], 3)
            self.assertEqual(result["tuning"][arm]["selected_l2"], 1.0)
            self.assertEqual([item["l2"] for item in result["tuning"][arm]["candidates"]], list(t2.L2_GRID))
        # Both arms see the same TRAIN-derived age signal, despite a positive validation row.
        for call in inputs.call_args_list:
            rows, age_probabilities, _ = call.args
            self.assertEqual(age_probabilities, [0.0] * len(rows))
        self.assertEqual(result["validation_verdicts"], {"OPEN": 1, "BLOCKED": 1, "CONTESTED": 1})
        self.assertEqual(result["arms"]["M3"]["coverage"], 2 / 3)
        self.assertEqual(result["arms"]["M3"]["by_verdict"]["BLOCKED"]["rows"], 1)
        self.assertAlmostEqual(result["arms"]["M3"]["by_verdict"]["BLOCKED"]["brier"], 0.04)
        self.assertEqual(result["open_actions"]["m3_predict_no_entry"], 1)
        self.assertEqual(result["open_actions"]["package_ensemble_predict_no_entry_on_same_open_rows"], 1)
        self.assertEqual(result["paired_aurc80"]["M3_minus_B1"]["status"], "unevaluable")
