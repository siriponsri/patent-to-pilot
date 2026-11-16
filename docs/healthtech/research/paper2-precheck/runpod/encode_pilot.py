"""Encode the RunPod pilot sample with PatEmbed-large and measure throughput (RunPod or dr-train).

Construction (copied from src/patent_to_pilot/evaluation/dapfam_acquisition.py, unchanged):
- passage text = NFKC + whitespace-normalized "title abstract claims", 384-term windows, 64-term overlap,
  each prefixed with "encode document for different retrieval: ";
- encoder = datalyes/patembed-large @ 2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad (weights sha256 pinned),
  tokenizer truncation at max_seq_length 512, masked mean pooling over all tokens (prompt included),
  L2 normalization; passages encoded in descending character-length order (as the DAPFAM runner).
Modes: fp32 (DAPFAM reference dtype) and fp16 (model weights half, pooling in fp32).

Outputs in --out-dir (refuses to overwrite): vectors-<mode>.npy (float32, row i = passage i in sample
order), passage-index.json, receipt-<mode>.json. Self-contained: needs torch, transformers, numpy.
Cost guards: --time-limit-seconds stops the full run and still writes a receipt; --max-gpu-mem-gb caps the
per-process CUDA allocator (dr-train: 8, shared with the Paper 1 S8 job) and aborts before model load if
free memory is short.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

REPO_ID = "datalyes/patembed-large"
REVISION = "2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad"
WEIGHTS_SHA256 = "234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482"
DENSE_CHUNK_SIZE = 384
DENSE_CHUNK_OVERLAP = 64
DENSE_DOCUMENT_PREFIX = "encode document for different retrieval: "


def dense_passages(title, abstract, claims):
    text = " ".join(unicodedata.normalize("NFKC", " ".join((title or "", abstract or "", claims or ""))).split())
    if not text:
        return []
    tokens = text.split(" ")
    step = DENSE_CHUNK_SIZE - DENSE_CHUNK_OVERLAP
    return [DENSE_DOCUMENT_PREFIX + " ".join(tokens[offset:offset + DENSE_CHUNK_SIZE])
            for offset in range(0, len(tokens), step)]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_passages(sample: Path, max_docs: int | None, fields: str):
    passages, index = [], []
    with sample.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle):
            if max_docs is not None and line_no >= max_docs:
                break
            record = json.loads(line)
            claims = record["claims"] if fields == "tac" else None
            for passage_no, text in enumerate(dense_passages(record["title"], record["abstract"], claims)):
                passages.append(text)
                index.append([record["doc_id"], line_no, passage_no])
    digest = hashlib.sha256("\n".join(passages).encode("utf-8")).hexdigest()
    return passages, index, digest


def resolve_model(args) -> Path:
    if args.model_dir:
        model_dir = Path(args.model_dir)
    else:
        from huggingface_hub import snapshot_download
        model_dir = Path(snapshot_download(REPO_ID, revision=REVISION, local_dir=args.model_cache))
    if sha256_file(model_dir / "model.safetensors") != WEIGHTS_SHA256:
        raise SystemExit("PatEmbed-large weight hash mismatch")
    config = json.loads((model_dir / "sentence_bert_config.json").read_text(encoding="utf-8"))
    pooling = json.loads((model_dir / "1_Pooling" / "config.json").read_text(encoding="utf-8"))
    modules = json.loads((model_dir / "modules.json").read_text(encoding="utf-8"))
    if [m["path"] for m in modules] != ["", "1_Pooling"] or not pooling["pooling_mode_mean_tokens"] \
            or not pooling["include_prompt"] or config.get("do_lower_case") or int(config["max_seq_length"]) != 512:
        raise SystemExit("unexpected PatEmbed-large module layout")
    return model_dir


def nvidia_smi(device_index: int) -> dict:
    try:
        out = subprocess.run(["nvidia-smi", f"--id={device_index}",
                              "--query-gpu=name,driver_version,memory.total,memory.used,uuid",
                              "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=20).stdout
        name, driver, total, used, uuid = [part.strip() for part in out.strip().split(",")]
        return {"name": name, "driver": driver, "memory_total_mib": int(total), "memory_used_mib_at_start": int(used),
                "uuid_sha256_prefix": hashlib.sha256(uuid.encode()).hexdigest()[:12]}
    except Exception as exc:  # noqa: BLE001 - receipt only
        return {"error": repr(exc)}


class Encoder:
    def __init__(self, torch, model_dir: Path, mode: str):
        from transformers import AutoModel, AutoTokenizer
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        dtype = torch.float16 if mode == "fp16" else torch.float32
        self.model = AutoModel.from_pretrained(model_dir, torch_dtype=dtype).to("cuda").eval()

    def run(self, texts, order, batch_size, out=None, deadline=None):
        torch = self.torch
        tokens = forward = tokenize = 0.0
        done = 0
        start = time.perf_counter()
        with torch.inference_mode():
            for begin in range(0, len(order), batch_size):
                if deadline is not None and time.perf_counter() > deadline:
                    break
                idx = order[begin:begin + batch_size]
                t0 = time.perf_counter()
                batch = self.tokenizer([texts[i] for i in idx], padding=True, truncation=True, max_length=512,
                                       return_tensors="pt").to("cuda")
                tokenize += time.perf_counter() - t0
                ev0, ev1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                ev0.record()
                hidden = self.model(**batch).last_hidden_state.float()
                mask = batch["attention_mask"].unsqueeze(-1).to(hidden.dtype)
                pooled = torch.nn.functional.normalize((hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9), p=2, dim=1)
                ev1.record()
                vectors = pooled.cpu().numpy()  # synchronizes
                forward += ev0.elapsed_time(ev1) / 1000.0
                tokens += int(batch["attention_mask"].sum())
                if out is not None:
                    out[idx] = vectors
                done += len(idx)
        torch.cuda.synchronize()
        return {"passages": done, "wall_seconds": time.perf_counter() - start, "gpu_forward_seconds": forward,
                "tokenize_seconds": tokenize, "tokens": int(tokens)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["fp16", "fp32"], required=True)
    parser.add_argument("--model-dir", help="local pinned model dir (dr-train); omit to download the pinned revision")
    parser.add_argument("--model-cache", default="/workspace/patembed-large", help="download target (RunPod)")
    parser.add_argument("--max-docs", type=int, help="encode only the first N sample documents (parity subset)")
    parser.add_argument("--fields", choices=["tac", "ta"], default="tac")
    parser.add_argument("--sweep", default="16,32,64,128,256", help="batch sizes for the throughput sweep; '' to skip")
    parser.add_argument("--sweep-passages", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, help="full-run batch size (default: fastest sweep entry)")
    parser.add_argument("--max-batch-size", type=int, default=1024)
    parser.add_argument("--max-gpu-mem-gb", type=float, help="cap the CUDA allocator; abort if free memory is short")
    parser.add_argument("--time-limit-seconds", type=float, default=2400.0)
    parser.add_argument("--device-index", type=int, default=0)
    args = parser.parse_args()

    t_start = time.time()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = args.out_dir / f"receipt-{args.mode}.json"
    vectors_path = args.out_dir / f"vectors-{args.mode}.npy"
    if receipt_path.exists() or vectors_path.exists():
        raise SystemExit(f"refusing to overwrite outputs in {args.out_dir}")

    import numpy as np
    import torch
    import transformers
    import tokenizers

    torch.cuda.set_device(args.device_index)
    free, total = torch.cuda.mem_get_info()
    gib = 1024 ** 3
    if args.max_gpu_mem_gb:
        if free < (args.max_gpu_mem_gb + 1.0) * gib:
            raise SystemExit(f"ABORT: free GPU memory {free / gib:.2f} GiB < cap {args.max_gpu_mem_gb} + 1 GiB margin")
        torch.cuda.set_per_process_memory_fraction(min(1.0, args.max_gpu_mem_gb * gib / total), args.device_index)

    passages, index, passages_sha = load_passages(args.sample, args.max_docs, args.fields)
    order = sorted(range(len(passages)), key=lambda i: -len(passages[i]))
    t_load = time.time()
    model_dir = resolve_model(args)
    encoder = Encoder(torch, model_dir, args.mode)
    load_seconds = time.time() - t_load
    deadline = time.perf_counter() + args.time_limit_seconds

    # Warm-up (excluded from all rates).
    encoder.run(passages, order[:min(64, len(order))], min(32, args.max_batch_size))

    sweep = []
    sizes = [int(s) for s in args.sweep.split(",") if s.strip()]
    # Sweep on a fixed slice from the middle of the length order (typical lengths, not only the longest).
    mid = max(0, len(order) // 2 - args.sweep_passages // 2)
    sweep_order = order[mid:mid + args.sweep_passages]
    for size in sizes:
        if size > args.max_batch_size:
            sweep.append({"batch_size": size, "status": "SKIPPED_ABOVE_MAX_BATCH"})
            continue
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        try:
            stats = encoder.run(passages, sweep_order, size)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            sweep.append({"batch_size": size, "status": "OOM"})
            break
        stats.update(batch_size=size, status="OK", passages_per_second=stats["passages"] / stats["wall_seconds"],
                     peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                     peak_reserved_bytes=torch.cuda.max_memory_reserved())
        sweep.append(stats)
    ok = [row for row in sweep if row.get("status") == "OK"]
    batch_size = args.batch_size or (max(ok, key=lambda r: r["passages_per_second"])["batch_size"] if ok else 32)
    batch_size = min(batch_size, args.max_batch_size)

    out = np.zeros((len(passages), encoder.model.config.hidden_size), dtype=np.float32)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    full = encoder.run(passages, order, batch_size, out=out, deadline=deadline)
    status = "COMPLETE" if full["passages"] == len(passages) else "TIME_LIMIT_PARTIAL"
    np.save(vectors_path, out)
    (args.out_dir / "passage-index.json").write_text(json.dumps(
        {"passages_sha256": passages_sha, "columns": ["doc_id", "sample_line", "passage_no"], "rows": index}),
        encoding="utf-8")

    receipt = {
        "status": status, "mode": args.mode, "fields": args.fields,
        "host": {"hostname_sha256_prefix": hashlib.sha256(socket.gethostname().encode()).hexdigest()[:12],
                 "platform": platform.platform(), "python": sys.version.split()[0],
                 "runpod_pod_id_present": bool(os.environ.get("RUNPOD_POD_ID"))},
        "gpu": {**nvidia_smi(args.device_index), "torch_name": torch.cuda.get_device_name(args.device_index),
                "free_bytes_at_start": free, "total_bytes": total, "mem_cap_gb": args.max_gpu_mem_gb},
        "software": {"torch": torch.__version__, "cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
                     "transformers": transformers.__version__, "tokenizers": tokenizers.__version__,
                     "numpy": np.__version__, "tf32_matmul": torch.backends.cuda.matmul.allow_tf32},
        "model": {"repo": REPO_ID, "revision": REVISION, "weights_sha256": WEIGHTS_SHA256,
                  "source": "local_dir" if args.model_dir else "hf_snapshot_download", "max_length": 512,
                  "pooling": "masked mean incl. prompt, L2"},
        "inputs": {"sample_sha256": sha256_file(args.sample), "max_docs": args.max_docs,
                   "documents": len({row[1] for row in index}), "passages": len(passages),
                   "passages_sha256": passages_sha},
        "sweep": sweep, "batch_size": batch_size,
        "full_run": {**full, "passages_per_second_wall": full["passages"] / full["wall_seconds"],
                     "passages_per_second_gpu_forward": full["passages"] / max(full["gpu_forward_seconds"], 1e-9),
                     "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                     "peak_reserved_bytes": torch.cuda.max_memory_reserved()},
        "model_load_seconds": load_seconds, "total_wall_seconds": time.time() - t_start,
        "vectors_sha256": sha256_file(vectors_path),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "mode", "batch_size", "total_wall_seconds")}
                     | {"passages_per_second_wall": receipt["full_run"]["passages_per_second_wall"],
                        "gpu": receipt["gpu"].get("torch_name")}, indent=2))
    return 0 if status == "COMPLETE" else 4


if __name__ == "__main__":
    raise SystemExit(main())
