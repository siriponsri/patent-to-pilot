"""Stage 0 for the organization-adaptive DAPFAM study: hash check, split, label-free GPU inputs.

Writes private files (split with query IDs, text JSONL for the GPU host) under --private-dir and an
aggregate-only summary under --summary. Protocol:
docs/healthtech/research/ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import (  # noqa: E402
    SPLIT_SEED,
    dense_passages,
    dense_query_text,
    dense_query_windows,
    component_split,
    first_ipc_section,
    positive_relations,
    query_components,
)

EXPECTED_SHA256 = {
    "corpus.parquet": "469fe8e04d8bd8775a1116eccf0983e570a03444bef9c6e14c97aabafb7526d6",
    "queries.parquet": "b5ad91a650349a0096911fadcb7bc35a0399eb12d1470fb2601d73af5fc2bcbe",
    "qrels_all.parquet": "e51ae4e13abee0fc7523560ecddd272bc85dc98befc8ab4466155a0c2d2d4f74",
}
TEXT_COLUMNS = ["title_en", "abstract_en", "claims_text"]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_jsonl(path: Path, rows: list[dict]) -> str:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return _sha256(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "methodology/datasets/research-only-nc")
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    import pyarrow.parquet as pq

    hashes = {name: _sha256(args.data_dir / name) for name in EXPECTED_SHA256}
    if hashes != EXPECTED_SHA256:
        raise SystemExit("DAPFAM input hash mismatch")
    args.private_dir.mkdir(parents=True, exist_ok=True)

    qrels = pq.read_table(args.data_dir / "qrels_all.parquet").to_pylist()
    queries = pq.read_table(args.data_dir / "queries.parquet",
                            columns=["query_id", "classifications_ipcr_list_first_three_chars_list", *TEXT_COLUMNS]).to_pylist()
    positives = positive_relations(qrels)
    query_ids = sorted(str(row["query_id"]) for row in queries)
    sections = {str(row["query_id"]): first_ipc_section(row["classifications_ipcr_list_first_three_chars_list"]) for row in queries}
    components = query_components(positives, query_ids)
    split = component_split(components, sections)
    split_path = args.private_dir / "split.json"
    split_path.write_text(json.dumps({"seed": SPLIT_SEED, "assignment": split, "component": components,
                                      "first_ipc_section": sections}, sort_keys=True, indent=1), encoding="utf-8")

    query_rows = [{"id": str(row["query_id"]), "text": dense_query_text(*(row[c] for c in TEXT_COLUMNS))}
                  for row in sorted(queries, key=lambda r: str(r["query_id"]))]
    corpus = pq.read_table(args.data_dir / "corpus.parquet", columns=["relevant_id", *TEXT_COLUMNS]).to_pylist()
    corpus_rows = []
    passages_total = 0
    for row in sorted(corpus, key=lambda r: str(r["relevant_id"])):
        record = {"id": str(row["relevant_id"]), "title": row["title_en"] or "", "abstract": row["abstract_en"] or "",
                  "claims": row["claims_text"] or ""}
        passages_total += len(dense_passages(record["title"], record["abstract"], record["claims"]))
        corpus_rows.append(record)
    queries_sha = _write_jsonl(args.private_dir / "queries-dense.jsonl", query_rows)
    window_rows = [{"id": str(row["query_id"]), "windows": dense_query_windows(*(row[c] for c in TEXT_COLUMNS))}
                   for row in sorted(queries, key=lambda r: str(r["query_id"]))]
    windows_sha = _write_jsonl(args.private_dir / "queries-dense-windows.jsonl", window_rows)
    corpus_sha = _write_jsonl(args.private_dir / "corpus-tac.jsonl", corpus_rows)

    comp_sizes = Counter(Counter(components.values()).values())
    by_split = Counter(split.values())
    out_eligible = Counter(split[q] for q in query_ids if positives.get(q, {}).get("OUT"))
    strata = Counter((sections[q], split[q]) for q in query_ids)
    summary = {
        "status": "PASS",
        "input_sha256": hashes,
        "split": {
            "seed": SPLIT_SEED,
            "rule": "connected components over shared positive targets; components with >= 50 queries go to dev; other components shuffled within majority first-IPC section until each section reaches ~1/3 dev (large components counted)",
            "split_file_sha256": _sha256(split_path),
            "queries": dict(by_split),
            "out_eligible_queries": dict(out_eligible),
            "components": len(set(components.values())),
            "component_size_histogram": {str(k): v for k, v in sorted(comp_sizes.items())},
            "largest_component": max(Counter(components.values()).values()),
            "by_first_ipc_section": {f"{s}:{p}": n for (s, p), n in sorted(strata.items())},
        },
        "gpu_inputs": {
            "queries_dense_jsonl_sha256": queries_sha,
            "queries_dense_windows_jsonl_sha256": windows_sha,
            "query_windows": sum(len(r["windows"]) for r in window_rows),
            "corpus_tac_jsonl_sha256": corpus_sha,
            "query_rows": len(query_rows),
            "corpus_rows": len(corpus_rows),
            "dense_passages": passages_total,
            "reference_passages_earlier_internal_run": 188944,
            "labels_in_gpu_inputs": False,
        },
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["split"], indent=1))
    print(json.dumps(summary["gpu_inputs"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
