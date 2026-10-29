"""Create a typed-rights copy of a legacy local HealthTech cohort.

The migration changes only source-registry policy declarations and the
manifest hash that pins that registry. Runtime, raw, evaluator, and group
artifacts are copied byte-for-byte into a new local output directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(_ROOT / "src"), str(_ROOT)]

from patent_to_pilot.healthtech.contracts import content_hash
from patent_to_pilot.healthtech.rights import load_rights_matrix, select_rights_policy
from scripts.healthtech.fetch_public_device_cohort import _rights_policy_id


class CohortRightsMigrationError(ValueError):
    """Raised when a legacy cohort cannot be migrated safely."""


INTEGRITY_FORMAT = "ht-runtime-integrity-v1"


def _read_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CohortRightsMigrationError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise CohortRightsMigrationError(f"JSON artifact must be an object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CohortRightsMigrationError(f"{label} must be a nonempty relative path")
    relative = PurePosixPath(value.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts or ":" in relative.parts[0]:
        raise CohortRightsMigrationError(f"{label} escapes the cohort root: {value}")
    return relative.as_posix()


def _preflight_source(source: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], int]:
    manifest = _read_object(source / "manifest.json")
    if manifest.get("integrity_format") != INTEGRITY_FORMAT:
        raise CohortRightsMigrationError("source manifest lacks runtime integrity format")

    runtime_path = source / _safe_relative(manifest.get("runtime_path", "runtime.json"), label="runtime_path")
    registry_path = source / _safe_relative(
        manifest.get("source_registry", "source_registry.json"), label="source_registry"
    )
    runtime = _read_object(runtime_path)
    registry = _read_object(registry_path)
    if content_hash(runtime) != manifest.get("runtime_sha256"):
        raise CohortRightsMigrationError("source runtime hash does not match manifest")
    if content_hash(registry) != manifest.get("source_registry_sha256"):
        raise CohortRightsMigrationError("source registry hash does not match manifest")

    raw_files = manifest.get("raw_files")
    if not isinstance(raw_files, list) or not raw_files:
        raise CohortRightsMigrationError("source manifest raw_files must be nonempty")
    seen: set[str] = set()
    for index, item in enumerate(raw_files):
        if not isinstance(item, dict):
            raise CohortRightsMigrationError(f"raw_files[{index}] must be an object")
        relative = _safe_relative(item.get("path"), label=f"raw_files[{index}].path")
        if relative in seen:
            raise CohortRightsMigrationError(f"source manifest repeats raw file: {relative}")
        seen.add(relative)
        path = source / relative
        expected_size = item.get("size_bytes", item.get("bytes"))
        expected_hash = item.get("sha256")
        if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
            raise CohortRightsMigrationError(f"raw_files[{index}] has invalid size")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise CohortRightsMigrationError(f"raw_files[{index}] has invalid SHA-256")
        if not path.is_file():
            raise CohortRightsMigrationError(f"source raw file is missing: {relative}")
        if path.stat().st_size != expected_size or _sha256_file(path) != expected_hash:
            raise CohortRightsMigrationError(f"source raw file hash/size mismatch: {relative}")

    files = list(source.rglob("*"))
    if any(path.is_symlink() for path in files):
        raise CohortRightsMigrationError("source cohort contains a symlink")
    copied_bytes = sum(path.stat().st_size for path in files if path.is_file())
    return manifest, runtime, registry, copied_bytes


def migrate_legacy_cohort_rights(
    source_dir: str | Path,
    output_dir: str | Path,
    *,
    rights_matrix_path: str | Path,
    max_storage_bytes: int = 140_000_000,
    max_file_bytes: int = 30_000_000,
) -> dict[str, Any]:
    """Copy a cohort and bind every source row to a reviewed policy ID."""
    source = Path(source_dir).resolve()
    output = Path(output_dir).resolve()
    if not source.is_dir():
        raise CohortRightsMigrationError(f"source cohort does not exist: {source_dir}")
    if output.exists():
        raise CohortRightsMigrationError(f"output already exists: {output_dir}")
    try:
        output.relative_to(source)
    except ValueError:
        pass
    else:
        raise CohortRightsMigrationError("output must not be inside the source cohort")
    if max_storage_bytes <= 0 or max_file_bytes <= 0:
        raise CohortRightsMigrationError("storage limits must be positive")

    manifest, _runtime, registry, copied_bytes = _preflight_source(source)
    if copied_bytes > max_storage_bytes:
        raise CohortRightsMigrationError("source cohort exceeds the storage bound")
    files = [path for path in source.rglob("*") if path.is_file()]
    if any(path.stat().st_size > max_file_bytes for path in files):
        raise CohortRightsMigrationError("source cohort contains a file above the per-file bound")

    policies = load_rights_matrix(rights_matrix_path)
    rows = registry.get("sources")
    if not isinstance(rows, list) or not rows:
        raise CohortRightsMigrationError("source registry sources must be nonempty")
    migrated_rows: list[dict[str, Any]] = []
    changed_rows = 0
    policy_ids: set[str] = set()
    for index, item in enumerate(rows):
        if not isinstance(item, dict):
            raise CohortRightsMigrationError(f"source registry row {index} is not an object")
        source_id = item.get("source_id")
        source_type = item.get("source_type")
        if not isinstance(source_id, str) or not source_id.strip():
            raise CohortRightsMigrationError(f"source registry row {index} lacks source_id")
        if not isinstance(source_type, str) or not source_type.strip():
            raise CohortRightsMigrationError(f"source registry row {index} lacks source_type")
        declared = item.get("rights_policy_id")
        if declared is None or (isinstance(declared, str) and not declared.strip()):
            declared = _rights_policy_id(source_id, source_type)
            changed_rows += 1
        if not isinstance(declared, str) or not declared.strip():
            raise CohortRightsMigrationError(f"source registry row {source_id} has invalid rights policy")
        select_rights_policy(
            policies,
            source_id=source_id,
            source_type=source_type,
            declared_policy_id=declared,
        )
        row = dict(item)
        row["rights_policy_id"] = declared
        migrated_rows.append(row)
        policy_ids.add(declared)

    migrated_registry = dict(registry)
    migrated_registry["sources"] = migrated_rows
    source_manifest_hash = content_hash(manifest)
    source_registry_hash = content_hash(registry)
    migrated_manifest = dict(manifest)
    migrated_manifest["source_registry_sha256"] = content_hash(migrated_registry)
    migrated_manifest["rights_policy_ids"] = sorted(policy_ids)
    migrated_manifest["rights_migration"] = {
        "format": "ht-legacy-rights-migration-v1",
        "source_manifest_sha256": source_manifest_hash,
        "source_registry_sha256_before": source_registry_hash,
        "rights_matrix_sha256": _sha256_file(Path(rights_matrix_path)),
        "changed_rows": changed_rows,
    }

    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=str(output.parent)))
    try:
        shutil.rmtree(staging)
        shutil.copytree(source, staging)
        registry_relative = _safe_relative(
            migrated_manifest.get("source_registry", "source_registry.json"),
            label="source_registry",
        )
        manifest_relative = _safe_relative(
            migrated_manifest.get("manifest_path", "manifest.json"), label="manifest_path"
        )
        _write_json(staging / registry_relative, migrated_registry)
        _write_json(staging / manifest_relative, migrated_manifest)
        _write_json(
            staging / "rights-migration.json",
            {
                "format": "ht-legacy-rights-migration-receipt-v1",
                "status": "PASS_LOCAL_TYPED_RIGHTS_MIGRATION",
                "source_manifest_sha256": source_manifest_hash,
                "source_registry_sha256_before": source_registry_hash,
                "target_registry_sha256": migrated_manifest["source_registry_sha256"],
                "rights_matrix_sha256": migrated_manifest["rights_migration"]["rights_matrix_sha256"],
                "source_rows": len(rows),
                "changed_rows": changed_rows,
                "policy_ids": sorted(policy_ids),
                "copied_bytes": copied_bytes,
                "max_storage_bytes": max_storage_bytes,
                "max_file_bytes": max_file_bytes,
            },
        )
        staging.replace(output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return {
        "status": "PASS_LOCAL_TYPED_RIGHTS_MIGRATION",
        "source": str(source_dir),
        "output": str(output_dir),
        "source_rows": len(rows),
        "changed_rows": changed_rows,
        "policy_ids": sorted(policy_ids),
        "copied_bytes": copied_bytes,
        "source_manifest_sha256": source_manifest_hash,
        "source_registry_sha256_before": source_registry_hash,
        "target_registry_sha256": migrated_manifest["source_registry_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rights-matrix", type=Path, required=True)
    parser.add_argument("--max-storage-bytes", type=int, default=140_000_000)
    parser.add_argument("--max-file-bytes", type=int, default=30_000_000)
    args = parser.parse_args()
    print(json.dumps(migrate_legacy_cohort_rights(
        args.source,
        args.output,
        rights_matrix_path=args.rights_matrix,
        max_storage_bytes=args.max_storage_bytes,
        max_file_bytes=args.max_file_bytes,
    ), indent=2))


if __name__ == "__main__":
    main()
