"""Network-free checks of the public Track A scorer."""

from contextlib import redirect_stdout
from datetime import date
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import numpy as np

from loe_bench import tracka_outcomes, tracka_statistics
from loe_bench.score_release import main, release_directory, score
from loe_bench.tracka_release import (
    ARMS, C9, CORE, FREEZE, IDENTITY, LLM, MANIFEST, PRIOR, ROSTER, SCORER, T0, TRACKA_FREEZE_SCHEMA, VERSION,
    digest, dump, load, read_release,
)

H12, H24 = date(2027, 11, 27), date(2028, 11, 27)
KEYS = [f"DRUG {i:02}" for i in range(20)]
FDA_URL = "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip"
OB_URL = "https://download.open.fda.gov/drug/orangebook/drug-orangebook-0001-of-0001.json.zip"


def jsonl(path, rows):
    path.write_bytes("".join(json.dumps(row) + "\n" for row in rows).encode())


def synthetic_release(folder, *, diagnostic_fields=None):
    folder.mkdir()
    dictionary = {
        arm: {"status": "INCLUDED", "files": {
            str(h): f"{arm.lower()}_{h}m.jsonl" if arm in LLM + C9 else
            f"{'core' if arm in CORE else 'prior'}_{h}m.jsonl" for h in ((24,) if arm in C9 else (12, 24))
        }} for arm in CORE + PRIOR + LLM + C9
    }
    all_rows = []
    for h in (12, 24):
        roster = [{"key": key, "t0": T0.isoformat(), "horizon_months": h} for key in KEYS]
        all_rows.extend(roster)
        graph = [1, .9, .8, .8, .6, .6, .6, .6, .6, .6, .8, .5] + [.1] * 8
        backwards = [.1] * 12 + [.9] * 8
        scores = {"B1": backwards, "M1": backwards, "M3": graph, "B3": [1] * 20}
        for group in (CORE, PRIOR):
            rows = [{**row, "arms": {arm: {"native": scores.get(arm, graph)[i], "calibrated": .4,
                                           **(diagnostic_fields or {})} for arm in group}}
                    for i, row in enumerate(roster)]
            jsonl(folder / dictionary[group[0]]["files"][str(h)], rows)
        for arm in LLM + (C9 if h == 24 else ()):
            rows = [{**row, "valid": i != 0, "p_entry": graph[i] if i else None}
                    for i, row in enumerate(roster)]
            jsonl(folder / dictionary[arm]["files"][str(h)], rows)
    jsonl(folder / ROSTER, all_rows)
    frozen = {path.name: digest(path) for path in folder.iterdir()}
    dump(folder / FREEZE, {"files_sha256": frozen})
    dump(folder / ARMS, dictionary)
    dump(folder / SCORER, {"version": VERSION, "python": "3.12.10", "numpy": "2.5.4", "source_files_sha256": {}})
    dump(folder / IDENTITY, {"roster_nda_ids": {key: [f"NDA{i:06d}"] for i, key in enumerate(KEYS)},
                             "fix2c_aliases": {}, "registry_aliases": {}, "registry_targets": {},
                             "s0_final_anda_apps": ["ANDA000022"]})
    dump(folder / MANIFEST, {"schema": 1, "freeze": "frozen", "analysis": "replication", "t0": T0.isoformat(),
                             "freeze_tag": "loe-test-fixture", "osf_timestamp": "2026-12-01T00:00:00Z",
                             "osf_manifest_sha256": digest(folder / FREEZE),
                             "frozen_files": {name: name for name in frozen},
                             "files_sha256": {path.name: digest(path) for path in folder.iterdir()}})
    return read_release(folder)


def approval(i, day, status="AP", submission_type="ORIG", app=None, products=True):
    return {"application_number": app or f"ANDA{i+1:06d}",
            "submissions": [{"submission_type": submission_type, "submission_status": status,
                             "submission_status_date": day}],
            "products": [{"product_number": "001", "active_ingredients": [{"name": KEYS[i % len(KEYS)]}]}]
            if products else []}


def zip_json(value, member):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(member, json.dumps(value))
    return buffer.getvalue()


