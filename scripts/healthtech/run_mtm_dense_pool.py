"""MTM dense rankings on the approved GPU: one corpus encoding, rankings for every (corpus view, lane) at depth 200.

Same encoder, prompts, 384/64-term TAC passages and MaxP aggregation as run_dapfam_dense_pool.py (imported, unchanged).
Per query: candidates with priority later than the query's priority are removed (time filter), its own family is
removed, and for lane X every family sharing a 3-character CPC code with the query is removed. Corpus views restrict
candidates to families whose "sets" intersect the view (main = all; small = target+small; matched = target+matched;
uniform = target+uniform). Query rows: {"id","text"}; query metadata (priority, family, c3) comes from queries-meta.jsonl.
Labels are never read. Writes rankings-<view>-<lane>-<name>.jsonl and a receipt; refuses to overwrite.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import POOL_DEPTH, dense_passages  # noqa: E402

_spec = importlib.util.spec_from_file_location("dapfam_dense", Path(__file__).with_name("run_dapfam_dense_pool.py"))
dapfam_dense = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dapfam_dense)

VIEWS = {"main": None, "small": {"target", "small"}, "matched": {"target", "matched"}, "uniform": {"target", "uniform"}}


def keep_mask(priority, cutoff: int, own_position: int | None, view_mask, shared_positions, lane: str):
    """numpy keep-mask over corpus positions: time filter, own family, corpus view and (lane X) shared CPC3."""
    import numpy as np

    keep = (np.asarray(priority) <= cutoff) & np.asarray(view_mask, dtype=bool)
    if own_position is not None:
        keep[own_position] = False
    if lane == "X" and len(shared_positions):
        keep[np.asarray(shared_positions, dtype=np.int64)] = False
    return keep


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--queries-meta", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", required=True, help="query view label, e.g. P-dev")
    parser.add_argument("--views", default="main,small,matched,uniform")
    parser.add_argument("--reuse-vectors", type=Path)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    import numpy as np
    import torch

    views = args.views.split(",")
    outputs = {(v, lane): args.output_dir / f"rankings-{v}-{lane}-{args.name}.jsonl" for v in views for lane in ("U", "X")}
    if any(p.exists() for p in outputs.values()):
        raise SystemExit("output exists: refusing to overwrite")
    if dapfam_dense._sha256(args.model_dir / "model.safetensors") != dapfam_dense.MODEL_SAFETENSORS_SHA256:
        raise SystemExit("PatEmbed-large weight hash mismatch")
    dapfam_dense.check_local_window()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    corpus = dapfam_dense._read_jsonl(args.corpus, None)
    queries = dapfam_dense._read_jsonl(args.queries, None)
    meta = {m["id"]: m for m in dapfam_dense._read_jsonl(args.queries_meta, None)}
    ids = [r["id"] for r in corpus]
    passages, owner = [], []
    for i, row in enumerate(corpus):
        chunks = dense_passages(row["title"], row["abstract"], row["claims"])
        passages += chunks
        owner += [i] * len(chunks)
    timings = {}
    with dapfam_dense.local_gpu_slot(args.model_dir):
        encoder = dapfam_dense.MeanPoolEncoder(args.model_dir, args.batch_size)
        started = time.time()
        if args.reuse_vectors:
            vectors = np.load(args.reuse_vectors)
            if vectors.shape != (len(passages), encoder.model.config.hidden_size):
                raise SystemExit("reused vectors do not match the corpus passages")
            timings["passage_vectors_reused_sha256"] = dapfam_dense._sha256(args.reuse_vectors)
        else:
            vectors = encoder.encode(passages)
            timings["passage_encode_seconds"] = round(time.time() - started, 3)
            np.save(args.output_dir / "passage-vectors-f32.npy", vectors)
        started = time.time()
        qvec = torch.from_numpy(encoder.encode([q["text"] for q in queries])).to("cuda")
        timings["query_encode_seconds"] = round(time.time() - started, 3)
        matrix = torch.from_numpy(vectors).to("cuda")
        family_index = torch.tensor(owner, dtype=torch.int64, device="cuda")
        priority = np.array([r["priority"] for r in corpus], dtype=np.int64)
        position = {f: i for i, f in enumerate(ids)}
        members: dict[str, list[int]] = {}
        for i, r in enumerate(corpus):
            for code in r["c3"]:
                members.setdefault(code, []).append(i)
        view_mask = {v: np.array([VIEWS[v] is None or bool(VIEWS[v] & set(r["sets"])) for r in corpus], dtype=bool)
                     for v in views}
        handles = {k: p.open("w", encoding="utf-8") for k, p in outputs.items()}
        started = time.time()
        try:
            for qi, q in enumerate(queries):
                m = meta[q["id"]]
                scores = qvec[qi:qi + 1] @ matrix.T
                best = torch.full((len(ids),), -float("inf"), device="cuda")
                best.scatter_reduce_(0, family_index, scores[0], reduce="amax", include_self=True)
                shared = sorted({i for code in m["c3"] for i in members.get(code, ())})
                for (v, lane), handle in handles.items():
                    keep = keep_mask(priority, m["priority"], position.get(m["family_id"]), view_mask[v], shared, lane)
                    masked = torch.where(torch.from_numpy(keep).to("cuda"), best, torch.full_like(best, -float("inf")))
                    values, indices = torch.topk(masked, k=min(POOL_DEPTH, len(ids)))
                    ok = torch.isfinite(values)
                    ranked = sorted(zip(values[ok].cpu().tolist(), indices[ok].cpu().tolist()),
                                    key=lambda item: (-item[0], ids[item[1]]))
                    handle.write(json.dumps({"query_id": q["id"], "families": [ids[i] for _, i in ranked]}) + "\n")
        finally:
            for handle in handles.values():
                handle.close()
        timings["ranking_seconds"] = round(time.time() - started, 3)
    receipt = {"status": "PASS", "retriever": "PatEmbed-large dense, 384/64-term TAC passages, MaxP (run_dapfam_dense_pool)",
               "model_safetensors_sha256": dapfam_dense.MODEL_SAFETENSORS_SHA256, "families": len(ids),
               "passages": len(passages), "queries": len(queries), "depth": POOL_DEPTH, "views": views,
               "inputs_sha256": {p.name: dapfam_dense._sha256(p) for p in (args.corpus, args.queries, args.queries_meta)},
               "rankings_sha256": {p.name: dapfam_dense._sha256(p) for p in outputs.values()},
               "timings": timings, "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "labels_used": False}
    (args.output_dir / f"receipt-{args.name}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "families", "passages", "queries", "timings")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
