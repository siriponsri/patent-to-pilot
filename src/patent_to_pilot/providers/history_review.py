"""Validate a previously reviewed history anchor; never infer completeness.

The anchor is installed by the recovery/reconciliation workflow after reviewing
the external all-attempt evidence and stopping competing writers. This module
does not create anchors from caller-supplied exports or legacy pilot receipts.
An anchor is a local review record, not a provider signature.
"""
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation


def history_digest(rows):
    return hashlib.sha256(json.dumps([list(row[:5]) for row in rows], separators=(",", ":")).encode()).hexdigest()


def read_history_anchor(db, authorization_id, ledger_id):
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "budget_history_anchor" not in tables:
        raise ValueError("R1 all-attempt history has not been reconciled; no fresh allowance")
    rows = db.execute("SELECT review_json FROM budget_history_anchor").fetchall()
    if len(rows) != 1:
        raise ValueError("one reviewed history anchor required")
    try:
        anchor = json.loads(rows[0][0])
        if anchor["authorization_id"] != authorization_id or anchor["ledger_id"] != ledger_id or anchor["status"] != "reviewed_all_attempts":
            raise ValueError()
        for key in ("export_sha256", "baseline_sha256"):
            if not re.fullmatch(r"[a-f0-9]{64}", anchor[key]):
                raise ValueError()
        for key in ("review_reference", "account_scope", "key_scope"):
            if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", anchor[key]):
                raise ValueError()
        count = anchor["baseline_count"]
        if type(count) is not int or count < 0:
            raise ValueError()
        baseline = db.execute("SELECT attempt_id,phase,model,payload_sha256,reserved,actual,state,breach FROM budget_attempts ORDER BY rowid LIMIT ?", (count,)).fetchall()
        if len(baseline) != count or history_digest(baseline) != anchor["baseline_sha256"]:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise ValueError("history review anchor is invalid or its reconciled baseline changed") from None
    return anchor


def _scope(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", value):
        raise ValueError(f"{label} is invalid")
    return value


def _digest(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError(f"{label} is invalid")
    return value


def _nonnegative_nano(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("carryover amount must be finite USD") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError("carryover amount must be finite USD")
    return int((amount * Decimal(1_000_000_000)).to_integral_value())


def read_pre_r1_carryover(db, *, authorization_id, ledger_id):
    """Read the one reviewed pre-R1 carryover, if migration installed it."""
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "budget_pre_r1_carryover" not in tables:
        return None
    rows = db.execute(
        "SELECT singleton,kind,amount_nano_usd,currency,original_date_scope,account_scope,key_scope,"
        "evidence_sha256,review_reference,recorded_at_utc,record_sha256 FROM budget_pre_r1_carryover"
    ).fetchall()
    if len(rows) != 1:
        raise ValueError("one reviewed pre-R1 carryover record required")
    singleton, kind, amount, currency, date_scope, account_scope, key_scope, evidence_sha256, review_reference, recorded_at_utc, record_sha256 = rows[0]
    if singleton != 1 or kind != "conservative_pre_r1_carryover" or currency != "USD":
        raise ValueError("pre-R1 carryover identity is invalid")
    if type(amount) is not int or amount <= 0:
        raise ValueError("pre-R1 carryover amount is invalid")
    if not isinstance(date_scope, str) or not date_scope.strip() or len(date_scope) > 200 or any(ord(ch) < 32 for ch in date_scope):
        raise ValueError("pre-R1 carryover date scope is invalid")
    _scope(account_scope, "carryover account scope")
    _scope(key_scope, "carryover key scope")
    _scope(review_reference, "carryover review reference")
    _digest(evidence_sha256, "carryover evidence hash")
    if not isinstance(recorded_at_utc, str) or not recorded_at_utc.strip():
        raise ValueError("carryover recorded time is invalid")
    record = {
        "authorization_id": authorization_id,
        "ledger_id": ledger_id,
        "kind": kind,
        "amount_nano_usd": amount,
        "currency": currency,
        "original_date_scope": date_scope,
        "account_scope": account_scope,
        "key_scope": key_scope,
        "evidence_sha256": evidence_sha256,
        "review_reference": review_reference,
        "recorded_at_utc": recorded_at_utc,
    }
    expected = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if record_sha256 != expected:
        raise ValueError("pre-R1 carryover record hash is invalid")
    return record


def require_live_history_review(db, authorization_id, ledger_id):
    """Require reviewed all-attempt history plus quiescence and carryover."""
    anchor = read_history_anchor(db, authorization_id, ledger_id)
    if anchor.get("writer_quiescence") != "verified":
        raise ValueError("writer quiescence is not verified")
    try:
        unresolved = _nonnegative_nano(anchor.get("unresolved_exposure_usd"))
    except (TypeError, ValueError):
        raise ValueError("reviewed unresolved exposure is missing") from None
    if unresolved != 0:
        raise ValueError("reviewed unresolved exposure is nonzero")
    carryover = read_pre_r1_carryover(db, authorization_id=authorization_id, ledger_id=ledger_id)
    if carryover is None:
        raise ValueError("reviewed pre-R1 carryover is missing")
    if carryover["account_scope"] != anchor["account_scope"] or carryover["key_scope"] != anchor["key_scope"]:
        raise ValueError("carryover scope differs from reviewed history scope")
    if carryover["review_reference"] != anchor["review_reference"]:
        raise ValueError("carryover review reference differs from reviewed history")
    return {"anchor": anchor, "carryover": carryover}
