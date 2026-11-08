"""MTM dev analysis of methods-log entries against the frozen lane-X baseline (dev only; refuses the test split).

For each (query view, corpus view) and method, it reports hit@20, recall@20, hit@100 and MRR@100, plus two shares:
- new-gold@100: the baseline X top 100 had no target, but the method's top 100 has one;
- lost-gold@100: the reverse.
Phase 3 adds hit@200 and new/lost-gold@200. It also gives method - X on hit@20 by paired query bootstrap (5,000 resamples, seed 20261107).
For a method family sharing --cv-prefix (e.g. hyb-0.5 ... hyb-0.9), it adds 4-fold cross-validation. A query's fold
is int(sha256(query_id)[:8], 16) % 4. Each fold uses the variant with the best mean hit@20 on the other folds; a tie
goes to the larger suffix value, the one closer to the baseline, then to the variant listed first in --methods.
--cv-prefix may list several groups (phase 2: e.g. llm,cef,fch); the suffix is the number after the last '-'. It reports the out-of-fold hit@20 and its contrast
with X, and the full-dev choice under the same rule. Writes aggregates only and refuses to overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.par4pc_study import paired_cluster_bootstrap  # noqa: E402

_spec = importlib.util.spec_from_file_location("analyze_mtm", Path(__file__).with_name("analyze_mtm.py"))
analyze_mtm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(analyze_mtm)

SEED, RESAMPLES, FOLDS = analyze_mtm.SEED, analyze_mtm.RESAMPLES, 4
MEASURES = ("hit20", "recall20", "hit100", "mrr100", "hit200")


def fold_of(query_id: str) -> int:
    return int(hashlib.sha256(query_id.encode("utf-8")).hexdigest()[:8], 16) % FOLDS


def per_query(meta: list[dict], ranks: dict[str, list[str]]) -> dict[str, dict[str, float]]:
    out = {}
    for q in meta:
        pool, gold = ranks.get(q["id"], []), set(q["targets"])
        out[q["id"]] = {**analyze_mtm.metrics(pool, gold), "hit200": float(bool(set(pool[:200]) & gold))}
    return out


def compare(rows: dict[str, dict[str, float]], base: dict[str, dict[str, float]]) -> dict:
    n = len(rows)
    ident = {q: q for q in rows}
    return {"means": {m: round(sum(r[m] for r in rows.values()) / n, 4) for m in MEASURES},
            "new_gold100": round(sum(base[q]["hit100"] == 0 and r["hit100"] == 1 for q, r in rows.items()) / n, 4),
            "lost_gold100": round(sum(base[q]["hit100"] == 1 and r["hit100"] == 0 for q, r in rows.items()) / n, 4),
            "new_gold200": round(sum(base[q]["hit200"] == 0 and r["hit200"] == 1 for q, r in rows.items()) / n, 4),
            "lost_gold200": round(sum(base[q]["hit200"] == 1 and r["hit200"] == 0 for q, r in rows.items()) / n, 4),
            "minus_X_hit20": paired_cluster_bootstrap({q: r["hit20"] for q, r in rows.items()},
                                                      {q: r["hit20"] for q, r in base.items()}, ident,
                                                      resamples=RESAMPLES, seed=SEED)}


def _suffix(name: str, prefix: str) -> float:
    """The lambda after the last '-' (hyb-0.9 -> 0.9; llmC-0.9 -> 0.9 under the joint prefix 'llm')."""
    return float(name.rsplit("-", 1)[1])


def choose(variants: dict[str, dict[str, dict[str, float]]], queries: list[str], prefix: str) -> str:
    def key(name):
        return (sum(variants[name][q]["hit20"] for q in queries), _suffix(name, prefix))
    return max(variants, key=key)


def cross_validate(variants: dict[str, dict[str, dict[str, float]]], base: dict[str, dict[str, float]], prefix: str) -> dict:
    queries = sorted(base)
    folds = {q: fold_of(q) for q in queries}
    chosen, oof = {}, {}
    for f in range(FOLDS):
        train = [q for q in queries if folds[q] != f]
        name = choose(variants, train, prefix)
        chosen[str(f)] = name
        oof.update({q: variants[name][q] for q in queries if folds[q] == f})
    result = compare(oof, base)
    result["chosen_per_fold"] = chosen
    result["fold_sizes"] = {str(f): sum(v == f for v in folds.values()) for f in range(FOLDS)}
    result["full_dev_choice"] = choose(variants, queries, prefix)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries-meta", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--methods-dir", type=Path, required=True, help="<dir>/<method>/rankings-<cv>-X-<qv>-dev.jsonl")
    parser.add_argument("--methods", required=True)
    parser.add_argument("--split", choices=("dev",), default="dev")
    parser.add_argument("--query-views", default="P,T")
    parser.add_argument("--corpus-views", default="main,small,matched,uniform")
    parser.add_argument("--cv-prefix", default="", help="comma list; each prefix is one CV group")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists: refusing to overwrite")
    meta = [m for m in map(json.loads, args.queries_meta.read_text(encoding="utf-8").splitlines()) if m and m["split"] == "dev"]
    methods = args.methods.split(",")
    result = {"format": "ptp-mtm-methods-v1", "split": "dev", "seed": SEED, "resamples": RESAMPLES, "results": {}}
    hashes = {}
    for qv in args.query_views.split(","):
        for cv in args.corpus_views.split(","):
            base_path = args.baseline_dir / f"rankings-{cv}-X-{qv}-dev.jsonl"
            paths = {m: args.methods_dir / m / f"rankings-{cv}-X-{qv}-dev.jsonl" for m in methods}
            paths = {m: p for m, p in paths.items() if p.exists()}
            if not base_path.exists() or not paths:
                continue
            hashes[base_path.name] = hashlib.sha256(base_path.read_bytes()).hexdigest()
            hashes.update({f"{m}/{p.name}": hashlib.sha256(p.read_bytes()).hexdigest() for m, p in paths.items()})
            base = per_query(meta, analyze_mtm._rankings(base_path))
            rows = {m: per_query(meta, analyze_mtm._rankings(p)) for m, p in paths.items()}
            cell = {"queries": len(meta), "baseline_X": {m: round(sum(r[m] for r in base.values()) / len(base), 4) for m in MEASURES},
                    "methods": {m: compare(r, base) for m, r in rows.items()}}
            prefixes = [x for x in args.cv_prefix.split(",") if x]
            groups = {}
            for prefix in prefixes:
                family = {m: r for m, r in rows.items() if m.startswith(prefix) and _suffix(m, prefix) < 1.0}
                if family:
                    groups[prefix] = cross_validate(family, base, prefix)
            if len(prefixes) == 1 and groups:
                cell["cv"] = groups[prefixes[0]]
            elif groups:
                cell["cv_groups"] = groups
            result["results"][f"{qv}|{cv}"] = cell
    result["inputs_sha256"] = {args.queries_meta.name: hashlib.sha256(args.queries_meta.read_bytes()).hexdigest(), **hashes}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {"X": v["baseline_X"]["hit20"], **{m: c["means"]["hit20"] for m, c in v["methods"].items()},
                          **({"cv_oof": v["cv"]["means"]["hit20"]} if "cv" in v else {}),
                          **{f"cv_oof_{g}": c["means"]["hit20"] for g, c in v.get("cv_groups", {}).items()}}
                      for k, v in result["results"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
