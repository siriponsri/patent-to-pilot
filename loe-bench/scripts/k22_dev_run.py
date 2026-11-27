"""Compare K07 graph versions on sealed-off development validation only."""
import argparse
from collections import Counter
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import platform

import numpy as np

from k20t1_run import FLAGS, ROOT, calibrator_inputs, replay, verify_windows
from loe_bench import devx, evidence_graph, t2
from loe_bench.baselines import Logistic
from loe_bench.review_metrics import METRICS, ReviewQueue
from loe_bench.t2_features import AsOfBuilder


ARMS = ("M1", "M3_v1", "M3_v2")
PAIRS = (("M3_v2", "M3_v1"), ("M3_v2", "M1"), ("M3_v1", "M1"))
DRAWS, SEED = 2_000, 20261127


def verify_seal():
    if replay.LOCK_PATH.exists() or replay.ENV_NAME in os.environ:
        raise RuntimeError("K22 requires the test seal to remain closed")
    if replay.DEVELOPMENT_END != date(2016, 1, 1):
        raise RuntimeError("K22 expects the guarded DEVX development observation date")


def v2_rows(rows, builder, horizon):
    updated = []
    for row in rows:
        previous = row["asof"]
        candidate = builder.build(row["key"], row["t"], horizon, row["x"])
        if (candidate.x != previous.x or candidate.challenge != previous.challenge
                or candidate.edition_source != previous.edition_source):
            raise ValueError("graph versions must share raw features and sources")
        updated.append(dict(row, asof=candidate))
    return updated


def predict(train, validation, train_v2, validation_v2, horizon, observed):
    baseline, _ = devx.raw_predictions(train, validation, horizon, FLAGS, observed)
    revised, _ = devx.raw_predictions(train_v2, validation_v2, horizon, FLAGS, observed, arms=("M3",))
    return dict(M1=baseline["M1"], M3_v1=baseline["M3"], M3_v2=revised["M3"])


def calibrate(train, train_v2, horizon, observed):
    inner = max(row["t"] for row in train)
    inner_rows = [i for i, row in enumerate(train) if row["t"] == inner]
    folds = [t2._fold(row["key"]) for row in train]
    oof = {arm: [None] * len(train) for arm in ARMS}
    for fold in sorted({folds[i] for i in inner_rows}):
        fit = [i for i, group in enumerate(folds) if group != fold]
        held = [i for i in inner_rows if folds[i] == fold]
        raw = predict([train[i] for i in fit], [train[i] for i in held],
                      [train_v2[i] for i in fit], [train_v2[i] for i in held], horizon, observed)
        for arm, values in raw.items():
            for i, value in zip(held, values, strict=True):
                oof[arm][i] = value
    return {arm: Logistic(feats=("logit",)).fit(t2._with_labels(
        calibrator_inputs([scores[i] for i in inner_rows]), [train[i] for i in inner_rows]))
        for arm, scores in oof.items()}


def policy_losses(rows, horizon, arm, probabilities, labels):
    actions = []
    for row, p in zip(rows, probabilities, strict=True):
        if arm == "M1":
            action = (evidence_graph.PREDICT_ENTRY if p >= 0.5 else evidence_graph.PREDICT_NO_ENTRY
                      if p <= 0.05 else evidence_graph.ABSTAIN)
        else:
            asof = row["asof"]
            decision = evidence_graph.decide(
                asof.snapshot, row["t"], horizon, p, lo=0.05, hi=0.5, graph_version=asof.graph_version,
                challenge_evidence=asof.challenge.state if asof.challenge else None,
            )
            if decision["verdict"] != asof.verdict:
                raise ValueError("M3 model and policy must use the same graph version")
            action = decision["action"]
        actions.append(action)
    actions = np.asarray(actions)
    flag = actions == evidence_graph.PREDICT_ENTRY
    clear = actions == evidence_graph.PREDICT_NO_ENTRY
    refer = actions == evidence_graph.ABSTAIN
    counts = {name: {"rows": int(mask.sum()), "events": int(labels[mask].sum())}
              for name, mask in (("clear", clear), ("flag", flag), ("refer", refer))}
    return 10 * clear * labels + flag * (1 - labels) + 0.5 * refer, counts


def intervals(point, draws):
    result = {}
    for metric, level, sample in zip(METRICS, point, draws.T, strict=True):
        valid = sample[np.isfinite(sample)]
        result[metric] = {"point": float(level) if np.isfinite(level) else None,
                          "ci95": np.percentile(valid, [2.5, 97.5]).tolist() if valid.size else None,
                          "valid_draws": int(valid.size), "invalid_draws": int(len(sample) - valid.size)}
    return result


