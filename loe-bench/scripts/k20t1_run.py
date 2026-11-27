"""Run the predeclared K20 trial and freeze the T1 development policies."""
import argparse
from collections import Counter
from datetime import date, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import subprocess
from unittest.mock import patch

import t4_power as guarded
import numpy as np

# DEVX imports two token patterns renamed or removed when T4b merged.
# Keep the merged T4b outcome projector and run DEVX without editing its card.
with (patch.object(guarded, "FLAGS", re.compile(rb'"submissions"\s*:\s*\['), create=True),
      patch.object(guarded, "TOKEN", guarded.JSON_TOKEN, create=True)):
    import devx_run as replay

from loe_bench import dataset, devx, evidence_graph as graph, k20t1, t2
from loe_bench.baselines import Logistic
from loe_bench.common import add_months
from loe_bench.nber_ob import DEFAULT_NBER_DIR, nber_sources
from loe_bench.ob_history import OBHistory
from loe_bench.t2_features import CHALLENGE_FEATURES, MODEL_FEATURES

ROOT = replay.ROOT
FLAGS = ("K07",)


def training_dates(start, horizon):
    annual = (date(year, 1, 1) for year in range(1987, start.year))
    return [day for day in annual if add_months(day, horizon) < start]


def candidate_train(entities, builder, dates, horizon):
    rows = dataset.build_samples(entities, dates, horizon, replay.DEVELOPMENT_END)
    sources = {day: builder.select_edition(day) for day in dates}
    for row in rows:
        key, cutoff = row["key"], row["t"]
        source, _ = sources[cutoff]
        row["asof"] = builder.build(key, cutoff, horizon, row["x"])
        zip_source = source is not None and source.identity["kind"] == "fda_zip"
        products = (builder._indexes[source].linked_products.get(builder.linker.canonical(key), ())
                    if zip_source else ())
        row["breadth"] = devx.presentation_breadth(products, source.edition_date if zip_source else cutoff)
    return [k20t1.with_edition_features(row, sources[row["t"]][0]) for row in rows], sources


def augment_validation(rows, zip_builder):
    sources = {day: zip_builder.select_edition(day)[0] for day in {row["t"] for row in rows}}
    if any(source is None for source in sources.values()):
        raise ValueError("K20T1 requires an availability-proven fresh validation edition")
    return [k20t1.with_edition_features(row, sources[row["t"]]) for row in rows]


def verify_windows(train, validation, horizon):
    t2.require_development_cutoffs([*train, *validation])
    if (not train or not validation or any(add_months(d, horizon) >= min(validation) for d in train)
            or any(add_months(d, horizon) > replay.DEVELOPMENT_END for d in validation)):
        raise ValueError("invalid K20T1 time partitions")


def source_audit(train, sources):
    counts = Counter(row["t"] for row in train)
    return {day.isoformat(): {"rows": counts[day], "source": coverage["source"],
                              "edition_date": coverage["chosen_edition"],
                              "availability_proof": coverage["availability_proof"],
                              **k20t1.edition_features(source, day)}
            for day, (source, coverage) in sources.items()}


def compare_split(name, splits, entities, builder, annual_builder, reference):
    results, fits = {}, {}
    prepared = {}
    for horizon, (short, validation_days) in splits.items():
        long = training_dates(min(validation_days), horizon)
        for dates in (short, long):
            verify_windows(dates, validation_days, horizon)
        baseline = replay.partition(entities, builder, short, horizon, training=True)
        validation = replay.partition(entities, builder, validation_days, horizon)
        evaluator = replay.PairedEvaluation(validation)
        old = evaluator.evaluate(*devx.predict(baseline, validation, horizon, FLAGS))
        if name == "primary":
            replay.verify_baseline(reference[str(horizon)], replay.cohort(baseline, validation, horizon), old[0])
        prepared[horizon] = (short, long, validation_days, baseline, validation, evaluator, old)

    for horizon, (short, long, validation_days, baseline, validation, evaluator, old) in prepared.items():
        print(f"{name} {horizon}m baseline ready, fitting annual candidate", flush=True)
        val_augmented = augment_validation(validation, builder)
        candidate, sources = candidate_train(entities, annual_builder, long, horizon)
        new = evaluator.evaluate(*devx.predict(candidate, val_augmented, horizon, FLAGS,
                                               extra_features=k20t1.EDITION_FEATURES))
        result = replay.compare(old, new)
        a, b = new[0]["arms"]["B1"]["aurc80"], old[0]["arms"]["B1"]["aurc80"]
        result["candidate_minus_current"]["B1"] = replay.interval(replay.difference(a, b),
                                                                  new[1]["B1"] - old[1]["B1"])
        result.update(baseline_train_rows=len(baseline), candidate_train_rows=len(candidate),
                      validation_rows=len(validation), baseline_train_cutoffs=[d.isoformat() for d in short],
                      validation_cutoffs=[d.isoformat() for d in validation_days],
                      candidate_train_sources=source_audit(candidate, sources),
                      validation_clusters=len({row["key"] for row in validation}),
                      validation_event_clusters=len({row["key"] for row in validation if row["y"]}))
        results[str(horizon)] = result
        fits[horizon] = (baseline, candidate, validation, val_augmented, short, long, validation_days)
    return results, fits


