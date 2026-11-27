"""Baselines (pure Python + optional numpy-free). No sklearn.

B0 BaseRate        : constant train prevalence.
B1 AgeHazardTable  : smoothed empirical rate per age-at-cutoff bin (the 'clock' baseline).
B2 Logistic        : L2 logistic regression via batch gradient descent (own implementation).
B3 ExclusivityRule : (Track A) deterministic rule from patent/exclusivity expiry dates.
"""
import math
from datetime import date
from typing import Dict, List, Sequence

from .dataset import FEATURE_NAMES


class BaseRate:
    name = "B0_base_rate"

    def fit(self, rows):
        self.p = sum(r["y"] for r in rows) / max(1, len(rows))
        return self

    def predict(self, rows):
        return [self.p] * len(rows)


class AgeHazardTable:
    name = "B1_age_table"

    def __init__(self, bin_years: float = 1.0, max_age: float = 30.0, prior_strength: float = 5.0):
        self.bw, self.max_age, self.m = bin_years, max_age, prior_strength

    def _bin(self, a):
        return int(min(max(a, 0.0), self.max_age) / self.bw)

    def fit(self, rows):
        self.base = sum(r["y"] for r in rows) / max(1, len(rows))
        cnt, pos = {}, {}
        for r in rows:
            b = self._bin(r["x"]["age_years"])
            cnt[b] = cnt.get(b, 0) + 1
            pos[b] = pos.get(b, 0) + r["y"]
        self.rate = {b: (pos[b] + self.m * self.base) / (cnt[b] + self.m) for b in cnt}
        return self

    def predict(self, rows):
        return [self.rate.get(self._bin(r["x"]["age_years"]), self.base) for r in rows]


def _sigmoid(z):
    if z >= 0:
        return 1 / (1 + math.exp(-z))
    e = math.exp(z)
    return e / (1 + e)


class Logistic:
    name = "B2_logistic"

    def __init__(self, l2: float = 1.0, lr: float = 0.3, epochs: int = 300, feats: Sequence[str] = tuple(FEATURE_NAMES)):
        self.l2, self.lr, self.epochs, self.feats = l2, lr, epochs, list(feats)

    def _vec(self, r):
        return [r["x"][f] for f in self.feats]

    def fit(self, rows):
        X = [self._vec(r) for r in rows]
        y = [r["y"] for r in rows]
        d, n = len(self.feats), len(rows)
        self.mu = [sum(x[j] for x in X) / n for j in range(d)]
        self.sd = [max(1e-9, (sum((x[j] - self.mu[j]) ** 2 for x in X) / n) ** 0.5) for j in range(d)]
        Z = [[(x[j] - self.mu[j]) / self.sd[j] for j in range(d)] for x in X]
        w, b = [0.0] * d, 0.0
        for _ in range(self.epochs):
            gw, gb = [0.0] * d, 0.0
            for z, t in zip(Z, y):
                err = _sigmoid(b + sum(wj * zj for wj, zj in zip(w, z))) - t
                gb += err
                for j in range(d):
                    gw[j] += err * z[j]
            for j in range(d):
                w[j] -= self.lr * (gw[j] / n + self.l2 * w[j] / n)
            b -= self.lr * gb / n
        self.w, self.b = w, b
        return self

    def predict(self, rows):
        out = []
        for r in rows:
            x = self._vec(r)
            z = self.b + sum(self.w[j] * (x[j] - self.mu[j]) / self.sd[j] for j in range(len(self.w)))
            out.append(_sigmoid(z))
        return out


def exclusivity_rule_score(snap: dict, t: date, horizon_months: int) -> int:
    """Track A deterministic baseline: 1 iff every listed patent AND exclusivity expires on/before t+h.
    This is the 'patent-clock' that incumbents sell; it ignores litigation/settlement/commercial choice."""
    from .common import add_months
    end = add_months(t, horizon_months)
    dates = list(snap.get("patent_exp", [])) + list(snap.get("excl_exp", []))
    if not dates:
        return 1
    return int(max(dates) <= end)
