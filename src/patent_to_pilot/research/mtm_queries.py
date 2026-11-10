"""Pinned dev-only query text; missing queries remain in the evaluation cohort."""
from pathlib import Path
import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json, exact_fields, identifier


def load_dev_queries(root: Path, trusted_manifest_sha256: str, metadata_ids: set[str]) -> dict:
    root = root.resolve(strict=True)
    manifest_path, payload = root / "manifest.json", root / "queries.jsonl"
    for path in (manifest_path, payload):
        if path.is_symlink() or path.resolve().parent != root:
            raise InputBoundaryError("query bundle escapes directory")
    manifest_raw = manifest_path.read_bytes()
    _manifest(manifest_raw, trusted_manifest_sha256)
    return parse_dev_queries(manifest_raw, payload.read_bytes(), trusted_manifest_sha256, metadata_ids)


def _manifest(manifest_raw, trusted_manifest_sha256):
    if hashlib.sha256(manifest_raw).hexdigest() != trusted_manifest_sha256:
        raise InputBoundaryError("query manifest differs from trusted digest")
    manifest = decode_json(manifest_raw)
    exact_fields(manifest, {"format", "split", "view", "sha256", "queries", "missing_ids"})
    if (manifest["format"] != "ptp-mtm-query-text-v1" or manifest["split"] != "dev" or
            manifest["view"] not in ("P", "T", "A")):
        raise InputBoundaryError("only declared development query text is permitted")
    if type(manifest["queries"]) is not int or manifest["queries"] <= 0:
        raise InputBoundaryError("invalid query count")
    missing = manifest["missing_ids"]
    if type(missing) is not list:
        raise InputBoundaryError("invalid missing-query ledger")
    for value in missing:
        identifier(value)
    if len(set(missing)) != len(missing):
        raise InputBoundaryError("duplicate missing query")
    return manifest


def parse_dev_queries(manifest_raw: bytes, payload_raw: bytes, trusted_manifest_sha256: str,
                      metadata_ids: set[str]) -> dict:
    """Validate the same byte snapshots that are decoded; no second payload read."""
    manifest = _manifest(manifest_raw, trusted_manifest_sha256)
    missing = manifest["missing_ids"]
    if hashlib.sha256(payload_raw).hexdigest() != manifest["sha256"]:
        raise InputBoundaryError("query payload hash mismatch")
    rows = [decode_json(line) for line in payload_raw.splitlines()]
    ids = set()
    for row in rows:
        exact_fields(row, {"id", "text"})
        identifier(row["id"])
        if type(row["text"]) is not str or not row["text"].strip():
            raise InputBoundaryError("empty or invalid query text")
        if row["id"] in ids:
            raise InputBoundaryError("duplicate query text")
        ids.add(row["id"])
    if (len(rows) != manifest["queries"] or ids & set(missing) or
            ids | set(missing) != metadata_ids):
        raise InputBoundaryError("query cohort differs from metadata and missing ledger")
    return {"rows": rows, "view": manifest["view"], "missing_ids": missing,
            "manifest_sha256": trusted_manifest_sha256, "payload_sha256": manifest["sha256"]}
