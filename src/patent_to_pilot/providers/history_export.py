"""Offline consistency check of sanitized recovery exports. Never activates R1.

An export cannot prove that omitted/failed/retried requests did not occur.
Completeness and writer shutdown require independent reconciliation evidence.
"""
import hashlib
import json
import re

from .project_budget import money
from .round1 import R1_AUTHORIZATION_ID


def inspect_history_export(raw):
    if not isinstance(raw, dict) or set(raw) != {"format", "authorization_id", "account_scope", "key_scope", "currency", "attempts", "coverage"}:
        raise ValueError("invalid sanitized recovery envelope")
    if raw["format"] != "ptp-r1-all-attempt-export-v1" or raw["authorization_id"] != R1_AUTHORIZATION_ID or raw["currency"] != "USD":
        raise ValueError("wrong recovery authority, format or currency")
    for field in ("account_scope", "key_scope"):
        if not isinstance(raw[field], str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", raw[field]):
            raise ValueError("invalid recovery account/key scope")
    if not isinstance(raw["attempts"], list) or not isinstance(raw["coverage"], dict):
        raise ValueError("attempt list and coverage description required")
    seen = set()
    generation_ids = set()
    actual = pending = 0
    required = {"attempt_id", "authorization_id", "account_scope", "key_scope", "currency", "mode", "purpose", "state", "reserved_usd", "actual_usd", "provider_generation_id", "payload_sha256", "phase", "model", "upstream_provider"}
    for row in raw["attempts"]:
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("invalid sanitized attempt fields")
        if any(row[name] != raw[name] for name in ("authorization_id", "account_scope", "key_scope", "currency")) or row["mode"] != "live":
            raise ValueError("mixed authority/account/key/currency or mock history")
        aid = row["attempt_id"]
        if not isinstance(aid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", aid) or aid in seen:
            raise ValueError("invalid or duplicate attempt ID; do not deduplicate billing")
        seen.add(aid)
        if row["phase"] not in {"canary", "paired_pilot", "robustness"} or any(not isinstance(row[key], str) or not row[key].strip() for key in ("model", "upstream_provider")):
            raise ValueError("exact historical phase/model/provider required; no inferred migration")
        if row["purpose"] not in {"generation", "judge", "reasoning", "retry"} or row["state"] not in {"settled", "pending", "unknown_pending"}:
            raise ValueError("unsupported attempt purpose or billing state")
        if not isinstance(row["payload_sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", row["payload_sha256"]):
            raise ValueError("exact payload hash required")
        reserve = money(row["reserved_usd"])
        if reserve <= 0:
            raise ValueError("positive historical reservation required")
        generation = row["provider_generation_id"]
        if generation is not None:
            if not isinstance(generation, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", generation) or generation in generation_ids:
                raise ValueError("invalid or duplicate provider generation ID")
            generation_ids.add(generation)
        if row["state"] == "settled":
            if row["actual_usd"] is None:
                raise ValueError("settled attempt lacks actual billing")
            actual += money(row["actual_usd"])
        else:
            if row["actual_usd"] is not None:
                raise ValueError("unresolved attempt must retain its full reservation")
            pending += reserve
    coverage = raw["coverage"]
    if coverage.get("attempt_count") != len(seen) or type(coverage.get("attempt_count")) is not int:
        raise ValueError("export count differs from declared coverage")
    return {
        "status": "CONSISTENT_EXPORT_ONLY",
        "export_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
        "attempt_count": len(seen), "known_actual_nano_usd": actual,
        "unresolved_reserved_nano_usd": pending,
        "provider_generation_ids_present": len(generation_ids),
        "history_completeness": "NOT_VERIFIED", "live_admission_enabled": False,
        "import_performed": False,
    }
