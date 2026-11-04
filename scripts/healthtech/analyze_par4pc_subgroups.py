"""Exploratory (not preregistered) subgroup and error analysis of frozen PAR4PC test outputs.

Reads private per-row metrics plus label-free row attributes; writes aggregates only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pyarrow.parquet as parquet  # noqa: E402

from patent_to_pilot.evaluation.par4pc_study import app_macro, paired_cluster_bootstrap  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-parquet", type=Path, required=True)
    parser.add_argument("--per-row", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parquet.read_table(args.test_parquet, columns=["application_number", "claim_number", "gold_answers"]).to_pylist()
    attrs = {f"{r['application_number']}:{r['claim_number']}": r for r in rows}
    groups = {k: str(r["application_number"]) for k, r in attrs.items()}
    per_row = json.loads(args.per_row.read_text(encoding="utf-8"))
    rr = {m: {k: v["rr"] for k, v in rows_.items()} for m, rows_ in per_row.items()}
    subsets = {
        "claim_1": lambda r: r["claim_number"] == 1,
        "claim_gt_1": lambda r: r["claim_number"] > 1,
        "single_gold": lambda r: len(r["gold_answers"]) == 1,
        "multi_gold": lambda r: len(r["gold_answers"]) > 1,
    }
    out = {"format": "ptp-wpi-par4pc-exploratory-subgroups-v1", "status": "EXPLORATORY_NOT_PREREGISTERED", "subgroups": {}}
    for name, keep in subsets.items():
        keys = [k for k, r in attrs.items() if keep(r)]
        sub_groups = {k: groups[k] for k in keys}
        entry = {"rows": len(keys), "apps": len(set(sub_groups.values()))}
        for method in ("bm25_full", "patembed_claim", "hybrid", "cascade"):
            entry[f"{method}_app_macro_mrr"] = app_macro({k: rr[method][k] for k in keys}, sub_groups)
        entry["patembed_claim_minus_bm25_full"] = paired_cluster_bootstrap(
            {k: rr["patembed_claim"][k] for k in keys}, {k: rr["bm25_full"][k] for k in keys}, sub_groups, resamples=5000)
        out["subgroups"][name] = entry
    first_hit = lambda m, k: rr[m][k] == 1.0
    out["error_table_top1"] = {
        "both_correct": sum(first_hit("bm25_full", k) and first_hit("patembed_claim", k) for k in attrs),
        "dense_only": sum(not first_hit("bm25_full", k) and first_hit("patembed_claim", k) for k in attrs),
        "bm25_only": sum(first_hit("bm25_full", k) and not first_hit("patembed_claim", k) for k in attrs),
        "both_wrong": sum(not first_hit("bm25_full", k) and not first_hit("patembed_claim", k) for k in attrs),
        "rows": len(attrs),
    }
    args.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1)[:2500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
