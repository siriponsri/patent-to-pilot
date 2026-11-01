#!/usr/bin/env python3
"""Acquire selected manifest files and record rights/hash/schema evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


CHUNK_SIZE = 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest_file(path: Path, algorithm: str) -> str:
    if algorithm == "git_blob_sha1":
        payload = path.read_bytes()
        digest = hashlib.sha1()
        digest.update(f"blob {len(payload)}\0".encode("ascii"))
        digest.update(payload)
        return digest.hexdigest()
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def head_metadata(url: str) -> dict[str, object]:
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
    with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as handle:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            handle.write(chunk)
    temporary.replace(destination)


def expected_checksum(file_record: dict[str, object]) -> tuple[str, str]:
    for algorithm, key in (
        ("md5", "md5"),
        ("sha256", "sha256_from_lfs_metadata"),
        ("git_blob_sha1", "git_blob_sha1"),
    ):
        value = file_record.get(key)
        if value:
            return algorithm, str(value)
    raise ValueError(f"No supported checksum for {file_record.get('path')}")


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


def csv_schema(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        columns = next(reader, [])
        rows = sum(1 for _ in reader)
    return {
        "status": "PASS",
        "num_rows": rows,
        "columns": columns,
        "column_count": len(columns),
    }


def json_schema(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
        if isinstance(payload, list):
            sample_keys = sorted(payload[0].keys()) if payload and isinstance(payload[0], dict) else []
            return {"status": "PASS", "format": "json", "num_rows": len(payload), "sample_keys": sample_keys}
        if isinstance(payload, dict):
            return {"status": "PASS", "format": "json", "top_level_keys": sorted(payload.keys())}
        return {"status": "PASS", "format": "json", "top_level_type": type(payload).__name__}
    except json.JSONDecodeError:
        rows = 0
        sample_keys: list[str] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            rows += 1
            if not sample_keys and isinstance(row, dict):
                sample_keys = sorted(row.keys())
        return {"status": "PASS", "format": "jsonl", "num_rows": rows, "sample_keys": sample_keys}


def inspect_payload(path: Path) -> dict[str, object] | None:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return parquet_schema(path)
    if suffix == ".csv":
        return csv_schema(path)
    if suffix == ".json":
        return json_schema(path)
    return None


def rights_record(dataset: dict[str, object]) -> dict[str, object]:
    license_text = str(dataset.get("license") or "")
    normalized_license = license_text.lower().replace("_", "-")
    unresolved = any(
        marker in license_text.lower()
        for marker in ("not established", "pending", "requires separate", "reported by parent")
    )
    non_commercial = any(
        marker in normalized_license
        for marker in ("non-commercial", "noncommercial", "-nc-", "-nc", " cc-nc")
    )
    research_only = unresolved or non_commercial
    return {
        "metadata_reported_license": license_text,
        "source_rights_status": (
            "UNRESOLVED_STANDALONE_DATA_RIGHTS"
            if unresolved
            else "NON_COMMERCIAL_LICENSE_REPORTED"
            if non_commercial
            else "SOURCE_METADATA_REPORTED"
        ),
        "permitted_scope": "local_research_only_until_rights_review" if research_only else "local_research_with_attribution",
        "commercial_release": "NOT_CLEARED" if research_only else "REQUIRES_SEPARATE_REVIEW",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--dataset", action="append", dest="datasets", required=True)
    args = parser.parse_args()

    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    selected = set(args.datasets)
    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    selected_datasets: list[str] = []

    for dataset in manifest["datasets"]:
        name = str(dataset["dataset"])
        if name not in selected:
            continue
        selected_datasets.append(name)
        for file_record in dataset.get("files", []):
            relative_path = Path(str(file_record["path"]))
            destination = args.output_dir / name.replace("/", "_") / relative_path
            entry: dict[str, object] = {
                "dataset": name,
                "path": str(relative_path),
                "url": file_record.get("download_url"),
                "license": dataset.get("license"),
                "source_version": dataset.get("version"),
                "observed_utc": utc_now(),
                "local_path": f"outside_git:_private_artifacts/healthtech/benchmark-expansion-20261101/{name.replace('/', '_')}/{relative_path.as_posix()}",
                "rights": rights_record(dataset),
            }
            try:
                if not file_record.get("download_url"):
                    raise ValueError("manifest file has no download_url")
                try:
                    entry["head"] = {"status": "PASS", **head_metadata(str(file_record["download_url"]))}
                except Exception as head_exc:
                    entry["head"] = {"status": "FAILED", "error": f"{type(head_exc).__name__}: {head_exc}"}
                    raise
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
                payload_schema = inspect_payload(destination)
                if payload_schema is not None:
                    entry["schema"] = payload_schema
                    if payload_schema.get("status") != "PASS":
                        raise ValueError(f"schema inspection did not pass: {payload_schema}")
                entry["status"] = "PASS"
            except Exception as exc:
                entry["status"] = "FAIL"
                entry["error"] = f"{type(exc).__name__}: {exc}"
                failures.append(entry)
            results.append(entry)

    missing = sorted(selected - set(selected_datasets))
    if missing:
        failures.append({"status": "FAIL", "error": f"datasets missing from manifest: {missing}"})
    receipt = {
        "receipt_version": "benchmark-expansion-selected-acquisition-v1",
        "created_utc": utc_now(),
        "status": "PASS_SELECTED_ACQUISITION" if results and not failures else "FAIL_SELECTED_ACQUISITION",
        "manifest_path": str(args.manifest),
        "manifest_sha256": manifest_hash,
        "payload_storage": "outside_git",
        "datasets_selected": sorted(selected),
        "files": results,
        "failure_count": len(failures),
        "failures": failures,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "files": len(results), "failures": len(failures), "receipt": str(args.receipt)}))
    return 0 if not failures and results else 1


if __name__ == "__main__":
    sys.exit(main())
