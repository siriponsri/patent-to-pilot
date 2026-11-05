"""Evaluate a DAPFAM Top-200 candidate pool with owner-local qrels.

Also compares the strict-OUT Recall@200 with the owner's earlier unpublished internal run of the same
dense baseline. That is an internal pipeline check, not a reported result.

Writes aggregate metrics only. Unlisted query-target pairs are unjudged and never counted as negatives.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import macro_recall, positive_relations  # noqa: E402

# Owner's earlier unpublished internal run of the same dense baseline (private records).
EARLIER_INTERNAL_RUN = {
    "all": {"recall_at_100": 0.438965, "recall_at_200": 0.546832, "queries": 1247},
    "IN": {"recall_at_100": 0.528164, "recall_at_200": 0.645077, "queries": 1217},
    "OUT": {"recall_at_100": 0.188450, "recall_at_200": 0.260167, "queries": 905},
}
REPRODUCTION_TOLERANCE = 0.005


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, default=ROOT / "methodology/datasets/research-only-nc/qrels_all.parquet")
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-test", action="store_true",
                        help="report test-split scores (only after the Stage 2 freeze)")
    args = parser.parse_args()
    import pyarrow.parquet as pq

    rankings = {}
    for line in args.rankings.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rankings[row["query_id"]] = row["families"]
    positives = positive_relations(pq.read_table(args.qrels).to_pylist())
    split = json.loads(args.split.read_text(encoding="utf-8"))["assignment"]
    relevant = {
        "all": {q: v["IN"] | v["OUT"] for q, v in positives.items()},
        "IN": {q: v["IN"] for q, v in positives.items()},
        "OUT": {q: v["OUT"] for q, v in positives.items()},
    }
    results: dict = {"populations": {}}
    for name, rel in relevant.items():
        entry = {}
        scopes = [("all_queries", None), ("dev", [q for q in split if split[q] == "dev"])]
        if args.include_test:
            scopes.append(("test", [q for q in split if split[q] == "test"]))
        for scope, queries in scopes:
            r100, n = macro_recall(rankings, rel, 100, queries)
            r200, _ = macro_recall(rankings, rel, 200, queries)
            entry[scope] = {"queries": n, "recall_at_100": round(r100, 6), "recall_at_200": round(r200, 6)}
        ref = EARLIER_INTERNAL_RUN[name]
        entry["earlier_internal_run"] = ref
        entry["delta_vs_earlier_internal_run"] = {k: round(entry["all_queries"][k] - ref[k], 6) for k in ("recall_at_100", "recall_at_200")}
        results["populations"][name] = entry
    out_pairs = sum(len(v) for v in relevant["OUT"].values())
    found_200 = sum(len(set(rankings.get(q, [])[:200]) & v) for q, v in relevant["OUT"].items())
    found_100 = sum(len(set(rankings.get(q, [])[:100]) & v) for q, v in relevant["OUT"].items())
    results["strict_out_pairs"] = {"total": out_pairs, "ranks_1_100": found_100, "ranks_101_200": found_200 - found_100,
                                   "absent_top200": out_pairs - found_200,
                                   "absent_share": round((out_pairs - found_200) / out_pairs, 4),
                                   "earlier_internal_run": {"total": 5193, "ranks_1_100": 796, "ranks_101_200": 332, "absent_top200": 4065}}
    out_delta = abs(results["populations"]["OUT"]["delta_vs_earlier_internal_run"]["recall_at_200"])
    results["consistency_check"] = {
        "tolerance": REPRODUCTION_TOLERANCE,
        "strict_out_abs_delta_recall_at_200": out_delta,
        "status": "PASS" if out_delta <= REPRODUCTION_TOLERANCE else "FAIL",
        "note": "Internal pipeline consistency check on strict-OUT Recall@200; not a reported result.",
    }
    results["inputs"] = {"rankings_sha256": hashlib.sha256(args.rankings.read_bytes()).hexdigest(),
                         "queries_ranked": len(rankings)}
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: results[k] for k in ("consistency_check", "strict_out_pairs")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
