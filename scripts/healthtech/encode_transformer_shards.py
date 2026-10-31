"""Encode runtime-only JSONL with the pinned PatEmbed or multilingual-e5 backend."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.transformer_encoders import (
    TransformerEncoder,
    build_transformer_model_binding,
)
from patent_to_pilot.evaluation.healthtech.vector_artifacts import encode_vector_shards


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--kind", choices=("patembed", "e5"), required=True)
    parser.add_argument("--role", choices=("query", "passage"), required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--shard-size", type=int, default=5000)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--patembed-prompt-name", default="retrieval_MIXED")
    parser.add_argument("--stop-after-shards", type=int)
    args = parser.parse_args()
    if args.batch_size < 1 or args.shard_size < 1 or args.shard_size > 5000:
        parser.error("batch size must be positive and shard size must be between 1 and 5000")
    prompt_name = args.patembed_prompt_name if args.kind == "patembed" else None
    encoder = TransformerEncoder(
        args.model_dir,
        kind=args.kind,
        role=args.role,
        max_length=args.max_length,
        device=args.device,
        prompt_name=prompt_name,
    )
    config = {
        "backend": "transformers_local_v1",
        "encoder_kind": args.kind,
        "role": args.role,
        "max_length": args.max_length,
        "representation": "masked_mean_projection_l2_normalized" if args.kind == "patembed" else "masked_mean_l2_normalized",
        "dtype": "<f4",
        "norm_policy": "l2",
        "batch_size": args.batch_size,
        "shard_size": args.shard_size,
        "e5_prefix_policy": {"query": "query: ", "passage": "passage: "} if args.kind == "e5" else None,
        "patembed_prompt_name": prompt_name,
        "device": str(encoder.device),
    }
    manifest = encode_vector_shards(
        args.input,
        args.output,
        encoder,
        model=build_transformer_model_binding(
            args.model_dir,
            model_id=args.model_id,
            revision=args.model_revision,
            kind=args.kind,
        ),
        config=config,
        batch_size=args.batch_size,
        shard_size=args.shard_size,
        stop_after_shards=args.stop_after_shards,
    )
    print(json.dumps({
        "status": manifest["status"],
        "output": str(args.output.resolve()),
        "rows": manifest["row_count"],
        "dimension": manifest["dimension"],
        "shards": len(manifest["shards"]),
        "encoder": {
            "kind": args.kind,
            "role": args.role,
            "device": str(encoder.device),
            "rows_encoded": encoder.stats.rows,
            "attention_tokens": encoder.stats.token_count,
        },
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
