"""Three-valued (Kleene) evidence engine for claim-element support.

Scope: literal element support *within a given evidence packet*. It is NOT an
infringement or FTO opinion. Unknown (redacted/silent) stays UNKNOWN; nothing
here reconstructs redacted values.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Sequence, Tuple, Union

MAX_UNKNOWN_ENUM = 16  # subset enumeration guard (2^16 evaluations at most)


class T3(IntEnum):
    FALSE = 0
    UNKNOWN = 1
    TRUE = 2


# gold census status -> truth value (see PLAN-B-RESEARCH-v2.md, section 3.2)
STATE_TO_T3 = {
    "supported_met": T3.TRUE,
    "supported_not_met": T3.FALSE,
    "unknown": T3.UNKNOWN,
}
VERDICT_LABEL = {
    T3.TRUE: "elements_all_supported_met",
    T3.FALSE: "at_least_one_supported_not_met",
    T3.UNKNOWN: "unknown_due_to_holes",
}


def k_and(values: Sequence[T3]) -> T3:
    return T3(min(values)) if values else T3.TRUE


def k_or(values: Sequence[T3]) -> T3:
    return T3(max(values)) if values else T3.FALSE


@dataclass(frozen=True)
class Leaf:
    id: str


@dataclass(frozen=True)
class And:
    children: Tuple["Node", ...]


@dataclass(frozen=True)
class Or:
    children: Tuple["Node", ...]


Node = Union[Leaf, And, Or]


def all_and(*ids: str) -> And:
    """Claim branch with parents already expanded: AND of its elements."""
    return And(tuple(Leaf(i) for i in ids))


def leaves(node: Node) -> List[str]:
    """Leaf ids in textual order; raises on duplicate ids (independence needs unique leaves)."""
    out: List[str] = []

    def walk(n: Node) -> None:
        if isinstance(n, Leaf):
            out.append(n.id)
        else:
            for c in n.children:
                walk(c)

    walk(node)
    if len(set(out)) != len(out):
        raise ValueError("duplicate leaf ids in claim tree")
    return out


def is_pure_and(node: Node) -> bool:
    if isinstance(node, Leaf):
        return True
    return isinstance(node, And) and all(isinstance(c, Leaf) for c in node.children)


def evaluate(node: Node, assign: Dict[str, T3]) -> T3:
    """Kleene evaluation; missing leaves are UNKNOWN. Unknown keys raise (typo guard)."""
    ids = set(leaves(node))
    bad = set(assign) - ids
    if bad:
        raise KeyError(f"assignment has ids not in tree: {sorted(bad)}")

    def ev(n: Node) -> T3:
        if isinstance(n, Leaf):
            return T3(assign.get(n.id, T3.UNKNOWN))
        vals = [ev(c) for c in n.children]
        return k_and(vals) if isinstance(n, And) else k_or(vals)

    return ev(node)


def assignment_from_census(rows: Dict[str, str]) -> Dict[str, T3]:
    """rows: element_id -> element_state_gold string."""
    out = {}
    for k, v in rows.items():
        if v not in STATE_TO_T3:
            raise ValueError(f"invalid element_state_gold {v!r} for {k}")
        out[k] = STATE_TO_T3[v]
    return out


def _minimal_sets(unknown: List[str], node: Node, assign: Dict[str, T3],
                  set_to: T3, target: T3) -> List[Tuple[str, ...]]:
    found: List[frozenset] = []
    for size in range(1, len(unknown) + 1):
        for combo in itertools.combinations(unknown, size):
            s = frozenset(combo)
            if any(f <= s for f in found):
                continue
            trial = dict(assign)
            for leaf in combo:
                trial[leaf] = set_to
            if evaluate(node, trial) == target:
                found.append(s)
    order = {l: i for i, l in enumerate(leaves(node))}
    return [tuple(sorted(f, key=order.get)) for f in found]


def analyze(node: Node, assign: Dict[str, T3]) -> Dict[str, object]:
    """Verdict + hole structure.

    sole_blockers      : single UNKNOWN leaves whose support would make the whole branch TRUE
    completion_sets    : minimal sets of UNKNOWN leaves that, if all supported, make the branch TRUE
    falsification_sets : minimal sets of UNKNOWN leaves that, if any-all shown not met, make it FALSE
    If the verdict is already definite, the hole lists are empty.
    """
    root = evaluate(node, assign)
    unknown = [i for i in leaves(node) if T3(assign.get(i, T3.UNKNOWN)) == T3.UNKNOWN]
    res: Dict[str, object] = {
        "verdict": root,
        "verdict_label": VERDICT_LABEL[root],
        "unknown_leaves": unknown,
        "sole_blockers": [],
        "completion_sets": [],
        "falsification_sets": [],
    }
    if root != T3.UNKNOWN:
        return res
    if len(unknown) > MAX_UNKNOWN_ENUM:
        raise ValueError(f"too many unknown leaves ({len(unknown)}) for enumeration")
    comp = _minimal_sets(unknown, node, assign, T3.TRUE, T3.TRUE)
    fals = _minimal_sets(unknown, node, assign, T3.FALSE, T3.FALSE)
    res["completion_sets"] = comp
    res["falsification_sets"] = fals
    res["sole_blockers"] = [s[0] for s in comp if len(s) == 1]
    return res


def rank_unknown_for_request(node: Node, assign: Dict[str, T3]) -> List[Tuple[str, str]]:
    """Deterministic ordering of holes for evidence requests (leaf, role).
    Sole blockers first, then leaves in smaller completion sets, then others; ties by text order."""
    a = analyze(node, assign)
    if a["verdict"] != T3.UNKNOWN:
        return []
    order = {l: i for i, l in enumerate(leaves(node))}
    best: Dict[str, int] = {}
    for s in a["completion_sets"]:
        for l in s:
            best[l] = min(best.get(l, 99), len(s))
    ranked = sorted(a["unknown_leaves"], key=lambda l: (best.get(l, 99), order[l]))
    return [(l, "sole_blocker" if l in a["sole_blockers"]
             else ("in_completion_set" if l in best else "other")) for l in ranked]
