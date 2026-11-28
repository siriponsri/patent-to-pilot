"""Discover and verify the first published Track A readout at either horizon."""

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import re
from zipfile import BadZipFile

from . import tracka_capture, tracka_custody as custody
from .common import add_months
from .score_release import DOI, RESULTS, SOURCES
from .tracka_release import DIGEST, HORIZONS, T0, VERSION, digest, load, require, verify_file

CHECKSUM = "results.sha256"
DRAWS = "bootstrap-draws.npz"
REPORT = "REPORT.md"
ASSETS = {RESULTS: 2**21, CHECKSUM: 1024, SOURCES: 2**21, DRAWS: 64 * 2**20, REPORT: 2**21}
PIN_LABELS = {RESULTS: "First result SHA-256", SOURCES: "FDA source manifest SHA-256",
              DRAWS: "Bootstrap draws SHA-256", REPORT: "Report SHA-256"}
MATURITY_12 = add_months(T0, 12).isoformat()
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
CANONICAL_REPOSITORY = "siriponsri/patent-to-pilot"
CANONICAL_DOI = "10.5281/zenodo.24629100"
CANONICAL_FREEZE = "8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d"


def canonical_scope(repository, doi, freeze_sha):
    match = DOI.fullmatch(doi or "")
    return (repository == CANONICAL_REPOSITORY and match is not None and match[1].lower() == CANONICAL_DOI
            and freeze_sha == CANONICAL_FREEZE)


def publication_scope(freeze_sha, doi, horizon=12):
    match = DOI.fullmatch(doi or "")
    require(match and DIGEST.fullmatch(freeze_sha) and horizon in HORIZONS, "Invalid first-readout publication scope")
    return f"track-a-{horizon}m-{match[2]}-{freeze_sha}", f"{freeze_sha}:{match[2]}"


def publish_pins(body, locator, pins):
    errors = []
    for filename, label in PIN_LABELS.items():
        for line in body.splitlines():
            if line.startswith(label):
                suffix = re.fullmatch(r" `([0-9a-f]{64})`\.", line[len(label):])
                if suffix:
                    pins[filename].append({"locator": locator, "sha256": suffix[1]})
                else:
                    errors.append(f"Malformed {label} at {locator}")
    return errors


def pin_disputes(pins):
    return [f"Publication witnesses disagree for {name}" for name, witnesses in pins.items()
            if len({item["sha256"] for item in witnesses}) > 1]


def scored_issues(query, api, record, horizon):
    marker = f"<!-- tracka:{horizon}:SCORED:{record} -->"
    page = 1
    issues = []
    while True:
        raw = query(f"{api}/issues?state=all&per_page=100&page={page}", 32 * 2**20)
        require(raw is not None, "Cannot inspect the canonical Track A issue history")
        batch = json.loads(raw)
        require(isinstance(batch, list), "Unexpected canonical Track A issue history")
        for issue in batch:
            trusted = (issue["user"]["login"] == "github-actions[bot]" or
                       issue["author_association"] in ("OWNER", "MEMBER", "COLLABORATOR"))
            if (trusted and issue["title"] == f"Track A {horizon}-month readout" and "pull_request" not in issue
                    and marker in (issue.get("body") or "").splitlines()):
                issues.append(issue)
        if len(batch) < 100:
            return issues
        page += 1


def verify_archive(folder, release_sha, freeze_sha, expected_sha=None, *, horizon=12):
    checksum_path = folder / CHECKSUM
    require(checksum_path.is_file() and not checksum_path.is_symlink(), "Missing first-readout SHA-256 file")
    checksum = checksum_path.read_text(encoding="ascii").strip().split()
    require(len(checksum) == 2 and checksum[1] == RESULTS and DIGEST.fullmatch(checksum[0]),
            "Invalid first-readout SHA-256 file")
    result_sha = checksum[0]
    require(expected_sha is None or expected_sha == result_sha,
            "First result checksum file disagrees with its publication digest")
    result = load(verify_file(folder, RESULTS, result_sha))
    maturity = add_months(T0, horizon).isoformat()
    require(result["status"] == "SCORED" and result["release_sha256"] == release_sha
            and result["freeze_manifest_sha256"] == freeze_sha and result["scorer_version"] == VERSION
            and result["horizon_months"] == horizon and result["maturity"] == maturity
            and result["t0"] == T0.isoformat(), "First result does not match the frozen release and horizon")
    source_sha = result["outcome_source_manifest_sha256"]
    sources = load(verify_file(folder, SOURCES, source_sha))
    require(sources["sources"] and not sources["missing"] and
            date.fromisoformat(sources["covered_through"]).isoformat() >= maturity and
            all(DIGEST.fullmatch(item["sha256"]) for item in sources["sources"]),
            "First result does not identify a complete FDA source manifest")
    scored = date.fromisoformat(result["scored_on_utc"]).isoformat()
    require(scored >= maturity, "First result was scored before maturity")
    panel = result["panels"][str(horizon)]
    if horizon == 12:
        contrast = panel["contrasts"]["M3-B1"]["recall"]
        require("estimate" in contrast and "ci95" in contrast, "First result lacks the registered H3 estimate")
    else:
        vintage = result["h3_input"]["status"]
        require(vintage == "FIRST_PUBLISHED" and
                result["hypotheses"]["H3"]["vintage_status"] == vintage,
                "First 24-month result lacks a verified H3 vintage")
    return panel, {"results_sha256": result_sha, "outcome_source_manifest_sha256": source_sha,
                   "scored_on_utc": scored, "fda_edition": sources["covered_through"]}


