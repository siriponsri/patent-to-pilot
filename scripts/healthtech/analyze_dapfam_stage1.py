"""Stage 1 (dev only): score every action and fixed mix, pick F* and M*, compute the oracle and the headroom gate.

Actions (each a Top-200 family list per query):
  R1 BM25 over title+abstract+claims    R2 dense passage, single-window query    R3 RRF(R1, R2)
  Q1 RRF(dense(functional query), BM25(functional query))
  Q2 dense(functional query) restricted to the proposed IPC classes    Q3 dense(pseudo-document)
A fixed mix merges its actions round-robin in the canonical order above under a 200-family budget.
Writes aggregate results to --output and per-query rows to --private-output. Test queries are never read.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import (  # noqa: E402
    POOL_DEPTH, assign_folds, budgeted_merge, crossfit_select, positive_relations)
from patent_to_pilot.evaluation.par4pc_study import paired_cluster_bootstrap, rrf  # noqa: E402

ACTIONS = ("R1", "R2", "R3", "Q1", "Q2", "Q3")
FIXED_SINGLE = ("R1", "R2", "R3")
GATE_ORACLE_MARGIN = 0.03
GATE_Q_SHARE = 0.10
CROSSFIT_FOLDS = 5
CROSSFIT_MIN_SECTION = 20


def _load(path: Path) -> dict[str, list[str]]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["query_id"]] = row["families"][:POOL_DEPTH]
    return rows


def _recall(pool: list[str], relevant: set[str], k: int = POOL_DEPTH) -> float:
    return len(set(pool[:k]) & relevant) / len(relevant)


def llm_calls(subset: tuple[str, ...]) -> int:
    return int(bool({"Q1", "Q2"} & set(subset))) + int("Q3" in subset)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("r1", "r2", "q1_dense", "q1_bm25", "q2", "q3"):
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, default=ROOT / "methodology/datasets/research-only-nc/qrels_all.parquet")
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    import pyarrow.parquet as pq

    split_doc = json.loads(args.split.read_text(encoding="utf-8"))
    split, sections = split_doc["assignment"], split_doc["first_ipc_section"]
    dev = sorted(q for q, s in split.items() if s == "dev")
    positives = positive_relations(pq.read_table(args.qrels).to_pylist())
    out_rel = {q: positives.get(q, {}).get("OUT", set()) for q in dev}
    in_rel = {q: positives.get(q, {}).get("IN", set()) for q in dev}
    all_rel = {q: out_rel[q] | in_rel[q] for q in dev}
    out_q = [q for q in dev if out_rel[q]]
    in_q = [q for q in dev if in_rel[q]]
    all_q = [q for q in dev if all_rel[q]]

    r1, r2 = _load(args.r1), _load(args.r2)
    q1d, q1b, q2, q3 = _load(args.q1_dense), _load(args.q1_bm25), _load(args.q2), _load(args.q3)
    actions = {
        q: {"R1": r1.get(q, []), "R2": r2.get(q, []), "R3": rrf([r1.get(q, []), r2.get(q, [])])[:POOL_DEPTH],
            "Q1": rrf([lst for lst in (q1d.get(q), q1b.get(q)) if lst])[:POOL_DEPTH],
            "Q2": q2.get(q, []), "Q3": q3.get(q, [])}
        for q in dev
    }
    missing = {a: sum(1 for q in dev if not actions[q][a]) for a in ACTIONS}

    subsets = [s for n in range(1, len(ACTIONS) + 1) for s in combinations(ACTIONS, n)]
    per_query: dict[str, dict[str, float]] = {q: {} for q in dev}
    summary = {}
    for subset in subsets:
        key = "+".join(subset)
        pools = {q: budgeted_merge([actions[q][a] for a in subset]) for q in dev}
        for q in out_q:
            per_query[q][key] = _recall(pools[q], out_rel[q])
        summary[key] = {
            "out_recall_at_200": sum(per_query[q][key] for q in out_q) / len(out_q),
            "out_recall_at_100": sum(_recall(pools[q], out_rel[q], 100) for q in out_q) / len(out_q),
            "out_hit_at_200": sum(bool(set(pools[q]) & out_rel[q]) for q in out_q) / len(out_q),
            "in_recall_at_200": sum(_recall(pools[q], in_rel[q]) for q in in_q) / len(in_q),
            "all_recall_at_200": sum(_recall(pools[q], all_rel[q]) for q in all_q) / len(all_q),
            "llm_calls_per_query": llm_calls(subset),
        }
    f_star = max(FIXED_SINGLE, key=lambda a: (summary[a]["out_recall_at_200"], a == "R2"))
    m_star = max(summary, key=lambda k: (round(summary[k]["out_recall_at_200"], 12), -summary[k]["llm_calls_per_query"], -k.count("+")))
    oracle = sum(max(per_query[q].values()) for q in out_q) / len(out_q)
    oracle_no_llm = sum(max(v for k, v in per_query[q].items() if not ({"Q1", "Q2", "Q3"} & set(k.split("+"))))
                        for q in out_q) / len(out_q)

    found_r: set[tuple[str, str]] = set()
    found_q: set[tuple[str, str]] = set()
    for q in out_q:
        for a in ACTIONS:
            hits = {(q, f) for f in actions[q][a] if f in out_rel[q]}
            (found_q if a.startswith("Q") else found_r).update(hits)
    union = found_r | found_q
    q_only = found_q - found_r
    q_share = len(q_only) / len(union) if union else 0.0

    f_pools = {q: actions[q][f_star] for q in out_q}
    pairs = sum(len(out_rel[q]) for q in out_q)
    in_200 = sum(len(set(f_pools[q]) & out_rel[q]) for q in out_q)
    in_100 = sum(len(set(f_pools[q][:100]) & out_rel[q]) for q in out_q)
    ceiling = sum(min(len(set(f_pools[q]) & out_rel[q]), 100) / len(out_rel[q]) for q in out_q) / len(out_q)

    gate = {
        "oracle_minus_f_star": oracle - summary[f_star]["out_recall_at_200"],
        "oracle_margin_required": GATE_ORACLE_MARGIN,
        "q_only_share_of_unique_out_positives": q_share,
        "q_share_required": GATE_Q_SHARE,
        "q_share_definition": "strict-OUT positives found in some Q action's Top-200 and in no R action's Top-200, over all positives found by any action",
    }
    gate["status"] = "PASS" if gate["oracle_minus_f_star"] >= GATE_ORACLE_MARGIN and q_share >= GATE_Q_SHARE else "FAIL"

    # Amendment 1 (recorded before any Q-action result was seen): the per-query oracle maximises over
    # 63 correlated pools, so it is inflated by selection. Report how far the label-free R-only
    # oracle already sits above F*, and estimate learnable headroom by 5-fold cross-fitting.
    section = {q: sections.get(q, "?") for q in out_q}
    folds = assign_folds(section, k=CROSSFIT_FOLDS)
    cost = {k: (summary[k]["llm_calls_per_query"], k.count("+") + 1) for k in summary}
    scores = {q: per_query[q] for q in out_q}
    chosen_global = crossfit_select(scores, folds, cost)
    chosen_section = crossfit_select(scores, folds, cost, section, min_group=CROSSFIT_MIN_SECTION)
    held = {name: {q: per_query[q][mix] for q, mix in chosen.items()}
            for name, chosen in (("global_mix", chosen_global), ("per_section_mix", chosen_section))}
    f_rows = {q: per_query[q][f_star] for q in out_q}
    ident = {q: q for q in out_q}
    crossfit = {
        "folds": CROSSFIT_FOLDS, "fold_strata": "first-IPC section", "min_section_train_queries": CROSSFIT_MIN_SECTION,
        "bootstrap_unit": "query (dev is dominated by one large component, so component resampling is not informative)",
        "held_out_out_recall_at_200": {"f_star": sum(f_rows.values()) / len(f_rows),
                                       **{k: sum(v.values()) / len(v) for k, v in held.items()}},
        "global_mix_minus_f_star": paired_cluster_bootstrap(held["global_mix"], f_rows, ident, resamples=5000),
        "per_section_minus_global": paired_cluster_bootstrap(held["per_section_mix"], held["global_mix"], ident,
                                                             resamples=5000),
        "mixes_chosen_global": dict(Counter(chosen_global.values())),
        "mixes_chosen_per_section": dict(Counter(chosen_section.values())),
        "llm_calls_per_query": {k: sum(llm_calls(tuple(m.split("+"))) for m in c.values()) / len(c)
                                for k, c in (("global_mix", chosen_global), ("per_section_mix", chosen_section))},
    }
    selection_inflation = {"oracle_without_llm_minus_f_star": oracle_no_llm - summary[f_star]["out_recall_at_200"],
                           "oracle_minus_oracle_without_llm": oracle - oracle_no_llm,
                           "single_action_oracle": sum(max(per_query[q][a] for a in ACTIONS) for q in out_q) / len(out_q)}
    decisions = {
        "carry_fixed_mix_claim_to_test": crossfit["global_mix_minus_f_star"]["ci95_low"] > 0,
        "carry_section_adaptive_claim_to_stage2": crossfit["per_section_minus_global"]["delta"] > 0,
    }
    top_mixes = sorted(summary, key=lambda k: -summary[k]["out_recall_at_200"])[:10]
    result = {
        "format": "ptp-org-adaptive-stage1-dev-v1", "split": "dev", "test_split_read": False,
        "queries": {"dev": len(dev), "out_eligible": len(out_q), "in_eligible": len(in_q)},
        "empty_action_lists": missing,
        "single_actions": {a: summary[a] for a in ACTIONS},
        "f_star": {"action": f_star, **summary[f_star]},
        "m_star": {"mix": m_star, **summary[m_star]},
        "m_star_minus_f_star": {k: summary[m_star][k] - summary[f_star][k] for k in
                                ("out_recall_at_200", "out_recall_at_100", "in_recall_at_200", "all_recall_at_200")},
        "top10_mixes_by_out_recall_at_200": {k: summary[k] for k in top_mixes},
        "oracle_out_recall_at_200": oracle, "oracle_without_llm_actions": oracle_no_llm,
        "exposure_diagnosis_f_star": {"out_pairs": pairs, "in_top100": in_100, "in_101_200": in_200 - in_100,
                                      "absent_top200": pairs - in_200, "absent_share": (pairs - in_200) / pairs,
                                      "observed_out_recall_at_100": summary[f_star]["out_recall_at_100"],
                                      "reordering_ceiling_out_recall_at_100": ceiling},
        "unique_out_positives": {"by_r_actions": len(found_r), "by_q_actions": len(found_q), "q_only": len(q_only),
                                 "union": len(union)},
        "headroom_gate": gate,
        "amendment_1_selection_inflation": selection_inflation,
        "amendment_1_crossfit": crossfit,
        "amendment_1_decisions": decisions,
        "inputs_sha256": {name: hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()
                          for name in ("r1", "r2", "q1_dense", "q1_bm25", "q2", "q3", "split")},
        "merge_order": list(ACTIONS), "budget": POOL_DEPTH,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.private_output.write_text(json.dumps({"per_query_out_recall_at_200": per_query}, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("f_star", "m_star", "oracle_out_recall_at_200", "headroom_gate",
                                             "unique_out_positives", "empty_action_lists", "amendment_1_selection_inflation",
                                             "amendment_1_crossfit", "amendment_1_decisions")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
