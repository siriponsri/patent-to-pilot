"""MTM analysis: older cross-field examiner targets in the first k results, per corpus view, arm and query view.

Arms: U (all patents), X (other-fields lane), M (U[:10] then X, deduplicated, to 20). A query without a ranking
(for example a failed P brief) scores 0. Measures: hit@20 (primary), recall@20, hit@100, MRR@100, median priority
gap (years) of U/X/M hits within 20. Contrasts X-U and M-U on hit@20: paired query bootstrap, 5,000 resamples,
seed 20261107. Writes aggregates only and refuses to overwrite.
Rules: docs/healthtech/research/MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.par4pc_study import paired_cluster_bootstrap  # noqa: E402

SEED = 20261107
RESAMPLES = 5000


def mixed(u: list[str], x: list[str], k: int = 20) -> list[str]:
    return list(dict.fromkeys(u[: k // 2] + x))[:k]


def metrics(pool: list[str], gold: set[str]) -> dict[str, float]:
    first = next((i for i, f in enumerate(pool[:100], 1) if f in gold), None)
    return {"hit20": float(bool(set(pool[:20]) & gold)), "recall20": len(set(pool[:20]) & gold) / len(gold),
            "hit100": float(bool(set(pool[:100]) & gold)), "mrr100": 1.0 / first if first else 0.0}


def evaluate(meta: list[dict], arms: dict[str, dict[str, list[str]]], priority: dict[str, int]) -> dict:
    per = {a: {} for a in ("U", "X", "M")}
    gaps = {a: [] for a in per}
    missing = {a: 0 for a in ("U", "X")}
    for q in meta:
        gold = set(q["targets"])
        pools = {}
        for a in ("U", "X"):
            if q["id"] not in arms[a]:
                missing[a] += 1
            pools[a] = arms[a].get(q["id"], [])
        pools["M"] = mixed(pools["U"], pools["X"])
        for a, pool in pools.items():
            per[a][q["id"]] = metrics(pool, gold)
            gaps[a] += [(q["priority"] - priority[t]) / 10000 // 1 for t in set(pool[:20]) & gold]
    ident = {q["id"]: q["id"] for q in meta}
    out = {"queries": len(meta), "pairs": sum(len(q["targets"]) for q in meta), "missing_rankings": missing,
           "means": {a: {m: round(sum(r[m] for r in rows.values()) / len(rows), 4) for m in ("hit20", "recall20", "hit100", "mrr100")}
                     for a, rows in per.items()},
           "hit_gap_years_median": {a: statistics.median(g) if g else None for a, g in gaps.items()}}
    for a in ("X", "M"):
        out[f"{a}_minus_U_hit20"] = paired_cluster_bootstrap({q: r["hit20"] for q, r in per[a].items()},
                                                             {q: r["hit20"] for q, r in per["U"].items()},
                                                             ident, resamples=RESAMPLES, seed=SEED)
    return out


def _rankings(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    return {r["query_id"]: r["families"] for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries-meta", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--rankings-dir", type=Path, required=True)
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--query-views", default="P,T,A")
    parser.add_argument("--corpus-views", default="main,small,matched,uniform")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists: refusing to overwrite")
    meta = [m for m in map(json.loads, args.queries_meta.read_text(encoding="utf-8").splitlines()) if m and m["split"] == args.split]
    priority = {}
    with args.corpus.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            priority[row["id"]] = row["priority"]
    result = {"format": "ptp-mtm-analysis-v1", "split": args.split, "seed": SEED, "resamples": RESAMPLES, "results": {}}
    hashes = {}
    for qv in args.query_views.split(","):
        for cv in args.corpus_views.split(","):
            paths = {a: args.rankings_dir / f"rankings-{cv}-{a}-{qv}-{args.split}.jsonl" for a in ("U", "X")}
            if not all(p.exists() for p in paths.values()):
                continue
            hashes.update({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()})
            result["results"][f"{qv}|{cv}"] = evaluate(meta, {a: _rankings(p) for a, p in paths.items()}, priority)
    result["inputs_sha256"] = {args.queries_meta.name: hashlib.sha256(args.queries_meta.read_bytes()).hexdigest(), **hashes}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {a: v["means"][a]["hit20"] for a in ("U", "X", "M")} for k, v in result["results"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
