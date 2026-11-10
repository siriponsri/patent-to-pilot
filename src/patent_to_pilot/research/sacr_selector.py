"""SACR-v0 proposed similarity proxy. No labels, extraction or search here."""
from __future__ import annotations

import numpy as np


def ranknorm(values) -> np.ndarray:
    scores = np.asarray(values, dtype=np.float64)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError("rank normalization requires finite nonempty scores")
    if len(scores) == 1:
        return np.ones(1)
    unique, inverse, counts = np.unique(scores, return_inverse=True, return_counts=True)
    if len(unique) == 1:
        return np.full(len(scores), 0.5)
    starts = np.cumsum(counts) - counts
    average_ranks = starts + (counts - 1) / 2
    return ((average_ranks - average_ranks[0]) / (average_ranks[-1] - average_ranks[0]))[inverse]


def local_coverage(block_cosines, beta: float = 0.5) -> float:
    """Each block is [components, same-family passages]; reduce locally first.

    All blocks use the same indexed passages and preserve their order. A
    condition-free block has one component (its relation). Empty profiles must
    use the separately declared anchor fallback, not an invented zero score.
    """
    if not np.isfinite(beta) or not 0 <= beta <= 1 or not block_cosines:
        raise ValueError("invalid block set or bottleneck weight")
    best, passages = [], None
    for block in block_cosines:
        scores = np.asarray(block, dtype=np.float64)
        if (scores.ndim != 2 or 0 in scores.shape or not np.isfinite(scores).all() or
                (np.abs(scores) > 1 + 1e-6).any()):
            raise ValueError("invalid component cosine matrix")
        if passages is not None and scores.shape[1] != passages:
            raise ValueError("blocks must use identical passage population")
        passages = scores.shape[1]
        z = (1 + np.clip(scores, -1, 1)) / 2
        joint = (1 - beta) * z.mean(axis=0) + beta * z.min(axis=0)
        best.append(float(joint.max()))
    return max(best)


def select_union(family_ids: list[str], anchor_scores, coverage_scores, *,
                 depth: int = 200, alpha: float = 0.5) -> list[dict]:
    """Rank an already eligible, deduplicated union; never expand its exposure."""
    if (type(depth) is not int or depth <= 0 or not np.isfinite(alpha) or not 0 <= alpha <= 1 or
            any(type(value) is not str or not value or value != value.strip() for value in family_ids) or
            len(set(family_ids)) != len(family_ids)):
        raise ValueError("invalid union, depth or anchor weight")
    anchor, coverage = np.asarray(anchor_scores, dtype=np.float64), np.asarray(coverage_scores, dtype=np.float64)
    if anchor.shape != (len(family_ids),) or coverage.shape != anchor.shape:
        raise ValueError("union score dimensions disagree")
    if not len(family_ids):
        return []
    if (not np.isfinite(coverage).all() or (coverage < 0).any() or (coverage > 1).any()):
        raise ValueError("invalid local coverage scores")
    fused = alpha * ranknorm(anchor) + (1 - alpha) * ranknorm(coverage)
    order = sorted(range(len(family_ids)), key=lambda i: (-fused[i], -anchor[i], family_ids[i]))
    return [{"family_id": family_ids[i], "score": float(fused[i]),
             "anchor_score": float(anchor[i]), "coverage_score": float(coverage[i]),
             "semantic_status": "unknown"} for i in order[:depth]]
