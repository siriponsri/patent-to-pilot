"""Verify a current-state bundle before future worker use; not an OS sandbox."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

from patent_to_pilot.evaluation.comparison import validate_public_packet, validate_public_profile
from patent_to_pilot.evaluation.pilot_readiness import validate_output_contract
from patent_to_pilot.integration.pipeline import AgentPacket, OrganizationProfile

FILES = frozenset({"runtime-input.json", "output-contract.json"})
MAX_FILE_BYTES = 1024 * 1024


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _reject_reparse(path: Path) -> None:
    info = path.lstat()
    if path.is_symlink() or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024):
        raise ValueError("symlink/reparse-point input is not permitted")


def verify_bundle(
    directory: Path, expected_hashes: dict[str, str], *, allowed_root: Path,
    case_id: str, state_id: str, max_file_bytes: int = MAX_FILE_BYTES,
) -> dict[str, Any]:
    if set(expected_hashes) != FILES or not all(re.fullmatch(r"[a-f0-9]{64}", h) for h in expected_hashes.values()):
        raise ValueError("exact two-file manifest with SHA256 values required")
    if max_file_bytes <= 0:
        raise ValueError("positive input size bound required")
    # Lexical containment first; inspect each path component before following it.
    root = Path(os.path.abspath(allowed_root))
    directory = Path(os.path.abspath(directory))
    try:
        relative = directory.relative_to(root)
    except ValueError:
        raise ValueError("bundle escapes allowed root") from None
    current = root
    _reject_reparse(current)
    for component in relative.parts:
        current = current / component
        _reject_reparse(current)
    if not directory.is_dir():
        raise ValueError("bundle must be a directory")
    entries = list(directory.iterdir())
    if {p.name for p in entries} != FILES:
        raise ValueError("bundle contains missing or unexpected files")
    objects: dict[str, Any] = {}
    actual: dict[str, str] = {}
    for name in sorted(FILES):
        path = directory / name
        _reject_reparse(path)
        if not path.is_file():
            raise ValueError("bundle entries must be regular files")
        with path.open("rb") as stream:
            data = stream.read(max_file_bytes + 1)
        if len(data) > max_file_bytes:
            raise ValueError("staged input exceeds size bound")
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_hashes[name]:
            raise ValueError(f"staged file hash mismatch: {name}")
        actual[name] = digest
        objects[name] = json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicates, parse_constant=_reject_constant)
    payload = objects["runtime-input.json"]
    if not isinstance(payload, dict) or set(payload) != {"packet", "profile"}:
        raise ValueError("closed packet/profile envelope required")
    validate_public_packet(payload["packet"])
    validate_public_profile(payload["profile"])
    packet = AgentPacket.model_validate(payload["packet"])
    profile = OrganizationProfile.model_validate(payload["profile"])
    if packet.case_id != case_id or packet.state_id != state_id:
        raise ValueError("current case/state identity mismatch")
    if packet.profile_id != profile.profile_id or packet.profile_version != profile.profile_version:
        raise ValueError("packet/profile identity or version mismatch")
    validate_output_contract(objects["output-contract.json"])
    return {
        "status": "PASS", "case_id": case_id, "state_id": state_id,
        "file_hashes": actual, "max_file_bytes": max_file_bytes,
        "scope": "identity, size, strict JSON, path and schema/key boundary",
        "os_process_isolation": "NOT_VERIFIED",
        "semantic_oracle_detection": "NOT_CLAIMED",
        "manifest_authentication": "CURATOR_TRUST_REQUIRED",
    }
