"""Sanitized availability observations, never spend authority or authentication.

A JSON hash detects changes; it does not attest who observed the balance.
No credentials or network access are used here.
"""
from datetime import datetime, timezone
import hashlib
import json
import re
from decimal import Decimal, ROUND_FLOOR

from .project_budget import money

FORMAT = "ptp-openrouter-credit-snapshot-v2"
MAX_AGE_SECONDS = 300


def available_money(value):
    money(value)  # Reject negative, nonfinite and invalid types first.
    return int((Decimal(str(value)) * Decimal(1_000_000_000)).to_integral_value(rounding=ROUND_FLOOR))


def utc_time(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO string with UTC timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("invalid UTC timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("timestamp must use UTC")
    return parsed


def normalize_credit(raw, *, now=None, require_current=False):
    if not isinstance(raw, dict) or raw.get("provider") != "openrouter":
        raise ValueError("invalid OpenRouter availability observation")
    # Old receipts remain readable, but cannot pass a live v2 scope check.
    if raw.get("format") not in {FORMAT, "ptp-openrouter-credit-snapshot-v1"}:
        raise ValueError("unsupported account credit snapshot format")
    if raw.get("source") not in {"approved_integration", "owner_sanitized_snapshot"}:
        raise ValueError("invalid availability observation source")
    at = utc_time(raw.get("as_of_utc"))
    remaining = available_money(raw.get("remaining_credits_usd"))
    unsigned = {key: raw[key] for key in ("format", "provider", "source", "as_of_utc")}
    unsigned["remaining_credits_usd"] = remaining / 1_000_000_000
    if raw["format"] == FORMAT:
        for name in ("authorization_id", "account_scope", "key_scope"):
            value = raw.get(name)
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", value):
                raise ValueError("availability scope identifier is missing or invalid")
            unsigned[name] = value
        if raw.get("currency") != "USD":
            raise ValueError("availability currency must be USD")
        unsigned["currency"] = "USD"
        key_remaining = raw.get("key_remaining_usd")
        if key_remaining is None and raw.get("key_limit_unlimited") is not True:
            raise ValueError("key limit remaining or explicit unlimited observation required")
        unsigned["key_remaining_usd"] = None if key_remaining is None else available_money(key_remaining) / 1_000_000_000
        unsigned["key_limit_unlimited"] = key_remaining is None
    digest = hashlib.sha256(json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if raw.get("snapshot_sha256") not in {None, digest}:
        raise ValueError("account credit snapshot hash mismatch")
    if require_current:
        if raw["format"] != FORMAT:
            raise ValueError("live availability requires v2 account/key/authority scope")
        age = ((now or datetime.now(timezone.utc)) - at).total_seconds()
        if age < 0 or age > MAX_AGE_SECONDS:
            raise ValueError("availability observation is future-dated or stale")
    return unsigned | {"snapshot_sha256": digest, "verification": "asserted_observation_not_provider_verified"}


def check_credit_for_reservation(db, raw, *, authorization_id, account_scope, key_scope, reserved, now):
    """Run within the same SQLite transaction as the project reservation.

    Count conservative bounds since the observation, including settled calls;
    do not reuse the same observed dollars on successive runs or processes.
    Other applications/account users can spend concurrently: this is advisory.
    """
    snapshot = normalize_credit(raw, now=now, require_current=True)
    if (snapshot["authorization_id"], snapshot["account_scope"], snapshot["key_scope"]) != (authorization_id, account_scope, key_scope):
        raise ValueError("availability account/key/authority binding mismatch")
    at = utc_time(snapshot["as_of_utc"]).timestamp()
    used = db.execute("SELECT COALESCE(SUM(reserved),0) FROM budget_attempts a JOIN budget_attempt_context c USING(attempt_id) WHERE c.created_epoch>=? OR c.settled_epoch IS NULL OR c.settled_epoch>=?", (at, at)).fetchone()[0]
    limits = [available_money(snapshot["remaining_credits_usd"])]
    if snapshot["key_remaining_usd"] is not None:
        limits.append(available_money(snapshot["key_remaining_usd"]))
    if used + reserved > min(limits):
        raise ValueError("account/key availability observation is below reserved exposure")
    return snapshot