def calibrator_inputs(probabilities):
    return [{"x": {"logit": t2._logit(p)}} for p in probabilities]


def fixed_policies(train, validation, days, validation_days, horizon, extra_features):
    verify_windows(days, validation_days, horizon)
    t2.require_development_cutoffs(row["t"] for row in (*train, *validation))
    inner_cutoff = max(days)  # Primary training ends at the shared 2010 FDA cutoff.
    inner = [row for row in train if row["t"] == inner_cutoff]
    if not inner or any(row["asof"].edition_source["kind"] != "fda_zip" for row in inner):
        raise ValueError("T1 needs a fresh FDA ZIP at the inner TRAIN cutoff")
    observed = min(validation_days) - timedelta(days=1)
    inner_folds = [t2._fold(row["key"]) for row in inner]
    inner_raw = {arm: [None] * len(inner) for arm in devx.ARMS}
    fold_counts = {}
    for fold in sorted(set(inner_folds)):
        fit = [row for row in train if t2._fold(row["key"]) != fold]
        held = [i for i, group in enumerate(inner_folds) if group == fold]
        raw, _ = devx.raw_predictions(fit, [inner[i] for i in held], horizon, FLAGS, observed,
                                     extra_features=extra_features)
        fold_counts[str(fold)] = {"fit_rows": len(fit), "inner_held_rows": len(held)}
        for arm in devx.ARMS:
            for i, p in zip(held, raw[arm], strict=True):
                inner_raw[arm][i] = p

    config, calibrators = {}, {}
    for arm in devx.ARMS:
        inner_inputs = calibrator_inputs(inner_raw[arm])
        sigmoid = Logistic(feats=("logit",)).fit(t2._with_labels(inner_inputs, inner))
        inner_p = sigmoid.predict(inner_inputs)
        points = k20t1.choose_operating_points(arm, inner_p, [r["asof"].verdict for r in inner])
        config[arm] = {"calibrator": {"mean": sigmoid.mu[0], "scale": sigmoid.sd[0],
                                     "weight": sigmoid.w[0], "intercept": sigmoid.b},
                       "operating_points": points}
        calibrators[arm] = sigmoid
        for point in points:
            predictions, _ = k20t1.apply_policy(arm, inner, inner_p, horizon, point["threshold"])
            if sum(item.action != graph.ABSTAIN for item in predictions) != point["inner_answered"]:
                raise ValueError("Threshold enumeration disagrees with actual policy")

    raw, _ = devx.raw_predictions(train, validation, horizon, FLAGS, observed, extra_features=extra_features)
    labels = [r["y"] for r in validation]
    metrics = {}
    for arm, sigmoid in calibrators.items():
        val_p = sigmoid.predict(calibrator_inputs(raw[arm]))
        metrics[arm] = []
        for point in config[arm]["operating_points"]:
            predictions, conflicts = k20t1.apply_policy(arm, validation, val_p, horizon, point["threshold"])
            summary = k20t1.policy_metrics(predictions, labels, point["target"], conflicts)
            metrics[arm].append({"target": point["target"], **summary})
    return {"inner_cutoff": inner_cutoff.isoformat(), "inner_rows": len(inner),
            "inner_events": sum(row["y"] for row in inner), "inner_folds": fold_counts,
            "train_cutoffs": [d.isoformat() for d in days],
            "validation_cutoffs": [d.isoformat() for d in validation_days],
            "train_rows": len(train), "arms": config}, metrics


def code_sha():
    command = ["rtk", "proxy", "git"]
    tracked = ["loe-bench/loe_bench", "loe-bench/scripts", "docs/loe-bench/receipts/K20T1.md"]
    dirty = subprocess.check_output([*command, "status", "--porcelain", "--", *tracked], cwd=ROOT.parent,
                                    text=True).strip()
    if dirty:
        raise ValueError("Commit the code and protocol before the K20T1 run")
    return subprocess.check_output([*command, "log", "-1", "--format=%H", "--", *tracked[:2]],
                                   cwd=ROOT.parent, text=True).strip()


