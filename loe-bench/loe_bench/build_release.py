"""Assemble shareable Track A artifacts without fetching outcome data."""

import argparse
from collections import defaultdict
import csv
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import re
from shutil import copyfile
from subprocess import check_output, CalledProcessError
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from .common import read_jsonl
from . import dataset, moiety
from .tracka_release import (ARMS, C9, CORE, DEADLINE, FREEZE, HORIZONS, IDENTITY, LLM, MANIFEST, PRIOR, ROSTER,
                             SCORER, T0, VERSION, code_digest, digest, dump, load, read_release, require, row_id,
                             verify_file)

REPO = Path(__file__).resolve().parents[2]
PRIVATE = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench")
CORE_MANIFEST = "TRACKA_CORE_MANIFEST.json"
STOCK_FREEZE = "loe-bench/data/TRACKA_FREEZE_MANIFEST.json"
REGISTRATION = "https://doi.org/10.17605/OSF.IO/P2SMD"
REASON_NO_RIGHTS = "Custodian may score identical frozen bytes after confirming use rights."
MODULES = ("__init__", "baselines", "challenge", "common", "dataset", "evidence_graph", "kleene", "llm_arm",
           "metrics", "moiety", "moiety_linkage", "ob_history", "piv_history", "priorarms", "regulatory_graph",
           "review_metrics", "score_release", "seal", "t1v3", "t2", "t2_features", "tracka_outcomes",
           "tracka_release", "tracka_statistics", "voi")
ARM_NAME = {
    "B1": "Age-table hazard baseline",
    "B3": "All-listed-expiry binary rule",
    "M1": "Flat-feature regulatory model",
    "M3": "Evidence-graph regulatory model",
    "P1-RSF-OPEN": "Open-input random survival forest",
    "P2-COX-OPEN": "Open-input Cox proportional hazards model",
    "L1": "One-shot language model",
    "L1e": "Evidence-augmented one-shot language model",
    "C9-SFT": "Evidence-augmented supervised fine-tuning",
    "C9-GRPO": "Evidence-augmented group relative policy optimization",
}


def prepare_identity(private, core, keys):
    raw = private / "raw-20261127"
    inputs = core["inputs"]
    for name in ("df_nda.jsonl", "df_anda.jsonl", *moiety.ORANGE_FILES):
        verify_file(raw, name, inputs["s0_raw_sha256"][name])
    gsrs = inputs["gsrs"]
    source = private / "moiety" / gsrs["file"]
    require(gsrs["file"] == moiety.GSRS_FILE and gsrs["sha256"] == moiety.GSRS_SHA256, "GSRS pin differs")
    registry = moiety.registry_for(raw, source)
    entities = dataset.build_entities(raw, gsrs_path=source)
    eligible = {key for key, e in entities.items() if e.nda_first and e.nda_first <= T0 and e.flag_at("nme", T0)
                and (e.anda_first is None or e.anda_first > T0)}
    require(eligible == keys, "Frozen roster differs from the verified S0 selection")
    orange = moiety.orange_products(raw)
    linkage = dataset.build_moiety_linkage(raw, registry, orange)
    ndas = defaultdict(set)
    for rec in read_jsonl(raw / "df_nda.jsonl"):
        approved = min((day for day, _ in dataset._final_originals(rec)), default=None)
        for key, day, _ in dataset._original_compositions(rec, approved, registry, orange, linkage):
            if key in keys and day is not None and day <= T0:
                ndas[key].add(rec["application_number"])
    require(set(ndas) == keys, "Some frozen keys lack their original NDA identifiers")
    s0_final = []
    for rec in read_jsonl(raw / "df_anda.jsonl"):
        days = [day for day, _ in dataset._final_originals(rec)]
        if any(day <= T0 for day in days) or (not days and any(
                sub.get("submission_type") == "ORIG" and sub.get("submission_status") == "AP"
                for sub in rec.get("submissions") or [])):
            s0_final.append(rec["application_number"])
    return {"roster_nda_ids": {key: sorted(ids) for key, ids in ndas.items()},
            "s0_final_anda_apps": sorted(set(s0_final)), "fix2c_aliases": linkage.canonical,
            "registry_aliases": {name: sorted(codes) for name, codes in registry.aliases.items()},
            "registry_targets": {code: sorted(values) for code, values in registry.targets.items()},
            "source_pins": {"gsrs": gsrs, "s0_raw_sha256": inputs["s0_raw_sha256"]}}


