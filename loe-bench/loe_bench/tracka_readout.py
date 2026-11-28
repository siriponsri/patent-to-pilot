"""Run the prospective Track A readout with first-publication and secondary evidence."""

import argparse
from datetime import date, datetime, timezone
from pathlib import Path
from platform import python_version
from shutil import copyfile
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

import numpy as np

from . import tracka_capture, tracka_custody as custody, tracka_secondary, tracka_vintage
from .common import add_months
from .score_release import RECEIPT, RESULTS, RUN, SOURCES, first_result, release_directory, write_report
from .tracka_outcomes import fetch_outcomes
from .tracka_release import ARMS, FREEZE, HORIZONS, SCORER, T0, VERSION, digest, dump, load, read_release, require, verify_file
from .tracka_statistics import panel, sequence

READOUT_VERSION = "2.0.0"
EXIT = {"SCORED": 0, "RECOVERED": 0, "PENDING": 0, "BLOCKED_SOURCE": 3}
FIRST_12M_PANEL = (
    "Verified first 12-month panel, retained for later H3 use. The panel is descriptive only. "
    "H3 can be tested only at the 24-month readout (on or after 27 November 2028) and only if H1 and H2 both pass."
)


def unverified_input(reason, *, detail=None, original=None, discovery=None):
    return {"status": "UNVERIFIED_INPUT", "reason": reason, "detail": detail,
            "original": original or {}, "discovery": discovery,
            "kind": f"UNVERIFIED_INPUT ({reason}). The H3 estimate is descriptive only"}


def local_panel(archive, release_sha, freeze_sha):
    if archive is None:
        return None, unverified_input("CANONICAL_DISCOVERY_REQUIRED")
    folder, expected_sha = archive
    try:
        require(isinstance(expected_sha, str), "Supply a result SHA-256 with the local archive")
        earlier, identity = tracka_vintage.verify_archive(folder, release_sha, freeze_sha, expected_sha)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return None, unverified_input("LOCAL_ARCHIVE_UNVERIFIED", detail=str(exc))
    return earlier, unverified_input("LOCAL_ARCHIVE_ONLY", original=identity)


def recover_published(stage, out, horizon, identity):
    target = out / f"{horizon}m" / f"first-published-{identity['results_sha256']}"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        stage.rename(target)
    except OSError:
        if not target.is_dir():
            raise
        for name, sha in identity["archive_sha256"].items():
            verify_file(target, name, sha)
    return target


def result_witness_locators(discovery):
    release = f"https://github.com/{discovery['repository']}/releases/tag/{discovery['tag']}"
    locators = [release, *discovery.get("issue_urls", []), *(query["url"] for query in discovery["queries"])]
    return list(dict.fromkeys(locators))


def check_current_12m_witnesses(repository, doi, freeze_sha, release_sha, folder, published):
    """Check today's witnesses against the H3 reference in the published bytes."""
    earlier, discovery = tracka_vintage.discover(repository, doi, freeze_sha, release_sha, folder, horizon=12)
    reason, detail = discovery.get("reason"), discovery.get("detail")
    if earlier is None:
        status = "CURRENT_DISPUTE" if discovery.get("witness_dispute") else custody.HOLD
    else:
        reference = published["h3_input"]
        recorded = reference.get("original", {})
        observed = discovery["original"]
        if (reference.get("results_sha256") == recorded.get("results_sha256") == observed["results_sha256"]
                and recorded.get("outcome_source_manifest_sha256") == observed["outcome_source_manifest_sha256"]):
            status = "VERIFIED_CONSISTENT"
        else:
            status = "CURRENT_DISPUTE"
            reason = "PUBLISHED_H3_DIGEST_MISMATCH"
            detail = "The verified 12-month result or FDA source-manifest digest differs from the published H3 reference."
    return {"status": status, "reason": reason, "detail": detail, "discovery": discovery,
            "witness_locators": result_witness_locators(discovery),
            "custodian_reconciliation_required": status != "VERIFIED_CONSISTENT"}


