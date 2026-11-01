"""Reviewed, append-only migration of an existing R1 journal.

The migration never creates a ledger, imports guessed attempts, or promotes a
mock journal. It installs only a reviewed history anchor and a separately
typed pre-R1 carryover, then binds that same file through the canonical
registry.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Mapping

from .history_review import history_digest, read_history_anchor, read_pre_r1_carryover
from .ledger_registry import CanonicalLedgerError, CanonicalLedgerBinding, register_canonical_ledger
from .project_budget import money, policy_identity_hash
from .round1 import R1_AUTHORIZATION_ID, build_round1_policy


EXPECTED_LEDGER_ID = f"{R1_AUTHORIZATION_ID}:canonical"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _scope(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", value):
        raise ValueError(f"{label} is invalid")
    return value


def _time(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{label} is invalid") from None
    return value


def _existing_r1_journal(path: Path, *, policy_hash: str) -> sqlite3.Connection:
    if not path.is_file():
        raise CanonicalLedgerError("reviewed migration requires an existing SQLite journal")
    try:
        with path.open("rb") as handle:
            if handle.read(16) != b"SQLite format 3\x00":
                raise CanonicalLedgerError("reviewed migration will not create or replace a ledger")
    except OSError as exc:
        raise CanonicalLedgerError("existing R1 journal is unreadable") from exc
    try:
        db = sqlite3.connect(path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"budget_meta", "budget_attempts", "budget_attempt_context", "budget_ledger_meta"}
        if not required.issubset(tables):
            raise CanonicalLedgerError("existing file is not an R1 budget journal")
        if db.execute("SELECT policy_hash FROM budget_meta").fetchall() != [(policy_hash,)]:
            raise CanonicalLedgerError("existing journal policy differs from the reviewed R1 policy")
        return db
    except CanonicalLedgerError:
        try:
            db.close()
        except UnboundLocalError:
            pass
        raise
    except sqlite3.Error as exc:
        try:
            db.close()
        except UnboundLocalError:
            pass
        raise CanonicalLedgerError("existing R1 journal is unreadable") from exc


def _reviewed_anchor(db, *, review: Mapping[str, Any], authorization_id: str, ledger_id: str) -> dict[str, Any]:
    required = {
        "authorization_id", "ledger_id", "status", "baseline_count", "baseline_sha256", "export_sha256",
        "review_reference", "account_scope", "key_scope", "writer_quiescence", "unresolved_exposure_usd",
        "reviewed_at_utc",
    }
    if not isinstance(review, Mapping) or not required.issubset(review):
        raise ValueError("reviewed migration requires the complete history review record")
    if review["authorization_id"] != authorization_id or review["ledger_id"] != ledger_id:
        raise ValueError("history review authority or ledger identity differs")
    if review["status"] != "reviewed_all_attempts" or review["writer_quiescence"] != "verified":
        raise ValueError("history review is not complete and quiescent")
    if type(review["baseline_count"]) is not int or review["baseline_count"] < 0:
        raise ValueError("reviewed baseline count is invalid")
    _digest(review["baseline_sha256"], "baseline hash")
    _digest(review["export_sha256"], "export hash")
    _scope(review["review_reference"], "review reference")
    _scope(review["account_scope"], "account scope")
    _scope(review["key_scope"], "key scope")
    _time(review["reviewed_at_utc"], "reviewed time")
    try:
        if money(review["unresolved_exposure_usd"]) != 0:
            raise ValueError("reviewed unresolved exposure must be zero")
    except (TypeError, ValueError):
        raise ValueError("reviewed unresolved exposure must be zero") from None
    rows = db.execute(
        "SELECT attempt_id,phase,model,payload_sha256,reserved,actual,state,breach FROM budget_attempts ORDER BY rowid LIMIT ?",
        (review["baseline_count"],),
    ).fetchall()
    if len(rows) != review["baseline_count"] or history_digest(rows) != review["baseline_sha256"]:
        raise ValueError("reviewed baseline does not match the existing journal")
    return dict(review)


def _carryover_record(carryover: Mapping[str, Any], *, review: Mapping[str, Any], authorization_id: str, ledger_id: str) -> dict[str, Any]:
    required = {"kind", "amount_usd", "currency", "original_date_scope", "account_scope", "key_scope", "evidence_sha256", "review_reference", "recorded_at_utc"}
    if not isinstance(carryover, Mapping) or not required.issubset(carryover):
        raise ValueError("reviewed migration requires the complete pre-R1 carryover record")
    if carryover["kind"] != "conservative_pre_r1_carryover" or carryover["currency"] != "USD":
        raise ValueError("carryover type or currency is invalid")
    amount_nano = money(carryover["amount_usd"])
    if amount_nano <= 0:
        raise ValueError("carryover must be positive")
    if not isinstance(carryover["original_date_scope"], str) or not carryover["original_date_scope"].strip() or len(carryover["original_date_scope"]) > 200:
        raise ValueError("carryover date scope is invalid")
    if carryover["account_scope"] != review["account_scope"] or carryover["key_scope"] != review["key_scope"]:
        raise ValueError("carryover scope differs from reviewed history scope")
    if carryover["review_reference"] != review["review_reference"]:
        raise ValueError("carryover review reference differs from reviewed history")
    _scope(carryover["account_scope"], "carryover account scope")
    _scope(carryover["key_scope"], "carryover key scope")
    _scope(carryover["review_reference"], "carryover review reference")
    _digest(carryover["evidence_sha256"], "carryover evidence hash")
    recorded_at = _time(carryover["recorded_at_utc"], "carryover recorded time")
    record = {
        "authorization_id": authorization_id,
        "ledger_id": ledger_id,
        "kind": carryover["kind"],
        "amount_nano_usd": amount_nano,
        "currency": carryover["currency"],
        "original_date_scope": carryover["original_date_scope"],
        "account_scope": carryover["account_scope"],
        "key_scope": carryover["key_scope"],
        "evidence_sha256": carryover["evidence_sha256"],
        "review_reference": carryover["review_reference"],
        "recorded_at_utc": recorded_at,
    }
    record["record_sha256"] = hashlib.sha256(_canonical(record).encode("utf-8")).hexdigest()
    return record


def migrate_reviewed_r1_history(
    ledger_path: str | Path,
    *,
    model_provider_map: Mapping[str, str],
    pricing_snapshot_sha256: str,
    pricing_snapshot_utc: str,
    review: Mapping[str, Any],
    carryover: Mapping[str, Any],
    registry_path: str | Path | None = None,
    ledger_id: str = EXPECTED_LEDGER_ID,
) -> CanonicalLedgerBinding:
    """Install reviewed metadata into the same existing journal and bind it once."""
    if ledger_id != EXPECTED_LEDGER_ID:
        raise ValueError("R1 canonical ledger identity is fixed")
    policy = build_round1_policy(
        model_provider_map,
        pricing_snapshot_sha256=pricing_snapshot_sha256,
        pricing_snapshot_utc=pricing_snapshot_utc,
    )
    policy_hash = policy_identity_hash(policy)
    path = Path(ledger_path).expanduser().resolve(strict=False)
    db = _existing_r1_journal(path, policy_hash=policy_hash)
    try:
        db.execute("BEGIN IMMEDIATE")
        meta = db.execute(
            "SELECT ledger_id,authorization_id,namespace,canonical_path,policy_hash,pricing_snapshot_sha256,pricing_snapshot_utc "
            "FROM budget_ledger_meta WHERE singleton=1"
        ).fetchone()
        expected_meta = (
            ledger_id, R1_AUTHORIZATION_ID, "canonical", str(path), policy_hash,
            pricing_snapshot_sha256, pricing_snapshot_utc,
        )
        if meta is not None:
            if tuple(meta) != expected_meta:
                raise CanonicalLedgerError("existing journal identity differs; refusing mock promotion or rebinding")
        else:
            db.execute(
                "INSERT INTO budget_ledger_meta(singleton,ledger_id,authorization_id,namespace,canonical_path,policy_hash,pricing_snapshot_sha256,pricing_snapshot_utc) VALUES(1,?,?,?,?,?,?,?)",
                expected_meta,
            )
        anchor = _reviewed_anchor(db, review=review, authorization_id=R1_AUTHORIZATION_ID, ledger_id=ledger_id)
        carry = _carryover_record(carryover, review=anchor, authorization_id=R1_AUTHORIZATION_ID, ledger_id=ledger_id)
        db.execute("CREATE TABLE IF NOT EXISTS budget_history_anchor(review_json TEXT NOT NULL)")
        existing_anchor = db.execute("SELECT review_json FROM budget_history_anchor").fetchall()
        anchor_json = _canonical(anchor)
        if existing_anchor:
            if len(existing_anchor) != 1 or existing_anchor[0][0] != anchor_json:
                raise CanonicalLedgerError("existing history review cannot be rewritten")
        else:
            db.execute("INSERT INTO budget_history_anchor(review_json) VALUES(?)", (anchor_json,))
        db.execute(
            "CREATE TABLE IF NOT EXISTS budget_pre_r1_carryover("
            "singleton INTEGER PRIMARY KEY CHECK(singleton=1),kind TEXT NOT NULL,amount_nano_usd INTEGER NOT NULL,"
            "currency TEXT NOT NULL,original_date_scope TEXT NOT NULL,account_scope TEXT NOT NULL,key_scope TEXT NOT NULL,"
            "evidence_sha256 TEXT NOT NULL,review_reference TEXT NOT NULL,recorded_at_utc TEXT NOT NULL,record_sha256 TEXT NOT NULL)"
        )
        existing_carry = db.execute(
            "SELECT singleton,kind,amount_nano_usd,currency,original_date_scope,account_scope,key_scope,evidence_sha256,review_reference,recorded_at_utc,record_sha256 FROM budget_pre_r1_carryover"
        ).fetchall()
        carry_values = (
            1, carry["kind"], carry["amount_nano_usd"], carry["currency"], carry["original_date_scope"],
            carry["account_scope"], carry["key_scope"], carry["evidence_sha256"], carry["review_reference"],
            carry["recorded_at_utc"], carry["record_sha256"],
        )
        if existing_carry:
            if len(existing_carry) != 1 or tuple(existing_carry[0]) != carry_values:
                raise CanonicalLedgerError("existing pre-R1 carryover cannot be rewritten")
        else:
            db.execute(
                "INSERT INTO budget_pre_r1_carryover(singleton,kind,amount_nano_usd,currency,original_date_scope,account_scope,key_scope,evidence_sha256,review_reference,recorded_at_utc,record_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                carry_values,
            )
        db.execute("COMMIT")
    except BaseException:
        try:
            db.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        db.close()
    return register_canonical_ledger(
        path,
        authorization_id=R1_AUTHORIZATION_ID,
        policy_hash=policy_hash,
        pricing_snapshot_sha256=pricing_snapshot_sha256,
        pricing_snapshot_utc=pricing_snapshot_utc,
        registry_path=registry_path,
        ledger_id=ledger_id,
    )
