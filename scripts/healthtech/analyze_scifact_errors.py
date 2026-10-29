"""Build deterministic evaluator-only error analysis for an HT-T2 run."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.scifact import (  # noqa: E402
    evaluate_predictions,
    load_corpus,
    load_gold_claims,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object row: {path}")
            rows.append(value)
    return rows


def _resolve_data_root(release_root: Path) -> Path:
    for candidate in (release_root, release_root / "data"):
        if (candidate / "corpus.jsonl").is_file() and (candidate / "claims_dev.jsonl").is_file():
            return candidate
    raise FileNotFoundError(
        f"SciFact release must contain corpus.jsonl and claims_dev.jsonl under {release_root}"
    )


def _count(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"expected non-negative integer metric, got {value!r}")
    return value


def classify_claim(row: dict[str, Any]) -> list[str]:
    """Classify evaluator outcomes without exposing claim text or gold labels."""
    abstract = row["abstract"]
    sentence = row["sentence"]
    abstract_relevant = _count(abstract["relevant"])
    abstract_retrieved = _count(abstract["retrieved"])
    abstract_correct_label = _count(abstract["correct_label_only"])
    abstract_correct_rationale = _count(abstract["correct_rationalized"])
    sentence_relevant = _count(sentence["relevant"])
    sentence_retrieved = _count(sentence["retrieved"])
    sentence_correct_selection = _count(sentence["correct_selection"])
    sentence_correct_label = _count(sentence["correct_label"])

    buckets: list[str] = []
    if abstract_relevant == 0:
        buckets.append("abstract_no_gold_evidence")
    elif abstract_correct_label == 0:
        buckets.append("abstract_retrieval_miss")
    elif abstract_correct_label < abstract_relevant:
        buckets.append("abstract_partial_retrieval")
    if abstract_correct_rationale < abstract_correct_label:
        buckets.append("abstract_rationale_mismatch")
    if abstract_relevant > 0 and abstract_correct_label == abstract_relevant and abstract_correct_rationale == abstract_correct_label:
        buckets.append("abstract_fully_aligned")

    if sentence_relevant == 0:
        buckets.append("sentence_no_gold_evidence")
    elif sentence_correct_selection == 0:
        buckets.append("sentence_retrieval_miss")
    elif sentence_correct_selection < sentence_relevant:
        buckets.append("sentence_partial_selection")
    if sentence_correct_label < sentence_correct_selection:
        buckets.append("sentence_label_mismatch")
    if sentence_relevant > 0 and sentence_correct_selection == sentence_relevant and sentence_correct_label == sentence_correct_selection:
        buckets.append("sentence_fully_aligned")

    if not buckets:
        buckets.append("no_classification")
    return buckets


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def build_analysis(
    *,
    manifest: dict[str, Any],
    score: dict[str, Any],
    per_claim: list[dict[str, Any]],
    input_hashes: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if manifest.get("format") != "ht-t2-scifact-prediction-manifest-v1":
        raise ValueError("unsupported prediction manifest format")
    if manifest.get("split") != "dev":
        raise ValueError("HT-T2 error analysis requires the declared dev split")
    if score.get("status") != "PASS_COMPONENT_SCORE":
        raise ValueError("score must be a completed component score")
    if len(per_claim) != manifest["inputs"]["claims"]:
        raise ValueError("per-claim rows do not match the manifest denominator")

    claim_rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    for row in per_claim:
        if "claim_id" not in row or not isinstance(row["claim_id"], int):
            raise ValueError("per-claim row is missing an integer claim_id")
        buckets = classify_claim(row)
        bucket_counts.update(buckets)
        claim_rows.append({"claim_id": row["claim_id"], "buckets": buckets, **row})

    if len({row["claim_id"] for row in claim_rows}) != len(claim_rows):
        raise ValueError("duplicate claim IDs in per-claim metrics")

    claim_count = len(claim_rows)
    error_buckets = {
        bucket: {"count": count, "rate": _rate(count, claim_count)}
        for bucket, count in sorted(bucket_counts.items())
    }
    analysis = {
        "format": "ht-t2-scifact-error-analysis-v1",
        "status": "PASS_COMPONENT_ERROR_ANALYSIS_DEV_ONLY",
        "task": "HT-T2",
        "split": "dev",
        "claim_count": claim_count,
        "corpus_documents": manifest["inputs"]["corpus_documents"],
        "prediction_method": manifest["prediction_method"],
        "runtime_only_generation": manifest["runtime_only_generation"],
        "evaluator_labels_read_by_generator": manifest["evaluator_labels_read_by_generator"],
        "error_buckets": error_buckets,
        "bucket_counts_are_non_exclusive": True,
        "input_hashes": input_hashes,
        "limitations": [
            "Development split only; no hidden or official test score.",
            "Counts describe SciFact evidence-verification behavior and are not device-patent semantic gold.",
            "The analysis reads evaluator-derived per-claim metrics only after prediction generation and scoring.",
            "No claim text, abstract text, or evaluator relation is copied into the committed audit summary.",
        ],
    }
    return analysis, claim_rows


def render_analysis(analysis: dict[str, Any]) -> str:
    lines = [
        "# HT-T2 SciFact error analysis",
        "",
        f"- Status: `{analysis['status']}`",
        f"- Split: `{analysis['split']}`",
        f"- Claims: `{analysis['claim_count']}`",
        f"- Corpus documents: `{analysis['corpus_documents']}`",
        f"- Prediction method: `{analysis['prediction_method']}`",
        "",
        "This is evaluator-only development analysis. It does not create device-patent labels, clinical evidence, or an official hidden-test score.",
        "",
        "| Bucket | Claims | Rate |",
        "|---|---:|---:|",
    ]
    for bucket, values in analysis["error_buckets"].items():
        lines.append(f"| {bucket} | {values['count']} | {values['rate']:.4f} |")
    lines.extend(
        [
            "",
            "Bucket counts are non-exclusive: a claim can have a partial retrieval and a rationale or label mismatch in the same split.",
            "",
            "Interpretation: retrieval misses, partial retrieval, rationale mismatch, sentence-selection misses, and sentence-label mismatch are reported as distinct failure modes. Claims with no gold evidence remain separate from retrieval errors.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output: Path, analysis: dict[str, Any], claim_rows: list[dict[str, Any]]) -> None:
    output.mkdir(parents=True)
    (output / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "claim_buckets.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in claim_rows),
        encoding="utf-8",
    )
    (output / "ANALYSIS.md").write_text(render_analysis(analysis), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--score", type=Path, required=True)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")

    manifest = _read_json(args.manifest)
    score = _read_json(args.score)
    prediction_path = args.manifest.parent / manifest["outputs"]["predictions_file"]
    data_root = _resolve_data_root(args.release_root)
    corpus_path = data_root / "corpus.jsonl"
    gold_path = data_root / "claims_dev.jsonl"
    predictions = _read_jsonl(prediction_path)
    corpus = load_corpus(corpus_path)
    gold = load_gold_claims(gold_path)
    metrics = evaluate_predictions(gold, predictions, corpus=corpus, missing_policy="error")
    if score.get("prediction_manifest_sha256") != _sha256(args.manifest):
        raise ValueError("score does not bind the prediction manifest")
    if score.get("prediction_sha256") != _sha256(prediction_path):
        raise ValueError("score does not bind the prediction rows")
    if score.get("gold_sha256") != _sha256(gold_path) or score.get("corpus_sha256") != _sha256(corpus_path):
        raise ValueError("score does not bind the evaluator inputs")

    input_hashes = {
        "prediction_manifest": _sha256(args.manifest),
        "score": _sha256(args.score),
        "predictions": _sha256(prediction_path),
        "corpus": _sha256(corpus_path),
        "claims_dev": _sha256(gold_path),
    }
    analysis, claim_rows = build_analysis(
        manifest=manifest,
        score=score,
        per_claim=metrics.get("per_claim", []),
        input_hashes=input_hashes,
    )
    write_outputs(args.output, analysis, claim_rows)
    print(json.dumps({"status": analysis["status"], "output": str(args.output), "claims": analysis["claim_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