def recovery_missing(capture, discovery):
    if discovery is None:
        return ["Recovery requires the registered repository, version DOI and freeze digest."]
    reason = discovery["reason"]
    capture_detail = capture.get("detail")
    if reason == "MISSING_ORIGINAL" and capture["status"] != "VERIFIED" and not capture_detail:
        return ["No verified first capture is available."]
    detail = discovery.get("detail", "No first published result was found.")
    missing = [f"First result discovery reported {reason}. {' '.join(detail.splitlines())}",
               *(f"Result witness or lookup at <{url}>." for url in result_witness_locators(discovery))]
    if capture_detail:
        missing.append(f"First capture verification reported {capture['status']}. {capture_detail}")
    return missing


def family_comparison(result, published, sources, published_sources):
    decisions = {}
    for name, first in published["hypotheses"].items():
        current = result["hypotheses"][name]
        decisions[name] = {field: {"published": first.get(field), "replay": current.get(field)}
                           for field in first.keys() | current.keys() if first.get(field) != current.get(field)}
    panels = {}
    for horizon in published["panels"].keys() | result["panels"].keys():
        first = published["panels"].get(horizon, {})
        current = result["panels"].get(horizon, {})
        panels[horizon] = sorted(key for key in first.keys() | current.keys() if first.get(key) != current.get(key))
    first_files = {item["file"]: item["sha256"] for item in published_sources["sources"]}
    replay_files = {item["file"]: item["sha256"] for item in sources["sources"]}
    return {"status": "COMPARED", "hypothesis_differences": decisions, "changed_panel_fields": panels,
            "fda_editions": {"published": published_sources["covered_through"], "replay": sources["covered_through"]},
            "changed_source_files": sorted(name for name in first_files.keys() | replay_files.keys()
                                           if first_files.get(name) != replay_files.get(name)),
            "source_manifest_matches": result["outcome_source_manifest_sha256"] ==
            published["outcome_source_manifest_sha256"]}


def replay_publication_lines(result):
    first = result["first_publication"]
    if result["horizon_months"] == 12:
        return [FIRST_12M_PANEL,
                f"[First published on {first['published_at_utc'][:10]} (UTC)]({first['release_url']})."]

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


