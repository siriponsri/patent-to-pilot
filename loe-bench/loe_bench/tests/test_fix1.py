"""Hand-checkable regression fixtures for the FIX1 task card."""
import csv
import contextlib
import hashlib
import io
import itertools
import json
import math
import tempfile
import unittest
from datetime import date
from pathlib import Path

from loe_bench import dataset, metrics, trackA_freeze
from loe_bench.evidence_graph import decide
from loe_bench.kleene import Leaf
from loe_bench.voi import voi


def product(name, approved=None, route="ORAL", **fields):
    row = {"active_ingredients": [{"name": name}], "route": route, **fields}
    if approved:
        row["approval_date"] = approved
    return row


def original(approved, status="AP", **fields):
    return {"submission_type": "ORIG", "submission_status": status,
            "submission_status_date": approved, **fields}


def application(submissions, *products):
    return {"submissions": submissions, "products": list(products)}


def write_jsonl(root, filename, rows):
    (root / filename).write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class RawFixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.raw = Path(tmp.name)

    def build(self, ndas, andas):
        write_jsonl(self.raw, "df_nda.jsonl", ndas)
        write_jsonl(self.raw, "df_anda.jsonl", andas)
        return dataset.build_entities(self.raw)


class TestTemporalDataset(RawFixture):
    def test_future_invariance_of_features_cohort_and_labels(self):
        cutoff, data_end = date(2014, 1, 1), date(2015, 1, 1)
        early = original("20090101")
        nme = original("20090101", submission_class_code="TYPE 1")
        future = original("20160101", submission_class_code="TYPE 1",
                          review_priority="PRIORITY", submission_property_type=[{"code": "Orphan"}])
        oral = product("ALPHA", "20090101")
        beta = product("BETA", "20090101", route="TOPICAL")
        andas = [application([original("20141101")], product("ALPHA"))]
        before = self.build([application([nme], oral), application([early], beta)], andas)
        after = self.build([
            application([nme, future], oral, product("ALPHA", "20150102", route="INJECTABLE"),
                        product("VARIANT", "20160101")),
            application([early], beta),
            application([future], product("BETA", "20160101", route="ORAL")),
            application([future], product("GAMMA", "20160101", route="ORAL")),
        ], andas + [application([original("20150102")], product("BETA"))])
        for only_nme, expected in [(True, {"ALPHA": 1}), (False, {"ALPHA": 1, "BETA": 0})]:
            earlier = dataset.build_samples(before, [cutoff], 12, data_end, only_nme)
            extended = dataset.build_samples(after, [cutoff], 12, data_end, only_nme)
            self.assertEqual({row["key"]: row["y"] for row in earlier}, expected)
            self.assertEqual(extended, earlier)
        self.assertEqual(dataset.features_at(after["BETA"], cutoff)["nme"], 0)
        self.assertEqual(dataset.features_at(after["BETA"], date(2016, 1, 1))["nme"], 1)
        self.assertEqual(dataset.features_at(after["ALPHA"], cutoff)["oral"], 1)
        self.assertEqual(dataset.features_at(after["ALPHA"], date(2015, 1, 2))["injectable"], 1)

    def test_undated_products_and_orig_submissions_do_not_supply_flags(self):
        approved = original("20090101")
        undated = original(None, submission_class_code="TYPE 1", review_priority="PRIORITY",
                           submission_property_type=[{"code": "Orphan"}])
        entities = self.build([application([approved, undated], product("ALPHA"))], [])
        x = dataset.features_at(entities["ALPHA"], date(2014, 1, 1))
        self.assertEqual([x[k] for k in ("nme", "priority", "orphan", "oral", "injectable")],
                         [0, 0, 0, 0, 0])

    def test_complete_follow_up_for_both_classes_and_first_final_only(self):
        nme = original("20090101", submission_class_code="TYPE 1")
        ndas = [application([nme], product(name)) for name in ("A", "B", "C", "D")]
        andas = [
            application([original("20130101", status="TA"), original("20141001")], product("A")),
            application([original("20130101", status="TA")], product("B")),
            application([original("20150102")], product("C")),
            application([original("20150101"), original("20150103")], product("D")),
        ]
        entities = self.build(ndas, andas)
        self.assertIsNone(entities["B"].anda_first)
        cutoff = date(2014, 1, 1)
        boundary = date(2015, 1, 1)
        self.assertEqual(dataset.build_samples(entities, [cutoff], 12, date(2014, 12, 31)), [])
        rows = dataset.build_samples(entities, [cutoff], 12, boundary)
        self.assertEqual({r["key"]: r["y"] for r in rows}, {"A": 1, "B": 0, "C": 0, "D": 1})
        self.assertEqual(dataset.build_samples(entities, [boundary], 12, boundary), [])

    def test_exact_embargo_boundary_and_overlapping_bounds(self):
        train_last, test_first = date(2014, 1, 1), date(2017, 1, 1)
        keep = {"t": date(2013, 12, 31), "t_end": date(2016, 12, 31)}
        purge = {"t": train_last, "t_end": test_first}
        test = {"t": test_first, "t_end": date(2018, 1, 1)}
        self.assertEqual(dataset.time_split([keep, purge, test], train_last, test_first),
                         ([keep], [test], 1))
        for bad in (train_last, date(2013, 12, 31)):
            with self.assertRaises(ValueError):
                dataset.time_split([], train_last, bad)

    def test_three_way_embargo_boundaries_and_invalid_dates(self):
        train_last = date(2012, 1, 1)
        val_first, val_last, test_first = date(2013, 1, 1), date(2014, 1, 1), date(2015, 1, 1)
        tr = {"t": date(2011, 12, 31), "t_end": date(2012, 12, 31)}
        tr_drop = {"t": train_last, "t_end": val_first}
        va = {"t": val_first, "t_end": date(2014, 1, 1)}
        va_drop = {"t": val_last, "t_end": test_first}
        te = {"t": test_first, "t_end": date(2016, 1, 1)}
        rows = [tr, tr_drop, va, va_drop, te]
        self.assertEqual(dataset.time_split(rows, train_last, test_first,
                                          validation_first_cutoff=val_first,
                                          validation_last_cutoff=val_last),
                         ([tr], [va], [te], 2))
        for first, last in [(val_first, None), (None, val_last), (train_last, val_last),
                            (val_last, val_first), (val_first, test_first)]:
            with self.subTest(first=first, last=last), self.assertRaises(ValueError):
                dataset.time_split(rows, train_last, test_first,
                                   validation_first_cutoff=first, validation_last_cutoff=last)


