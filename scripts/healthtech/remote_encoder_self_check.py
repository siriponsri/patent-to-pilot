"""Run a bounded remote encoder/layout/GPU self-check and write JSON evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.transformer_encoders import (
    TransformerEncoder,
    build_transformer_model_binding,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--kind", choices=("patembed", "e5"), required=True)
    parser.add_argument("--role", choices=("query", "passage"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--approved-gpu-uuid", required=True)
    parser.add_argument("--prompt-name", default="retrieval_MIXED")
    args = parser.parse_args()
    import numpy as np
    import torch

    torch.set_num_threads(8)
    visible_uuid = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if visible_uuid != args.approved_gpu_uuid:
        raise RuntimeError("CUDA_VISIBLE_DEVICES is not bound to the approved GPU UUID")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("exactly one CUDA device must be visible")
    binding = build_transformer_model_binding(
        args.model_dir,
        model_id=args.model_id,
        revision=args.revision,
        kind=args.kind,
    )
    encoder = TransformerEncoder(
        args.model_dir,
        kind=args.kind,
        role=args.role,
        max_length=512,
        device="cuda",
        prompt_name=args.prompt_name if args.kind == "patembed" else None,
    )
    texts = [
        "A catheter-based heart valve with a flexible sealing skirt.",
        "ลิ้นหัวใจเทียมสำหรับการรักษาผู้ป่วยโรคหัวใจ",
        "Combining e\u0301, emoji 🫀, and punctuation — for tokenizer coverage.",
        "A long edge-case row " + ("with repeated medical-device terminology " * 80),
    ]
    values, token_count = encoder.encode(texts)
    norms = np.linalg.norm(values, axis=1).tolist()
    payload = {
        "format": "ht-transformer-self-check-v1",
        "status": "PASS",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": binding,
        "runtime": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
            "cuda_device_name": torch.cuda.get_device_name(0),
            "visible_gpu_uuid": visible_uuid,
            "device": str(encoder.device),
            "torch_threads": torch.get_num_threads(),
            "max_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "encoder": {
            "kind": args.kind,
            "role": args.role,
            "prompt_name": args.prompt_name if args.kind == "patembed" else None,
            "rows": len(texts),
            "attention_tokens": token_count,
            "shape": list(values.shape),
            "dtype": values.dtype.str,
            "l2_norms": norms,
        },
        "limits": {
            "cpu_threads_max": 8,
            "ram_bytes_max": 32 * 1024 ** 3,
            "provider_calls": 0,
            "paid_cost_usd": 0,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