def write_replay(path, result):
    first = result["first_publication"]
    comparison = result["replay_comparison"]
    lines = ["# Track A replay", "", *replay_publication_lines(result), "",
             f"[Verified local copy](../first-published-{first['results_sha256']}/REPORT.md).",
             f"First result SHA-256 `{first['results_sha256']}`.", ""]
    if comparison["status"] == "COMPARED":
        editions = comparison["fda_editions"]
        lines.append(f"FDA edition {editions['published']} → {editions['replay']}.")
        lines.append(f"Changed FDA source files: {', '.join(comparison['changed_source_files']) or 'none'}.")
        lines.append(f"FDA manifest digest matches the first publication: {comparison['source_manifest_matches']}.")
        for name, fields in comparison["hypothesis_differences"].items():
            lines.extend(["", f"## {name}", ""])
            lines.extend([f"- {field}: `{values['published']}` → `{values['replay']}`."
                          for field, values in sorted(fields.items())] or ["No hypothesis differences."])
        for horizon, fields in sorted(comparison["changed_panel_fields"].items()):
            lines.extend(["", f"Changed {horizon}-month panel fields: {', '.join(fields) or 'none'}."])
    else:
        lines.append(f"Comparison status `{comparison['status']}`. {comparison['detail']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_estimate_pp(estimate):
    return "unavailable" if estimate is None else f"{100 * estimate:+.2f} pp"


def write_run_report(path, result, published):
    write_report(path, result)
    if published is None:
        return

    if result["horizon_months"] == 12:
        role = "first published 12-month panel"
        h3 = published["panels"]["12"]["contrasts"]["M3-B1"]["recall"]
    else:
        role = "first published 24-month family"
        h3 = published["hypotheses"]["H3"]
    release_url = result["first_publication"]["release_url"]
    bounds = h3["ci95"]
    interval = "unavailable" if bounds is None else f"[{100 * bounds[0]:+.2f}, {100 * bounds[1]:+.2f}] pp"
    retained = f"Retained H3 estimate from the [{role}]({release_url})"
    context = [f"{retained} is {format_estimate_pp(h3['estimate'])} (95% interval {interval})."]
    report = path.read_text(encoding="utf-8")
    if result["status"] == "SCORED":
        for name, differences in result["replay_comparison"]["hypothesis_differences"].items():
            if estimates := differences.get("estimate"):
                current = format_estimate_pp(estimates["replay"])
                first = format_estimate_pp(estimates["published"])
                context.append(f"{name} differs in the current recomputation ({current}) "
                               f"from the first publication ({first}).")
        context.append("**Decision table, current recomputation (not used for inference)**")
        # The pinned renderer supplies this table header for every scored run.
        header = report.index("\n| Step | Contrast |") + 1
        report = report[:header] + "\n\n".join(context) + "\n\n" + report[header:]
    else:
        report += "\nNo replay calculation was completed.\n\n" + context[0] + "\n"
    path.write_text(report + "\n" + "\n".join(replay_publication_lines(result)) + "\n", encoding="utf-8")


def finish_run(stage, out, result, *, published=None):
    """Render integrated reports before hashing and promoting the run."""
    if result["family_status"] == "REPLAY":
        write_replay(stage / "REPLAY.md", result)

    status, horizon = result["status"], result["horizon_months"]
    destination = out / f"{horizon}m"
    destination.mkdir(parents=True, exist_ok=True)
    while True:
        numbers = [int(match[1]) for path in destination.iterdir() if (match := RUN.fullmatch(path.name))]
        version = max(numbers, default=0) + 1
        target = destination / f"run-{version:04d}"
        current, _ = first_result(out, result["release_sha256"], horizon)
        result.update(run_version=version, result_role="status" if status != "SCORED"
                      else "revision" if current else "first_scored",
                      first_scored_run=current.name if current else target.name if status == "SCORED" else None)
        dump(stage / RESULTS, result)
        write_run_report(stage / "REPORT.md", result, published)
        dump(stage / RECEIPT, {"files_sha256": {path.name: digest(path) for path in stage.iterdir()
                                               if path.is_file() and path.name != RECEIPT}})
        try:
            stage.rename(target)
            return status, target
        except OSError:
            if not target.exists():
                raise


def prepare_publication(run, target):
    """Stage the pinned bundle for the registered workflow's release creation step."""
    result = load(run / RESULTS)
    require(result["status"] == "SCORED" and result["family_status"] == "PROVISIONAL"
            and result.get("publication_eligible") is True
            and result["capture"]["status"] == "VERIFIED", "Run is ineligible for first Track A publication")
    files = load(run / RECEIPT)["files_sha256"]
    for name in (RESULTS, SOURCES, tracka_vintage.DRAWS):
        verify_file(run, name, files[name])
    target.mkdir()
    result.update(family_status="FORMAL", result_role="first_published")
    del result["publication_eligible"]
    for step in result["hypotheses"].values():
        step["decision"] = step.pop("sequence_decision")
        step["reached"] = step.pop("sequence_reached")
    for name in (SOURCES, tracka_vintage.DRAWS):
        copyfile(run / name, target / name)
    dump(target / RESULTS, result)
    (target / tracka_vintage.CHECKSUM).write_text(f"{digest(target / RESULTS)}  {RESULTS}\n", encoding="ascii")
    report = target / tracka_vintage.REPORT
    write_report(report, result)
    publication_status = (FIRST_12M_PANEL if result["horizon_months"] == 12 else
                          "These decisions are formal in the verified first GitHub release for this horizon.")
    with report.open("a", encoding="utf-8") as stream:
        capture = result["capture"]
        stream.write(f"\n[First verified FDA capture]({capture['release_url']}) "
                     f"SHA-256 `{capture['bundle_sha256']}`.\n"
                     f"Capture: {'Late' if capture['capture_late'] else 'On time'}. "
                     f"Scoring: {'Late' if result['scoring_late'] else 'On time'}.\n"
                     f"{publication_status}\n")


def score(release, horizon, out, *, today, snapshot=None, repository=None, doi=None, archive=None, recover=False):
    end = add_months(T0, horizon)
    freeze_sha = release.manifest["files_sha256"][FREEZE]
    result = {"status": "PENDING", "release_sha256": release.manifest_sha256,
              "freeze_manifest_sha256": freeze_sha, "scorer_version": VERSION, "readout_version": READOUT_VERSION,
              "t0": T0.isoformat(), "horizon_months": horizon, "maturity": end.isoformat(), "missing": [],
              "scored_on_utc": today.isoformat(), "family_status": "PROVISIONAL", "publication_eligible": False}
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
            return finish_run(stage, out, result)

        repository = repository or tracka_vintage.CANONICAL_REPOSITORY
        canonical = tracka_vintage.canonical_scope(repository, doi, freeze_sha)
        published, current, capture, replay = None, None, None, snapshot
        earlier, unverified, discovery = None, None, None
        if canonical:
            scope = custody.Scope(repository, tracka_vintage.DOI.fullmatch(doi)[1].lower(), freeze_sha, horizon, "capture")
            captured, capture = tracka_capture.discover(scope, Path(temporary) / "capture")
            result["capture"] = capture
            if snapshot is None:
                replay = captured
            retained = Path(temporary) / "first-published"
            first_panel, current = tracka_vintage.discover(repository, doi, freeze_sha, release.manifest_sha256,
                                                          retained, horizon=horizon, capture=capture)
            result["publication_discovery"] = current
            if first_panel is not None:
                target = recover_published(retained, out, horizon, current["original"])
                published = load(target / RESULTS)
                result.update(family_status="REPLAY", first_publication=current["original"])
                if horizon == 24:
                    result["current_12m_witness_check"] = check_current_12m_witnesses(
                        repository, doi, freeze_sha, release.manifest_sha256, Path(temporary) / "first-12", published)
            elif capture["status"] != "VERIFIED" or current["reason"] != "MISSING_ORIGINAL":
                result["family_status"] = custody.HOLD
            if horizon == 24 and not recover:
                if published is not None:
                    earlier = published["panels"]["12"]
                    discovery = published["h3_input"]["discovery"]
                elif archive is not None:
                    earlier, unverified = local_panel(archive, release.manifest_sha256, freeze_sha)
                else:
                    earlier, discovery = tracka_vintage.discover(repository, doi, freeze_sha, release.manifest_sha256,
                                                                 Path(temporary) / "first-12")
                    if earlier is None:
                        unverified = unverified_input(custody.HOLD, detail=discovery.get("detail"),
                                                      original=discovery["original"], discovery=discovery)
                        result["family_status"] = custody.HOLD
        elif horizon == 24:
            earlier, unverified = local_panel(archive, release.manifest_sha256, freeze_sha)

        if recover and published is not None:
            result.update(status="RECOVERED", replay_comparison={"status": "NOT_RUN_RECOVERY_ONLY",
                                                                 "detail": "Recovery retrieves the pinned bytes."})
            return finish_run(stage, out, result, published=published)
        if replay is None or recover:
            missing = recovery_missing(capture, current) if recover else [
                "No verified first capture or explicit local snapshot is available."]
            result.update(status="BLOCKED_SOURCE", family_status=custody.HOLD,
                          missing=missing)
            dump(stage / SOURCES, {"sources": [], "missing": result["missing"]})
            return finish_run(stage, out, result, published=published)

        locked = load(release.folder / SCORER)
        require((python_version(), np.__version__) == (locked["python"], locked["numpy"]),
                f"Use the locked CPython {locked['python']} and NumPy {locked['numpy']} for scoring")
        result["runtime"] = {"python": python_version(), "numpy": np.__version__}
        sources_dir = stage / "sources"
        sources_dir.mkdir()
        source_manifest, first_dates, witnesses = fetch_outcomes(release, end, today, sources_dir, replay)
        dump(stage / SOURCES, source_manifest)
        if first_dates is None:
            result.update(status="BLOCKED_SOURCE", missing=source_manifest["missing"])
            if published is not None:
                result["replay_comparison"] = {"status": "NOT_RUN_BLOCKED_SOURCE",
                                              "detail": "See the source coverage checks in REPORT.md."}
            return finish_run(stage, out, result, published=published)

        source_sha = digest(stage / SOURCES)
        panels, draws = {}, {}
        if horizon == 24:
            if unverified is not None:
                result["h3_input"] = unverified
            else:
                original = discovery["original"]
                result["h3_input"] = {"status": "FIRST_PUBLISHED", "original": original,
                                      "discovery": discovery, "results_sha256": original["results_sha256"],
                                      "kind": f"FIRST_PUBLISHED. First 12-month result SHA-256 {original['results_sha256']}."}
            if earlier is not None:
                panels[12] = earlier

        for h in HORIZONS:
            if h > horizon or h in panels:
                continue
            maturity = add_months(T0, h)
            # Missing keys incur administrative censoring at the horizon.
            dates = [first_dates.get(key, date.max) for key in release.keys]
            labels = [int(T0 < day <= maturity) for day in dates]
            elapsed = [(min(day, maturity) - T0).days for day in dates]
            panels[h], samples = panel(release.keys, release.scores[h], labels, elapsed)
            secondary, extra = tracka_secondary.summarize(release, h, labels, panels[h], samples)
            panels[h]["secondary"] = secondary
            draws.update({f"{h}m:{key}": value for key, value in samples.items()})
            draws.update({f"{h}m:secondary:{key}": value for key, value in extra.items()})
        np.savez_compressed(stage / "bootstrap-draws.npz", **draws)
        dump(stage / "event-witnesses.json", witnesses)
        hypotheses = sequence(panels, formal=release.manifest["analysis"] == "replication"
                              and result["family_status"] != custody.HOLD)
        if horizon == 24:
            if unverified:
                hypotheses["H3"].update(decision="DESCRIPTIVE_ONLY", reached=False)
            hypotheses["H3"]["vintage_status"] = result["h3_input"]["status"]
        result.update(status="SCORED", analysis=release.manifest["analysis"],
                      outcome_source_manifest_sha256=source_sha, arm_availability=load(release.folder / ARMS),
                      panels={str(h): values for h, values in panels.items()}, hypotheses=hypotheses,
                      scoring_late=today > end,
                      publication_eligible=canonical and current.get("reason") == "MISSING_ORIGINAL"
                      and capture["status"] == "VERIFIED" and snapshot is None and unverified is None)
        if published is not None:
            result["replay_comparison"] = family_comparison(result, published, source_manifest, load(target / SOURCES))
        for step in hypotheses.values():
            step.update(sequence_decision=step["decision"], sequence_reached=step["reached"],
                        decision="DESCRIPTIVE_ONLY" if result["family_status"] == custody.HOLD else result["family_status"],
                        reached=False)
        return finish_run(stage, out, result, published=published)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, help="Local directory or exact Zenodo version DOI")
    parser.add_argument("--horizon", required=True, type=int, choices=HORIZONS)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--freeze-sha256", required=True, help="Manifest hash from OSF update 4")
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--snapshot", type=Path, help="Archived sources/ directory for provisional scoring or replay")
    sources.add_argument("--recover", action="store_true", help="Retrieve the verified first publication without FDA scoring")
    prior = parser.add_mutually_exclusive_group()
    prior.add_argument("--repository", help="Discover the registered first publications in the canonical GitHub repository")
    prior.add_argument("--prior-12", type=Path, help="Archive directory for descriptive replay")
    parser.add_argument("--prior-12-sha256", help="Result checksum for descriptive replay")
    args = parser.parse_args(argv)
    if bool(args.prior_12) != bool(args.prior_12_sha256):
        parser.error("Supply --prior-12 and --prior-12-sha256 together")
    if args.horizon == 12 and args.prior_12:
        parser.error("Use --prior-12 with --horizon 24")
    if args.repository and not tracka_vintage.DOI.fullmatch(args.release):
        parser.error("Use the exact Zenodo DOI for GitHub discovery")
    try:
        with release_directory(args.release) as folder:
            release = read_release(folder, args.freeze_sha256)
            status, path = score(release, args.horizon, args.out, today=datetime.now(timezone.utc).date(),
                                 snapshot=args.snapshot, repository=args.repository, doi=args.release,
                                 archive=(args.prior_12, args.prior_12_sha256) if args.prior_12 else None,
                                 recover=args.recover)
    except (OSError, BadZipFile, ValueError, KeyError, TypeError) as exc:
        print(f"INVALID_RELEASE_OR_RUN: {exc}")
        return 1
    print(f"{status} {path}")
    return EXIT[status]


if __name__ == "__main__":
    raise SystemExit(main())
