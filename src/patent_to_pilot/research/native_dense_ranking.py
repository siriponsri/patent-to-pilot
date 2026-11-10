"""Label-free exact MaxP ranking for the native DAPFAM baseline.

No encoding, qrels, domain masks, or output repair. This module consumes scores
already computed against the bound passage vectors in their original order.
"""
from __future__ import annotations

import numpy as np


def rank_maxp(scores, passage_family, family_ids, *, depth=200):
    """Resolve ties over the entire family universe before taking top-k.

    Sorting a torch.topk subset cannot enforce the lexical tie rule at its
    boundary. A full family sort is cheap for DAPFAM's45,336 families and avoids
    both arbitrary tie membership and any dependence on input family order.
    """
    values = np.asarray(scores)
    owners = np.asarray(passage_family)
    if (values.ndim != 1 or owners.shape != values.shape or not values.size
            or values.dtype.kind != "f" or owners.dtype.kind not in "iu"
            or not np.isfinite(values).all()):
        raise ValueError("invalid passage score arrays")
    if (not family_ids or any(type(f) is not str or not f for f in family_ids)
            or len(set(family_ids)) != len(family_ids)
            or type(depth) is not int or depth <= 0):
        raise ValueError("invalid family universe or depth")
    if owners.min() < 0 or owners.max() >= len(family_ids):
        raise ValueError("passage owner outside family universe")
    if len(np.unique(owners)) != len(family_ids):
        raise ValueError("family without a passage")
    best = np.full(len(family_ids), -np.inf, dtype=values.dtype)
    np.maximum.at(best, owners, values)
    order = np.lexsort((np.asarray(family_ids), -best))[:depth]
    return {"families": [family_ids[i] for i in order],
            "scores": [float(best[i]) for i in order]}
