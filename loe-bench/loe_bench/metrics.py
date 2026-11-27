"""Metrics: Brier, ECE, AUROC (rank-based, ties averaged), risk-coverage curve, AURC, bootstrap CI."""
import math
import random
from bisect import bisect_right
from itertools import groupby
from typing import List, NamedTuple, Optional, Sequence, Tuple


def brier(p: Sequence[float], y: Sequence[int]) -> float:
    return sum((a - b) ** 2 for a, b in zip(p, y)) / len(y)


class CalibrationError(NamedTuple):
    ece: float
    bin_counts: Tuple[int, ...]


def ece(p: Sequence[float], y: Sequence[int], bins: int = 10) -> CalibrationError:
    """Equal-width ECE and counts in bin order. The last bin includes 1."""
    if len(p) != len(y) or len(y) == 0:
        raise ValueError("ECE requires non-empty, equally sized probabilities and labels")
    if not isinstance(bins, int) or isinstance(bins, bool) or bins < 1:
        raise ValueError("bins must be a positive integer")
    if any(not 0 <= probability <= 1 for probability in p):
        raise ValueError("probabilities must be in [0, 1]")
    if any(label not in (0, 1) for label in y):
        raise ValueError("labels must be binary")
    counts = [0] * bins
    residuals = [[] for _ in range(bins)]
    edges = [b / bins for b in range(1, bins)]
    for probability, label in zip(p, y):
        i = bisect_right(edges, probability)
        counts[i] += 1
        residuals[i].append(probability - label)
    return CalibrationError(sum(abs(math.fsum(bucket)) for bucket in residuals) / len(y),
                            tuple(counts))


