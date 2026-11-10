"""One-shot native TA dev baseline using immutable pre-existing corpus vectors.

Launch only through the approved isolated supervisor. No corpus encoding path,
domain masks, qrels, sampling, overwrite, downloads, or automatic retries.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from run_dapfam_dense_pool import MeanPoolEncoder, _sha256, _read_jsonl
from patent_to_pilot.evaluation.dapfam_acquisition import dense_passages, DENSE_QUERY_PREFIX
from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot
from patent_to_pilot.research.native_dense_ranking import rank_maxp

PINS = {
    "manifest.json": "fd950817b3cab234c4175bb6c68cc9942ae4fcafd8c7108f2adeaab1ce161c1f",
    "corpus.jsonl": "42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d",
    "queries-ta.jsonl": "6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a",
}
VECTOR_SHA = "9a385bcfd0aab6c4c19f2a8715824922d42d328c53f0da58857b0106ed4f0137"
MODEL_PINS = {
    "model.safetensors": "234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482",
    "config.json": "bfa5f86c1416b6df6e51ef0b8a6d0d4cc8f34c083d0435c57856b95f8ed47854",
    "tokenizer.json": "d5496fadd2d7fda4e958da4285f7cd97c41177bbfc500580addc9c08896fb773",
    "tokenizer_config.json": "0088a6f8bcdd4014184fb068b83ebb12896a9db2bb269a71f73de83fef24bceb",
    "special_tokens_map.json": "b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3",
    "vocab.txt": "a123c19b8d4677efb40940208592207ef800cf302149a85ba073b430d050f591",
    "modules.json": "8f4b264b80206c830bebbdcae377e137925650a433b689343a63bdc9b3145460",
    "sentence_bert_config.json": "948201d8329907aae938fa62f9ceeed53f5694dacc2b87b9f3b78b37ee986529",
    "1_Pooling/config.json": "a30548e8bc4255aafe5e5c638f6b15712eebbc8e84ea5988a5835f976c412907",
}


def verify_inputs(runtime, model, vectors):
    for base, pins in ((runtime, PINS), (model, MODEL_PINS)):
        for name, expected in pins.items():
            if _sha256(base / name) != expected:
                raise ValueError("immutable input hash mismatch")
    if _sha256(vectors) != VECTOR_SHA:
        raise ValueError("immutable vector hash mismatch")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("runtime", "model", "vectors", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    check_local_window()
    if args.output.exists():
        raise ValueError("exclusive output already exists")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    started = time.monotonic()
    verify_inputs(args.runtime, args.model, args.vectors)
    import numpy as np
    corpus = _read_jsonl(args.runtime / "corpus.jsonl", None)
    queries = _read_jsonl(args.runtime / "queries-ta.jsonl", None)
    ids = [r["id"] for r in corpus]
    if (len(corpus) != 45336 or len(queries) != 474 or len(set(ids)) != len(ids)
            or len({r["id"] for r in queries}) != len(queries)
            or any(set(r) != {"id", "text"} for r in queries)):
        raise ValueError("unexpected runtime population or query schema")
    owners = np.asarray([i for i, r in enumerate(corpus)
                         for _ in dense_passages(r["title"], r["abstract"], r["claims"])], dtype=np.int64)
    vectors = np.load(args.vectors, mmap_mode="r", allow_pickle=False)
    if vectors.shape != (188944, 1024) or vectors.dtype != np.float32 or len(owners) != len(vectors):
        raise ValueError("passage/vector shape mismatch")
    if not np.isfinite(vectors).all():
        raise ValueError("nonfinite vectors")
    # Native TA bytes preserved after the model's declared retrieval prefix.
    texts = [DENSE_QUERY_PREFIX + r["text"] for r in queries]
    args.output.mkdir(exist_ok=False)
    with local_gpu_slot(args.model):
        encoder = MeanPoolEncoder(args.model, 32, device="cuda")
        torch = encoder.torch
        torch.set_num_threads(8)
        torch.backends.cuda.matmul.allow_tf32 = False
        t = time.monotonic()
        query_vectors = encoder.encode(texts)  # The only encode call:474 dev queries.
        encode_seconds = time.monotonic() - t
        np.save(args.output / "query-vectors-f32.npy", query_vectors, allow_pickle=False)
        matrix = torch.from_numpy(np.array(vectors)).to("cuda")
        t = time.monotonic()
        with (args.output / "rankings-top200.jsonl").open("x", encoding="utf-8") as handle:
            for row, vector in zip(queries, query_vectors, strict=True):
                scores = (torch.from_numpy(vector).to("cuda") @ matrix.T).cpu().numpy()
                ranked = rank_maxp(scores, owners, ids)
                handle.write(json.dumps({"query_id": row["id"], **ranked}) + "\n")
        rank_seconds = time.monotonic() - t
    receipt = {"status": "COMPLETED_NOT_EVALUATED", "queries": 474, "families": 45336,
               "passages": 188944, "corpus_encode_calls": 0, "labels_used": False,
               "vectors_sha256": VECTOR_SHA, "runtime_pins": PINS, "model_pins": MODEL_PINS,
               "query_view": "exact_native_TA_plus_retrieval_OUT_prefix_no_extra_normalization",
               "query_prefix": DENSE_QUERY_PREFIX, "batch_size": 32, "precision": "float32",
               "ranking": "full_universe_MaxP_global_lexical_ties_top200",
               "query_attention_tokens": encoder.tokens, "query_encode_seconds": encode_seconds,
               "ranking_seconds": rank_seconds, "wall_seconds": time.monotonic() - started,
               "rankings_sha256": _sha256(args.output / "rankings-top200.jsonl"),
               "query_vectors_sha256": _sha256(args.output / "query-vectors-f32.npy")}
    with (args.output / "completion.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
    print(json.dumps({"status": receipt["status"], "queries": 474, "wall_seconds": receipt["wall_seconds"]}))


if __name__ == "__main__":
    main()
