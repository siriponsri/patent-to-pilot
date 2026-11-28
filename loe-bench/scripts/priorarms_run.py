"""Prepare PRIORARMS development metrics and prospective predictions offline."""

import argparse
from collections import Counter
from datetime import timedelta
from hashlib import file_digest, sha256
import json
from math import isclose, isfinite
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import tracka_core as core
from loe_bench import dataset, priorarms, t1v3
from loe_bench.baselines import exclusivity_rule_score

MANIFEST = "PRIORARMS_MANIFEST.json"
CORE_SHA = "6497ab59ba41b0429a6169d5118c6afd14680233076a6a6693c03599d0176628"
IDENTITY = ("key", "t0", "horizon_months")
LOCK = core.REPO / "loe-bench/requirements-priorarms.lock"
DEV_LABEL = "development validation (descriptive)"


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def package_checks(folder, manifest):
    raw = (folder / "SHA256SUMS").read_bytes()
    expected = {**manifest["files_sha256"], core.MANIFEST: CORE_SHA}
    entries = [line.split("  ", 1) for line in raw.decode("ascii").splitlines()]
    listed = {name: value for value, name in entries}
    core.require(len(entries) == len(listed) and listed == expected, "Track A checksum roster differs")
    for name, value in expected.items():
        core.require(digest(folder / name) == value, f"Track A digest mismatch: {name}")
    return raw


def identities(rows):
    return [tuple(row[name] for name in IDENTITY) for row in rows]


def read_rows(path):
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def fit_research(python, train, predict, entities):
    def matrix(rows):
        data = [priorarms.predictors(row, entities[row["key"]].nda_first) for row in rows]
        return {arm: [row[arm] for row in data] for arm in priorarms.ARMS}

    targets = []
    for row in train:
        event, days = priorarms.survival_target(row, entities[row["key"]].anda_first)
        targets.append((event, days / (row["t_end"] - row["t"]).days))
    payload = {"train": matrix(train), "predict": matrix(predict), "target": targets}
    encoded = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("ascii")
    child = subprocess.run([str(python), "-B", "-m", "loe_bench.priorarms_survival"],
                           cwd=core.frozen.DATA.parent, input=encoded, stdout=subprocess.PIPE, check=True)
    result = json.loads(child.stdout)
    core.require(result["runtime"] == {"python": priorarms.PYTHON_VERSION, **priorarms.RESEARCH_VERSIONS}
                 and set(result["arms"]) == set(priorarms.ARMS), "Isolated research worker differs")
    for fit in result["arms"].values():
        if fit["status"] == "PASS":
            core.require(len(fit["scores"]) == len(predict)
                         and all(isfinite(x) and 0 <= x <= 1 for x in fit["scores"]), "Invalid forecast panel")
    return result["arms"], sha256(encoded).hexdigest()


def summarize(fits):
    return {arm: {name: value for name, value in fit.items() if name != "scores"} for arm, fit in fits.items()}


def development(args, cfg, raw):
    frozen = core.frozen
    replay = frozen.t1.replay
    entities, builder, _ = replay.inputs(raw, args.private / "ob_editions", args.private / "piv",
                                         args.private / "challenge")
    days = {day for split in replay.PRIMARY.values() for subset in split for day in subset}
    core.verify_editions(builder, days)
    report_path = frozen.manifest("FREEZE_dev_report.json")
    core.require(report_path["sha256"] == cfg["development_report_sha256"], "FREEZE development digest differs")
    reference = frozen.read_json(report_path["file"])["horizons"]
    result = {}
    for h, (train_days, validation_days) in replay.PRIMARY.items():
        print(f"{DEV_LABEL}, {h} months", flush=True)
        frozen.t1.verify_windows(train_days, validation_days, h)
        observed = min(validation_days) - timedelta(days=1)
        train = replay.partition(entities, builder, train_days, h, training=True)
        rows = replay.partition(entities, builder, validation_days, h)
        calibrators, policies, inner = frozen.inner_fits(train, h, observed)
        expected = cfg["horizons"][str(h)]
        core.require(len(train) == expected["train_rows"] and inner == expected["inner"] and
                     all(policies[arm]["calibrator"] == expected["arms"][arm]["calibrator"] for arm in t1v3.ARMS),
                     "Frozen development TRAIN calibration differs")
        native = frozen.t1.native(train, rows, h, observed)
        probabilities = {arm: calibrators[arm].predict(frozen.t1.calibrator_inputs(scores))
                         for arm, scores in native.items()}
        native["B3"] = [b3_score(builder, row, h) for row in rows]
        probabilities["B3"] = native["B3"]
        fits, input_sha = fit_research(args.research_python, train, rows, entities)
        for arm, fit in fits.items():
            if fit["status"] == "PASS":
                native[arm] = probabilities[arm] = fit["scores"]
        times = [priorarms.survival_target(row, entities[row["key"]].anda_first)[1] for row in rows]
        panel = priorarms.development_metrics(rows, times, native, probabilities)
        ref = reference[str(h)]
        core.require(panel["rows"] == ref["rows"] and panel["drugs"] == ref["drug_clusters"] and
                     panel["events"] == ref["event_rows"], "Frozen development roster counts differ")
        for arm in t1v3.ARMS:
            levels = panel["arms"][arm]
            core.require(isclose(levels["recall20"], ref["arms"][arm]["recall"], rel_tol=0, abs_tol=1e-12) and
                         isclose(levels["brier"], ref["levels"][arm]["brier"]["estimate"], rel_tol=0, abs_tol=1e-12),
                         "Frozen development reference scores differ")
        panel.update(train_rows=len(train), train_events=sum(row["y"] for row in train),
                     train_cutoffs=[day.isoformat() for day in train_days], models=summarize(fits),
                     research_input_sha256=input_sha, freeze_comparator_parity="PASS")
        result[str(h)] = panel
    return result


