"""E1/E2 of the frozen Solution Scout protocol on the DAPFAM test split. Run once; the first output is final.

Reads rankings-{u,o,x}-{P,T,R2}-test.jsonl from --rankings-dir, the split and DAPFAM qrels; writes aggregates only.
Protocol: docs/healthtech/research/SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import POOL_DEPTH, positive_relations  # noqa: E402
from patent_to_pilot.evaluation.scout_frozen import VIEWS, e1_e2  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rankings-dir", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, default=ROOT / "methodology/datasets/research-only-nc/qrels_all.parquet")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import pyarrow.parquet as pq

    if args.output.exists():
        raise SystemExit("output exists: the frozen analysis runs once; write an amendment instead of overwriting")
    split = json.loads(args.split.read_text(encoding="utf-8"))["assignment"]
    test = sorted(q for q, s in split.items() if s == "test")
    positives = positive_relations(pq.read_table(args.qrels).to_pylist())
    out_rel = {q: positives.get(q, {}).get("OUT", set()) for q in test}
    in_rel = {q: positives.get(q, {}).get("IN", set()) for q in test}
    rankings, hashes = {}, {}
    for kind in ("u", "o", "x"):
        for view in VIEWS:
            path = args.rankings_dir / f"rankings-{kind}-{view}-test.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            unknown = [r["query_id"] for r in rows if split.get(r["query_id"]) != "test"]
            if unknown:
                raise SystemExit(f"{path.name} holds non-test queries")
            rankings[f"{kind}-{view}"] = {r["query_id"]: r["families"][:POOL_DEPTH] for r in rows}
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = {"format": "ptp-scout-frozen-test-v1", "split": "test",
              "queries": {"test": len(test), "out_eligible": sum(1 for q in test if out_rel[q]),
                          "in_eligible": sum(1 for q in test if in_rel[q])},
              "rankings_sha256": hashes, **e1_e2(rankings, out_rel, in_rel)}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"queries": result["queries"], "primary": result["primary"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
