"""Value-of-information planner (PLAN-B-RESEARCH-v2.md, section 4.3).

The engineering model assumes independent leaves. The prior truth probability
describes a leaf's state. The reveal probability describes an evidence action.
"""
from __future__ import annotations

import itertools
import math
from typing import Dict, List, Optional, Sequence

from .kleene import And, Leaf, Node, Or, T3, is_pure_and, leaves, evaluate

MAX_GENERAL_LEAVES = 11  # 3^11 = 177k states


def h(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def _check_probs(ps: Sequence[float]) -> None:
    for p in ps:
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"probability out of range: {p}")


def voi_and(reveal_probabilities: Sequence[float], prior_truth_probability: float = 0.5) -> float:
    """Closed form for AND over n UNKNOWN leaves. Depends only on |R| -> Poisson-binomial DP."""
    _check_probs(list(reveal_probabilities) + [prior_truth_probability])
    n = len(reveal_probabilities)
    if n == 0:
        return 0.0
    # dist[r] = P(|R| = r)
    dist = [1.0]
    for reveal in reveal_probabilities:
        new = [0.0] * (len(dist) + 1)
        for r, pr in enumerate(dist):
            new[r] += pr * (1 - reveal)
            new[r + 1] += pr * reveal
        dist = new
    truth = prior_truth_probability
    h0 = h(truth ** n)
    e_post = sum(dist[r] * (truth ** r) * h(truth ** (n - r)) for r in range(n + 1))
    return h0 - e_post


def _p_true(node: Node, state: Dict[str, float]) -> float:
    if isinstance(node, Leaf):
        return state[node.id]
    ps = [_p_true(c, state) for c in node.children]
    if isinstance(node, And):
        out = 1.0
        for x in ps:
            out *= x
        return out
    out = 1.0
    for x in ps:
        out *= (1 - x)
    return 1 - out


def voi_general(node: Node, reveal_probabilities: Dict[str, float], assign: Optional[Dict[str, T3]] = None,
                prior_truth_probability: float = 0.5) -> float:
    """Exact expected entropy reduction for any AND/OR tree with unique leaves.
    An UNKNOWN leaf with no specified reveal probability stays hidden."""
    assign = assign or {}
    ids = leaves(node)
    unknown = [i for i in ids if T3(assign.get(i, T3.UNKNOWN)) == T3.UNKNOWN]
    if len(unknown) > MAX_GENERAL_LEAVES:
        raise ValueError(f"{len(unknown)} unknown leaves exceeds exact-enumeration cap")
    truth = prior_truth_probability
    _check_probs(list(reveal_probabilities.values()) + [truth])
    base = {i: (1.0 if assign.get(i) == T3.TRUE else 0.0) for i in ids if i not in unknown}
    prior_state = dict(base, **{i: truth for i in unknown})
    h0 = h(_p_true(node, prior_state))
    e_post = 0.0
    for combo in itertools.product((0, 1, 2), repeat=len(unknown)):  # 0 hidden, 1 revealed T, 2 revealed F
        prob = 1.0
        state = dict(base)
        for leaf, c in zip(unknown, combo):
            reveal = reveal_probabilities.get(leaf, 0.0)
            if c == 0:
                prob *= 1 - reveal
                state[leaf] = truth
            elif c == 1:
                prob *= reveal * truth
                state[leaf] = 1.0
            else:
                prob *= reveal * (1 - truth)
                state[leaf] = 0.0
            if prob == 0.0:
                break
        if prob == 0.0:
            continue
        e_post += prob * h(_p_true(node, state))
    return h0 - e_post


def voi(node: Node, reveal_probabilities: Dict[str, float], assign: Optional[Dict[str, T3]] = None,
        prior_truth_probability: float = 0.5) -> float:
    assign = assign or {}
    if evaluate(node, assign) != T3.UNKNOWN:
        return 0.0
    ids = leaves(node)
    unknown = [i for i in ids if T3(assign.get(i, T3.UNKNOWN)) == T3.UNKNOWN]
    if is_pure_and(node) and all(T3(assign.get(i, T3.UNKNOWN)) in (T3.UNKNOWN, T3.TRUE) for i in ids):
        return voi_and([reveal_probabilities.get(i, 0.0) for i in unknown], prior_truth_probability)
    return voi_general(node, reveal_probabilities, assign, prior_truth_probability)


def estimate_p(k: int, n: int, p0: float, alpha: float, lam: float = 0.0,
               rho: float = 0.0, redaction_prone: bool = False) -> float:
    """p(a,i) = (k + alpha*p0)/(n + alpha) * (1 - lam*rho*I[prone]); clipped to [0,1].
    k,n counts come from DEVELOPMENT census only; p0 is a frozen domain prior."""
    if n < 0 or k < 0 or k > n or alpha <= 0:
        raise ValueError("require 0<=k<=n and alpha>0")
    base = (k + alpha * p0) / (n + alpha)
    adj = 1.0 - (lam * rho if redaction_prone else 0.0)
    return min(1.0, max(0.0, base * adj))


def plan(node: Node, actions: Dict[str, Dict], assign: Optional[Dict[str, T3]] = None,
         prior_truth_probability: float = 0.5, tau: float = 0.0) -> Dict[str, object]:
    """Each action stores per-leaf reveal probabilities in "p" and a positive "cost".
    Returns ranking by VoI/cost; decision 'open:<name>' or 'request_only' if max VoI < tau
    (also request_only when the verdict is already definite)."""
    rows = []
    for name in sorted(actions):  # sorted -> deterministic tie-break by name
        c = actions[name]["cost"]
        if c <= 0:
            raise ValueError("cost must be > 0")
        v = voi(node, reveal_probabilities=actions[name]["p"], assign=assign,
                prior_truth_probability=prior_truth_probability)
        rows.append({"action": name, "voi": v, "cost": c, "score": v / c})
    rows.sort(key=lambda r: (-r["score"], r["action"]))
    best_voi = max((r["voi"] for r in rows), default=0.0)
    decision = "request_only" if (not rows or best_voi < tau or best_voi == 0.0) else f"open:{rows[0]['action']}"
    return {"ranking": rows, "decision": decision}


# Checklist baseline (arm A): fixed, field-aware, deterministic. Mapping is a placeholder to be frozen in B3.
CHECKLIST = {"strength": "label", "form": "label", "route": "label",
             "composition": "review", "process": "review", "property": "review", "distribution": "review"}


def checklist_choice(feature_type: str, tie_break: str = "label") -> str:
    return CHECKLIST.get(feature_type, tie_break)
