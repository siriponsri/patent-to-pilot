"""Produce the canonical criteria v3 report from guarded development inputs."""
import argparse
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess

import t1v3_run as t1
import numpy as np

from loe_bench import devx, evidence_graph as graph, k20t1, metrics, power, t1v3, t2
from loe_bench.baselines import Logistic
from loe_bench.common import add_months
from loe_bench.ob_history import OBHistory
from loe_bench.review_metrics import ReviewQueue
from loe_bench.t2_features import CHALLENGE_FEATURES, MODEL_FEATURES, edition_coverage


DATA = t1.ROOT / "data"
CODE = ("loe-bench/loe_bench", "loe-bench/scripts")
ARMS = t1v3.ARMS
METRICS = (*t1v3.METRICS, "average_precision", "decision_loss", "aurc80", "e_aurc", "brier", "ece")
COSTS = {"missed_clear": 10, "false_flag": 1, "referral": 0.5}


def parser(description):
    ob = Path(t1.replay.DEFAULT_DIR)
    base = ob.parent
    args = argparse.ArgumentParser(description=description)
    args.add_argument("--raw", type=Path, default=base / "raw-20261127")
    args.add_argument("--ob-dir", type=Path, default=ob)
    args.add_argument("--piv-dir", type=Path, default=base / "piv")
    args.add_argument("--challenge-dir", type=Path, default=base / "challenge")
    return args


def read_json(name):
    return json.loads((DATA / name).read_bytes())


def manifest(name):
    content = (DATA / name).read_bytes().replace(b"\r\n", b"\n")
    return {"file": name, "sha256": sha256(content).hexdigest(), "line_endings": "LF"}


def write_json(name, value):
    path = DATA / name
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    path.write_bytes(data)
    print(f"{name} {sha256(data).hexdigest()}", flush=True)
    return sha256(data).hexdigest()


def code_revision():
    def git(*args):
        return subprocess.check_output(["rtk", "proxy", "git", *args], cwd=t1.ROOT.parent, text=True).strip()

    if git("status", "--porcelain", "--", *CODE):
        raise ValueError("Commit implementation before generating the freeze")
    return git("log", "-1", "--format=%H", "--", *CODE)


def inner_fits(train, horizon, observed):
    """Use the T1v3 OOF procedure and retain the legacy confidence operating point."""
    day = max(row["t"] for row in train)
    inner = [row for row in train if row["t"] == day]
    if any((row["asof"].edition_source or {}).get("kind") != "fda_zip" for row in inner):
        raise ValueError("Inner cutoff requires a fresh FDA ZIP")
    folds = [t2._fold(row["key"]) for row in inner]
    scores = {arm: [None] * len(inner) for arm in ARMS}
    counts = {}
    for fold in sorted(set(folds)):
        fit = [row for row in train if t2._fold(row["key"]) != fold]
        held = [i for i, group in enumerate(folds) if group == fold]
        predicted = t1.native(fit, [inner[i] for i in held], horizon, observed)
        counts[str(fold)] = {"fit_rows": len(fit), "held_rows": len(held)}
        for arm in ARMS:
            for i, value in zip(held, predicted[arm], strict=True):
                scores[arm][i] = value
    labels = [row["y"] for row in inner]
    verdicts = [row["asof"].verdict for row in inner]
    fits, policies = {}, {}
    for arm in ARMS:
        inputs = t1.calibrator_inputs(scores[arm])
        fitted = Logistic(feats=("logit",)).fit(t2._with_labels(inputs, inner))
        p = fitted.predict(inputs)
        lo, hi = t1v3.choose_thresholds(p, labels, [arm == "M3" and v == "BLOCKED" for v in verdicts])
        audit = t1v3.policy_metrics(arm, inner, horizon, p, lo, hi)
        if audit["flag_rows"] > len(inner) // 5 or (audit["clear_event_rate"] or 0) > t1v3.CLEAR_EVENT_LIMIT:
            raise ValueError("Inner policy exceeds training flag or missed-clear target")
        legacy = k20t1.choose_operating_points("M3" if arm == "M3" else "M1", p, verdicts)[-1]
        policies[arm] = {"lo": lo, "hi": hi, "inner_policy": audit, "legacy_90": legacy,
                         "calibrator": {"mean": fitted.mu[0], "scale": fitted.sd[0],
                                        "weight": fitted.w[0], "intercept": fitted.b}}
        fits[arm] = fitted
    return fits, policies, {"cutoff": day.isoformat(), "rows": len(inner), "events": sum(labels),
                             "fold_counts": counts}


