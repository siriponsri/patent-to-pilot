"""Check that the transformers mean-pool encoder for the dense baseline matches SentenceTransformer encode().

Both run on the same device on a deterministic sample of dense passages and queries, using
``model.encode(..., convert_to_numpy=True, normalize_embeddings=True)`` as the reference.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from patent_to_pilot.evaluation.dapfam_acquisition import dense_passages  # noqa: E402
from run_dapfam_dense_pool import MeanPoolEncoder  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--passages", type=int, default=64)
    parser.add_argument("--queries-n", type=int, default=16)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    import torch

    torch.set_num_threads(8)
    rng = random.Random(20261105)
    families = [json.loads(line) for line in args.corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
    queries = [json.loads(line)["text"] for line in args.queries.read_text(encoding="utf-8").splitlines() if line.strip()]
    passages = [p for row in rng.sample(families, args.passages) for p in dense_passages(row["title"], row["abstract"], row["claims"])]
    passages = rng.sample(passages, args.passages)
    sample_queries = rng.sample(queries, args.queries_n)
    texts = passages + sample_queries

    ours = MeanPoolEncoder(args.model_dir, batch_size=16, device=args.device).encode(texts)
    st_model = SentenceTransformer(str(args.model_dir), device=args.device)
    theirs = st_model.encode(texts, batch_size=16, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    theirs = np.asarray(theirs, dtype=np.float32)
    diff = np.abs(ours - theirs)
    cosine = np.sum(ours * theirs, axis=1)
    result = {
        "status": "PASS" if float(diff.max()) < 1e-4 and float(cosine.min()) > 0.99999 else "FAIL",
        "device": args.device, "texts": len(texts), "passages": len(passages), "queries": len(sample_queries),
        "max_abs_diff": float(diff.max()), "mean_abs_diff": float(diff.mean()), "min_cosine": float(cosine.min()),
        "st_max_seq_length": int(st_model.max_seq_length), "sentence_transformers": sentence_transformers.__version__,
        "torch": torch.__version__, "thresholds": {"max_abs_diff": 1e-4, "min_cosine": 0.99999},
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
