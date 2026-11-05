"""Dev-only aggregate map of where known cross-domain (strict-OUT) prior art is lost.

For every dev (query, OUT-positive) pair, records the query's first-IPC section, the target family's
first-IPC section and where the target sits in the primary action's Top-200 (Top-100, 101-200 or
absent). Each further action adds how many pairs it reaches in its own Top-200, and how many of the
pairs the primary action misses. IN pairs are counted the same way for contrast.
Writes aggregate counts only; no query or family identifiers. Test queries are never read.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import POOL_DEPTH, first_ipc_section, positive_relations  # noqa: E402

SECTIONS = tuple("ABCDEFGH")
RANK_BUCKETS = ((1, 10), (11, 50), (51, 100), (101, 200))


def _load(path: Path) -> dict[str, list[str]]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["query_id"]] = row["families"][:POOL_DEPTH]
    return rows


def _position(pool: list[str], target: str) -> str:
    if target in pool[:100]:
        return "top100"
    return "r101_200" if target in pool else "absent"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rankings", nargs="+", required=True, help="NAME=PATH Top-200 rankings, dev queries")
    parser.add_argument("--primary", default="R2")
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, default=ROOT / "methodology/datasets/research-only-nc/qrels_all.parquet")
    parser.add_argument("--corpus-parquet", type=Path, default=ROOT / "methodology/datasets/research-only-nc/corpus.parquet")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import pyarrow.parquet as pq

    paths = dict(item.split("=", 1) for item in args.rankings)
    actions = {name: _load(Path(path)) for name, path in paths.items()}
    if args.primary not in actions:
        raise SystemExit(f"primary action {args.primary!r} not among --rankings")
    split_doc = json.loads(args.split.read_text(encoding="utf-8"))
    dev = sorted(q for q, s in split_doc["assignment"].items() if s == "dev")
    query_section = split_doc["first_ipc_section"]
    corpus = pq.read_table(args.corpus_parquet,
                           columns=["relevant_id", "classifications_ipcr_list_first_three_chars_list"]).to_pylist()
    target_section = {str(r["relevant_id"]): first_ipc_section(r["classifications_ipcr_list_first_three_chars_list"])
                      for r in corpus}
    positives = positive_relations(pq.read_table(args.qrels).to_pylist())

    cells: dict[tuple[str, str], Counter] = defaultdict(Counter)
    in_position: Counter = Counter()
    rank_hist: Counter = Counter()
    per_query_found: list[int] = []
    query_macro: dict[str, list[float]] = defaultdict(list)
    component = split_doc["component"]
    largest, largest_size = Counter(component[q] for q in dev).most_common(1)[0]
    largest_pairs = 0
    for query in dev:
        primary = actions[args.primary].get(query, [])
        for target in positives.get(query, {}).get("IN", set()):
            in_position[_position(primary, target)] += 1
        out = positives.get(query, {}).get("OUT", set())
        if not out:
            continue
        per_query_found.append(sum(t in primary for t in out))
        absent_fraction = sum(t not in primary for t in out) / len(out)
        query_macro[query_section.get(query, "?")].append(absent_fraction)
        if component.get(query) == largest:
            largest_pairs += len(out)
        for target in sorted(out):
            cell = cells[(query_section.get(query, "?"), target_section.get(target, "?"))]
            position = _position(primary, target)
            cell["pairs"] += 1
            cell[position] += 1
            if target in primary:
                rank = primary.index(target) + 1
                rank_hist[next(f"{lo}-{hi}" for lo, hi in RANK_BUCKETS if lo <= rank <= hi)] += 1
            any_q = False
            for name, ranking in actions.items():
                if name == args.primary:
                    continue
                pool = ranking.get(query, [])
                if target in pool:
                    cell[f"found_by_{name}"] += 1
                    if position == "absent":
                        cell[f"recovered_by_{name}"] += 1
                        any_q = any_q or name.startswith("Q")
            if any_q:
                cell["recovered_by_any_Q"] += 1

    def total(predicate) -> Counter:
        out = Counter()
        for key, cell in cells.items():
            if predicate(key):
                out.update(cell)
        return out

    def summarize(counter: Counter) -> dict:
        pairs = counter["pairs"]
        row = dict(sorted(counter.items()))
        row["absent_share"] = counter["absent"] / pairs if pairs else None
        return row

    in_pairs = sum(in_position.values())
    result = {
        "format": "ptp-org-adaptive-loss-map-dev-v1", "split": "dev", "test_split_read": False,
        "primary_action": args.primary, "actions": sorted(actions), "depth": POOL_DEPTH,
        "section_rule": "first IPC3 code listed for the family; OUT means the families share no IPC3 code",
        "out_queries": len(per_query_found),
        "out_queries_with_no_positive_in_primary_top200": sum(1 for n in per_query_found if n == 0),
        "out_overall": summarize(total(lambda key: True)),
        "out_query_macro_absent_share": {
            "all": sum(sum(v) for v in query_macro.values()) / sum(len(v) for v in query_macro.values()),
            **{s: {"queries": len(query_macro[s]), "absent_share": sum(query_macro[s]) / len(query_macro[s])}
               for s in SECTIONS if query_macro[s]}},
        "largest_component": {"dev_queries": largest_size, "out_pairs": largest_pairs,
                              "note": "one shared-target component; it dominates pair counts, so query-macro shares are reported too"},
        "in_overall": {**dict(in_position), "pairs": in_pairs, "absent_share": in_position["absent"] / in_pairs},
        "out_same_section": summarize(total(lambda key: key[0] == key[1])),
        "out_cross_section": summarize(total(lambda key: key[0] != key[1])),
        "primary_rank_histogram_of_found_out_pairs": dict(rank_hist),
        "by_query_section": {s: summarize(total(lambda key, s=s: key[0] == s)) for s in SECTIONS},
        "by_target_section": {s: summarize(total(lambda key, s=s: key[1] == s)) for s in SECTIONS},
        "cells": [{"query_section": q, "target_section": t, **summarize(c)} for (q, t), c in sorted(cells.items())],
        "inputs_sha256": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for name, path in paths.items()},
        "split_sha256": hashlib.sha256(args.split.read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("out_queries", "out_queries_with_no_positive_in_primary_top200",
                                             "out_overall", "in_overall", "out_same_section", "out_cross_section",
                                             "primary_rank_histogram_of_found_out_pairs")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