def b3_score(builder, row, horizon):
    source, _ = builder.select_edition(row["t"])
    core.require(source is not None, "B3 development requires a verified cutoff edition")
    key = builder.linker.canonical(row["key"])
    patents, exclusivities = builder._indexes[source].records(key)
    clocks = {kind: [record["expiry"] for record in records or () if record["expiry"] is not None]
              for kind, records in (("patent_exp", patents), ("excl_exp", exclusivities))}
    return exclusivity_rule_score(clocks, row["t"], horizon)


def track_a(args, folder, manifest, core_roster, entities, builder):
    roster, eligibility = core.forecast_roster(entities)
    core.require(eligibility == manifest["eligibility"] and len(roster) == 651, "TRACKA-CORE roster differs")
    results, rows_by_horizon = {}, {}
    for h in core.HORIZONS:
        print(f"Track A t0, {h} months", flush=True)
        pinned = manifest["horizons"][str(h)]
        windows = pinned["training_windows"]
        cutoffs, calendar = core.schedule(builder.history, h)
        core.require([d.isoformat() for d in cutoffs] == [d for d, w in windows.items() if w["status"] == "ELIGIBLE"],
                     "TRACKA-CORE TRAIN cutoffs differ")
        train = dataset.build_samples(entities, cutoffs, h, core.T0)
        windows_replay = {d.isoformat(): w for d, w in calendar.items()}
        for row in train:
            item = windows_replay[row["t"].isoformat()]
            item["rows"] = item.get("rows", 0) + 1
            item["events"] = item.get("events", 0) + row["y"]
        core.require(windows_replay == windows and len(train) == pinned["training_rows"] and
                     sum(r["y"] for r in train) == pinned["training_events"] and
                     len({r["key"] for r in train}) == pinned["training_drugs"] and
                     len(train) == len({(r["t"], r["key"]) for r in train}), "TRACKA-CORE TRAIN rows differ")
        core.require(core.verify_editions(builder, {*cutoffs, core.T0}) ==
                     {d.isoformat(): manifest["edition_audit"][d.isoformat()] for d in (*cutoffs, core.T0)},
                     "TRACKA-CORE as-of edition audit differs")
        forecasts = [dict(row) for row in roster]
        core.add_predictors(train, builder, h)
        core.add_predictors(forecasts, builder, h)
        keys = [{"key": r["key"], "t0": core.T0.isoformat(), "horizon_months": h} for r in forecasts]
        core_pred = read_rows(folder / f"core_predictions_{h}m.jsonl")
        expected = [r for r in core_roster if r["horizon_months"] == h]
        core.require(identities(keys) == identities(expected) == identities(core_pred) and
                     len(set(identities(keys))) == 651, "TRACKA-CORE (key, t0, horizon) join failed")
        fits, input_sha = fit_research(args.research_python, train, forecasts, entities)
        results[str(h)] = {"train_rows": len(train), "train_events": sum(r["y"] for r in train),
                           "train_drugs": pinned["training_drugs"], "train_cutoffs": [d.isoformat() for d in cutoffs],
                           "roster_rows": len(keys), "roster_join": "PASS_EXACT_ORDER",
                           "research_input_sha256": input_sha, "models": summarize(fits)}
        rows_by_horizon[h] = (keys, fits)
    return results, rows_by_horizon


