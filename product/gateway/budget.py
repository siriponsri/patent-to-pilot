"""Gateway admission around the shared budget ledger."""

import hashlib
import json
import os
import sqlite3
from contextlib import closing, contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from threading import Lock
from zoneinfo import ZoneInfo

from patent_to_pilot.budget.ledger import BudgetLedger, BudgetRefused, Envelope, Reservation

from .evidence import PROMPT_VERSION
from .providers import PRESETS, Completion, Route

BANGKOK = ZoneInfo("Asia/Bangkok")
EXPIRY = datetime(2026, 12, 16, tzinfo=BANGKOK)
ENVELOPE = Envelope(
    "D43", list(PRESETS), hard_limit_usd=10, stop_usd=8, max_requests=200,
    requires_approval=False, scope_text="MWD organization trial only",
    source_ref="docs/maintenance/OWNER-DECISIONS-20261122.md D43; PRD-MWD-v1 section 4b",
)
AUDIT_SCOPE = "mwd_gateway"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class AdmissionRefused(Exception):
    def __init__(self, reason: str):
        self.reason = reason


@contextmanager
def exclusive_owner(path: Path):
    """An OS-backed single-process lease, released on clean shutdown or process death."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + ".lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class Admission:
    def __init__(self, path: Path, *, require_existing: bool = False):
        self.path = path
        self._lock = Lock()
        self._unsafe = False
        if require_existing and (not path.is_file() or path.stat().st_size == 0):
            raise ValueError("the operator must restore the dedicated D43 ledger before live dispatch")
        self.ledger = BudgetLedger(path, seed=False)
        envelopes = self.ledger.envelopes()
        if set(envelopes) - {ENVELOPE.envelope_id}:
            raise ValueError("MWD requires a dedicated D43 ledger")
        if require_existing and ENVELOPE.envelope_id not in envelopes:
            raise ValueError("the live ledger has no D43 envelope")
        self.ledger.put_envelope(ENVELOPE)
        if self.ledger.envelopes()[ENVELOPE.envelope_id] != ENVELOPE:
            raise ValueError("unexpected D43 envelope configuration")
        self.ledger.recover_stale(max_age_s=0)
        with self._connect() as con:
            con.execute("CREATE TABLE IF NOT EXISTS mwd_route (id INTEGER PRIMARY KEY CHECK(id=1), fingerprint TEXT)")
            con.execute(
                """CREATE INDEX IF NOT EXISTS mwd_request ON entries
                   (envelope_id, scope, json_extract(detail_json, '$.request_key'))"""
            )

    @contextmanager
    def _connect(self):
        with closing(sqlite3.connect(self.path, timeout=10)) as con:
            with con:
                yield con

    def reserve(self, route: Route, estimate: float, user: str, key: str, task: str, now: datetime) -> Reservation:
        now = now.astimezone(BANGKOK)
        if now >= EXPIRY:
            raise AdmissionRefused("envelope_expired")
        user_hash = digest(user)
        request_key = digest(f"{user_hash}:{key}")
        tag = f"{user_hash}:{now.date().isoformat()}"
        fingerprint = digest(json.dumps(asdict(route), sort_keys=True))
        with self._lock:
            if self._unsafe:
                raise AdmissionRefused("ledger_unavailable")
            with self._connect() as con:
                pinned = con.execute("SELECT fingerprint FROM mwd_route WHERE id=1").fetchone()
                if pinned is not None and pinned[0] != fingerprint:
                    raise AdmissionRefused("route_or_price_changed")
                changed = con.execute(
                    """SELECT 1 FROM entries WHERE envelope_id=? AND scope=?
                       AND json_extract(detail_json, '$.configuration_changed')=1""",
                    (ENVELOPE.envelope_id, AUDIT_SCOPE),
                ).fetchone()
                if changed:
                    raise AdmissionRefused("route_or_price_changed")
                duplicate = con.execute(
                    """SELECT status FROM entries
                       WHERE envelope_id=? AND scope=? AND json_extract(detail_json, '$.request_key')=?""",
                    (ENVELOPE.envelope_id, AUDIT_SCOPE, request_key),
                ).fetchone()
                if duplicate:
                    reason = "request_in_progress" if duplicate[0] == "reserved" else "duplicate_request"
                    raise AdmissionRefused(reason)
                # A date rollover must not permit a second request while the prior one is outstanding.
                active = con.execute(
                    """SELECT 1 FROM entries WHERE envelope_id=? AND scope=? AND status='reserved'
                       AND json_extract(detail_json, '$.user_hash')=?""",
                    (ENVELOPE.envelope_id, AUDIT_SCOPE, user_hash),
                ).fetchone()
                if active:
                    raise AdmissionRefused("request_in_progress")
                if pinned is None:
                    con.execute("INSERT INTO mwd_route VALUES (1, ?)", (fingerprint,))
            try:
                return self.ledger.reserve(
                    route.provider, estimate, scope=AUDIT_SCOPE, envelope_id=ENVELOPE.envelope_id,
                    model=route.preset.model, tag=tag, tag_max_requests=5, run_usd_cap=8, run_max_requests=200,
                    detail={
                        "request_key": request_key, "user_hash": user_hash, "route": route.label,
                        "prompt_version": PROMPT_VERSION, "task": task, "tariff_evidence": route.tariff.evidence_ref,
                    },
                )
            except BudgetRefused as exc:
                reason = {
                    "tag_cap": "daily_limit", "request_cap": "attempt_limit", "run_cap": "budget_limit",
                    "stop_threshold": "budget_limit", "usd_limit": "budget_limit",
                    "paused_unknown_cost": "unknown_billing", "price_unknown": "unknown_billing",
                }.get(exc.reason, "ledger_unavailable")
                raise AdmissionRefused(reason) from None

    def unknown(self, reservation: Reservation, outcome: str, detail: dict | None = None) -> None:
        if outcome == "route_or_price_changed":
            detail = {**(detail or {}), "configuration_changed": True}
        with self._lock:
            try:
                self.ledger.mark_unknown(reservation.entry_id, outcome=outcome, detail=detail)
            except (OSError, sqlite3.Error, ValueError):
                self._unsafe = True
                raise

    def settle(self, reservation: Reservation, completion: Completion, outcome: str) -> None:
        detail = {
            "input_tokens": completion.input_tokens, "output_tokens": completion.output_tokens,
            "cost_basis": completion.cost_basis,
        }
        if completion.cost_usd > reservation.reserved_usd + 1e-9:
            self.unknown(reservation, "route_or_price_changed", {**detail, "reported_gross_usd": completion.cost_usd})
            raise AdmissionRefused("route_or_price_changed")
        with self._lock:
            try:
                state = self.ledger.settle(
                    reservation.entry_id, completion.cost_usd, generation_id=completion.generation_id,
                    outcome=outcome, detail=detail,
                )["status"]
            except (OSError, sqlite3.Error, ValueError):
                self._unsafe = True
                raise
            if state != "settled":
                raise AdmissionRefused("unknown_billing")