def full_area(counts, errors, total, harmonic):
    """Right-step selective risk at all prefixes, averaging exact confidence ties."""
    previous = counts.cumsum() - counts
    prior_errors = errors.cumsum() - errors
    risk = errors / np.maximum(counts, 1)
    integral = counts * risk + (prior_errors - previous * risk) * (
        harmonic[previous + counts] - harmonic[previous])
    return integral.sum() / total


def legacy_summary(predictions, labels, conflicts):
    summary = k20t1.policy_metrics(predictions, labels, 0.9, conflicts)
    summary["e_aurc"] = None
    if summary["answered"] == len(labels):
        errors = summary["errors"]
        oracle = full_area(np.array([len(labels) - errors, errors]), np.array([0, errors]),
                           len(labels), power.harmonic_numbers(len(labels)))
        summary["e_aurc"] = metrics.aurc([p.probability for p in predictions], labels,
                                         scores=[p.score for p in predictions],
                                         actions=[p.action for p in predictions]) - oracle
    return summary


class Secondary:
    def __init__(self, rows, horizon, arm, native, p, policy):
        self.labels = np.array([row["y"] for row in rows])
        self.queue = ReviewQueue(native, [row["t"] for row in rows])
        lo, hi = policy["lo"], policy["hi"]
        actions = np.array([t1v3.action(arm, row, horizon, prob, lo, hi)[0]
                            for row, prob in zip(rows, p, strict=True)])
        self.losses = (COSTS["missed_clear"] * (actions == graph.PREDICT_NO_ENTRY) * self.labels
                       + COSTS["false_flag"] * (actions == graph.PREDICT_ENTRY) * (1 - self.labels)
                       + COSTS["referral"] * (actions == graph.ABSTAIN))
        p = np.asarray(p)
        self.errors = ((p >= 0.5) != self.labels).astype(int)
        self.confidence_bins = np.unique(-np.maximum(p, 1 - p), return_inverse=True)[1]
        self.ece_bins = np.searchsorted(np.arange(1, 10) / 10, p, side="right")
        self.residuals = p - self.labels

    def measure(self, weights, harmonic):
        _, _, ap, loss = self.queue.measure(self.labels, self.losses, weights)
        total = int(weights.sum())
        counts = np.bincount(self.confidence_bins, weights).astype(int)
        errors = np.bincount(self.confidence_bins, weights * self.errors).astype(int)
        auc80 = float(power.area(counts, errors, total, harmonic))
        n_errors = int(errors.sum())
        oracle = full_area(np.array([total - n_errors, n_errors]), np.array([0, n_errors]), total, harmonic)
        excess = full_area(counts, errors, total, harmonic) - oracle
        brier = weights @ (self.residuals ** 2) / total
        calibration_counts = np.bincount(self.ece_bins, weights * self.residuals, minlength=10)
        return [ap, loss, auc80, excess, brier, np.abs(calibration_counts).sum() / total]


def with_intervals(panel, secondary):
    n = len(panel.keys)
    point = panel.evaluate(np.ones(n, dtype=int))
    harmonic = power.harmonic_numbers(n * len(panel.cutoffs))

    def measure(summary, copies):
        w = copies[panel.groups]
        return np.asarray([[*(summary["arms"][arm][metric] for metric in t1v3.METRICS),
                            *secondary[arm].measure(w, harmonic)] for arm in ARMS], dtype=float)

    values = measure(point, np.ones(n, dtype=int))
    rng = np.random.default_rng(t2.BOOTSTRAP_SEED)
    draws = []
    for _ in range(t2.BOOTSTRAP_DRAWS):
        copies = np.bincount(rng.integers(n, size=n), minlength=n)
        draws.append(measure(panel.evaluate(copies), copies))
    samples = np.stack(draws)

    def intervals(levels, distribution):
        return {name: t1v3.interval(float(v) if np.isfinite(v) else None, d)
                for name, v, d in zip(METRICS, levels, distribution.T, strict=True)}

    point["levels"] = {arm: intervals(values[i], samples[:, i]) for i, arm in enumerate(ARMS)}
    point["contrasts"] = {}
    for left, right in t1v3.PAIRS:
        a, b = ARMS.index(left), ARMS.index(right)
        point["contrasts"][f"{left}-{right}"] = intervals(values[a] - values[b], samples[:, a] - samples[:, b])
    point["undefined_draws"] = int(np.count_nonzero(~np.isfinite(samples).all(axis=(1, 2))))
    return point


