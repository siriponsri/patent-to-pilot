"""Exercise first capture and result custody with fictional FDA editions."""

from contextlib import nullcontext, redirect_stdout
from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from loe_bench import tracka_capture, tracka_custody as custody, tracka_outcomes, tracka_publish
from loe_bench import tracka_readout, tracka_release, tracka_vintage
from loe_bench.score_release import RECEIPT, RESULTS, SOURCES, score as legacy_score
from loe_bench.tracka_readout import prepare_publication, score
from loe_bench.tracka_release import FREEZE, digest, dump, load
from loe_bench.tests.test_score_release import H12, H24, approval, fake_fda, synthetic_release, zip_json

REPO = "example/fictional-track-a"
DOI = "10.5281/zenodo.1234"
COMMIT = "c" * 40
ORANGE = "https://download.open.fda.gov/drug/orangebook/example.json.zip"
# scorer-version.json from the public Track A kit for DOI 10.5281/zenodo.24629100.
PUBLISHED_SCORER = Path(__file__).with_name("fixtures") / "zenodo-24629100-scorer-version.json"


def at(day, hour=1):
    return datetime.combine(day, time(hour), tzinfo=timezone.utc)


def sources(day, **kwargs):
    data = fake_fda(day, **kwargs)
    index = json.loads(data[tracka_outcomes.INDEX_URL])
    index["results"]["drug"]["orangebook"] = {
        "export_date": str(day), "total_records": 1, "partitions": [{"file": ORANGE, "records": 1}]}
    data[tracka_outcomes.INDEX_URL] = json.dumps(index).encode()
    data[ORANGE] = zip_json({"meta": {"last_updated": str(day), "results": {"skip": 0, "total": 1}},
                            "results": [{"fixture": True}]}, "orangebook.json")
    return data


class ReadoutTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source_pins = load(PUBLISHED_SCORER)["source_files_sha256"]
        self.release = synthetic_release(self.root / "release", diagnostic_fields={
            "diagnostic_action": "PREDICT_NO_ENTRY", "graph_conflict": False}, source_pins=self.source_pins)
        self.freeze = self.release.manifest["files_sha256"][FREEZE]
        self.responses = {}
        self.issues = []
        self.guard = self.patch(tracka_outcomes, "fetch_bytes", side_effect=AssertionError("Unexpected FDA fetch"))
        self.patch(tracka_vintage, "CANONICAL_REPOSITORY", REPO)
        self.patch(tracka_vintage, "CANONICAL_DOI", DOI)
        self.patch(tracka_vintage, "CANONICAL_FREEZE", self.freeze)
        self.patch(custody, "fetch", side_effect=self.query)
        self.patch(custody, "verify_statements", side_effect=self.verify_statements)

    def test_cli_accepts_current_tree_with_published_source_pins(self):
        self.assertEqual(len(self.source_pins), 25)
        out = self.root / "cli-pending"
        command = ["--release", str(self.release.folder), "--horizon", "12", "--out", str(out),
                   "--freeze-sha256", self.freeze]
        with patch.object(tracka_readout, "datetime") as clock, redirect_stdout(StringIO()) as stdout:
            clock.now.return_value = at(H12 - timedelta(days=1))
            self.assertEqual(tracka_readout.main(command), 0)
        self.assertTrue(stdout.getvalue().startswith("PENDING "))
        run, = sorted((out / "12m").iterdir())
        self.assertEqual(load(run / RESULTS)["status"], "PENDING")
        self.assertEqual(load(run / SOURCES)["sources"], [])
        self.guard.assert_not_called()
        custody.fetch.assert_not_called()

    def test_published_source_pins_reject_a_change_to_each_file(self):
        installed = Path(tracka_release.__file__).parent
        isolated = self.root / "installed-scorer"
        isolated.mkdir()
        for name in self.source_pins:
            (isolated / name).write_bytes((installed / name).read_bytes())
        with patch.object(tracka_release, "__file__", str(isolated / "tracka_release.py")):
            for name in self.source_pins:
                with self.subTest(source=name):
                    path = isolated / name
                    original = path.read_bytes()
                    path.write_bytes(original + b"\n# Altered after publication\n")
                    try:
                        with self.assertRaises(ValueError) as rejected:
                            tracka_release.read_release(self.release.folder, self.freeze)
                        self.assertEqual(str(rejected.exception), f"Installed scorer differs from the release for {name}")
                    finally:
                        path.write_bytes(original)

    def patch(self, obj, name, *args, **kwargs):
        patcher = patch.object(obj, name, *args, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def scope(self, horizon=12, kind="capture"):
        return custody.Scope(REPO, DOI, self.freeze, horizon, kind)

    def query(self, url, limit, **kwargs):
        if "/issues?" in url:
            return json.dumps(self.issues).encode()
        if url in self.responses:
            return self.responses[url]
        if "/releases?per_page=" in url:
            return b"[]"
        if "/attestations/" in url:
            return b'{"attestations":[]}'
        if "/git/matching-refs/" in url:
            return b"[]"
        if "/releases/tags/" in url:
            return None
        raise AssertionError(f"Unexpected GitHub request: {url}")

    def index_url(self, scope):
        return f"{scope.api}/attestations/sha256:{sha256(scope.witness()).hexdigest()}?per_page=100&page=1"

    def attest(self, scope, pins):
        self.responses[self.index_url(scope)] = json.dumps({"attestations": [{"bundle": item} for item in pins]}).encode()

    def verify_statements(self, scope, witness, count):
        self.assertEqual(witness.read_bytes(), scope.witness())
        batch = json.loads(self.responses[self.index_url(scope)])["attestations"]
        self.assertEqual(len(batch), count)
        return [item["bundle"] for item in batch]

    def release_bundle(self, scope, bundle, day, *, draft=False, attest=True):
        pin = {"bundle_sha256": digest(bundle), "signed_at_utc": at(day, 2 if scope.kind == "capture" else 4).isoformat(),
               "run_id": "12345", "run_attempt": "1", "workflow_ref": scope.identity, "commit": COMMIT}
        published = at(day, 3 if scope.kind == "capture" else 5).isoformat()
        asset = f"https://github.com/{REPO}/releases/download/{scope.tag}/{scope.archive}"
        refs = f"{scope.api}/git/matching-refs/tags/{scope.tag}"
        release = f"{scope.api}/releases/tags/{scope.tag}"
        metadata = {"id": 10, "tag_name": scope.tag, "draft": draft, "published_at": published,
                    "body": f"{custody.PIN}{digest(bundle)}\n{custody.PROVENANCE}{json.dumps(pin)}",
                    "assets": [{"id": 20, "name": scope.archive, "state": "uploaded",
                                "size": bundle.stat().st_size, "digest": f"sha256:{digest(bundle)}"}]}
        if draft:
            self.responses[f"{scope.api}/releases?per_page=100&page=1"] = json.dumps([metadata]).encode()
            self.responses[f"{scope.api}/releases/assets/20"] = bundle.read_bytes()
        else:
            self.responses[release] = json.dumps(metadata).encode()
            self.responses[refs] = json.dumps([{"ref": f"refs/tags/{scope.tag}",
                                               "object": {"type": "commit", "sha": COMMIT,
                                                          "url": f"{scope.api}/git/commits/{COMMIT}"}}]).encode()
            self.responses[asset] = bundle.read_bytes()
        if attest:
            self.attest(scope, [pin])
        return pin

    def capture(self, name, horizon, day, fda=None, *, publish=True):
        path = self.root / f"{name}.zip"
        fda = fda or sources(day)
        with patch.object(tracka_outcomes, "fetch_bytes", side_effect=lambda url, *_: fda[url]):
            tracka_capture.build(self.scope(horizon), at(day), path)
        if publish:
            self.release_bundle(self.scope(horizon), path, day)
        return path

    def readout(self, name, horizon, day, **kwargs):
        if "doi" not in kwargs:
            kwargs["doi"] = DOI
        status, folder = score(self.release, horizon, self.root / name, today=day, **kwargs)
        self.guard.assert_not_called()
        return status, folder, load(folder / RESULTS)

    def archive(self, horizon, day, *, publish=True):
        status, path, result = self.readout(f"score-{horizon}", horizon, day)
        self.assertEqual(status, "SCORED")
        self.assertTrue(result["publication_eligible"])
        staged = path / "staged"
        prepare_publication(path, staged)
        bundle = path / "result.zip"
        custody.pack(staged, tracka_vintage.ASSETS, bundle)
        if publish:
            self.release_bundle(self.scope(horizon, "result"), bundle, day)
        return staged, bundle

    def scored_issue(self, number, body):
        return {"user": {"login": "maintainer"}, "author_association": "OWNER",
                "title": "Track A 12-month readout", "body": body,
                "html_url": f"https://github.com/{REPO}/issues/{number}"}

    def stage_24_context(self):
        self.capture("first12", 12, H12)
        first, _ = self.archive(12, H12)
        self.capture("first24", 24, H24)
        scope = self.scope(24, "result")
        area = self.root / "stage"
        area.mkdir()
        self.patch(tracka_publish, "release_directory", return_value=nullcontext(self.release.folder))
        return first, scope, area

    def test_capture_preserves_raw_index_and_both_exports_before_outcomes(self):
        edition = sources(H12)
        with patch.object(tracka_outcomes, "resolve_first_approvals", side_effect=AssertionError):
            bundle = self.capture("blind", 12, H12, edition)
        snapshot, manifest = tracka_capture.restore(self.scope(), bundle, self.root / "snapshot")
        for entry in manifest["sources"]:
            self.assertEqual((snapshot / entry["file"]).read_bytes(), edition[entry["url"]])
            self.assertEqual(digest(snapshot / entry["file"]), entry["sha256"])
        self.assertEqual(set(manifest["editions"]), {"drugsfda", "orangebook"})

    def test_late_retry_reuses_first_capture_and_excludes_reviewers_second_edition(self):
        self.capture("first12", 12, H12)
        first12, _ = self.archive(12, H12)
        first24 = self.capture("first24", 24, H24)
        first, _ = self.archive(24, H24, publish=False)  # Scoring finished but publication failed.
        snapshot1, _ = tracka_capture.restore(self.scope(24), first24, self.root / "caller-first")
        day = H24 + timedelta(days=2)
        extra = tuple(approval(i, "20271126", app=f"ANDA0001{i:02d}") for i in range(12, 20))
        edition2 = self.capture("other24", 24, day, sources(day, extra=extra), publish=False)
        caller_snapshot, _ = tracka_capture.restore(self.scope(24), edition2, self.root / "caller")
        # The frozen calculation still flips when the reviewer deliberately changes FDA bytes.
        for name, scored_on, snapshot, decision in (
                ("earlier", H24, snapshot1, "PASS"), ("later", day, caller_snapshot, "FAIL")):
            _, legacy = legacy_score(self.release, 24, self.root / f"legacy-{name}", today=scored_on,
                                     snapshot=snapshot, prior_12=first12.parent)
            self.assertEqual(load(legacy / RESULTS)["hypotheses"]["H1"]["decision"], decision)
        _, caller, provisional = self.readout("caller", 24, day, snapshot=caller_snapshot)
        self.assertEqual(provisional["hypotheses"]["H1"]["sequence_decision"], "FAIL")
        self.assertEqual(provisional["h3_input"]["results_sha256"], digest(first12 / RESULTS))
        with self.assertRaisesRegex(ValueError, "ineligible"):
            prepare_publication(caller, self.root / "forbidden")
        self.assertEqual([step["decision"] for step in load(first / RESULTS)["hypotheses"].values()], ["PASS"] * 3)

        status, retry, result = self.readout("retry", 24, day)
        self.assertEqual(status, "SCORED")
        self.assertTrue(result["scoring_late"])
        self.assertEqual(result["capture"]["bundle_sha256"], digest(first24))
        self.assertEqual(result["hypotheses"]["H1"]["sequence_decision"], "PASS")
        self.assertEqual(digest(retry / SOURCES), digest(first / SOURCES))
        self.assertEqual(result["h3_input"]["results_sha256"], digest(first12 / RESULTS))
        _, published = self.archive(24, day)
        self.assertTrue(published.exists())
        _, later, replay = self.readout("after-publication", 24, day + timedelta(days=1))
        self.assertEqual(replay["family_status"], "REPLAY")
        self.assertEqual(replay["replay_comparison"]["changed_source_files"], [])
        with self.assertRaisesRegex(ValueError, "ineligible"):
            prepare_publication(later, self.root / "no-second-bundle")

    def test_staging_the_same_capture_again_never_fetches(self):
        day = H12 + timedelta(days=2)
        area = self.root / "stage"
        area.mkdir()
        self.capture("late", 12, day)
        tracka_publish.stage_capture(self.scope(), area, at(day + timedelta(days=1)))
        _, _, result = self.readout("late", 12, day + timedelta(days=1))
        self.assertTrue(result["capture"]["capture_late"])
        self.assertTrue(result["capture"]["publication_late"])
        self.guard.assert_not_called()

    def test_admitted_capture_draft_resumes_after_grace_without_fetching(self):
        bundle = self.capture("draft", 12, H12, publish=False)
        self.release_bundle(self.scope(), bundle, H12, draft=True)
        area = self.root / "stage"
        area.mkdir()
        with patch.object(tracka_publish, "output") as output:
            tracka_publish.stage_capture(self.scope(), area, at(H12 + timedelta(days=9)))
        self.assertEqual(digest(area / self.scope().archive), digest(bundle))
        output.assert_any_call("attest", "false")
        output.assert_any_call("publish", "true")
        self.guard.assert_not_called()

    def test_result_draft_survives_scoring_and_is_resumed_without_recomputation(self):
        self.capture("first12", 12, H12)
        _, bundle = self.archive(12, H12, publish=False)
        self.release_bundle(self.scope(12, "result"), bundle, H12, draft=True)
        area = self.root / "stage"
        area.mkdir()
        with (patch.object(tracka_publish, "release_directory", return_value=nullcontext(self.release.folder)),
              patch.object(tracka_publish, "score", side_effect=AssertionError("Unexpected rescoring")),
              patch.object(tracka_publish, "output") as output):
            tracka_publish.stage_result(self.scope(12, "result"), area, H12 + timedelta(days=8))
        self.assertEqual(digest(area / self.scope(12, "result").archive), digest(bundle))
        output.assert_any_call("attest", "false")

    def test_fresh_24_month_publication_stages_with_registered_scope(self):
        first, scope, area = self.stage_24_context()
        with (patch.object(tracka_publish, "create_draft") as create_draft,
              patch.object(tracka_publish, "output") as output):
            tracka_publish.stage_result(scope, area, H24)
        create_draft.assert_called_once_with(scope, area)
        output.assert_any_call("publish", "true")
        original = load(area / "result" / RESULTS)["h3_input"]["original"]
        self.assertEqual(original["results_sha256"], digest(first / RESULTS))
        self.assertEqual(original["outcome_source_manifest_sha256"], digest(first / SOURCES))

    def test_24_month_12_month_pin_conflict_holds_fresh_and_restored_drafts(self):
        first, scope, area = self.stage_24_context()
        _, bundle = self.archive(24, H24, publish=False)
        _, record = tracka_vintage.publication_scope(self.freeze, DOI)
        marker = f"<!-- tracka:12:SCORED:{record} -->"
        trusted = self.scored_issue(1, f"{marker}\nFirst result SHA-256 `{digest(first / RESULTS)}`.")
        conflict = self.scored_issue(2, f"{marker}\nFirst result SHA-256 `{'0' * 64}`.")
        self.issues = [trusted, conflict]
        _, _, result = self.readout("fresh-conflict", 24, H24)
        self.assertEqual(result["family_status"], custody.HOLD)
        self.assertFalse(result["publication_eligible"])

        output = self.patch(tracka_publish, "output")
        summary = self.patch(tracka_publish, "summary")
        gh = self.patch(tracka_publish, "gh")
        tracka_publish.stage_result(scope, area, H24)
        output.assert_called_once_with("publish", "false")
        self.assertIn("witnesses disagree", str(summary.call_args_list))
        gh.assert_not_called()
        self.assertFalse((area / scope.archive).exists())

        self.release_bundle(scope, bundle, H24, draft=True)
        self.patch(tracka_publish, "score", side_effect=AssertionError("Unexpected rescoring"))
        output.reset_mock()
        summary.reset_mock()
        tracka_publish.stage_result(scope, area, H24 + timedelta(days=1))
        output.assert_called_once_with("publish", "false")
        self.assertIn("witnesses disagree", summary.call_args.args[0])
        original_bytes = bundle.read_bytes()
        self.assertEqual((area / scope.archive).read_bytes(), original_bytes)

        self.issues = [trusted]
        output.reset_mock()
        tracka_publish.stage_result(scope, area, H24 + timedelta(days=1))
        output.assert_any_call("attest", "false")
        output.assert_any_call("publish", "true")

        self.issues.append(conflict)  # A witness can change after the staging gate.
        output.reset_mock()
        tracka_publish.publish(scope, area)
        output.assert_called_once_with("publish", "false")
        self.assertIn("witnesses disagree", summary.call_args.args[0])
        gh.assert_not_called()

        self.issues = [trusted]

        def promote(*args):
            self.assertEqual(args[:4], ("api", "--method", "PATCH", f"repos/{REPO}/releases/10"))
            self.assertIn("draft=false", args)
            self.assertEqual(self.responses[f"{scope.api}/releases/assets/20"], original_bytes)
            self.release_bundle(scope, bundle, H24)

        gh.side_effect = promote
        tracka_publish.publish(scope, area)
        gh.assert_called_once()
        panel, evidence = tracka_vintage.discover(REPO, DOI, self.freeze, self.release.manifest_sha256,
                                                 self.root / "published24", horizon=24)
        self.assertIsNotNone(panel, evidence)
        self.assertEqual(evidence["original"]["bundle_sha256"], digest(bundle))
        self.assertEqual((area / scope.archive).read_bytes(), original_bytes)

    def test_24_month_staged_h3_digest_mismatches_hold_promotion(self):
        _, scope, area = self.stage_24_context()
        staged, _ = self.archive(24, H24, publish=False)
        result = load(staged / RESULTS)
        self.patch(tracka_publish, "score", side_effect=AssertionError("Unexpected rescoring"))
        output = self.patch(tracka_publish, "output")
        summary = self.patch(tracka_publish, "summary")
        gh = self.patch(tracka_publish, "gh")

        for field in ("results_sha256", "outcome_source_manifest_sha256"):
            with self.subTest(field=field):
                h3 = result["h3_input"]
                reference = {**h3, "original": {**h3["original"], field: "0" * 64}}
                if field == "results_sha256":
                    reference[field] = "0" * 64
                dump(staged / RESULTS, {**result, "h3_input": reference})
                (staged / tracka_vintage.CHECKSUM).write_text(f"{digest(staged / RESULTS)}  {RESULTS}\n", encoding="ascii")
                bundle = self.root / f"wrong-{field}.zip"
                custody.pack(staged, tracka_vintage.ASSETS, bundle)
                self.release_bundle(scope, bundle, H24, draft=True)

                output.reset_mock()
                tracka_publish.stage_result(scope, area, H24)
                output.assert_called_once_with("publish", "false")
                output.reset_mock()
                tracka_publish.publish(scope, area)
                output.assert_called_once_with("publish", "false")
                self.assertIn("differs from the verified first 12-month result", summary.call_args.args[0])
                self.assertEqual((area / scope.archive).read_bytes(), bundle.read_bytes())
        gh.assert_not_called()

    def test_capture_publication_records_verified_signer_and_bundle(self):
        scope = self.scope()
        bundle = self.capture("draft", 12, H12, publish=False)
        pin = self.release_bundle(scope, bundle, H12, draft=True)
        area = self.root / "stage"
        area.mkdir()
        (area / scope.archive).write_bytes(bundle.read_bytes())

        def publish_draft(*args):
            self.assertEqual(args[:4], ("api", "--method", "PATCH", f"repos/{REPO}/releases/10"))
            self.assertIn(f"target_commitish={COMMIT}", args)
            self.assertIn("draft=false", args)
            notes = Path(next(arg.removeprefix("body=@") for arg in args if arg.startswith("body=@")))
            self.assertEqual(custody.note_value({"body": notes.read_text(encoding="utf-8")}, custody.PIN), digest(bundle))
            provenance = custody.note_value({"body": notes.read_text(encoding="utf-8")}, custody.PROVENANCE)
            self.assertEqual(json.loads(provenance), pin)
            self.release_bundle(scope, bundle, H12)

        with patch.object(tracka_publish, "gh", side_effect=publish_draft) as gh:
            tracka_publish.publish(scope, area)
        gh.assert_called_once()
        self.assertEqual(self.readout("AFTER", 12, H12)[2]["capture"]["provenance"], pin)

    def test_missing_capture_cannot_stage_after_grace(self):
        area = self.root / "stage"
        area.mkdir()
        with self.assertRaisesRegex(ValueError, "Outside the declared"):
            tracka_publish.stage_capture(self.scope(), area, at(H12 + timedelta(days=8)))
        status, _, result = self.readout("missed", 12, H12 + timedelta(days=8))
        self.assertEqual((status, result["family_status"]), ("BLOCKED_SOURCE", custody.HOLD))

    def test_missing_first12_is_descriptive_even_with_verified_24_capture(self):
        self.capture("capture24", 24, H24)
        _, path, result = self.readout("no12", 24, H24)
        self.assertEqual(result["family_status"], custody.HOLD)
        self.assertEqual({step["decision"] for step in result["hypotheses"].values()}, {"DESCRIPTIVE_ONLY"})
        self.assertFalse(any(step["reached"] for step in result["hypotheses"].values()))
        self.assertFalse(result["publication_eligible"])
        with self.assertRaisesRegex(ValueError, "ineligible"):
            prepare_publication(path, self.root / "deny")

    def test_deleted_release_and_tag_with_signed_capture_intent_stays_on_hold(self):
        scope = self.scope()
        bundle = self.capture("deleted", 12, H12, publish=False)
        claim = self.release_bundle(scope, bundle, H12)
        del self.responses[f"{scope.api}/releases/tags/{scope.tag}"]
        del self.responses[f"{scope.api}/git/matching-refs/tags/{scope.tag}"]
        status, _, result = self.readout("lost", 12, H12 + timedelta(days=2))
        self.assertEqual((status, result["family_status"]), ("BLOCKED_SOURCE", custody.HOLD))
        self.assertEqual(result["capture"]["attestations"], [claim])
        self.assertIn("survives without", result["capture"]["detail"])

    def test_deleted_result_witnesses_cannot_start_a_second_formal_result(self):
        self.capture("capture12", 12, H12)
        self.archive(12, H12)
        scope = self.scope(12, "result")
        del self.responses[f"{scope.api}/releases/tags/{scope.tag}"]
        del self.responses[f"{scope.api}/git/matching-refs/tags/{scope.tag}"]
        _, _, result = self.readout("lost-result", 12, H12 + timedelta(days=2))
        self.assertEqual(result["family_status"], custody.HOLD)
        self.assertFalse(result["publication_eligible"])
        self.assertIn("survives without", result["publication_discovery"]["detail"])

    def test_two_signed_capture_editions_for_the_same_scope_trigger_hold(self):
        scope = self.scope()
        first = self.capture("first", 12, H12)
        pin = self.release_bundle(scope, first, H12)
        second = self.capture("second", 12, H12 + timedelta(days=1), publish=False)
        self.attest(scope, [pin, {**pin, "bundle_sha256": digest(second)}])
        _, _, result = self.readout("conflicting", 12, H12 + timedelta(days=2))
        self.assertEqual(result["family_status"], custody.HOLD)
        self.assertIn("Conflicting attested", result["capture"]["detail"])

    def test_unattested_or_edited_release_is_not_accepted(self):
        scope = self.scope()
        bundle = self.capture("unattested", 12, H12, publish=False)
        pin = self.release_bundle(scope, bundle, H12, attest=False)
        _, _, result = self.readout("unattested", 12, H12)
        self.assertIn("lacks signed intent", result["capture"]["detail"])
        for field in ("commit", "workflow_ref", "run_id", "bundle_sha256"):
            with self.subTest(field=field):
                self.attest(scope, [{**pin, field: "0" * 64}])
                _, _, result = self.readout("edited", 12, H12)
                self.assertEqual(result["family_status"], custody.HOLD)

    def test_corrupt_capture_download_blocks_scoring(self):
        scope = self.scope()
        self.capture("corrupt", 12, H12)
        key = f"https://github.com/{REPO}/releases/download/{scope.tag}/{scope.archive}"
        self.responses[key] = b"?" + self.responses[key][1:]
        status, _, result = self.readout("bad", 12, H12)
        self.assertEqual(status, "BLOCKED_SOURCE")
        self.assertIn("bytes disagree", result["capture"]["detail"])

        status, folder, result = self.readout("bad-recovery", 12, H12, recover=True)
        self.assertEqual(status, "BLOCKED_SOURCE")
        for text in ("\n".join(result["missing"]), (folder / "REPORT.md").read_text(encoding="utf-8")):
            self.assertIn("MISSING_ORIGINAL", text)
            self.assertIn("bytes disagree", text)
            self.assertNotIn("No verified first capture", text)

    def test_issue_conflict_blocks_formal_recovery(self):
        self.capture("first", 12, H12)
        first, _ = self.archive(12, H12)
        _, record = tracka_vintage.publication_scope(self.freeze, DOI)

        def issue(index, pin):
            return {"user": {"login": "github-actions[bot]"}, "title": "Track A 12-month readout",
                    "body": f"<!-- tracka:12:SCORED:{record} -->\nFirst result SHA-256 `{pin}`.",
                    "html_url": f"https://github.com/{REPO}/issues/{index}"}

        self.issues = [issue(1, digest(first / RESULTS)), issue(2, "0" * 64)]
        status, folder, result = self.readout("disputed", 12, H12, recover=True)
        self.assertEqual(status, "BLOCKED_SOURCE")
        self.assertEqual(result["family_status"], custody.HOLD)
        self.assertEqual(result["capture"]["status"], "VERIFIED")
        discovery = result["publication_discovery"]
        self.assertEqual(len(discovery["issue_urls"]), 2)
        report = (folder / "REPORT.md").read_text(encoding="utf-8")
        self.assertEqual(load(folder / RECEIPT)["files_sha256"]["REPORT.md"], digest(folder / "REPORT.md"))
        for text in ("\n".join(result["missing"]), report):
            self.assertIn(discovery["reason"], text)
            self.assertIn(discovery["detail"], text)
            self.assertNotIn("No verified first capture", text)
            for url in discovery["issue_urls"]:
                self.assertIn(url, text)

    def test_recovery_distinguishes_missing_capture_from_missing_result(self):
        missing_capture = "No verified first capture is available."
        status, folder, result = self.readout("missing-capture", 12, H12, recover=True)
        self.assertEqual(status, "BLOCKED_SOURCE")
        self.assertEqual(result["missing"], [missing_capture])
        self.assertIn(missing_capture, (folder / "REPORT.md").read_text(encoding="utf-8"))

        self.capture("first", 12, H12)
        status, folder, result = self.readout("missing-result", 12, H12, recover=True)
        self.assertEqual(status, "BLOCKED_SOURCE")
        self.assertEqual(result["capture"]["status"], "VERIFIED")
        for text in ("\n".join(result["missing"]), (folder / "REPORT.md").read_text(encoding="utf-8")):
            self.assertIn("MISSING_ORIGINAL", text)
            self.assertNotIn(missing_capture, text)

    def test_24_month_replay_and_recovery_report_current_witnesses(self):
        first12, scope, _ = self.stage_24_context()
        first24, bundle = self.archive(24, H24, publish=False)
        publication_day = H24 + timedelta(days=1)
        self.release_bundle(scope, bundle, publication_day)
        bundle_bytes = bundle.read_bytes()

        _, record = tracka_vintage.publication_scope(self.freeze, DOI)
        marker = f"<!-- tracka:12:SCORED:{record} -->"
        manifest_pin = f"FDA source manifest SHA-256 `{digest(first12 / SOURCES)}`."
        trusted = self.scored_issue(1, f"{marker}\nFirst result SHA-256 `{digest(first12 / RESULTS)}`.\n{manifest_pin}")
        conflict = self.scored_issue(2, f"{marker}\nFirst result SHA-256 `{'0' * 64}`.\n{manifest_pin}")
        self.issues = [trusted]
        for expected in ("VERIFIED_CONSISTENT", "CURRENT_DISPUTE", custody.HOLD):
            disputed = expected == "CURRENT_DISPUTE"
            if disputed:
                self.issues.append(conflict)
                panel, discovery = tracka_vintage.discover(REPO, DOI, self.freeze, self.release.manifest_sha256,
                                                           self.root / "standalone-dispute")
                self.assertIsNone(panel)
                self.assertEqual(discovery["reason"], custody.HOLD)
            if expected == custody.HOLD:
                self.issues.clear()
                first12_scope = self.scope(12, "result")
                self.responses.pop(f"{first12_scope.api}/releases/tags/{first12_scope.tag}")
                self.responses.pop(f"{first12_scope.api}/git/matching-refs/tags/{first12_scope.tag}")
                self.responses.pop(self.index_url(first12_scope))
            for recover, expected_run in ((False, "SCORED"), (True, "RECOVERED")):
                with self.subTest(expected=expected, recover=recover):
                    status, folder, result = self.readout(f"published-{expected}-{recover}", 24,
                                                          publication_day + timedelta(days=1), recover=recover)
                    self.assertEqual(status, expected_run)
                    self.assertEqual(result["family_status"], "REPLAY")
                    self.assertFalse(result["publication_eligible"])
                    self.assertEqual(result["first_publication"]["published_at_utc"], at(publication_day, 5).isoformat())
                    check = result["current_12m_witness_check"]
                    self.assertEqual(check["status"], expected)
                    needs_reconciliation = expected != "VERIFIED_CONSISTENT"
                    self.assertEqual(check["custodian_reconciliation_required"], needs_reconciliation)
                    self.assertEqual(check["discovery"]["issue_urls"], [issue["html_url"] for issue in self.issues])
                    manifest = load(folder / RECEIPT)["files_sha256"]
                    for name in ("REPORT.md", "REPLAY.md"):
                        self.assertEqual(manifest[name], digest(folder / name))
                        report = (folder / name).read_text(encoding="utf-8")
                        self.assertIn(f"formal as verified at publication on {publication_day}", report)
                        self.assertIn(f"Current 12-month witness check `{expected}`", report)
                        self.assertNotIn("remains formal", report)
                        if needs_reconciliation:
                            self.assertIn("custodian for reconciliation", report)
                            for locator in check["witness_locators"]:
                                self.assertIn(locator, report)
                    archived = folder.parent / f"first-published-{digest(first24 / RESULTS)}"
                    for name in tracka_vintage.ASSETS:
                        self.assertEqual((archived / name).read_bytes(), (first24 / name).read_bytes())
        self.assertEqual(bundle.read_bytes(), bundle_bytes)

    def test_24_month_recovery_checks_unavailable_and_replaced_12_month_result(self):
        first12, _, _ = self.stage_24_context()
        self.archive(24, H24)
        scope = self.scope(12, "result")
        self.responses.pop(f"{scope.api}/releases/tags/{scope.tag}")
        self.responses.pop(f"{scope.api}/git/matching-refs/tags/{scope.tag}")
        self.responses.pop(self.index_url(scope))

        status, folder, result = self.readout("lost-first12", 24, H24, recover=True)
        self.assertEqual(status, "RECOVERED")
        check = result["current_12m_witness_check"]
        self.assertEqual(check["status"], custody.HOLD)
        self.assertEqual(check["reason"], "MISSING_ORIGINAL")
        self.assertTrue(check["custodian_reconciliation_required"])
        report = (folder / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn(f"Current 12-month witness check `{custody.HOLD}`", report)
        self.assertIn(f"https://github.com/{REPO}/releases/tag/{scope.tag}", report)

        replacement, _ = self.archive(12, H12 + timedelta(days=1))
        self.assertNotEqual(digest(replacement / RESULTS), digest(first12 / RESULTS))
        self.assertEqual(digest(replacement / SOURCES), digest(first12 / SOURCES))
        status, _, result = self.readout("replaced-first12", 24, H24, recover=True)
        self.assertEqual(status, "RECOVERED")
        check = result["current_12m_witness_check"]
        self.assertEqual(check["status"], "CURRENT_DISPUTE")
        self.assertEqual(check["reason"], "PUBLISHED_H3_DIGEST_MISMATCH")
        self.assertEqual(check["discovery"]["original"]["results_sha256"], digest(replacement / RESULTS))

    def test_reader_verifies_the_documented_maintainer_acknowledgement(self):
        guide = Path(__file__).resolve().parents[3] / "docs/loe-bench/HOW-TO-SCORE-TRACK-A.md"
        example, = re.findall(r"^```text\n(<!-- tracka:12:SCORED:[\s\S]*?)\n```$",
                              guide.read_text(encoding="utf-8"), re.MULTILINE)
        pins = {name: [] for name in tracka_vintage.PIN_LABELS}
        self.assertEqual(tracka_vintage.publish_pins(example, "guide", pins), [])
        example_result, = pins[RESULTS]
        example_manifest, = pins[SOURCES]

        self.capture("first", 12, H12)
        first, _ = self.archive(12, H12)
        _, record = tracka_vintage.publication_scope(self.freeze, DOI)
        marker, remainder = example.split("\n", 1)
        scope = f"<!-- tracka:12:SCORED:{record} -->"
        self.assertRegex(marker, r"^<!-- tracka:12:SCORED:[0-9a-f]{64}:\d+ -->$")
        body = scope + "\n" + remainder.replace(example_result["sha256"], digest(first / RESULTS)).replace(
            example_manifest["sha256"], digest(first / SOURCES))
        self.issues = [self.scored_issue(1, body)]
        panel, evidence = tracka_vintage.discover(REPO, DOI, self.freeze, self.release.manifest_sha256,
                                                 self.root / "maintainer")
        self.assertIsNotNone(panel, evidence)
        self.assertEqual(evidence["original"]["results_sha256"], digest(first / RESULTS))
        self.assertEqual(evidence["original"]["outcome_source_manifest_sha256"], digest(first / SOURCES))
        self.issues = [self.scored_issue(1, scope + "\n\nReadout report.")]
        panel, evidence = tracka_vintage.discover(REPO, DOI, self.freeze, self.release.manifest_sha256,
                                                 self.root / "incomplete")
        self.assertIsNone(panel)
        self.assertEqual(evidence["reason"], custody.HOLD)
        self.assertIn("Missing publication result digest", evidence["detail"])

    def test_recovery_preserves_result_bytes_without_fda(self):
        self.capture("capture12", 12, H12)
        first, _ = self.archive(12, H12)
        status, stage, result = self.readout("recover", 12, H12 + timedelta(days=2), recover=True)
        self.assertEqual(status, "RECOVERED")
        self.assertEqual(result["family_status"], "REPLAY")
        archived = stage.parent / f"first-published-{digest(first / RESULTS)}"
        for name in tracka_vintage.ASSETS:
            self.assertEqual((archived / name).read_bytes(), (first / name).read_bytes())

    def test_readout_has_no_live_fda_path(self):
        self.patch(tracka_capture, "discover", side_effect=AssertionError("prematurity made a discovery"))
        status, _, _ = self.readout("early", 24, H12)
        self.assertEqual(status, "PENDING")
        status, _, result = self.readout("local", 12, H12, doi=None)
        self.assertEqual(status, "BLOCKED_SOURCE")
        self.assertFalse(result["publication_eligible"])


class AttestationTest(unittest.TestCase):
    def test_missing_digest_requires_an_accessible_public_repository(self):
        scope = custody.Scope(REPO, DOI, "f" * 64, 12, "capture")
        with patch.object(custody, "verify_statements", side_effect=AssertionError):
            self.assertEqual(custody.attestations(scope, lambda u, _: (
                json.dumps({"full_name": REPO, "visibility": "public"}).encode() if u == scope.api else None)), [])
            with self.assertRaisesRegex(ValueError, "repository is unavailable"):
                custody.attestations(scope, lambda *_: None)

    def test_verifier_requires_scope_and_bundle_in_one_statement(self):
        scope = custody.Scope(REPO, DOI, "f" * 64, 12, "capture")
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            witness = folder / "track-a-scope.json"
            witness.write_bytes(scope.witness())
            claims = {"runInvocationURI": f"https://github.com/{REPO}/actions/runs/12345/attempts/2",
                      "sourceRepositoryDigest": COMMIT, "buildConfigURI": f"https://github.com/{scope.identity}",
                      "sourceRepositoryVisibilityAtSigning": "public"}
            statement = {"subject": [{"name": witness.name, "digest": {"sha256": digest(witness)}},
                                     {"name": scope.archive, "digest": {"sha256": "1" * 64}}]}
            verification = {"signature": {"certificate": claims},
                            "verifiedTimestamps": [{"type": "Tlog", "timestamp": at(H12, 2).isoformat()}],
                            "statement": statement}

            def output(result):
                return SimpleNamespace(returncode=0, stdout=json.dumps([{"verificationResult": result}]))

            with patch.object(custody, "run", return_value=output(verification)) as gh:
                identity, = custody.verify_statements(scope, witness, 1)
                self.assertEqual((identity["run_id"], identity["run_attempt"], identity["commit"]),
                                 ("12345", "2", COMMIT))
                self.assertIn(f"https://github.com/{scope.identity}", gh.call_args.args[0])
                self.assertIn(custody.REF, gh.call_args.args[0])
                verification["verifiedTimestamps"][0]["type"] = "TimestampAuthority"
                gh.return_value = output(verification)
                with self.assertRaisesRegex(ValueError, "transparency log"):
                    custody.verify_statements(scope, witness, 1)
                verification["verifiedTimestamps"][0]["type"] = "Tlog"
                verification["statement"]["subject"].pop()
                gh.return_value = output(verification)
                with self.assertRaisesRegex(ValueError, "does not bind"):
                    custody.verify_statements(scope, witness, 1)
                with self.assertRaisesRegex(ValueError, "Some indexed"):
                    custody.verify_statements(scope, witness, 2)


if __name__ == "__main__":
    unittest.main()
