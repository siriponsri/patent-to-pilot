"""Deterministic local retrieval components for the HT development runner."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import re
from time import perf_counter, process_time
from typing import Any, Iterable, Mapping

from patent_to_pilot.healthtech.contracts import canonical_patent_id, content_hash


_TOKEN_RE = re.compile(r"[\w-]+", flags=re.UNICODE)
_FORBIDDEN_RUNTIME_KEYS = {
    "references", "known_links", "disclosed_by", "evaluator", "gold", "split", "family_label",
}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text) if len(token) > 1]


def query_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DeviceRecord:
    query_id: str
    device_id_raw: str
    device_id_canonical: str
    company: str
    trade_name: str
    generic_name: str
    product_code: str
    technical_description: str
    features_of_interest: tuple[str, ...]
    source_id: str
    evidence_cutoff: str

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "DeviceRecord":
        return cls(
            query_id=str(row["query_id"]),
            device_id_raw=str(row["device_id_raw"]),
            device_id_canonical=str(row["device_id_canonical"]),
            company=str(row.get("company", "")),
            trade_name=str(row.get("trade_name", "")),
            generic_name=str(row.get("generic_name", "")),
            product_code=str(row.get("product_code", "")),
            technical_description=str(row["technical_description"]),
            features_of_interest=tuple(str(value) for value in row.get("features_of_interest", [])),
            source_id=str(row["source_id"]),
            evidence_cutoff=str(row["evidence_cutoff"]),
        )


@dataclass(frozen=True)
class PatentRecord:
    patent_id_raw: str
    patent_id_canonical: str
    document_kind: str
    jurisdiction: str
    title: str
    abstract: str
    claims: str
    text: str
    source_id: str
    source_revision: str
    source_url: str
    raw_html_sha256: str
    normalized_sha256: str
    source_date: str
    company_metadata: str
    company_metadata_basis: str

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "PatentRecord":
        canonical = canonical_patent_id(str(row["patent_id_canonical"]))
        if canonical != row["patent_id_canonical"]:
            raise ValueError("runtime patent canonical ID is not normalized")
        return cls(
            patent_id_raw=str(row["patent_id_raw"]),
            patent_id_canonical=canonical,
            document_kind=str(row["document_kind"]),
            jurisdiction=str(row["jurisdiction"]),
            title=str(row["title"]),
            abstract=str(row["abstract"]),
            claims=str(row.get("claims", "")),
            text=str(row["text"]),
            source_id=str(row["source_id"]),
            source_revision=str(row["source_revision"]),
            source_url=str(row["source_url"]),
            raw_html_sha256=str(row["raw_html_sha256"]),
            normalized_sha256=str(row["normalized_sha256"]),
            source_date=str(row["source_date"]),
            company_metadata=str(row.get("company_metadata", "")),
            company_metadata_basis=str(row.get("company_metadata_basis", "")),
        )


def validate_runtime_payload(payload: Mapping[str, Any]) -> tuple[list[DeviceRecord], list[PatentRecord]]:
    """Validate runtime-only data and reject evaluator shortcuts."""
    if payload.get("status") != "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS":
        raise ValueError("runtime payload must declare evaluator-label isolation")
    if not isinstance(payload.get("devices"), list) or not isinstance(payload.get("patents"), list):
        raise ValueError("runtime payload needs device and patent lists")
    for row in payload["devices"] + payload["patents"]:
        if not isinstance(row, dict):
            raise ValueError("runtime rows must be objects")
        leaked = _FORBIDDEN_RUNTIME_KEYS.intersection(row)
        if leaked:
            raise ValueError(f"runtime row exposes evaluator fields: {sorted(leaked)}")
    devices = [DeviceRecord.from_dict(row) for row in payload["devices"]]
    patents = [PatentRecord.from_dict(row) for row in payload["patents"]]
    if len({device.query_id for device in devices}) != len(devices):
        raise ValueError("duplicate runtime query IDs")
    if len({patent.patent_id_canonical for patent in patents}) != len(patents):
        raise ValueError("duplicate runtime patent IDs")
    if any(not patent.text.strip() for patent in patents):
        raise ValueError("runtime patent text cannot be empty")
    return devices, patents


def _ranked_ids(scores: Mapping[str, float], *, limit: int | None = None) -> list[str]:
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [item[0] for item in ordered[:limit]]


class BM25Index:
    """Small deterministic BM25 implementation for the declared patent universe."""

    def __init__(self, documents: Iterable[PatentRecord], *, k1: float = 1.2, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.documents = {document.patent_id_canonical: document for document in documents}
        self.tokens = {key: tokenize(document.text) for key, document in self.documents.items()}
        self.lengths = {key: len(value) for key, value in self.tokens.items()}
        self.avgdl = sum(self.lengths.values()) / max(len(self.lengths), 1)
        self.document_frequency: dict[str, int] = {}
        for values in self.tokens.values():
            for token in set(values):
                self.document_frequency[token] = self.document_frequency.get(token, 0) + 1

    def search(self, query: str, *, limit: int) -> list[dict[str, Any]]:
        terms = tokenize(query)
        document_count = len(self.documents)
        scores: dict[str, float] = {}
        for document_id, values in self.tokens.items():
            frequencies: dict[str, int] = {}
            for token in values:
                frequencies[token] = frequencies.get(token, 0) + 1
            score = 0.0
            for term in terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                df = self.document_frequency.get(term, 0)
                idf = math.log(1.0 + (document_count - df + 0.5) / (df + 0.5))
                denominator = frequency + self.k1 * (1.0 - self.b + self.b * self.lengths[document_id] / max(self.avgdl, 1e-9))
                score += idf * (frequency * (self.k1 + 1.0)) / denominator
            scores[document_id] = score
        return [
            {"patent_id_canonical": patent_id, "score": float(score), "rank": rank}
            for rank, (patent_id, score) in enumerate(sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit], 1)
        ]


def _load_model_dependencies():
    try:
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer
    except ImportError as exc:  # pragma: no cover - environment-specific dependency boundary
        raise RuntimeError("dense/reranker execution requires numpy, onnxruntime and tokenizers") from exc
    return np, ort, Tokenizer


class _OnnxTokenizer:
    def __init__(self, tokenizer_path: str, *, max_length: int) -> None:
        _, _, tokenizer_type = _load_model_dependencies()
        self.tokenizer = tokenizer_type.from_file(tokenizer_path)
        self.max_length = max_length
        self.pad_id = self.tokenizer.token_to_id("[PAD]") or 0

    def encode_texts(self, texts: list[str]) -> tuple[Any, Any, Any, int]:
        np, _, _ = _load_model_dependencies()
        encoded = [self.tokenizer.encode(text) for text in texts]
        width = min(self.max_length, max((len(item.ids) for item in encoded), default=1))
        ids = np.full((len(encoded), width), self.pad_id, dtype=np.int64)
        masks = np.zeros((len(encoded), width), dtype=np.int64)
        types = np.zeros((len(encoded), width), dtype=np.int64)
        token_count = 0
        for row, item in enumerate(encoded):
            length = min(width, len(item.ids))
            token_count += length
            ids[row, :length] = item.ids[:length]
            masks[row, :length] = 1
            if item.type_ids:
                types[row, :length] = item.type_ids[:length]
        return ids, masks, types, token_count

    def encode_pairs(self, pairs: list[tuple[str, str]]) -> tuple[Any, Any, Any, int]:
        np, _, _ = _load_model_dependencies()
        encoded = [self.tokenizer.encode(query, document) for query, document in pairs]
        width = min(self.max_length, max((len(item.ids) for item in encoded), default=1))
        ids = np.full((len(encoded), width), self.pad_id, dtype=np.int64)
        masks = np.zeros((len(encoded), width), dtype=np.int64)
        types = np.zeros((len(encoded), width), dtype=np.int64)
        token_count = 0
        for row, item in enumerate(encoded):
            length = min(width, len(item.ids))
            token_count += length
            ids[row, :length] = item.ids[:length]
            masks[row, :length] = 1
            if item.type_ids:
                types[row, :length] = item.type_ids[:length]
        return ids, masks, types, token_count


class DenseEncoder:
    def __init__(self, *, model_path: str, tokenizer_path: str, max_length: int = 256) -> None:
        np, ort, _ = _load_model_dependencies()
        self.np = np
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.tokenizer = _OnnxTokenizer(tokenizer_path, max_length=max_length)
        self.output_name = self.session.get_outputs()[0].name

    def encode(self, texts: list[str]) -> tuple[Any, int]:
        ids, masks, types, token_count = self.tokenizer.encode_texts(texts)
        values = self.session.run([self.output_name], {
            "input_ids": ids,
            "attention_mask": masks,
            "token_type_ids": types,
        })[0]
        weights = masks.astype("float32")[:, :, None]
        pooled = (values * weights).sum(axis=1) / self.np.clip(weights.sum(axis=1), 1e-9, None)
        norms = self.np.linalg.norm(pooled, axis=1, keepdims=True)
        return pooled / self.np.clip(norms, 1e-9, None), token_count


class CrossEncoderReranker:
    def __init__(self, *, model_path: str, tokenizer_path: str, max_length: int = 256) -> None:
        _, ort, _ = _load_model_dependencies()
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.tokenizer = _OnnxTokenizer(tokenizer_path, max_length=max_length)
        self.output_name = self.session.get_outputs()[0].name

    def score(self, query: str, documents: list[str]) -> tuple[list[float], int]:
        if not documents:
            return [], 0
        pairs = [(query, document) for document in documents]
        ids, masks, types, token_count = self.tokenizer.encode_pairs(pairs)
        values = self.session.run([self.output_name], {
            "input_ids": ids,
            "attention_mask": masks,
            "token_type_ids": types,
        })[0]
        return [float(value) for value in values.reshape(-1)], token_count


def cosine_scores(query_vector: Any, document_vectors: Any, document_ids: list[str]) -> dict[str, float]:
    values = document_vectors @ query_vector
    return {document_id: float(values[index]) for index, document_id in enumerate(document_ids)}


def reciprocal_rank_fusion(rankings: Iterable[list[str]], *, k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, document_id in enumerate(ranking, 1):
            scores[document_id] = scores.get(document_id, 0.0) + 1.0 / (k + rank)
    return scores


def explicit_patent_id_tokens(text: str) -> list[str]:
    return re.findall(r"\b(?:US|EP|WO)\s*\d{4,14}\s*[A-Z]\d?\b", text.upper())


def mask_explicit_patent_ids(text: str) -> str:
    return re.sub(r"\b(?:US|EP|WO)\s*\d{4,14}\s*[A-Z]\d?\b", "[PATENT-ID]", text, flags=re.IGNORECASE)


class SharedRetriever:
    """Shared lexical, dense and reranker components used by B1/B2/B3."""

    def __init__(self, patents: list[PatentRecord], *, encoder: DenseEncoder, reranker: CrossEncoderReranker) -> None:
        self.patents = patents
        self.by_id = {patent.patent_id_canonical: patent for patent in patents}
        self.lexical = BM25Index(patents)
        self.encoder = encoder
        self.reranker = reranker
        self.document_ids = [patent.patent_id_canonical for patent in patents]
        self.document_vectors, self.index_tokens = encoder.encode([patent.text for patent in patents])

    def dense_search(self, query: str, *, limit: int) -> tuple[list[dict[str, Any]], int]:
        query_vector, query_tokens = self.encoder.encode([query])
        scores = cosine_scores(query_vector[0], self.document_vectors, self.document_ids)
        return [
            {"patent_id_canonical": patent_id, "score": score, "rank": rank}
            for rank, (patent_id, score) in enumerate(sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit], 1)
        ], query_tokens

    def rerank(self, query: str, candidate_ids: list[str]) -> tuple[list[dict[str, Any]], int]:
        documents = [self.by_id[patent_id].text for patent_id in candidate_ids]
        scores, token_count = self.reranker.score(query, documents)
        rows = [
            {"patent_id_canonical": patent_id, "score": score, "rank": rank}
            for rank, (patent_id, score) in enumerate(sorted(zip(candidate_ids, scores), key=lambda item: (-item[1], item[0])), 1)
        ]
        return rows, token_count

    def fixed_bundle(self, query: str, *, candidate_depth: int, rerank_depth: int) -> dict[str, Any]:
        started = perf_counter()
        cpu_started = process_time()
        lexical = self.lexical.search(query, limit=candidate_depth)
        dense, dense_tokens = self.dense_search(query, limit=candidate_depth)
        lexical_ids = [row["patent_id_canonical"] for row in lexical]
        dense_ids = [row["patent_id_canonical"] for row in dense]
        fused_scores = reciprocal_rank_fusion([lexical_ids, dense_ids])
        fused_ids = _ranked_ids(fused_scores, limit=rerank_depth)
        reranked, rerank_tokens = self.rerank(query, fused_ids)
        lexical_top = set(lexical_ids[:5])
        dense_top = set(dense_ids[:5])
        disagreement = 1.0 - len(lexical_top & dense_top) / max(len(lexical_top | dense_top), 1)
        return {
            "query": query,
            "query_hash": query_hash(query),
            "lexical": lexical,
            "dense": dense,
            "fusion": [{"patent_id_canonical": pid, "score": fused_scores[pid], "rank": rank} for rank, pid in enumerate(fused_ids, 1)],
            "reranked": reranked,
            "resources": {
                "lexical_candidates": len(lexical),
                "dense_candidates": len(dense),
                "fusion_candidates": len(fused_ids),
                "rerank_pairs": len(fused_ids),
                "query_calls": 1,
                "returned_candidates": len(fused_ids),
                "embedding_query_tokens": dense_tokens,
                "rerank_tokens": rerank_tokens,
                "wall_seconds": perf_counter() - started,
                "cpu_seconds": process_time() - cpu_started,
            },
            "observables": {
                "lexical_dense_top5_jaccard": len(lexical_top & dense_top) / max(len(lexical_top | dense_top), 1),
                "lexical_dense_disagreement": disagreement,
            },
        }


def final_ranking(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    return list(bundle["reranked"])


def combine_reranked_bundles(bundles: list[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    fused = reciprocal_rank_fusion([[row["patent_id_canonical"] for row in bundle["reranked"]] for bundle in bundles])
    return [{"patent_id_canonical": patent_id, "score": score, "rank": rank} for rank, (patent_id, score) in enumerate(sorted(fused.items(), key=lambda item: (-item[1], item[0]))[:limit], 1)]


def bundle_resources(bundles: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for bundle in bundles:
        for key, value in bundle["resources"].items():
            totals[key] = totals.get(key, 0.0) + float(value)
    return totals


def stable_json_hash(value: Any) -> str:
    return content_hash(value)
