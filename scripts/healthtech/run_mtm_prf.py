"""MTM dev phase 3a (methods log): dense vector PRF (Rocchio) in lane X with PatEmbed-large MaxP.

For each query and corpus view, the first k families of the query's own X ranking give feedback. A family's feedback
vector is its best-matching passage vector for the query (the MaxP winner), and c_k is their mean. The new query is
q' = normalise(w * q + (1 - w) * normalise(c_k)). A second full MaxP lane-X retrieval with q' under the same keep_mask
gives the ranking (depth 200). Variants prfK<k>-<w> for k in --ks and w in --weights; prfK0-1.0 is the sanity row and must
reproduce X. Labels are never read. Writes <output-dir>/<variant>/rankings-<view>-X-<name>.jsonl plus a receipt, and
refuses -test names and overwrites. Methods log: docs/healthtech/research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
DEPTH = 200


@lru_cache(maxsize=None)
def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unit(v):
    import numpy as np

    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def prf_query(q, feedback, w: float):
    """normalise(w * q + (1 - w) * normalise(mean(feedback))); w = 1 or no feedback returns normalise(q)."""
    import numpy as np

    q = _unit(np.asarray(q, dtype=np.float64))
    if w >= 1.0 or len(feedback) == 0:
        return q
    c = _unit(np.asarray(feedback, dtype=np.float64).mean(axis=0))
    return _unit(w * q + (1.0 - w) * c)


def winning_passages(passage_scores, starts, families: list[int]) -> list[int]:
    """Index of the best passage of each family; family f owns passages starts[f]:starts[f + 1]."""
    import numpy as np

    out = []
    for f in families:
        lo, hi = int(starts[f]), int(starts[f + 1])
        out.append(lo + int(np.argmax(passage_scores[lo:hi])))
    return out


def variant_names(ks, weights) -> list[str]:
    return ["prfK0-1.0"] + [f"prfK{k}-{w:.1f}" for w in weights for k in ks]


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
    parser.add_argument("--ks", default="3,5,10")
    parser.add_argument("--weights", default="0.7,0.8,0.9")
    args = parser.parse_args()
    if args.name.endswith("-test"):
        raise SystemExit("phase-3 methods run on dev only")
    import numpy as np
    import torch

    hybrid = _load("run_mtm_hybrid")
    dense_pool = hybrid._load("run_mtm_dense_pool")
    dapfam_dense = dense_pool.dapfam_dense
    views = args.views.split(",")
    ks = [int(x) for x in args.ks.split(",")]
    weights = [float(x) for x in args.weights.split(",")]
    names = variant_names(ks, weights)
    outputs = {(n, v): args.output_dir / n / f"rankings-{v}-X-{args.name}.jsonl" for n in names for v in views}
    receipt_path = args.output_dir / f"receipt-prf-{args.name}.json"
    if receipt_path.exists() or any(p.exists() for p in outputs.values()):
        raise SystemExit("output exists: refusing to overwrite")
    if dapfam_dense._sha256(args.model_dir / "model.safetensors") != dapfam_dense.MODEL_SAFETENSORS_SHA256:
        raise SystemExit("PatEmbed-large weight hash mismatch")
    dapfam_dense.check_local_window()
    corpus = dapfam_dense._read_jsonl(args.corpus, None)
    queries = dapfam_dense._read_jsonl(args.queries, None)
    meta = {m["id"]: m for m in dapfam_dense._read_jsonl(args.queries_meta, None)}
    ids = [r["id"] for r in corpus]
    id_rank = np.empty(len(ids), dtype=np.int64)
    id_rank[np.argsort(np.asarray(ids, dtype=object), kind="stable")] = np.arange(len(ids))
    counts = [len(dense_pool.dense_passages(r["title"], r["abstract"], r["claims"])) for r in corpus]
    starts = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    owner = np.repeat(np.arange(len(ids)), counts)
    visible_from = np.array([r["visible_from"] for r in corpus], dtype=np.int64)
    position = {f: i for i, f in enumerate(ids)}
    members: dict[str, list[int]] = {}
    for i, r in enumerate(corpus):
        for code in r["c3"]:
            members.setdefault(code, []).append(i)
    view_mask = {v: np.array([dense_pool.VIEWS[v] is None or bool(dense_pool.VIEWS[v] & set(r["sets"])) for r in corpus],
                             dtype=bool) for v in views}
    del corpus
    for p in outputs.values():
        p.parent.mkdir(parents=True, exist_ok=True)
    sanity_ok = 0
    with dapfam_dense.local_gpu_slot(args.model_dir):
        encoder = dapfam_dense.MeanPoolEncoder(args.model_dir, 64)
        vectors = np.load(args.vectors)
        if vectors.shape != (int(starts[-1]), encoder.model.config.hidden_size):
            raise SystemExit("vectors do not match the corpus passages")
        started = time.time()
        qvec = encoder.encode([q["text"] for q in queries])
        matrix = torch.from_numpy(vectors).to("cuda")
        family_index = torch.from_numpy(owner).to("cuda")

        def scores_for(vecs):
            """(passage scores of the first vector, family MaxP scores per vector) for a (n, d) array."""
            ps = torch.from_numpy(np.asarray(vecs, dtype=np.float32)).to("cuda") @ matrix.T
            best = torch.full((ps.shape[0], len(ids)), -float("inf"), device="cuda")
            best.scatter_reduce_(1, family_index.expand(ps.shape[0], -1), ps, reduce="amax", include_self=True)
            return ps[0].cpu().numpy(), best.cpu().numpy()

        handles = {k: p.open("w", encoding="utf-8") for k, p in outputs.items()}
        try:
            for qi, q in enumerate(queries):
                m = meta[q["id"]]
                shared = sorted({i for code in m["c3"] for i in members.get(code, ())})
                q0 = prf_query(qvec[qi], [], 1.0)
                passage_scores, base = scores_for(qvec[qi][None, :])  # exactly as the baseline: raw float32 query
                for v in views:
                    keep = dense_pool.keep_mask(visible_from, m["priority"], position.get(m["family_id"]), view_mask[v],
                                                shared, "X")
                    x_order = hybrid.topk(np.where(keep, base[0], -np.inf), DEPTH, id_rank)
                    ranked = {"prfK0-1.0": x_order}
                    plan = [(k, w) for w in weights for k in ks]
                    fb = {k: vectors[winning_passages(passage_scores, starts, [int(f) for f in x_order[:k]])] for k in ks}
                    new_q = np.stack([prf_query(q0, fb[k], w) for k, w in plan])
                    _, fam_scores = scores_for(new_q)
                    for (k, w), row in zip(plan, fam_scores):
                        ranked[f"prfK{k}-{w:.1f}"] = hybrid.topk(np.where(keep, row, -np.inf), DEPTH, id_rank)
                    for n, order in ranked.items():
                        handles[(n, v)].write(json.dumps({"query_id": q["id"], "families": [ids[i] for i in order]}) + "\n")
                    sanity_ok += 1
        finally:
            for handle in handles.values():
                handle.close()
        seconds = round(time.time() - started, 3)
        gpu = torch.cuda.get_device_name(0)
    receipt = {"status": "PASS", "entry": "3a dense vector PRF", "ks": ks, "weights": weights, "variants": names,
               "feedback": "MaxP-winning passage vectors of the first k X families in the same view",
               "families": len(ids), "queries": len(queries), "depth": DEPTH, "views": views, "lane": "X",
               "query_view_cells": sanity_ok,
               "inputs_sha256": {p.name: dapfam_dense._sha256(p) for p in (args.corpus, args.queries, args.queries_meta, args.vectors)},
               "rankings_sha256": {f"{n}/{p.name}": dapfam_dense._sha256(p) for (n, _), p in outputs.items()},
               "seconds": seconds, "gpu": gpu, "torch": torch.__version__, "labels_used": False}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "queries", "query_view_cells", "seconds")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
