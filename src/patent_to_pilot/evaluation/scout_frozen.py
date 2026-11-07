"""Frozen-protocol metrics for Solution Scout (E1, E2, E5). Pure functions; no I/O.

Protocol: docs/healthtech/research/SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from patent_to_pilot.evaluation.par4pc_study import holm, paired_cluster_bootstrap

SEED = 20261106
RESAMPLES = 5000
VIEWS = ("P", "T", "R2")
BUDGETS = (20, 200)


def recall(pool: Sequence[str], relevant: set[str], k: int) -> float:
    return len(set(pool[:k]) & relevant) / len(relevant)


def single_pool(u: Sequence[str], k: int) -> list[str]:
    return list(u[:k])


def two_lane_pool(o: Sequence[str], x: Sequence[str], k: int) -> list[str]:
    """O[:k/2] then X[:k/2]; the lanes are disjoint by construction, duplicates are dropped defensively."""
    half = k // 2
    return list(dict.fromkeys(list(o[:half]) + list(x[:half])))


def per_query(pools: Mapping[str, Sequence[str]], relevant: Mapping[str, set[str]], k: int) -> dict[str, float]:
    """Recall@k for every query with a non-empty relevant set; a missing pool scores 0."""
    return {q: recall(pools.get(q, []), rel, k) for q, rel in relevant.items() if rel}


def contrast(a: Mapping[str, float], b: Mapping[str, float]) -> dict[str, float]:
    ident = {q: q for q in a}
    return paired_cluster_bootstrap(a, b, ident, resamples=RESAMPLES, seed=SEED)


def grounding_decision(rows: Sequence[Mapping]) -> dict:
    """E3 decision. rows: {key, cluster, v0_g1, v1_g1, v0_g2, v1_g2} with 0/1 values, one row per candidate pair.

    Adopt v1 when G1 (v1 - v0) has 95% lower bound > 0 and G2 (v1 - v0) has 95% lower bound > -0.05.
    """
    clusters = {r["key"]: r["cluster"] for r in rows}
    out = {}
    for g in ("g1", "g2"):
        a = {r["key"]: float(r[f"v1_{g}"]) for r in rows}
        b = {r["key"]: float(r[f"v0_{g}"]) for r in rows}
        out[g] = {"v0": sum(b.values()) / len(b), "v1": sum(a.values()) / len(a),
                  "v1_minus_v0": paired_cluster_bootstrap(a, b, clusters, resamples=RESAMPLES, seed=SEED)}
    adopt = out["g1"]["v1_minus_v0"]["ci95_low"] > 0 and out["g2"]["v1_minus_v0"]["ci95_low"] > -0.05
    return {**out, "pairs": len(rows), "clusters": len(set(clusters.values())), "non_inferiority_margin": 0.05,
            "decision": "ADOPT_V1" if adopt else "KEEP_V0"}


def brief_gap(full: Mapping[str, Sequence[str]], brief: Mapping[str, Sequence[str]],
              relevant: Mapping[str, set[str]]) -> dict:
    """E5: brief (T) minus full text on Recall@20 and @200 over queries with positives."""
    out = {}
    for k in BUDGETS:
        f, t = per_query(full, relevant, k), per_query(brief, relevant, k)
        out[f"k{k}"] = {"full": sum(f.values()) / len(f), "title": sum(t.values()) / len(t),
                        "title_minus_full": contrast(t, f), "queries": len(f)}
    return out


def e1_e2(rankings: Mapping[str, Mapping[str, Sequence[str]]], out_rel: Mapping[str, set[str]],
          in_rel: Mapping[str, set[str]]) -> dict:
    """rankings[f"{u|o|x}-{view}"][query] -> ranked families. Returns the E1 and E2 blocks of the protocol."""
    def get(kind: str, view: str) -> Mapping[str, Sequence[str]]:
        return rankings.get(f"{kind}-{view}", {})

    queries = set(out_rel) | set(in_rel)
    result: dict = {"E1": {}, "E2": {"protocol_effect": {}, "brief_cost": {}}}
    for view in VIEWS:
        block = {}
        for k in BUDGETS:
            single = {q: single_pool(get("u", view).get(q, []), k) for q in queries}
            lanes = {q: two_lane_pool(get("o", view).get(q, []), get("x", view).get(q, []), k) for q in queries}
            row = {}
            for name, rel in (("out", out_rel), ("in", in_rel)):
                s, t = per_query(single, rel, k), per_query(lanes, rel, k)
                row[name] = {"single": sum(s.values()) / len(s), "two_lane": sum(t.values()) / len(t),
                             "two_lane_minus_single": contrast(t, s), "queries": len(s)}
            hits = [bool(set(lanes[q][:k]) & rel) for q, rel in out_rel.items() if rel]
            row["out_hit_two_lane"] = sum(hits) / len(hits)
            block[f"k{k}"] = row
        result["E1"][view] = block
        effect = {}
        for k in BUDGETS:
            u = per_query({q: get("u", view).get(q, []) for q in queries}, out_rel, k)
            x = per_query({q: get("x", view).get(q, []) for q in queries}, out_rel, k)
            effect[f"k{k}"] = {"full_candidates": sum(u.values()) / len(u), "other_fields_only": sum(x.values()) / len(x),
                               "other_fields_only_minus_full": contrast(x, u)}
        result["E2"]["protocol_effect"][view] = effect
    for view in ("P", "T"):
        cost = {}
        for kind, rel, label in (("u", out_rel, "out_full_candidates"), ("x", out_rel, "out_other_fields_only"),
                                 ("u", in_rel, "in_full_candidates")):
            a = per_query({q: get(kind, view).get(q, []) for q in queries}, rel, 200)
            b = per_query({q: get(kind, "R2").get(q, []) for q in queries}, rel, 200)
            cost[label] = contrast(a, b)
        result["E2"]["brief_cost"][f"{view}_minus_R2_at200"] = cost
    primary = {"H1a_out_recall_at20": result["E1"]["P"]["k20"]["out"]["two_lane_minus_single"],
               "H1b_in_recall_at20": result["E1"]["P"]["k20"]["in"]["two_lane_minus_single"]}
    adjusted = holm({name: value["p_bootstrap"] for name, value in primary.items()})
    result["primary"] = {name: {**value, "p_holm": adjusted[name]} for name, value in primary.items()}
    return result