def auroc(p: Sequence[float], y: Sequence[int]) -> float:
    pos = [i for i in range(len(y)) if y[i] == 1]
    neg = [i for i in range(len(y)) if y[i] == 0]
    if not pos or not neg:
        return float("nan")
    order = sorted(range(len(p)), key=lambda i: p[i])
    ranks = [0.0] * len(p)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and p[order[j + 1]] == p[order[i]]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    s = sum(ranks[i] for i in pos)
    return (s - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def risk_coverage(p: Sequence[float], y: Sequence[int], thr: float = 0.5, *,
                  scores: Optional[Sequence[float]] = None,
                  actions: Optional[Sequence[str]] = None) -> List[Tuple[float, float]]:
    """Order answered rows by descending score. Coverage uses the entire cohort.

    Without policy actions, threshold p to assign labels. Without scores, use
    max(p, 1-p). Within a tie group, each prefix has the expected error count
    under uniform random ordering of the group.
    """
    n = len(y)
    if len(p) != n or (scores is not None and len(scores) != n) or (actions is not None and len(actions) != n):
        raise ValueError("probabilities, labels, scores and actions must align")
    if scores is None:
        scores = [max(prob, 1 - prob) for prob in p]
    pred = [int(prob >= thr) for prob in p]
    if actions is not None:
        policy_labels = {"PREDICT_ENTRY": 1, "PREDICT_NO_ENTRY": 0, "ABSTAIN_REFER_TO_EVALUATOR": None}
        try:
            pred = [policy_labels[action] for action in actions]
        except KeyError as exc:
            raise ValueError(f"unknown policy action: {exc.args[0]}") from exc
    ranked = [(score, int(call != label)) for score, call, label in zip(scores, pred, y) if call is not None]
    if any(not math.isfinite(score) for score, _ in ranked):
        raise ValueError("scores for answered rows must be finite")
    ranked.sort(key=lambda row: row[0], reverse=True)
    out = []
    answered = errors = 0
    for _, ties in groupby(ranked, key=lambda row: row[0]):
        group = [error for _, error in ties]
        group_errors = sum(group)
        for j in range(1, len(group) + 1):
            k = answered + j
            expected_errors = errors + j * group_errors / len(group)
            out.append((k / n, expected_errors / k))
        answered += len(group)
        errors += group_errors
    return out


def aurc(p: Sequence[float], y: Sequence[int], thr: float = 0.5, *,
         scores: Optional[Sequence[float]] = None, actions: Optional[Sequence[str]] = None) -> float:
    """Right-step area up to achieved policy coverage. All-abstain is undefined."""
    rc = risk_coverage(p, y, thr, scores=scores, actions=actions)
    return math.fsum(risk for _, risk in rc) / len(y) if rc else float("nan")


def selective_error(p: Sequence[float], y: Sequence[int], lo: float, hi: float) -> dict:
    """Abstain when lo < p < hi. Report coverage and error among answered."""
    ans = [i for i in range(len(p)) if p[i] <= lo or p[i] >= hi]
    if not ans:
        return {"coverage": 0.0, "error": float("nan"), "n_answered": 0}
    err = sum(int((p[i] >= hi) != bool(y[i])) for i in ans) / len(ans)
    return {"coverage": len(ans) / len(p), "error": err, "n_answered": len(ans)}


def bootstrap_ci(fn, p, y, n_boot: int = 500, seed: int = 0, alpha: float = 0.05):
    rng = random.Random(seed)
    n = len(y)
    vals = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        v = fn([p[i] for i in idx], [y[i] for i in idx])
        if v == v:
            vals.append(v)
    vals.sort()
    if not vals:
        return (float("nan"), float("nan"))
    return (vals[int(alpha / 2 * len(vals))], vals[min(len(vals) - 1, int((1 - alpha / 2) * len(vals)))])


def cluster_bootstrap_ci(fn, p, y, groups, n_boot: int = 300, seed: int = 0, alpha: float = 0.05):
    """Resample whole groups (e.g. drug entities) because (entity, cutoff) rows are NOT independent."""
    rng = random.Random(seed)
    by = {}
    for i, g in enumerate(groups):
        by.setdefault(g, []).append(i)
    keys = list(by)
    vals = []
    for _ in range(n_boot):
        idx = []
        for _k in range(len(keys)):
            idx.extend(by[keys[rng.randrange(len(keys))]])
        v = fn([p[i] for i in idx], [y[i] for i in idx])
        if v == v:
            vals.append(v)
    vals.sort()
    if not vals:
        return (float("nan"), float("nan"))
    return (vals[int(alpha / 2 * len(vals))], vals[min(len(vals) - 1, int((1 - alpha / 2) * len(vals)))])


def paired_cluster_bootstrap_ci(fn, arm_a, arm_b, y, groups,
                                n_boot: int = 300, seed: int = 0, alpha: float = 0.05):
    """Return (lower, upper, invalid_draws) for the paired difference A minus B.

    The metric receives a sampled arm and the same sampled labels for each
    arm. Arm entries can bundle a probability, ranking score and policy action.
    A draw with a non-finite result contributes only to invalid_draws.
    """
    if not len(arm_a) == len(arm_b) == len(y) == len(groups) or len(y) == 0:
        raise ValueError("both arms, labels and cluster IDs must align and be non-empty")
    if n_boot < 1 or not 0 < alpha < 1:
        raise ValueError("require at least one draw and alpha in (0, 1)")
    by_group = {}
    for i, group in enumerate(groups):
        by_group.setdefault(group, []).append(i)
    clusters = list(by_group.values())
    rng = random.Random(seed)
    deltas = []
    for _ in range(n_boot):
        idx = [i for _ in clusters for i in rng.choice(clusters)]
        labels = [y[i] for i in idx]
        delta = fn([arm_a[i] for i in idx], labels) - fn([arm_b[i] for i in idx], labels)
        if math.isfinite(delta):
            deltas.append(delta)
    n = len(deltas)
    if n == 0:
        return float("nan"), float("nan"), n_boot
    deltas.sort()
    return deltas[int(alpha / 2 * n)], deltas[min(n - 1, int((1 - alpha / 2) * n))], n_boot - n
