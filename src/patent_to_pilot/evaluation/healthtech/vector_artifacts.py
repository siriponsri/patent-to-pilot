"""Portable, resumable vector artifacts for HealthTech runtime retrieval.

The bundle format is intentionally task-neutral: it carries runtime text
identity and source provenance, never qrels or evaluator labels.  Completed
bundles are immutable from the importer's perspective; partial files are
accepted only by the encoder resume path and rejected by the importer.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

from patent_to_pilot.healthtech.contracts import content_hash


FORMAT = "ht-vector-bundle-v1"
RUNTIME_FORMAT = "ht-runtime-text-v1"
_FORBIDDEN_KEYS = {
    "references", "known_links", "disclosed_by", "evaluator", "gold",
    "qrels", "split", "family_label", "relevance", "adjudication",
}


class VectorArtifactError(ValueError):
    """Raised when a runtime export or vector bundle violates its contract."""


class Encoder(Protocol):
    def encode(self, texts: list[str]) -> tuple[Any, int]: ...


def _numpy():
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - optional dependency boundary
        raise RuntimeError("vector artifacts require numpy") from exc
    return np


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    _atomic_write_bytes(path, encoded)


def _atomic_write_npy(path: Path, values: Any) -> None:
    np = _numpy()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("wb") as handle:
        np.save(handle, values, allow_pickle=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _stable_id(dataset_id: str, raw_id: str) -> str:
    dataset = dataset_id.strip()
    value = raw_id.strip()
    if not dataset or not value:
        raise VectorArtifactError("dataset and row IDs must be nonempty")
    prefix = dataset + ":"
    return value if value.startswith(prefix) else prefix + value


def _ordered_hash(values: Iterable[str]) -> str:
    return _sha256_bytes(("\n".join(values) + "\n").encode("utf-8"))


@dataclass(frozen=True)
class RuntimeTextRow:
    item_id: str
    document_id: str
    text: str
    text_sha256: str
    source_id: str
    source_revision: str

    @classmethod
    def from_mapping(
        cls,
        row: Mapping[str, Any],
        *,
        dataset_id: str,
        source_revision: str,
        text_field: str = "text",
        id_field: str = "item_id",
    ) -> "RuntimeTextRow":
        leaked = _FORBIDDEN_KEYS.intersection(row)
        if leaked:
            raise VectorArtifactError(f"runtime row exposes evaluator fields: {sorted(leaked)}")
        raw_id = row.get(id_field, row.get("document_id"))
        if raw_id is None:
            raise VectorArtifactError(f"runtime row requires {id_field!r} or document_id")
        text = row.get(text_field)
        if not isinstance(text, str) or not text.strip():
            raise VectorArtifactError("runtime text must be a nonempty string")
        document_id = str(row.get("document_id", raw_id)).strip()
        if not document_id:
            raise VectorArtifactError("document_id must be nonempty")
        source_id = str(row.get("source_id", dataset_id)).strip()
        revision = str(row.get("source_revision", source_revision)).strip()
        if not source_id or not revision:
            raise VectorArtifactError("source identity and revision must be nonempty")
        return cls(
            item_id=_stable_id(dataset_id, str(raw_id)),
            document_id=document_id,
            text=text,
            text_sha256=_sha256_bytes(text.encode("utf-8")),
            source_id=source_id,
            source_revision=revision,
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "item_id": self.item_id,
            "document_id": self.document_id,
            "text": self.text,
            "text_sha256": self.text_sha256,
            "source_id": self.source_id,
            "source_revision": self.source_revision,
        }


def export_runtime_text(
    rows: Iterable[Mapping[str, Any]],
    destination: str | Path,
    *,
    dataset_id: str,
    source_revision: str,
    representation: str,
    text_field: str = "text",
    id_field: str = "item_id",
) -> dict[str, Any]:
    """Write ordered runtime-only JSONL and return its binding manifest."""
    parsed = [
        RuntimeTextRow.from_mapping(
            row,
            dataset_id=dataset_id,
            source_revision=source_revision,
            text_field=text_field,
            id_field=id_field,
        )
        for row in rows
    ]
    parsed.sort(key=lambda row: row.item_id)
    item_ids = [row.item_id for row in parsed]
    if len(item_ids) != len(set(item_ids)):
        raise VectorArtifactError("runtime export contains duplicate item IDs")
    document_ids = [row.document_id for row in parsed]
    if len(document_ids) != len(set(document_ids)):
        raise VectorArtifactError("runtime export contains duplicate document IDs")
    destination = Path(destination)
    payload = b"".join(
        (json.dumps(row.as_dict(), ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in parsed
    )
    _atomic_write_bytes(destination, payload)
    return {
        "format": RUNTIME_FORMAT,
        "dataset_id": dataset_id,
        "source_revision": source_revision,
        "representation": representation,
        "row_count": len(parsed),
        "item_order_sha256": _ordered_hash(item_ids),
        "document_order_sha256": _ordered_hash(document_ids),
        "text_hashes_sha256": _ordered_hash(row.text_sha256 for row in parsed),
        "sha256": sha256_file(destination),
        "path": destination.name,
    }


def read_runtime_text(path: str | Path) -> list[RuntimeTextRow]:
    """Read and validate an ordered runtime-only JSONL export."""
    rows: list[RuntimeTextRow] = []
    item_ids: set[str] = set()
    document_ids: set[str] = set()
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise VectorArtifactError(f"invalid runtime JSONL at line {line_number}") from exc
            if not isinstance(value, dict):
                raise VectorArtifactError(f"runtime row at line {line_number} is not an object")
            leaked = _FORBIDDEN_KEYS.intersection(value)
            if leaked:
                raise VectorArtifactError(f"runtime row exposes evaluator fields: {sorted(leaked)}")
            text = value.get("text")
            if not isinstance(text, str) or _sha256_bytes(text.encode("utf-8")) != value.get("text_sha256"):
                raise VectorArtifactError(f"runtime text hash mismatch at line {line_number}")
            row = RuntimeTextRow(
                item_id=str(value.get("item_id", "")),
                document_id=str(value.get("document_id", "")),
                text=text,
                text_sha256=str(value.get("text_sha256", "")),
                source_id=str(value.get("source_id", "")),
                source_revision=str(value.get("source_revision", "")),
            )
            if not row.item_id or not row.document_id or not row.source_id or not row.source_revision:
                raise VectorArtifactError(f"runtime row missing identity at line {line_number}")
            if row.item_id in item_ids or row.document_id in document_ids:
                raise VectorArtifactError("runtime export contains duplicate IDs")
            item_ids.add(row.item_id)
            document_ids.add(row.document_id)
            rows.append(row)
    return rows


def _parent_binding(input_path: Path, rows: list[RuntimeTextRow], model: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    item_ids = [row.item_id for row in rows]
    document_ids = [row.document_id for row in rows]
    return {
        "format": FORMAT,
        "status": "partial",
        "input_sha256": sha256_file(input_path),
        "row_count": len(rows),
        "item_order_sha256": _ordered_hash(item_ids),
        "document_order_sha256": _ordered_hash(document_ids),
        "text_hashes_sha256": _ordered_hash(row.text_sha256 for row in rows),
        "model": dict(model),
        "model_sha256": content_hash(model),
        "config": dict(config),
        "config_sha256": content_hash(config),
        "dtype": "<f4",
        "endianness": "little",
        "norm_policy": config.get("norm_policy", "none"),
    }


def _validate_vectors(values: Any, *, expected_rows: int, dimension: int | None = None) -> Any:
    np = _numpy()
    array = np.asarray(values)
    if array.dtype != np.dtype("<f4"):
        raise VectorArtifactError(f"vectors must be little-endian float32, got {array.dtype.str}")
    if array.ndim != 2 or array.shape[0] != expected_rows or array.shape[1] < 1:
        raise VectorArtifactError(f"vector shape mismatch: {array.shape}")
    if dimension is not None and array.shape[1] != dimension:
        raise VectorArtifactError("vector dimension mismatch")
    if not bool(np.isfinite(array).all()):
        raise VectorArtifactError("vectors contain non-finite values")
    return array


def _safe_child(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or len(path.parts) != 1 or path.name in {"", ".", ".."}:
        raise VectorArtifactError(f"unsafe bundle path: {relative!r}")
    resolved = (root / path).resolve()
    if resolved.parent != root.resolve():
        raise VectorArtifactError(f"bundle path escapes root: {relative!r}")
    return resolved


def _write_ids(path: Path, rows: list[RuntimeTextRow]) -> None:
    payload = b"".join(
        (json.dumps({"item_id": row.item_id, "document_id": row.document_id}, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )
    _atomic_write_bytes(path, payload)


def _read_ids(path: Path) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict) or not value.get("item_id") or not value.get("document_id"):
                raise VectorArtifactError(f"invalid shard IDs at line {line_number}")
            result.append({"item_id": str(value["item_id"]), "document_id": str(value["document_id"])})
    return result


def _shard_binding(root: Path, shard: Mapping[str, Any], parent: Mapping[str, Any]) -> tuple[list[dict[str, str]], Any]:
    np = _numpy()
    ids_path = _safe_child(root, str(shard["ids_file"]))
    vectors_path = _safe_child(root, str(shard["vectors_file"]))
    manifest_path = _safe_child(root, str(shard["manifest_file"]))
    if not ids_path.is_file() or not vectors_path.is_file() or not manifest_path.is_file():
        raise VectorArtifactError("bundle shard is missing an artifact")
    ids = _read_ids(ids_path)
    if sha256_file(ids_path) != shard["ids_sha256"]:
        raise VectorArtifactError("shard IDs hash mismatch")
    if sha256_file(vectors_path) != shard["vectors_sha256"]:
        raise VectorArtifactError("shard vector hash mismatch")
    values = np.load(vectors_path, mmap_mode="r", allow_pickle=False)
    values = _validate_vectors(values, expected_rows=len(ids), dimension=int(parent["dimension"]))
    child = json.loads(manifest_path.read_text(encoding="utf-8"))
    if child != dict(shard):
        raise VectorArtifactError("shard manifest mismatch")
    if int(shard["row_count"]) != len(ids) or list(shard["shape"]) != list(values.shape):
        raise VectorArtifactError("shard row or shape mismatch")
    return ids, values


@dataclass(frozen=True)
class VectorBundle:
    item_ids: tuple[str, ...]
    document_ids: tuple[str, ...]
    vectors: tuple[Any, ...]
    manifest: Mapping[str, Any]
    root: Path

    @property
    def dimension(self) -> int:
        return int(self.manifest["dimension"])

    def search(self, query_vector: Any, *, limit: int) -> list[dict[str, Any]]:
        np = _numpy()
        if type(limit) is not int or limit < 1:
            raise ValueError("limit must be a positive integer")
        query = np.asarray(query_vector)
        if query.dtype != np.dtype("<f4"):
            query = query.astype("<f4")
        if query.shape != (self.dimension,):
            raise VectorArtifactError("query vector shape mismatch")
        if not bool(np.isfinite(query).all()):
            raise VectorArtifactError("query vector contains non-finite values")
        scored: list[tuple[float, str, str]] = []
        offset = 0
        for values in self.vectors:
            scores = values @ query
            for local, score in enumerate(scores.tolist()):
                index = offset + local
                scored.append((float(score), self.document_ids[index], self.item_ids[index]))
            offset += len(values)
        scored.sort(key=lambda row: (-row[0], row[1], row[2]))
        return [
            {"item_id": item_id, "document_id": document_id, "score": score, "rank": rank}
            for rank, (score, document_id, item_id) in enumerate(scored[:limit], 1)
        ]


def load_vector_bundle(bundle_dir: str | Path) -> VectorBundle:
    """Validate and load a completed bundle for exact NumPy/memmap search."""
    np = _numpy()
    root = Path(bundle_dir).resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise VectorArtifactError("bundle manifest is missing")
    if list(root.glob("*.partial")) or list(root.glob("*.partial.*")) or (root / "manifest.partial.json").exists():
        raise VectorArtifactError("partial bundle artifacts are not importable")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != FORMAT or manifest.get("status") != "complete":
        raise VectorArtifactError("bundle manifest is not a completed vector bundle")
    if not isinstance(manifest.get("shards"), list) or not manifest["shards"]:
        raise VectorArtifactError("bundle must contain shards")
    dimension = int(manifest.get("dimension", 0))
    if dimension < 1 or manifest.get("dtype") != "<f4" or manifest.get("endianness") != "little":
        raise VectorArtifactError("bundle dtype/endianness/dimension contract is invalid")
    if manifest.get("model_sha256") != content_hash(manifest.get("model", {})):
        raise VectorArtifactError("bundle model binding hash mismatch")
    if manifest.get("config_sha256") != content_hash(manifest.get("config", {})):
        raise VectorArtifactError("bundle config binding hash mismatch")
    item_ids: list[str] = []
    document_ids: list[str] = []
    arrays: list[Any] = []
    expected_start = 0
    for shard in manifest["shards"]:
        if not isinstance(shard, dict):
            raise VectorArtifactError("invalid shard manifest")
        if int(shard.get("row_start", -1)) != expected_start:
            raise VectorArtifactError("shard row order has a gap or overlap")
        ids, values = _shard_binding(root, shard, {**manifest, "dimension": dimension})
        item_ids.extend(row["item_id"] for row in ids)
        document_ids.extend(row["document_id"] for row in ids)
        arrays.append(values)
        expected_start += len(ids)
    if len(item_ids) != int(manifest["row_count"]) or len(document_ids) != int(manifest["row_count"]):
        raise VectorArtifactError("bundle row count mismatch")
    if len(item_ids) != len(set(item_ids)) or len(document_ids) != len(set(document_ids)):
        raise VectorArtifactError("bundle contains duplicate IDs")
    if _ordered_hash(item_ids) != manifest["item_order_sha256"]:
        raise VectorArtifactError("bundle item order hash mismatch")
    if _ordered_hash(document_ids) != manifest["document_order_sha256"]:
        raise VectorArtifactError("bundle document order hash mismatch")
    if int(sum(len(values) for values in arrays)) != int(manifest["row_count"]):
        raise VectorArtifactError("bundle vector count mismatch")
    return VectorBundle(tuple(item_ids), tuple(document_ids), tuple(arrays), manifest, root)


def _verify_existing_shard(root: Path, shard: Mapping[str, Any], parent: Mapping[str, Any]) -> None:
    bindings = {
        "parent_input_sha256": "input_sha256",
        "model_sha256": "model_sha256",
        "config_sha256": "config_sha256",
    }
    for shard_key, parent_key in bindings.items():
        if shard.get(shard_key) != parent.get(parent_key):
            raise VectorArtifactError(f"existing shard binding mismatch: {shard_key}")
    _shard_binding(root, shard, parent)


def encode_vector_shards(
    input_path: str | Path,
    output_dir: str | Path,
    encoder: Encoder,
    *,
    model: Mapping[str, Any],
    config: Mapping[str, Any],
    batch_size: int = 32,
    shard_size: int = 5000,
    stop_after_shards: int | None = None,
) -> dict[str, Any]:
    """Encode runtime JSONL into resumable, atomically published shards."""
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be positive")
    if type(shard_size) is not int or shard_size < 1 or shard_size > 5000:
        raise ValueError("shard_size must be between 1 and 5000")
    input_path = Path(input_path).resolve()
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    rows = read_runtime_text(input_path)
    parent = _parent_binding(input_path, rows, model, config)
    final_manifest_path = root / "manifest.json"
    partial_manifest_path = root / "manifest.partial.json"
    if final_manifest_path.exists():
        existing = json.loads(final_manifest_path.read_text(encoding="utf-8"))
        if existing.get("status") != "complete":
            raise VectorArtifactError("existing final manifest is not complete")
        for key in ("input_sha256", "row_count", "item_order_sha256", "document_order_sha256", "text_hashes_sha256", "model_sha256", "config_sha256"):
            if existing.get(key) != parent.get(key):
                raise VectorArtifactError(f"existing bundle binding mismatch: {key}")
        load_vector_bundle(root)
        return existing
    if partial_manifest_path.exists():
        existing = json.loads(partial_manifest_path.read_text(encoding="utf-8"))
        for key in ("input_sha256", "row_count", "item_order_sha256", "document_order_sha256", "text_hashes_sha256", "model_sha256", "config_sha256"):
            if existing.get(key) != parent.get(key):
                raise VectorArtifactError(f"partial bundle binding mismatch: {key}")
        shard_records = list(existing.get("shards", []))
    else:
        shard_records = []
        _atomic_write_json(partial_manifest_path, parent)
    completed = {int(shard["shard_index"]): shard for shard in shard_records}
    dimension: int | None = int(parent["dimension"]) if "dimension" in parent else None
    published = 0
    for shard_index, start in enumerate(range(0, len(rows), shard_size)):
        end = min(start + shard_size, len(rows))
        existing = completed.get(shard_index)
        if existing is not None:
            _verify_existing_shard(root, existing, {**parent, "dimension": existing["shape"][1]})
            if dimension is None:
                dimension = int(existing["shape"][1])
            elif dimension != int(existing["shape"][1]):
                raise VectorArtifactError("existing shard dimensions disagree")
            published += 1
            continue
        shard_rows = rows[start:end]
        batches: list[Any] = []
        for batch_start in range(0, len(shard_rows), batch_size):
            batch_rows = shard_rows[batch_start:batch_start + batch_size]
            values, _ = encoder.encode([row.text for row in batch_rows])
            values = _validate_vectors(values, expected_rows=len(batch_rows), dimension=dimension)
            if dimension is None:
                dimension = int(values.shape[1])
            batches.append(values)
        np = _numpy()
        values = _validate_vectors(np.concatenate(batches, axis=0), expected_rows=len(shard_rows), dimension=dimension)
        vector_name = f"shard-{shard_index:05d}.npy"
        ids_name = f"shard-{shard_index:05d}.ids.jsonl"
        manifest_name = f"shard-{shard_index:05d}.json"
        _atomic_write_npy(root / vector_name, values)
        _write_ids(root / ids_name, shard_rows)
        record = {
            "shard_index": shard_index,
            "row_start": start,
            "row_count": len(shard_rows),
            "ids_file": ids_name,
            "vectors_file": vector_name,
            "manifest_file": manifest_name,
            "ids_sha256": sha256_file(root / ids_name),
            "vectors_sha256": sha256_file(root / vector_name),
            "shape": list(values.shape),
            "dtype": values.dtype.str,
            "endianness": "little",
            "parent_input_sha256": parent["input_sha256"],
            "model_sha256": parent["model_sha256"],
            "config_sha256": parent["config_sha256"],
            "item_order_sha256": _ordered_hash(row.item_id for row in shard_rows),
            "document_order_sha256": _ordered_hash(row.document_id for row in shard_rows),
            "text_hashes_sha256": _ordered_hash(row.text_sha256 for row in shard_rows),
        }
        _atomic_write_json(root / manifest_name, record)
        completed[shard_index] = record
        shard_records = [completed[index] for index in sorted(completed)]
        partial = {**parent, "dimension": dimension, "shards": shard_records}
        _atomic_write_json(partial_manifest_path, partial)
        published += 1
        if stop_after_shards is not None and published >= stop_after_shards:
            raise RuntimeError("injected interruption after shard publication")
    if dimension is None:
        raise VectorArtifactError("cannot publish an empty vector bundle")
    complete = {
        **parent,
        "status": "complete",
        "dimension": dimension,
        "shards": [completed[index] for index in sorted(completed)],
    }
    _atomic_write_json(final_manifest_path, complete)
    partial_manifest_path.unlink(missing_ok=True)
    return complete


class PrecomputedVectorRetriever:
    """Adapt a validated vector bundle to the shared retrieval contract."""

    def __init__(self, bundle: VectorBundle, *, query_encoder: Encoder) -> None:
        self.bundle = bundle
        self.query_encoder = query_encoder

    def search(self, query: str, *, limit: int) -> tuple[list[dict[str, Any]], int]:
        values, token_count = self.query_encoder.encode([query])
        np = _numpy()
        values = np.asarray(values)
        if values.shape != (1, self.bundle.dimension):
            raise VectorArtifactError("query encoder dimension does not match vector bundle")
        rows = self.bundle.search(values[0], limit=limit)
        return [
            {
                "patent_id_canonical": row["document_id"],
                "score": row["score"],
                "rank": row["rank"],
                "item_id": row["item_id"],
            }
            for row in rows
        ], int(token_count)