class TestPolicyMetrics(unittest.TestCase):
    def test_explicit_ranking_and_policy_coverage(self):
        p, y, scores = [0.99, 0.1, 0.95], [1, 0, 1], [2, 4, 6]
        actions = ["PREDICT_ENTRY", "PREDICT_ENTRY", "ABSTAIN_REFER_TO_EVALUATOR"]
        curve = metrics.risk_coverage(p, y, scores=scores, actions=actions)
        self.assertEqual(curve, [(1 / 3, 1), (2 / 3, 1 / 2)])
        self.assertEqual(metrics.aurc(p, y, scores=scores, actions=actions), 0.5)
        self.assertEqual(metrics.aurc(p, y, scores=[4, 2, 6], actions=actions), 1 / 6)
        self.assertTrue(math.isnan(metrics.aurc(p, y, actions=[actions[-1]] * 3)))

    def test_expected_aurc_invariant_to_tie_permutations(self):
        p, y = [0.9] * 3, [1, 0, 0]
        for order in itertools.permutations(range(3)):
            self.assertAlmostEqual(metrics.aurc(p, [y[i] for i in order]), 2 / 3)
        self.assertAlmostEqual(metrics.aurc([0.9, 0.7, 0.6], [1, 0, 1], scores=[2, 1, 1]),
                               (0 + 1 / 4 + 1 / 3) / 3)

    def test_paired_cluster_draws_and_invalid_counts(self):
        def metric(p, y):
            return sum(p) / len(y) if 0 in y and 1 in y else float("nan")

        a, b = [0.5, 0.75, 0.875], [0.25, 0.5, 0.625]
        # For two groups and seed 0, 11 of the first 20 draws contain both groups.
        args = (metric, a, b, [0, 0, 1], ["large", "large", "small"])
        ci = metrics.paired_cluster_bootstrap_ci(*args, n_boot=20, seed=0)
        self.assertAlmostEqual(ci[0], 0.25)
        self.assertAlmostEqual(ci[1], 0.25)
        self.assertEqual(ci[2], 9)
        self.assertEqual(metrics.paired_cluster_bootstrap_ci(*args, n_boot=20, seed=0), ci)
        lo, hi, invalid = metrics.paired_cluster_bootstrap_ci(
            metric, a, b, [0, 0, 0], ["large", "large", "small"], n_boot=3)
        self.assertTrue(math.isnan(lo) and math.isnan(hi))
        self.assertEqual(invalid, 3)

    def test_ece_validates_inputs_and_returns_bin_counts(self):
        value, counts = metrics.ece([0, 0.25, 0.5, 1], [0, 1, 1, 1], bins=4)
        self.assertEqual(counts, (1, 1, 1, 1))
        self.assertAlmostEqual(value, (0.75 + 0.5) / 4)
        self.assertEqual(metrics.ece([0, 1], [0, 1], bins=4).bin_counts, (1, 0, 0, 1))
        self.assertEqual(metrics.ece([0.58], [1], bins=50).bin_counts[29], 1)
        for p, y, bins in [([], [], 4), ([-0.1], [0], 4), ([1.01], [1], 4),
                           ([math.nan], [1], 4), ([0.5, 0.2], [1], 4),
                           ([0.5], [2], 4), ([0.5], [1], 0)]:
            with self.subTest(p=p, y=y, bins=bins), self.assertRaises(ValueError):
                metrics.ece(p, y, bins)


