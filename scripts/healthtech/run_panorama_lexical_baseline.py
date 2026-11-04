#!/usr/bin/env python3
"""Run a deterministic lexical option-ranking baseline on pinned PANORAMA splits."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from collections import Counter
from pathlib import Path

import pyarrow.parquet as parquet


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tokens(value: object) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(str(value or ""))]


def flatten_par4pc_context(value: dict[str, object]) -> str:
    claims = value.get("claims") or []
    return " ".join([str(value.get("title") or ""), str(value.get("abstract") or ""), *[str(x) for x in claims]])


def flatten_par4pc_option(value: dict[str, object]) -> str:
    claims = value.get("claims") or []
    return " ".join([str(value.get("title") or ""), str(value.get("abstract") or ""), *[str(x) for x in claims]])


def parse_options(task: str, row: dict[str, object]) -> tuple[str, dict[str, str]]:
    if task == "PAR4PC":
        context = flatten_par4pc_context(row["context"])
        options = {str(key): flatten_par4pc_option(value) for key, value in row["options"].items()}
        return context, options
    context = str(row["context"] or "")
    parsed = json.loads(str(row["options"]))
    return context, {str(key): str(value) for key, value in parsed.items()}


def bm25(query: list[str], document: list[str], document_frequency: Counter[str], document_count: int, average_length: float) -> float:
    if not query or not document:
        return 0.0
    query_counts = Counter(query)
    document_counts = Counter(document)
    k1 = 1.2
    b = 0.75
    score = 0.0
    length = len(document)
    for term in query_counts:
        frequency = document_counts.get(term, 0)
        if not frequency:
            continue
        idf = math.log(1.0 + (document_count - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
        denominator = frequency + k1 * (1.0 - b + b * length / max(average_length, 1.0))
        score += idf * (frequency * (k1 + 1.0) / denominator)
    return score


def rank_row(task: str, row: dict[str, object]) -> tuple[list[str], str | None]:
    context, options = parse_options(task, row)
    if not options:
        return [], "no_options"
    query_tokens = tokens(context)
    docs = {key: tokens(value) for key, value in options.items()}
    document_frequency: Counter[str] = Counter()
    for doc in docs.values():
        document_frequency.update(set(doc))
    average_length = sum(len(doc) for doc in docs.values()) / max(len(docs), 1)
    ranked = sorted(
        docs,
        key=lambda key: (-bm25(query_tokens, docs[key], document_frequency, len(docs), average_length), key),
    )
    return ranked, None


def evaluate(task: str, source: Path, split: str, predictions_out: Path, summary_out: Path) -> dict[str, object]:
    started = time.perf_counter()
    table = parquet.read_table(source)
    rows = table.to_pylist()
    predictions = []
    failures = []
    top1_hits = 0
    top8_hits = 0
    singleton_exact = 0
    singleton_rows = 0
    for row in rows:
        ranked, failure = rank_row(task, row)
        key = f"{row['application_number']}::{row['claim_number']}"
        predictions.append({"key": key, "ranked_options": ranked})
        if failure:
            failures.append({"key": key, "reason": failure})
            continue
        gold = {str(value) for value in (row.get("gold_answers") or [])}
        if ranked and ranked[0] in gold:
            top1_hits += 1
        if any(value in gold for value in ranked[:8]):
            top8_hits += 1
        if len(gold) == 1:
            singleton_rows += 1
            if ranked and {ranked[0]} == gold:
                singleton_exact += 1
    elapsed = time.perf_counter() - started
    predictions_out.parent.mkdir(parents=True, exist_ok=True)
    predictions_out.write_text(json.dumps(predictions, indent=2) + "\n", encoding="utf-8")
    summary = {
        "run_version": "panorama-lexical-baseline-v1",
        "task": task,
        "split": split,
        "source": str(source),
        "source_sha256": sha256_file(source),
        "rows": len(rows),
        "failed_rows": len(failures),
        "failed_output_rate": len(failures) / max(len(rows), 1),
        "macro_gold_hit_at_1": top1_hits / max(len(rows), 1),
        "macro_gold_hit_at_8": top8_hits / max(len(rows), 1),
        "singleton_exact_top1": singleton_exact / max(singleton_rows, 1),
        "singleton_rows": singleton_rows,
        "wall_seconds": elapsed,
        "machine_time_per_row_seconds": elapsed / max(len(rows), 1),
        "method": "BM25-style lexical ranking over task-provided context and options; no gold/silver/negative fields read for ranking",
        "runtime_exclusions": ["gold_answers", "silver_answers", "negative_answers"],
        "retry_policy": "none",
        "predictions_path": str(predictions_out),
        "failure_reasons": failures,
    }
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["PAR4PC", "PI4PC"], required=True)
    parser.add_argument("--split", choices=["validation", "test"], required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--predictions-out", type=Path, required=True)
    parser.add_argument("--summary-out", type=Path, required=True)
    args = parser.parse_args()
    summary = evaluate(args.task, args.source, args.split, args.predictions_out, args.summary_out)
    print(json.dumps({"task": args.task, "split": args.split, "rows": summary["rows"], "macro_gold_hit_at_1": summary["macro_gold_hit_at_1"], "failed_output_rate": summary["failed_output_rate"], "summary": str(args.summary_out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
