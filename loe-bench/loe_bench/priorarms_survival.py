"""Fit prior-method arms inside the isolated research environment."""

import json
from hashlib import sha256
from importlib.metadata import version
import platform
import sys
import warnings

import numpy as np

from .priorarms import ARMS, FEATURES, P1, P2, PYTHON_VERSION, RESEARCH_VERSIONS, SEED

SETTINGS = {
    P1: {"n_estimators": 500, "max_features": "sqrt", "min_samples_split": 10,
         "min_samples_leaf": 5, "max_depth": None, "bootstrap": True, "n_jobs": 1, "random_state": SEED},
    P2: {"alpha": 1.0, "ties": "breslow", "n_iter": 100, "tol": 1e-9},
}
SCALE = ("age_years", "first_nda_year")


def runtime():
    if sys.prefix == sys.base_prefix or platform.python_version() != PYTHON_VERSION:
        raise RuntimeError("PRIORARMS requires an isolated CPython 3.12.10 environment")
    installed = {name: version(name) for name in RESEARCH_VERSIONS}
    if installed != RESEARCH_VERSIONS:
        raise RuntimeError("PRIORARMS research dependency pins differ")
    return {"python": platform.python_version(), **installed}


def cox_inputs(train, predict):
    columns = np.array(FEATURES[P2])
    varies = np.ptp(train, axis=0) != 0
    train, predict = train[:, varies].copy(), predict[:, varies].copy()
    scales = {}
    for i, name in enumerate(columns[varies]):
        if name in SCALE:
            mean, sd = float(train[:, i].mean()), float(train[:, i].std())
            train[:, i] = (train[:, i] - mean) / sd
            predict[:, i] = (predict[:, i] - mean) / sd
            scales[str(name)] = {"mean": mean, "scale": sd}
    return train, predict, {"features": columns[varies].tolist(),
                            "zero_variance_dropped": columns[~varies].tolist(), "train_scaling": scales}


def fit_once(arm, train, predict, target):
    from scipy.linalg import LinAlgWarning
    from sklearn.exceptions import ConvergenceWarning
    from sksurv.ensemble import RandomSurvivalForest
    from sksurv.linear_model import CoxPHSurvivalAnalysis
    from threadpoolctl import threadpool_limits

    summary = {"input_features": list(FEATURES[arm]), "settings": SETTINGS[arm]}
    if arm == P2:
        train, predict, transform = cox_inputs(train, predict)
        summary.update(transform)
        model = CoxPHSurvivalAnalysis(**SETTINGS[arm])
    else:
        model = RandomSurvivalForest(**SETTINGS[arm])

    with threadpool_limits(limits=1), warnings.catch_warnings():
        for category in (ConvergenceWarning, LinAlgWarning, RuntimeWarning):
            warnings.simplefilter("error", category)
        model.fit(train, target)
        scores = np.array([1.0 - fn(1.0) for fn in model.predict_survival_function(predict)])

    if not np.all(np.isfinite(scores) & (scores >= 0) & (scores <= 1)):
        raise ValueError("Nonfinite or out-of-range native probability")
    summary["survival_grid_times"] = len(model.unique_times_)
    if arm == P2:
        if not np.isfinite(model.coef_).all() or not np.isfinite(model.baseline_survival_.y).all():
            raise ValueError("Nonfinite Cox coefficients or baseline survival")
        summary["coefficients"] = model.coef_.tolist()
        summary["baseline_survival_at_horizon"] = float(model.baseline_survival_(1.0))
        summary["convergence"] = "PASS"
    else:
        if len(model.estimators_) != SETTINGS[P1]["n_estimators"]:
            raise ValueError("Incomplete forest fit")
        summary["fitted_trees"] = len(model.estimators_)
        summary["tree_node_counts"] = [min(tree.tree_.node_count for tree in model.estimators_),
                                       max(tree.tree_.node_count for tree in model.estimators_)]
        summary["convergence"] = "NOT_APPLICABLE_NO_ITERATIVE_OPTIMIZER"
    return scores, summary


def fit_arm(arm, train, predict, target):
    train, predict = (np.asarray(matrix, dtype=float) for matrix in (train, predict))
    if not np.isfinite(train).all() or not np.isfinite(predict).all():
        raise ValueError("Nonfinite PRIORARMS predictor")
    scores, summary = fit_once(arm, train, predict, target)
    repeated, repeat_summary = fit_once(arm, train, predict, target)
    if not np.array_equal(scores, repeated) or summary != repeat_summary:
        raise ValueError("Repeated fit differs")
    summary["repeat_fit"] = "PASS_EXACT"
    summary["native_score_float64_le_sha256"] = sha256(scores.astype("<f8").tobytes()).hexdigest()
    return {"status": "PASS", "model": summary, "scores": scores.tolist()}


def main():
    def offline(event, _args):
        if event.startswith("socket."):
            raise RuntimeError(f"PRIORARMS forbids network access: {event}")

    sys.addaudithook(offline)
    current_runtime = runtime()
    from sksurv.util import Surv

    payload = json.load(sys.stdin)
    events, durations = zip(*payload["target"], strict=True)
    if set(events) != {False, True} or any(not 0 < t <= 1 or (not e and t != 1)
                                          for e, t in payload["target"]):
        raise ValueError("TRAIN needs both classes and the locked horizon clock")
    target = Surv.from_arrays(events, durations)
    result = {}
    for arm in ARMS:
        try:
            result[arm] = fit_arm(arm, payload["train"][arm], payload["predict"][arm], target)
        except (ValueError, ArithmeticError, np.linalg.LinAlgError, Warning) as exc:
            result[arm] = {"status": "FAIL", "reason": f"{type(exc).__name__}: {exc}"}
    print(json.dumps({"runtime": current_runtime, "arms": result}, allow_nan=False))


if __name__ == "__main__":
    main()