class TestEvidencePolicy(unittest.TestCase):
    t = date(2026, 1, 1)

    def test_missing_evidence_is_unknown(self):
        for snapshot in ({}, {"excl_exp": [], "patent_exp": []}):
            result = decide(snapshot, self.t, 12, 0.5)
            self.assertEqual(result["verdict"], "CONTESTED")
            self.assertEqual(result["trace"]["L_excl"], "UNKNOWN")
            self.assertEqual(result["trace"]["L_pat"], "UNKNOWN")

    def test_blocked_conflict_refers_by_default_at_high_boundary(self):
        s = {"excl_exp": [date(2030, 1, 1)]}
        self.assertEqual(decide(s, self.t, 12, 0.749)["action"], "PREDICT_NO_ENTRY")
        for p in (0.75, 0.95):
            result = decide(s, self.t, 12, p)
            self.assertEqual(result["action"], "ABSTAIN_REFER_TO_EVALUATOR")
            self.assertTrue(result["conflict"])
            self.assertEqual(decide(s, self.t, 12, p, blocked_conflict_action="PREDICT_NO_ENTRY")
                             ["action"], "PREDICT_NO_ENTRY")

    def test_voi_reveal_rate_and_truth_prior_have_separate_roles(self):
        for rate in (0.3, 0.6, 1):
            for truth, entropy in [(0.5, 1), (0.25, 0.8112781244591328), (1, 0)]:
                result = voi(Leaf("item"), reveal_probabilities={"item": rate},
                             prior_truth_probability=truth)
                self.assertAlmostEqual(result, rate * entropy)
        self.assertEqual(voi(Leaf("item"), reveal_probabilities={},
                             prior_truth_probability=0.5), 0)
        snapshot = {"excl_exp": [self.t], "patent_exp": [date(2030, 1, 1)]}
        d = decide(snapshot, self.t, 12, 0.5, reveal_probabilities={"L_challenge": 0.6},
                   prior_truth_probability=0.25)
        self.assertAlmostEqual(d["next_evidence"]["voi_bits"], 0.6 * 0.8112781244591328)