def fake_fda(version, *, embedded=None, extra=()):
    records = [approval(i, "20271127" if i == 9 else "20270601") for i in range(10)]
    records += [approval(10, "20280203"), approval(11, "20281127"),
                approval(12, "20271115", "TA"), approval(13, "20271115", submission_type="SUPPL"),
                approval(14, "20271115", app="NDA000015"), approval(15, "20281128"),
                approval(16, None, app="ANDA000022"), *extra]
    n = len(records)
    index = {"results": {"drug": {"drugsfda": {"export_date": version.isoformat(), "total_records": n,
                                              "partitions": [{"file": FDA_URL, "records": n}]}}}}
    asset = {"meta": {"last_updated": (embedded or version).isoformat(), "results": {"skip": 0, "total": n}},
             "results": records}
    return {tracka_outcomes.INDEX_URL: json.dumps(index).encode(), FDA_URL: zip_json(asset, "drugsfda.json")}


class ScoreReleaseTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.release = synthetic_release(self.root / "release")
        network = patch.object(tracka_outcomes, "urlopen", side_effect=AssertionError("Unexpected network"))
        network.start()
        self.addCleanup(network.stop)

    def readout(self, horizon, date_now, data, out=None, **kwargs):
        with patch.object(tracka_outcomes, "fetch_bytes", side_effect=lambda url, *_: data[url]) as fetch:
            status, folder = score(self.release, horizon, out or self.root / "out", today=date_now, **kwargs)
        return status, folder, load(folder / "results.json"), fetch

    def test_known_answers_sequence_and_revision(self):
        status, first, year1, _ = self.readout(12, H12, fake_fda(H12))
        self.assertEqual(status, "SCORED")
        self.assertEqual(year1["hypotheses"]["H3"]["decision"], "DESCRIPTIVE_PENDING")
        panel = year1["panels"]["12"]
        self.assertEqual((panel["event_rows"], panel["drugs"], panel["slots_per_arm"]), (10, 20, 4))
        self.assertAlmostEqual(panel["arms"]["M3"]["recall"]["estimate"], 1 / 3)
        self.assertEqual(panel["arms"]["M3"]["boundary_tie_rows"], 3)
        self.assertEqual(panel["arms"]["B1"]["recall"]["estimate"], 0)
        self.assertAlmostEqual(panel["arms"]["B3"]["recall"]["estimate"], .2)
        self.assertEqual(panel["arms"]["B3"]["roc_auc"], .5)
        self.assertEqual(panel["arms"]["B3"]["c_index"]["comparable_pairs"], 99)
        self.assertEqual(panel["arms"]["B3"]["c_index"]["estimate"], .5)
        self.assertEqual(panel["arms"]["M3"]["accuracy"], .5)
        self.assertEqual(panel["arms"]["M3"]["fn"], 10)
        self.assertIn("brier", panel["arms"][PRIOR[0]])
        self.assertIn("hard_rule_brier", panel["arms"]["B3"])
        self.assertIn("grouped_average_precision", panel["contrasts"]["L1e-L1"])
        with np.load(first / "bootstrap-draws.npz") as draws:
            self.assertEqual(len(draws["12m:M3-B1:recall"]), 2000)
            self.assertGreater(float(np.quantile(draws["12m:M3-B1:recall"], .025, method="linear")), 0)

        status, _, year2, _ = self.readout(24, H24, fake_fda(H24))
        self.assertEqual(status, "SCORED")
        self.assertEqual(year2["h3_input"]["results_sha256"], digest(first / "results.json"))
        self.assertEqual([year2["hypotheses"][h]["decision"] for h in ("H1", "H2", "H3")], ["PASS"] * 3)
        self.assertEqual(year2["panels"]["24"]["event_rows"], 12)
        self.assertEqual(year2["panels"]["24"]["contrasts"]["C9-GRPO-C9-SFT"]["raw_brier"]["estimate"], 0)
        first_hash = digest(first / "results.json")
        status, later, revised, _ = self.readout(12, H24, fake_fda(H24, extra=(approval(16, "20271126"),)))
        self.assertEqual((status, revised["result_role"], revised["first_scored_run"]),
                         ("SCORED", "revision", "run-0001"))
        self.assertEqual(revised["panels"]["12"]["event_rows"], 11)
        self.assertEqual(revised["first_formal_readout"]["hypotheses"]["H3"]["decision"], "PASS")
        self.assertNotEqual(later, first)
        self.assertEqual(digest(first / "results.json"), first_hash)

        status, _, replayed, fetch = self.readout(12, H24, {}, out=self.root / "replay", snapshot=first / "sources")
        fetch.assert_not_called()
        self.assertEqual(status, "SCORED")
        self.assertEqual(replayed["panels"], year1["panels"])

    def test_pending_before_maturity_and_pending_release(self):
        for today in (T0, H12):
            if today == H12:
                self.release.manifest["freeze"] = "pending"
            status, _, report, fetch = self.readout(12, today, {})
            self.assertEqual(status, "PENDING")
            self.assertTrue(report["missing"])
            fetch.assert_not_called()

    def test_partial_coverage_blocks_scoring(self):
        status, folder, report, fetch = self.readout(12, H12, fake_fda(date(2027, 11, 26)))
        self.assertEqual(status, "BLOCKED_SOURCE")
        self.assertIn("coverage through 2027-11-27", report["missing"][0])
        self.assertFalse((folder / "bootstrap-draws.npz").exists())
        self.assertEqual(fetch.call_count, 1)
        status, _, report, _ = self.readout(12, H12, fake_fda(H12, embedded=date(2027, 11, 26)))
        self.assertEqual(status, "BLOCKED_SOURCE")
        self.assertIn("partition date", report["missing"][0])

    def test_ambiguous_approval_requires_orange_book(self):
        data = fake_fda(H12, extra=(approval(16, "20271126", products=False),))
        status, _, report, _ = self.readout(12, H12, data)
        self.assertEqual(status, "BLOCKED_SOURCE")
        self.assertTrue(any("Orange Book" in gap for gap in report["missing"]))
        index = json.loads(data[tracka_outcomes.INDEX_URL])
        index["results"]["drug"]["orangebook"] = {"export_date": H12.isoformat(), "total_records": 1,
                                                   "partitions": [{"file": OB_URL, "records": 1}]}
        data[tracka_outcomes.INDEX_URL] = json.dumps(index).encode()
        data[OB_URL] = zip_json({"meta": {"last_updated": H12.isoformat(), "results": {"skip": 0, "total": 1}},
                                "results": [{"products": [{"application_type": "A", "application_number": "000017",
                                                           "product_number": "001", "approval_date": "20271126",
                                                           "active_ingredients": [{"name": KEYS[16]}]}]}]}, "ob.json")
        status, folder, report, _ = self.readout(12, H12, data)
        self.assertEqual(status, "SCORED")
        self.assertEqual(report["panels"]["12"]["event_rows"], 11)
        self.assertEqual(load(folder / "event-witnesses.json")[KEYS[16]]["locator"], "ANDA000017")

    def test_bad_hash_fails_cli(self):
        (self.release.folder / "core_12m.jsonl").write_bytes(b"wrong bytes\n")
        with redirect_stdout(StringIO()) as output:
            rc = main(("--release", str(self.release.folder), "--horizon", "12", "--out", str(self.root / "bad")))
        self.assertEqual(rc, 1)
        self.assertIn("SHA-256 mismatch", output.getvalue())
        self.assertFalse((self.root / "bad").exists())

    def test_per_arm_freeze_binds_each_score_to_its_arm(self):
        folder = self.release.folder
        manifest = load(folder / MANIFEST)
        dictionary = load(folder / ARMS)
        predictions = {}
        l1_inputs = folder / "L1DEV_inputs.jsonl"
        for arm, source in dictionary.items():
            filename = f"{arm}_predictions.jsonl"
            rows = []
            for original in source["files"].values():
                for line in (folder / original).read_text(encoding="utf-8").splitlines():
                    row = json.loads(line)
                    if arm in CORE + PRIOR:
                        row.update(row.pop("arms")[arm])
                    if arm in LLM:
                        row["entity"] = "Display name for " + row.pop("key")
                    rows.append(row)
            if arm == "L1":
                jsonl(l1_inputs, [{k: row[k] for k in ("entity", "horizon_months", "t0")} for row in rows])
            jsonl(folder / filename, rows)
            source["files"] = dict.fromkeys(source["files"], filename)
            predictions[arm] = {"file": filename, "sha256": digest(folder / filename), "status": "ADMITTED"}
        roster_hash = digest(folder / ROSTER)
        dump(folder / FREEZE, {"schema": TRACKA_FREEZE_SCHEMA, "t0": T0.isoformat(),
                               "git_tag": manifest["freeze_tag"], "predictions": predictions,
                               "roster": {"canonical_file": ROSTER, "sha256": roster_hash},
                               "upstream_private_sha256": {ROSTER: roster_hash, l1_inputs.name: digest(l1_inputs)}})
        manifest["osf_manifest_sha256"] = digest(folder / FREEZE)
        names = [ROSTER, *(record["file"] for record in predictions.values())]
        manifest["frozen_files"] = {name: name for name in names}
        manifest["files_sha256"] = {name: digest(folder / name) for name in (*names, IDENTITY, FREEZE, SCORER)}
        dump(folder / ARMS, dictionary)
        manifest["files_sha256"][ARMS] = digest(folder / ARMS)
        dump(folder / MANIFEST, manifest)
        self.assertEqual(read_release(folder, manifest["osf_manifest_sha256"]).scores, self.release.scores)
        dictionary["M3"]["files"] = dictionary["B1"]["files"]
        dump(folder / ARMS, dictionary)
        manifest["files_sha256"][ARMS] = digest(folder / ARMS)
        dump(folder / MANIFEST, manifest)
        with self.assertRaisesRegex(ValueError, "pinned to another arm"):
            read_release(folder, manifest["osf_manifest_sha256"])

    def test_wrong_order_stops_even_with_matching_hashes(self):
        folder = self.release.folder
        file = folder / "core_12m.jsonl"
        file.write_bytes(b"\n".join(reversed(file.read_bytes().splitlines())) + b"\n")
        frozen = load(folder / FREEZE)
        frozen["files_sha256"][file.name] = digest(file)
        dump(folder / FREEZE, frozen)
        manifest = load(folder / MANIFEST)
        manifest["files_sha256"].update({file.name: digest(file), FREEZE: digest(folder / FREEZE)})
        manifest["osf_manifest_sha256"] = digest(folder / FREEZE)
        dump(folder / MANIFEST, manifest)
        with self.assertRaisesRegex(ValueError, "Roster order"):
            read_release(folder)

    def test_version_doi_not_concept_doi(self):
        zip_path = BytesIO()
        with ZipFile(zip_path, "w") as archive:
            for file in self.release.folder.iterdir():
                archive.write(file, file.name)
        def fake_zenodo(url, *_):
            if "/api/records/" in url:
                return json.dumps({"id": 123, "doi": "10.5281/zenodo.123",
                                   "files": [{"key": "track-a-release.zip"}]}).encode()
            return zip_path.getvalue()
        with patch("loe_bench.score_release.fetch_bytes", side_effect=fake_zenodo):
            with release_directory("https://doi.org/10.5281/zenodo.123") as folder:
                self.assertEqual(read_release(folder).keys, self.release.keys)
            with self.assertRaisesRegex(ValueError, "exact version DOI"):
                with release_directory("10.5281/zenodo.124"):
                    self.fail("concept DOI accepted")

    def test_stopped_and_unevaluable_sequence(self):
        point = {"estimate": .1, "ci95": [.01, .2], "undefined_draws": 0}
        tie = {"estimate": .1, "ci95": [0.0, .2], "undefined_draws": 0}
        empty = {"estimate": None, "ci95": None, "undefined_draws": 2000}
        panels = {12: {"contrasts": {"M3-B1": {"recall": point}}},
                  24: {"contrasts": {"M3-B1": {"recall": point}, "M3-M1": {"recall": tie}}}}
        steps = tracka_statistics.sequence(panels)
        self.assertEqual([steps[h]["decision"] for h in ("H1", "H2", "H3")],
                         ["PASS", "FAIL", "NOT_REACHED_DESCRIPTIVE"])
        panels[24]["contrasts"]["M3-B1"]["recall"] = empty
        steps = tracka_statistics.sequence(panels)
        self.assertEqual([steps[h]["decision"] for h in ("H1", "H2", "H3")],
                         ["UNEVALUABLE", "NOT_REACHED_DESCRIPTIVE", "NOT_REACHED_DESCRIPTIVE"])


if __name__ == "__main__":
    unittest.main()