def discover(repository, doi, freeze_sha, release_sha, folder, *, horizon=12, capture=None):
    """Return the first independently verified panel, or a continuity disposition."""
    require(canonical_scope(repository, doi, freeze_sha) and DIGEST.fullmatch(release_sha),
            "Invalid canonical publication identity")
    tag, record = publication_scope(freeze_sha, doi, horizon)
    scope = custody.Scope(repository, DOI.fullmatch(doi)[1].lower(), freeze_sha, horizon, "result")
    original, queries = {}, []
    evidence = {"schema_version": 2, **vars(scope), "release_sha256": release_sha,
                "tag": tag, "queries": queries, "original": original}

    def query(url, limit, **kwargs):
        data = custody.fetch(url, limit, **kwargs)
        # The attestation service can return expiring, signed bundle URLs.
        if url.startswith(scope.api + "/") and not kwargs:
            queries.append({"url": url, "queried_at_utc": datetime.now(timezone.utc).isoformat(),
                            "status": "NOT_FOUND" if data is None else "FOUND"})
        return data

    try:
        issues = scored_issues(query, scope.api, record, horizon)
        pins = {name: [] for name in PIN_LABELS}
        evidence.update(publication_pins=pins, issue_urls=[issue["html_url"] for issue in issues])
        disputes = []
        for issue in issues:
            locator = issue["html_url"]
            count = len(pins[RESULTS])
            disputes.extend(publish_pins(issue.get("body") or "", locator, pins))
            if len(pins[RESULTS]) == count:
                disputes.append(f"Missing publication result digest at {locator}")
        disputes.extend(pin_disputes(pins))
        require(not disputes, "\n".join(disputes))
        with TemporaryDirectory() as temp:
            received = Path(temp)
            archive = custody.inspect(scope, received, query=query)
            evidence["custody"] = archive
            if archive["status"] == "EMPTY" and not issues:
                return None, {**evidence, "reason": "MISSING_ORIGINAL"}
            require(archive["status"] == "VERIFIED",
                    archive.get("detail", "Publication witnesses survive without an attested result"))
            custody.unpack(received / scope.archive, folder, lambda names: names == ASSETS.keys())
            panel, identity = verify_archive(folder, release_sha, freeze_sha, horizon=horizon)
            result = load(folder / RESULTS)
            require(result["family_status"] == "FORMAL", "First publication does not contain a formal family")
            if capture is None:
                _, capture = tracka_capture.discover(scope, received / "capture", query=query)
            require(capture["status"] == "VERIFIED"
                    and result["capture"]["bundle_sha256"] == capture["bundle_sha256"]
                    and custody.utc_time(archive["provenance"]["signed_at_utc"]) >=
                    custody.utc_time(capture["published_at_utc"]),
                    "First result is not bound to its verified published capture")
            require(all(capture["source_sha256"].get(entry["file"]) == entry["sha256"]
                        for entry in load(folder / SOURCES)["sources"]),
                    "First result used bytes outside its capture")
            asset_hashes = {name: digest(folder / name) for name in ASSETS}
            for name, witnesses in pins.items():
                require(all(item["sha256"] == asset_hashes[name] for item in witnesses),
                        f"Publication issue digest disagrees with {name}")
            original.update(identity, archive_sha256=asset_hashes, **{
                key: archive[key] for key in ("release_url", "published_at_utc", "provenance", "bundle_sha256")})
            return panel, evidence
    except (OSError, KeyError, TypeError, ValueError, BadZipFile) as exc:
        return None, {**evidence, "reason": custody.HOLD, "detail": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--doi", required=True)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--release-sha256", required=True)
    parser.add_argument("--horizon", type=int, choices=HORIZONS, default=12)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    _, evidence = discover(args.repository, args.doi, args.freeze_sha256, args.release_sha256, args.out,
                           horizon=args.horizon)
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
