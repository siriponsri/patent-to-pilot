"""Hand-checkable C4 fixtures for counts, provenance and calendar math."""

import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from loe_bench import c4
from loe_bench.moiety import Registry


def product(ndc, *ingredients, start="20060101"):
    return {
        "active_ingredients": [{"name": name} for name in ingredients],
        "marketing_start_date": start,
        "packaging": [{"package_ndc": ndc}],
    }


class CrosswalkTests(unittest.TestCase):
    def test_package_segments_and_collisions(self):
        self.assertEqual(c4.package_ndc11("1234-5678-90"), "01234567890")
        self.assertEqual(c4.package_ndc11("12345-678-90"), "12345067890")
        self.assertEqual(c4.package_ndc11("12345-6789-0"), "12345678900")
        self.assertEqual(c4.package_ndc11("12345-6789-00"), "12345678900")
        self.assertIsNone(c4.package_ndc11("1234567890"))
        self.assertIsNone(c4.package_ndc11("12345-6789-A"))
        walk = c4.build_crosswalk([
            product("12345-6789-0", " Alpha ", "Beta"),
            product("12345-6789-00", "Beta", "ALPHA"),
            product("12345-6000-00", "A"),
            product("12345-6000-0", "B"),
            product("12345-6001-0", "A", ""),
            product("12345-6002-0", "A", start=""),
        ])
        self.assertEqual(walk, {
            "12345678900": c4.Package(frozenset({"ALPHA", "BETA"}), date(2006, 1, 1))
        })


