"""Bounded local staging for an authorized semantic-judgment source."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Mapping

from patent_to_pilot.evaluation.healthtech.source_authorization import (
    SourceAuthorizationError,
    validate_semantic_source_authorization,
)


FORMAT = "ht-semantic-source-acquisition-receipt-v1"
HEX64 = set("0123456789abcdef")


class SourceAcquisitionError(ValueError):
    """Raised when an authorized local source cannot be staged safely."""


def _require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in HEX64 for char in value):
        raise SourceAcquisitionError(f"{field} must be a lowercase SHA-256")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_inventory_hash(entries: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"ht-semantic-source-snapshot-v1\n")
    for entry in entries:
        line = json.dumps(
            [entry["relative_path"], entry["bytes"], entry["sha256"]],
            ensure_ascii=True,
            separators=(",", ":"),
        )
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def source_snapshot_sha256(source_root: str | Path) -> str:
    """Return the deterministic hash used by this acquisition boundary."""
    return _inventory(source_root)[1]


def _inventory(source_root: str | Path) -> tuple[list[dict[str, Any]], str]:
    root = Path(source_root)
    if not root.exists():
        raise SourceAcquisitionError("source root does not exist")
    root = root.resolve()
    if root.is_symlink():
        raise SourceAcquisitionError("source root symlinks are not allowed")

    if root.is_file():
        candidates = [root]
        base = root.parent
    elif root.is_dir():
        candidates = sorted(root.rglob("*"), key=lambda path: path.as_posix())
        base = root
    else:
        raise SourceAcquisitionError("source root must be a regular file or directory")

    entries: list[dict[str, Any]] = []
    for path in candidates:
        if path.is_symlink():
            raise SourceAcquisitionError("source symlinks are not allowed")
        if path.is_dir():
            continue
        if not path.is_file():
            raise SourceAcquisitionError("source contains a non-regular file")
        relative = path.name if root.is_file() else path.relative_to(base).as_posix()
        entries.append({
            "source_path": path,
            "relative_path": relative,
            "bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
        })
    if not entries:
        raise SourceAcquisitionError("source contains no regular files")
    return entries, _canonical_inventory_hash(entries)


def _is_within(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SourceAcquisitionError("receipt must be a JSON object")
    return value


def _resume_copy(source: Path, partial: Path, expected_bytes: int) -> None:
    partial.parent.mkdir(parents=True, exist_ok=True)
    existing = partial.stat().st_size if partial.exists() else 0
    if existing > expected_bytes:
        raise SourceAcquisitionError("partial file exceeds the authorized source size")
    if existing:
        with source.open("rb") as source_handle, partial.open("rb") as partial_handle:
            remaining = existing
            while remaining:
                chunk_size = min(1024 * 1024, remaining)
                if source_handle.read(chunk_size) != partial_handle.read(chunk_size):
                    raise SourceAcquisitionError("partial file prefix does not match source")
                remaining -= chunk_size
    with source.open("rb") as source_handle, partial.open("ab") as output:
        source_handle.seek(existing)
        shutil.copyfileobj(source_handle, output, length=1024 * 1024)


def stage_authorized_semantic_source(
    source_root: str | Path,
    destination_root: str | Path,
    authorization_manifest: Mapping[str, Any],
    *,
    authorization_sha256: str,
    receipt_path: str | Path,
) -> dict[str, Any]:
    """Stage a local snapshot under the declared bounds and return its receipt.

    This function is intentionally local-only. It performs no URL fetch, provider
    transfer, rights discovery, or label interpretation.
    """
    try:
        authorization = validate_semantic_source_authorization(dict(authorization_manifest))
    except (SourceAuthorizationError, TypeError) as exc:
        raise SourceAcquisitionError(f"source authorization failed: {exc}") from exc
    authorization_sha256 = _require_sha256(authorization_sha256, "authorization_sha256")

    entries, snapshot_sha256 = _inventory(source_root)
    bounds = authorization["storage_bounds"]
    actual_bytes = sum(entry["bytes"] for entry in entries)
    actual_files = len(entries)
    if actual_bytes != bounds["expected_bytes"]:
        raise SourceAcquisitionError("source byte count does not match authorization")
    if actual_files != bounds["expected_files"]:
        raise SourceAcquisitionError("source file count does not match authorization")
    if actual_bytes > bounds["max_bytes"] or actual_files > bounds["max_files"]:
        raise SourceAcquisitionError("source exceeds authorization bounds")
    if snapshot_sha256 != authorization["source_sha256"]:
        raise SourceAcquisitionError("source snapshot hash does not match authorization")

    source_path = Path(source_root).resolve()
    source_scope = source_path.parent if source_path.is_file() else source_path
    destination = Path(destination_root).resolve()
    if _is_within(source_scope, destination) or _is_within(destination, source_scope):
        raise SourceAcquisitionError("source and destination must not overlap")

    relative_paths = authorization["relative_paths"]
    storage_relpath = Path(relative_paths["storage"])
    raw_relpath = Path(relative_paths["raw"])
    normalized_relpath = Path(relative_paths["normalized"])
    storage_target = (destination / storage_relpath).resolve()
    if not _is_within(destination, storage_target):
        raise SourceAcquisitionError("storage path escapes destination root")
    for label, candidate in (("raw", raw_relpath), ("normalized", normalized_relpath)):
        candidate_path = (destination / candidate).resolve()
        if not _is_within(storage_target, candidate_path):
            raise SourceAcquisitionError(f"{label} path escapes storage root")

    receipt = Path(receipt_path).resolve()
    prior: dict[str, Any] | None = _read_json(receipt) if receipt.exists() else None
    if prior is not None:
        if prior.get("format") != FORMAT:
            raise SourceAcquisitionError("existing receipt format is not supported")
        if prior.get("authorization_manifest_sha256") != authorization_sha256:
            raise SourceAcquisitionError("existing receipt is bound to another authorization manifest")
        if prior.get("source_sha256") != snapshot_sha256:
            raise SourceAcquisitionError("existing receipt is bound to another source snapshot")

    receipt_payload: dict[str, Any] = {
        "format": FORMAT,
        "status": "IN_PROGRESS",
        "source_id": authorization["source_id"],
        "source_revision": authorization["source_revision"],
        "source_sha256": snapshot_sha256,
        "source_digest_mode": "canonical_file_inventory_v1",
        "authorization_manifest_sha256": authorization_sha256,
        "rights_policy_id": authorization["rights_policy_id"],
        "storage_relpath": storage_relpath.as_posix(),
        "raw_relpath": raw_relpath.as_posix(),
        "normalized_relpath": normalized_relpath.as_posix(),
        "expected_bytes": bounds["expected_bytes"],
        "expected_files": bounds["expected_files"],
        "max_bytes": bounds["max_bytes"],
        "max_files": bounds["max_files"],
        "actual_bytes": actual_bytes,
        "actual_files": actual_files,
        "resumable": authorization["resumable"],
        "files": [],
    }
    _write_json_atomic(receipt, receipt_payload)

    completed: list[dict[str, Any]] = []
    try:
        for entry in entries:
            relative = Path(entry["relative_path"])
            destination_file = (storage_target / relative).resolve()
            if not _is_within(storage_target, destination_file):
                raise SourceAcquisitionError("source relative path escapes storage root")
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            status = "staged"
            if destination_file.exists():
                if not destination_file.is_file():
                    raise SourceAcquisitionError("destination path is not a regular file")
                if destination_file.stat().st_size != entry["bytes"] or _sha256_file(destination_file) != entry["sha256"]:
                    raise SourceAcquisitionError("existing destination file does not match source")
                status = "reused"
            else:
                partial = destination_file.with_name(destination_file.name + ".partial")
                _resume_copy(entry["source_path"], partial, entry["bytes"])
                if partial.stat().st_size != entry["bytes"] or _sha256_file(partial) != entry["sha256"]:
                    raise SourceAcquisitionError("staged file failed hash verification")
                os.replace(partial, destination_file)
            completed.append({
                "relative_path": entry["relative_path"],
                "bytes": entry["bytes"],
                "sha256": entry["sha256"],
                "status": status,
            })
            receipt_payload["files"] = completed
            receipt_payload["completed_files"] = len(completed)
            _write_json_atomic(receipt, receipt_payload)
    except SourceAcquisitionError as exc:
        receipt_payload["status"] = "FAILED"
        receipt_payload["error"] = str(exc)
        receipt_payload["files"] = completed
        receipt_payload["completed_files"] = len(completed)
        _write_json_atomic(receipt, receipt_payload)
        raise

    receipt_payload["status"] = "PASS"
    receipt_payload["files"] = completed
    receipt_payload["completed_files"] = len(completed)
    receipt_payload["interpretation"] = (
        "Local staging and integrity verification only; no semantic labels were created or transferred."
    )
    _write_json_atomic(receipt, receipt_payload)
    return receipt_payload
