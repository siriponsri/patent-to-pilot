"""Descriptive Track A measures over frozen predictions and mature labels."""

import numpy as np

from . import evidence_graph as graph, metrics, power, t1v3, t2
from .common import read_jsonl
from .tracka_release import ARMS, FREEZE, load, require, row_id
from .tracka_statistics import DRAWS, SEED, finite

VERSION = "1.1.0"
CORE = ("B1", "M1", "M3")
ACTIONS = (graph.PREDICT_NO_ENTRY, graph.PREDICT_ENTRY, graph.ABSTAIN)
MEASURES = ("brier", "ece", "aurc80", "e_aurc", "mean_decision_loss", "flag_rate", "referral_rate",
            "flag_or_referral_rate")


def frozen_actions(release, arm, horizon):
    name = load(release.folder / ARMS)[arm]["files"][str(horizon)]
    rows = [row for row in read_jsonl(release.folder / name) if row_id(row)[2] == horizon]
    require(tuple(row_id(row)[0] for row in rows) == release.keys,
            f"Frozen action roster differs for {arm}")
    fields = [row.get("arms", {}).get(arm, row) for row in rows]
    return [(row.get("diagnostic_action"), row.get("graph_conflict")) for row in fields]


def full_area(counts, errors, harmonic):
    """Discrete right-step full area with uniform ordering inside ties."""
    ends = counts.cumsum(axis=-1)
    preceding = ends - counts
    rate = errors / np.maximum(counts, 1)
    offset = errors.cumsum(axis=-1) - errors - preceding * rate
    return (counts * rate + offset * (harmonic[ends] - harmonic[preceding])).sum(axis=-1) / ends[..., -1]


def legacy_actions(arm, probabilities, conflicts, threshold, diagnostic_hi):
    clear, flag, refer = ACTIONS
    require(0.5 <= threshold <= 1, "Invalid frozen legacy threshold")
    if arm != "M3":
        return [refer if max(p, 1 - p) < threshold else flag if p > 0.5 else clear
                for p in probabilities]
    lo = 1 - threshold
    require(lo < threshold and 0 <= diagnostic_hi <= 1, "Invalid frozen M3 policy thresholds")
    actions = []
    for p, conflict in zip(probabilities, conflicts, strict=True):
        if p <= lo:
            actions.append(clear)
        else:
            require(p >= diagnostic_hi and type(conflict) is bool, "Frozen M3 conflict is not identifiable")
            if conflict:
                actions.append(clear if p < threshold else refer)
            else:
                actions.append(refer if p < threshold else flag)
    return actions


def legacy_measures(arm, probabilities, labels, conflicts, policy):
    if policy is None:
        return {"status": "NOT_ESTIMABLE", "reason": "FROZEN_LEGACY_THRESHOLD_MISSING"}
    threshold = policy["legacy_90"]["threshold"]
    try:
        actions = legacy_actions(arm, probabilities, conflicts, threshold, policy["hi"])
    except ValueError as exc:
        return {"status": "NOT_ESTIMABLE", "reason": str(exc)}
    predictions = [t2.Prediction(p, action) for p, action in zip(probabilities, actions, strict=True)]
    answered = sum(action != graph.ABSTAIN for action in actions)
    errors = sum((action == graph.PREDICT_ENTRY) != bool(y)
                 for action, y in zip(actions, labels, strict=True) if action != graph.ABSTAIN)
    n = len(labels)
    full = answered == n
    excess = None
    if full:
        area = metrics.aurc(probabilities, labels, scores=[item.score for item in predictions], actions=actions)
        oracle = sum(i / (n - errors + i) for i in range(1, errors + 1)) / n
        excess = area - oracle
    return {"status": "ESTIMATED", "threshold": threshold, "answered": answered, "rows": n,
            "realized_coverage": answered / n, "errors": errors,
            "aurc80": finite(t2._aurc80(predictions, labels)),
            "aurc80_coverage_met": 5 * answered >= 4 * n, "aurc80_minimum_coverage": 0.8,
            "e_aurc": excess, "e_aurc_coverage_met": full, "e_aurc_minimum_coverage": 1.0}


