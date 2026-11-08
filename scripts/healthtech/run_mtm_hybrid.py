"""MTM dev phase 1, methods-log entries V1 and V2: BM25 and a score-calibrated BM25 + PatEmbed hybrid in lane X.

Labels are never read. Candidate rules match run_mtm_dense_pool.py (keep_mask imported): publication-date time filter,
own family removed, lane X removes families sharing a CPC3 with the query, corpus views by "sets".
BM25 indexes title + abstract + claims per family. Tokens are lowercase [a-z0-9]+ of length >= 2 minus the Lucene
English stopwords, with no stemming. Scoring uses k1 = 0.9, b = 0.4 and idf = ln(1 + (N - df + 0.5) / (df + 0.5)), and
each query term counts once. Dense scores are PatEmbed-large MaxP family scores from the reused passage vectors, as in
the baseline. Hybrid candidates are the union of the dense top 1,000 and the BM25 top 1,000 kept families. Each score is
z-normalised over that union per query, and fused = lam * z_dense + (1 - lam) * z_bm25; lam = 1 reproduces the dense
order. Writes <output-dir>/<method>/rankings-<view>-X-<name>.jsonl at depth 200 plus a receipt, and refuses to overwrite.
Methods log: docs/healthtech/research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md.
Phase 1b (V1b, V2b): the PatEmbed instruction prefix is stripped from the query before BM25 tokenisation; the dense
encoder still gets the full prefixed text. The phase-1 code without the strip is at commit 2feec03 (defective).
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

TOKEN = re.compile(r"[a-z0-9]+")
LUCENE_STOPWORDS = frozenset(
    "a an and are as at be but by for if in into is it no not of on or such that the their then there these they "
    "this to was will with".split())
K1, B = 0.9, 0.4
UNION_DEPTH = 1000
DEPTH = 200
DENSE_QUERY_PREFIX = "encode query for different document retrieval: "  # = dapfam_acquisition.DENSE_QUERY_PREFIX


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strip_prefix(text: str) -> str:
    """Query text without the PatEmbed instruction prefix (for BM25 and rerankers, never for the dense encoder)."""
    return text[len(DENSE_QUERY_PREFIX):] if text.startswith(DENSE_QUERY_PREFIX) else text


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if len(t) >= 2 and t not in LUCENE_STOPWORDS]


def build_bm25(token_lists, k1: float = K1, b: float = B):
    """Return (vocab, W) with W a CSR (docs x terms) matrix of BM25 document-side term weights."""
    import numpy as np
    from scipy.sparse import csr_matrix

    vocab: dict[str, int] = {}
    indptr, indices, tfs, lengths = [0], [], [], []
    for tokens in token_lists:
        counts = Counter(tokens)
        ids = [vocab.setdefault(t, len(vocab)) for t in counts]
        indices.append(np.asarray(ids, dtype=np.int32))
        tfs.append(np.asarray(list(counts.values()), dtype=np.float32))
        indptr.append(indptr[-1] + len(ids))
        lengths.append(len(tokens))
    indices = np.concatenate(indices) if indices else np.zeros(0, np.int32)
    tf = np.concatenate(tfs) if tfs else np.zeros(0, np.float32)
    n = len(lengths)
    dl = np.asarray(lengths, dtype=np.float32)
    avgdl = float(dl.mean()) if n and dl.mean() > 0 else 1.0
    df = np.bincount(indices, minlength=len(vocab)).astype(np.float64)
    idf = np.log1p((n - df + 0.5) / (df + 0.5)).astype(np.float32)
    dl_rep = np.repeat(dl, np.diff(np.asarray(indptr)))
    weights = idf[indices] * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl_rep / avgdl))
    return vocab, csr_matrix((weights, indices, np.asarray(indptr, dtype=np.int64)), shape=(n, len(vocab)))


def query_matrix(token_lists: list[list[str]], vocab: dict[str, int]):
    import numpy as np
    from scipy.sparse import csr_matrix

    rows, cols = [], []
    for i, tokens in enumerate(token_lists):
        for t in sorted({t for t in tokens if t in vocab}):
            rows.append(i)
            cols.append(vocab[t])
    data = np.ones(len(rows), dtype=np.float32)
    return csr_matrix((data, (rows, cols)), shape=(len(token_lists), len(vocab)))


def topk(scores, k: int, id_rank):
    """Indices of the k highest finite scores, ordered by (-score, id) deterministically."""
    import numpy as np

    finite = np.flatnonzero(np.isfinite(scores))
    k = min(k, len(finite))
    if k == 0:
        return np.zeros(0, dtype=np.int64)
    values = scores[finite]
    part = finite[np.argpartition(-values, k - 1)[:k]]
    threshold = scores[part].min()
    above = finite[values > threshold]
    ties = finite[values == threshold]
    ties = ties[np.argsort(id_rank[ties], kind="stable")][: k - len(above)]
    chosen = np.concatenate([above, ties])
    return chosen[np.lexsort((id_rank[chosen], -scores[chosen]))]


def zscore(values):
    import numpy as np

    std = float(values.std())
    return (values - values.mean()) / std if std > 0 else np.zeros_like(values)


def hybrid_order(dense, bm25, lambdas, id_rank, union_depth: int = UNION_DEPTH, depth: int = DEPTH):
    """{lam: ranked indices} over the union of the two top lists, fused on per-query z-scores."""
    import numpy as np

    union = np.union1d(topk(dense, union_depth, id_rank), topk(bm25, union_depth, id_rank))
    if len(union) == 0:
        return {lam: union for lam in lambdas}
    zd, zb = zscore(dense[union].astype(np.float64)), zscore(bm25[union].astype(np.float64))
    out = {}
    for lam in lambdas:
        fused = lam * zd + (1 - lam) * zb
        out[lam] = union[np.lexsort((id_rank[union], -fused))][:depth]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--queries-meta", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--vectors", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", required=True, help="query view label, e.g. P-dev")
    parser.add_argument("--views", default="main,small,matched,uniform")
    parser.add_argument("--lambdas", default="0.5,0.6,0.7,0.8,0.9,1.0")
    args = parser.parse_args()
    if args.name.endswith("-test"):
        raise SystemExit("phase-1 methods run on dev only")
    import numpy as np
    import torch

    dense_pool = _load("run_mtm_dense_pool")
    dapfam_dense = dense_pool.dapfam_dense
    views = args.views.split(",")
    lambdas = [float(x) for x in args.lambdas.split(",")]
    methods = ["bm25"] + [f"hyb-{lam:.1f}" for lam in lambdas]
    outputs = {(m, v): args.output_dir / m / f"rankings-{v}-X-{args.name}.jsonl" for m in methods for v in views}
    receipt_path = args.output_dir / f"receipt-hybrid-{args.name}.json"
    if receipt_path.exists() or any(p.exists() for p in outputs.values()):
        raise SystemExit("output exists: refusing to overwrite")
    if dapfam_dense._sha256(args.model_dir / "model.safetensors") != dapfam_dense.MODEL_SAFETENSORS_SHA256:
        raise SystemExit("PatEmbed-large weight hash mismatch")
    dapfam_dense.check_local_window()
    timings: dict[str, float] = {}
    started = time.time()
    corpus = dapfam_dense._read_jsonl(args.corpus, None)
    queries = dapfam_dense._read_jsonl(args.queries, None)
    meta = {m["id"]: m for m in dapfam_dense._read_jsonl(args.queries_meta, None)}
    ids = [r["id"] for r in corpus]
    id_rank = np.empty(len(ids), dtype=np.int64)
    id_rank[np.argsort(np.asarray(ids, dtype=object), kind="stable")] = np.arange(len(ids))
    owner = []
    for i, row in enumerate(corpus):
        owner += [i] * len(dense_pool.dense_passages(row["title"], row["abstract"], row["claims"]))
    vocab, weights = build_bm25(tokenize(" ".join((r["title"], r["abstract"], r["claims"]))) for r in corpus)
    weights_t = weights.T.tocsr()
    lexical = [strip_prefix(q["text"]) for q in queries]
    if any(t.startswith("encode query") for t in lexical):
        raise SystemExit("query prefix still present after strip")
    qmatrix = query_matrix([tokenize(t) for t in lexical], vocab)
    stripped_sha = hashlib.sha256("".join(t + "\n" for t in lexical).encode("utf-8")).hexdigest()
    timings["bm25_index_seconds"] = round(time.time() - started, 3)
    visible_from = np.array([r["visible_from"] for r in corpus], dtype=np.int64)
    position = {f: i for i, f in enumerate(ids)}
    members: dict[str, list[int]] = {}
    for i, r in enumerate(corpus):
        for code in r["c3"]:
            members.setdefault(code, []).append(i)
    view_mask = {v: np.array([dense_pool.VIEWS[v] is None or bool(dense_pool.VIEWS[v] & set(r["sets"])) for r in corpus],
                             dtype=bool) for v in views}
    for p in outputs.values():
        p.parent.mkdir(parents=True, exist_ok=True)
    with dapfam_dense.local_gpu_slot(args.model_dir):
        encoder = dapfam_dense.MeanPoolEncoder(args.model_dir, 64)
        vectors = np.load(args.vectors)
        if vectors.shape != (len(owner), encoder.model.config.hidden_size):
            raise SystemExit("vectors do not match the corpus passages")
        started = time.time()
        qvec = torch.from_numpy(encoder.encode([q["text"] for q in queries])).to("cuda")
        matrix = torch.from_numpy(vectors).to("cuda")
        family_index = torch.tensor(owner, dtype=torch.int64, device="cuda")
        handles = {k: p.open("w", encoding="utf-8") for k, p in outputs.items()}
        try:
            for start in range(0, len(queries), 64):
                bm_block = (qmatrix[start:start + 64] @ weights_t).toarray().astype(np.float32)
                for offset, bm_all in enumerate(bm_block):
                    qi = start + offset
                    q = queries[qi]
                    m = meta[q["id"]]
                    best = torch.full((len(ids),), -float("inf"), device="cuda")
                    best.scatter_reduce_(0, family_index, (qvec[qi:qi + 1] @ matrix.T)[0], reduce="amax", include_self=True)
                    dense_all = best.cpu().numpy()
                    shared = sorted({i for code in m["c3"] for i in members.get(code, ())})
                    for v in views:
                        keep = dense_pool.keep_mask(visible_from, m["priority"], position.get(m["family_id"]), view_mask[v],
                                                    shared, "X")
                        dense = np.where(keep, dense_all, -np.inf)
                        bm25 = np.where(keep, bm_all, -np.inf)
                        ranked = {"bm25": topk(bm25, DEPTH, id_rank)}
                        for lam, order in hybrid_order(dense, bm25, lambdas, id_rank).items():
                            ranked[f"hyb-{lam:.1f}"] = order
                        for method, order in ranked.items():
                            handles[(method, v)].write(json.dumps({"query_id": q["id"], "families": [ids[i] for i in order]}) + "\n")
        finally:
            for handle in handles.values():
                handle.close()
        timings["ranking_seconds"] = round(time.time() - started, 3)
    receipt = {"status": "PASS", "entries": ["V1b bm25", "V2b hybrid"], "bm25": {"k1": K1, "b": B, "vocab": len(vocab),
               "nnz": int(weights.nnz), "stopwords": "lucene-english-33", "stemming": False,
               "query": "dense instruction prefix stripped", "stripped_queries_sha256": stripped_sha},
               "hybrid": {"union_depth": UNION_DEPTH, "lambdas": lambdas, "normalisation": "per-query z over union"},
               "dense": "PatEmbed-large MaxP, reused passage vectors", "families": len(ids), "queries": len(queries),
               "depth": DEPTH, "views": views, "lane": "X",
               "inputs_sha256": {p.name: dapfam_dense._sha256(p) for p in (args.corpus, args.queries, args.queries_meta, args.vectors)},
               "rankings_sha256": {f"{m}/{p.name}": dapfam_dense._sha256(p) for (m, _), p in outputs.items()},
               "timings": timings, "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "labels_used": False}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "families", "queries", "timings")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
