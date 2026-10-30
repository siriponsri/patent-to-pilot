"""Export task-neutral runtime text from DAPFAM parquet inputs.

Only identifiers, title/abstract text, source identity, and hashes are
written. Qrels, relevance labels, split labels, and evaluator fields are
deliberately not read or exported.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Iterable, Mapping

from patent_to_pilot.evaluation.healthtech.vector_artifacts import export_runtime_text


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sql_literal(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def export_parquet_rows(duckdb: Path, source: Path, destination: Path, *, columns: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    sql = (
        "COPY (SELECT " + columns + " FROM read_parquet('" + sql_literal(source) + "')) "
        "TO '" + sql_literal(destination) + "' "
        "(FORMAT CSV, HEADER TRUE, DELIMITER '\\t');"
    )
    subprocess.run(
        [str(duckdb), ":memory:", "-c", sql],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def _text(row: Mapping[str, str]) -> str:
    return " ".join(value.strip() for value in (row.get("title_en") or "", row.get("abstract_en") or "") if value and value.strip())


def runtime_rows(rows: Iterable[Mapping[str, str]], *, id_column: str, dataset_id: str, source_revision: str):
    for row in rows:
        raw_id = (row.get(id_column) or "").strip()
        text = _text(row)
        if not raw_id or not text:
            raise ValueError(f"missing {id_column} or title/abstract text")
        yield {
            "item_id": raw_id,
            "document_id": raw_id,
            "text": text,
            "source_id": dataset_id,
            "source_revision": source_revision,
        }


def read_tsv(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def run(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    corpus = args.corpus.resolve()
    queries = args.queries.resolve()
    for path in (corpus, queries):
        if not path.is_file():
            raise FileNotFoundError(path)
    corpus_revision = args.source_revision or sha256_file(corpus)
    query_revision = args.source_revision or sha256_file(queries)
    with tempfile.TemporaryDirectory(prefix="ht-runtime-export-") as temp_dir:
        temp = Path(temp_dir)
        corpus_tsv = temp / "corpus.tsv"
        queries_tsv = temp / "queries.tsv"
        export_parquet_rows(args.duckdb, corpus, corpus_tsv, columns="relevant_id, title_en, abstract_en")
        export_parquet_rows(args.duckdb, queries, queries_tsv, columns="query_id, title_en, abstract_en")
        corpus_manifest = export_runtime_text(
            runtime_rows(read_tsv(corpus_tsv), id_column="relevant_id", dataset_id="dapfam-corpus", source_revision=corpus_revision),
            output / "corpus.jsonl",
            dataset_id="dapfam-corpus",
            source_revision=corpus_revision,
            representation="title_en+abstract_en",
        )
        query_manifest = export_runtime_text(
            runtime_rows(read_tsv(queries_tsv), id_column="query_id", dataset_id="dapfam-query", source_revision=query_revision),
            output / "queries.jsonl",
            dataset_id="dapfam-query",
            source_revision=query_revision,
            representation="title_en+abstract_en",
        )
    manifest = {
        "format": "ht-runtime-export-bundle-v1",
        "status": "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS",
        "qrels_included": False,
        "source_files": {
            "corpus": {"path": str(corpus), "sha256": sha256_file(corpus), "bytes": corpus.stat().st_size},
            "queries": {"path": str(queries), "sha256": sha256_file(queries), "bytes": queries.stat().st_size},
        },
        "exports": {"corpus": corpus_manifest, "queries": query_manifest},
        "limits": [
            "DAPFAM title/abstract text is a separate citation-based retrieval diagnostic.",
            "No qrels, relevance labels, split labels, or evaluator-only fields were exported.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckdb", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    manifest = run(args)
    print(json.dumps({
        "status": manifest["status"],
        "output": str(args.output.resolve()),
        "corpus_rows": manifest["exports"]["corpus"]["row_count"],
        "query_rows": manifest["exports"]["queries"]["row_count"],
        "qrels_included": manifest["qrels_included"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
