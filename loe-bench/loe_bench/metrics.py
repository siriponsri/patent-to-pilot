"""Metrics: Brier, ECE, AUROC (rank-based, ties averaged), risk-coverage curve, AURC, bootstrap CI."""
import random
from typing import List, Sequence, Tuple


def brier(p: Sequence[float], y: Sequence[int]) -> float:
    return sum((a - b) ** 2 for a, b in zip(p, y)) / len(y)


def ece(p: Sequence[float], y: Sequence[int], bins: int = 10) -> float:
    n = len(y)
    tot = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i in range(n) if (lo <= p[i] < hi) or (b == bins - 1 and p[i] == 1.0)]
        if idx:
            conf = sum(p[i] for i in idx) / len(idx)
            acc = sum(y[i] for i in idx) / len(idx)
            tot += len(idx) / n * abs(conf - acc)
    return tot


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


def risk_coverage(p: Sequence[float], y: Sequence[int], thr: float = 0.5) -> List[Tuple[float, float]]:
    """Confidence = max(p,1-p). Answer most-confident first. Returns [(coverage, error_rate)]."""
    conf = [max(a, 1 - a) for a in p]
    pred = [int(a >= thr) for a in p]
    order = sorted(range(len(p)), key=lambda i: -conf[i])
    out, err = [], 0
    for k, i in enumerate(order, 1):
        err += int(pred[i] != y[i])
        out.append((k / len(p), err / k))
    return out


def aurc(p: Sequence[float], y: Sequence[int]) -> float:
    rc = risk_coverage(p, y)
    return sum(r for _, r in rc) / len(rc)


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
