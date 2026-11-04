#!/usr/bin/env python3
"""Acquire and validate manifest-listed benchmark files without touching Git payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


CHUNK_SIZE = 1024 * 1024
CORE_DATASETS = {
    "Helmers expert human-evaluation",
    "PANORAMA PAR4PC/PI4PC validation+test",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def head_metadata(url: str) -> dict[str, str | int | None]:
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "patent-to-pilot/benchmark-expansion"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return {
            "http_status": response.status,
            "content_type": response.headers.get("Content-Type"),
            "content_length": int(response.headers["Content-Length"])
            if response.headers.get("Content-Length")
            else None,
            "resolved_host": urlparse(response.geturl()).netloc,
        }


def download(url: str, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "patent-to-pilot/benchmark-expansion"},
    )
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as handle:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            handle.write(chunk)
    temporary.replace(destination)


def parquet_schema(path: Path) -> dict[str, object]:
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:  # pragma: no cover - environment-specific guard
        return {"status": "NOT_RUN_MISSING_PYARROW", "error": str(exc)}
    metadata = parquet.ParquetFile(path)
    schema = metadata.schema_arrow
    return {
        "status": "PASS",
        "num_rows": metadata.metadata.num_rows,
        "num_row_groups": metadata.metadata.num_row_groups,
        "columns": [field.name for field in schema],
        "types": {field.name: str(field.type) for field in schema},
    }


def zip_inventory(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        return {
            "status": "PASS",
            "member_count": len(members),
            "members": [
                {
                    "name": member.filename,
                    "compressed_bytes": member.compress_size,
                    "uncompressed_bytes": member.file_size,
                }
                for member in members
            ],
            "total_uncompressed_bytes": sum(member.file_size for member in members),
        }


def expected_checksum(file_record: dict[str, object]) -> tuple[str, str]:
    for algorithm, key in (("md5", "md5"), ("sha256", "sha256_from_lfs_metadata"), ("sha1", "git_blob_sha1")):
        value = file_record.get(key)
        if value:
            return algorithm, str(value)
    raise ValueError(f"No supported checksum in manifest for {file_record.get('path')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []

    for dataset in manifest["datasets"]:
        if dataset["dataset"] not in CORE_DATASETS:
            continue
        for file_record in dataset["files"]:
            relative_path = Path(file_record["path"])
            destination = args.output_dir / dataset["dataset"].replace("/", "_") / relative_path
            entry: dict[str, object] = {
                "dataset": dataset["dataset"],
                "path": file_record["path"],
                "url": file_record["download_url"],
                "license": dataset.get("license"),
                "source_version": dataset.get("version"),
                "observed_utc": utc_now(),
                "local_path": str(destination),
            }
            try:
                try:
                    entry["head"] = {"status": "PASS", **head_metadata(str(file_record["download_url"]))}
                except Exception as head_exc:
                    entry["head"] = {
                        "status": "FAILED_REUSED_LOCAL_ALLOWED",
                        "error": f"{type(head_exc).__name__}: {head_exc}",
                    }
                expected_bytes = int(file_record["bytes"])
                if destination.exists():
                    entry["download_action"] = "REUSED_EXISTING"
                else:
                    download(str(file_record["download_url"]), destination)
                    entry["download_action"] = "DOWNLOADED"
                actual_bytes = destination.stat().st_size
                entry["expected_bytes"] = expected_bytes
                entry["actual_bytes"] = actual_bytes
                if actual_bytes != expected_bytes:
                    raise ValueError(f"byte mismatch: expected {expected_bytes}, got {actual_bytes}")
                algorithm, expected_digest = expected_checksum(file_record)
                actual_digest = digest_file(destination, algorithm)
                entry["checksum_algorithm"] = algorithm
                entry["expected_checksum"] = expected_digest
                entry["actual_checksum"] = actual_digest
                if actual_digest != expected_digest:
                    raise ValueError(f"{algorithm} mismatch: expected {expected_digest}, got {actual_digest}")
                if destination.suffix.lower() == ".parquet":
                    entry["schema"] = parquet_schema(destination)
                    if entry["schema"].get("status") != "PASS":
                        raise ValueError(f"Parquet schema inspection did not pass: {entry['schema']}")
                elif destination.suffix.lower() == ".zip":
                    entry["archive"] = zip_inventory(destination)
                entry["status"] = "PASS"
            except Exception as exc:  # keep every failure in the receipt
                entry["status"] = "FAIL"
                entry["error"] = f"{type(exc).__name__}: {exc}"
                failures.append(entry)
            results.append(entry)

    receipt = {
        "receipt_version": "benchmark-expansion-acquisition-v1",
        "created_utc": utc_now(),
        "status": "PASS_CORE_ACQUISITION" if results and not failures else "FAIL_CORE_ACQUISITION",
        "manifest_path": str(args.manifest),
        "manifest_sha256": manifest_hash,
        "payload_storage": "outside_git",
        "datasets_selected": sorted(CORE_DATASETS),
        "files": results,
        "failure_count": len(failures),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "files": len(results), "failures": len(failures), "receipt": str(args.receipt)}))
    return 0 if not failures and results else 1


if __name__ == "__main__":
    sys.exit(main())
