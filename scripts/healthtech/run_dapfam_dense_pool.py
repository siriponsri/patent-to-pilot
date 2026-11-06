"""Build a label-free DAPFAM Top-200 dense candidate pool on the approved GPU.

PatEmbed-large (pinned) with its retrieval_OUT prompt pair, 384/64-term TAC passages, masked mean
pooling over all tokens (SentenceTransformer Pooling with include_prompt), L2 normalization, fp32,
MaxP family aggregation and a lexical family-id tie break. Query rows are either {"id","text"}
(single 512-token window) or {"id","windows":[...]} (multi-window; score = max over windows).
Passage vectors from an earlier run can be reused with --reuse-vectors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import POOL_DEPTH, dense_passages  # noqa: E402
from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot  # noqa: E402
from patent_to_pilot.healthtech.scout import class_member_indices  # noqa: E402

MODEL_SAFETENSORS_SHA256 = "234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_jsonl(path: Path, limit: int | None) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
                if limit is not None and len(rows) >= limit:
                    break
    return rows


class MeanPoolEncoder:
    def __init__(self, model_dir: Path, batch_size: int, device: str = "cuda"):
        import torch
        from transformers import AutoModel, AutoTokenizer

        config = json.loads((model_dir / "sentence_bert_config.json").read_text(encoding="utf-8"))
        pooling = json.loads((model_dir / "1_Pooling" / "config.json").read_text(encoding="utf-8"))
        modules = json.loads((model_dir / "modules.json").read_text(encoding="utf-8"))
        if [m["path"] for m in modules] != ["", "1_Pooling"] or not pooling["pooling_mode_mean_tokens"] \
                or not pooling["include_prompt"] or config.get("do_lower_case"):
            raise SystemExit("unexpected PatEmbed-large module layout")
        self.torch = torch
        self.max_length = int(config["max_seq_length"])
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModel.from_pretrained(model_dir, torch_dtype=torch.float32).to(device).eval()
        self.device = device
        self.batch_size = batch_size
        self.tokens = 0

    def encode(self, texts: list[str]):
        import numpy as np

        torch = self.torch
        order = sorted(range(len(texts)), key=lambda i: -len(texts[i]))
        out = np.zeros((len(texts), self.model.config.hidden_size), dtype=np.float32)
        with torch.inference_mode():
            for start in range(0, len(order), self.batch_size):
                idx = order[start:start + self.batch_size]
                batch = self.tokenizer([texts[i] for i in idx], padding=True, truncation=True,
                                       max_length=self.max_length, return_tensors="pt").to(self.device)
                hidden = self.model(**batch).last_hidden_state
                mask = batch["attention_mask"].unsqueeze(-1).to(hidden.dtype)
                pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
                pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
                out[idx] = pooled.float().cpu().numpy()
                self.tokens += int(batch["attention_mask"].sum())
        return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rankings-name", default="rankings-top200.jsonl")
    parser.add_argument("--window-aggregation", choices=("max", "mean"), default="max",
                        help="combine per-window passage scores of a multi-window query")
    parser.add_argument("--reuse-vectors", type=Path, help="passage-vectors-f32.npy from an earlier run on the same corpus")
    parser.add_argument("--family-ipc3", type=Path,
                        help="JSONL {id, ipc3}; query rows with allowed_ipc3 are restricted to families in those classes, "
                             "and rows with excluded_ipc3 drop families sharing any of those classes")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--limit-families", type=int)
    parser.add_argument("--limit-queries", type=int)
    args = parser.parse_args()
    import numpy as np

    if _sha256(args.model_dir / "model.safetensors") != MODEL_SAFETENSORS_SHA256:
        raise SystemExit("PatEmbed-large weight hash mismatch")
    check_local_window()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    families = _read_jsonl(args.corpus, args.limit_families)
    queries = _read_jsonl(args.queries, args.limit_queries)
    query_mode = "windows" if "windows" in queries[0] else "single"
    query_texts = [w for row in queries for w in (row["windows"] if query_mode == "windows" else [row["text"]])]
    query_owner = [i for i, row in enumerate(queries) for _ in (row["windows"] if query_mode == "windows" else [0])]
    family_ids = [row["id"] for row in families]
    passages: list[str] = []
    passage_family: list[int] = []
    for index, row in enumerate(families):
        chunks = dense_passages(row["title"], row["abstract"], row["claims"])
        passages.extend(chunks)
        passage_family.extend([index] * len(chunks))
    timings = {}
    with local_gpu_slot(args.model_dir):
        encoder = MeanPoolEncoder(args.model_dir, args.batch_size)
        started = time.time()
        if args.reuse_vectors:
            vectors = np.load(args.reuse_vectors)
            if vectors.shape != (len(passages), encoder.model.config.hidden_size):
                raise SystemExit("reused passage vectors do not match the corpus passages")
            timings["passage_vectors_reused_sha256"] = _sha256(args.reuse_vectors)
        else:
            vectors = encoder.encode(passages)
            timings["passage_encode_seconds"] = round(time.time() - started, 3)
        passage_tokens = encoder.tokens
        started = time.time()
        query_vectors = encoder.encode(query_texts)
        timings["query_encode_seconds"] = round(time.time() - started, 3)
        torch = encoder.torch
        started = time.time()
        class_members: dict[str, list[int]] = {}
        if args.family_ipc3:
            position = {family: i for i, family in enumerate(family_ids)}
            for row in _read_jsonl(args.family_ipc3, None):
                if row["id"] in position:
                    for code in row["ipc3"]:
                        class_members.setdefault(code, []).append(position[row["id"]])
        matrix = torch.from_numpy(vectors).to("cuda")
        family_index = torch.tensor(passage_family, dtype=torch.int64, device="cuda")
        all_queries = torch.from_numpy(query_vectors).to("cuda")
        owner = torch.tensor(query_owner, dtype=torch.int64)
        depth = min(POOL_DEPTH, len(family_ids))
        rankings_path = args.output_dir / args.rankings_name
        with rankings_path.open("w", encoding="utf-8") as handle:
            for index, row in enumerate(queries):
                rows = torch.nonzero(owner == index).flatten().to("cuda")
                window_scores = all_queries[rows] @ matrix.T
                scores = window_scores.amax(dim=0) if args.window_aggregation == "max" else window_scores.mean(dim=0)
                best = torch.full((len(family_ids),), -float("inf"), device="cuda")
                best.scatter_reduce_(0, family_index, scores, reduce="amax", include_self=True)
                if "allowed_ipc3" in row:
                    allowed = class_member_indices(row["allowed_ipc3"], class_members)
                    mask = torch.ones(len(family_ids), dtype=torch.bool, device="cuda")
                    mask[torch.tensor(allowed, dtype=torch.int64, device="cuda")] = False
                    best[mask] = -float("inf")
                if row.get("excluded_ipc3"):
                    # Cross-domain lane: drop every family that shares any IPC3 code with the query.
                    excluded = class_member_indices(row["excluded_ipc3"], class_members)
                    if excluded:
                        best[torch.tensor(excluded, dtype=torch.int64, device="cuda")] = -float("inf")
                values, indices = torch.topk(best, k=depth)
                keep = torch.isfinite(values)
                values, indices = values[keep], indices[keep]
                ranked = sorted(zip(values.cpu().tolist(), indices.cpu().tolist()),
                                key=lambda item: (-item[0], family_ids[item[1]]))
                handle.write(json.dumps({"query_id": row["id"], "families": [family_ids[i] for _, i in ranked],
                                         "scores": [round(v, 7) for v, _ in ranked]}) + "\n")
        timings["ranking_seconds"] = round(time.time() - started, 3)
    if not args.reuse_vectors:
        np.save(args.output_dir / "passage-vectors-f32.npy", vectors)
    receipt = {
        "status": "PASS",
        "retriever": "dense passage (PatEmbed-large, 384/64-term TAC passages, MaxP)",
        "query_mode": query_mode,
        "window_aggregation": args.window_aggregation if query_mode == "windows" else None,
        "model": {"repo": "datalyes/patembed-large", "revision": "2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad",
                  "model_safetensors_sha256": MODEL_SAFETENSORS_SHA256, "dtype": "float32", "max_length": encoder.max_length},
        "inputs": {"corpus_sha256": _sha256(args.corpus), "queries_sha256": _sha256(args.queries),
                   "limit_families": args.limit_families, "limit_queries": args.limit_queries},
        "families": len(family_ids), "passages": len(passages), "queries": len(queries),
        "query_windows": len(query_texts), "depth": depth,
        "ipc3_restricted_queries": sum("allowed_ipc3" in row for row in queries),
        "ipc3_excluded_queries": sum(bool(row.get("excluded_ipc3")) for row in queries),
        "family_ipc3_sha256": _sha256(args.family_ipc3) if args.family_ipc3 else None,
        "passage_attention_tokens": passage_tokens, "query_attention_tokens": encoder.tokens - passage_tokens,
        "batch_size": args.batch_size, "timings": timings,
        "rankings_sha256": _sha256(rankings_path),
        "vectors_sha256": _sha256(args.reuse_vectors or args.output_dir / "passage-vectors-f32.npy"),
        "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__,
        "labels_used": False,
    }
    (args.output_dir / f"{rankings_path.stem}.receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
