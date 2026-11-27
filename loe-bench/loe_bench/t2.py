"""Development splits, fixed arm fits and validation-only evaluation for card T2."""
import hashlib
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date

from . import evidence_graph as graph
from .baselines import AgeHazardTable, Logistic
from .common import add_months
from .metrics import brier, ece, paired_cluster_bootstrap_ci, risk_coverage
from .seal import TEST_FIRST, require_rows
from .t2_features import MODEL_FEATURES

HORIZONS = (12, 24, 36)
VERDICTS = ("OPEN", "BLOCKED", "CONTESTED")
VERDICT_FEATURES = tuple(f"verdict_{verdict}" for verdict in VERDICTS)
FOLDS = 5
LO, HI = 0.25, 0.75
COMMON_COVERAGE = 0.80
BOOTSTRAP_DRAWS, BOOTSTRAP_SEED = 1000, 20261127


def development_split(horizon):
    """Earliest feasible validation start maximizes the number of validation cutoffs."""
    annual = [date(year, 1, 1) for year in range(2010, TEST_FIRST.year)]
    eligible = [cutoff for cutoff in annual if add_months(cutoff, horizon) < TEST_FIRST]
    for first in eligible:
        train = [cutoff for cutoff in eligible if add_months(cutoff, horizon) < first]
        if train:
            return train, [cutoff for cutoff in eligible if cutoff >= first]
    return [], []


def _inputs(rows, with_verdict=False):
    inputs = []
    for row in rows:
        x = dict(row["asof"].x)
        if with_verdict:
            x.update({name: float(row["asof"].verdict == verdict)
                      for name, verdict in zip(VERDICT_FEATURES, VERDICTS)})
        inputs.append({"x": x})
    return inputs


def _with_labels(inputs, rows):
    return [dict(features, y=row["y"]) for features, row in zip(inputs, rows, strict=True)]


def _fold(key):
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % FOLDS


def _logit_input(probability):
    p = min(max(probability, 1e-8), 1 - 1e-8)
    return {"x": {"logit": math.log(p / (1 - p))}}


def _cross_calibrate(rows, m1, m3):
    """Fit on other validation groups. M2 uses saturated, smoothed verdict logits."""
    folds = [_fold(row["key"]) for row in rows]
    outputs = {arm: [None] * len(rows) for arm in ("M1", "M2", "M3")}
    for fold in sorted(set(folds)):
        calibration = [i for i, group in enumerate(folds) if group != fold]
        held = [i for i, group in enumerate(folds) if group == fold]
        if not calibration:
            raise ValueError("cross-calibration requires at least two occupied drug-key folds")
        count, events = Counter(), Counter()
        for i in calibration:
            verdict = rows[i]["asof"].verdict
            count[verdict] += 1
            events[verdict] += rows[i]["y"]
        pooled = (sum(events.values()) + 1) / (len(calibration) + 2)
        table = {v: (events[v] + 1) / (count[v] + 2) if count[v] else pooled for v in VERDICTS}
        for i in held:
            outputs["M2"][i] = table[rows[i]["asof"].verdict]
        for arm, raw in (("M1", m1), ("M3", m3)):
            inputs = [_logit_input(prob) for prob in raw]
            fitted = Logistic(feats=("logit",)).fit(
                _with_labels([inputs[i] for i in calibration], [rows[i] for i in calibration]))
            for i, probability in zip(held, fitted.predict([inputs[i] for i in held]), strict=True):
                outputs[arm][i] = probability
    return outputs


@dataclass(frozen=True)
class Prediction:
    probability: float
    action: str

    @property
    def score(self):
        return self.probability if self.action == graph.PREDICT_ENTRY else 1 - self.probability


def _flat_action(probability):
    if probability >= HI:
        return graph.PREDICT_ENTRY
    if probability <= LO:
        return graph.PREDICT_NO_ENTRY
    return graph.ABSTAIN


def _aurc80(predictions, labels):
    curve = risk_coverage([p.probability for p in predictions], labels,
                          scores=[p.score for p in predictions], actions=[p.action for p in predictions])
    if not curve or curve[-1][0] < COMMON_COVERAGE:
        return math.nan
    widths = []
    previous = 0.0
    for coverage, risk in curve:
        endpoint = min(coverage, COMMON_COVERAGE)
        widths.append((endpoint - previous) * risk)
        if endpoint == COMMON_COVERAGE:
            break
        previous = endpoint
    return math.fsum(widths) / COMMON_COVERAGE


