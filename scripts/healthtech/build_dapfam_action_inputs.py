"""Turn Qwen action outputs into label-free retrieval inputs, and export corpus IPC3 metadata.

Writes (in --output-dir):
  family-ipc3.jsonl   {id, ipc3}                    corpus metadata for the IPC-restricted action
  q1-dense.jsonl      {id, text}                    functional query, dense query prefix
  q1-bm25.jsonl       {id, text}                    functional query, plain text
  q2-dense.jsonl      {id, text, allowed_ipc3}      functional query restricted to proposed classes
  q3-dense.jsonl      {id, text}                    pseudo-document, dense query prefix
A failed generation produces no row, so that action contributes an empty list for that query.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import DENSE_QUERY_PREFIX  # noqa: E402


def _write(path: Path, rows: list[dict]) -> dict:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    return {"rows": len(rows), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qwen-output", type=Path, required=True)
    parser.add_argument("--corpus-parquet", type=Path, default=ROOT / "methodology/datasets/research-only-nc/corpus.parquet")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    import pyarrow.parquet as pq

    args.output_dir.mkdir(parents=True, exist_ok=True)
    corpus = pq.read_table(args.corpus_parquet,
                           columns=["relevant_id", "classifications_ipcr_list_first_three_chars_list"]).to_pylist()
    ipc_rows = [{"id": str(r["relevant_id"]), "ipc3": sorted(set(r["classifications_ipcr_list_first_three_chars_list"] or []))}
                for r in sorted(corpus, key=lambda r: str(r["relevant_id"]))]
    outputs = [json.loads(line) for line in args.qwen_output.read_text(encoding="utf-8").splitlines() if line.strip()]
    q1_dense, q1_bm25, q2, q3 = [], [], [], []
    for row in outputs:
        a, b = row["A"]["parsed"], row["B"]["parsed"]
        if a:
            q1_dense.append({"id": row["id"], "text": DENSE_QUERY_PREFIX + a["functional_query"]})
            q1_bm25.append({"id": row["id"], "text": a["functional_query"]})
            q2.append({"id": row["id"], "text": DENSE_QUERY_PREFIX + a["functional_query"], "allowed_ipc3": a["target_ipc3"]})
        if b:
            q3.append({"id": row["id"], "text": DENSE_QUERY_PREFIX + b["pseudo_document"]})
    summary = {
        "qwen_output_sha256": hashlib.sha256(args.qwen_output.read_bytes()).hexdigest(),
        "queries": len(outputs),
        "family-ipc3.jsonl": _write(args.output_dir / "family-ipc3.jsonl", ipc_rows),
        "q1-dense.jsonl": _write(args.output_dir / "q1-dense.jsonl", q1_dense),
        "q1-bm25.jsonl": _write(args.output_dir / "q1-bm25.jsonl", q1_bm25),
        "q2-dense.jsonl": _write(args.output_dir / "q2-dense.jsonl", q2),
        "q3-dense.jsonl": _write(args.output_dir / "q3-dense.jsonl", q3),
        "q2_rows_without_classes": sum(1 for r in q2 if not r["allowed_ipc3"]),
        "labels_used": False,
    }
    (args.output_dir / "action-inputs.summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
