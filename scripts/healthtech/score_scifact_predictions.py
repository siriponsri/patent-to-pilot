"""Score a declared SciFact prediction manifest using evaluator-only labels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.scifact import (  # noqa: E402
    evaluate_predictions,
    load_corpus,
    load_gold_claims,
    sha256_file,
)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _resolve_data_root(release_root: Path) -> Path:
    """Accept either the extracted release root or its nested data directory."""
    for candidate in (release_root, release_root / "data"):
        if (candidate / "corpus.jsonl").is_file() and (candidate / "claims_dev.jsonl").is_file():
            return candidate
    raise FileNotFoundError(
        f"SciFact release must contain corpus.jsonl and claims_dev.jsonl under {release_root} or {release_root / 'data'}"
    )


def score_manifest(manifest_path: Path, release_root: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "ht-t2-scifact-prediction-manifest-v1":
        raise ValueError("unsupported prediction manifest format")
    if manifest.get("split") != "dev":
        raise ValueError("this scorer currently requires the declared dev split")
    prediction_path = manifest_path.parent / manifest["outputs"]["predictions_file"]
    data_root = _resolve_data_root(release_root)
    gold_path = data_root / "claims_dev.jsonl"
    corpus_path = data_root / "corpus.jsonl"
    predictions = _read_jsonl(prediction_path)
    corpus = load_corpus(corpus_path)
    gold = load_gold_claims(gold_path)
    metrics = evaluate_predictions(gold, predictions, corpus=corpus, missing_policy="error")
    return {
        "format": "ht-t2-scifact-score-v1",
        "status": "PASS_COMPONENT_SCORE",
        "task": "HT-T2",
        "split": "dev",
        "score_type": "development_split_only",
        "prediction_manifest": str(manifest_path),
        "prediction_manifest_sha256": sha256_file(manifest_path),
        "prediction_sha256": sha256_file(prediction_path),
        "gold_sha256": sha256_file(gold_path),
        "corpus_sha256": sha256_file(corpus_path),
        "claim_count": len(gold),
        "prediction_row_count": len(predictions),
        "corpus_documents": len(corpus),
        "metrics": {key: value for key, value in metrics.items() if key != "per_claim"},
        "per_claim_metrics_file": "per_claim_metrics.json",
        "limitations": [
            "This is a local dev-split component score, not an official hidden-test score.",
            "SciFact evidence verification is separate from HT-T1 device-patent retrieval and product claims.",
            "The prediction generator did not read evaluator labels; this scoring phase loads them only after predictions were written.",
        ],
    }, metrics.get("per_claim", [])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="fresh score JSON path")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; select a fresh score path")
    score, per_claim = score_manifest(args.manifest, args.release_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(score, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output.parent / score["per_claim_metrics_file"]).write_text(json.dumps(per_claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": score["status"], "output": str(args.output), "claims": score["claim_count"], "provider_calls": 0, "paid_cost_usd": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
