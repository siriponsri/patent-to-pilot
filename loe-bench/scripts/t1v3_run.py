"""Fit and evaluate criteria v3 on the sealed E7b + K07 development split."""
import argparse
from datetime import date, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess

# Reuse the merged DEVX import compatibility shim and pre-decode projector.
from k20t1_run import calibrator_inputs, replay, verify_windows
import numpy as np

from loe_bench import devx, evidence_graph as graph, t1v3, t2
from loe_bench.baselines import Logistic
from loe_bench.seal import TestSealError
from loe_bench.t2_features import CHALLENGE_FEATURES, MODEL_FEATURES


ROOT = replay.ROOT
RECEIPT = "docs/loe-bench/receipts/T1v3.md"
CODE_PATHS = ("loe-bench/loe_bench", "loe-bench/scripts")
FLAGS = ("K07",)
HYPOTHESES = {"H1": (24, "M3-B1"), "H2": (24, "M3-M1"), "H3": (12, "M3-B1")}


def require_closed_seal():
    if replay.LOCK_PATH.exists() or replay.ENV_NAME in os.environ:
        raise TestSealError("T1v3 requires the closed development seal")
    if replay.DEVELOPMENT_END != date(2016, 1, 1):
        raise TestSealError("T1v3 requires the pinned development observation end")


def code_revision():
    cmd = ["rtk", "proxy", "git"]

    def git(*args):
        return subprocess.check_output([*cmd, *args], cwd=ROOT.parent, text=True).strip()

    if git("status", "--porcelain", "--", *CODE_PATHS, RECEIPT):
        raise ValueError("Commit the implementation and receipt protocol before scoring")
    return git("log", "-1", "--format=%H", "--", *CODE_PATHS)


def native(train, forecast, horizon, observed_through):
    raw, age = devx.raw_predictions(train, forecast, horizon, FLAGS, observed_through)
    return {"B1": age, **raw}


def fit_inner(train, horizon, observed_through):
    inner_day = max(row["t"] for row in train)
    inner = [row for row in train if row["t"] == inner_day]
    if any((row["asof"].edition_source or {}).get("kind") != "fda_zip" for row in inner):
        raise ValueError("Inner TRAIN cutoff requires the fresh FDA ZIP")
    folds = [t2._fold(row["key"]) for row in inner]
    inner_scores = {arm: [None] * len(inner) for arm in t1v3.ARMS}
    fold_counts = {}
    for fold in sorted(set(folds)):
        fit = [row for row in train if t2._fold(row["key"]) != fold]
        held = [i for i, group in enumerate(folds) if group == fold]
        scores = native(fit, [inner[i] for i in held], horizon, observed_through)
        fold_counts[str(fold)] = {"fit_rows": len(fit), "held_rows": len(held)}
        for arm in t1v3.ARMS:
            for idx, probability in zip(held, scores[arm], strict=True):
                inner_scores[arm][idx] = probability
    labels = [row["y"] for row in inner]
    calibrators, policies = {}, {}
    for arm, scores in inner_scores.items():
        inputs = calibrator_inputs(scores)
        sigmoid = Logistic(feats=("logit",)).fit(t2._with_labels(inputs, inner))
        p = sigmoid.predict(inputs)
        blocked = [arm == "M3" and row["asof"].verdict == "BLOCKED" for row in inner]
        lo, hi = t1v3.choose_thresholds(p, labels, blocked)
        inner_actions = t1v3.policy_metrics(arm, inner, horizon, p, lo, hi)
        budget = len(inner) // t1v3.REVIEW_DIVISOR
        if (inner_actions["flag_rows"] > budget
                or (inner_actions["clear_event_rate"] or 0) > t1v3.CLEAR_EVENT_LIMIT):
            raise ValueError("Inner actions exceed the declared flag or missed-clear target")
        calibrators[arm] = sigmoid
        policies[arm] = {
            "calibrator": {"mean": sigmoid.mu[0], "scale": sigmoid.sd[0],
                           "weight": sigmoid.w[0], "intercept": sigmoid.b},
            "lo": lo, "hi": hi, "inner": inner_actions,
        }
    return calibrators, policies, {
        "cutoff": inner_day.isoformat(), "rows": len(inner), "events": sum(labels),
        "fold_counts": fold_counts, "flag_capacity": budget,
    }


