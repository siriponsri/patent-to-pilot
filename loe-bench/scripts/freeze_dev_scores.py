"""Export native validation scores after exact verification against FREEZE."""

from collections import Counter
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from c3_dev_guard import nda_reader


DATA = Path(__file__).resolve().parents[1] / "data"
CONFIG_SHA256 = "d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39"
FIRST_TEST = date(2017, 1, 1)
EXPORT_ARMS = ("M3", "B1")


def read_pinned(name, expected):
    content = (DATA / name).read_bytes().replace(b"\r\n", b"\n")
    if sha256(content).hexdigest() != expected:
        raise ValueError(f"{name} digest mismatch")
    return json.loads(content)


def payload(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def require_match(actual, expected, path):
    if actual == expected:
        return
    if isinstance(actual, dict) and isinstance(expected, dict) and actual.keys() == expected.keys():
        for name in actual:
            require_match(actual[name], expected[name], f"{path}.{name}")
    if isinstance(actual, list) and isinstance(expected, list) and len(actual) == len(expected):
        for i, (left, right) in enumerate(zip(actual, expected, strict=True)):
            require_match(left, right, f"{path}[{i}]")
    raise ValueError(f"FREEZE replay mismatch at {path}: {actual!r} != {expected!r}")


def verification_rows(freeze, horizon, rows, native, reference):
    cutoffs = [date.fromisoformat(row["cutoff"]) for row in reference["cutoffs"]]
    panel = freeze.t1v3.QueuePanel(rows, cutoffs, native)
    point = panel.evaluate(freeze.np.ones(len(panel.keys), dtype=int))
    require_match(point, {name: reference[name] for name in point}, f"{horizon}m queue")
    for arm, scores in native.items():
        for indices, day, audit in zip(panel.by_cutoff, cutoffs, point["arms"][arm]["cutoffs"], strict=True):
            labels = panel.labels[indices]
            events = int(labels.sum())
            hits = audit["expected_queued_events"]
            slots = audit["allocated_slots"]
            local = freeze.ReviewQueue(freeze.np.asarray(scores)[indices], [day] * len(indices))
            weights = freeze.np.ones(len(indices), dtype=int)
            ap = local.measure(labels, freeze.np.zeros(len(indices)), weights)[2]
            yield {
                "horizon": horizon, "cutoff": day.isoformat(), "arm": arm,
                "rows": len(indices), "event_rows": events, "slots": slots,
                "recall20": hits / events if events else None, "precision20": hits / slots,
                "average_precision": float(ap) if events else None,
                "expected_queued_events": hits, "boundary_tie_rows": audit["boundary_tie_rows"],
                "published_match": "cutoff roster, slots, expected hits and ties",
            }
        labels = panel.labels
        queue = freeze.ReviewQueue(scores, [row["t"] for row in rows])
        weights = freeze.np.ones(len(rows), dtype=int)
        ap = float(queue.measure(labels, freeze.np.zeros(len(rows)), weights)[2])
        require_match(ap, reference["levels"][arm]["average_precision"]["estimate"], f"{horizon}m {arm} AP")
        metrics = point["arms"][arm]
        yield {
            "horizon": horizon, "cutoff": "pooled", "arm": arm, "rows": len(rows),
            "event_rows": point["event_rows"], "slots": point["queue_slots"],
            "recall20": metrics["recall"], "precision20": metrics["precision"],
            "average_precision": ap, "expected_queued_events": metrics["expected_queued_events"],
            "published_match": "pooled rows, event rows, slots, expected hits, recall, precision and AP",
        }


def main():
    # Load the pinned runner from its own checkout. The observer below returns
    # the identical score object to FREEZE and records only validation calls.
    import argparse

    cli = argparse.ArgumentParser(add_help=False)
    cli.add_argument("--implementation", type=Path, required=True)
    cli.add_argument("--out-dir", type=Path, required=True)
    cli.add_argument("--manifest", type=Path, required=True)
    export, rest = cli.parse_known_args()
    config = read_pinned("FROZEN_CONFIG.json", CONFIG_SHA256)
    report_digest = config["development_report_sha256"]
    reference = read_pinned("FREEZE_dev_report.json", report_digest)
    if not config["development_only"] or reference["status"] != "DEVELOPMENT_ONLY":
        raise ValueError("Expected a development-only FREEZE")
    implementation = export.implementation.resolve()
    git = ["rtk", "proxy", "git", "-C", str(implementation)]
    head = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    if head != config["code_commit_sha"] or subprocess.check_output(
            [*git, "status", "--porcelain"], text=True).strip():
        raise ValueError("Require a clean checkout at the FREEZE implementation pin")
    sys.path[:0] = [str(implementation / "loe-bench/scripts"), str(implementation / "loe-bench")]
    import freeze_run as freeze
    import e7_dev_run
    import t4_power

    args = freeze.parser(__doc__).parse_args(rest)
    freeze.t1.require_closed_seal()
    schedules = {}
    for horizon, split in freeze.t1.replay.PRIMARY.items():
        train, validation = split
        settings = config["horizons"][str(horizon)]
        if ([day.isoformat() for day in train] != settings["train_cutoffs"]
                or [day.isoformat() for day in validation] != settings["validation_cutoffs"]
                or any(day >= FIRST_TEST for day in (*train, *validation))):
            raise ValueError("Unexpected development split")
        freeze.t1.verify_windows(train, validation, horizon)
        schedules[horizon] = set(validation)

    out_dir = export.out_dir.resolve()
    outputs = {horizon: out_dir / ("FREEZE_dev_scores.json" if horizon == 24 else
                                  f"FREEZE_dev_scores_{horizon}m.json") for horizon in schedules}
    if any(path.exists() for path in (*outputs.values(), export.manifest)):
        raise ValueError("Use new paths for verified exports and manifest")
    captured = {}
    native = freeze.t1.native

    def observe(train, forecast, horizon, observed):
        scores = native(train, forecast, horizon, observed)
        if {row["t"] for row in forecast} == schedules[horizon]:
            if horizon in captured:
                raise ValueError("Unexpected duplicate validation score call")
            captured[horizon] = (forecast, scores)
        return scores

    replay = freeze.t1.replay
    original_reader = replay.read_jsonl

    def guarded_nda(path):
        return nda_reader(path, original_reader, projector=t4_power, redact_dates=replay.without_later_approvals)

    with (patch.object(freeze.t1, "native", observe),
          patch.object(replay, "read_jsonl", guarded_nda),
          patch.object(e7_dev_run, "read_jsonl", guarded_nda)):
        report, rebuilt_config = freeze.run(args)
    require_match(rebuilt_config, {k: v for k, v in config.items() if k != "development_report_sha256"}, "config")
    require_match(report, reference, "report")
    freeze.t1.require_closed_seal()

    artifacts, checks, serialized = {}, [], {}
    for horizon, days in schedules.items():
        rows, scores = captured[horizon]
        expected = reference["horizons"][str(horizon)]
        sizes = Counter(row["t"].isoformat() for row in rows)
        require_match(dict(sizes), {row["cutoff"]: row["rows"] for row in expected["cutoffs"]}, "rows")
        if {row["t"] for row in rows} != days:
            raise ValueError("Unexpected export cutoff")
        scores = {arm: freeze.np.asarray(values, dtype=float) for arm, values in scores.items()}
        if any(not freeze.np.isfinite(values).all() or ((values < 0) | (values > 1)).any()
               for values in scores.values()):
            raise ValueError("Expected native probabilities")
        content = payload({
            "status": "DEVELOPMENT_ONLY", "prediction_horizon_months": horizon,
            "frozen_config_sha256": CONFIG_SHA256,
            "rows": [{"key": row["key"], "cutoff": row["t"].isoformat(),
                      **{arm: float(scores[arm][i]) for arm in EXPORT_ARMS}}
                     for i, row in enumerate(rows)],
        })
        decoded = json.loads(content)["rows"]
        for arm in EXPORT_ARMS:
            require_match([row[arm] for row in decoded], scores[arm].tolist(), f"{horizon}m {arm} export")
        checks.extend(verification_rows(freeze, horizon, rows, scores, expected))
        serialized[horizon] = content
        artifacts[str(horizon)] = {
            "path": outputs[horizon].as_posix(), "sha256": sha256(content).hexdigest(),
            "rows": len(rows), "cutoff_rows": dict(sizes),
        }
    for horizon, path in outputs.items():
        with path.open("xb") as handle:
            handle.write(serialized[horizon])
    with export.manifest.open("xb") as handle:
        handle.write(payload({
            "status": "DEVELOPMENT_ONLY", "implementation_sha": head,
            "frozen_config_sha256": CONFIG_SHA256, "published_report_sha256": report_digest,
            "verification": "EXACT_FULL_PUBLISHED_REPORT_REPLAY",
            "per_cutoff_reference_limit": (
                "Published cutoff rows, slots, expected hits and boundary ties were checked exactly. "
                "Cutoff event counts, recall, precision and AP are replay diagnostics. "
                "FREEZE publishes independent references for these quantities at pooled horizon level."
            ),
            "exports": artifacts, "metrics": checks,
        }))
    for details in artifacts.values():
        print(f"{details['path']} {details['sha256']}", flush=True)


if __name__ == "__main__":
    main()
