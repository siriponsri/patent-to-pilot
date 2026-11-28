"""Locked PRIORARMS features, survival clock and development metrics."""

from datetime import date
from math import isfinite

import numpy as np

from . import metrics, t1v3
from .review_metrics import ReviewQueue

P1, P2 = "P1-RSF-OPEN", "P2-COX-OPEN"
ARMS = (P1, P2)
DRAWS, SEED = 2000, 20261127
PYTHON_VERSION = "3.12.10"
RESEARCH_VERSIONS = {"numpy": "2.2.6", "scikit-learn": "1.7.2", "scikit-survival": "0.25.0"}
FEATURES = {
    P1: ("age_years", "oral", "injectable", "nce_remaining_years", "years_to_last_patent_expiry",
         "nce_remaining_years_missing", "years_to_last_patent_expiry_missing"),
    P2: ("age_years", "orphan", "oral", "injectable", "challenge_present", "challenge_missing",
         "first_nda_year"),
}


def predictors(row, first_nda):
    if first_nda is None or first_nda > row["t"]:
        raise ValueError("First NDA must be dated by the cutoff")
    x = dict(row["asof"].x, first_nda_year=first_nda.year)
    return {arm: [x[name] for name in columns] for arm, columns in FEATURES.items()}


def survival_target(row, first_anda):
    """Return the locked event flag and elapsed days before administrative censoring."""
    cutoff, end = row["t"], row["t_end"]
    if end <= cutoff or (first_anda is not None and first_anda <= cutoff):
        raise ValueError("Survival target requires an at-risk row and a positive horizon")
    event = first_anda is not None and first_anda <= end
    if event != row["y"]:
        raise ValueError("Survival target disagrees with the core endpoint")
    return event, ((first_anda if event else end) - cutoff).days


def concordance(scores, labels, days, cutoffs):
    """Pool strictly ordered times within cutoff and give native-risk ties half credit."""
    scores, labels, days, cutoffs = map(np.asarray, (scores, labels, days, cutoffs))
    pairs, credit = 0, 0.0
    for i in np.flatnonzero(labels):
        later = scores[(cutoffs == cutoffs[i]) & (days > days[i])]
        pairs += len(later)
        credit += np.count_nonzero(scores[i] > later) + 0.5 * np.count_nonzero(scores[i] == later)
    return {"estimate": credit / pairs if pairs else None, "comparable_pairs": pairs}


def classification(probabilities, labels):
    flagged = np.asarray(probabilities) >= 0.5
    actual = np.asarray(labels, dtype=bool)
    tp = int(np.count_nonzero(flagged & actual))
    fp = int(np.count_nonzero(flagged & ~actual))
    tn = int(np.count_nonzero(~flagged & ~actual))
    fn = int(np.count_nonzero(~flagged & actual))
    return {"accuracy": (tp + tn) / len(actual), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "always_negative_accuracy": (tn + fp) / len(actual)}


def recall(queue, labels, weights):
    event_copies = weights * labels
    n = event_copies.sum()
    inclusion, slots = queue.allocation(weights)
    return (float(np.dot(inclusion, event_copies) / n) if n else None), slots


def development_metrics(rows, elapsed, native, probabilities):
    keys = [row["key"] for row in rows]
    cutoffs = [row["t"].toordinal() for row in rows]
    labels = np.asarray([row["y"] for row in rows])
    weights = np.ones(len(rows), dtype=int)
    queues = {arm: ReviewQueue(scores, cutoffs) for arm, scores in native.items()}
    report = {}
    for arm, scores in native.items():
        captured, slots = recall(queues[arm], labels, weights)
        auc = metrics.auroc(scores, labels)
        p = probabilities[arm]
        report[arm] = {"recall20": captured, "slots": slots, "roc_auc": auc if isfinite(auc) else None,
                       "c_index": concordance(scores, labels, elapsed, cutoffs),
                       **classification(p, labels), "hard_rule_brier" if arm == "B3" else "brier":
                       metrics.brier(p, labels)}

    # Each draw copies entire drug histories, with identical copies across all arms.
    drugs = sorted(set(keys))
    index = {key: i for i, key in enumerate(drugs)}
    row_to_drug = np.asarray([index[key] for key in keys])
    paired_arms = [arm for arm in ARMS if arm in queues]
    rng = np.random.Generator(np.random.PCG64(SEED))
    bootstrap = {arm: np.full(DRAWS, np.nan) for arm in paired_arms}
    for i in range(DRAWS if paired_arms else 0):
        copies = np.bincount(rng.integers(len(drugs), size=len(drugs)), minlength=len(drugs))
        weights = copies[row_to_drug]
        base, _ = recall(queues["M3"], labels, weights)
        if base is not None:
            for arm in paired_arms:
                candidate, _ = recall(queues[arm], labels, weights)
                bootstrap[arm][i] = candidate - base
    contrasts = {f"{arm}-M3": t1v3.interval(report[arm]["recall20"] - report["M3"]["recall20"]
                                          if labels.any() else None, draws)
                 for arm, draws in bootstrap.items()}
    return {"status": "development validation (descriptive)",
            "cutoffs": [date.fromordinal(day).isoformat() for day in sorted(set(cutoffs))],
            "rows": len(rows), "drugs": len(drugs), "events": int(labels.sum()),
            "event_drugs": len({key for key, y in zip(keys, labels, strict=True) if y}),
            "prevalence": float(labels.mean()), "arms": report, "contrasts": contrasts,
            "bootstrap": {"draws": DRAWS, "generator": "PCG64", "seed": SEED}}
