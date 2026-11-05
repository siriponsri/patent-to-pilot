"""Solution-scout feasibility on dev: score every arm and the pre-declared pools; apply the stop rule.

Arms per brief type b (T title, P problem brief), each a Top-200 family list:
  D dense(brief)  X cross-domain lane(brief)  B BM25(brief)
  FD / FX function text, plain / lane       SD / SX solution sketch, plain / lane
Pools (200 families): base = D; lane = D[:100] then X; scout = D[:100] then FX and SX round-robin;
llm_no_lane = D[:100] then FD and SD round-robin.
Primary comparison (plan §4): scout vs base and scout vs lane on the problem brief P.
Test queries are never read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import POOL_DEPTH, lane_merge, positive_relations  # noqa: E402
from patent_to_pilot.evaluation.par4pc_study import paired_cluster_bootstrap  # noqa: E402

BRIEFS = ("P", "T")
KEEP = 100
MIN_GAIN = 0.02
SEED = 20261105


def _load(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    return {r["query_id"]: r["families"][:POOL_DEPTH]
            for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def _recall(pool: list[str], relevant: set[str], k: int = POOL_DEPTH) -> float:
    return len(set(pool[:k]) & relevant) / len(relevant)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rankings-dir", type=Path, required=True, help="rankings-<arm>-<b>-dev.jsonl files")
    parser.add_argument("--r2", type=Path, required=True, help="full-patent dense rankings (reference only)")
    parser.add_argument("--qrels", type=Path, default=ROOT / "methodology/datasets/research-only-nc/qrels_all.parquet")
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--masked-r2", type=Path,
                        help="post-hoc, descriptive only: full-patent dense rankings under the same IPC3 mask")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import pyarrow.parquet as pq

    split = json.loads(args.split.read_text(encoding="utf-8"))["assignment"]
    dev = sorted(q for q, s in split.items() if s == "dev")
    positives = positive_relations(pq.read_table(args.qrels).to_pylist())
    out_rel = {q: positives.get(q, {}).get("OUT", set()) for q in dev}
    in_rel = {q: positives.get(q, {}).get("IN", set()) for q in dev}
    out_q = [q for q in dev if out_rel[q]]
    in_q = [q for q in dev if in_rel[q]]
    ident = {q: q for q in out_q}
    r2 = _load(args.r2)

    def metrics(pools: dict[str, list[str]]) -> dict:
        return {"out_recall_at_200": sum(_recall(pools.get(q, []), out_rel[q]) for q in out_q) / len(out_q),
                "out_recall_at_100": sum(_recall(pools.get(q, []), out_rel[q], 100) for q in out_q) / len(out_q),
                "out_hit_at_200": sum(bool(set(pools.get(q, [])) & out_rel[q]) for q in out_q) / len(out_q),
                "in_recall_at_200": sum(_recall(pools.get(q, []), in_rel[q]) for q in in_q) / len(in_q)}

    def per_query(pools: dict[str, list[str]]) -> dict[str, float]:
        return {q: _recall(pools.get(q, []), out_rel[q]) for q in out_q}

    result = {"format": "ptp-solution-scout-feasibility-dev-v1", "split": "dev", "test_split_read": False,
              "queries": {"dev": len(dev), "out_eligible": len(out_q), "in_eligible": len(in_q)},
              "reference_full_patent_dense": metrics(r2), "briefs": {}, "inputs_sha256": {}}
    for b in BRIEFS:
        arms = {arm: _load(args.rankings_dir / f"rankings-{name}-{b}-dev.jsonl")
                for arm, name in (("D", "d"), ("X", "x"), ("B", "bm25"), ("FD", "f"), ("FX", "fx"),
                                  ("SD", "s"), ("SX", "sx"))}
        for arm, name in (("D", "d"), ("X", "x"), ("B", "bm25"), ("FD", "f"), ("FX", "fx"), ("SD", "s"), ("SX", "sx")):
            path = args.rankings_dir / f"rankings-{name}-{b}-dev.jsonl"
            if path.exists():
                result["inputs_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        pools = {
            "base": arms["D"],
            "lane": {q: lane_merge(arms["D"].get(q, []), [arms["X"].get(q, [])], KEEP) for q in dev},
            "scout": {q: lane_merge(arms["D"].get(q, []), [arms["FX"].get(q, []), arms["SX"].get(q, [])], KEEP)
                      for q in dev},
            "llm_no_lane": {q: lane_merge(arms["D"].get(q, []), [arms["FD"].get(q, []), arms["SD"].get(q, [])], KEEP)
                            for q in dev},
        }
        rows = {name: per_query(p) for name, p in pools.items()}
        result["briefs"][b] = {
            "single_arms": {arm: metrics(lists) for arm, lists in arms.items()},
            "empty_arm_lists": {arm: sum(1 for q in out_q if not lists.get(q)) for arm, lists in arms.items()},
            "pools": {name: metrics(p) for name, p in pools.items()},
            "scout_minus_base": paired_cluster_bootstrap(rows["scout"], rows["base"], ident, resamples=5000, seed=SEED),
            "scout_minus_lane": paired_cluster_bootstrap(rows["scout"], rows["lane"], ident, resamples=5000, seed=SEED),
            "lane_minus_base": paired_cluster_bootstrap(rows["lane"], rows["base"], ident, resamples=5000, seed=SEED),
            "scout_minus_llm_no_lane": paired_cluster_bootstrap(rows["scout"], rows["llm_no_lane"], ident,
                                                                resamples=5000, seed=SEED),
        }
    p = result["briefs"]["P"]
    beats_base = p["scout_minus_base"]["delta"] >= MIN_GAIN and p["scout_minus_base"]["ci95_low"] > 0
    beats_lane = p["scout_minus_lane"]["ci95_low"] > 0
    lane_helps = p["lane_minus_base"]["ci95_low"] > 0
    result["stop_rule"] = {
        "min_gain": MIN_GAIN,
        "scout_beats_base": beats_base, "scout_beats_lane": beats_lane, "lane_beats_base": lane_helps,
        "status": "PASS" if beats_base and beats_lane else ("PARTIAL_LANE_ONLY" if lane_helps else "FAIL"),
    }
    if args.masked_r2:
        # Added after the stop rule was applied. The lane mask equals the strict-OUT definition (no shared IPC3),
        # so this reference shows how much of the lane gain comes from the candidate set rather than the brief.
        masked = _load(args.masked_r2)
        result["inputs_sha256"][args.masked_r2.name] = hashlib.sha256(args.masked_r2.read_bytes()).hexdigest()
        r2_lane = {q: lane_merge(r2.get(q, []), [masked.get(q, [])], KEEP) for q in dev}
        x_p = _load(args.rankings_dir / "rankings-x-P-dev.jsonl")
        result["post_hoc_descriptive"] = {
            "note": "not pre-declared; no decision attached",
            "full_patent_masked": metrics(masked),
            "full_patent_lane_pool": metrics(r2_lane),
            "brief_P_masked_minus_full_patent_masked": paired_cluster_bootstrap(
                per_query(x_p), per_query(masked), ident, resamples=5000, seed=SEED),
            "full_patent_masked_minus_full_patent": paired_cluster_bootstrap(
                per_query(masked), per_query(r2), ident, resamples=5000, seed=SEED),
        }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"stop_rule": result["stop_rule"], "reference": result["reference_full_patent_dense"],
                      **{b: {"pools": result["briefs"][b]["pools"],
                             "single": {a: round(m["out_recall_at_200"], 4)
                                        for a, m in result["briefs"][b]["single_arms"].items()}}
                         for b in BRIEFS}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
