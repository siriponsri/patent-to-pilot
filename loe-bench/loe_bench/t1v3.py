"""Development queue metrics and asymmetric actions for criteria v3."""
from math import exp, isclose, log

import numpy as np

from . import evidence_graph as graph, t2


ARMS = ("B1", "M1", "M3")
PAIRS = (("M3", "B1"), ("M3", "M1"), ("M1", "B1"))
METRICS = ("recall", "precision", "distinct_event_drug_capture")
REVIEW_DIVISOR = 5
CLEAR_EVENT_LIMIT = 0.01
VALIDATION_UPPER_LIMIT = 0.03


def ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else None


class QueuePanel:
    """Prepare score ties once and rerank the weighted roster on each draw."""

    def __init__(self, rows, cutoffs, native_scores):
        cutoffs = list(cutoffs)
        times = [row["t"] for row in rows]
        t2.require_development_cutoffs(cutoffs)
        t2.require_development_cutoffs(times)
        keys = [row["key"] for row in rows]
        if (not set(times) <= set(cutoffs) or len(set(cutoffs)) != len(cutoffs)
                or len(set(zip(keys, times))) != len(rows)):
            raise ValueError("Queue requires one eligible row per drug and declared cutoff")
        labels = [row["y"] for row in rows]
        if any(y not in (0, 1) for y in labels):
            raise ValueError("Queue labels must be binary")
        self.labels = np.asarray(labels, dtype=np.int64)
        self.events = self.labels == 1
        self.keys, self.groups = np.unique(np.asarray(keys, dtype=str), return_inverse=True)
        self.event_groups = np.unique(self.groups[self.events])
        self.cutoffs = cutoffs
        times = np.asarray(times, dtype=object)
        self.by_cutoff = [np.flatnonzero(times == day) for day in cutoffs]
        self.ranks = {}
        for arm in ARMS:
            scores = np.asarray(native_scores[arm], dtype=float)
            if scores.shape != self.labels.shape or not np.isfinite(scores).all():
                raise ValueError("Queue needs one finite native score per row and arm")
            self.ranks[arm] = [np.unique(-scores[idx], return_inverse=True)[1] for idx in self.by_cutoff]

    def evaluate(self, drug_copies):
        copies = np.asarray(drug_copies)
        if (copies.shape != self.keys.shape or copies.dtype.kind not in "iu" or (copies < 0).any()):
            raise ValueError("Supply one nonnegative integer count per drug")
        row_copies = copies[self.groups]
        event_rows = int(row_copies @ self.labels)
        event_drugs = int(copies[self.event_groups].sum())
        roster_sizes = [int(row_copies[idx].sum()) for idx in self.by_cutoff]
        capacities = [size // REVIEW_DIVISOR for size in roster_sizes]
        slots = sum(capacities)
        arms = {}
        for arm in ARMS:
            included = np.zeros(len(row_copies))
            audit = []
            for idx, ranks, capacity in zip(self.by_cutoff, self.ranks[arm], capacities, strict=True):
                tied_counts = np.bincount(ranks, weights=row_copies[idx]).astype(float, copy=False)
                preceding = tied_counts.cumsum() - tied_counts
                allocated = np.clip(capacity - preceding, 0, tied_counts)
                weights = np.divide(allocated, tied_counts, out=np.zeros_like(allocated),
                                    where=tied_counts > 0)
                included[idx] = weights[ranks]
                if not isclose(float(included[idx] @ row_copies[idx]), capacity, rel_tol=0, abs_tol=1e-9):
                    raise ValueError("Queue allocation violates cutoff capacity")
                audit.append({"allocated_slots": int(allocated.sum()),
                              "boundary_tie_rows": int(tied_counts[(weights > 0) & (weights < 1)].sum()),
                              "expected_queued_events": float(included[idx] @ (row_copies[idx] * self.labels[idx]))})
            hits = float(included @ (self.labels * row_copies))
            # Each sampled copy is a drug history. A copy is captured when any of
            # its positive rows enters a queue, with independent draws across years.
            missed = np.ones(len(copies))
            np.multiply.at(missed, self.groups[self.events], 1 - included[self.events])
            distinct_hits = float((1 - missed) @ copies)
            arms[arm] = {"recall": ratio(hits, event_rows), "precision": ratio(hits, slots),
                         "distinct_event_drug_capture": ratio(distinct_hits, event_drugs),
                         "expected_queued_events": hits, "expected_captured_event_drugs": distinct_hits,
                         "cutoffs": audit}
        return {"event_rows": event_rows, "event_drugs": event_drugs,
                "queue_slots": slots, "arms": arms,
                "cutoffs": [{"cutoff": day.isoformat(), "rows": size, "capacity": capacity}
                            for day, size, capacity in zip(self.cutoffs, roster_sizes, capacities, strict=True)]}


def interval(point, samples):
    invalid = int(np.count_nonzero(~np.isfinite(samples)))
    bounds = None
    if point is not None and not invalid:
        bounds = np.quantile(samples, (0.025, 0.975)).tolist()
    return {"estimate": point, "ci95": bounds, "undefined_draws": invalid}


def bootstrap(panel):
    """Use common cluster draws for every arm, year and contrast at this horizon."""
    n = len(panel.keys)
    point = panel.evaluate(np.ones(n, dtype=int))
    rng = np.random.default_rng(t2.BOOTSTRAP_SEED)
    samples = np.empty((t2.BOOTSTRAP_DRAWS, len(ARMS), len(METRICS)))
    for i in range(t2.BOOTSTRAP_DRAWS):
        copies = np.bincount(rng.integers(n, size=n), minlength=n) if n else np.zeros(0, dtype=int)
        arms = panel.evaluate(copies)["arms"]
        samples[i] = [[arms[arm][metric] for metric in METRICS] for arm in ARMS]
    contrasts = {}
    for left, right in PAIRS:
        a, b = ARMS.index(left), ARMS.index(right)
        contrasts[f"{left}-{right}"] = {}
        for j, metric in enumerate(METRICS):
            x, y = point["arms"][left][metric], point["arms"][right][metric]
            contrasts[f"{left}-{right}"][metric] = interval(
                x - y if x is not None and y is not None else None, samples[:, a, j] - samples[:, b, j])
    levels = {arm: {metric: interval(point["arms"][arm][metric], samples[:, i, j])
                    for j, metric in enumerate(METRICS)} for i, arm in enumerate(ARMS)}
    point.update(levels=levels, contrasts=contrasts,
                 undefined_draws=int(np.count_nonzero(~np.isfinite(samples).all(axis=(1, 2)))))
    return point


def choose_thresholds(probabilities, labels, blocked):
    """Fill as much flag capacity as score ties allow, then maximize safe clears."""
    p = np.asarray(probabilities, dtype=float)
    y = np.asarray(labels)
    blocked = np.asarray(blocked, dtype=bool)
    if (p.ndim != 1 or p.size == 0 or y.shape != p.shape or blocked.shape != p.shape
            or not np.isin(y, (0, 1)).all() or not ((p > 0) & (p < 1)).all()):
        raise ValueError("Threshold fitting requires aligned inner rows and sigmoid risks in (0, 1)")
    candidates = np.unique(p)
    budget = len(p) // REVIEW_DIVISOR
    hi = next((float(h) for h in candidates if np.count_nonzero((p >= h) & ~blocked) <= budget), 1.0)
    lo = 0.0
    for threshold in candidates[candidates < hi]:
        clear = p <= threshold
        if float(y[clear].mean()) <= CLEAR_EVENT_LIMIT:
            lo = float(threshold)
    return lo, hi


def action(arm, row, horizon, p, lo, hi):
    if arm == "M3":
        evidence = row["asof"]
        decision = graph.decide(evidence.snapshot, row["t"], horizon, p, lo=lo, hi=hi,
                                challenge_evidence=evidence.challenge.state if evidence.challenge else None)
        # Enforce the v3 clear limit even for the legacy BLOCKED no-entry action.
        if decision["action"] == graph.PREDICT_NO_ENTRY and p > lo:
            return graph.ABSTAIN, decision["conflict"]
        return decision["action"], decision["conflict"]
    if p <= lo:
        return graph.PREDICT_NO_ENTRY, False
    if p >= hi:
        return graph.PREDICT_ENTRY, False
    return graph.ABSTAIN, False


def clear_rate_ci(labels, groups):
    """Conservative 95% CI conditional on the observed clear roster.

    Scale each independent cluster's miss count into [0,1] by the largest
    cluster size. The bounded-variable MGF is at most the Poisson MGF with
    the same mean. Invert each Chernoff tail at 0.025, allowing within-drug
    dependence and a positive upper bound even when no misses are observed.
    """
    n = len(labels)
    if not n:
        return None
    max_cluster = int(np.unique(groups, return_counts=True)[1].max())
    observed = sum(labels) / max_cluster
    target = -log(0.025)
    if not observed:
        return [0.0, min(1.0, target * max_cluster / n)]

    def distance(mean):
        return mean - observed + observed * log(observed / mean)

    def invert(left, right, lower):
        for _ in range(60):
            mid = (left + right) / 2
            if (distance(mid) > target) == lower:
                left = mid
            else:
                right = mid
        return (left + right) / 2

    left = observed * exp(-1 - target / observed)
    right = 2 * (observed + target)
    bounds = invert(left, observed, True), invert(observed, right, False)
    return [min(1.0, x * max_cluster / n) for x in bounds]


def policy_metrics(arm, rows, horizon, p, lo, hi):
    t2.require_development_cutoffs(row["t"] for row in rows)
    decisions = [action(arm, row, horizon, risk, lo, hi) for row, risk in zip(rows, p, strict=True)]
    labels = np.asarray([row["y"] for row in rows], dtype=int)
    actions = np.asarray([value for value, _ in decisions], dtype=str)
    clear = actions == graph.PREDICT_NO_ENTRY
    flag = actions == graph.PREDICT_ENTRY
    refer = actions == graph.ABSTAIN
    n_clear, n_flag, n_refer = (int(mask.sum()) for mask in (clear, flag, refer))
    missed, caught = int(labels[clear].sum()), int(labels[flag].sum())
    events = int(labels.sum())
    groups = np.asarray([row["key"] for row in rows])
    return {"rows": len(rows), "events": events, "clear_rows": n_clear, "missed_events": missed,
            "clear_rate": ratio(n_clear, len(rows)), "clear_event_rate": ratio(missed, n_clear),
            "clear_event_ci95": clear_rate_ci(labels[clear], groups[clear]),
            "cleared_event_fraction": ratio(missed, events), "flag_rows": n_flag, "flag_events": caught,
            "flag_precision": ratio(caught, n_flag), "flag_recall": ratio(caught, events),
            "refer_rows": n_refer, "refer_rate": ratio(n_refer, len(rows)),
            "refer_events": int(labels[refer].sum()),
            "blocked_conflict_referrals": sum(conflict for _, conflict in decisions)}
