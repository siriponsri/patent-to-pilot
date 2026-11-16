"""Compare passage vectors from two encode_pilot.py runs on the same first N sample documents.

Inputs: two run directories (each with passage-index.json and vectors-<mode>.npy). The runs may cover
different numbers of documents; the comparison uses the passages of sample lines 0..N-1, which are a
prefix of both runs (passages are stored in sample order). Text identity is checked first.

Reports:
- per-passage cosine (vectors are L2-normalized, so cosine = dot): min, p01, mean, count < 0.999 / 0.99;
- rank agreement: Q query documents are chosen deterministically (sha256 of "parity:<doc_id>"); the query
  vector is the query document's FIRST passage vector taken from each run itself (document prefix, no
  extra encoding); each query ranks the other N-1 documents by MaxP over their passages. Report top-1
  agreement, mean/min overlap@10 and mean overlap@100 between run A and run B.
numpy only; CPU.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def load(run_dir: Path, mode: str | None):
    index = json.loads((run_dir / "passage-index.json").read_text(encoding="utf-8"))
    files = sorted(run_dir.glob("vectors-*.npy")) if mode is None else [run_dir / f"vectors-{mode}.npy"]
    if len(files) != 1:
        raise SystemExit(f"{run_dir}: expected exactly one vectors file, found {files}")
    receipt = json.loads((run_dir / files[0].name.replace("vectors-", "receipt-").replace(".npy", ".json"))
                         .read_text(encoding="utf-8"))
    return index, np.load(files[0], mmap_mode="r"), receipt


def ranking(vectors, doc_of_passage, n_docs, query_vec, exclude_doc, depth):
    scores = vectors @ query_vec
    best = np.full(n_docs, -np.inf, dtype=np.float64)
    np.maximum.at(best, doc_of_passage, scores)
    best[exclude_doc] = -np.inf
    order = np.lexsort((np.arange(n_docs), -best))  # score desc, sample line asc
    return order[:depth]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-a", type=Path, required=True)
    parser.add_argument("--run-b", type=Path, required=True)
    parser.add_argument("--mode-a")
    parser.add_argument("--mode-b")
    parser.add_argument("--n-docs", type=int, default=1000)
    parser.add_argument("--n-queries", type=int, default=50)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    index_a, vec_a, rec_a = load(args.run_a, args.mode_a)
    index_b, vec_b, rec_b = load(args.run_b, args.mode_b)
    rows_a = [r for r in index_a["rows"] if r[1] < args.n_docs]
    rows_b = [r for r in index_b["rows"] if r[1] < args.n_docs]
    if rows_a != rows_b or rows_a != index_a["rows"][:len(rows_a)] or rows_b != index_b["rows"][:len(rows_b)]:
        raise SystemExit("passage index mismatch between runs on the compared prefix")
    n_pass = len(rows_a)
    docs = sorted({r[1] for r in rows_a})
    if docs != list(range(args.n_docs)):
        raise SystemExit("compared prefix does not contain sample lines 0..N-1")
    a = np.asarray(vec_a[:n_pass], dtype=np.float64)
    b = np.asarray(vec_b[:n_pass], dtype=np.float64)
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise SystemExit("non-finite vectors")
    norms_a, norms_b = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1)
    if np.any(norms_a < 0.5) or np.any(norms_b < 0.5):
        raise SystemExit("zero/unencoded rows inside the compared prefix (partial run?)")
    cos = np.sum(a * b, axis=1) / (norms_a * norms_b)

    doc_of = np.array([r[1] for r in rows_a], dtype=np.int64)
    first = {}
    for pos, r in enumerate(rows_a):
        first.setdefault(r[1], pos)
    doc_ids = {r[1]: r[0] for r in rows_a}
    queries = sorted(docs, key=lambda d: hashlib.sha256(f"parity:{doc_ids[d]}".encode()).hexdigest())[:args.n_queries]
    top1, ov10, ov100 = [], [], []
    for q in queries:
        ra = ranking(a, doc_of, args.n_docs, a[first[q]], q, 100)
        rb = ranking(b, doc_of, args.n_docs, b[first[q]], q, 100)
        top1.append(int(ra[0] == rb[0]))
        ov10.append(len(set(ra[:10]) & set(rb[:10])) / 10)
        ov100.append(len(set(ra) & set(rb)) / 100)

    result = {
        "run_a": {"dir": str(args.run_a), "mode": rec_a["mode"], "gpu": rec_a["gpu"].get("torch_name"),
                  "vectors_sha256": rec_a["vectors_sha256"]},
        "run_b": {"dir": str(args.run_b), "mode": rec_b["mode"], "gpu": rec_b["gpu"].get("torch_name"),
                  "vectors_sha256": rec_b["vectors_sha256"]},
        "n_docs": args.n_docs, "n_passages": n_pass,
        "cosine": {"min": float(cos.min()), "p01": float(np.quantile(cos, 0.01)), "mean": float(cos.mean()),
                   "below_0_999": int((cos < 0.999).sum()), "below_0_99": int((cos < 0.99).sum())},
        "rank_agreement": {"n_queries": len(queries), "query": "first passage vector of the query document (per run)",
                           "aggregation": "MaxP over passages, query document excluded",
                           "top1_agreement": float(np.mean(top1)), "overlap_at_10_mean": float(np.mean(ov10)),
                           "overlap_at_10_min": float(np.min(ov10)), "overlap_at_100_mean": float(np.mean(ov100))},
    }
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