class NationalCountsTests(unittest.TestCase):
    def read_rows(self, year, *rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sdud.csv"
            with path.open("w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.writer(stream)
                writer.writerow(c4.FIELDS)
                for state, ndc, kind, suppression, value in rows:
                    writer.writerow((state, ndc, year, 1, kind, suppression, value))
            return c4.read_sdud(path, year)[c4.quarter(year, 1)]

    def test_counts_only_use_national_disjoint_types_and_preserve_suppression(self):
        ndcs = ["00000111101", "00000111102", "00000111103", "00000111104", "00000111105"]
        walk = c4.build_crosswalk([
            product("00000-1111-01", "ALPHA", "BETA"),
            product("00000-1111-02", "BETA"),
            product("00000-1111-03", "GAMMA"),
            product("00000-1111-04", "DELTA"),
            product("00000-1111-05", "EPSILON"),
        ])
        rows = self.read_rows(2010,
                              ("XX", ndcs[0], "FFSU", "false", "00015"),
                              ("XX", ndcs[0], "MCOU", "false", "21"),
                              ("AK", ndcs[0], "FFSU", "false", 1234),
                              ("XX", ndcs[1], "FFSU", "true", 100),
                              ("XX", ndcs[1], "MCOU", "false", 20),
                              ("XX", ndcs[2], "FFSU", "false", 50),
                              ("AK", ndcs[2], "MCOU", "true", ""),
                              ("AK", ndcs[3], "FFSU", "false", 92),
                              ("XX", ndcs[4], "FFSU", "false", 0),
                              ("XX", ndcs[4], "MCOU", "false", 0))
        total = c4.aggregate(c4.quarter(2010, 1), rows, walk)
        self.assertEqual(total.counts, {"ALPHA": 36, "BETA": None, "GAMMA": None,
                                        "DELTA": None, "EPSILON": 0})
        self.assertEqual(total.issues["suppressed_national_rows"], 1)
        self.assertEqual(total.issues["missing_national_type"], 2)
        self.assertEqual(total.issues["state_only_package"], 1)
        self.assertTrue(total.frame_complete)

    def test_duplicate_conflicting_unmapped_and_pre_2010_types(self):
        rows = self.read_rows(2009,
                              ("XX", "00000111101", "FFSU", "false", 12),
                              ("XX", "00000111102", "FFSU", "false", 20),
                              ("XX", "00000111102", "FFSU", "false", 20),
                              ("XX", "00000111103", "FFSU", "false", 30),
                              ("XX", "00000111104", "FFSU", "false", 50),
                              ("XX", "00000111104", "MCOU", "false", 42))
        walk = c4.build_crosswalk([product("00000-1111-01", "A"),
                                    product("00000-1111-02", "B"),
                                    product("00000-1111-03", "C", start="20090401"),
                                    product("00000-1111-04", "D")])
        total = c4.aggregate(c4.quarter(2009, 1), rows, walk)
        self.assertEqual(total.counts, {"A": 12, "B": None, "D": None})
        self.assertEqual(total.issues["duplicate_national_key"], 1)
        self.assertEqual(total.issues["unresolved_packages"], 1)
        self.assertEqual(total.issues["unexpected_utilization_type"], 1)
        self.assertFalse(total.frame_complete)

    def test_unknown_counts_are_not_zeros(self):
        for flag, value in (("false", ""), ("", "12"), ("false", "-1"), ("false", "1.2")):
            self.assertEqual(c4.parse_count(flag, value), (None, "unknown_count"))
        self.assertEqual(c4.parse_count("false", "*"), (None, "suppressed"))


class PilotTests(unittest.TestCase):
    def test_tracked_lock_uses_git_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.json"
            path.write_bytes(b'{\r\n}\r\n')
            self.assertEqual(c4.lock_bytes(path), b'{\n}\n')

    def test_lag_and_quarterwise_nonnegative_drift(self):
        self.assertEqual(c4.forecast([10, 12, 14, 16, 18, 20, 22, 24], 2),
                         {"carry_forward": 96, "drift": 132})
        self.assertEqual(c4.forecast([8, 7, 6, 5, 4, 3, 2, 1], 0),
                         {"carry_forward": 4, "drift": 0})
        with self.assertRaisesRegex(ValueError, "eight consecutive"):
            c4.forecast([0] * 7 + [None], 2)

    def test_scores_are_paired_and_unknown_outcomes_are_excluded(self):
        origin, anchor = date(2016, 12, 31), c4.quarter(2016, 2)
        training = {q: self.series(A=10 + i, B=2, C=None)
                    for i, q in enumerate(range(anchor - 7, anchor + 1))}
        training[anchor + 1] = self.series(A=10_000, LATE_ONLY=99)
        outcomes = {c4.quarter(2017, q): self.series(A=20, C=2, OUTCOME_ONLY=99)
                    for q in range(1, 5)}
        ingredients, primary, diagnostic, exclusions = c4.score_origin(
            origin, anchor, training, outcomes
        )
        self.assertEqual(ingredients, {"A", "B", "C"})
        self.assertEqual(primary, [("A", -12, 6.0)])
        self.assertEqual(primary, diagnostic)
        self.assertEqual(exclusions, {"incomplete_outcome": 1, "incomplete_history": 1})
        score = c4.metrics(primary)
        self.assertEqual(score["paired_mae_difference_drift_minus_carry"], -6.0)
        self.assertEqual(score["carry_forward_bias"], -12)
        self.assertEqual(score["drift_bias"], 6)
        outcomes[c4.quarter(2017, 1)].issues["unresolved_packages"] = 1
        _, primary, diagnostic, _ = c4.score_origin(origin, anchor, training, outcomes)
        self.assertEqual(c4.metrics(primary)["status"], "NOT_ESTIMABLE")
        self.assertEqual(len(diagnostic), 1)
        del training[anchor - 3]
        self.assertFalse(c4.score_origin(origin, anchor, training, outcomes)[2])

    def test_vintage_evidence_must_bind_bytes_before_origin(self):
        origin = date(2016, 12, 31)
        digest = "a" * 64
        evidence = {"method": "archive_payload_replay", "url": "https://example.test/data.csv",
                    "available_utc": "2016-12-30T23:59:59Z", "sha256": digest}
        self.assertTrue(c4.proven_before({"sha256": digest, "availability": evidence}, origin))
        self.assertFalse(c4.proven_before({"sha256": "b" * 64, "availability": evidence}, origin))
        evidence["method"] = "catalog"
        self.assertFalse(c4.proven_before({"sha256": digest, "availability": evidence}, origin))
        evidence.update(method="archive_payload_replay", available_utc="2016-12-31T00:00:00Z")
        self.assertFalse(c4.proven_before({"sha256": digest, "availability": evidence}, origin))

    def test_reserved_origin_fails_before_loading_inputs(self):
        for value in ("2017-01-01", "2017-03-31"):
            with self.assertRaisesRegex(ValueError, "must precede"):
                c4.run_pilot({}, {"origins": [{"origin": value}]}, None, Registry())
        with self.assertRaisesRegex(ValueError, "must precede"):
            c4.score_origin(date(2017, 3, 31), 0, None, None)

    @staticmethod
    def series(**counts):
        value = c4.IngredientQuarter(counts)
        value.issues["national_rows"] = 2
        return value
