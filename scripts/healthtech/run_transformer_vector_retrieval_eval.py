"""Evaluate imported PatEmbed/e5 vectors with the matching local query encoder."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.transformer_encoders import (
    TransformerEncoder,
    build_transformer_model_binding,
)
from patent_to_pilot.evaluation.healthtech.vector_artifacts import (
    PrecomputedQueryEncoder,
    load_vector_bundle,
    read_runtime_text,
    sha256_file,
)
from scripts.healthtech.run_dapfam_bm25 import export_parquet, read_qrels
from scripts.healthtech.run_vector_retrieval_eval import _write_rankings, run_evaluation


def _git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _validate_model_binding(bundle: Any, model_dir: Path) -> dict[str, Any]:
    model = bundle.manifest.get("model", {})
    config = bundle.manifest.get("config", {})
    kind = config.get("encoder_kind")
    if config.get("backend") != "transformers_local_v1" or kind not in {"patembed", "e5"}:
        raise ValueError("vector bundle is not a transformer encoder bundle")
    binding = build_transformer_model_binding(
        model_dir,
        model_id=str(model.get("model_id", "")),
        revision=str(model.get("revision", "")),
        kind=kind,
    )
    if binding.get("artifact_files") != model.get("artifact_files"):
        raise ValueError("local transformer artifacts do not match vector bundle")
    return {"kind": kind, "model_id": model.get("model_id"), "revision": model.get("revision")}


def _validate_query_bundle(document_bundle: Any, query_bundle: Any, query_ids: list[str]) -> dict[str, Any]:
    document_model = document_bundle.manifest.get("model", {})
    query_model = query_bundle.manifest.get("model", {})
    if document_model != query_model:
        raise ValueError("document and query vector bundles use different model bindings")
    document_config = document_bundle.manifest.get("config", {})
    query_config = query_bundle.manifest.get("config", {})
    for key in ("backend", "encoder_kind", "max_length", "representation", "dtype", "norm_policy", "patembed_prompt_name", "e5_prefix_policy"):
        if document_config.get(key) != query_config.get(key):
            raise ValueError(f"document and query vector configs disagree on {key}")
    if document_config.get("role") != "passage" or query_config.get("role") != "query":
        raise ValueError("document/query vector roles must be passage/query")
    if list(query_bundle.document_ids) != query_ids:
        raise ValueError("query vector order does not match runtime query order")
    return {
        "kind": document_model.get("encoder_kind"),
        "model_id": document_model.get("model_id"),
        "revision": document_model.get("revision"),
    }


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
    config = bundle.manifest["config"]
    if args.query_bundle is not None:
        query_bundle = load_vector_bundle(args.query_bundle)
        model_info = _validate_query_bundle(bundle, query_bundle, [row.document_id for row in query_rows])
        encoder = PrecomputedQueryEncoder(query_bundle, [row.document_id for row in query_rows])
        query_source = "imported_query_bundle"
    else:
        if args.model_dir is None:
            raise ValueError("--model-dir is required when --query-bundle is omitted")
        model_info = _validate_model_binding(bundle, args.model_dir.resolve())
        encoder = TransformerEncoder(
            args.model_dir,
            kind=config["encoder_kind"],
            role="query",
            max_length=int(config["max_length"]),
            device=args.device,
            prompt_name=config.get("patembed_prompt_name"),
        )
        query_source = "local_query_encoder"
    with tempfile.TemporaryDirectory(prefix="ht-transformer-vector-eval-") as temp_dir:
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
        "task": "DAPFAM matched BM25/transformer-dense/hybrid retrieval diagnostic",
        "summary": summary,
        "inputs": {
            "runtime_corpus": {"sha256": sha256_file(corpus_path), "rows": len(corpus_rows)},
            "runtime_queries": {"sha256": sha256_file(query_path), "rows": len(query_rows)},
            "qrels": {"sha256": sha256_file(qrels_path), "rows": summary["qrel_pair_count"]},
            "vector_manifest": {"sha256": sha256_file(Path(args.bundle).resolve() / "manifest.json")},
        },
        "model": model_info,
        "runtime": {
            "elapsed_seconds": elapsed,
            "provider_calls": 0,
            "paid_cost_usd": 0,
            "query_source": query_source,
            "query_rows_encoded": len(query_rows),
            "query_attention_tokens": getattr(getattr(encoder, "stats", None), "token_count", 0),
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
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--query-bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="auto")
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
