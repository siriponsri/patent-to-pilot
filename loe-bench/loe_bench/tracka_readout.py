"""Run the prospective Track A readout with first-publication and secondary evidence."""

import argparse
from datetime import date, datetime, timezone
from pathlib import Path
from platform import python_version
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

import numpy as np

from . import tracka_secondary, tracka_vintage
from .common import add_months
from .score_release import SOURCES, commit_run, release_directory
from .tracka_outcomes import fetch_outcomes
from .tracka_release import ARMS, FREEZE, HORIZONS, SCORER, T0, VERSION, digest, dump, load, read_release, require, verify_file
from .tracka_statistics import panel, sequence

READOUT_VERSION = "1.1.0"
EXIT = {"SCORED": 0, "PENDING": 2, "BLOCKED_SOURCE": 3}


def h3_provenance(evidence, today, source_manifest, source_sha):
    original = evidence["original"]
    vintage = {"original": original, "original_maturity": tracka_vintage.MATURITY_12, "discovery": evidence}
    if "reason" not in evidence:
        return {**vintage, "status": "FIRST_PUBLISHED",
                "kind": f"FIRST_PUBLISHED. Scored {original['scored_on_utc']} UTC with FDA edition "
                        f"{original['fda_edition']}. Result SHA-256 {original['results_sha256']}",
                "results_sha256": original["results_sha256"]}
    revised = {"scored_on_utc": today.isoformat(), "fda_edition": source_manifest["covered_through"],
               "outcome_source_manifest_sha256": source_sha}
    original_day = original.get("scored_on_utc") or original.get("published_at_utc") or "unknown"
    return {**vintage, "status": "REVISED_VINTAGE", "reason": evidence["reason"],
            "revised": revised, **({"detail": evidence["detail"]} if "detail" in evidence else {}),
            "kind": f"REVISED_VINTAGE ({evidence['reason']}). Original date {original_day} "
                    f"(12-month maturity {tracka_vintage.MATURITY_12}). Revised scoring date {today} UTC, "
                    f"FDA edition {revised['fda_edition']}"}


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


def recover_published(stage, out, identity):
    target = out / "24m" / f"first-published-{identity['results_sha256']}"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        stage.rename(target)
    except OSError:
        if not target.is_dir():
            raise
        for name, sha in identity["archive_sha256"].items():
            verify_file(target, name, sha)
    return "SCORED", target


def score(release, horizon, out, *, today, snapshot=None, repository=None, doi=None, archive=None):
    end = add_months(T0, horizon)
    freeze_sha = release.manifest["files_sha256"][FREEZE]
    result = {"status": "PENDING", "release_sha256": release.manifest_sha256,
              "freeze_manifest_sha256": freeze_sha, "scorer_version": VERSION, "readout_version": READOUT_VERSION,
              "t0": T0.isoformat(), "horizon_months": horizon, "maturity": end.isoformat(), "missing": [],
              "scored_on_utc": today.isoformat()}
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

        canonical = horizon == 24 and tracka_vintage.canonical_scope(repository, doi, freeze_sha) and archive is None
        earlier, unverified, discovery = None, None, None
        if canonical:
            retained = Path(temporary) / "first-24"
            published, evidence_24 = tracka_vintage.discover(repository, doi, freeze_sha, release.manifest_sha256,
                                                            retained, horizon=24)
            if published is not None:
                return recover_published(retained, out, evidence_24["original"])
            if evidence_24["reason"] != "MISSING_ORIGINAL" or evidence_24["original"].get("issue_url"):
                unverified = unverified_input("FIRST_24_PUBLICATION_UNRESOLVED", discovery=evidence_24)
            else:
                earlier, discovery = tracka_vintage.discover(repository, doi, freeze_sha, release.manifest_sha256,
                                                             Path(temporary) / "first-12")
                if earlier is None and not tracka_vintage.verified_absence(discovery, release.manifest_sha256):
                    unverified = unverified_input(discovery["reason"], detail=discovery.get("detail"),
                                                  original=discovery["original"], discovery=discovery)
        elif horizon == 24:
            earlier, unverified = local_panel(archive, release.manifest_sha256, freeze_sha)

        locked = load(release.folder / SCORER)
        require((python_version(), np.__version__) == (locked["python"], locked["numpy"]),
                f"Use the locked CPython {locked['python']} and NumPy {locked['numpy']} for scoring")
        result["runtime"] = {"python": python_version(), "numpy": np.__version__}
        sources_dir = stage / "sources"
        sources_dir.mkdir()
        source_manifest, first_dates, witnesses = fetch_outcomes(release, end, today, sources_dir, snapshot)
        dump(stage / SOURCES, source_manifest)
        if first_dates is None:
            result.update(status="BLOCKED_SOURCE", missing=source_manifest["missing"])
            return result["status"], commit_run(stage, out, result)

        source_sha = digest(stage / SOURCES)
        panels, draws = {}, {}
        if horizon == 24:
            result["h3_input"] = unverified or h3_provenance(discovery, today, source_manifest, source_sha)
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
        hypotheses = sequence(panels, formal=release.manifest["analysis"] == "replication")
        if horizon == 24:
            if unverified:
                hypotheses["H3"].update(decision="DESCRIPTIVE_ONLY", reached=False)
            hypotheses["H3"]["vintage_status"] = result["h3_input"]["status"]
        result.update(status="SCORED", analysis=release.manifest["analysis"],
                      outcome_source_manifest_sha256=source_sha, arm_availability=load(release.folder / ARMS),
                      panels={str(h): values for h, values in panels.items()}, hypotheses=hypotheses)
        return result["status"], commit_run(stage, out, result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, help="Local directory or exact Zenodo version DOI")
    parser.add_argument("--horizon", required=True, type=int, choices=HORIZONS)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--freeze-sha256", required=True, help="Manifest hash from OSF update 4")
    parser.add_argument("--snapshot", type=Path, help="Archived sources/ directory for offline replay")
    prior = parser.add_mutually_exclusive_group()
    prior.add_argument("--repository", help="Discover the registered first publications in the canonical GitHub repository")
    prior.add_argument("--prior-12", type=Path, help="Archive directory for descriptive replay")
    parser.add_argument("--prior-12-sha256", help="Result checksum for descriptive replay")
    args = parser.parse_args(argv)
    if bool(args.prior_12) != bool(args.prior_12_sha256):
        parser.error("Supply --prior-12 and --prior-12-sha256 together")
    if args.horizon == 12 and (args.repository or args.prior_12):
        parser.error("Use prior publication options with --horizon 24")
    if args.repository and not tracka_vintage.DOI.fullmatch(args.release):
        parser.error("Use the exact Zenodo DOI for GitHub discovery")
    try:
        with release_directory(args.release) as folder:
            release = read_release(folder, args.freeze_sha256)
            status, path = score(release, args.horizon, args.out, today=datetime.now(timezone.utc).date(),
                                 snapshot=args.snapshot, repository=args.repository, doi=args.release,
                                 archive=(args.prior_12, args.prior_12_sha256) if args.prior_12 else None)
    except (OSError, BadZipFile, ValueError, KeyError, TypeError) as exc:
        print(f"INVALID_RELEASE_OR_RUN: {exc}")
        return 1
    print(f"{status} {path}")
    return EXIT[status]


if __name__ == "__main__":
    raise SystemExit(main())
