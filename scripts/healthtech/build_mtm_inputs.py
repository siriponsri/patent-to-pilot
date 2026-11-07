"""Turn the BigQuery MTM exports (tm03 build, tm04 uniform distractors) into runner inputs (private; no scoring).

Writes to --out-dir:
  corpus.jsonl            {"id": family_id, "title", "abstract", "claims", "priority", "visible_from", "c3", "sets": [...]}
                          visible_from = publication date of the representative member whose text is indexed (tm05);
                          documents without a known publication date are left out and counted
                          sets: target / matched / small / uniform. Corpus views: main = all, small = target+small,
                          matched = target+matched, uniform = target+uniform.
  family-cpc3.jsonl       {"id", "ipc3": c3} for the runner's other-fields lane (3-character CPC = IPC3-equivalent)
  queries-meta.jsonl      {"id", "split", "family_id", "priority", "c3", "targets": [family_id, ...]}  (labels)
  brief-inputs-{split}.jsonl  records for run_qwen_scout_actions.py generate --actions P (title + abstract;
                          the description slot is empty by rule)
  queries-{T,A}-{split}.jsonl  dense query views: T title only, A full abstract (leakage reference)
  receipt.json            counts and sha256 of every input and output
Uniform families already present in tm03 are dropped (deterministic). Time-machine visibility (pre-freeze fix,
7 Nov 2026): a document is searchable for query q only if visible_from <= T(q); a gold target that was not yet
published at T(q) is removed from that query's gold, and a query left without targets is dropped (both counted). Rules:
docs/healthtech/research/MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import DENSE_QUERY_PREFIX  # noqa: E402

csv.field_size_limit(2 ** 31 - 1)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def clean(value: str | None) -> str:
    return " ".join((value or "").split())


def corpus_row(row: dict, sets: list[str], pubdates: dict[str, int]) -> dict:
    return {"id": row["family_id"], "publication_number": row["publication_number"], "title": clean(row["title"]),
            "abstract": clean(row["abstract"]), "claims": clean(row.get("claims_head")),
            "priority": int(row["priority_date"]), "visible_from": pubdates.get(row["publication_number"]),
            "c3": json.loads(row["c3"] or "[]"), "sets": sets}


def build(build_rows, uniform_rows, pubdates: dict[str, int]) -> tuple[list[dict], list[dict], dict]:
    corpus: dict[str, dict] = {}
    queries = []
    for row in build_rows:
        if row["role"] == "query":
            queries.append({"id": row["publication_number"], "split": row["split"], "family_id": row["family_id"],
                            "priority": int(row["priority_date"]), "c3": json.loads(row["c3"] or "[]"),
                            "title": clean(row["title"]), "abstract": clean(row["abstract"]),
                            "targets": sorted(t["t_family"] for t in json.loads(row["targets"] or "[]"))})
        elif row["role"] == "target":
            corpus[row["family_id"]] = corpus_row(row, ["target"], pubdates)
        elif row["role"] == "distractor":
            small = str(row["in_small_corpus"]).lower() == "true"
            corpus[row["family_id"]] = corpus_row(row, ["matched", "small"] if small else ["matched"], pubdates)
    for row in uniform_rows:
        if row["family_id"] not in corpus:
            corpus[row["family_id"]] = corpus_row(row, ["uniform"], pubdates)
    stats = {"no_publication_date": sum(r["visible_from"] is None for r in corpus.values())}
    corpus = {f: r for f, r in corpus.items() if r["visible_from"] is not None}
    kept_queries, dropped_pairs = [], 0
    for q in queries:
        visible = [t for t in q["targets"] if t in corpus and corpus[t]["visible_from"] <= q["priority"]]
        dropped_pairs += len(q["targets"]) - len(visible)
        if visible:
            kept_queries.append({**q, "targets": visible})
    stats.update({"gold_pairs_dropped_not_yet_published": dropped_pairs,
                  "queries_dropped_no_visible_target": len(queries) - len(kept_queries)})
    return sorted(corpus.values(), key=lambda r: r["id"]), sorted(kept_queries, key=lambda q: q["id"]), stats


def _write(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True, help="tm03_mtm_build.csv")
    parser.add_argument("--uniform", type=Path, required=True, help="tm04_uniform_distractors.csv")
    parser.add_argument("--pubdates", type=Path, required=True, help="tm05_us_publication_dates.csv")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if (args.out_dir / "receipt.json").exists():
        raise SystemExit("output exists: refusing to overwrite")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with args.pubdates.open(encoding="utf-8", newline="") as handle:
        pubdates = {r["publication_number"]: int(r["publication_date"]) for r in csv.DictReader(handle)}
    with args.build.open(encoding="utf-8", newline="") as b, args.uniform.open(encoding="utf-8", newline="") as u:
        corpus, queries, stats = build(csv.DictReader(b), csv.DictReader(u), pubdates)
    _write(args.out_dir / "corpus.jsonl", corpus)
    _write(args.out_dir / "family-cpc3.jsonl", ({"id": r["id"], "ipc3": r["c3"]} for r in corpus))
    _write(args.out_dir / "queries-meta.jsonl", ({k: q[k] for k in ("id", "split", "family_id", "priority", "c3", "targets")}
                                                 for q in queries))
    for split in ("dev", "test"):
        part = [q for q in queries if q["split"] == split]
        _write(args.out_dir / f"brief-inputs-{split}.jsonl",
               ({"id": q["id"], "title": q["title"], "abstract": q["abstract"], "description": "", "own_ipc3": q["c3"]}
                for q in part))
        _write(args.out_dir / f"queries-T-{split}.jsonl", ({"id": q["id"], "text": DENSE_QUERY_PREFIX + q["title"]} for q in part))
        _write(args.out_dir / f"queries-A-{split}.jsonl", ({"id": q["id"], "text": DENSE_QUERY_PREFIX + q["abstract"]} for q in part))
    counts = {s: sum(s in r["sets"] for r in corpus) for s in ("target", "matched", "small", "uniform")}
    receipt = {"inputs": {p.name: _sha(p) for p in (args.build, args.uniform, args.pubdates)}, "corpus_families": len(corpus),
               "visibility": stats,
               "sets": counts, "queries": {s: sum(q["split"] == s for q in queries) for s in ("dev", "test")},
               "outputs": {p.name: _sha(p) for p in sorted(args.out_dir.glob("*.jsonl"))}}
    (args.out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("corpus_families", "sets", "queries", "visibility")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
