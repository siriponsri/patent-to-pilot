"""Server-owned vector retrieval binding for loopback HealthTech jobs."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from patent_to_pilot.evaluation.healthtech.vector_artifacts import (
    PrecomputedVectorRetriever,
    VectorArtifactError,
    VectorBundle,
    load_vector_bundle,
    read_runtime_text,
    sha256_file,
)
from patent_to_pilot.healthtech.contracts import canonical_patent_id
from patent_to_pilot.healthtech.engine import DossierInput


CONFIG_FORMAT = "ht-http-vector-config-v1"
_COMPATIBLE_CONFIG_KEYS = (
    "backend",
    "encoder_kind",
    "max_length",
    "representation",
    "dtype",
    "norm_policy",
    "patembed_prompt_name",
    "e5_prefix_policy",
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VectorArtifactError(f"vector HTTP config is unreadable: {path}") from exc
    if not isinstance(value, dict):
        raise VectorArtifactError("vector HTTP config must be a JSON object")
    return value


def _validate_bundle_pair(corpus: VectorBundle, queries: VectorBundle) -> None:
    corpus_model = corpus.manifest.get("model", {})
    query_model = queries.manifest.get("model", {})
    if corpus_model != query_model:
        raise VectorArtifactError("corpus and query bundles use different model bindings")
    corpus_config = corpus.manifest.get("config", {})
    query_config = queries.manifest.get("config", {})
    for key in _COMPATIBLE_CONFIG_KEYS:
        if corpus_config.get(key) != query_config.get(key):
            raise VectorArtifactError(f"corpus and query vector configs disagree on {key}")
    if corpus_config.get("role") != "passage" or query_config.get("role") != "query":
        raise VectorArtifactError("corpus/query vector roles must be passage/query")
    if corpus.dimension != queries.dimension:
        raise VectorArtifactError("corpus/query vector dimensions disagree")


class _FixedQueryEncoder:
    """Return one precomputed query vector only for its exact bound text."""

    def __init__(self, vector: Any, expected_text: str):
        self.vector = vector
        self.expected_text = expected_text

    def encode(self, texts: list[str]) -> tuple[Any, int]:
        if any(text != self.expected_text for text in texts):
            raise VectorArtifactError("query text is not bound to the imported fixed vector")
        return self.vector.reshape((1, -1)).repeat(len(texts), axis=0), 0


@dataclass(frozen=True)
class ConfiguredVectorSearch:
    """Validate and expose a private, server-owned vector bundle pair."""

    corpus_bundle: VectorBundle
    query_bundle: VectorBundle
    query_rows: Mapping[str, Any]
    corpus_document_ids: frozenset[str]
    config_path: Path
    config_sha256: str
    corpus_runtime_sha256: str | None
    query_runtime_sha256: str

    @classmethod
    def from_config(cls, path: str | Path) -> "ConfiguredVectorSearch":
        config_path = Path(path).resolve()
        config = _read_json(config_path)
        if config.get("format") != CONFIG_FORMAT:
            raise VectorArtifactError("unsupported vector HTTP config format")
        corpus_path = Path(str(config.get("corpus_bundle", ""))).resolve()
        query_path = Path(str(config.get("query_bundle", ""))).resolve()
        query_runtime_path = Path(str(config.get("query_runtime", ""))).resolve()
        corpus_runtime_value = config.get("corpus_runtime")
        corpus_runtime_path = Path(str(corpus_runtime_value)).resolve() if corpus_runtime_value else None
        if not corpus_path.is_dir() or not query_path.is_dir() or not query_runtime_path.is_file():
            raise VectorArtifactError("vector HTTP config references missing bundle/runtime paths")
        corpus_bundle = load_vector_bundle(corpus_path)
        query_bundle = load_vector_bundle(query_path)
        _validate_bundle_pair(corpus_bundle, query_bundle)
        query_rows = read_runtime_text(query_runtime_path)
        if list(query_bundle.document_ids) != [row.document_id for row in query_rows]:
            raise VectorArtifactError("query vector order does not match runtime query order")
        query_by_id = {row.document_id: row for row in query_rows}
        if len(query_by_id) != len(query_rows):
            raise VectorArtifactError("runtime query IDs are duplicated")
        corpus_document_ids = frozenset(corpus_bundle.document_ids)
        if corpus_runtime_path is not None:
            if not corpus_runtime_path.is_file():
                raise VectorArtifactError("vector HTTP config references a missing corpus runtime")
            corpus_rows = read_runtime_text(corpus_runtime_path)
            if [row.document_id for row in corpus_rows] != list(corpus_bundle.document_ids):
                raise VectorArtifactError("corpus vector order does not match runtime corpus order")
        expected_model = config.get("model")
        if expected_model is not None and expected_model != corpus_bundle.manifest.get("model"):
            raise VectorArtifactError("vector HTTP config model binding does not match bundle")
        expected_query_ids = config.get("query_ids")
        if expected_query_ids is not None and list(expected_query_ids) != list(query_bundle.document_ids):
            raise VectorArtifactError("vector HTTP config query_ids do not match query bundle")
        return cls(
            corpus_bundle=corpus_bundle,
            query_bundle=query_bundle,
            query_rows=query_by_id,
            corpus_document_ids=corpus_document_ids,
            config_path=config_path,
            config_sha256=sha256_file(config_path),
            corpus_runtime_sha256=(None if corpus_runtime_path is None else sha256_file(corpus_runtime_path)),
            query_runtime_sha256=sha256_file(query_runtime_path),
        )

    def validate_input(self, data: DossierInput) -> None:
        query_id = data.query.query_id
        row = self.query_rows.get(query_id)
        if row is None:
            raise VectorArtifactError(f"query_id is not present in the configured query runtime: {query_id}")
        if _sha256_text(data.query.technical_description) != row.text_sha256:
            raise VectorArtifactError("query technical_description does not match the imported fixed query vector")
        input_ids = frozenset(canonical_patent_id(item.patent_id) for item in data.patents)
        if input_ids != self.corpus_document_ids:
            raise VectorArtifactError("DossierInput patent IDs do not match the configured vector corpus")

    def for_input(self, data: DossierInput) -> PrecomputedVectorRetriever:
        self.validate_input(data)
        row = self.query_rows[data.query.query_id]
        index = list(self.query_bundle.document_ids).index(row.document_id)
        vector_count = 0
        vector = None
        for shard in self.query_bundle.vectors:
            if index < vector_count + len(shard):
                vector = shard[index - vector_count]
                break
            vector_count += len(shard)
        if vector is None:
            raise VectorArtifactError("query vector row is missing from the imported bundle")
        return PrecomputedVectorRetriever(
            self.corpus_bundle,
            query_encoder=_FixedQueryEncoder(vector, data.query.technical_description),
        )

    def describe(self) -> dict[str, Any]:
        model = self.corpus_bundle.manifest.get("model", {})
        return {
            "id": "local-vector",
            "label": f"Local vector engine ({model.get('model_id', 'unknown')})",
            "available": True,
            "model": model.get("model_id"),
            "revision": model.get("revision"),
            "encoder_kind": self.corpus_bundle.manifest.get("config", {}).get("encoder_kind"),
            "corpus_rows": self.corpus_bundle.manifest.get("row_count"),
            "query_ids": sorted(self.query_rows),
            "bundle_manifest_sha256": sha256_file(self.corpus_bundle.root / "manifest.json"),
            "query_bundle_manifest_sha256": sha256_file(self.query_bundle.root / "manifest.json"),
            "config_sha256": self.config_sha256,
            "billing_status": "not_billable_local",
            "actual_usd": 0.0,
            "reserved_usd": 0.0,
            "unknown_usd": 0.0,
            "resource_usage": "measured_local_resources",
        }
