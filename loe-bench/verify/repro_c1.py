"""Recompute the registered C′ queue results from two authenticated exports."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


ARMS = ("B1", "M1", "M3")
SCORE_DIGESTS = {
    12: "a644f1d40271c9a59a5405b840724906332ce975854d2afedd3d22c4ded80891",
    24: "c3b9e51891fd8f577dfce9f7fbbfb466f25f29ae50ed4edd9d8b2d0fcbcc84e7",
}
DRAWS = 2_000
SEED = 20261127
ALPHA = 0.025
CONTRASTS = (
    ("H1", 24, "M3", "B1"),
    ("H2", 24, "M3", "M1"),
    ("H3", 12, "M3", "B1"),
    ("secondary", 24, "M1", "B1"),
)


def authenticated_exports(score_dir):
    """Hash both byte streams before decoding either one."""
    payloads = {}
    for horizon, sha256 in SCORE_DIGESTS.items():
        path = score_dir / f"C1_scores_{horizon}m.json"
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != sha256:
            raise ValueError(f"SHA-256 verification failed for {path.name}")
        payloads[horizon] = payload

    rows_by_horizon = {}
    for horizon, payload in payloads.items():
        document = json.loads(payload)
        if document["prediction_horizon_months"] != horizon:
            raise ValueError(f"Unexpected horizon in the {horizon}m export")
        rows_by_horizon[horizon] = document["rows"]
    return rows_by_horizon


def queue_weights(scores, copies):
    """Return capacity and per-copy review probabilities at a single cutoff."""
    n_rows = int(copies.sum())
    slots = n_rows // 5
    if not slots:
        return slots, np.zeros(len(scores))

    expanded_scores = np.repeat(scores, copies)
    boundary_index = n_rows - slots
    boundary = np.partition(expanded_scores, boundary_index)[boundary_index]
    above = scores > boundary
    tied = scores == boundary
    remaining = slots - copies[above].sum()
    weights = np.zeros(len(scores))
    weights[above] = 1.0
    weights[tied] = remaining / copies[tied].sum()
    return slots, weights


def ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else None


def queue_metrics(scores, positive, cutoff_groups, drug_index, drug_copies, capture=False):
    copies = drug_copies[drug_index]
    event_rows = int(copies[positive].sum())
    hits = 0.0
    slots = 0
    missed_every_time = np.ones(len(drug_copies)) if capture else None
    for group in cutoff_groups:
        cutoff_copies = copies[group]
        cutoff_slots, weights = queue_weights(scores[group], cutoff_copies)
        cutoff_positive = positive[group]
        hits += float(np.sum(weights[cutoff_positive] * cutoff_copies[cutoff_positive]))
        slots += cutoff_slots
        if capture:
            np.multiply.at(
                missed_every_time, drug_index[group][cutoff_positive], 1 - weights[cutoff_positive]
            )

    result = {
        "expected_hits": hits,
        "slots": slots,
        "event_rows": event_rows,
        "recall": ratio(hits, event_rows),
        "precision": ratio(hits, slots),
    }
    if capture:
        event_drugs = np.unique(drug_index[positive])
        event_drug_copies = drug_copies[event_drugs]
        expected_captured = float(np.sum((1 - missed_every_time[event_drugs]) * event_drug_copies))
        event_count = int(event_drug_copies.sum())
        result["event_drugs"] = event_count
        result["expected_captured_drugs"] = expected_captured
        result["distinct_event_drug_capture"] = ratio(expected_captured, event_count)
    return result


def interval(values):
    """Even one undefined draw makes the registered interval unevaluable."""
    undefined = int(np.count_nonzero(~np.isfinite(values)))
    bounds = None if undefined else np.quantile(values, [ALPHA, 1 - ALPHA], method="linear").tolist()
    return {"ci95": bounds, "undefined_draws": undefined}


def analyze(rows, horizon):
    keys = np.asarray([row["key"] for row in rows], dtype=str)
    cutoffs = np.asarray([row["cutoff"] for row in rows], dtype=str)
    if len(set(zip(keys, cutoffs))) != len(rows):
        raise ValueError(f"Duplicate drug-cutoff pair at {horizon}m")
    unique_keys, drug_index = np.unique(keys, return_inverse=True)
    n_drugs = len(unique_keys)
    if not n_drugs:
        raise ValueError(f"Empty roster at {horizon}m")
    cutoff_groups = [np.flatnonzero(cutoffs == cutoff) for cutoff in np.unique(cutoffs)]
    outcomes = np.asarray([row["y"] for row in rows])
    if not np.isin(outcomes, [0, 1]).all():
        raise ValueError(f"Nonbinary outcome at {horizon}m")
    positive = outcomes == 1
    scores = {arm: np.asarray([row[arm] for row in rows], dtype=float) for arm in ARMS}
    if not all(np.isfinite(arm_scores).all() for arm_scores in scores.values()):
        raise ValueError(f"Nonfinite score at {horizon}m")

    observed = {
        arm: queue_metrics(
            scores[arm], positive, cutoff_groups, drug_index, np.ones(n_drugs, dtype=int),
            capture=(horizon == 24 and arm == "M3"),
        )
        for arm in ARMS
    }
    replicate_recall = {arm: np.full(DRAWS, np.nan) for arm in ARMS}
    replicate_capture = np.full(DRAWS, np.nan)
    rng = np.random.default_rng(SEED)
    for draw in range(DRAWS):
        sampled = rng.integers(n_drugs, size=n_drugs)
        multiplicities = np.bincount(sampled, minlength=n_drugs)
        for arm in ARMS:
            metrics = queue_metrics(
                scores[arm], positive, cutoff_groups, drug_index, multiplicities,
                capture=(horizon == 24 and arm == "M3"),
            )
            if metrics["recall"] is not None:
                replicate_recall[arm][draw] = metrics["recall"]
                if horizon == 24 and arm == "M3":
                    replicate_capture[draw] = metrics["distinct_event_drug_capture"]
    if horizon == 24:
        observed["M3"]["capture_bootstrap"] = interval(replicate_capture)
    return observed, replicate_recall


def recompute(rows_by_horizon):
    summaries = {horizon: analyze(rows, horizon) for horizon, rows in rows_by_horizon.items()}
    contrasts = {}
    reached = True
    for step, horizon, left, right in CONTRASTS:
        points, draws = summaries[horizon]
        left_recall, right_recall = points[left]["recall"], points[right]["recall"]
        difference = None if left_recall is None else left_recall - right_recall
        uncertainty = interval(draws[left] - draws[right])
        lower = None if uncertainty["ci95"] is None else uncertainty["ci95"][0]
        result = {
            "horizon_months": horizon,
            "comparison": f"{left}-{right}",
            "recall_difference": difference,
            **uncertainty,
            "one_sided_lower": lower,
            "at_least_10pp": None if difference is None else difference >= 0.10,
        }
        if step == "secondary" or not reached:
            result["decision"] = "descriptive"
        elif difference is None or lower is None:
            result["decision"] = "unevaluable"
        else:
            result["decision"] = "succeeds" if lower > 0 else "fails"
        if step != "secondary":
            reached = reached and result["decision"] == "succeeds"
        contrasts[step] = result
    return {
        "horizons": {horizon: points for horizon, (points, _) in summaries.items()},
        "contrasts": contrasts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score_dir", type=Path, help="directory with the two authenticated C1 score exports")
    args = parser.parse_args()
    result = recompute(authenticated_exports(args.score_dir))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
