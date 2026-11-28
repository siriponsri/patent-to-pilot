"""Registered Track A metrics on a single mature prospective roster."""

import numpy as np

from . import metrics, priorarms, t1v3
from .review_metrics import ReviewQueue
from .tracka_release import C9, CORE, LLM, PRIOR

DRAWS, SEED = 2000, 20261127
ALPHA = 0.025
PAIRS = (("M3", "B1"), ("M3", "M1"), ("M1", "B1"), ("M3", "B3"),
         ("L1", "B1"), ("L1", "M3"), ("L1e", "L1"), ("L1e", "M3"), ("L1e", "B1"),
         *((arm, "M3") for arm in PRIOR), ("C9-GRPO", "C9-SFT"))
STEPS = (("H1", 24, "M3-B1"), ("H2", 24, "M3-M1"), ("H3", 12, "M3-B1"))


def finite(value):
    return float(value) if np.isfinite(value) else None


def panel(keys, frozen_scores, labels, elapsed):
    labels = np.asarray(labels, dtype=np.int64)
    drugs, groups = np.unique(np.asarray(keys, dtype=str), return_inverse=True)
    cutoffs = np.zeros(len(keys), dtype=int)
    ones = np.ones(len(keys), dtype=int)
    zero_losses = np.zeros(len(keys))
    queues, probabilities, point, report, draws = {}, {}, {}, {}, {}
    for arm, scores in frozen_scores.items():
        native, p, valid = zip(*scores, strict=True)
        queues[arm] = ReviewQueue(native, cutoffs)
        probabilities[arm] = np.asarray(p, dtype=float)
        draws[arm] = np.full((DRAWS, 4), np.nan)
        fractions, slots = queues[arm].allocation(ones)
        if slots != len(keys) // 5 or not np.isclose(fractions.sum(), slots, rtol=0, atol=1e-9):
            raise ValueError(f"Queue allocation violates the registered budget for {arm}")
        report[arm] = {"expected_queued_events": float(fractions @ labels),
                       "boundary_tie_rows": int(np.count_nonzero((fractions > 0) & (fractions < 1)))}
        if arm in CORE + PRIOR:
            concordance = priorarms.concordance(native, labels, elapsed, cutoffs)
            concordance["status"] = "ESTIMATED" if concordance["comparable_pairs"] else "NOT_ESTIMABLE"
            report[arm].update(
                roc_auc=finite(metrics.auroc(native, labels)),
                c_index=concordance,
                **priorarms.classification(p, labels),
                **{"hard_rule_brier" if arm == "B3" else "brier": metrics.brier(p, labels)},
            )
        if arm in LLM + C9:
            report[arm].update(malformed=len(valid) - sum(valid),
                               malformed_rate=(len(valid) - sum(valid)) / len(valid))

    def measures(arm, weights):
        values = queues[arm].measure(labels, zero_losses, weights)
        brier = np.average((probabilities[arm] - labels) ** 2, weights=weights) if arm in C9 else np.nan
        return np.array([*values[:3], brier])

    for arm in queues:
        point[arm] = measures(arm, ones)
    rng = np.random.Generator(np.random.PCG64(SEED))
    for i in range(DRAWS):
        copies = np.bincount(rng.integers(len(drugs), size=len(drugs)), minlength=len(drugs))
        for arm in queues:
            draws[arm][i] = measures(arm, copies[groups])

    metrics_for = ("recall", "precision", "grouped_average_precision", "raw_brier")
    saved = {}
    for arm in queues:
        count = 4 if arm in C9 else 3
        for j, metric in enumerate(metrics_for[:count]):
            report[arm][metric] = t1v3.interval(finite(point[arm][j]), draws[arm][:, j])
            saved[f"{arm}:{metric}"] = draws[arm][:, j]
    contrasts = {}
    for a, b in PAIRS:
        pair = f"{a}-{b}"
        if a not in queues or b not in queues:
            contrasts[pair] = {"status": "NOT_RUN", "missing_arms": [arm for arm in (a, b) if arm not in queues]}
            continue
        indices = (0, 3) if a in C9 else (0, 1, 2) if a in LLM else (0,)
        contrasts[pair] = {"status": "ESTIMATED"}
        for j in indices:
            metric = metrics_for[j]
            difference = draws[a][:, j] - draws[b][:, j]
            contrasts[pair][metric] = t1v3.interval(finite(point[a][j] - point[b][j]), difference)
            saved[f"{pair}:{metric}"] = difference
    return {"rows": len(keys), "drugs": len(drugs), "event_rows": int(labels.sum()),
            "event_drugs": len(np.unique(groups[labels == 1])), "prevalence": float(labels.mean()),
            "slots_per_arm": slots, "arms": report, "contrasts": contrasts,
            "bootstrap": {"generator": "PCG64", "seed": SEED, "draws": DRAWS, "quantile_method": "linear",
                          "undefined_recall_cause": "empty event denominator in resampled roster"}}, saved


def sequence(panels, *, formal=True):
    result, reached = {}, True
    for name, horizon, pair in STEPS:
        item = {"horizon_months": horizon, "contrast": pair}
        if horizon not in panels:
            result[name] = {**item, "decision": "PENDING", "reached": False}
            continue
        estimate = panels[horizon]["contrasts"][pair]["recall"]
        lower = estimate["ci95"][0] if estimate["ci95"] else None
        point = estimate["estimate"]
        if not formal:
            decision = "DESCRIPTIVE_ONLY"
        elif 24 not in panels:
            decision = "DESCRIPTIVE_PENDING"
        elif not reached:
            decision = "NOT_REACHED_DESCRIPTIVE"
        else:
            decision = "UNEVALUABLE" if lower is None else "PASS" if lower > 0 else "FAIL"
        result[name] = {**item, **estimate, "one_sided_lower": lower, "alpha": ALPHA,
                        "decision": decision, "reached": formal and reached and 24 in panels,
                        "meets_plus_10pp": point >= 0.10 if point is not None else None}
        reached = reached and decision == "PASS"
    return result