def publication(args, frozen):
    if args.dry_run:
        require(not any((args.freeze_tag, args.osf_timestamp, args.osf_manifest_sha256)),
                "A pending dry run cannot carry final registration metadata")
        return {"freeze": "pending", "analysis": "pending"}
    require(args.freeze_tag and args.osf_timestamp and args.osf_manifest_sha256,
            "A public build requires the exact freeze tag and OSF timestamp and SHA-256")
    require(re.fullmatch(r"loe-[A-Za-z0-9][A-Za-z0-9_.-]*", args.freeze_tag), "Invalid freeze tag")
    require(args.freeze_tag != "loe-S0-input-20261127", "The S0 input tag is not a prediction freeze")
    tag_path = PurePosixPath(args.freeze_git_path)
    require(str(tag_path).startswith("loe-bench/data/") and ".." not in tag_path.parts, "Invalid tagged manifest path")
    tagged = check_output(["git", "show", f"refs/tags/{args.freeze_tag}:{tag_path}"], cwd=REPO)
    require(tagged == frozen.read_bytes() and args.osf_manifest_sha256 == digest(frozen),
            "Tagged manifest, private manifest and OSF SHA-256 must match")
    stamped = datetime.fromisoformat(args.osf_timestamp)
    require(stamped.utcoffset() is not None and stamped.date() >= T0, "Invalid OSF timestamp")
    return {"freeze": "frozen", "freeze_tag": args.freeze_tag,
            "registration": REGISTRATION, "osf_manifest_sha256": args.osf_manifest_sha256,
            "osf_timestamp": stamped.isoformat(),
            "analysis": "exploratory" if args.exploratory or stamped >= DEADLINE else "replication"}


def prediction_files(pins, args):
    files = {}
    for arm in CORE:
        files[arm] = {str(h): f"core_predictions_{h}m.jsonl" for h in HORIZONS}
    prior = {str(h): f"priorarms_predictions_{h}m.jsonl" for h in HORIZONS}
    if all(name in pins for name in prior.values()):
        for arm in PRIOR:
            files[arm] = prior
    else:
        require(not (pins.keys() & set(prior.values())), "Incomplete prior-method prediction horizons")
    names = {"L1": "L1DEV_outputs.jsonl", "L1e": "L1E_outputs.jsonl",
             "C9-SFT": "c9_sft_predictions.jsonl", "C9-GRPO": "c9_grpo_predictions.jsonl"}
    if args.arm_file:
        for option in args.arm_file:
            arm, sep, name = option.partition("=")
            require(sep and arm in names and name in pins, f"Unknown optional arm or frozen file: {option}")
            names[arm] = name
    require(len(set(names.values())) == len(names), "Optional arms must use distinct source files")
    require((names[C9[0]] in pins) == (names[C9[1]] in pins), "C9 freeze must contain both arms")
    for arm, name in names.items():
        if name in pins:
            files[arm] = {str(h): name for h in ((24,) if arm in C9 else HORIZONS)}
    return files


def frozen_file(folder, name, sha):
    relative = PurePosixPath(name)
    require(name == relative.as_posix() and not relative.is_absolute() and
            all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", part) for part in relative.parts),
            f"Invalid freeze file locator: {name}")
    require((folder / name).resolve().is_relative_to(folder.resolve()), f"Freeze file leaves the package: {name}")
    return verify_file(folder.joinpath(*relative.parts[:-1]), relative.name, sha)


