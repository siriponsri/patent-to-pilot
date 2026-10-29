"""Generate deterministic runtime-only SciFact lexical predictions."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.scifact import (  # noqa: E402
    SciFactDocument,
    SciFactRuntimeClaim,
    load_corpus,
    load_runtime_claims,
)


TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    "a an and are as at be by for from in is it of on or that the this to was were with".split()
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_data_root(release_root: Path) -> Path:
    """Accept either the extracted release root or its nested data directory."""
    for candidate in (release_root, release_root / "data"):
        if (candidate / "corpus.jsonl").is_file() and (candidate / "claims_dev.jsonl").is_file():
            return candidate
    raise FileNotFoundError(
        f"SciFact release must contain corpus.jsonl and claims_dev.jsonl under {release_root} or {release_root / 'data'}"
    )


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for token in TOKEN_RE.findall(text.lower()) if token not in STOPWORDS)


def _idf(document_tokens: Iterable[tuple[str, ...]]) -> dict[str, float]:
    documents = list(document_tokens)
    count = len(documents)
    document_frequency: Counter[str] = Counter()
    for tokens in documents:
        document_frequency.update(set(tokens))
    return {
        token: math.log(1.0 + (count - frequency + 0.5) / (frequency + 0.5))
        for token, frequency in document_frequency.items()
    }


def _bm25_score(query_tokens: tuple[str, ...], document_tokens: tuple[str, ...], idf: dict[str, float], average_length: float) -> float:
    if not query_tokens or not document_tokens:
        return 0.0
    frequencies = Counter(document_tokens)
    length = len(document_tokens)
    k1 = 1.2
    b = 0.75
    score = 0.0
    for token in set(query_tokens):
        term_frequency = frequencies.get(token, 0)
        if not term_frequency:
            continue
        denominator = term_frequency + k1 * (1.0 - b + b * length / average_length)
        score += idf.get(token, 0.0) * term_frequency * (k1 + 1.0) / denominator
    return score


def _rationale_sentences(claim_tokens: tuple[str, ...], document: SciFactDocument, maximum: int) -> list[int]:
    query = set(claim_tokens)
    ranked: list[tuple[int, int]] = []
    for sentence_id, sentence in enumerate(document.sentences):
        overlap = len(query.intersection(tokenize(sentence)))
        if overlap:
            ranked.append((overlap, sentence_id))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    return sorted(sentence_id for _, sentence_id in ranked[:maximum])


def generate_predictions(
    claims: Iterable[SciFactRuntimeClaim],
    corpus: dict[str, SciFactDocument],
    *,
    top_k: int = 3,
    minimum_score: float = 0.0,
    maximum_rationale_sentences: int = 3,
    default_label: str = "SUPPORT",
) -> list[dict]:
    """Rank corpus documents from claim text without reading evaluator fields."""
    if top_k <= 0 or maximum_rationale_sentences <= 0:
        raise ValueError("top_k and maximum_rationale_sentences must be positive")
    if default_label not in {"SUPPORT", "CONTRADICT"}:
        raise ValueError("default_label must be SUPPORT or CONTRADICT")
    document_tokens = {doc_id: tokenize(doc.title + " " + " ".join(doc.sentences)) for doc_id, doc in corpus.items()}
    average_length = sum(len(tokens) for tokens in document_tokens.values()) / max(len(document_tokens), 1)
    idf = _idf(document_tokens.values())
    predictions: list[dict] = []
    for claim in sorted(claims, key=lambda item: item.claim_id):
        query_tokens = tokenize(claim.claim)
        ranked = sorted(
            (
                _bm25_score(query_tokens, tokens, idf, average_length),
                doc_id,
            )
            for doc_id, tokens in document_tokens.items()
        )
        ranked.reverse()
        evidence: dict[str, dict] = {}
        for score, doc_id in ranked[:top_k]:
            if score <= minimum_score:
                continue
            sentences = _rationale_sentences(query_tokens, corpus[doc_id], maximum_rationale_sentences)
            if not sentences:
                continue
            evidence[doc_id] = {"label": default_label, "sentences": sentences}
        predictions.append({"id": claim.claim_id, "evidence": evidence})
    return predictions


def _write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="fresh ignored result directory")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; select a fresh result directory")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config.get("split") != "dev":
        parser.error("this baseline currently requires the declared dev split")
    args.output.mkdir(parents=True)
    data_root = _resolve_data_root(args.release_root)
    corpus_path = data_root / "corpus.jsonl"
    claims_path = data_root / "claims_dev.jsonl"
    corpus = load_corpus(corpus_path)
    claims = load_runtime_claims(claims_path)
    runtime_claims_path = args.output / "runtime_claims.jsonl"
    _write_jsonl(runtime_claims_path, [{"id": claim.claim_id, "claim": claim.claim} for claim in claims])
    predictions = generate_predictions(
        claims,
        corpus,
        top_k=int(config["selection"]["top_k_documents"]),
        minimum_score=float(config["selection"]["minimum_document_score"]),
        maximum_rationale_sentences=int(config["selection"]["maximum_rationale_sentences"]),
        default_label=str(config["selection"]["default_label"]),
    )
    predictions_path = args.output / "predictions.jsonl"
    _write_jsonl(predictions_path, predictions)
    manifest = {
        "format": "ht-t2-scifact-prediction-manifest-v1",
        "status": "PREDICTIONS_WRITTEN",
        "task": "HT-T2",
        "split": "dev",
        "protocol_id": config["protocol_id"],
        "prediction_method": config["prediction_method"],
        "runtime_only_generation": True,
        "evaluator_labels_read_by_generator": False,
        "inputs": {
            "release_root": str(args.release_root),
            "data_root": str(data_root),
            "corpus_file": "corpus.jsonl",
            "runtime_claim_projection_file": "runtime_claims.jsonl",
            "corpus_sha256": sha256_file(corpus_path),
            "claims_source_sha256": sha256_file(claims_path),
            "corpus_documents": len(corpus),
            "claims": len(claims),
        },
        "outputs": {
            "predictions_file": "predictions.jsonl",
            "runtime_claim_projection_file": "runtime_claims.jsonl",
            "prediction_sha256": sha256_file(predictions_path),
            "prediction_rows": len(predictions),
            "rows_with_evidence": sum(bool(row["evidence"]) for row in predictions),
        },
        "configuration": config["selection"],
        "limitations": config["limitations"],
    }
    (args.output / "prediction_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "output": str(args.output), "claims": len(claims), "documents": len(corpus), "provider_calls": 0, "paid_cost_usd": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
