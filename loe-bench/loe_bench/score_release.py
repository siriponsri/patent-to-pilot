"""Score a frozen Track A release directory or Zenodo version DOI."""

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
import json
from platform import python_version
import re
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

import numpy as np

from .common import add_months
from .tracka_outcomes import fetch_bytes, fetch_outcomes
from .tracka_release import FREEZE, HORIZONS, SCORER, T0, VERSION, digest, dump, load, read_release, require, verify_file
from .tracka_statistics import panel, sequence

RESULTS = "results.json"
SOURCES = "outcome-source-manifest.json"
RECEIPT = "run-manifest.json"
ARCHIVE = "track-a-release.zip"
DOI = re.compile(r"(?:https://doi\.org/)?(10\.5281/zenodo\.([0-9]+))", re.IGNORECASE)
RUN = re.compile(r"run-([0-9]{4,})")


@contextmanager
def release_directory(reference):
    local = Path(reference)
    if local.is_dir():
        yield local
        return
    match = DOI.fullmatch(reference)
    require(match, "Use a release directory or a Zenodo version DOI")
    doi, record_id = match.groups()
    base = f"https://zenodo.org/api/records/{record_id}"
    record = json.loads(fetch_bytes(base, 2 * 1024**2, "zenodo.org"))
    require(record["doi"].lower() == doi.lower() and str(record["id"]) == record_id,
            "Zenodo release must use an exact version DOI")
    archives = [item for item in record["files"] if item["key"] == ARCHIVE]
    require(len(archives) == 1, f"Version DOI must contain {ARCHIVE}")
    with TemporaryDirectory(prefix="track-a-release-") as temporary:
        folder = Path(temporary)
        filename = folder / ARCHIVE
        content_url = f"https://zenodo.org/records/{record_id}/files/{ARCHIVE}?download=1"
        filename.write_bytes(fetch_bytes(content_url, 128 * 1024**2, "zenodo.org"))
        with ZipFile(filename) as archive:
            flat = [item for item in archive.infolist() if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", item.filename)]
            require(len(flat) == len({item.filename.casefold() for item in flat})
                    and all(item.filename.casefold() != ARCHIVE for item in flat)
                    and sum(item.file_size for item in flat) <= 384 * 1024**2,
                    "Unexpected archive member names or size")
            for item in flat:
                (folder / item.filename).write_bytes(archive.read(item))
        yield folder


def verified_result(folder, release_sha, horizon):
    receipt = load(folder / RECEIPT)
    for name, sha in receipt["files_sha256"].items():
        verify_file(folder, name, sha)
    require({RESULTS, SOURCES, "bootstrap-draws.npz"} <= receipt["files_sha256"].keys(),
            "Prior run is missing scored artifacts")
    result = load(folder / RESULTS)
    require(result["status"] == "SCORED" and result["release_sha256"] == release_sha
            and result["scorer_version"] == VERSION and result["horizon_months"] == horizon,
            "Prior run must be scored with the identical release and scorer")
    for item in load(folder / SOURCES)["sources"]:
        verify_file(folder / "sources", item["file"], item["sha256"])
    return result


def first_result(out, release_sha, horizon):
    runs = [(int(match[1]), path) for path in (out / f"{horizon}m").glob("run-*")
            if (match := RUN.fullmatch(path.name))]
    for _, path in sorted(runs):
        manifest = load(path / RESULTS)
        if manifest["release_sha256"] == release_sha and manifest["status"] == "SCORED":
            return path, verified_result(path, release_sha, horizon)
    return None, None


def replay_publication_lines(result):
    first = result["first_publication"]
    lines = [f"The [first published aggregate]({first['release_url']}) was formal as verified at publication "
             f"on {first['published_at_utc'][:10]} (UTC)."]
    if check := result.get("current_12m_witness_check"):
        lines.extend(["", f"Current 12-month witness check `{check['status']}`."])
        if reason := check.get("reason"):
            lines.append(f"Discovery or comparison reason `{reason}`.")
        if detail := check.get("detail"):
            lines.append(" ".join(detail.splitlines()))
        if check["custodian_reconciliation_required"]:
            lines.append("Refer the current witness check to the custodian for reconciliation.")
            lines.extend(["", *(f"- <{locator}>" for locator in check["witness_locators"])])
    return lines


def write_report(path, result):
    lines = [f"# Track A · {result['horizon_months']} months", "", f"**{result['status']}**",
             "", f"Window ends {result['maturity']}. Release SHA-256 {result['release_sha256']}.",
             f"Run {result['run_version']}. Series {result['result_role']}."]
    if result["missing"]:
        lines.extend(["", "Coverage or release checks", "",
                      *(f"- {item}" for item in result["missing"])])
    if result.get("first_publication"):
        lines.extend(["", *replay_publication_lines(result)])
    if result["status"] == "SCORED":
        lines.extend(["", f"Analysis type {result['analysis']}."])
        if result.get("h3_input"):
            lines.extend(["", f"12-month input for H3. {result['h3_input']['kind']}."])
        lines.extend(["", "| Step | Contrast | Estimate, pp | 95% interval, pp | Decision |",
                      "| --- | --- | ---: | --- | --- |"])
        for name, step in result["hypotheses"].items():
            point, ci = step.get("estimate"), step.get("ci95")
            estimate = "—" if point is None else f"{100 * point:+.2f}"
            bounds = "—" if ci is None else f"[{100 * ci[0]:+.2f}, {100 * ci[1]:+.2f}]"
            lines.append(f"| {name} | {step['contrast']} | {estimate} | {bounds} | {step['decision']} |")
        summary = result["panels"][str(result["horizon_months"])]
        lines.extend(["", f"{summary['event_rows']} events among {summary['rows']} drugs. "
                          f"{summary['slots_per_arm']} review slots per arm.",
                      "", "The aggregate JSON includes the arm metrics, tie counts, and exploratory contrasts."])
        if result.get("first_formal_readout"):
            lines.append("The first 24-month readout preserves the formal sequence.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def commit_run(stage, out, result):
    destination = out / f"{result['horizon_months']}m"
    destination.mkdir(parents=True, exist_ok=True)
    while True:
        numbers = [int(match[1]) for path in destination.iterdir() if (match := RUN.fullmatch(path.name))]
        version = max(numbers, default=0) + 1
        target = destination / f"run-{version:04d}"
        current, _ = first_result(out, result["release_sha256"], result["horizon_months"])
        result.update(run_version=version, result_role="status" if result["status"] != "SCORED"
                      else "revision" if current else "first_scored",
                      first_scored_run=current.name if current else target.name if result["status"] == "SCORED" else None)
        dump(stage / RESULTS, result)
        write_report(stage / "REPORT.md", result)
        dump(stage / RECEIPT, {"files_sha256": {path.name: digest(path) for path in stage.iterdir()
                                               if path.is_file() and path.name != RECEIPT}})
        try:
            stage.rename(target)
            return target
        except OSError:
            if not target.exists():
                raise


def score(release, horizon, out, *, today, prior_12=None, snapshot=None):
    end = add_months(T0, horizon)
    result = {"status": "PENDING", "release_sha256": release.manifest_sha256,
              "freeze_manifest_sha256": release.manifest["files_sha256"][FREEZE],
              "scorer_version": VERSION, "t0": T0.isoformat(), "horizon_months": horizon,
              "maturity": end.isoformat(), "missing": []}
    out.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".staging-", dir=out) as temporary:
        stage = Path(temporary) / "output"
        stage.mkdir()
        if today < end:
            result["missing"].append(f"Calendar maturity is {end}; UTC date is {today}.")
        if release.manifest["freeze"] != "frozen":
            result["missing"].append("Prediction freeze is pending.")
        if result["missing"]:
            dump(stage / SOURCES, {"sources": [], "missing": result["missing"]})
            return result["status"], commit_run(stage, out, result)

        locked = load(release.folder / SCORER)
        require((python_version(), np.__version__) == (locked["python"], locked["numpy"]),
                f"Use the locked CPython {locked['python']} and NumPy {locked['numpy']} for scoring")
        result["runtime"] = {"python": python_version(), "numpy": np.__version__}
        first_24, previous_24 = first_result(out, release.manifest_sha256, 24)
        stored_panels = {}
        if horizon == 24:
            if prior_12 is not None:
                archived_12 = verified_result(prior_12, release.manifest_sha256, 12)
                prior_panel = archived_12["panels"]["12"]
                h3_input = {"kind": "supplied archived 12-month readout",
                            "results_sha256": digest(prior_12 / RESULTS)}
            elif previous_24 is not None:
                prior_panel = previous_24["panels"]["12"]
                h3_input = {"kind": "12-month input retained from the first 24-month readout",
                            "results_sha256": digest(first_24 / RESULTS)}
            else:
                local_12, archived_12 = first_result(out, release.manifest_sha256, 12)
                prior_panel = archived_12["panels"]["12"] if archived_12 else None
                h3_input = {"kind": "first local 12-month readout", "results_sha256": digest(local_12 / RESULTS)} \
                    if local_12 else {"kind": "late first 12-month readout from the 24-month snapshot"}
            result["h3_input"] = h3_input
            if prior_panel is not None:
                stored_panels[12] = prior_panel

        sources_dir = stage / "sources"
        sources_dir.mkdir()
        source_manifest, first_dates, witnesses = fetch_outcomes(release, end, today, sources_dir, snapshot)
        dump(stage / SOURCES, source_manifest)
        if first_dates is None:
            result.update(status="BLOCKED_SOURCE", missing=source_manifest["missing"])
            return result["status"], commit_run(stage, out, result)

        panels, draws = stored_panels, {}
        for h in HORIZONS:
            if h > horizon or h in panels:
                continue
            maturity = add_months(T0, h)
            dates = [first_dates.get(key, date.max) for key in release.keys]
            labels = [int(T0 < day <= maturity) for day in dates]
            elapsed = [(min(day, maturity) - T0).days for day in dates]
            panels[h], samples = panel(release.keys, release.scores[h], labels, elapsed)
            draws.update({f"{h}m:{key}": value for key, value in samples.items()})
        np.savez_compressed(stage / "bootstrap-draws.npz", **draws)
        dump(stage / "event-witnesses.json", witnesses)
        result.update(status="SCORED", analysis=release.manifest["analysis"],
                      arm_availability=load(release.folder / "arm-dictionary.json"),
                      panels={str(h): values for h, values in panels.items()},
                      hypotheses=sequence(panels, formal=release.manifest["analysis"] == "replication"))
        if horizon == 12 and previous_24 is not None:
            result["first_formal_readout"] = {"results_sha256": digest(first_24 / RESULTS),
                                              "hypotheses": previous_24["hypotheses"]}
        return result["status"], commit_run(stage, out, result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, help="Local directory or exact Zenodo version DOI")
    parser.add_argument("--horizon", required=True, type=int, choices=HORIZONS)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--freeze-sha256", help="Manifest hash from the OSF registration update")
    parser.add_argument("--prior-12", type=Path, help="Directory of the first completed 12-month readout")
    parser.add_argument("--snapshot", type=Path, help="Archived sources/ directory for an offline rerun")
    args = parser.parse_args(argv)
    if args.prior_12 and args.horizon != 24:
        parser.error("--prior-12 is used with --horizon 24")
    try:
        with release_directory(args.release) as folder:
            release = read_release(folder, args.freeze_sha256)
            status, path = score(release, args.horizon, args.out, today=datetime.now(timezone.utc).date(),
                                 prior_12=args.prior_12, snapshot=args.snapshot)
    except (OSError, BadZipFile, ValueError, KeyError, TypeError) as exc:
        print(f"INVALID_RELEASE_OR_RUN: {exc}")
        return 1
    print(f"{status} {path}")
    return {"SCORED": 0, "PENDING": 2, "BLOCKED_SOURCE": 3}[status]


if __name__ == "__main__":
    raise SystemExit(main())
