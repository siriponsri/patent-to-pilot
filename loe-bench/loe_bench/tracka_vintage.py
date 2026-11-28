"""Discover and verify the first published Track A readout at either horizon."""

import argparse
from datetime import date, datetime, timezone
import json
from os import environ
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

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


def verified_absence(evidence, release_sha):
    """Check the scope and observations of a discovery record from a trusted source."""
    repo, doi, freeze = (evidence.get(key) for key in ("repository", "doi", "freeze_manifest_sha256"))
    if not (canonical_scope(repo, doi, freeze) and evidence.get("schema_version") == 1 and
            evidence.get("reason") == "MISSING_ORIGINAL" and evidence.get("exact_tag_found") is False and
            evidence.get("horizon_months") == 12 and evidence.get("release_sha256") == release_sha):
        return False
    tag, _ = publication_scope(freeze, doi)
    api = f"https://api.github.com/repos/{repo}"
    observations = {(query["url"], query["status"]) for query in evidence["queries"]
                    if datetime.fromisoformat(query["queried_at_utc"]).tzinfo is not None}
    return evidence["tag"] == tag and {
        (f"{api}/issues?state=all&per_page=100&page=1", "FOUND"),
        (f"{api}/releases/tags/{tag}", "NOT_FOUND"),
        (f"{api}/git/matching-refs/tags/{tag}", "FOUND"),
    } <= observations


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


def note_dates(body):
    published = re.search(r"^First publication UTC (\S+)\.$", body, re.M)
    scored = re.search(r"Scoring started ([0-9]{4}-[0-9]{2}-[0-9]{2}) UTC", body)
    return {"published_at_utc": published[1] if published else None,
            "scored_on_utc": scored[1] if scored else None}


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
        require(vintage in ("FIRST_PUBLISHED", "REVISED_VINTAGE") and
                result["hypotheses"]["H3"]["vintage_status"] == vintage,
                "First 24-month result lacks a verified H3 vintage")
        if vintage == "REVISED_VINTAGE":
            require(verified_absence(result["h3_input"]["discovery"], release_sha),
                    "First 24-month result lacks the canonical absence record")
    return panel, {"results_sha256": result_sha, "outcome_source_manifest_sha256": source_sha,
                   "scored_on_utc": scored, "fda_edition": sources["covered_through"]}


def discover(repository, doi, freeze_sha, release_sha, folder, *, horizon=12):
    """Return a verified panel and evidence, or an explicit publication disposition."""
    require(REPO.fullmatch(repository) and DIGEST.fullmatch(release_sha), "Invalid publication repository or release pin")
    tag, record = publication_scope(freeze_sha, doi, horizon)
    api = f"https://api.github.com/repos/{repository}"
    original, queries = {}, []
    evidence = {"schema_version": 1, "repository": repository, "doi": DOI.fullmatch(doi)[1].lower(),
                "freeze_manifest_sha256": freeze_sha, "release_sha256": release_sha,
                "horizon_months": horizon, "tag": tag, "queries": queries, "original": original}

    def query(url, limit):
        at = datetime.now(timezone.utc).isoformat()
        data = fetch(url, limit)
        queries.append({"url": url, "queried_at_utc": at, "status": "NOT_FOUND" if data is None else "FOUND"})
        return data

    issues = scored_issues(query, api, record, horizon)
    pins = {name: [] for name in PIN_LABELS}
    evidence["publication_pins"] = pins
    evidence["issue_urls"] = [issue["html_url"] for issue in issues]
    disputes = []
    for issue in issues:
        locator = issue["html_url"]
        count = len(pins[RESULTS])
        disputes.extend(publish_pins(issue.get("body") or "", locator, pins))
        if len(pins[RESULTS]) == count:
            disputes.append(f"Missing publication result digest at {locator}")
    if issues:
        first = min(issues, key=lambda item: item["created_at"])
        original.update(note_dates(first.get("body") or ""), issue_url=first["html_url"])
    raw = query(f"{api}/releases/tags/{tag}", 2**20)
    if raw is None:
        refs = query(f"{api}/git/matching-refs/tags/{tag}", 2**20)
        require(refs is not None, "Cannot inspect the canonical Track A tag history")
        refs = json.loads(refs)
        require(isinstance(refs, list), "Unexpected canonical Track A tag history")
        evidence["exact_tag_found"] = any(ref["ref"] == f"refs/tags/{tag}" for ref in refs)
        disputes.extend(pin_disputes(pins))
        if disputes:
            return None, {**evidence, "reason": "DISPUTED", "detail": "\n".join(disputes)}
        if evidence["exact_tag_found"]:
            return None, {**evidence, "reason": "INVALID_ORIGINAL", "detail": "Publication tag survives without a release"}
        return None, {**evidence, "reason": "MISSING_ORIGINAL"}

    release_url = f"https://github.com/{repository}/releases/tag/{tag}"
    original["release_url"] = release_url
    try:
        release = json.loads(raw)
        notes = release.get("body") or ""
        original["published_at_utc"] = release.get("published_at")
        if not original.get("scored_on_utc"):
            original["scored_on_utc"] = note_dates(notes)["scored_on_utc"]
        require(not release["draft"] and release["tag_name"] == tag and
                datetime.fromisoformat(release["published_at"]).tzinfo is not None,
                "Unexpected GitHub publication identity")
        malformed_notes = publish_pins(notes, release_url, pins)
        disputes.extend(pin_disputes(pins))
        if disputes:
            return None, {**evidence, "reason": "DISPUTED", "detail": "\n".join(disputes + malformed_notes)}
        require(not malformed_notes, "\n".join(malformed_notes))
        require(pins[RESULTS], "Missing publication result digest")
        if horizon == 24:
            require(all(pins.values()), "Missing 24-month publication asset digest")

        files = {asset["name"]: asset for asset in release["assets"] if asset["state"] == "uploaded"}
        folder.mkdir(parents=True, exist_ok=True)
        for name, limit in ASSETS.items():
            require(name in files, f"Missing release asset: {name}")
            data = query(f"https://github.com/{repository}/releases/download/{tag}/{name}", limit)
            require(data is not None, f"Unavailable release asset: {name}")
            path = folder / name
            path.write_bytes(data)
            sha = digest(path)
            asset_sha = files[name].get("digest")
            require(asset_sha is None or asset_sha == f"sha256:{sha}", f"GitHub asset digest mismatch: {name}")
            if pins.get(name):
                require(pins[name][0]["sha256"] == sha, f"Publication digest disagrees with {name}")
        panel, identity = verify_archive(folder, release_sha, freeze_sha, pins[RESULTS][0]["sha256"], horizon=horizon)
        require(load(folder / RESULTS).get("family_status") == "FORMAL",
                "First publication does not contain a formal family")
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        return None, {**evidence, "reason": "INVALID_ORIGINAL", "detail": str(exc)}
    original.update(identity, archive_sha256={name: digest(folder / name) for name in ASSETS})
    return panel, evidence


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
