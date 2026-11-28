"""Discover and verify the first published 12-month Track A result."""

import argparse
from datetime import date, datetime
import json
from os import environ
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .score_release import DOI, RESULTS, SOURCES
from .tracka_release import DIGEST, T0, VERSION, digest, load, require, verify_file

CHECKSUM = "results.sha256"
ASSETS = {RESULTS: 2**21, CHECKSUM: 1024, SOURCES: 2**21}
MATURITY_12 = "2027-11-27"
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def publication_scope(freeze_sha, doi):
    match = DOI.fullmatch(doi)
    require(match and DIGEST.fullmatch(freeze_sha), "Invalid first-readout publication scope")
    record = f"{freeze_sha}:{match[2]}"
    return f"track-a-12m-{match[2]}-{freeze_sha}", record


def fetch(url, limit):
    request = Request(url, headers={"User-Agent": "loe-bench-tracka-readout"})
    if url.startswith("https://api.github.com/") and (token := environ.get("GH_TOKEN")):
        request.add_unredirected_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read(limit + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    require(len(data) <= limit, "First-readout response exceeds the expected size")
    return data


def iso_day(value):
    return date.fromisoformat(value).isoformat()


def original_dates(issue):
    if issue is None:
        return {}
    body = issue.get("body") or ""
    published = re.search(r"^First publication UTC (\S+)\.$", body, re.M)
    scored = re.search(r"Scoring started ([0-9]{4}-[0-9]{2}-[0-9]{2}) UTC", body)
    checksum = re.search(r"^First result SHA-256 `([0-9a-f]{64})`", body, re.M)
    return {"published_at_utc": published[1] if published else None,
            "scored_on_utc": scored[1] if scored else None,
            "issue_url": issue.get("html_url"), "issue_results_sha256": checksum[1] if checksum else None}


def first_issue(repository, record):
    marker = f"<!-- tracka:12:SCORED:{record} -->"
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repository}/issues?state=all&per_page=100&page={page}"
        raw = fetch(url, 32 * 2**20)
        require(raw is not None, "Cannot inspect the canonical Track A issue history")
        issues = json.loads(raw)
        for issue in issues:
            trusted = (issue["user"]["login"] == "github-actions[bot]" or
                       issue["author_association"] in ("OWNER", "MEMBER", "COLLABORATOR"))
            if (trusted and issue["title"] == "Track A 12-month readout" and "pull_request" not in issue
                    and marker in (issue.get("body") or "").splitlines()):
                return issue
        if len(issues) < 100:
            return None
        page += 1


def verify_archive(folder, release_sha, freeze_sha, expected_sha=None):
    checksum_path = folder / CHECKSUM
    require(checksum_path.is_file() and not checksum_path.is_symlink(), "Missing first-readout SHA-256 file")
    checksum = checksum_path.read_text(encoding="ascii").strip().split()
    require(len(checksum) == 2 and checksum[1] == RESULTS and DIGEST.fullmatch(checksum[0]),
            "Invalid first-readout SHA-256 file")
    result_sha = checksum[0]
    require(expected_sha is None or expected_sha == result_sha, "First result differs from its publication digest")
    result = load(verify_file(folder, RESULTS, result_sha))
    require(result["status"] == "SCORED" and result["release_sha256"] == release_sha
            and result["freeze_manifest_sha256"] == freeze_sha and result["scorer_version"] == VERSION
            and result["horizon_months"] == 12 and result["maturity"] == MATURITY_12
            and result["t0"] == T0.isoformat(), "First result does not match the frozen release and 12-month horizon")
    source_sha = result["outcome_source_manifest_sha256"]
    sources = load(verify_file(folder, SOURCES, source_sha))
    require(sources["sources"] and not sources["missing"] and
            iso_day(sources["covered_through"]) >= MATURITY_12 and
            all(DIGEST.fullmatch(item["sha256"]) for item in sources["sources"]),
            "First result does not identify a complete FDA source manifest")
    scored = iso_day(result["scored_on_utc"])
    require(scored >= MATURITY_12, "First result was scored before maturity")
    panel = result["panels"]["12"]
    contrast = panel["contrasts"]["M3-B1"]["recall"]
    require("estimate" in contrast and "ci95" in contrast, "First result lacks the registered H3 estimate")
    return panel, {"results_sha256": result_sha, "outcome_source_manifest_sha256": source_sha,
                   "scored_on_utc": scored, "fda_edition": sources["covered_through"]}


def discover(repository, doi, freeze_sha, release_sha, folder, *, check_issue=True):
    """Return a verified panel, or the reason and surviving identity of its absence."""
    require(REPO.fullmatch(repository), "Use an owner/repository GitHub name")
    tag, record = publication_scope(freeze_sha, doi)
    issue = first_issue(repository, record) if check_issue else None
    original = original_dates(issue)
    raw = fetch(f"https://api.github.com/repos/{repository}/releases/tags/{tag}", 2**20)
    if raw is None:
        return None, {"reason": "MISSING_ORIGINAL", "original": original}
    release = json.loads(raw)
    if release["draft"]:
        return None, {"reason": "MISSING_ORIGINAL", "original": original}
    original["release_url"] = f"https://github.com/{repository}/releases/tag/{tag}"
    original["published_at_utc"] = release["published_at"]
    notes = original_dates(release)
    if not original.get("scored_on_utc"):
        original["scored_on_utc"] = notes.get("scored_on_utc")
    try:
        require(release["tag_name"] == tag and datetime.fromisoformat(release["published_at"]).tzinfo is not None,
                "Unexpected GitHub publication identity")
        files = {asset["name"]: asset for asset in release["assets"] if asset["state"] == "uploaded"}
        folder.mkdir(parents=True, exist_ok=True)
        for name, limit in ASSETS.items():
            require(name in files, f"Missing release asset: {name}")
            data = fetch(f"https://github.com/{repository}/releases/download/{tag}/{name}", limit)
            require(data is not None, f"Unavailable release asset: {name}")
            path = folder / name
            path.write_bytes(data)
            asset_sha = files[name].get("digest")
            if asset_sha is not None:
                require(asset_sha == f"sha256:{digest(path)}", f"GitHub asset digest mismatch: {name}")
        panel, identity = verify_archive(folder, release_sha, freeze_sha,
                                         original.get("issue_results_sha256") or notes.get("issue_results_sha256"))
    except (KeyError, TypeError, ValueError) as exc:
        return None, {"reason": "INVALID_ORIGINAL", "detail": str(exc), "original": original}
    return panel, {"original": {**original, **identity}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--doi", required=True)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--release-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    _, evidence = discover(args.repository, args.doi, args.freeze_sha256, args.release_sha256, args.out,
                           check_issue=False)
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
