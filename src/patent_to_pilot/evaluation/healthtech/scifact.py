"""Local SciFact release reader and evaluator.

The runtime claim reader intentionally drops evidence labels. Gold loading is a
separate function used only by evaluator code, so evaluator material cannot
silently enter the HealthTech acquisition path.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping


MAX_ABSTRACT_SENTS = 3
SciFactLabel = Literal["SUPPORT", "CONTRADICT"]


class SciFactFormatError(ValueError):
    """Raised when a local release does not match the pinned format."""


@dataclass(frozen=True)
class SciFactDocument:
    doc_id: str
    title: str
    sentences: tuple[str, ...]
    structured: bool


@dataclass(frozen=True)
class SciFactRuntimeClaim:
    claim_id: int
    claim: str


@dataclass(frozen=True)
class SciFactEvidence:
    label: SciFactLabel
    rationales: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class SciFactGoldClaim:
    claim_id: int
    claim: str
    evidence: dict[str, SciFactEvidence]
    cited_doc_ids: tuple[str, ...]


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SciFactFormatError(f"invalid JSON at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise SciFactFormatError(f"expected object at {path}:{line_number}")
            rows.append(row)
    return rows


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SciFactFormatError(f"{label} must be an integer")
    return value


def _doc_key(value: Any, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise SciFactFormatError(f"{label} must be a document identifier")
    text = str(value)
    if not text.isdigit():
        raise SciFactFormatError(f"{label} must be numeric")
    return text


def load_corpus(path: str | Path) -> dict[str, SciFactDocument]:
    documents: dict[str, SciFactDocument] = {}
    for row in _read_jsonl(path):
        doc_id = _doc_key(row.get("doc_id"), "doc_id")
        title = row.get("title")
        abstract = row.get("abstract")
        structured = row.get("structured", False)
        if not isinstance(title, str) or not title.strip():
            raise SciFactFormatError(f"document {doc_id} has no title")
        if not isinstance(abstract, list) or any(not isinstance(item, str) for item in abstract):
            raise SciFactFormatError(f"document {doc_id} abstract must be a string list")
        if not isinstance(structured, bool):
            raise SciFactFormatError(f"document {doc_id} structured must be boolean")
        if doc_id in documents:
            raise SciFactFormatError(f"duplicate document {doc_id}")
        documents[doc_id] = SciFactDocument(doc_id, title, tuple(abstract), structured)
    return documents


def _cited_doc_ids(row: Mapping[str, Any], claim_id: int) -> tuple[str, ...]:
    raw = row.get("cited_doc_ids", [])
    if not isinstance(raw, list):
        raise SciFactFormatError(f"claim {claim_id} cited_doc_ids must be a list")
    values = tuple(_doc_key(item, f"claim {claim_id} cited_doc_id") for item in raw)
    return values


def _claim_header(row: Mapping[str, Any]) -> tuple[int, str, tuple[str, ...]]:
    claim_id = _integer(row.get("id"), "claim id")
    claim = row.get("claim")
    if not isinstance(claim, str) or not claim.strip():
        raise SciFactFormatError(f"claim {claim_id} has no text")
    return claim_id, claim, _cited_doc_ids(row, claim_id)


def load_runtime_claims(path: str | Path) -> list[SciFactRuntimeClaim]:
    """Load open-retrieval claim text without citation or evidence metadata."""
    claims: list[SciFactRuntimeClaim] = []
    seen: set[int] = set()
    for row in _read_jsonl(path):
        claim_id, claim, _ = _claim_header(row)
        if claim_id in seen:
            raise SciFactFormatError(f"duplicate claim {claim_id}")
        seen.add(claim_id)
        claims.append(SciFactRuntimeClaim(claim_id, claim))
    return sorted(claims, key=lambda item: item.claim_id)


def _load_evidence(row: Mapping[str, Any], claim_id: int) -> dict[str, SciFactEvidence]:
    raw = row.get("evidence", {})
    if not isinstance(raw, dict):
        raise SciFactFormatError(f"claim {claim_id} evidence must be an object")
    evidence: dict[str, SciFactEvidence] = {}
    for raw_doc_id, raw_entries in raw.items():
        doc_id = _doc_key(raw_doc_id, f"claim {claim_id} evidence document")
        if not isinstance(raw_entries, list) or not raw_entries:
            raise SciFactFormatError(f"claim {claim_id} evidence {doc_id} must be nonempty")
        labels: set[str] = set()
        rationales: list[tuple[int, ...]] = []
        for entry in raw_entries:
            if not isinstance(entry, dict):
                raise SciFactFormatError(f"claim {claim_id} evidence {doc_id} entry must be an object")
            label = entry.get("label")
            if label not in {"SUPPORT", "CONTRADICT"}:
                raise SciFactFormatError(f"claim {claim_id} has unsupported label {label!r}")
            labels.add(label)
            sentences = entry.get("sentences")
            if not isinstance(sentences, list) or not sentences:
                raise SciFactFormatError(f"claim {claim_id} evidence {doc_id} needs sentences")
            sentence_ids = tuple(_integer(item, "rationale sentence") for item in sentences)
            if any(item < 0 for item in sentence_ids) or len(set(sentence_ids)) != len(sentence_ids):
                raise SciFactFormatError(f"claim {claim_id} evidence {doc_id} has invalid sentence IDs")
            rationales.append(sentence_ids)
        if len(labels) != 1:
            raise SciFactFormatError(f"claim {claim_id} evidence {doc_id} mixes labels")
        evidence[doc_id] = SciFactEvidence(next(iter(labels)), tuple(rationales))  # type: ignore[arg-type]
    return evidence


def load_gold_claims(path: str | Path) -> list[SciFactGoldClaim]:
    """Load labels/rationales for evaluator use only."""
    claims: list[SciFactGoldClaim] = []
    seen: set[int] = set()
    for row in _read_jsonl(path):
        claim_id, claim, cited = _claim_header(row)
        if claim_id in seen:
            raise SciFactFormatError(f"duplicate claim {claim_id}")
        seen.add(claim_id)
        claims.append(SciFactGoldClaim(claim_id, claim, _load_evidence(row, claim_id), cited))
    return sorted(claims, key=lambda item: item.claim_id)


def validate_against_corpus(
    claims: Iterable[SciFactRuntimeClaim | SciFactGoldClaim],
    corpus: Mapping[str, SciFactDocument],
) -> None:
    """Check cited/evidence document and rationale sentence references."""
    for claim in claims:
        if isinstance(claim, SciFactGoldClaim):
            for doc_id in claim.cited_doc_ids:
                if doc_id not in corpus:
                    raise SciFactFormatError(f"claim {claim.claim_id} cites missing document {doc_id}")
            for doc_id, evidence in claim.evidence.items():
                if doc_id not in corpus:
                    raise SciFactFormatError(f"claim {claim.claim_id} has missing evidence document {doc_id}")
                sentence_count = len(corpus[doc_id].sentences)
                seen_sentences: set[int] = set()
                for rationale in evidence.rationales:
                    if seen_sentences.intersection(rationale):
                        raise SciFactFormatError(
                            f"claim {claim.claim_id} evidence {doc_id} has overlapping rationales"
                        )
                    seen_sentences.update(rationale)
                if any(sentence >= sentence_count for sentence in seen_sentences):
                    raise SciFactFormatError(f"claim {claim.claim_id} references an out-of-range sentence")


def _f1(correct: int, retrieved: int, relevant: int) -> dict[str, float]:
    precision = correct / retrieved if retrieved else 0.0
    recall = correct / relevant if relevant else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    values = {"precision": precision, "recall": recall, "f1": f1}
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values.values()):
        raise SciFactFormatError("metric out of bounds")
    return values


def _prediction_map(
    predictions: Mapping[int, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    *,
    corpus: Mapping[str, SciFactDocument] | None = None,
) -> dict[int, dict[str, Any]]:
    rows = predictions.values() if isinstance(predictions, Mapping) else predictions
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise SciFactFormatError("prediction must be an object")
        claim_id = _integer(row.get("id"), "prediction id")
        if claim_id in result:
            raise SciFactFormatError(f"duplicate prediction {claim_id}")
        evidence = row.get("evidence", {})
        if not isinstance(evidence, dict):
            raise SciFactFormatError(f"prediction {claim_id} evidence must be an object")
        normalized: dict[str, dict[str, Any]] = {}
        for raw_doc_id, value in evidence.items():
            doc_id = _doc_key(raw_doc_id, f"prediction {claim_id} document")
            if not isinstance(value, Mapping):
                raise SciFactFormatError(f"prediction {claim_id} document {doc_id} must be an object")
            label = value.get("label")
            if label not in {"SUPPORT", "CONTRADICT"}:
                raise SciFactFormatError("predictions must use SUPPORT or CONTRADICT")
            if "sentences" not in value or not isinstance(value["sentences"], list):
                raise SciFactFormatError(f"prediction {claim_id} document {doc_id} has invalid sentences")
            sentences = [_integer(item, "prediction sentence") for item in value["sentences"]]
            if any(item < 0 for item in sentences):
                raise SciFactFormatError(f"prediction {claim_id} document {doc_id} has invalid sentences")
            if len(set(sentences)) != len(sentences):
                raise SciFactFormatError(
                    f"prediction {claim_id} document {doc_id} repeats a sentence ID"
                )
            if corpus is not None:
                if doc_id not in corpus:
                    raise SciFactFormatError(
                        f"prediction {claim_id} references unknown document {doc_id}"
                    )
                sentence_count = len(corpus[doc_id].sentences)
                if any(sentence >= sentence_count for sentence in sentences):
                    raise SciFactFormatError(
                        f"prediction {claim_id} document {doc_id} references an out-of-range sentence"
                    )
            normalized[doc_id] = {"label": label, "sentences": sentences}
        result[claim_id] = {"id": claim_id, "evidence": normalized}
    return result


def evaluate_predictions(
    gold_claims: Iterable[SciFactGoldClaim],
    predictions: Mapping[int, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    *,
    corpus: Mapping[str, SciFactDocument] | None = None,
    missing_policy: Literal["empty", "error"] = "empty",
) -> dict[str, Any]:
    """Mirror pinned SciFact semantics behind a strict local input contract.

    Missing claim rows are scored as empty evidence by default so they remain in
    the denominator. Unexpected claim IDs, duplicate rows/sentence IDs, invalid
    labels/types, and corpus/sentence-bound violations are format errors.
    """
    if missing_policy not in {"empty", "error"}:
        raise SciFactFormatError("missing_policy must be empty or error")
    gold = list(gold_claims)
    expected_ids = [claim.claim_id for claim in gold]
    if len(set(expected_ids)) != len(expected_ids):
        raise SciFactFormatError("duplicate gold claim")
    if any(isinstance(claim.claim_id, bool) or not isinstance(claim.claim_id, int) for claim in gold):
        raise SciFactFormatError("gold claim IDs must be integers")
    predicted = _prediction_map(predictions, corpus=corpus)
    unexpected = sorted(set(predicted) - set(expected_ids))
    if unexpected:
        raise SciFactFormatError(f"unexpected prediction claim IDs: {unexpected}")
    missing = sorted(set(expected_ids) - set(predicted))
    if missing_policy == "error" and missing:
        raise SciFactFormatError(f"missing prediction claim IDs: {missing}")
    abstract = Counter(relevant=0, retrieved=0, correct_label_only=0, correct_rationalized=0)
    sentence = Counter(relevant=0, retrieved=0, correct_selection=0, correct_label=0)
    per_claim: list[dict[str, Any]] = []
    for claim in gold:
        row = predicted.get(claim.claim_id, {"evidence": {}})
        row_evidence = row["evidence"]
        abstract["relevant"] += len(claim.evidence)
        sentence["relevant"] += sum(len(rationale) for evidence in claim.evidence.values() for rationale in evidence.rationales)
        claim_abstract = Counter(relevant=len(claim.evidence), retrieved=0, correct_label_only=0, correct_rationalized=0)
        claim_sentence = Counter(
            relevant=sum(len(rationale) for evidence in claim.evidence.values() for rationale in evidence.rationales),
            retrieved=0, correct_selection=0, correct_label=0,
        )
        for doc_id, prediction in row_evidence.items():
            abstract["retrieved"] += 1
            claim_abstract["retrieved"] += 1
            rationale = list(prediction["sentences"])
            rationale_set = set(rationale)
            sentence["retrieved"] += len(rationale)
            claim_sentence["retrieved"] += len(rationale)
            gold_evidence = claim.evidence.get(doc_id)
            if gold_evidence is None:
                continue
            label_matches = prediction["label"] == gold_evidence.label
            if label_matches:
                abstract["correct_label_only"] += 1
                claim_abstract["correct_label_only"] += 1
            if label_matches and any(set(gold_rationale).issubset(set(rationale[:MAX_ABSTRACT_SENTS]))
                                     for gold_rationale in gold_evidence.rationales):
                abstract["correct_rationalized"] += 1
                claim_abstract["correct_rationalized"] += 1
            for sentence_id in rationale_set:
                matching = [gold_rationale for gold_rationale in gold_evidence.rationales if sentence_id in gold_rationale]
                if len(matching) > 1:
                    raise SciFactFormatError("a gold sentence appears in multiple rationale sets")
                if matching and set(matching[0]).issubset(rationale_set):
                    sentence["correct_selection"] += 1
                    claim_sentence["correct_selection"] += 1
                    if label_matches:
                        sentence["correct_label"] += 1
                        claim_sentence["correct_label"] += 1
        per_claim.append({"claim_id": claim.claim_id, "abstract": dict(claim_abstract), "sentence": dict(claim_sentence)})
    return {
        "claim_count": len(gold),
        "missing_prediction_claim_ids": missing,
        "abstract_label_only": _f1(abstract["correct_label_only"], abstract["retrieved"], abstract["relevant"]),
        "abstract_rationalized": _f1(abstract["correct_rationalized"], abstract["retrieved"], abstract["relevant"]),
        "sentence_selection": _f1(sentence["correct_selection"], sentence["retrieved"], sentence["relevant"]),
        "sentence_label": _f1(sentence["correct_label"], sentence["retrieved"], sentence["relevant"]),
        "counts": {"abstract": dict(abstract), "sentence": dict(sentence)},
        "per_claim": per_claim,
    }


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_release(data_dir: str | Path) -> dict[str, Any]:
    """Return counts and hashes for a local release without model execution."""
    root = Path(data_dir)
    corpus_path = root / "corpus.jsonl"
    train_path = root / "claims_train.jsonl"
    dev_path = root / "claims_dev.jsonl"
    test_path = root / "claims_test.jsonl"
    corpus = load_corpus(corpus_path)
    train = load_gold_claims(train_path)
    dev = load_gold_claims(dev_path)
    test = load_runtime_claims(test_path)
    validate_against_corpus([*train, *dev], corpus)
    labels = Counter(evidence.label for claim in [*train, *dev] for evidence in claim.evidence.values())
    return {
        "corpus_documents": len(corpus),
        "claims_train": len(train),
        "claims_dev": len(dev),
        "claims_test": len(test),
        "gold_label_counts_train_dev": dict(labels),
        "test_labels_present": False,
        "files": {name: {"path": str(root / name), "bytes": (root / name).stat().st_size,
                          "sha256": sha256_file(root / name)}
                   for name in ("corpus.jsonl", "claims_train.jsonl", "claims_dev.jsonl", "claims_test.jsonl")},
        "rights": {
            "claims_and_annotations": "CC BY 4.0",
            "abstracts": "ODC-By 1.0",
            "code": "Apache 2.0",
        },
        "limitations": [
            "Official test labels are not present in the release.",
            "SciFact evidence verification is a component task, not a device-patent truth label.",
            "Runtime readers expose claim text and corpus documents, never gold evidence.",
        ],
    }