def build(args, stage):
    private, package = args.private, args.private / "trackA"
    core = load(package / CORE_MANIFEST)
    require(digest(package / CORE_MANIFEST) == "6497ab59ba41b0429a6169d5118c6afd14680233076a6a6693c03599d0176628",
            "Private core manifest differs from the audited TRACKA-CORE bytes")
    if args.dry_run:
        core_pins = core["files_sha256"]
        prior = load(REPO / "loe-bench/data/PRIORARMS_MANIFEST.json")
        pins = {**core_pins, **prior["files_sha256"]}
        frozen = stage / FREEZE
        dump(frozen, {"freeze": "pending", "files_sha256": pins})
    else:
        frozen = args.freeze_manifest or package / Path(args.freeze_git_path).name
        pins = load(frozen)["files_sha256"]
        copyfile(frozen, stage / FREEZE)
    manifest = {"schema": 1, "t0": T0.isoformat(), **publication(args, frozen), "frozen_files": {}}
    rights = []

    def declare(name, source, license_name, shareable="yes", details=""):
        rights.append([name, source, license_name, shareable, details])

    def include(name, exposed_name=None):
        original = frozen_file(package, name, pins[name])
        exposed_name = exposed_name or original.name
        require(not (stage / exposed_name).exists(), f"Duplicate release filename: {exposed_name}")
        copyfile(original, stage / exposed_name)
        manifest["frozen_files"][exposed_name] = name
        return exposed_name

    include(ROSTER)
    declare(ROSTER, "Track A public-source roster", "Apache-2.0 project artifact")
    keys = {row_id(row)[0] for row in read_jsonl(stage / ROSTER)}
    dump(stage / IDENTITY, prepare_identity(private, core, keys))
    declare(IDENTITY, "S0 openFDA and pinned GSRS name/UNII fields; FIX2c", "CC0 1.0 source fields; Apache-2.0 adapter")
    declare(FREEZE, "Track A prediction freeze", "Apache-2.0 project metadata")
    sources = prediction_files(pins, args)
    share_optional = set(args.share_optional)
    require(not args.dry_run or not share_optional, "GPU outputs are outside the pending rehearsal")
    require(share_optional <= sources.keys(), "An approved optional arm is absent from the freeze manifest")
    require(share_optional.intersection(C9) in (set(), set(C9)), "Share both C9 arms or withhold both")
    include_names = {name for arm, horizons in sources.items() if arm in CORE + PRIOR or arm in share_optional
                     for name in horizons.values()}
    copies = {}
    for name in sorted(include_names):
        exposed = include(name, name.replace("/", "__"))
        copies[name] = exposed
        edition = "Project prediction output" if name.startswith(("core_", "priorarms_")) else "Maintainer-reviewed GPU output"
        declare(exposed, edition, "Apache-2.0 project artifact", details="Frozen prediction bytes")

    arm_dictionary = {}
    for arm in CORE + PRIOR + LLM + C9:
        if arm not in sources:
            arm_dictionary[arm] = {"status": "NOT_RUN", "files": {}}
        elif set(sources[arm].values()) <= copies.keys():
            arm_dictionary[arm] = {"status": "INCLUDED", "files": {h: copies[name] for h, name in sources[arm].items()}}
        else:
            arm_dictionary[arm] = {"status": "WITHHELD", "files": {}, "reason": REASON_NO_RIGHTS}
            for name in sorted(set(sources[arm].values())):
                declare(name, f"Track A {arm} freeze", "Rights review pending", "no", REASON_NO_RIGHTS)
        arm_dictionary[arm].update(name=ARM_NAME[arm], role="primary" if arm in ("B1", "M1", "M3")
                                   else "descriptive" if arm == "B3" else "exploratory",
                                   queue_score="p_entry" if arm in LLM + C9 else "native")
    dump(stage / ARMS, arm_dictionary)
    declare(ARMS, "Track A release builder", "Apache-2.0")
    for name in sorted(pins.keys() - set(manifest["frozen_files"].values()) -
                       {row[0] for row in rights if row[3] == "no"}):
        declare(name, "Private freeze inputs or training artifacts", "Mixed source terms", "no",
                "Preserve privately with the custodian. See SOURCE-RECIPES.md.")
    declare("NBER-derived or raw archive bytes", "NBER Orange Book archive", "NBER site terms", "no",
            "Use the source recipe.")

    guide = REPO / "docs/loe-bench/HOW-TO-SCORE-TRACK-A.md"
    copyfile(guide, stage / "README.md")
    copyfile(REPO / "LICENSE", stage / "LICENSE")
    copyfile(REPO / "loe-bench/requirements-tracka.lock", stage / "requirements-tracka.lock")
    (stage / "SOURCE-RECIPES.md").write_text(
        "# Source recipes\n\n"
        "- For S0 input hashes, use `loe-S0-input-20261127` and `loe-bench/data/S0_INPUT_MANIFEST.json`.\n"
        "- The GSRS recipe uses the [2026-08-06 public export](https://gsrs.ncats.nih.gov/assets/downloads/"
        "dump-public-2026-08-06.gsrs) and the hash in identity.json. The release includes the scoring projection.\n"
        "- If auditing historical NBER-derived features independently, obtain them under the "
        "[publisher's terms](https://www.nber.org/terms-and-conditions) and follow the "
        "[E8 source manifest](https://github.com/siriponsri/patent-to-pilot/blob/5861d077/loe-bench/data/"
        "E8_NBER_MANIFEST.json). The score command uses frozen forecasts.\n", encoding="utf-8")
    (stage / "CITATION").write_text(
        "Siripon Srihangpiboon and Tuchsanai Ploysuwan. LOE-Bench Track A prediction release.\n"
        f"Freeze {manifest['freeze']}. Scorer version {VERSION}.\n"
        f"OSF registration {REGISTRATION}\n"
        f"Zenodo version DOI {args.zenodo_doi or '(cite the exact version DOI of the public record)'}\n",
        encoding="utf-8")
    dump(stage / "example-output.json", {"status": "PENDING", "horizon_months": 12, "maturity": "2027-11-27",
                                         "missing": ["Calendar maturity is 2027-11-27."]})
    code = stage / "loe_bench"
    code.mkdir()
    for module in MODULES:
        source = Path(__file__).with_name(f"{module}.py")
        copyfile(source, code / source.name)
        declare(f"loe_bench/{source.name}", "Patent-to-Pilot repository", "Apache-2.0")
    dump(stage / SCORER, {"version": VERSION, "python": "3.12.10", "numpy": "2.5.4",
                          "source_files_sha256": {path.name: code_digest(path) for path in sorted(code.iterdir())}})
    for name in ("README.md", "LICENSE", "requirements-tracka.lock", "SOURCE-RECIPES.md", "CITATION",
                 "example-output.json", "RIGHTS.csv", SCORER, MANIFEST):
        declare(name, "Patent-to-Pilot release kit", "Apache-2.0")
    with (stage / "RIGHTS.csv").open("w", newline="", encoding="utf-8") as file:
        table = csv.writer(file, lineterminator="\n")
        table.writerow(("file", "source", "license", "shareable", "details"))
        table.writerows(sorted(rights))
    manifest["files_sha256"] = {path.name: digest(path) for path in sorted(stage.iterdir()) if path.is_file()}
    dump(stage / MANIFEST, manifest)
    read_release(stage, manifest.get("osf_manifest_sha256"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--private", type=Path, default=PRIVATE, help="Private LOE-Bench root, containing trackA/")
    parser.add_argument("--dry-run", action="store_true", help="Stage pending files locally before the freeze")
    parser.add_argument("--freeze-manifest", type=Path)
    parser.add_argument("--freeze-tag")
    parser.add_argument("--freeze-git-path", default=STOCK_FREEZE)
    parser.add_argument("--osf-timestamp")
    parser.add_argument("--osf-manifest-sha256")
    parser.add_argument("--exploratory", action="store_true", help="Record a prospective protocol deviation")
    parser.add_argument("--arm-file", action="append", help="Optional ARM=relative/frozen-predictions.jsonl")
    parser.add_argument("--share-optional", action="append", choices=LLM + C9, default=[],
                        help="Include a GPU arm only after reviewing its exact frozen file and rights")
    parser.add_argument("--zenodo-doi")
    parser.add_argument("--archive", type=Path, help="Write the release ZIP for Zenodo")
    args = parser.parse_args(argv)
    try:
        require(not args.out.exists(), f"Release destination already exists: {args.out}")
        if args.archive:
            require(not args.dry_run, "Keep the dry run as a local directory")
            require(args.archive.name == "track-a-release.zip" and not args.archive.exists()
                    and not args.archive.resolve().is_relative_to(args.out.resolve()),
                    "Use a new track-a-release.zip outside the release directory")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".tracka-build-", dir=args.out.parent) as temporary:
            stage = Path(temporary) / "release"
            stage.mkdir()
            build(args, stage)
            stage.rename(args.out)
        if args.archive:
            with ZipFile(args.archive, "x", compression=ZIP_DEFLATED) as archive:
                for file in sorted(args.out.rglob("*")):
                    if file.is_file():
                        archive.write(file, file.relative_to(args.out).as_posix())
    except (OSError, ValueError, KeyError, TypeError, CalledProcessError) as exc:
        print(f"BUILD_FAILED: {exc}")
        return 1
    print(f"freeze: {'pending' if args.dry_run else 'frozen'} | {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
