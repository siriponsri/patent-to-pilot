"""Refresh a versioned backend integration contract without mutating history."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class IntegrationContractError(ValueError):
    """Raised when a contract cannot be refreshed safely."""


def _repo_path(relative_path: str, field: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise IntegrationContractError(f"{field} must be repository-relative")
    resolved = (ROOT / candidate).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise IntegrationContractError(f"{field} escapes the repository") from exc
    return resolved


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrationContractError(f"cannot read JSON contract: {path}") from exc
    if not isinstance(value, dict):
        raise IntegrationContractError("integration contract must be an object")
    return value


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _current_head() -> str:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise IntegrationContractError("cannot resolve the current Git head") from exc
    if not GIT_SHA_RE.fullmatch(value):
        raise IntegrationContractError("current Git head is not a full SHA-1")
    return value


def refresh_contract(
    parent_contract: Path,
    output_contract: Path,
    *,
    code_head: str | None = None,
    refresh_date: str | None = None,
) -> dict[str, Any]:
    """Create a new contract with current backend hashes; never overwrite output."""
    parent_contract = parent_contract if parent_contract.is_absolute() else ROOT / parent_contract
    output_contract = output_contract if output_contract.is_absolute() else ROOT / output_contract
    if output_contract.exists():
        raise IntegrationContractError(f"refusing to overwrite existing contract: {output_contract}")

    contract = _load_json(parent_contract)
    backend_hashes = contract.get("backend_source_hashes")
    if not isinstance(backend_hashes, dict) or not backend_hashes:
        raise IntegrationContractError("parent contract lacks backend_source_hashes")
    current_backend_hashes: dict[str, str] = {}
    for relative_path, expected_hash in backend_hashes.items():
        if not isinstance(relative_path, str) or not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
            raise IntegrationContractError("parent backend hash entries are malformed")
        path = _repo_path(relative_path, "backend_source_hashes path")
        if not path.is_file():
            raise IntegrationContractError(f"backend source is missing: {relative_path}")
        current_backend_hashes[relative_path] = _sha256(path)

    fixture_hashes = contract.get("sanitized_fixture_hashes", [])
    if not isinstance(fixture_hashes, list):
        raise IntegrationContractError("sanitized_fixture_hashes must be a list")
    verified_fixtures = []
    for row in fixture_hashes:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str) or not isinstance(row.get("sha256"), str):
            raise IntegrationContractError("sanitized fixture entries are malformed")
        if not SHA256_RE.fullmatch(row["sha256"]):
            raise IntegrationContractError(f"invalid fixture hash: {row['path']}")
        path = _repo_path(row["path"], "sanitized fixture path")
        if not path.is_file():
            raise IntegrationContractError(f"sanitized fixture is missing: {row['path']}")
        actual_hash = _sha256(path)
        if actual_hash != row["sha256"]:
            raise IntegrationContractError(f"sanitized fixture hash drift: {row['path']}")
        verified_fixtures.append(row)

    resolved_head = code_head or _current_head()
    if not isinstance(resolved_head, str) or not GIT_SHA_RE.fullmatch(resolved_head):
        raise IntegrationContractError("code_head must be a full Git SHA-1")
    resolved_date = refresh_date or date.today().isoformat()
    if not isinstance(resolved_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", resolved_date):
        raise IntegrationContractError("refresh_date must use YYYY-MM-DD")

    refreshed = deepcopy(contract)
    refreshed["tested_code_head"] = resolved_head
    refreshed["backend_source_hashes"] = current_backend_hashes
    refreshed["refresh"] = {
        "type": "current_head_backend_hash_refresh",
        "date": resolved_date,
        "parent_contract": _display_path(parent_contract),
        "fixture_hashes_verified": len(verified_fixtures),
        "backend_hashes_recomputed": len(current_backend_hashes),
        "historical_parent_unchanged": True,
    }
    output_contract.parent.mkdir(parents=True, exist_ok=True)
    output_contract.write_text(json.dumps(refreshed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return refreshed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-head")
    parser.add_argument("--date", dest="refresh_date")
    args = parser.parse_args()
    try:
        refreshed = refresh_contract(
            args.parent_contract,
            args.output,
            code_head=args.code_head,
            refresh_date=args.refresh_date,
        )
    except (IntegrationContractError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "status": "REFRESHED",
        "tested_code_head": refreshed["tested_code_head"],
        "output": str(args.output),
        "backend_hashes": len(refreshed["backend_source_hashes"]),
        "fixture_hashes_verified": refreshed["refresh"]["fixture_hashes_verified"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
