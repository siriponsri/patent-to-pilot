"""Bounded read-only OpenRouter observations. No inference or ledger mutation.

Only execute with explicit owner authorization. Receipts are local observations,
not signed provider attestations, complete R1 history, or spend authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import http.client
import json
from pathlib import Path
import ssl

from .env_file import MAX_FILE_BYTES, parse_key

HOST = "openrouter.ai"
MAX_RESPONSE_BYTES = 262144
SCOPES = {"workspace_default_member", "workspace_default_key", "member", "api_key", "workspace", "key_limit"}


class ObservationError(ValueError):
    """Only fixed codes; never include an upstream message or input value."""


def selected_key(path):
    """Extract only the named key. Other values are neither parsed nor returned."""
    try:
        selected = []
        total = 0
        with Path(path).open("rb") as handle:
            for line in handle:
                total += len(line)
                if total > MAX_FILE_BYTES:
                    raise ValueError()
                line = line.removeprefix(b"\xef\xbb\xbf").strip()
                name = line.partition(b"=")[0].strip()
                if name == b"OPENROUTER_API_KEY":
                    selected.append(line.decode("utf-8"))
        return parse_key("\n".join(selected))
    except Exception:
        raise ObservationError("KEY_FILE_NOT_USABLE") from None


def decimal_field(value, *, signed=False, nullable=False):
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ObservationError("INVALID_NUMERIC_METADATA")
    number = Decimal(str(value))
    if not number.is_finite() or (number < 0 and not signed):
        raise ObservationError("INVALID_NUMERIC_METADATA")
    return str(number)


def budget(row):
    if not isinstance(row, dict) or row.get("scope") not in SCOPES:
        raise ObservationError("INVALID_BUDGET_METADATA")
    return {"scope": row["scope"], **{
        k: decimal_field(row.get(k), signed=k == "remaining_usd")
        for k in ("limit_usd", "spend_usd", "remaining_usd")
    }}


def sanitize_key(data):
    if not isinstance(data, dict):
        raise ObservationError("INVALID_KEY_METADATA")
    # Preserve presence before normalization: absent != provider-explicit null.
    presence = {k: k in data for k in ('limit', 'limit_remaining', 'budgets', 'effective_budget')}
    result = {k: decimal_field(data.get(k), signed=k == "limit_remaining", nullable=k in {"limit", "limit_remaining"})
              for k in ("limit", "limit_remaining", "usage")}
    for k in ("usage_daily", "usage_weekly", "usage_monthly", "byok_usage"):
        if k in data:
            result[k] = decimal_field(data[k])
    for k in ("is_management_key", "is_free_tier", "include_byok_in_limit"):
        if k in data:
            if type(data[k]) is not bool:
                raise ObservationError("INVALID_BOOLEAN_METADATA")
            result[k] = data[k]
    # A null/missing budget list is not evidence of no applicable budget.
    rows = data.get("budgets")
    if rows is not None and (not isinstance(rows, list) or len(rows) > 100):
        raise ObservationError("INVALID_BUDGET_METADATA")
    result["budgets"] = None if rows is None else [budget(row) for row in rows]
    result["effective_budget"] = None if data.get("effective_budget") is None else budget(data["effective_budget"])
    reset = data.get("limit_reset")
    result["limit_reset"] = reset if reset in {None, "daily", "weekly", "monthly"} else "unrecognized"
    for k in ("creator_user_id", "organization_id", "workspace_id"):
        value = data.get(k)
        if value is not None:
            if not isinstance(value, str) or len(value) > 256:
                raise ObservationError("INVALID_SCOPE_METADATA")
            result[k + "_sha256"] = hashlib.sha256(value.encode()).hexdigest()
    result['field_presence'] = presence
    result['key_limit_state'] = key_limit_state(result)
    return result


def key_limit_state(metadata):
    """Interpret only presence-preserving observations, never legacy v1 nulls.

    A key cap is independent of account balance and applicable guardrail budgets.
    OpenRouter /api/v1/key documents explicit null as unlimited.
    """
    presence = metadata.get('field_presence', {})
    if not isinstance(presence, dict) or not all(presence.get(k) is True for k in ('limit', 'limit_remaining')):
        return 'UNAVAILABLE_FIELD_PRESENCE'
    limit, remaining = metadata.get('limit'), metadata.get('limit_remaining')
    if limit is None and remaining is None:
        return 'UNLIMITED'
    if limit is None or remaining is None:
        return 'INCONSISTENT'
    # Values have already passed strict numeric validation in sanitize_key.
    if Decimal(remaining) > Decimal(limit):
        return 'INCONSISTENT'
    return 'EXHAUSTED' if Decimal(remaining) <= 0 else 'LIMITED'


def availability_summary(result):
    """Explain missing prerequisites without granting admission or inventing balance."""
    metadata = result.get('key_metadata', {})
    state = key_limit_state(metadata)
    presence = metadata.get('field_presence', {})
    budgets = metadata.get('budgets')
    effective = metadata.get('effective_budget')
    limits = []
    if state in {'LIMITED', 'EXHAUSTED'}:
        limits.append(Decimal(metadata['limit_remaining']))
    if isinstance(budgets, list):
        limits.extend(Decimal(row['remaining_usd']) for row in budgets)
    if effective is not None:
        limits.append(Decimal(effective['remaining_usd']))
    budgets_known = (presence.get('budgets') is True and isinstance(budgets, list)
                     and presence.get('effective_budget') is True)
    blocked = []
    if state not in {'LIMITED', 'UNLIMITED'}:
        blocked.append('KEY_LIMIT_' + state)
    if not budgets_known:
        blocked.append('APPLICABLE_BUDGETS_UNAVAILABLE')
    if limits and min(limits) <= 0:
        blocked.append('APPLICABLE_KEY_OR_BUDGET_EXHAUSTED')
    if 'remaining_credits_usd' not in result.get('account_credits', {}):
        blocked.append('ACCOUNT_CREDIT_NOT_OBSERVED_BY_THIS_COLLECTOR')
    if result.get('account_scope_binding') != 'RECONCILED':
        blocked.append('ACCOUNT_KEY_BINDING_NOT_RECONCILED')
    return {'key_limit_state': state, 'applicable_budgets_observed': budgets_known,
            'observed_key_or_budget_remaining_usd': str(min(limits)) if limits else None,
            'blocked_prerequisites': blocked, 'live_admission_enabled': False,
            'scope': 'metadata explanation only; freshness, canonical E2, rights and route checks remain required'}


def endpoint_request(key, endpoint):
    """Fixed host, verified TLS, no redirects/proxies/retries and bounded body."""
    if endpoint not in {"/api/v1/key", "/api/v1/credits"}:
        raise ObservationError("ENDPOINT_NOT_ALLOWED")
    connection = None
    try:
        connection = http.client.HTTPSConnection(HOST, timeout=15, context=ssl.create_default_context())
        connection.request("GET", endpoint, headers={"Authorization": "Bearer " + key, "Accept": "application/json"})
        response = connection.getresponse()
        # Do not read, print, or persist error bodies or redirect destinations.
        if response.status != 200:
            return {"status": "HTTP_REJECTED", "http_status": response.status}, None
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            return {"status": "RESPONSE_TOO_LARGE", "http_status": 200}, None
        raw = json.loads(body, parse_float=Decimal, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if not isinstance(raw, dict) or not isinstance(raw.get("data"), dict):
            raise ValueError()
        return {"status": "OBSERVED", "http_status": 200, "response_sha256": hashlib.sha256(body).hexdigest()}, raw["data"]
    except Exception as error:
        kind = "TLS_ERROR" if isinstance(error, ssl.SSLError) else "TIMEOUT" if isinstance(error, TimeoutError) else "NETWORK_ERROR" if isinstance(error, OSError) else "RESPONSE_FORMAT_ERROR"
        return {"status": "TRANSPORT_OR_FORMAT_ERROR", "error_kind": kind}, None
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def collect(key, *, allow_credits_if_management=False):
    started = datetime.now(timezone.utc).isoformat()
    status, data = endpoint_request(key, "/api/v1/key")
    result = {
        "format": "ptp-openrouter-metadata-observation-v2", "provider": "openrouter", "currency": "USD",
        "started_at_utc": started, "key_scope": "sha256:" + hashlib.sha256(key.encode()).hexdigest(),
        "key_endpoint": status, "account_scope": None, "account_scope_binding": "NOT_RECONCILED",
        "account_credits": {"status": "NOT_REQUESTED_MANAGEMENT_KEY_REQUIRED"},
        "history_completeness": "NOT_PROVEN", "r1_actual_spend_usd": None,
        "r1_unresolved_exposure_usd": None, "live_admission_enabled": False,
        "verification": "local_https_observation_not_signed_attestation",
    }
    if data is not None:
        result["key_metadata"] = sanitize_key(data)
        if allow_credits_if_management and data.get("is_management_key") is True:
            credit_status, credits = endpoint_request(key, "/api/v1/credits")
            result["account_credits"] = credit_status
            if credits is not None:
                purchased = decimal_field(credits.get("total_credits"))
                used = decimal_field(credits.get("total_usage"))
                result["account_credits"].update(total_credits_usd=purchased, total_usage_usd=used,
                                               remaining_credits_usd=str(Decimal(purchased) - Decimal(used)))
    result["availability"] = availability_summary(result)
    result["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["receipt_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result


def run(key_path, output_path, *, allow_credits_if_management=False):
    # Reserve a new output before reading the key or contacting any endpoint.
    try:
        with Path(output_path).open("x", encoding="utf-8") as output:
            key = selected_key(key_path)
            try:
                result = collect(key, allow_credits_if_management=allow_credits_if_management)
            finally:
                key = None  # Best effort only; Python memory erasure is not guaranteed.
            json.dump(result, output, indent=2, allow_nan=False)
            output.write("\n")
        return result["key_endpoint"]["status"]
    except Exception:
        raise ObservationError("OBSERVATION_FAILED_NO_RAW_DETAILS") from None
