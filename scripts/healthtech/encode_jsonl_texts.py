"""Encode {id,text,text_sha256} JSONL with the pinned PatEmbed or e5 encoder on the approved GPU.

Writes <output>.npy (float32, L2-normalized rows) and <output>.ids.json in input order.
Label-free: the input files contain runtime text only.
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

from patent_to_pilot.evaluation.healthtech.transformer_encoders import TransformerEncoder  # noqa: E402
from patent_to_pilot.healthtech.local_execution import check_local_window, local_gpu_slot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="output prefix")
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--kind", choices=("patembed", "e5"), required=True)
    parser.add_argument("--role", choices=("query", "passage"), required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=512)
    args = parser.parse_args()
    import numpy as np

    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in rows:
        if hashlib.sha256(row["text"].encode("utf-8")).hexdigest() != row["text_sha256"]:
            raise SystemExit("text hash mismatch")
    check_local_window()
    started = time.time()
    with local_gpu_slot(args.model_dir):
        encoder = TransformerEncoder(args.model_dir, kind=args.kind, role=args.role, max_length=args.max_length,
                                     device="cuda", prompt_name="retrieval_MIXED" if args.kind == "patembed" else None)
        chunks = []
        for start in range(0, len(rows), args.batch_size):
            vectors, _ = encoder.encode([row["text"] for row in rows[start:start + args.batch_size]])
            chunks.append(np.asarray(vectors, dtype=np.float32))
    matrix = np.concatenate(chunks, axis=0)
    np.save(f"{args.output}.npy", matrix)
    Path(f"{args.output}.ids.json").write_text(json.dumps([row["id"] for row in rows]), encoding="utf-8")
    receipt = {"input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(), "rows": len(rows),
               "dimension": int(matrix.shape[1]), "kind": args.kind, "role": args.role, "max_length": args.max_length,
               "device": str(encoder.device), "attention_tokens": encoder.stats.token_count,
               "seconds": round(time.time() - started, 3),
               "npy_sha256": hashlib.sha256(Path(f"{args.output}.npy").read_bytes()).hexdigest()}
    Path(f"{args.output}.receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