def run(args):
    if replay.LOCK_PATH.exists() or replay.ENV_NAME in os.environ:
        raise ValueError("K20T1 requires a closed test seal")
    revision = code_sha()
    receipt = ROOT.parent / "docs/loe-bench/receipts/K20T1.md"
    protocol = receipt.read_text(encoding="utf-8").split("\n## Results", 1)[0].strip()
    devx_result, ref_hash = replay._manifest(ROOT / "data/DEVX_results.json")
    retained = next(trial for trial in devx_result["trials"] if trial["id"] == "K07")["horizons"]
    reference = {h: {**retained[h]["candidate"], **cohort}
                 for h, cohort in devx_result["primary_cohorts"].items()}
    entities, builder, inputs = replay.inputs(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    manifest, nber_hash = replay._manifest(ROOT / "data/E8_NBER_MANIFEST.json")
    annual = k20t1.AnnualTrainingBuilder(builder, OBHistory(nber_sources(manifest, args.nber_dir)))
    for horizon, (_, validation) in replay.FORWARD.items():
        for day in training_dates(min(validation), horizon):
            source, _ = builder.select_edition(day)
            if source is not None:
                replay._verify(args.ob_dir / source.identity["file"], source.identity["sha256"])
    inputs.update(devx_reference=ref_hash, nber_manifest=nber_hash,
                  nber_archive=manifest["archive"], nber_members=manifest["tables"])

    primary, fits = compare_split("primary", replay.PRIMARY, entities, builder, annual, reference)
    adopted, gates = replay.adoption(primary)
    print(f"K20 primary decision: {'adopt' if adopted else 'retain baseline'}", flush=True)
    forward, _ = compare_split("forward", replay.FORWARD, entities, builder, annual, reference)
    horizons, policies = {}, {}
    extras = k20t1.EDITION_FEATURES if adopted else ()
    for horizon, (short, long, original, augmented, short_days, long_days, val_days) in fits.items():
        print(f"T1 {horizon}m inner calibration", flush=True)
        train, validation, days = ((long, augmented, long_days) if adopted else (short, original, short_days))
        horizons[str(horizon)], policies[str(horizon)] = fixed_policies(
            train, validation, days, val_days, horizon, extras)
    coverage_ok = all(point["within_tolerance"] for arms in policies.values()
                      for points in arms.values() for point in points)
    reach_ok = all(points[-1]["aurc80_reachable"] for arms in policies.values() for points in arms.values())
    features = [*MODEL_FEATURES, t2.AGE_SIGNAL, *CHALLENGE_FEATURES, *devx.BREADTH, *extras]
    frozen_inputs = {name: pin for name, pin in inputs.items()
                     if name != "devx_reference" and (adopted or not name.startswith("nber_"))}
    config = {"status": "PASS" if coverage_ok and reach_ok else "FAILED_DEVELOPMENT_ACCEPTANCE",
              "development_only": True, "code_commit_sha": revision, "input_sha256": frozen_inputs,
              "pipeline_flags": [*FLAGS, "K20"] if adopted else list(FLAGS), "horizons": horizons,
              "training_scope": {"nme_only": True, "observation_end": replay.DEVELOPMENT_END.isoformat(),
                                 "strict_horizon_embargo": True, "protected_start": replay.TEST_FIRST.isoformat()},
              "editions": {"fresh_zip_max_age_calendar_months": 6, "validation_zip_only": True,
                           "annual_training_fallback": adopted,
                           "challenge_filing_linkage": "E7b FDA ZIP only", "moiety_linkage": "FIX2c"},
              "features": {"B1": ["age_years"], "M1": features, "M3": [*features, *t2.VERDICT_FEATURES]},
              "model_settings": {"B1": {"bin_years": 1, "max_age": 30, "prior_strength": 5,
                                        "entry_probability_at_least": 0.5},
                                 "M1_M3": {"type": "L2 logistic", "l2": devx.L2, "epochs": 300,
                                           "learning_rate": 0.3, "standardization_floor": 1e-9}},
              "calibration_settings": {"type": "logistic sigmoid on clipped raw logit", "folds": t2.FOLDS,
                                       "drug_fold_hash": "first eight SHA-256 bytes, big-endian, modulo folds",
                                       "clip_epsilon": 1e-8, "l2": 1, "epochs": 300, "learning_rate": 0.3,
                                       "standardization_floor": 1e-9},
              "policy_settings": {"M1": "max(p, 1-p); entry iff p > 0.5", "M3": "evidence_graph.decide",
                                  "blocked_conflict_action": graph.ABSTAIN,
                                  "aurc80_operating_target": 0.9, "coverage_tolerance": 0.03}}
    return {"status": "DEVELOPMENT_ONLY", "code_commit_sha": revision, "input_sha256": inputs,
            "protocol_sha256": sha256(protocol.encode("utf-8")).hexdigest(),
            "runtime": {"python": platform.python_version(), "numpy": np.__version__},
            "k20": {"adopted": adopted, "gates": gates, "primary": primary, "forward": forward,
                    "baseline_primary_replay_verified": True,
                    "bootstrap": {"draws": t2.BOOTSTRAP_DRAWS, "seed": t2.BOOTSTRAP_SEED, "unit": "drug"}},
            "t1": {"coverage_tolerance_pass": coverage_ok, "aurc80_reachability_pass": reach_ok,
                   "horizons": policies}}, config


if __name__ == "__main__":
    base = Path(replay.DEFAULT_DIR).parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=base / "raw-20261127")
    parser.add_argument("--ob-dir", type=Path, default=Path(replay.DEFAULT_DIR))
    parser.add_argument("--piv-dir", type=Path, default=base / "piv")
    parser.add_argument("--challenge-dir", type=Path, default=base / "challenge")
    parser.add_argument("--nber-dir", type=Path, default=DEFAULT_NBER_DIR)
    trial, freeze = run(parser.parse_args())
    for name, value in (("K20T1_results.json", trial), ("K20T1_frozen_config.json", freeze)):
        output = ROOT / "data" / name
        output.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                          encoding="utf-8", newline="\n")
        print(output)
