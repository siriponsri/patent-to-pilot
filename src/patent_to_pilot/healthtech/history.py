"""Local, file-backed dossier versions and source inspection helpers."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping

from patent_to_pilot.healthtech.contracts import DossierVersion


class DossierHistoryError(ValueError):
    """Raised when a local version chain is inconsistent or unsafe to overwrite."""


def _version_path(history_dir: Path, version: int) -> Path:
    return history_dir / f"version-{version:04d}.json"


def save_version(history_dir: str | Path, dossier: DossierVersion) -> Path:
    root = Path(history_dir)
    root.mkdir(parents=True, exist_ok=True)
    destination = _version_path(root, dossier.version)
    payload = dossier.model_dump_json(indent=2) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(destination, flags)
    except FileExistsError as exc:
        raise DossierHistoryError(f"version already exists or concurrent writer won: {destination}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            destination.unlink()
        except FileNotFoundError:
            pass
        raise
    return destination


def load_versions(history_dir: str | Path) -> list[DossierVersion]:
    root = Path(history_dir)
    versions = []
    for path in sorted(root.glob("version-*.json")):
        versions.append(DossierVersion.model_validate_json(path.read_text(encoding="utf-8")))
    if [item.version for item in versions] != list(range(1, len(versions) + 1)):
        raise DossierHistoryError("version files must form a contiguous chain")
    for previous, current in zip(versions, versions[1:]):
        if current.parent_version != previous.version or current.dossier_id != previous.dossier_id:
            raise DossierHistoryError("dossier version chain is not contiguous")
    return versions


def select_version(history_dir: str | Path, version: int | None = None) -> DossierVersion:
    versions = load_versions(history_dir)
    if not versions:
        raise DossierHistoryError("history has no versions")
    if version is None:
        return versions[-1]
    for item in versions:
        if item.version == version:
            return item
    raise DossierHistoryError(f"version not found: {version}")


def append_user_edits(history_dir: str | Path, edits: Mapping[str, str], *, expected_parent_version: int | None = None) -> DossierVersion:
    versions = load_versions(history_dir)
    if not versions:
        raise DossierHistoryError("cannot append edits before saving version 1")
    current = versions[-1]
    if expected_parent_version is not None and current.version != expected_parent_version:
        raise DossierHistoryError(
            f"expected parent version {expected_parent_version}, current version is {current.version}"
        )
    merged = {**current.user_edits, **{str(key): str(value) for key, value in edits.items()}}
    next_version = current.model_copy(update={
        "version": current.version + 1,
        "parent_version": current.version,
        "user_edits": merged,
        "created_at": datetime.now(timezone.utc),
    })
    save_version(history_dir, next_version)
    return next_version


def source_view(dossier: DossierVersion, source_id: str, field: str | None = None) -> dict[str, Any]:
    for source in dossier.sources:
        if source.source.source_id != source_id:
            continue
        payload: Any = source.payload
        if field is not None:
            if not isinstance(payload, dict) or field not in payload:
                raise DossierHistoryError(f"field not available in source {source_id}: {field}")
            payload = {field: payload[field]}
        return {
            "source_id": source.source.source_id,
            "source_type": source.source.source_type,
            "uri": source.source.uri,
            "revision": source.source.version_label,
            "jurisdiction": source.jurisdiction,
            "source_date": str(source.source_date),
            "sha256": source.source.sha256,
            "synthetic": source.synthetic,
            "payload": payload,
        }
    raise DossierHistoryError(f"source not found: {source_id}")


def history_manifest(history_dir: str | Path) -> dict[str, Any]:
    versions = load_versions(history_dir)
    return {
        "dossier_id": versions[-1].dossier_id if versions else None,
        "versions": [{"version": item.version, "parent_version": item.parent_version,
                      "path": _version_path(Path(history_dir), item.version).name,
                      "user_edit_keys": sorted(item.user_edits)} for item in versions],
    }