def evaluate_horizon(entities, builder, horizon):
    train_days, validation_days = replay.PRIMARY[horizon]
    verify_windows(train_days, validation_days, horizon)
    observed_through = min(validation_days) - timedelta(days=1)
    train = replay.partition(entities, builder, train_days, horizon, training=True)
    calibrators, policies, inner = fit_inner(train, horizon, observed_through)
    validation = replay.partition(entities, builder, validation_days, horizon)
    native_scores = native(train, validation, horizon, observed_through)
    queue = t1v3.bootstrap(t1v3.QueuePanel(validation, validation_days, native_scores))
    outcomes = {}
    for arm in t1v3.ARMS:
        lo, hi = policies[arm]["lo"], policies[arm]["hi"]
        p = calibrators[arm].predict(calibrator_inputs(native_scores[arm]))
        outcomes[arm] = t1v3.policy_metrics(arm, validation, horizon, p, lo, hi)
        by_cutoff = {}
        for day in validation_days:
            indices = [i for i, row in enumerate(validation) if row["t"] == day]
            by_cutoff[day.isoformat()] = t1v3.policy_metrics(
                arm, [validation[i] for i in indices], horizon, [p[i] for i in indices], lo, hi)
        outcomes[arm]["by_cutoff"] = by_cutoff
    config = {"train_cutoffs": [d.isoformat() for d in train_days], "train_rows": len(train),
              "train_labels_observed_through": observed_through.isoformat(),
              "validation_cutoffs": [d.isoformat() for d in validation_days], "inner": inner,
              "arms": policies}
    return config, {"rows": len(validation), "drugs": len({row["key"] for row in validation}),
                    "queue": queue, "policy": outcomes}


def acceptance(horizons):
    capacity_failures, safety_failures, undefined = [], [], []
    for horizon, result in horizons.items():
        queue = result["queue"]
        for arm, value in queue["arms"].items():
            for roster, allocation in zip(queue["cutoffs"], value["cutoffs"], strict=True):
                if allocation["allocated_slots"] != roster["capacity"]:
                    capacity_failures.append(f"{horizon}m {arm} {roster['cutoff']}: queue size mismatch")
        if queue["undefined_draws"] or any(
                v["ci95"] is None for arm in queue["levels"].values() for v in arm.values()):
            undefined.append(f"{horizon}m: queue has an undefined point estimate or bootstrap draw")
        for arm, policy in result["policy"].items():
            ci = policy["clear_event_ci95"]
            if ci is None:
                safety_failures.append(f"{horizon}m {arm}: no validation auto-clears, safety unevaluable")
            elif ci[1] > t1v3.VALIDATION_UPPER_LIMIT:
                safety_failures.append(f"{horizon}m {arm}: auto-clear upper 95% bound {ci[1]:.6g} exceeds 3%")
            for metric in ("clear_event_rate", "flag_precision", "flag_recall", "refer_rate"):
                if policy[metric] is None:
                    undefined.append(f"{horizon}m {arm}: {metric} undefined")
    return {"queue_capacity": capacity_failures, "auto_clear_safety": safety_failures, "defined": undefined}


