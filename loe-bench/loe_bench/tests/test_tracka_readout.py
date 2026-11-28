"""First-publication and revised-vintage checks with fictional FDA editions."""

from datetime import timedelta
import json
from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from loe_bench import tracka_outcomes, tracka_vintage
from loe_bench.score_release import RESULTS, SOURCES, score as legacy_score
from loe_bench.tracka_readout import score
from loe_bench.tracka_release import FREEZE, digest, load
from loe_bench.tests.test_score_release import H12, H24, approval, fake_fda, synthetic_release

REPO = "example/fictional-track-a"
DOI = "10.5281/zenodo.1234"
PUB_DATE = "2027-11-28T00:05:00Z"


class ReadoutTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.release = synthetic_release(self.root / "release", diagnostic_fields={
            "diagnostic_action": "PREDICT_NO_ENTRY", "graph_conflict": False})
        self.freeze = self.release.manifest["files_sha256"][FREEZE]
        scope = patch.multiple(tracka_vintage, CANONICAL_REPOSITORY=REPO, CANONICAL_DOI=DOI,
                               CANONICAL_FREEZE=self.freeze)
        scope.start()
        self.addCleanup(scope.stop)
        tag, self.record = tracka_vintage.publication_scope(self.freeze, DOI)
        self.tag = tag
        self.api = f"https://api.github.com/repos/{REPO}"
        self.assets = f"https://github.com/{REPO}/releases/download/{tag}"
        self.release_url = f"{self.api}/releases/tags/{tag}"
        self.refs_url = f"{self.api}/git/matching-refs/tags/{tag}"
        self.issues_url = f"{self.api}/issues?state=all&per_page=100&page=1"
        for module in (tracka_outcomes, tracka_vintage):
            guard = patch.object(module, "urlopen", side_effect=AssertionError("Unexpected network"))
            guard.start()
            self.addCleanup(guard.stop)

    def readout(self, root, horizon, today, sources, *, scorer=score, **options):
        with patch.object(tracka_outcomes, "fetch_bytes", side_effect=lambda url, *_: sources[url]):
            status, folder = scorer(self.release, horizon, self.root / root, today=today, **options)
        self.assertEqual(status, "SCORED")
        return folder, load(folder / RESULTS)

    def archive(self, horizon=12, **options):
        today = H12 if horizon == 12 else H24
        folder, result = self.readout(f"first-runner-{horizon}", horizon, today, fake_fda(today), **options)
        sha = digest(folder / RESULTS)
        (folder / tracka_vintage.CHECKSUM).write_text(f"{sha}  {RESULTS}\n", encoding="ascii")
        return folder, sha, result

    def issue(self, sha, *, horizon=12, manifest_sha=None):
        today = H12 if horizon == 12 else H24
        body = (f"<!-- tracka:{horizon}:SCORED:{self.record} -->\n\nScoring started {today} UTC.\n\n"
                f"First publication UTC {PUB_DATE}.\n\nFirst result SHA-256 `{sha}`.")
        if manifest_sha:
            body += f"\n\nFDA source manifest SHA-256 `{manifest_sha}`."
        return {"title": f"Track A {horizon}-month readout", "user": {"login": "github-actions[bot]"},
                "created_at": PUB_DATE, "html_url": "https://github.com/example/fictional-track-a/issues/1",
                "body": body}

    def empty_publications(self):
        responses = {self.issues_url: b"[]"}
        for h in (12, 24):
            tag, _ = tracka_vintage.publication_scope(self.freeze, DOI, h)
            responses[f"{self.api}/releases/tags/{tag}"] = None
            responses[f"{self.api}/git/matching-refs/tags/{tag}"] = b"[]"
        return responses

    def published(self, folder, sha, *, horizon=12):
        tag, _ = tracka_vintage.publication_scope(self.freeze, DOI, horizon)
        assets = f"https://github.com/{REPO}/releases/download/{tag}"
        responses = self.empty_publications()
        responses.update({f"{assets}/{name}": (folder / name).read_bytes() for name in tracka_vintage.ASSETS})
        body = "\n\n".join(f"{label} `{digest(folder / name)}`." for name, label in tracka_vintage.PIN_LABELS.items())
        published_at = PUB_DATE if horizon == 12 else "2028-11-28T00:05:00Z"
        responses[f"{self.api}/releases/tags/{tag}"] = json.dumps({
            "draft": False, "tag_name": tag, "published_at": published_at, "body": body,
            "assets": [{"name": name, "state": "uploaded", "digest": f"sha256:{digest(folder / name)}"}
                       for name in tracka_vintage.ASSETS]}).encode()
        responses[self.issues_url] = json.dumps([self.issue(sha, horizon=horizon, manifest_sha=digest(folder / SOURCES))]).encode()
        return responses

    def test_published_vintage_survives_a_revision_on_a_separate_runner(self):
        first, sha, original = self.archive()
        older, legacy = self.readout("legacy", 12, H12, fake_fda(H12), scorer=legacy_score)
        self.assertTrue(older.exists())
        self.assertEqual(legacy["hypotheses"], original["hypotheses"])
        self.assertEqual(legacy["panels"]["12"],
                         {name: value for name, value in original["panels"]["12"].items() if name != "secondary"})
        secondary = original["panels"]["12"]["secondary"]
        self.assertEqual(secondary["arms"]["M3"]["diagnostic"]["rows"]["clear"], 20)
        self.assertEqual(secondary["distinct_event_drug_capture"]["M3"]["event_drugs"], 10)
        revision = fake_fda(H24, extra=(approval(16, "20271126"),))
        responses = self.published(first, sha)
        with patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]) as fetch:
            _, final = self.readout("second-runner", 24, H24, revision, repository=REPO, doi=DOI)
        self.assertIn(self.release_url, [call.args[0] for call in fetch.call_args_list])
        self.assertEqual(final["h3_input"]["status"], "FIRST_PUBLISHED")
        self.assertEqual(final["h3_input"]["results_sha256"], sha)
        self.assertEqual(final["h3_input"]["original"]["outcome_source_manifest_sha256"], digest(first / SOURCES))
        self.assertEqual(final["panels"]["12"], original["panels"]["12"])
        self.assertEqual(final["panels"]["24"]["event_rows"], 13)
        self.assertEqual(digest(first / RESULTS), sha)

    def test_r2_invocation_probe_cannot_select_formal_h3(self):
        first, sha, original = self.archive()
        sources = fake_fda(H24, extra=(approval(16, "20271126"),))
        responses = self.published(first, sha)
        with patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]) as fetch:
            for name, options, estimate in (
                ("original", {"archive": (first, sha)}, 1 / 3),
                ("omitted", {}, 0.25757575757575757),
                ("wrong-pin", {"archive": (first, "0" * 64)}, 0.25757575757575757),
                ("unreadable", {"archive": (self.root / "missing", sha)}, 0.25757575757575757),
                ("wrong-repo", {"repository": "example/other", "doi": DOI}, 0.25757575757575757),
            ):
                with self.subTest(name=name):
                    _, result = self.readout(name, 24, H24, sources, **options)
                    h3 = result["hypotheses"]["H3"]
                    self.assertEqual((h3["decision"], h3["reached"], h3["vintage_status"]),
                                     ("DESCRIPTIVE_ONLY", False, "UNVERIFIED_INPUT"))
                    self.assertAlmostEqual(h3["estimate"], estimate)
            fetch.assert_not_called()
            _, formal = self.readout("canonical", 24, H24, sources, repository=REPO, doi=DOI)
        h3 = formal["hypotheses"]["H3"]
        self.assertEqual((h3["decision"], h3["reached"]), ("PASS", True))
        self.assertEqual(h3["estimate"], original["hypotheses"]["H3"]["estimate"])
        self.assertEqual(h3["ci95"], original["hypotheses"]["H3"]["ci95"])

    def test_missing_original_uses_explicit_revised_vintage_and_old_issue_date(self):
        first, sha, original = self.archive()
        responses = self.published(first, sha)
        responses[self.release_url] = None
        edition = H24 + timedelta(days=2)
        with patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]):
            folder, final = self.readout("missing-runner", 24, edition, fake_fda(edition, extra=(approval(16, "20271126"),)),
                                         repository=REPO, doi=DOI)
        info = final["h3_input"]
        self.assertEqual((info["reason"], final["hypotheses"]["H3"]["vintage_status"]),
                         ("MISSING_ORIGINAL", "REVISED_VINTAGE"))
        self.assertEqual(info["original"]["scored_on_utc"], H12.isoformat())
        self.assertEqual(info["revised"]["fda_edition"], edition.isoformat())
        self.assertEqual(final["panels"]["12"]["event_rows"], 11)
        self.assertNotEqual(final["hypotheses"]["H3"]["estimate"], original["hypotheses"]["H3"]["estimate"])
        self.assertIn("REVISED_VINTAGE", (folder / "REPORT.md").read_text(encoding="utf-8"))
        record = info["discovery"]
        self.assertTrue(tracka_vintage.verified_absence(record, self.release.manifest_sha256))
        self.assertEqual([query["status"] for query in record["queries"]], ["FOUND", "NOT_FOUND", "FOUND"])
        self.assertFalse(tracka_vintage.verified_absence(record, "0" * 64))

    def test_corrupt_asset_or_mismatched_issue_digest_is_invalid(self):
        first, sha, _ = self.archive()
        for name in (RESULTS, SOURCES, self.issues_url):
            with self.subTest(name=name):
                responses = self.published(first, sha)
                if name == self.issues_url:
                    responses[name] = json.dumps([self.issue("0" * 64)]).encode()
                else:
                    responses[f"{self.assets}/{name}"] += b" "
                with patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]):
                    panel, evidence = tracka_vintage.discover(REPO, DOI, self.freeze, self.release.manifest_sha256,
                                                               self.root / "download")
                self.assertIsNone(panel)
                self.assertEqual(evidence["reason"], "INVALID_ORIGINAL")
                self.assertEqual(evidence["original"]["published_at_utc"], PUB_DATE)

    def test_invalid_original_blocks_formal_h3(self):
        first, sha, _ = self.archive()
        responses = self.published(first, sha)
        responses[f"{self.assets}/{RESULTS}"] = b"{}"
        with patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]):
            _, final = self.readout("invalid-runner", 24, H24, fake_fda(H24), repository=REPO, doi=DOI)
        self.assertEqual(final["h3_input"]["reason"], "INVALID_ORIGINAL")
        self.assertEqual(final["hypotheses"]["H3"]["vintage_status"], "UNVERIFIED_INPUT")
        self.assertEqual(final["hypotheses"]["H3"]["decision"], "DESCRIPTIVE_ONLY")

    def test_surviving_tag_blocks_revised_vintage(self):
        responses = self.empty_publications()
        responses[self.refs_url] = json.dumps([{"ref": f"refs/tags/{self.tag}"}]).encode()
        with patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]):
            _, result = self.readout("tag-survives", 24, H24, fake_fda(H24), repository=REPO, doi=DOI)
        self.assertIn("tag survives", result["h3_input"]["detail"])
        self.assertEqual(result["hypotheses"]["H3"]["decision"], "DESCRIPTIVE_ONLY")

    def test_publication_witnesses_and_release_only_recovery(self):
        first, sha, _ = self.archive()
        responses = self.published(first, sha)
        release = json.loads(responses[self.release_url])
        cases = {
            "release-only": (release["body"], [], None),
            "result-conflict": (release["body"].replace(sha, "0" * 64), [self.issue(sha)],
                                "Publication witnesses disagree for results.json"),
            "manifest-conflict": (release["body"], [self.issue(sha, manifest_sha="0" * 64)],
                                  "Publication witnesses disagree for outcome-source-manifest.json"),
            "manifest-against-embedded": (f"First result SHA-256 `{sha}`.",
                                          [self.issue(sha, manifest_sha="0" * 64)],
                                          "Publication digest disagrees with outcome-source-manifest.json"),
            "missing": ("", [], "Missing publication result digest"),
            "second-issue-conflict": (release["body"], [self.issue(sha), self.issue("0" * 64)],
                                      "Publication witnesses disagree for results.json"),
        }
        for name, (body, issues, error) in cases.items():
            with self.subTest(name=name):
                responses[self.release_url] = json.dumps({**release, "body": body}).encode()
                responses[self.issues_url] = json.dumps(issues).encode()
                with patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]):
                    panel, evidence = tracka_vintage.discover(REPO, DOI, self.freeze, self.release.manifest_sha256,
                                                               self.root / name)
                if error is None:
                    self.assertEqual(panel["event_rows"], 10)
                    self.assertEqual(evidence["original"]["results_sha256"], sha)
                else:
                    self.assertIsNone(panel)
                    self.assertEqual((evidence["reason"], evidence["detail"]), ("INVALID_ORIGINAL", error))

    def test_first_24_month_release_recovers_safety_and_bytes_after_artifact_expiry(self):
        # The first 24-month run recorded canonical absence at 12 months.
        responses = self.empty_publications()
        with patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]):
            transient, sha, first = self.archive(24, repository=REPO, doi=DOI)
        self.assertEqual(first["h3_input"]["status"], "REVISED_VINTAGE")
        self.assertTrue(first["hypotheses"]["H3"]["reached"])
        responses = self.published(transient, sha, horizon=24)
        assets = {name: (transient / name).read_bytes() for name in tracka_vintage.ASSETS}
        rmtree(transient.parent.parent)
        self.assertFalse(transient.exists())

        # The original 12-month release is later restored. The 24-month archive remains authoritative.
        first_12, sha_12, _ = self.archive()
        responses.update({url: data for url, data in self.published(first_12, sha_12).items()
                          if data is not None and self.tag in url})
        with (patch.object(tracka_vintage, "fetch", side_effect=lambda url, _: responses[url]) as fetch,
              patch.object(tracka_outcomes, "fetch_bytes", side_effect=AssertionError("Unexpected FDA fetch"))):
            status, folder = score(self.release, 24, self.root / "recovery", today=H24 + timedelta(days=2),
                                   repository=REPO, doi=DOI)
        self.assertEqual(status, "SCORED")
        self.assertNotIn(self.release_url, [call.args[0] for call in fetch.call_args_list])
        self.assertEqual({name: (folder / name).read_bytes() for name in assets}, assets)
        recovered = load(folder / RESULTS)
        self.assertEqual(recovered["h3_input"], first["h3_input"])
        safety = recovered["panels"]["24"]["secondary"]["arms"]["M3"]["diagnostic"]
        self.assertEqual((safety["missed_clear_events"], safety["auto_clear_safety"]), (12, "FAIL"))
        self.assertIsInstance(safety["missed_clear_ci95"][1], float)
        self.assertGreater(safety["missed_clear_ci95"][1], 0.6)

    def test_offline_verification_checks_linked_manifest_even_without_github(self):
        first, sha, _ = self.archive()
        panel, _ = tracka_vintage.verify_archive(first, self.release.manifest_sha256, self.freeze, sha)
        self.assertEqual(panel["event_rows"], 10)
        with (first / SOURCES).open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            tracka_vintage.verify_archive(first, self.release.manifest_sha256, self.freeze, sha)

    def test_http_404_is_absent_but_403_and_503_are_operational_errors(self):
        for code in (404, 403, 503):
            error = HTTPError(self.release_url, code, "synthetic status", {}, None)
            with patch.object(tracka_vintage, "urlopen", side_effect=error):
                if code == 404:
                    self.assertIsNone(tracka_vintage.fetch(self.release_url, 1024))
                else:
                    with self.assertRaises(HTTPError):
                        tracka_vintage.fetch(self.release_url, 1024)

    def test_pre_maturity_cannot_fetch_sources_or_first_publication(self):
        with patch.object(tracka_outcomes, "fetch_bytes", side_effect=AssertionError("unexpected FDA request")):
            status, folder = score(self.release, 24, self.root / "early", today=H12, repository=REPO, doi=DOI)
        self.assertEqual(status, "PENDING")
        self.assertNotIn("h3_input", load(folder / RESULTS))
