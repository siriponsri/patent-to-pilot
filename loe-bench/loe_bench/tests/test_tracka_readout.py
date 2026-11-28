"""Exercise first capture and result custody with fictional FDA editions."""

from contextlib import nullcontext
from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from loe_bench import tracka_capture, tracka_custody as custody, tracka_outcomes, tracka_publish, tracka_vintage
from loe_bench.score_release import RESULTS, SOURCES, score as legacy_score
from loe_bench.tracka_readout import prepare_publication, score
from loe_bench.tracka_release import FREEZE, digest, load
from loe_bench.tests.test_score_release import H12, H24, approval, fake_fda, synthetic_release, zip_json

REPO = "example/fictional-track-a"
DOI = "10.5281/zenodo.1234"
COMMIT = "c" * 40
ORANGE = "https://download.open.fda.gov/drug/orangebook/example.json.zip"


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
        self.release = synthetic_release(self.root / "release", diagnostic_fields={
            "diagnostic_action": "PREDICT_NO_ENTRY", "graph_conflict": False})
        self.freeze = self.release.manifest["files_sha256"][FREEZE]
        self.responses = {}
        self.issues = []
        self.guard = self.patch(tracka_outcomes, "fetch_bytes", side_effect=AssertionError("Unexpected FDA fetch"))
        self.patch(tracka_vintage, "CANONICAL_REPOSITORY", REPO)
        self.patch(tracka_vintage, "CANONICAL_DOI", DOI)
        self.patch(tracka_vintage, "CANONICAL_FREEZE", self.freeze)
        self.patch(custody, "fetch", side_effect=self.query)
        self.patch(custody, "verify_statement", side_effect=lambda scope, witness, bundle, folder: json.loads(bundle))

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

    def test_issue_conflict_blocks_formal_recovery(self):
        self.capture("first", 12, H12)
        first, _ = self.archive(12, H12)
        _, record = tracka_vintage.publication_scope(self.freeze, DOI)

        def issue(index, pin):
            return {"user": {"login": "github-actions[bot]"}, "title": "Track A 12-month readout",
                    "body": f"<!-- tracka:12:SCORED:{record} -->\nFirst result SHA-256 `{pin}`.",
                    "html_url": f"https://github.com/{REPO}/issues/{index}"}

        self.issues = [issue(1, digest(first / RESULTS)), issue(2, "0" * 64)]
        _, _, result = self.readout("disputed", 12, H12)
        self.assertEqual(result["family_status"], custody.HOLD)
        self.assertEqual(len(result["publication_discovery"]["issue_urls"]), 2)
        self.assertIn("witnesses disagree", result["publication_discovery"]["detail"])

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
            verification = {"signature": {"certificate": {"extensions": claims}},
                            "verifiedTimestamps": [{"timestamp": at(H12, 2).isoformat()}],
                            "statement": statement}

            def output(result):
                return SimpleNamespace(returncode=0, stdout=json.dumps([{"verificationResult": result}]))

            with patch.object(custody, "run", return_value=output(verification)) as gh:
                identity = custody.verify_statement(scope, witness, b"fixture", folder)
                self.assertEqual((identity["run_id"], identity["run_attempt"], identity["commit"]),
                                 ("12345", "2", COMMIT))
                self.assertIn(f"https://github.com/{scope.identity}", gh.call_args.args[0])
                self.assertIn(custody.REF, gh.call_args.args[0])
                verification["statement"]["subject"].pop()
                gh.return_value = output(verification)
                with self.assertRaisesRegex(ValueError, "does not bind"):
                    custody.verify_statement(scope, witness, b"fixture", folder)


if __name__ == "__main__":
    unittest.main()