def _metrics(predictions, labels, verdicts):
    p = [item.probability for item in predictions]
    ece_value, bin_counts = ece(p, labels)
    answered = sum(item.action != graph.ABSTAIN for item in predictions)
    area = _aurc80(predictions, labels)
    by_verdict = {}
    for verdict in VERDICTS:
        indices = [i for i, label in enumerate(verdicts) if label == verdict]
        by_verdict[verdict] = {
            "rows": len(indices),
            "brier": brier([p[i] for i in indices], [labels[i] for i in indices]) if indices else None,
        }
    return {"aurc80_status": "evaluated" if math.isfinite(area) else "unevaluable",
            "aurc80": area if math.isfinite(area) else None,
            "brier": brier(p, labels), "ece": ece_value, "ece_bin_counts": bin_counts,
            "coverage": answered / len(labels), "answered": answered, "by_verdict": by_verdict}


def evaluate(train, validation, horizon):
    """Score validation only. Seal both sets before stripping cutoff metadata."""
    require_rows(validation)
    require_rows(train)
    if not train or not validation:
        raise ValueError("T2 requires non-empty train and validation partitions")
    validation_start = min(row["t"] for row in validation)
    if (any(add_months(row["t"], horizon) >= validation_start for row in train)
            or any(add_months(row["t"], horizon) >= TEST_FIRST for row in validation)):
        raise ValueError("T2 requires closed label windows strictly before the next partition")

    raw = {}
    for arm, with_verdict, features in (("M1", False, MODEL_FEATURES),
                                        ("M3", True, (*MODEL_FEATURES, *VERDICT_FEATURES))):
        fitted = Logistic(feats=features).fit(_with_labels(_inputs(train, with_verdict), train))
        raw[arm] = fitted.predict(_inputs(validation, with_verdict))
    calibrated = _cross_calibrate(validation, raw["M1"], raw["M3"])
    verdicts = [row["asof"].verdict for row in validation]
    predictions = {arm: [Prediction(p, _flat_action(p)) for p in calibrated[arm]] for arm in ("M1", "M2")}
    predictions["M3"] = [
        Prediction(p, graph.decide(row["asof"].snapshot, row["t"], horizon, p, lo=LO, hi=HI)["action"])
        for row, p in zip(validation, calibrated["M3"], strict=True)
    ]
    original_train = [{"x": row["x"], "y": row["y"]} for row in train]
    original_validation = [{"x": row["x"]} for row in validation]
    age_probabilities = AgeHazardTable().fit(original_train).predict(original_validation)
    predictions["B1"] = [
        Prediction(p, graph.PREDICT_ENTRY if p >= 0.5 else graph.PREDICT_NO_ENTRY)
        for p in age_probabilities
    ]
    labels = [row["y"] for row in validation]
    keys = [row["key"] for row in validation]
    metrics = {arm: _metrics(pred, labels, verdicts) for arm, pred in predictions.items()}

    comparisons = {}
    for arm in ("M1", "B1"):
        pair = {"status": "unevaluable", "delta": None, "ci95": None}
        a, b = metrics["M3"]["aurc80"], metrics[arm]["aurc80"]
        if a is not None and b is not None:
            low, high, invalid = paired_cluster_bootstrap_ci(
                _aurc80, predictions["M3"], predictions[arm], labels, keys,
                n_boot=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED)
            pair.update(status="evaluated" if math.isfinite(low) else "unevaluable_ci",
                        delta=a - b, ci95=[low, high] if math.isfinite(low) else None,
                        valid_draws=BOOTSTRAP_DRAWS - invalid, invalid_draws=invalid)
        comparisons[f"M3_minus_{arm}"] = pair

    open_indices = [i for i, verdict in enumerate(verdicts) if verdict == "OPEN"]
    open_inputs = [original_validation[i] for i in open_indices]
    original_logistic = Logistic(epochs=200).fit(original_train).predict(open_inputs) if open_inputs else []
    original_no_entry = sum((age_probabilities[i] + p) / 2 <= LO
                            for i, p in zip(open_indices, original_logistic, strict=True))
    return {
        "validation_rows": len(validation), "validation_drug_clusters": len(set(keys)),
        "validation_event_clusters": len({key for key, y in zip(keys, labels) if y}),
        "arms": metrics, "paired_aurc80": comparisons,
        "open_actions": {
            "rows": len(open_indices),
            "m3_predict_no_entry": sum(predictions["M3"][i].action == graph.PREDICT_NO_ENTRY for i in open_indices),
            "package_ensemble_predict_no_entry_on_same_open_rows": original_no_entry,
        },
    }
