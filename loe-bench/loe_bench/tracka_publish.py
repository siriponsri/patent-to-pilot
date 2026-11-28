"""Stage and publish first Track A bundles from the authorized Actions workflow."""

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from os import environ
from pathlib import Path
from subprocess import TimeoutExpired, run
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

from . import tracka_capture, tracka_custody as custody, tracka_vintage
from .score_release import RESULTS, SOURCES, release_directory
from .tracka_readout import prepare_publication, score
from .tracka_release import HORIZONS, digest, load, read_release, require


def output(key, value):
    with Path(environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
        stream.write(f"{key}={value}\n")


def summary(text):
    with Path(environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
        stream.write(text + "\n")


def gh(*args):
    response = run(["gh", *args], capture_output=True, text=True, check=False, timeout=180)
    require(response.returncode == 0, f"GitHub operation failed: gh {' '.join(args[:2])}")
    return response.stdout


def assert_workflow(scope):
    require(tracka_vintage.canonical_scope(scope.repository, scope.doi, scope.freeze)
            and scope.repository == environ.get("GITHUB_REPOSITORY")
            and scope.identity == environ.get("GITHUB_WORKFLOW_REF")
            and custody.REF == environ.get("GITHUB_REF") and environ.get("TRACKA_CONTINUITY_HOLD") != "true",
            "Track A publishing requires the canonical workflow and open continuity gate")


def create_draft(scope, area):
    path = area / scope.archive
    gh("release", "create", scope.tag, "--draft", "--latest=false", "--repo", scope.repository,
       "--title", f"Track A first {scope.horizon}-month {scope.kind}",
       "--notes", custody.PIN + digest(path), str(path))


def stage_subjects(scope, area, evidence):
    witness = area / "track-a-scope.json"
    witness.write_bytes(scope.witness())
    archive = area / scope.archive
    output("checksums", area / "subjects.sha256")
    (area / "subjects.sha256").write_text(
        f"{digest(witness)}  {witness.name}\n{digest(archive)}  {archive.name}\n", encoding="ascii")
    output("attest", "false" if evidence["attestations"] else "true")
    output("publish", "true")


def result_issues(scope):
    _, record = tracka_vintage.publication_scope(scope.freeze, scope.doi, scope.horizon)
    return tracka_vintage.scored_issues(custody.fetch, scope.api, record, scope.horizon)


def stage_capture(scope, area, started):
    state = custody.inspect(scope, area, include_draft=True)
    if state["status"] == "VERIFIED":
        return
    if state["status"] == "EMPTY":
        with TemporaryDirectory() as temp:
            result_scope = replace(scope, kind="result")
            result = custody.inspect(result_scope, Path(temp), include_draft=True)
            require(result["status"] == "EMPTY" and not result_issues(result_scope),
                    "A result witness survives without a verified capture")
        tracka_capture.build(scope, started, area / scope.archive)
        create_draft(scope, area)
    else:
        require(state["status"] == "DRAFT", state.get("detail", custody.HOLD))
        with TemporaryDirectory() as temporary:
            tracka_capture.restore(scope, area / scope.archive, Path(temporary) / "snapshot")
    stage_subjects(scope, area, state)


def draft_result(scope, bundle, folder, release_sha, capture):
    custody.unpack(bundle, folder, lambda names: names == tracka_vintage.ASSETS.keys())
    tracka_vintage.verify_archive(folder, release_sha, scope.freeze, horizon=scope.horizon)
    result = load(folder / RESULTS)
    require(result["family_status"] == "FORMAL" and capture["status"] == "VERIFIED"
            and result["capture"]["bundle_sha256"] == capture["bundle_sha256"]
            and all(capture["source_sha256"].get(entry["file"]) == entry["sha256"]
                    for entry in load(folder / SOURCES)["sources"]), "Result draft differs from its verified capture")
    return result


def stage_result(scope, area, today):
    state = custody.inspect(scope, area, include_draft=True)
    with release_directory(scope.doi) as folder:
        release = read_release(folder, scope.freeze)
        if state["status"] == "DRAFT":
            require(not result_issues(scope), "A scored issue survives alongside the result draft")
            with TemporaryDirectory() as temporary:
                received = Path(temporary)
                _, capture = tracka_capture.discover(scope, received / "capture")
                draft_result(scope, area / scope.archive, received / "result", release.manifest_sha256, capture)
        else:
            _, scored = score(release, scope.horizon, area / "readout", today=today)
            result = load(scored / RESULTS)
            if not result["publication_eligible"]:
                summary(f"Family status: {result['family_status']}.")
                summary((scored / tracka_vintage.REPORT).read_text(encoding="utf-8"))
                return
            require(state["status"] == "EMPTY", "Track A result custody changed before draft creation")
            prepared = area / "result"
            prepare_publication(scored, prepared)
            custody.pack(prepared, tracka_vintage.ASSETS, area / scope.archive)
            create_draft(scope, area)
        stage_subjects(scope, area, state)


def publish(scope, area):
    with TemporaryDirectory() as temporary:
        folder = Path(temporary)
        state = custody.inspect(scope, folder, include_draft=True)
        require(state["status"] == "DRAFT" and state["attestations"]
                and digest(area / scope.archive) == state["bundle_sha256"],
                state.get("detail", "Track A draft or verified attestation is missing"))
        provenance = state["attestations"][0]
        notes = folder / "notes.md"
        contents = [custody.PIN + state["bundle_sha256"], custody.PROVENANCE + json.dumps(provenance, sort_keys=True),
                    f"[Workflow run](https://github.com/{scope.repository}/actions/runs/{provenance['run_id']})."]
        if scope.kind == "capture":
            _, manifest = tracka_capture.restore(scope, folder / scope.archive, folder / "capture")
            started = custody.utc_time(manifest["capture_started_utc"])
            require(started <= custody.utc_time(provenance["signed_at_utc"]), "Capture was signed before it started")
            contents.append(f"Capture started {started.isoformat()}. Edition dates: {manifest['editions']}.")
        else:
            require(not result_issues(scope), "A scored issue survives alongside the result draft")
            _, capture = tracka_capture.discover(scope, folder / "capture")
            require(capture["status"] == "VERIFIED" and custody.utc_time(provenance["signed_at_utc"]) >=
                    custody.utc_time(capture["published_at_utc"]), "Result attestation predates its published capture")
            with release_directory(scope.doi) as frozen:
                release = read_release(frozen, scope.freeze)
                prepared = folder / "result"
                draft_result(scope, folder / scope.archive, prepared, release.manifest_sha256, capture)
            contents.append((prepared / tracka_vintage.REPORT).read_text(encoding="utf-8"))
        notes.write_text("\n\n".join(contents) + "\n", encoding="utf-8")
        gh("api", "--method", "PATCH", f"repos/{scope.repository}/releases/{state['release_id']}",
           "-F", "draft=false", "-F", f"body=@{notes}", "-f", f"target_commitish={provenance['commit']}")


def finalize_result(scope):
    with TemporaryDirectory() as temporary, release_directory(scope.doi) as frozen:
        release = read_release(frozen, scope.freeze)
        _, evidence = tracka_vintage.discover(scope.repository, scope.doi, scope.freeze, release.manifest_sha256,
                                             Path(temporary) / "result", horizon=scope.horizon)
        if evidence.get("reason") == "MISSING_ORIGINAL":
            return
        require("reason" not in evidence, evidence.get("detail", custody.HOLD))
        first = evidence["original"]
        summary(f"[Verified first {scope.horizon}-month Track A release]({first['release_url']}).")
        if not evidence["issue_urls"]:
            _, record = tracka_vintage.publication_scope(scope.freeze, scope.doi, scope.horizon)
            pins = "\n\n".join(f"{label} `{first['archive_sha256'][name]}`."
                                for name, label in tracka_vintage.PIN_LABELS.items())
            body = (f"<!-- tracka:{scope.horizon}:SCORED:{record} -->\n\n"
                    f"Scoring started {first['scored_on_utc']} UTC.\n\n"
                    f"First publication UTC {first['published_at_utc']}.\n\n{pins}\n\n"
                    f"[First attested Track A result]({first['release_url']}).")
            gh("api", "--method", "POST", f"repos/{scope.repository}/issues",
               "-f", f"title=Track A {scope.horizon}-month readout", "-f", f"body={body}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("stage", "publish", "finalize"))
    parser.add_argument("kind", choices=("capture", "result"))
    parser.add_argument("area", type=Path)
    args = parser.parse_args()
    try:
        scope = custody.Scope(environ["GITHUB_REPOSITORY"], environ["RELEASE_DOI"].removeprefix("https://doi.org/"),
                              environ["FREEZE_SHA256"], int(environ["HORIZON"]), args.kind)
        assert_workflow(scope)
        started = datetime.now(timezone.utc)
        if started.date() < scope.maturity:
            summary(f"Calendar maturity is {scope.maturity} UTC.")
            return 0
        args.area.mkdir(parents=True, exist_ok=True)
        if args.operation == "stage":
            if args.kind == "capture":
                stage_capture(scope, args.area, started)
            else:
                stage_result(scope, args.area, started.date())
        elif args.operation == "publish":
            publish(scope, args.area)
        else:
            finalize_result(scope)
    except (OSError, KeyError, TypeError, ValueError, BadZipFile, TimeoutExpired) as exc:
        summary(f"{custody.HOLD}. {exc}")
        print(f"{custody.HOLD}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