def evaluate(entities, builder, horizon):
    train_days, validation_days = t1.replay.PRIMARY[horizon]
    t1.verify_windows(train_days, validation_days, horizon)
    observed = min(validation_days) - timedelta(days=1)
    train = t1.replay.partition(entities, builder, train_days, horizon, training=True)
    fits, policies, inner = inner_fits(train, horizon, observed)
    rows = t1.replay.partition(entities, builder, validation_days, horizon)
    native = t1.native(train, rows, horizon, observed)
    validation, secondary = {}, {}
    for arm in ARMS:
        p = fits[arm].predict(t1.calibrator_inputs(native[arm]))
        policy = policies[arm]
        secondary[arm] = Secondary(rows, horizon, arm, native[arm], p, policy)
        action = t1v3.policy_metrics(arm, rows, horizon, p, policy["lo"], policy["hi"])
        ci = action["clear_event_ci95"]
        action["auto_clear_safety"] = "UNEVALUABLE" if ci is None else (
            "PASS" if ci[1] <= t1v3.VALIDATION_UPPER_LIMIT else "FAIL")
        legacy, conflicts = k20t1.apply_policy(arm, rows, p, horizon, policy["legacy_90"]["threshold"])
        validation[arm] = {
            "asymmetric_policy": action,
            "legacy_policy_90": legacy_summary(legacy, [r["y"] for r in rows], conflicts),
            "ece_bin_counts": np.bincount(secondary[arm].ece_bins, minlength=10).tolist(),
        }
    panel = t1v3.QueuePanel(rows, validation_days, native)
    report = with_intervals(panel, secondary)
    report.update(rows=len(rows), drug_clusters=len(panel.keys), policy=validation)
    return report, {"train_cutoffs": [d.isoformat() for d in train_days], "train_rows": len(train),
                    "train_labels_observed_through": observed.isoformat(), "inner": inner, "arms": policies,
                    "validation_cutoffs": [d.isoformat() for d in validation_days]}


def sealed_schedule():
    end = date.fromisoformat(read_json("S0_INPUT_MANIFEST.json")["t0"])
    history = OBHistory.from_records(read_json("OB_EDITIONS.json"))
    horizons = {}
    for h in t1.replay.HORIZONS:
        candidates = [date(year, 1, 1) for year in range(t1.replay.TEST_FIRST.year, end.year + 1)
                      if add_months(date(year, 1, 1), h) <= end]
        fresh = [d for d in candidates if edition_coverage(history, d)["status"] == "FRESH"]
        horizons[str(h)] = {"candidates": [d.isoformat() for d in candidates],
                            "test_cutoffs": [d.isoformat() for d in fresh]}
    return {"test_first": t1.replay.TEST_FIRST.isoformat(), "outcomes_observed_through": end.isoformat(),
            "schedule": horizons, "track": "C-prime; at-risk Track C active-moiety NME rows",
            "freshness": "FDA ZIP edition within six calendar months with verified availability by cutoff",
            "min_distinct_event_drug_clusters": 50, "cluster_gate_horizon": 24,
            "gate_script": "scripts/freeze_gate.py", "gate_status": "NOT_RUN",
            "strict_post_2023": "descriptive sensitivity only",
            "fallback": "C-prime feasibility; Track A prospective replication"}