def arm_measures(keys, p, labels, actions, weights, *, arm=None, policy=None):
    """The first weight row gives the observed roster, followed by bootstrap draws."""
    p, labels = np.asarray(p), np.asarray(labels)
    n = len(keys)
    calibration = metrics.ece(p, labels)
    bins = np.searchsorted(np.arange(1, 10) / 10, p, side="right")
    confidences = np.unique(-np.maximum(p, 1 - p), return_inverse=True)[1]
    wrong = (p >= 0.5) != labels
    n_groups = int(confidences.max()) + 1
    counts = np.array([np.bincount(confidences, w, minlength=n_groups) for w in weights], dtype=int)
    errors = np.array([np.bincount(confidences, w * wrong, minlength=n_groups) for w in weights], dtype=int)
    harmonic = power.harmonic_numbers(n)
    n_errors = errors.sum(axis=1)
    oracle = full_area(np.column_stack((n - n_errors, n_errors)),
                       np.column_stack((np.zeros_like(n_errors), n_errors)), harmonic)
    levels = {
        "brier": weights @ ((p - labels) ** 2) / n,
        "ece": np.array([np.abs(np.bincount(bins, w * (p - labels), minlength=10)).sum() / n
                         for w in weights]),
        "aurc80": power.area(counts, errors, n, harmonic),
        "e_aurc": full_area(counts, errors, harmonic) - oracle,
    }
    names, conflicts = zip(*actions, strict=True)
    row = {"ece_bin_counts": list(calibration.bin_counts),
           "legacy_policy_90": legacy_measures(arm, p, labels, conflicts, policy)}
    require(all(action is None or action in ACTIONS for action in names), "Unknown frozen diagnostic action")
    if None in names:
        row["diagnostic"] = {"status": "NOT_ESTIMABLE", "reason": "FROZEN_DIAGNOSTIC_ACTION_MISSING"}
        return row, levels

    names = np.asarray(names)
    clear, flag, refer = (names == action for action in ACTIONS)
    counts = {name: int(mask.sum()) for name, mask in zip(("clear", "flag", "refer"), (clear, flag, refer))}
    missed = int(labels[clear].sum())
    false_flags = int((1 - labels[flag]).sum())
    safety = t1v3.clear_rate_ci(labels[clear], np.asarray(keys)[clear])
    levels.update({name: (weights @ values) / n for name, values in {
        "mean_decision_loss": 10 * clear * labels + flag * (1 - labels) + 0.5 * refer,
        "flag_rate": flag,
        "referral_rate": refer,
        "flag_or_referral_rate": flag | refer,
    }.items()})
    row["diagnostic"] = {
        "status": "ESTIMATED", "rows": counts, "rates": {name: value / n for name, value in counts.items()},
        "flag_or_referral_rows": counts["flag"] + counts["refer"], "flag_events": int(labels[flag].sum()),
        "false_flags": false_flags, "referred_events": int(labels[refer].sum()),
        "conflict_referrals": sum(conflict is True and bool(is_referred)
                                  for conflict, is_referred in zip(conflicts, refer, strict=True))
        if all(type(conflict) is bool for conflict in conflicts) else None,
        "missed_clear_events": missed, "missed_clear_rate": missed / counts["clear"] if counts["clear"] else None,
        "missed_clear_ci95": safety, "safety_upper_limit": 0.03,
        "auto_clear_safety": "UNEVALUABLE" if safety is None else "PASS" if safety[1] <= 0.03 else "FAIL",
    }
    return row, levels


def summarize(release, horizon, labels, panel, primary_draws):
    """Use the same single-cutoff drug draws as the registered primary scorer."""
    keys = release.keys
    n = len(keys)
    rng = np.random.default_rng(SEED)
    weights = np.stack([np.ones(n, dtype=int), *(
        np.bincount(rng.integers(n, size=n), minlength=n) for _ in range(DRAWS))])
    arms, levels, draws = {}, {}, {}
    frozen = load(release.folder / FREEZE)
    policies = (frozen.get("models_and_policies", {}).get("core_prediction_policy", {})
                .get(str(horizon), {}).get("policy_thresholds", {}))

    def intervals(name, samples):
        draws[name] = samples[1:]
        return t1v3.interval(finite(samples[0]), samples[1:])

    for arm in CORE:
        probabilities = [p for _, p, _ in release.scores[horizon][arm]]
        arms[arm], levels[arm] = arm_measures(keys, probabilities, labels, frozen_actions(release, arm, horizon),
                                             weights, arm=arm, policy=policies.get(arm))
        arms[arm]["levels"] = {name: intervals(f"{arm}:{name}", values) for name, values in levels[arm].items()}
    contrasts = {}
    for left, right in t1v3.PAIRS:
        pair = f"{left}-{right}"
        contrasts[pair] = {name: intervals(f"{pair}:{name}", levels[left][name] - levels[right][name])
                           for name in MEASURES if name in levels[left] and name in levels[right]}
        for name in ("precision", "grouped_average_precision"):
            a, b = (panel["arms"][arm][name]["estimate"] for arm in (left, right))
            samples = primary_draws[f"{left}:{name}"] - primary_draws[f"{right}:{name}"]
            contrasts[pair][name] = intervals(f"{pair}:{name}", np.r_[np.nan if None in (a, b) else a - b, samples])
        contrasts[pair]["distinct_event_drug_capture"] = panel["contrasts"][pair]["recall"]
    capture = {arm: {"expected_captured_event_drugs": queue["expected_queued_events"],
                     "event_drugs": panel["event_drugs"], "capture_fraction": queue["recall"]}
               for arm, queue in panel["arms"].items()}
    return {"version": VERSION, "arms": arms, "contrasts": contrasts, "distinct_event_drug_capture": capture}, draws
