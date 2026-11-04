"""Pure functions for the PAR4PC claim-level prior-art option-ranking study.

Rankers never read labels. Metrics treat PANORAMA gold answers (examiner-cited
for the claim's rejection) as relevant; silver answers get graded credit only
in nDCG. Uncertainty resamples applications, the independent unit.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Iterable, Mapping, Sequence

RRF_K = 60


def rank_by_scores(scores: Mapping[str, float]) -> list[str]:
    """Descending score; ties broken by option letter for determinism."""
    return sorted(scores, key=lambda key: (-scores[key], key))


def rrf(rankings: Sequence[Sequence[str]], k: int = RRF_K) -> list[str]:
    fused: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for position, key in enumerate(ranking, start=1):
            fused[key] += 1.0 / (k + position)
    return rank_by_scores(fused)


def bm25_margin(scores: Mapping[str, float]) -> float:
    """Relative gap between the top two lexical scores; 0 when undecidable."""
    ordered = sorted(scores.values(), reverse=True)
    if len(ordered) < 2 or ordered[0] <= 0:
        return 0.0
    return (ordered[0] - ordered[1]) / ordered[0]


def cascade(lexical: Sequence[str], fused: Sequence[str], margin: float, tau: float) -> tuple[list[str], bool]:
    """Keep the lexical ranking when its margin is at least tau, else escalate."""
    if margin >= tau:
        return list(lexical), False
    return list(fused), True


def row_metrics(ranked: Sequence[str], gold: Iterable[str], silver: Iterable[str] = ()) -> dict[str, float]:
    gold, silver = set(gold), set(silver) - set(gold)
    if not gold:
        raise ValueError("row without gold answers")
    first = next((i for i, key in enumerate(ranked, start=1) if key in gold), None)
    rel = {key: 2 for key in gold} | {key: 1 for key in silver}
    dcg = sum((2 ** rel.get(key, 0) - 1) / math.log2(i + 1) for i, key in enumerate(ranked[:8], start=1))
    ideal = sorted(rel.values(), reverse=True)[:8]
    idcg = sum((2 ** r - 1) / math.log2(i + 1) for i, r in enumerate(ideal, start=1))
    return {
        "rr": 0.0 if first is None else 1.0 / first,
        "hit1": float(bool(ranked) and ranked[0] in gold),
        "recall3": len(gold & set(ranked[:3])) / len(gold),
        "ndcg8": dcg / idcg if idcg else 0.0,
    }


def app_macro(values: Mapping[str, float], groups: Mapping[str, str]) -> float:
    """Mean over applications of the mean over that application's rows."""
    by_group: dict[str, list[float]] = defaultdict(list)
    for key, value in values.items():
        by_group[groups[key]].append(value)
    return sum(sum(v) / len(v) for v in by_group.values()) / len(by_group)


def paired_cluster_bootstrap(a: Mapping[str, float], b: Mapping[str, float], groups: Mapping[str, str],
                             *, resamples: int = 10000, seed: int = 20261104) -> dict[str, float]:
    """95% percentile CI for app-macro(a) - app-macro(b), resampling applications."""
    if set(a) != set(b):
        raise ValueError("paired comparison needs identical row keys")
    per_group: dict[str, list[float]] = defaultdict(list)
    for key in a:
        per_group[groups[key]].append(a[key] - b[key])
    group_means = [sum(v) / len(v) for _, v in sorted(per_group.items())]
    n = len(group_means)
    rng = random.Random(seed)
    draws = sorted(sum(group_means[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    observed = sum(group_means) / n
    lo, hi = draws[int(0.025 * resamples)], draws[int(0.975 * resamples) - 1]
    # Two-sided bootstrap p-value: share of resamples on the other side of zero.
    p = min(1.0, 2 * min(sum(d <= 0 for d in draws), sum(d >= 0 for d in draws)) / resamples)
    return {"delta": observed, "ci95_low": lo, "ci95_high": hi, "p_bootstrap": p, "groups": n}


def holm(pvalues: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    adjusted, running = {}, 0.0
    for i, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - i) * p))
        adjusted[name] = running
    return adjusted
