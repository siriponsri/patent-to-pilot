"""Strict label-free MTM inputs for prospective development runners.

This is input validation, not an OS access-control boundary. Run only with a
curator-provided runtime directory; protected sources must not be mounted in
the development environment. This module never imports evaluator/staging code.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re


class InputBoundaryError(ValueError):
    """Messages deliberately omit input values, keys, IDs and label contents."""


def exact_fields(value, fields: set[str]) -> None:
    if type(value) is not dict or set(value) != fields:
        raise InputBoundaryError("input fields do not match the declared schema")


def identifier(value) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise InputBoundaryError("invalid identifier")


def calendar_date(value) -> None:
    if type(value) is not int or not 10000101 <= value <= 99991231:
        raise InputBoundaryError("invalid calendar date")
    try:
        date(value // 10000, value // 100 % 100, value % 100)
    except ValueError:
        raise InputBoundaryError("invalid calendar date") from None


def validate_metadata(row: dict) -> dict:
    exact_fields(row, {"id", "family_id", "priority", "c3"})
    identifier(row["id"])
    identifier(row["family_id"])
    calendar_date(row["priority"])
    codes = row["c3"]
    if (type(codes) is not list or
            any(type(c) is not str or re.fullmatch(r"[A-HY][0-9]{2}", c) is None for c in codes) or
            len(set(codes)) != len(codes)):
        raise InputBoundaryError("invalid CPC3 codes")
    return {**row, "c3": list(codes)}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputBoundaryError("duplicate JSON key")
        result[key] = value
    return result


def decode_json(raw: bytes):
    try:
        return json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError):
        raise InputBoundaryError("invalid JSON input") from None


def read_bound_rows(root: Path, *, expected_format: str, filename: str) -> list[dict]:
    """Fixed filenames only; reject test manifests before opening payloads."""
    if filename not in {"metadata.jsonl", "qrels.jsonl"}:
        raise InputBoundaryError("unsupported payload filename")
    root = root.resolve(strict=True)
    manifest_path = root / "manifest.json"
    payload_path = root / filename
    for path in (manifest_path, payload_path):
        if path.is_symlink() or path.resolve().parent != root:
            raise InputBoundaryError("bundle file escapes its directory")
    manifest = decode_json(manifest_path.read_bytes())
    exact_fields(manifest, {"format", "split", "sha256", "queries"})
    if manifest["format"] != expected_format or manifest["split"] != "dev":
        raise InputBoundaryError("only the declared development bundle is permitted")
    if type(manifest["queries"]) is not int or manifest["queries"] <= 0:
        raise InputBoundaryError("invalid query count")
    digest = manifest["sha256"]
    if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise InputBoundaryError("invalid content digest")
    raw = payload_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise InputBoundaryError("bundle content hash mismatch")
    lines = raw.splitlines()
    if len(lines) != manifest["queries"] or any(not line.strip() for line in lines):
        raise InputBoundaryError("bundle row count mismatch")
    return [decode_json(line) for line in lines]


def load_dev_metadata(root: Path) -> dict[str, dict]:
    rows = read_bound_rows(root, expected_format="ptp-mtm-runtime-v1", filename="metadata.jsonl")
    result = {}
    families = set()
    for row in rows:
        clean = validate_metadata(row)
        if clean["id"] in result or clean["family_id"] in families:
            raise InputBoundaryError("duplicate query or query family")
        result[clean["id"]] = clean
        families.add(clean["family_id"])
    return result
