"""Matched development-only LOE-Bench techniques. Actions retain the E7b policy."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from itertools import product
import re

import numpy as np

from . import evidence_graph as graph, t2
from .baselines import AgeHazardTable, Logistic
from .common import add_months
from .kleene import T3, evaluate
from .seal import TEST_FIRST
from .t2_features import CHALLENGE_FEATURES, MODEL_FEATURES

ARMS = ("M1", "M3")
TRIALS = ("K07", "K09", "K10", "K08", "K06")
L2 = 100.0
BREADTH = ("strength_count", "form_route_count", "strength_missing", "form_route_missing")
ERROR_FEATURES = ("confidence", "age_disagreement")
UNKNOWN = {"", "-", "N/A", "NA", "UNKNOWN", "NOT APPLICABLE", "NOT AVAILABLE"}


def normalize_strength(value):
    value = re.sub(r"\s*([;/])\s*", r"\1", " ".join(value.upper().split()))
    # Preserve units, component order, and equivalent-basis markers.
    value = re.sub(r"\d*\.\d+", lambda m: format(Decimal(m[0]).normalize(), "f"), value)
    return re.sub(r"(?<=\d) (?=[A-Z])", "", value)


def presentation_breadth(products, edition_date):
    """Count observed presentations, carrying partial and absent coverage flags."""
    by_id = defaultdict(set)
    form_missing = strength_missing = not products
    for row in products:
        approved = row["approval_date"]
        if approved is None and row["approval_date_text"].upper() != "APPROVED PRIOR TO JAN 1, 1982":
            form_missing = strength_missing = True
            continue
        if approved is not None and approved > edition_date:
            continue
        parts = tuple(" ".join(part.upper().split()) for part in row["form_route"].split(";"))
        form = parts if len(parts) == 2 and all(p not in UNKNOWN for p in parts) else None
        strength = normalize_strength(row["strength"])
        strength = strength if strength not in UNKNOWN and any(c.isdigit() for c in strength) else None
        form_missing |= form is None
        strength_missing |= form is None or strength is None
        by_id[row["appl_no"], row["product_no"]].add((form, strength))
    forms, strengths = set(), set()
    for presentations in by_id.values():
        if len(presentations) != 1:
            form_missing = strength_missing = True
            continue
        form, strength = next(iter(presentations))
        if form is not None:
            forms.add(form)
            if strength is not None:
                strengths.add((form, strength))
    return dict(zip(BREADTH, map(float, (len(strengths), len(forms),
                                         strength_missing or not strengths,
                                         form_missing or not forms)), strict=True))


def annual_targets(landmark, observed_through, first_event):
    """Yield interval/label pairs for completed at-risk periods and observed events."""
    if first_event is not None and first_event <= landmark:
        raise ValueError("hazard landmarks must start at risk")
    for second in (0, 1):
        end = add_months(landmark, 12 * (second + 1))
        if first_event is not None and first_event <= min(end, observed_through):
            yield second, 1
            break
        if end > observed_through:
            break
        yield second, 0


def cumulative_hazard(first, second):
    return 1 - (1 - first) * (1 - second)


def beta_calibration(calibration, probabilities):
    """Use the E7b log-loss update with nonnegative standardized beta slopes."""
    if len({y for _, y in calibration}) < 2:
        return list(probabilities)

    def design(values):
        p = np.clip(np.asarray(values), 1e-8, 1 - 1e-8)
        return np.column_stack((np.log(p), -np.log1p(-p)))

    values, labels = zip(*calibration, strict=True)
    x = design(values)
    mean, scale = x.mean(axis=0), np.maximum(x.std(axis=0), 1e-9)
    z = (x - mean) / scale
    weights, intercept = np.zeros(2), 0.0
    labels = np.asarray(labels)

    def sigmoid(logit):
        return np.exp(-np.logaddexp(0, -logit))

    for _ in range(300):
        error = sigmoid(z @ weights + intercept) - labels
        weights = np.maximum(0, weights - 0.3 * (z.T @ error + weights) / len(z))
        intercept -= 0.3 * error.mean()
    return sigmoid((design(probabilities) - mean) / scale @ weights + intercept).tolist()


def decision_relevant_unknown(assignment):
    unknowns = [name for name, state in assignment.items() if state == T3.UNKNOWN]
    for name in unknowns:
        others = [leaf for leaf in unknowns if leaf != name]
        for values in product((T3.FALSE, T3.TRUE), repeat=len(others)):
            completed = {**assignment, **dict(zip(others, values, strict=True))}
            if evaluate(graph.ROOT, {**completed, name: T3.FALSE}) != evaluate(
                    graph.ROOT, {**completed, name: T3.TRUE}):
                return True
    return False


@dataclass(frozen=True)
class RankedPrediction:
    probability: float
    action: str
    score: float


def assignment(row, horizon):
    evidence = row["asof"]
    return graph.build_assignment(evidence.snapshot, row["t"], horizon,
                                  evidence.challenge.state if evidence.challenge else None)


def discounted(prediction, inputs, arm):
    missing = (decision_relevant_unknown(inputs) if arm == "M3"
               else T3.UNKNOWN in inputs.values())
    if missing and prediction.action != graph.ABSTAIN:
        return RankedPrediction(prediction.probability, prediction.action, prediction.score - 0.05)
    return prediction


def emitted(probability, row, horizon, arm):
    if arm == "M3":
        evidence = row["asof"]
        action = graph.decide(evidence.snapshot, row["t"], horizon, probability, lo=t2.LO, hi=t2.HI,
                              challenge_evidence=evidence.challenge.state if evidence.challenge else None)["action"]
    else:
        action = t2._flat_action(probability)
    return t2.Prediction(probability, action)


def model_inputs(rows, age, arm, flags):
    inputs = t2._inputs(rows, age, arm == "M3")
    if "K07" in flags:
        for features, row in zip(inputs, rows, strict=True):
            features["x"].update(row["breadth"])
    return inputs


def raw_predictions(train, validation, horizon, flags, observed_through):
    """Fit the current matched model using only eligible TRAIN labels."""
    age = AgeHazardTable().fit(train).predict(validation)
    hazard = "K09" in flags
    model_train = train
    model_validation = validation
    if hazard:
        model_train = [dict(row, asof=row["asof12"], y=row["event12"]) for row in train]
        model_validation = [dict(row, asof=row["asof12"]) for row in validation]
    age_model = AgeHazardTable().fit(model_train)
    train_age = age_model.predict(model_train)
    val_age = age_model.predict(model_validation)
    features = (*MODEL_FEATURES, t2.AGE_SIGNAL, *CHALLENGE_FEATURES)
    if "K07" in flags:
        features += BREADTH
    if hazard:
        features += ("second_interval",)

    probabilities = {}
    for arm in ARMS:
        columns = features + (t2.VERDICT_FEATURES if arm == "M3" else ())
        tr = model_inputs(model_train, train_age, arm, flags)
        va = model_inputs(model_validation, val_age, arm, flags)
        if hazard:
            tr = [{"x": dict(x["x"], second_interval=second), "y": y}
                  for x, row in zip(tr, train, strict=True)
                  for second, y in annual_targets(row["t"], observed_through, row["first_event"])]
            va = [{"x": dict(x["x"], second_interval=second)}
                  for second in range(horizon // 12) for x in va]
        else:
            tr = t2._with_labels(tr, train)
        raw = Logistic(l2=L2, feats=columns).fit(tr).predict(va)
        if hazard and horizon == 24:
            n = len(validation)
            raw = list(map(cumulative_hazard, raw[:n], raw[n:]))
        probabilities[arm] = raw
    return probabilities, age


def calibrate(raw, rows, fit, held, beta):
    data = [(raw[i], rows[i]["y"]) for i in fit]
    test = [raw[i] for i in held]
    if beta:
        return beta_calibration(data, test)
    model = Logistic(feats=("logit",)).fit(
        [{"x": {"logit": t2._logit(p)}, "y": y} for p, y in data])
    return model.predict([{"x": {"logit": t2._logit(p)}} for p in test])


def selector_input(prediction, age):
    age_for_action = age if prediction.action == graph.PREDICT_ENTRY else 1 - age
    confidence = (prediction.probability if prediction.action == graph.PREDICT_ENTRY
                  else 1 - prediction.probability)
    return {"x": dict(zip(ERROR_FEATURES, (confidence, abs(confidence - age_for_action)), strict=True))}


def select_errors(training, predictions, age, held):
    if len({row["y"] for row in training}) < 2:
        return
    answered = [i for i in held if predictions[i].action != graph.ABSTAIN]
    model = Logistic(feats=ERROR_FEATURES).fit(training)
    errors = model.predict([selector_input(predictions[i], age[i]) for i in answered])
    for i, error in zip(answered, errors, strict=True):
        item = predictions[i]
        predictions[i] = RankedPrediction(item.probability, item.action, 1 - error)


def nested_selector(predictions, train, rows, horizon, flags, observed_through):
    folds = [t2._fold(row["key"]) for row in rows]
    groups = sorted(set(folds))
    diagnostics = []
    if len(groups) < 3:
        return diagnostics
    # Pairwise exclusion is symmetric. Share only these raw fits across outer folds.
    fits = {}
    for outer in groups:
        held = [i for i, fold in enumerate(folds) if fold == outer]
        outer_train = [row for row in train if t2._fold(row["key"]) != outer]
        if not outer_train:
            continue
        age = AgeHazardTable().fit(outer_train).predict(rows)
        selector_train = {arm: [] for arm in ARMS}
        for inner in groups:
            if inner == outer:
                continue
            pair = tuple(sorted((outer, inner)))
            if pair not in fits:
                subset = [row for row in train if t2._fold(row["key"]) not in pair]
                fits[pair] = raw_predictions(subset, rows, horizon, flags, observed_through) if subset else None
            if fits[pair] is None:
                continue
            raw, inner_age = fits[pair]
            fit = [i for i, fold in enumerate(folds) if fold not in pair]
            test = [i for i, fold in enumerate(folds) if fold == inner]
            for arm in ARMS:
                probabilities = calibrate(raw[arm], rows, fit, test, "K10" in flags)
                for i, p in zip(test, probabilities, strict=True):
                    action = emitted(p, rows[i], horizon, arm)
                    if action.action != graph.ABSTAIN:
                        error = int((action.action == graph.PREDICT_ENTRY) != bool(rows[i]["y"]))
                        selector_train[arm].append(dict(selector_input(action, inner_age[i]), y=error))
        for arm in ARMS:
            examples = selector_train[arm]
            select_errors(examples, predictions[arm], age, held)
            errors = sum(row["y"] for row in examples)
            diagnostics.append({"fold": outer, "arm": arm, "fit_rows": len(examples), "fit_errors": errors,
                                "fallback": errors in (0, len(examples))})
    return diagnostics


def predict(train, validation, horizon, flags):
    t2.require_development_cutoffs(row["t"] for row in (*train, *validation))
    start = min(row["t"] for row in validation)
    if (not train or any(add_months(row["t"], horizon) >= start for row in train)
            or any(add_months(row["t"], horizon) >= TEST_FIRST for row in validation)):
        raise ValueError("DEVX requires non-empty, strictly embargoed partitions")
    observed_through = start - timedelta(days=1)
    raw, age = raw_predictions(train, validation, horizon, flags, observed_through)
    calibrated = t2._cross_calibrate(
        validation, raw["M1"], raw["M3"], calibrator=beta_calibration if "K10" in flags else None)
    predictions = {arm: [emitted(p, row, horizon, arm)
                         for p, row in zip(values, validation, strict=True)]
                   for arm, values in calibrated.items()}
    predictions["B1"] = [
        t2.Prediction(p, graph.PREDICT_ENTRY if p >= 0.5 else graph.PREDICT_NO_ENTRY) for p in age
    ]
    diagnostics = nested_selector(predictions, train, validation, horizon, flags, observed_through) if "K08" in flags else []
    if "K06" in flags:
        inputs = [assignment(row, horizon) for row in validation]
        for arm in ARMS:
            predictions[arm] = [discounted(pred, a, arm)
                                for pred, a in zip(predictions[arm], inputs, strict=True)]
    return predictions, diagnostics
