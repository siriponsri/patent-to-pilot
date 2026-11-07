"""Time-machine feasibility probe on the DAPFAM dev split (pre-declared; runs once).

Plan: docs/healthtech/research/TIME_MACHINE_DEV_PROBE_PLAN_20261107_EN.md.
Population: dev A61 queries with OUT positives whose earliest claim year is >= GAP years older than the query.
Every ranking is time-filtered (candidates newer than the query year are dropped) before truncation.
Arms: U = brief P over all patents, X = brief P other-fields lane, M = U[:10] + X; R2 / R2x are leakage references.
Reads only dev queries; the test split is never scored. Writes aggregates; demo case IDs go to a private file.
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
DATA = ROOT / "methodology/datasets/research-only-nc"


def year(value) -> int | None:
    text = str(value or "")[:4]
    return int(text) if text.isdigit() else None


def time_filter(families: list[str], years: dict[str, int | None], cutoff: int | None) -> tuple[list[str], int]:
    """Drop candidates newer than the cutoff year; unknown years are kept and counted."""
    if cutoff is None:
        return list(families), 0
    kept, unknown = [], 0
    for f in families:
        y = years.get(f)
        if y is None:
            unknown += 1
            kept.append(f)
        elif y <= cutoff:
            kept.append(f)
    return kept, unknown


def mixed(u: list[str], x: list[str], k: int = 20) -> list[str]:
    return list(dict.fromkeys(u[: k // 2] + x))[:k]


def hit(pool: list[str], gold: set[str], k: int) -> float:
    return float(bool(set(pool[:k]) & gold))


def recall(pool: list[str], gold: set[str], k: int) -> float:
    return len(set(pool[:k]) & gold) / len(gold)


def decide(n: int, x_hit: float, u_hit: float, ci_low: float) -> str:
    if ci_low > 0 and n >= 20 and x_hit >= 0.25 and x_hit >= 2 * u_hit:
        return "GO_SHOCK"
    return "GO_DESCRIPTIVE" if ci_low > 0 else "NO_GO"


def _rankings(path: Path) -> dict[str, list[str]]:
    return {r["query_id"]: [str(f) for f in r["families"]]
            for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def main() -> int:
    import pyarrow.parquet as pq

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--rankings-dir", type=Path, required=True)
    parser.add_argument("--r2", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases-output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.cases_output.exists():
        raise SystemExit("output exists: the probe runs once")

    dev = {q for q, s in json.loads(args.split.read_text(encoding="utf-8"))["assignment"].items() if s == "dev"}
    cols = ["earliest_claim_year", "classifications_ipcr_list_first_three_chars_list"]
    queries = {r["query_id"]: r for r in pq.read_table(DATA / "queries.parquet", columns=["query_id", *cols]).to_pylist()
               if r["query_id"] in dev}
    corpus = {str(r["relevant_id"]): r for r in pq.read_table(DATA / "corpus.parquet", columns=["relevant_id", *cols]).to_pylist()}
    years = {f: year(r["earliest_claim_year"]) for f, r in corpus.items()}
    out: dict[str, set[str]] = {}
    for r in pq.read_table(DATA / "qrels_all.parquet").to_pylist():
        if r["query_id"] in dev and r["domain_rel"] == "OUT" and float(r["relevance_score"] or 0) > 0:
            out.setdefault(r["query_id"], set()).add(str(r["relevant_id"]))
    arms = {"U": _rankings(args.rankings_dir / "rankings-d-P-dev.jsonl"),
            "X": _rankings(args.rankings_dir / "rankings-x-P-dev.jsonl"),
            "R2": _rankings(args.r2), "R2x": _rankings(args.rankings_dir / "rankings-x-R2-dev.jsonl")}

    def population(a61: bool, gap: int) -> dict[str, set[str]]:
        pop = {}
        for q, r in queries.items():
            qy = year(r["earliest_claim_year"])
            if qy is None or (a61 and "A61" not in (r["classifications_ipcr_list_first_three_chars_list"] or [])):
                continue
            gold = {t for t in out.get(q, ()) if years.get(t) is not None and qy - years[t] >= gap}
            if gold:
                pop[q] = gold
        return pop

    def evaluate(pop: dict[str, set[str]], cases: list | None = None) -> dict:
        per = {name: {"hit20": {}, "recall20": {}, "hit100": {}} for name in ("U", "X", "M", "R2", "R2x")}
        unknown, hit_gaps, hit_sections = 0, [], {}
        for q, gold in pop.items():
            cutoff = year(queries[q]["earliest_claim_year"])
            pools = {}
            for name, ranking in arms.items():
                pools[name], u = time_filter(ranking.get(q, []), years, cutoff)
                unknown += u
            pools["M"] = mixed(pools["U"], pools["X"])
            for name, pool in pools.items():
                per[name]["hit20"][q] = hit(pool, gold, 20)
                per[name]["recall20"][q] = recall(pool, gold, 20)
                per[name]["hit100"][q] = hit(pool, gold, 100)
            found = set(pools["X"][:20]) & gold
            for t in found:
                hit_gaps.append(cutoff - years[t])
                for s in {c[:1] for c in (corpus[t]["classifications_ipcr_list_first_three_chars_list"] or [])}:
                    hit_sections[s] = hit_sections.get(s, 0) + 1
            if cases is not None and found and not set(pools["U"][:20]) & gold:
                cases.append({"query_id": q, "query_year": cutoff, "targets_found_by_X": sorted(found),
                              "x_ranks": [pools["X"].index(t) + 1 for t in sorted(found)]})
        ident = {q: q for q in pop}
        means = {name: {m: round(sum(v.values()) / len(v), 4) for m, v in metrics.items()} for name, metrics in per.items()}
        contrast = paired_cluster_bootstrap(per["X"]["hit20"], per["U"]["hit20"], ident, resamples=RESAMPLES, seed=SEED)
        m_contrast = paired_cluster_bootstrap(per["M"]["hit20"], per["U"]["hit20"], ident, resamples=RESAMPLES, seed=SEED)
        return {"queries": len(pop), "pairs": sum(len(g) for g in pop.values()), "means": means,
                "x_minus_u_hit20": contrast, "m_minus_u_hit20": m_contrast,
                "x_hit_gap_years": {"median": statistics.median(hit_gaps), "min": min(hit_gaps), "max": max(hit_gaps)}
                if hit_gaps else None, "x_hit_ipc_sections": dict(sorted(hit_sections.items())),
                "unknown_year_candidates_kept": unknown}

    cases: list = []
    primary = evaluate(population(True, 5), cases)
    result = {
        "format": "ptp-time-machine-dev-probe-v1", "split": "dev", "seed": SEED, "resamples": RESAMPLES,
        "inputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                          [args.split, args.rankings_dir / "rankings-d-P-dev.jsonl", args.rankings_dir / "rankings-x-P-dev.jsonl",
                           args.r2, args.rankings_dir / "rankings-x-R2-dev.jsonl"]},
        "primary_a61_gap5": primary,
        "secondary": {"a61_gap1": evaluate(population(True, 1)), "a61_gap10": evaluate(population(True, 10)),
                      "all_sections_gap5": evaluate(population(False, 5))},
        "decision": decide(primary["queries"], primary["means"]["X"]["hit20"], primary["means"]["U"]["hit20"],
                           primary["x_minus_u_hit20"]["ci95_low"]),
        "demo_cases_private": len(cases),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.cases_output.write_text("".join(json.dumps(c) + "\n" for c in cases), encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "n": primary["queries"], "means_hit20":
                      {k: v["hit20"] for k, v in primary["means"].items()}, "x_minus_u": primary["x_minus_u_hit20"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
