"""Encode runtime-only JSONL into a resumable HealthTech vector bundle.

The command is suitable for a pre-authorized compute host because it reads
only the named runtime export and writes only the named bundle directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from patent_to_pilot.evaluation.healthtech.local_retrieval import DenseEncoder
from patent_to_pilot.evaluation.healthtech.vector_artifacts import encode_vector_shards


ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_model_binding(
    model_path: Path,
    tokenizer_path: Path,
    *,
    model_id: str,
    revision: str,
) -> dict[str, object]:
    """Return a host-independent model identity for the vector manifest."""
    for path in (model_path, tokenizer_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    return {
        "model_id": model_id,
        "revision": revision,
        "model_artifact": {
            "filename": model_path.name,
            "sha256": sha256_file(model_path),
        },
        "tokenizer_artifact": {
            "filename": tokenizer_path.name,
            "sha256": sha256_file(tokenizer_path),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--shard-size", type=int, default=5000)
    parser.add_argument("--max-length", type=int, default=256)
    args = parser.parse_args()
    encoder = DenseEncoder(
        model_path=str(args.model),
        tokenizer_path=str(args.tokenizer),
        max_length=args.max_length,
    )
    manifest = encode_vector_shards(
        args.input,
        args.output,
        encoder,
        model=build_model_binding(
            args.model,
            args.tokenizer,
            model_id=args.model_id,
            revision=args.model_revision,
        ),
        config={
            "representation": "mean_pool_l2_normalized",
            "max_length": args.max_length,
            "dtype": "<f4",
            "norm_policy": "l2",
            "batch_size": args.batch_size,
            "shard_size": args.shard_size,
        },
        batch_size=args.batch_size,
        shard_size=args.shard_size,
    )
    print(json.dumps({
        "status": manifest["status"],
        "output": str(args.output.resolve()),
        "rows": manifest["row_count"],
        "dimension": manifest["dimension"],
        "shards": len(manifest["shards"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
