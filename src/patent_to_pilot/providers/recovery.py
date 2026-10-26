"""One separately approved synthetic Gemini recovery; never rewrites Phase A."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
from contextlib import closing, nullcontext
from pathlib import Path

from .openrouter import (
    AttemptLedger, BudgetExceededError, OpenRouterAdapter, OpenRouterHTTPTransport,
    ProviderAttempt, ProviderCapabilities, ProviderConfig, ProviderRequest,
)
from .pilot import Journal, PilotError, canonical, config_for, exclusive_run, plan_hash, request_for, validate_plan

ORIGINAL_PLAN = "6cf9bd14059f1df9f11ff6f913d31bcc5e5c60f3f993ac4766621bf1c7c148b2"
PAYLOAD = "f31be6bc37b4c522b7bfa38a7e79d17e0000e9e129ee3ad332a90f1133fcadf9"


def _read_original(plan, path):
    path = Path(path).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        meta = db.execute("SELECT digest,mode FROM meta WHERE id=1").fetchone()
        rows = db.execute("SELECT seq,phase,job,config,request,reservation,finished FROM attempts ORDER BY seq").fetchall()
        reconciled = db.execute("SELECT COUNT(*) FROM reconciliations").fetchone()[0]
    if meta != (plan_hash(plan), "live") or len(rows) != 2 or reconciled:
        raise PilotError("original terminal journal differs from the reviewed Phase A")
    records = []
    for expected_seq, (row, job, status) in enumerate(zip(rows, ["smoke-1-1", "smoke-1-2"], ["model_drift", "success"]), 1):
        seq, phase, actual_job, config, request, reservation, finished = row
        attempt = ProviderAttempt.model_validate_json(reservation)
        cost = attempt.observed_cost_usd
        if seq != expected_seq or phase != "smoke" or actual_job != job or not finished or attempt.status != status or attempt.reservation_status != "settled" or cost is None or not math.isfinite(cost) or cost < 0:
            raise PilotError("original outcome or billing is unresolved/different")
        records.append((ProviderConfig.model_validate_json(config), ProviderRequest.model_validate_json(request), attempt))
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise PilotError("original journal changed while reading")
    if not math.isclose(sum(a.observed_cost_usd for _, _, a in records), 0.0000732, abs_tol=1e-12, rel_tol=0):
        raise PilotError("original debit differs from the approved recovery baseline")
    return digest, records


def recovery_contract(plan, original, state):
    validate_plan(plan)
    if plan_hash(plan) != ORIGINAL_PLAN or Path(original).resolve() == Path(state).resolve():
        raise PilotError("recovery requires the unchanged original plan and a separate state")
    job = plan["phases"]["smoke"]["jobs"][0]
    config, request = config_for(plan, "smoke", job, True), request_for(plan, job)
    payload = OpenRouterHTTPTransport._request_payload(config, request)
    if hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest() != PAYLOAD:
        raise PilotError("recovery payload differs from approved synthetic echo")
    digest, records = _read_original(plan, original)
    return dict(version="gemini-identity-recovery-1", original_plan_sha256=ORIGINAL_PLAN,
                original_state_path=str(Path(original).resolve()), original_state_sha256=digest,
                original_status="PHASE_FAILED", original_attempts=2,
                original_debit_usd=sum(a.observed_cost_usd for _, _, a in records),
                recovery_state_path=str(Path(state).resolve()), attempts_max=1, retries=0,
                cumulative_spend_cap_usd=0.6, payload_sha256=PAYLOAD,
                endpoint=OpenRouterHTTPTransport._url(config), model=config.model,
                routing_only=config.routing_only, allow_fallbacks=False)


def validate_recovery_approval(contract, approval):
    if not approval or approval.get("approved") is not True or approval.get("funding_confirmed") is not True or approval.get("contract_sha256") != plan_hash(contract) or approval.get("contract") != contract or not approval.get("owner_reference"):
        raise PilotError("exact one-attempt recovery approval is required")


class _RecoveryLedger(AttemptLedger):
    def __init__(self, journal, original_records):
        super().__init__()
        self.journal = journal
        self.current = None
        for config, request, old in original_records:
            self.configure_cap(config.max_spend_usd)
            entry = super().reserve(config=config, request=request, attempt=1)
            super().settle(entry, usage=dict(input_tokens=old.observed_input_tokens,
                           output_tokens=old.observed_output_tokens, total_tokens=old.observed_total_tokens),
                           cost=old.observed_cost_usd, outcome_known=True)
            entry.status = old.status

    def reserve(self, *, config, request, attempt):
        if self.journal.rows():
            raise BudgetExceededError("one recovery attempt already reserved; no replay")
        entry = super().reserve(config=config, request=request, attempt=attempt)
        self.journal.db.execute("INSERT INTO attempts(seq,phase,job,config,request,reservation) VALUES(1,?,?,?,?,?)",
                                ("recovery", "gemini-identity-1", config.model_dump_json(), request.model_dump_json(), entry.model_dump_json()))
        self.journal.db.commit()  # Durable consumption of the only slot BEFORE send.
        self.current = entry
        return entry

    def save(self, *, finished=False, response=None):
        if self.current is not None:
            self.journal.db.execute("UPDATE attempts SET reservation=?,finished=?,response=? WHERE seq=1",
                                    (self.current.model_dump_json(), int(finished), response))
            self.journal.db.commit()

    def settle(self, entry, **kwargs):
        result = super().settle(entry, **kwargs)
        if entry is self.current:
            self.save()
        return result


def _summary(journal, contract, reason=None):
    rows = journal.rows()
    status = "RECOVERY_BLOCKED_PRE_DISPATCH"
    if rows:
        if len(rows) != 1:
            raise PilotError("recovery single-attempt gate is inconsistent")
        row = rows[0]
        if not row["finished"] or row["attempt"].reservation_status != "settled":
            status = "BLOCKED_UNKNOWN_PENDING"
        else:
            status = "RECOVERY_SUCCESS" if row["attempt"].status == "success" else "RECOVERY_FAILED"
    result = journal.summary(status, reason)
    result["recovery_debit_usd"] = result.pop("actual_debit_usd")
    result.update(original_status="PHASE_FAILED", original_attempts=2,
                  original_debit_usd=contract["original_debit_usd"],
                  cumulative_actual_debit_usd=contract["original_debit_usd"] + result["recovery_debit_usd"],
                  cumulative_spend_cap_usd=0.6, total_attempts=2 + len(rows))
    return result


def run_recovery(plan, original, state, approval, transport_factory, *, live=False, credential_context=nullcontext):
    contract = recovery_contract(plan, original, state)
    validate_recovery_approval(contract, approval)  # Before locks, state writes or key loading.
    original, state = Path(original).resolve(), Path(state).resolve()
    with exclusive_run(original), exclusive_run(state):
        if recovery_contract(plan, original, state) != contract:
            raise PilotError("original state changed after recovery approval check")
        marker = Path(str(state) + ".started.json")
        activation = dict(contract_sha256=plan_hash(contract), state_path=str(state), mode="live" if live else "mock")
        if marker.exists():
            if not state.exists() or json.loads(marker.read_text(encoding="utf-8")) != activation:
                raise PilotError("recovery activation differs or database is missing; refuse reset")
        elif state.exists():
            raise PilotError("recovery database has no activation marker; refuse reset")
        else:
            with marker.open("x", encoding="utf-8") as handle:
                handle.write(canonical(activation)); handle.flush(); os.fsync(handle.fileno())
        journal = Journal(state, plan, live)
        try:
            if journal.rows():
                return _summary(journal, contract)  # No credential/transport access on resume.
            _, records = _read_original(plan, original)
            ledger = _RecoveryLedger(journal, records)
            job = plan["phases"]["smoke"]["jobs"][0]
            config = config_for(plan, "smoke", job, live)
            config.retries = 0
            response = None
            reason = None
            finished = False
            try:
                with credential_context():
                    adapter = OpenRouterAdapter(config, transport_factory(job),
                              ProviderCapabilities(provider="openrouter", model=job["model"], structured_outputs=True), ledger)
                    response = adapter.complete(request_for(plan, job))
                    finished = True
            except Exception as exc:
                reason = type(exc).__name__  # No raw exceptions, response data or key values.
                finished = True
            finally:
                ledger.save(finished=finished, response=response.model_dump_json() if response else None)
            return _summary(journal, contract, reason)
        finally:
            journal.db.close()
