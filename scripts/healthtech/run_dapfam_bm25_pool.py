"""Build label-free BM25 Top-200 DAPFAM pools over title+abstract+claims (CPU).

Query rows come either from a JSONL file {"id","text"} (e.g. LLM action texts) or from the queries
parquet restricted to one split (R1: the query family's own title+abstract+claims). Tokenization and
BM25Okapi parameters follow scripts/healthtech/run_dapfam_bm25.py (k1 1.5, b 0.75, IDF floor 0.25).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from patent_to_pilot.evaluation.dapfam_acquisition import POOL_DEPTH, CompactBM25  # noqa: E402
from run_dapfam_bm25 import tokenize, top_indices  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True, help="corpus-tac.jsonl from Stage 0")
    parser.add_argument("--queries-jsonl", type=Path)
    parser.add_argument("--queries-parquet", type=Path)
    parser.add_argument("--split", type=Path)
    parser.add_argument("--split-name", choices=("dev", "test"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.queries_jsonl:
        queries = [json.loads(line) for line in args.queries_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
        source = {"queries_jsonl_sha256": _sha256(args.queries_jsonl)}
    else:
        import pyarrow.parquet as pq

        split = json.loads(args.split.read_text(encoding="utf-8"))["assignment"]
        rows = pq.read_table(args.queries_parquet, columns=["query_id", "title_en", "abstract_en", "claims_text"]).to_pylist()
        queries = [{"id": str(r["query_id"]), "text": " ".join(r[c] or "" for c in ("title_en", "abstract_en", "claims_text"))}
                   for r in sorted(rows, key=lambda r: str(r["query_id"])) if split[str(r["query_id"])] == args.split_name]
        source = {"queries_parquet_sha256": _sha256(args.queries_parquet), "split_sha256": _sha256(args.split),
                  "split_name": args.split_name}

    started = time.time()
    family_ids: list[str] = []

    def documents():
        with args.corpus.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    family_ids.append(row["id"])
                    yield tokenize(" ".join((row["title"], row["abstract"], row["claims"])))

    index = CompactBM25(documents())
    index_seconds = time.time() - started
    started = time.time()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for query in queries:
            scores = index.get_scores(tokenize(query["text"]))
            top = top_indices(scores, POOL_DEPTH)
            handle.write(json.dumps({"query_id": query["id"], "families": [family_ids[i] for i in top],
                                     "scores": [round(float(scores[i]), 6) for i in top]}) + "\n")
    receipt = {
        "status": "PASS", "retriever": "BM25Okapi over title+abstract+claims (k1 1.5, b 0.75, IDF floor 0.25)",
        "tokenizer": "lowercase Unicode word tokens (\\w+)", "corpus_sha256": _sha256(args.corpus), **source,
        "families": len(family_ids), "vocabulary": len(index.vocab), "postings": int(len(index.doc_ids)),
        "queries": len(queries), "depth": POOL_DEPTH, "index_seconds": round(index_seconds, 3),
        "query_seconds": round(time.time() - started, 3), "rankings_sha256": _sha256(args.output), "labels_used": False,
    }
    Path(str(args.output).replace(".jsonl", ".receipt.json")).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
