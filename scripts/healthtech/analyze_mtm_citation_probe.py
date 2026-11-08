"""MTM dev phase 3b (methods log): citation-reuse gating probe. CPU only, dev labels only, aggregates only.

Edges come from tm06 (citing family, citing grant date, cited family): examiner (SEA) citations by US device grants
granted 2001-2016. An edge is visible for query q if citing_grant <= T(q) (the query's priority date) and the citing
family is neither the query's own family nor any benchmark query family (dev or test; only their family ids are read,
never test targets). Measures:
  (i)   reach: share of dev queries with >= 1 target cited by a visible edge (upper bound of citation chasing);
  (ii)  co-citation inter-connection: among dev queries with >= 2 targets, share with a target pair co-cited by one
        visible citer;
  (iii) popularity null: lane-X main-view corpus families ranked by their number of visible citing families (ties by
        family id, no query text); hit@20/100/200;
  (iv)  outside-corpus share: distinct cited families (non-benchmark citers) not in the MTM corpus.
The go/no-go rule for 3c is applied and recorded. Refuses to overwrite.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
GATE_REACH, GATE_X_HIT200 = 0.488, 0.388


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_edges(path: Path, excluded: set[str]) -> dict[str, list[tuple[int, str]]]:
    """cited family -> sorted [(citing grant, citing family)] for citers outside `excluded`."""
    by_cited: dict[str, set[tuple[int, str]]] = defaultdict(set)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["citing_family"] not in excluded:
                by_cited[row["cited_family"]].add((int(row["citing_grant"]), row["citing_family"]))
    return {k: sorted(v) for k, v in by_cited.items()}


def visible_citers(edges: list[tuple[int, str]], cutoff: int, own_family: str) -> set[str]:
    end = bisect.bisect_right(edges, (cutoff, "￿"))
    return {f for _, f in edges[:end] if f != own_family}


def reach_and_cocitation(queries: list[dict], by_cited) -> dict:
    reached, multi, cocited = 0, 0, 0
    for q in queries:
        citers = [visible_citers(by_cited.get(t, []), q["priority"], q["family_id"]) for t in q["targets"]]
        reached += any(citers)
        if len(citers) >= 2:
            multi += 1
            cocited += any(citers[i] & citers[j] for i in range(len(citers)) for j in range(i + 1, len(citers)))
    return {"queries": len(queries), "reach": round(reached / len(queries), 4), "multi_target_queries": multi,
            "cocitation_interconnection": round(cocited / multi, 4) if multi else None}


def gate(reach: float, null_hit200: float) -> dict:
    ok = reach >= GATE_REACH and null_hit200 < reach / 2
    return {"rule": f"reach >= {GATE_REACH} and popularity-null hit@200 < reach/2", "reach": reach,
            "popularity_null_hit200": null_hit200, "decision": "GO" if ok else "NO_GO"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries-meta", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists: refusing to overwrite")
    import numpy as np

    hybrid = _load("run_mtm_hybrid")
    dense_pool = hybrid._load("run_mtm_dense_pool")
    meta_rows = [json.loads(line) for line in args.queries_meta.read_text(encoding="utf-8").splitlines() if line.strip()]
    benchmark_families = {m["family_id"] for m in meta_rows}  # dev and test query ids only
    dev = [m for m in meta_rows if m["split"] == "dev"]
    del meta_rows
    by_cited = read_edges(args.edges, benchmark_families)
    result = {"format": "ptp-mtm-citation-probe-v1", "split": "dev",
              "excluded_citers": "query's own family and all benchmark query families"}
    result["reach"] = reach_and_cocitation(dev, by_cited)
    corpus_ids, visible_from, c3s = [], [], []
    with args.corpus.open(encoding="utf-8") as handle:
        for line in handle:
            r = json.loads(line)
            corpus_ids.append(r["id"])
            visible_from.append(r["visible_from"])
            c3s.append(r["c3"])
    position = {f: i for i, f in enumerate(corpus_ids)}
    cited_all = set(by_cited)
    result["outside_corpus"] = {"distinct_cited_families": len(cited_all),
                                "in_corpus": sum(f in position for f in cited_all),
                                "outside_share": round(1 - sum(f in position for f in cited_all) / max(len(cited_all), 1), 4)}
    id_rank = np.empty(len(corpus_ids), dtype=np.int64)
    id_rank[np.argsort(np.asarray(corpus_ids, dtype=object), kind="stable")] = np.arange(len(corpus_ids))
    members: dict[str, list[int]] = defaultdict(list)
    for i, codes in enumerate(c3s):
        for code in codes:
            members[code].append(i)
    visible_from = np.asarray(visible_from, dtype=np.int64)
    view_all = np.ones(len(corpus_ids), dtype=bool)
    events = sorted((g, position[c]) for c, lst in by_cited.items() if c in position for g, _ in
                    {(g, f) for g, f in lst})
    counts = np.zeros(len(corpus_ids), dtype=np.float64)
    hits = {20: 0, 100: 0, 200: 0}
    e = 0
    for q in sorted(dev, key=lambda m: m["priority"]):
        while e < len(events) and events[e][0] <= q["priority"]:
            counts[events[e][1]] += 1
            e += 1
        shared = sorted({i for code in q["c3"] for i in members.get(code, ())})
        keep = dense_pool.keep_mask(visible_from, q["priority"], position.get(q["family_id"]), view_all, shared, "X")
        order = hybrid.topk(np.where(keep, counts, -np.inf), 200, id_rank)
        gold = {position[t] for t in q["targets"] if t in position}
        for k in hits:
            hits[k] += bool(gold & set(order[:k].tolist()))
    result["popularity_null"] = {k_name: round(v / len(dev), 4) for k_name, v in
                                 (("hit20", hits[20]), ("hit100", hits[100]), ("hit200", hits[200]))}
    result["gate"] = gate(result["reach"]["reach"], result["popularity_null"]["hit200"])
    result["inputs_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (args.edges, args.queries_meta)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