def run(args):
    t1.require_closed_seal()
    revision = code_revision()
    entities, builder, sources = t1.replay.inputs(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    for key in ("s0_manifest", "ob_manifest", "piv_manifest", "court_manifest"):
        sources[key] = manifest(sources[key]["file"])
    sources["nber_manifest"] = {**manifest("E8_NBER_MANIFEST.json"), "admission": "EXCLUDED_REJECTED_K20"}
    sources["rai"] = read_json("E7_sources.json")["rai"]
    results, settings = {}, {}
    for horizon in t1.replay.HORIZONS:
        print(f"FREEZE {horizon} months: train and evaluate development", flush=True)
        results[str(horizon)], settings[str(horizon)] = evaluate(entities, builder, horizon)
    gates = {"queue_capacity": all(
        all(c["allocated_slots"] == r["capacity"] for c, r in zip(a["cutoffs"], h["cutoffs"], strict=True))
        for h in results.values() for a in h["arms"].values()),
        "defined_endpoints": all(
            v["ci95"] is not None for h in results.values() for kind in ("levels", "contrasts")
            for metrics in h[kind].values() for v in metrics.values())}
    family = {name: {"horizon": h, "contrast": pair, **results[str(h)]["contrasts"][pair]["recall"]}
              for name, (h, pair) in t1.HYPOTHESES.items()}
    common = {"code_commit_sha": revision, "input_sha256": sources,
              "runtime": {"python": platform.python_version(), "numpy": np.__version__}}
    features = [*MODEL_FEATURES, t2.AGE_SIGNAL, *CHALLENGE_FEATURES, *devx.BREADTH]
    optimization = {"epochs": 300, "learning_rate": 0.3, "standardization_floor": 1e-9,
                    "initial_weights_and_intercept": 0}
    config = {
        **common, "status": "FROZEN_FOR_PREREG" if all(gates.values()) else "FAILED_DEVELOPMENT_ACCEPTANCE",
        "development_only": True, "acceptance": gates, "horizons": settings, "sealed_test": sealed_schedule(),
        "development_observed_through": t1.replay.DEVELOPMENT_END.isoformat(), "strict_split_embargo": True,
        "pipeline": "FIX2c active moiety; E7b challenge with REG undated PIV fix; K07 FDA ZIP breadth",
        "features": {"B1": ["age_years"], "M1": features, "M3": [*features, *t2.VERDICT_FEATURES]},
        "model_settings": {
            "graph_version": "v1", "B1": {"type": "age-hazard", "bin_years": 1, "age_clip": [0, 30],
                                          "prior_strength": 5, "prior_and_unseen_bin": "TRAIN prevalence"},
            "M1_M3": {"type": "L2 logistic", "l2": devx.L2, "age_feature": "B1 clipped logit", **optimization}},
        "calibration": {"type": "logistic sigmoid on native logit", "l2": 1, "clip_epsilon": 1e-8,
                        "folds": t2.FOLDS, "fold_hash": "first 8 SHA-256 bytes of UTF-8 drug key, big-endian mod 5",
                        "fit_on": "whole-drug out-of-fold TRAIN scores at latest TRAIN cutoff", **optimization},
        "native_scores": {"B1": "uncalibrated age-hazard probability", "M1": "uncalibrated logistic risk",
                          "M3": "uncalibrated graph-feature logistic risk before M3 actions"},
        "queue": {"capacity": "floor(N_t/5)", "fraction": 0.20, "rank": "descending native score per cutoff",
                  "tie": "uniform without replacement; independent across cutoffs",
                  "other_rows": "evaluator's normal process"},
        "policy": {"status": "SECONDARY_NOT_RECOMMENDED_FOR_AUTO_CLEAR",
                   "hi": "lowest observed inner score with flags <= floor(N/5); fallback 1",
                   "lo": "highest observed inner score below hi with missed-clear rate <= 1%; fallback 0",
                   "actions": "clear p <= lo; flag p >= hi; refer other rows and M3 BLOCKED conflicts",
                   "costs": COSTS, "clear_safety_limit": t1v3.VALIDATION_UPPER_LIMIT,
                   "clear_ci": "95% cluster Chernoff inversion on the observed clear roster"},
        "endpoints": {"primary": "pooled event-row recall@20% with expected ties",
                      "fixed_sequence": [{"name": name, "horizon": h, "contrast": p}
                                         for name, (h, p) in t1.HYPOTHESES.items()],
                      "alpha": "T4 owner disposition pending; apply criteria v3 rule before preregistration",
                      "useful_recall_difference": 0.10, "event": "first final ANDA approval in (cutoff, cutoff+h]",
                      "secondary": list(METRICS[1:]), "AP": "grouped native-score average precision",
                      "distinct_event_drug_capture": "expected fraction with at least one event row queued",
                      "AURC80": "calibrated probability-only classification at 0.5, max(p,1-p) confidence",
                      "E-AURC": "full probability-only AURC minus discrete correct-first oracle",
                      "legacy_AURC80": "K20T1 TRAIN 90% target; requires observed coverage >= 80%",
                      "legacy_E-AURC": "K20T1 TRAIN 90% target; requires full observed coverage",
                      "ECE": "10 equal-width bins on calibrated probabilities"},
        "bootstrap": {"unit": "whole drug history with replacement", "draws": t2.BOOTSTRAP_DRAWS,
                      "seed_per_horizon": t2.BOOTSTRAP_SEED, "rng": "NumPy default_rng PCG64",
                      "ci": "two-sided percentile 95% for development", "undefined_replicate": "unevaluable"},
    }
    t1.require_closed_seal()
    return {**common, "status": "DEVELOPMENT_ONLY", "horizons": results, "family": family,
            "acceptance": gates}, config


if __name__ == "__main__":
    report, config = run(parser(__doc__).parse_args())
    config["development_report_sha256"] = write_json("FREEZE_dev_report.json", report)
    write_json("FROZEN_CONFIG.json", config)