def evaluate(validation, validation_v2, horizon, native, calibrators):
    labels = np.asarray([row["y"] for row in validation])
    drugs, drug_ids = np.unique([row["key"] for row in validation], return_inverse=True)
    cutoffs = np.asarray([row["t"] for row in validation])
    queues = {arm: ReviewQueue(native[arm], cutoffs) for arm in ARMS}
    losses, counts = {}, {}
    for arm in ARMS:
        rows = validation_v2 if arm == "M3_v2" else validation
        calibrated = calibrators[arm].predict(calibrator_inputs(native[arm]))
        losses[arm], counts[arm] = policy_losses(rows, horizon, arm, calibrated, labels)

    def score(weights):
        return np.array([queues[arm].measure(labels, losses[arm], weights) for arm in ARMS])

    unit = np.ones(len(labels))
    point = score(unit)
    rng = np.random.default_rng(SEED)
    draws = np.array([score(np.bincount(rng.integers(len(drugs), size=len(drugs)), minlength=len(drugs))[drug_ids])
                      for _ in range(DRAWS)])
    by_version = {version: dict.fromkeys(t2.VERDICTS, 0) | dict(Counter(row["asof"].verdict for row in rows))
                  for version, rows in (("v1", validation), ("v2", validation_v2))}
    return {
        "rows": len(labels), "event_rows": int(labels.sum()), "drug_clusters": len(drugs),
        "event_drugs": len(np.unique(drug_ids[labels == 1])),
        "slots_by_cutoff": {cutoff.isoformat(): int((cutoffs == cutoff).sum()) // 5 for cutoff in np.unique(cutoffs)},
        "verdicts": by_version,
        "actions": counts,
        "distinct_event_drugs_expected_captured": {
            arm: queues[arm].distinct_event_drugs(labels, drug_ids, unit) for arm in ARMS},
        "levels": {arm: intervals(point[i], draws[:, i]) for i, arm in enumerate(ARMS)},
        "contrasts": {f"{left}_minus_{right}": intervals(
            point[ARMS.index(left)] - point[ARMS.index(right)],
            draws[:, ARMS.index(left)] - draws[:, ARMS.index(right)]) for left, right in PAIRS},
    }


def run(args):
    verify_seal()
    entities, builder, sources = replay.inputs(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    revised = AsOfBuilder(builder.history, linker=builder.linker, challenge=builder.challenge, graph_version="v2")
    horizons = {}
    for horizon, (training_days, validation_days) in sorted(replay.PRIMARY.items(), reverse=True):
        verify_windows(training_days, validation_days, horizon)
        t2.require_development_cutoffs((*training_days, *validation_days))
        train = replay.partition(entities, builder, training_days, horizon, training=True)
        validation = replay.partition(entities, builder, validation_days, horizon)
        train_v2, val_v2 = (v2_rows(rows, revised, horizon) for rows in (train, validation))
        observed = min(validation_days) - timedelta(days=1)
        calibrators = calibrate(train, train_v2, horizon, observed)
        native = predict(train, validation, train_v2, val_v2, horizon, observed)
        horizons[horizon] = evaluate(validation, val_v2, horizon, native, calibrators)
        horizons[horizon]["training_rows"] = len(train)
        horizons[horizon]["training_cutoffs"] = [day.isoformat() for day in training_days]

    def delta(horizon):
        return horizons[horizon]["contrasts"]["M3_v2_minus_M3_v1"]["recall20"]["point"]

    contested = {version: sum(data["verdicts"][version]["CONTESTED"] for data in horizons.values())
                 for version in ("v1", "v2")}
    gates = {"recall_gain_24_ge_0.02": delta(24) is not None and delta(24) >= 0.02,
             "recall_gain_12_ge_minus_0.02": delta(12) is not None and delta(12) >= -0.02,
             "fewer_contested": contested["v2"] < contested["v1"]}
    verify_seal()
    code = ("loe_bench/regulatory_graph.py", "loe_bench/evidence_graph.py", "loe_bench/t2_features.py",
            "loe_bench/review_metrics.py", "scripts/k22_dev_run.py")
    return {"role": "DEVELOPMENT_ONLY", "development_observed_through": replay.DEVELOPMENT_END.isoformat(),
            "python": platform.python_version(), "numpy": np.__version__, "sources": sources,
            "code_sha256_lf": {name: hashlib.sha256((ROOT / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                               for name in code},
            "bootstrap_seed": SEED, "bootstrap_draws": DRAWS, "raw_features_matched": True,
            "pooled_contested": contested, "gates": gates, "decision": "ADOPT_V2" if all(gates.values()) else "RETAIN_V1",
            "horizons": horizons}


if __name__ == "__main__":
    ob = Path(replay.DEFAULT_DIR)
    base = ob.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=base / "raw-20261127")
    parser.add_argument("--ob-dir", type=Path, default=ob)
    parser.add_argument("--piv-dir", type=Path, default=base / "piv")
    parser.add_argument("--challenge-dir", type=Path, default=base / "challenge")
    output = ROOT / "data/K22_trial.json"
    result = run(parser.parse_args())
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
                      encoding="utf-8", newline="\n")
    print(f"{result['decision']} | {output}")