def run(args):
    require_closed_seal()
    revision = code_revision()
    protocol = (ROOT.parent / RECEIPT).read_text(encoding="utf-8").split("\n## Results", 1)[0].strip()
    entities, builder, inputs = replay.inputs(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    configs, results = {}, {}
    for horizon in replay.HORIZONS:
        print(f"T1v3 {horizon} months: fit inner policies and score primary development", flush=True)
        configs[str(horizon)], results[str(horizon)] = evaluate_horizon(entities, builder, horizon)
    failures = acceptance(results)
    require_closed_seal()

    common = {"code_commit_sha": revision, "input_sha256": inputs,
              "protocol_sha256": sha256(protocol.encode("utf-8")).hexdigest(),
              "runtime": {"python": platform.python_version(), "numpy": np.__version__}}
    features = [*MODEL_FEATURES, t2.AGE_SIGNAL, *CHALLENGE_FEATURES, *devx.BREADTH]
    settings = {"epochs": 300, "learning_rate": 0.3, "standardization_floor": 1e-9}
    config = {
        **common,
        "status": "FAILED_DEVELOPMENT_ACCEPTANCE" if any(failures.values()) else "FROZEN_FOR_PREREG",
        "development_only": True, "acceptance_failures": failures,
        "pipeline": "E7b + K07; FIX2c; fresh FDA ZIPs only for presentation breadth",
        "cohort": {"track": "Track C NME only", "observation_end": replay.DEVELOPMENT_END.isoformat(),
                   "test_first": replay.TEST_FIRST.isoformat(), "strict_train_embargo": True,
                   "max_fda_zip_staleness_calendar_months": 6},
        "features": {"B1": ["age_years"], "M1": features, "M3": [*features, *t2.VERDICT_FEATURES]},
        "model_settings": {
            "B1": {"type": "age hazard table", "bin_years": 1, "age_clip": [0, 30],
                   "prior_strength": 5, "prior_and_unseen_bin": "TRAIN event prevalence"},
            "M1_M3": {"type": "L2 logistic", "l2": devx.L2, "initial_weights_and_intercept": 0,
                      "age_feature": "B1 probability logit clipped at 1e-8 and 1 - 1e-8", **settings},
        },
        "calibration_settings": {
            "type": "logistic sigmoid on clipped raw logit", "l2": 1, "clip_epsilon": 1e-8,
            "folds": t2.FOLDS, "fold_hash": "first 8 SHA-256 bytes of drug key, big-endian, modulo 5",
            "fit_on": "out-of-fold TRAIN predictions at final TRAIN cutoff", **settings,
        },
        "native_scores": {"B1": "uncalibrated age-hazard probability", "M1": "uncalibrated logistic risk",
                          "M3": "uncalibrated graph-feature logistic risk before actions"},
        "queue": {"rank": "descending native entry risk per cutoff", "capacity": "floor(N_t / 5)",
                  "tie": "uniform without replacement within boundary, independent across cutoffs",
                  "pooling": "sum expected hits and divide by total event rows or slots"},
        "bootstrap": {"unit": "whole drug history with replacement", "draws": t2.BOOTSTRAP_DRAWS,
                      "seed_per_horizon": t2.BOOTSTRAP_SEED, "generator": "NumPy default_rng (PCG64)",
                      "ci": "percentile 95%", "undefined_replicate": "unevaluable"},
        "policy_settings": {
            "actions": "clear at p <= lo, flag at p >= hi, refer otherwise",
            "M3": f"evidence_graph.decide with {graph.ABSTAIN} on BLOCKED conflicts; all clears require p <= lo",
            "hi": "lowest observed inner threshold with at most floor(N/5) flags; 1.0 fallback",
            "lo": "largest observed inner threshold below hi with clear event rate <= 1%; 0.0 fallback",
            "inner_clear_event_limit": t1v3.CLEAR_EVENT_LIMIT,
            "validation_clear_upper_limit": t1v3.VALIDATION_UPPER_LIMIT,
            "clear_ci": "95% two-sided conservative cluster Chernoff inversion conditional on observed clears",
        },
        "horizons": configs,
    }
    family = {name: {"horizon": horizon, "contrast": pair,
                     **results[str(horizon)]["queue"]["contrasts"][pair]["recall"]}
              for name, (horizon, pair) in HYPOTHESES.items()}
    return {**common, "status": "DEVELOPMENT_ONLY", "horizons": results, "family": family}, config


if __name__ == "__main__":
    base = Path(replay.DEFAULT_DIR).parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=base / "raw-20261127")
    parser.add_argument("--ob-dir", type=Path, default=Path(replay.DEFAULT_DIR))
    parser.add_argument("--piv-dir", type=Path, default=base / "piv")
    parser.add_argument("--challenge-dir", type=Path, default=base / "challenge")
    metrics, config = run(parser.parse_args())
    for name, value in (("T1v3_results.json", metrics), ("T1v3_frozen_config.json", config)):
        output = ROOT / "data" / name
        output.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                          encoding="utf-8", newline="\n")
        print(output)
