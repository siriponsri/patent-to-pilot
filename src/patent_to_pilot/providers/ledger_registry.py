"""Canonical durable-ledger bindings shared by HealthTech worktrees.

The registry is deliberately outside any checkout. A live authorization is
allowed to resolve to one existing ledger path only; a caller-supplied path
must match that binding exactly. Test/mock ledgers use a separate namespace and
never resolve through the live registry.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any


REGISTRY_FORMAT = "ptp-canonical-budget-ledger-v1"


class CanonicalLedgerError(RuntimeError):
    """Raised when an authorization cannot resolve to its one ledger."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _absolute(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def default_registry_path(authorization_id: str) -> Path:
    """Return a stable per-user path independent of the active worktree."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", authorization_id):
        raise ValueError("invalid authorization ID")
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    elif os.environ.get("XDG_STATE_HOME"):
        root = Path(os.environ["XDG_STATE_HOME"])
    else:
        root = Path.home() / ".local" / "state"
    return root / "PatentToPilot" / "healthtech" / "budget-ledgers" / f"{authorization_id}.json"


@dataclass(frozen=True)
class CanonicalLedgerBinding:
    authorization_id: str
    ledger_id: str
    ledger_path: Path
    policy_hash: str
    pricing_snapshot_sha256: str
    pricing_snapshot_utc: str
    registry_path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "format": REGISTRY_FORMAT,
            "authorization_id": self.authorization_id,
            "ledger_id": self.ledger_id,
            "ledger_path": str(self.ledger_path),
            "policy_hash": self.policy_hash,
            "pricing_snapshot_sha256": self.pricing_snapshot_sha256,
            "pricing_snapshot_utc": self.pricing_snapshot_utc,
        }


def _validate_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise CanonicalLedgerError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _validate_existing_sqlite_journal(path: Path, *, authorization_id: str, policy_hash: str) -> None:
    """Reject a readable SQLite journal from the wrong policy or namespace.

    Non-SQLite files remain bindable for registry-only tests and future storage
    adapters; the live SQLite budget path is checked before a registry write.
    """
    try:
        with path.open("rb") as handle:
            if handle.read(16) != b"SQLite format 3\x00":
                return
    except OSError as exc:
        raise CanonicalLedgerError("canonical ledger journal is unreadable") from exc
    try:
        with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "budget_meta" not in tables:
                raise CanonicalLedgerError("existing SQLite journal is not a compatible R1 budget ledger")
            hashes = db.execute("SELECT policy_hash FROM budget_meta").fetchall()
            if hashes != [(policy_hash,)]:
                raise CanonicalLedgerError("existing SQLite journal policy hash differs from the requested authorization")
            if "budget_ledger_meta" in tables:
                row = db.execute(
                    "SELECT authorization_id, namespace FROM budget_ledger_meta WHERE singleton=1"
                ).fetchone()
                if row is not None:
                    journal_authorization, namespace = row
                    if journal_authorization not in {None, authorization_id}:
                        raise CanonicalLedgerError("existing SQLite journal authorization differs from the requested authorization")
                    if namespace != "canonical":
                        raise CanonicalLedgerError("mock or non-canonical SQLite journal cannot be bound for live dispatch")
    except CanonicalLedgerError:
        raise
    except sqlite3.Error as exc:
        raise CanonicalLedgerError("existing SQLite journal is unreadable") from exc


def _binding_from_dict(raw: dict[str, Any], registry_path: Path, expected_authorization: str) -> CanonicalLedgerBinding:
    if raw.get("format") != REGISTRY_FORMAT:
        raise CanonicalLedgerError("unsupported canonical ledger registry format")
    if raw.get("authorization_id") != expected_authorization:
        raise CanonicalLedgerError("canonical ledger authorization mismatch")
    ledger_id = raw.get("ledger_id")
    if not isinstance(ledger_id, str) or not re.fullmatch(r"[A-Za-z0-9_:.-]{1,160}", ledger_id):
        raise CanonicalLedgerError("canonical ledger identity is invalid")
    raw_path = raw.get("ledger_path")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        raise CanonicalLedgerError("canonical ledger path must be absolute")
    pricing_time = raw.get("pricing_snapshot_utc")
    if not isinstance(pricing_time, str) or not pricing_time.strip():
        raise CanonicalLedgerError("canonical ledger pricing snapshot time is missing")
    return CanonicalLedgerBinding(
        authorization_id=expected_authorization,
        ledger_id=ledger_id,
        ledger_path=_absolute(raw_path),
        policy_hash=_validate_digest(raw.get("policy_hash"), "policy hash"),
        pricing_snapshot_sha256=_validate_digest(raw.get("pricing_snapshot_sha256"), "pricing snapshot hash"),
        pricing_snapshot_utc=pricing_time,
        registry_path=_absolute(registry_path),
    )


def register_canonical_ledger(
    ledger_path: str | Path,
    *,
    authorization_id: str,
    policy_hash: str,
    pricing_snapshot_sha256: str,
    pricing_snapshot_utc: str,
    registry_path: str | Path | None = None,
    ledger_id: str | None = None,
) -> CanonicalLedgerBinding:
    """Bind an already-existing journal without creating/resetting its budget."""
    path = _absolute(ledger_path)
    if not path.is_file():
        raise CanonicalLedgerError("cannot register a missing ledger journal")
    _validate_existing_sqlite_journal(path, authorization_id=authorization_id, policy_hash=policy_hash)
    registry = _absolute(registry_path or default_registry_path(authorization_id))
    binding = CanonicalLedgerBinding(
        authorization_id=authorization_id,
        ledger_id=ledger_id or f"{authorization_id}:canonical",
        ledger_path=path,
        policy_hash=_validate_digest(policy_hash, "policy hash"),
        pricing_snapshot_sha256=_validate_digest(pricing_snapshot_sha256, "pricing snapshot hash"),
        pricing_snapshot_utc=pricing_snapshot_utc,
        registry_path=registry,
    )
    if not isinstance(pricing_snapshot_utc, str) or not pricing_snapshot_utc.strip():
        raise CanonicalLedgerError("pricing snapshot time is required")
    if registry.exists():
        try:
            existing = _binding_from_dict(json.loads(registry.read_text(encoding="utf-8")), registry, authorization_id)
        except (OSError, json.JSONDecodeError) as exc:
            raise CanonicalLedgerError("canonical ledger registry is unreadable") from exc
        if existing != binding:
            raise CanonicalLedgerError("authorization is already bound to a different ledger or pricing snapshot")
        return existing
    registry.parent.mkdir(parents=True, exist_ok=True)
    payload = binding.as_dict() | {"registered_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        with registry.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        return resolve_canonical_ledger(
            authorization_id=authorization_id,
            policy_hash=policy_hash,
            pricing_snapshot_sha256=pricing_snapshot_sha256,
            pricing_snapshot_utc=pricing_snapshot_utc,
            registry_path=registry,
        )
    return binding


def resolve_canonical_ledger(
    *,
    authorization_id: str,
    policy_hash: str,
    pricing_snapshot_sha256: str,
    pricing_snapshot_utc: str,
    requested_path: str | Path | None = None,
    registry_path: str | Path | None = None,
) -> CanonicalLedgerBinding:
    """Resolve the one live ledger and reject path substitution."""
    registry = _absolute(registry_path or default_registry_path(authorization_id))
    if not registry.is_file():
        raise CanonicalLedgerError(
            f"canonical ledger registry is missing for {authorization_id}; reconcile the existing journal before paid dispatch"
        )
    try:
        raw = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonicalLedgerError("canonical ledger registry is unreadable") from exc
    if not isinstance(raw, dict):
        raise CanonicalLedgerError("canonical ledger registry must be a JSON object")
    binding = _binding_from_dict(raw, registry, authorization_id)
    if not binding.ledger_path.is_file():
        raise CanonicalLedgerError("canonical ledger journal is missing; do not create a replacement")
    _validate_existing_sqlite_journal(
        binding.ledger_path,
        authorization_id=authorization_id,
        policy_hash=policy_hash,
    )
    if requested_path is not None and _absolute(requested_path) != binding.ledger_path:
        raise CanonicalLedgerError("requested budget path is not the registered canonical ledger")
    if binding.policy_hash != _validate_digest(policy_hash, "policy hash"):
        raise CanonicalLedgerError("canonical ledger policy hash differs from the verified R1 policy")
    if binding.pricing_snapshot_sha256 != _validate_digest(pricing_snapshot_sha256, "pricing snapshot hash"):
        raise CanonicalLedgerError("canonical ledger pricing snapshot differs from the verified R1 policy")
    if binding.pricing_snapshot_utc != pricing_snapshot_utc:
        raise CanonicalLedgerError("canonical ledger pricing snapshot time differs from the verified R1 policy")
    return binding


def ephemeral_ledger_id(path: str | Path, namespace: str = "mock") -> str:
    """Return a deterministic ID for an isolated non-live ledger."""
    resolved = str(_absolute(path)).encode("utf-8")
    return f"{namespace}:{hashlib.sha256(resolved).hexdigest()[:24]}"
