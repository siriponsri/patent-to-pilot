"""Evaluate imported dense vectors against the matched DAPFAM diagnostic.

Runtime corpus/query JSONL and the validated vector bundle contain no qrels.
Qrels are read locally through DuckDB for evaluation only and never copied to
the remote encoder or written to the output directory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.local_retrieval import DenseEncoder
from patent_to_pilot.evaluation.healthtech.vector_artifacts import (
    RuntimeTextRow,
    VectorBundle,
    load_vector_bundle,
    read_runtime_text,
    sha256_file,
)
from scripts.healthtech.run_dapfam_bm25 import (
    SparseBM25,
    evaluate,
    export_parquet,
    read_qrels,
    read_rows,
    tokenize,
    top_indices,
)


def _rrf_rankings(rankings: Sequence[Sequence[str]], *, rrf_k: int) -> list[str]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        if len(ranking) != len(set(ranking)):
            raise ValueError("RRF input contains duplicate candidate IDs")
        for rank, document_id in enumerate(ranking, 1):
            scores[document_id] = scores.get(document_id, 0.0) + 1.0 / (rrf_k + rank)
    return [document_id for document_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]


def _dense_rankings(
    query_rows: Sequence[RuntimeTextRow],
    bundle: VectorBundle,
    encoder: Any,
    *,
    batch_size: int,
    limit: int,
) -> tuple[dict[str, list[str]], dict[str, str], dict[str, int]]:
    rankings: dict[str, list[str]] = {}
    statuses: dict[str, str] = {}
    token_counts: dict[str, int] = {}
    for start in range(0, len(query_rows), batch_size):
        batch = list(query_rows[start:start + batch_size])
        try:
            values, token_count = encoder.encode([row.text for row in batch])
            if len(values) != len(batch):
                raise ValueError("query encoder returned the wrong row count")
            per_query_tokens = int(token_count / max(len(batch), 1))
            for row, vector in zip(batch, values):
                hits = bundle.search(vector, limit=limit)
                rankings[row.document_id] = [str(hit["document_id"]) for hit in hits]
                statuses[row.document_id] = "completed"
                token_counts[row.document_id] = per_query_tokens
        except (RuntimeError, ValueError, TypeError):
            for row in batch:
                rankings[row.document_id] = []
                statuses[row.document_id] = "failed"
                token_counts[row.document_id] = 0
    return rankings, statuses, token_counts


def _bm25_rankings(
    corpus_rows: Sequence[RuntimeTextRow],
    query_rows: Sequence[RuntimeTextRow],
    *,
    limit: int,
) -> dict[str, list[str]]:
    corpus_ids = [row.document_id for row in corpus_rows]
    index = SparseBM25([tokenize(row.text) for row in corpus_rows], k1=1.5, b=0.75, epsilon=0.25)
    return {
        query.document_id: [corpus_ids[index_id] for index_id in top_indices(index.get_scores(tokenize(query.text)), limit)]
        for query in query_rows
    }


def _write_rankings(output: Path, method_rankings: Mapping[str, Mapping[str, Sequence[str]]]) -> Path:
    path = output / "rankings.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for method in sorted(method_rankings):
            for query_id in sorted(method_rankings[method]):
                handle.write(json.dumps({
                    "method": method,
                    "query_id": query_id,
                    "ranked_ids": list(method_rankings[method][query_id]),
                }, sort_keys=True) + "\n")
    return path


def _validate_model_artifacts(bundle: VectorBundle, model_path: Path, tokenizer_path: Path) -> None:
    model = bundle.manifest.get("model", {})
    expected_model = model.get("model_artifact", {}).get("sha256")
    expected_tokenizer = model.get("tokenizer_artifact", {}).get("sha256")
    if not expected_model or not expected_tokenizer:
        raise ValueError("vector bundle is missing portable model artifact bindings")
    if sha256_file(model_path) != expected_model:
        raise ValueError("query model artifact does not match vector bundle")
    if sha256_file(tokenizer_path) != expected_tokenizer:
        raise ValueError("query tokenizer artifact does not match vector bundle")


def run_evaluation(
    corpus_rows: Sequence[RuntimeTextRow],
    query_rows: Sequence[RuntimeTextRow],
    qrels: dict[str, dict[str, float]],
    bundle: VectorBundle,
    encoder: Any,
    *,
    batch_size: int,
    k: int,
    rrf_k: int,
) -> tuple[dict[str, Any], dict[str, dict[str, list[str]]], dict[str, dict[str, str]]]:
    corpus_ids = [row.document_id for row in corpus_rows]
    if list(bundle.document_ids) != corpus_ids:
        raise ValueError("vector bundle document order does not match runtime corpus")
    query_ids = [row.document_id for row in query_rows]
    if set(query_ids) != set(qrels):
        raise ValueError("runtime query IDs and qrels query IDs do not match")
    corpus_id_set = set(corpus_ids)
    dense, dense_status, token_counts = _dense_rankings(
        query_rows, bundle, encoder, batch_size=batch_size, limit=k
    )
    bm25 = _bm25_rankings(corpus_rows, query_rows, limit=k)
    hybrid = {
        query_id: _rrf_rankings([bm25[query_id], dense[query_id]], rrf_k=rrf_k)[:k]
        for query_id in query_ids
    }
    method_rankings = {"bm25": bm25, "dense": dense, "hybrid_rrf": hybrid}
    method_statuses = {
        "bm25": {query_id: "completed" for query_id in query_ids},
        "dense": dense_status,
        "hybrid_rrf": dense_status,
    }
    metrics = {
        method: evaluate(
            method_rankings[method],
            qrels,
            k=k,
            universe=corpus_id_set,
            statuses=method_statuses[method],
        )
        for method in method_rankings
    }
    return {
        "metrics": metrics,
        "query_count": len(query_rows),
        "corpus_count": len(corpus_rows),
        "dense_failed_query_count": sum(status == "failed" for status in dense_status.values()),
        "dense_token_count_total": sum(token_counts.values()),
        "qrel_pair_count": sum(len(labels) for labels in qrels.values()),
        "k": k,
        "rrf_k": rrf_k,
        "failure_denominator_policy": "failed and missing queries remain in macro denominator; unlisted pairs remain unjudged",
    }, method_rankings, method_statuses


def _git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    corpus_path = args.corpus_runtime.resolve()
    query_path = args.queries_runtime.resolve()
    qrels_path = args.qrels.resolve()
    for path in (corpus_path, query_path, qrels_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    corpus_rows = read_runtime_text(corpus_path)
    query_rows = read_runtime_text(query_path)
    bundle = load_vector_bundle(args.bundle)
    model = bundle.manifest["model"]
    _validate_model_artifacts(bundle, args.model.resolve(), args.tokenizer.resolve())
    encoder = DenseEncoder(
        model_path=str(args.model),
        tokenizer_path=str(args.tokenizer),
        max_length=int(bundle.manifest["config"]["max_length"]),
    )
    with tempfile.TemporaryDirectory(prefix="ht-vector-eval-") as temp_dir:
        qrels_csv = Path(temp_dir) / "qrels.csv"
        export_parquet(args.duckdb, qrels_path, qrels_csv, "query_id, relevant_id, relevance_score, domain_rel")
        qrels, _ = read_qrels(qrels_csv)

    started = perf_counter()
    summary, method_rankings, method_statuses = run_evaluation(
        corpus_rows,
        query_rows,
        qrels,
        bundle,
        encoder,
        batch_size=args.batch_size,
        k=args.k,
        rrf_k=args.rrf_k,
    )
    elapsed = perf_counter() - started
    rankings_path = _write_rankings(output, method_rankings)
    payload = {
        "status": "PASS" if summary["dense_failed_query_count"] == 0 else "PARTIAL_DENSE_FAILURES",
        "task": "DAPFAM matched BM25/dense/hybrid retrieval diagnostic",
        "summary": summary,
        "inputs": {
            "runtime_corpus": {"sha256": sha256_file(corpus_path), "rows": len(corpus_rows)},
            "runtime_queries": {"sha256": sha256_file(query_path), "rows": len(query_rows)},
            "qrels": {"sha256": sha256_file(qrels_path), "rows": summary["qrel_pair_count"]},
            "vector_manifest": {"sha256": sha256_file(Path(args.bundle).resolve() / "manifest.json")},
        },
        "model": model,
        "runtime": {
            "elapsed_seconds": elapsed,
            "provider_calls": 0,
            "paid_cost_usd": 0,
        },
        "outputs": {"rankings": str(rankings_path)},
        "limits": [
            "DAPFAM qrels are a citation-based family retrieval diagnostic, not semantic device-product gold.",
            "Unlisted query-target pairs remain unjudged and are not treated as negatives.",
            "Dense document vectors are imported artifacts; query vectors are encoded locally with the bound model.",
        ],
        "code_revision": _git_revision(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "status.json").write_text(json.dumps({"method_statuses": method_statuses}, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckdb", type=Path, required=True)
    parser.add_argument("--corpus-runtime", type=Path, required=True)
    parser.add_argument("--queries-runtime", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--k", type=int, default=100)
    parser.add_argument("--rrf-k", type=int, default=60)
    args = parser.parse_args()
    if args.batch_size < 1 or args.k < 1 or args.rrf_k < 1:
        parser.error("batch size, k, and rrf-k must be positive")
    print(json.dumps(run(args), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