class TestTrackAFreeze(RawFixture):
    t0 = date(2014, 1, 1)

    def setUp(self):
        super().setUp()
        self.out = self.raw / "predictions.csv"
        self.manifest = self.raw / "S0_INPUT_MANIFEST.json"
        nme = original("20100101", submission_class_code="TYPE 1")
        self.entities = self.build(
            [application([nme], product(name)) for name in ("A", "B", "C", "D")],
            [application([original("20150101")], product("A")),
             application([original("20140101")], product("B"))])
        write_jsonl(self.raw, "ob_nda.jsonl", [
            {"approval_date": approved, "products": [product(name), product("VARIANT", "20140102")],
             "patents": [{"expiration_date": "20160101"}]}
            for name, approved in [("A", "20100101"), ("B", "20100101"), ("C", "20140102")]
        ])

    def write_manifest(self, snapshot="2014-01-01", fetched=None, omit=None):
        paths = ["df_nda.jsonl", "df_anda.jsonl", "ob_nda.jsonl"]
        payload = {"t0": snapshot, "fetched_at_utc": (fetched or snapshot) + "T01:00:00+00:00",
                   "files": [{"raw_file": filename,
                              "sha256": hashlib.sha256((self.raw / filename).read_bytes()).hexdigest()}
                             for filename in paths if filename != omit]}
        self.manifest.write_text(json.dumps(payload), encoding="utf-8")

    def freeze(self, arms=None):
        return trackA_freeze.freeze_predictions(self.raw, self.manifest, self.out, self.t0,
                                                arms or {"B0": lambda train, rows, t, h: [0] * len(rows)})

    def test_snapshot_filters_by_cutoff_and_keeps_future_expiration(self):
        snapshots = dataset.snapshot_features(self.raw, self.t0, self.entities)
        self.assertEqual(set(snapshots), {"A"})
        self.assertEqual(snapshots["A"]["patent_exp"], [date(2016, 1, 1)])

    def test_freeze_refuses_newer_manifest_fetch_or_hash_mismatch(self):
        for snapshot, fetched, message in [("2014-01-02", None, "after t0"),
                                           ("2014-01-01", "2014-01-02", "after t0"),
                                           ("2014-01-01", None, "SHA-256 mismatch")]:
            with self.subTest(snapshot=snapshot, fetched=fetched, message=message):
                self.write_manifest(snapshot, fetched)
                if "mismatch" in message:
                    with (self.raw / "df_anda.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write("\n")
                with self.assertRaisesRegex(ValueError, message):
                    self.freeze()
                self.assertFalse(self.out.exists())

    def test_freeze_requires_all_used_files_to_be_manifested(self):
        self.write_manifest(omit="ob_nda.jsonl")
        with self.assertRaisesRegex(ValueError, "ob_nda.jsonl"):
            self.freeze()
        self.assertFalse(self.out.exists())

    def test_freeze_only_closed_windows_and_full_precision_per_arm(self):
        self.write_manifest()
        precision = 0.12345678901234567
        calls = []

        def predict(train, rows, t, h):
            self.assertTrue(train)
            self.assertEqual(max(r["t_end"] for r in train), t)
            self.assertEqual({r["key"] for r in train if r["y"]}, {"B"})
            self.assertEqual([r["key"] for r in rows], ["A"])
            self.assertNotIn("y", rows[0])
            calls.append(h)
            return [precision]

        n, digest = self.freeze({"M1": predict, "M3": lambda train, rows, t, h: [0.875]})
        with self.out.open(encoding="utf-8", newline="") as stream:
            read = csv.DictReader(stream)
            self.assertEqual(read.fieldnames, ["entity", "t0", "horizon_months", "M1", "M3"])
            rows = list(read)
        self.assertEqual(calls, [12, 24, 36])
        self.assertEqual(n, len(rows))
        self.assertEqual(digest, hashlib.sha256(self.out.read_bytes()).hexdigest())
        self.assertEqual([float(r["M1"]) for r in rows], [precision] * 3)

    def test_cli_freezes_only_explicit_baseline_arms(self):
        self.write_manifest()
        with contextlib.redirect_stdout(io.StringIO()):
            trackA_freeze.main(["--raw", str(self.raw), "--manifest", str(self.manifest),
                                "--out", str(self.out), "--t0", self.t0.isoformat(),
                                "--arm", "B3", "--arm", "B0"])
        with self.out.open(encoding="utf-8", newline="") as stream:
            read = csv.DictReader(stream)
            self.assertEqual(read.fieldnames, ["entity", "t0", "horizon_months", "B3", "B0"])
            rows = list(read)
        self.assertEqual([float(r["B3"]) for r in rows], [0, 1, 1])
        self.assertEqual([float(r["B0"]) for r in rows], [1 / 16, 1 / 12, 1 / 8])