def stage_predictions(out, track, panels, admission):
    files = {}
    for h, (keys, fits) in panels.items():
        rows = [dict(row, arms={}) for row in keys]
        for arm in priorarms.ARMS:
            if admission[arm] != "ADMITTED":
                continue
            scores = fits[arm]["scores"]
            weights, boundary = core.queue_allocation(scores, [core.T0] * len(keys))
            track[str(h)]["models"][arm].update(queue=boundary, native=core.distribution(scores))
            for row, score, weight in zip(rows, scores, weights, strict=True):
                row["arms"][arm] = {"native": score, "queue_inclusion_probability": weight}
        if rows[0]["arms"]:
            path = out / f"priorarms_predictions_{h}m.jsonl"
            path.write_bytes(core.llm_input.jsonl(rows))
            files[path.name] = digest(path)
    return files


def publish(folder, out, original, files):
    lock = folder / ".priorarms-write.lock"
    with lock.open("x"):
        pass
    published = []
    try:
        sums = folder / "SHA256SUMS"
        core.require(sums.read_bytes() == original and all(not (folder / n).exists() for n in files),
                     "Concurrent or previous Track A outputs require reconciliation")
        extended = original + "".join(f"{value}  {name}\n" for name, value in sorted(files.items())).encode("ascii")
        pending = out / "SHA256SUMS"
        pending.write_bytes(extended)
        for name, value in files.items():
            destination = folder / name
            (out / name).rename(destination)
            published.append(destination)
            core.require(digest(destination) == value, f"Published digest differs: {name}")
        core.require(sums.read_bytes() == original, "Track A checksums changed during publication")
        os.replace(pending, sums)
    except Exception:
        for path in published:
            path.unlink()
        raise
    finally:
        lock.unlink()
    return sha256(extended).hexdigest()


def prepare(args):
    cfg, revision = core.check_local_release()
    folder = args.private / "trackA"
    core.require(core.frozen.manifest(core.MANIFEST)["sha256"] == CORE_SHA, "TRACKA-CORE manifest differs")
    core_manifest = core.frozen.read_json(core.MANIFEST)
    original = package_checks(folder, core_manifest)
    core_roster = read_rows(folder / "roster.jsonl")
    core.require(Counter(row["horizon_months"] for row in core_roster) == {12: 651, 24: 651},
                 "Track A roster counts differ")
    with TemporaryDirectory(prefix="priorarms-", dir=args.private) as temporary:
        out = Path(temporary)
        raw, _, entities, builder, inputs = core.source_inputs(args.private, cfg, out)
        core.require(inputs == core_manifest["inputs"], "TRACKA-CORE pinned input digests differ")
        dev = development(args, cfg, raw)
        track, panels = track_a(args, folder, core_manifest, core_roster, entities, builder)
        admission = {arm: "ADMITTED" if all(panel["models"][arm]["status"] == "PASS"
                                            for panel in (*track.values(), *dev.values())) else "FAILED"
                     for arm in priorarms.ARMS}
        files = stage_predictions(out, track, panels, admission)
        new_sums = publish(folder, out, original, files)
    lock_sha = sha256(LOCK.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return {"status": "PREPARED_FOR_FREEZE_REVIEW", "code_commit_sha": revision, "t0": core.T0.isoformat(),
            "research_runtime": {"python": priorarms.PYTHON_VERSION, **priorarms.RESEARCH_VERSIONS},
            "core_scoring_runtime": cfg["runtime"], "research_lock_lf_sha256": lock_sha,
            "tracka_core_manifest_sha256": CORE_SHA, "core_roster_sha256": core_manifest["files_sha256"]["roster.jsonl"],
            "sha256sums_before": sha256(original).hexdigest(), "sha256sums_after": new_sums,
            "files_sha256": files, "admission": admission, "development": dev, "track_a": track,
            "cprime_supplement": "NOT_RUN"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private", type=Path, default=core.PRIVATE)
    parser.add_argument("--research-python", type=Path)
    args = parser.parse_args()
    args.private = args.private.resolve()
    args.research_python = (args.research_python or args.private / "venv-priorarms/Scripts/python.exe").resolve()
    sys.addaudithook(core.network_guard)
    path = core.frozen.DATA / MANIFEST
    core.require(not path.exists(), "PRIORARMS manifest already exists")
    result = prepare(args)
    core.write_json(path, result)
    print(f"{MANIFEST} {digest(path)}", flush=True)


if __name__ == "__main__":
    main()
