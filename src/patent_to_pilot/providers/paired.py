"""Fresh two-model paired revalidation with an isolated durable journal."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Callable

from .openrouter import (
    AttemptLedger,
    BudgetExceededError,
    ModelDriftError,
    OpenRouterAdapter,
    ProviderAttempt,
    ProviderCapabilities,
    ProviderConfig,
    ProviderRequest,
    ProviderResponse,
    TimeoutError,
)
from .pilot import PilotError, canonical, exclusive_run


PAIR_VERSION = "ptp-paired-revalidation-1"
PAIR_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
HISTORICAL_DEBIT = 0.0000732


class PairError(PilotError):
    """A paired-run contract or durable-state failure."""


def plan_hash(plan: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(plan).encode("utf-8")).hexdigest()


def body_hash(config: ProviderConfig, request: ProviderRequest) -> str:
    from .openrouter import OpenRouterHTTPTransport

    payload = OpenRouterHTTPTransport._request_payload(config, request)
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()


def _resolve(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else Path.cwd() / value


def _read_prior_history(path: str | Path) -> dict[str, Any]:
    resolved = _resolve(path)
    if not resolved.exists():
        raise PairError("prior Phase A journal is missing")
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    try:
        db = sqlite3.connect(f"file:{resolved.as_posix()}?mode=ro", uri=True)
        meta = db.execute("SELECT digest, mode FROM meta WHERE id=1").fetchone()
        rows = db.execute("SELECT seq, phase, job, reservation, finished FROM attempts ORDER BY seq").fetchall()
        reconciliations = db.execute("SELECT COUNT(*) FROM reconciliations").fetchone()[0]
    except (OSError, sqlite3.Error) as exc:
        raise PairError("prior Phase A journal cannot be read") from exc
    finally:
        try:
            db.close()
        except UnboundLocalError:
            pass
    attempts = []
    actual_debit = 0.0
    unknown = []
    for seq, phase, job, raw, finished in rows:
        try:
            reservation = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PairError("prior Phase A journal reservation is invalid") from exc
        cost = reservation.get("observed_cost_usd")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(float(cost)):
            actual_debit += float(cost)
        if not finished or reservation.get("reservation_status") != "settled":
            unknown.append(seq)
        attempts.append({
            "seq": seq,
            "phase": phase,
            "job": job,
            "status": reservation.get("status"),
            "cost_usd": cost,
            "finished": bool(finished),
        })
    return {
        "path": str(resolved),
        "sha256": digest,
        "meta": meta,
        "attempts": attempts,
        "attempt_count": len(attempts),
        "actual_debit_usd": round(actual_debit, 10),
        "unknown_pending": unknown,
        "reconciliations": reconciliations,
    }


def _pair_job(plan: dict[str, Any], job_id: str) -> dict[str, Any]:
    for job in plan["jobs"]:
        if job["id"] == job_id:
            return job
    raise PairError("unknown paired job")


def validate_pair_plan(plan: dict[str, Any]) -> None:
    if plan.get("version") != PAIR_VERSION or plan.get("endpoint") != PAIR_ENDPOINT:
        raise PairError("unsupported paired plan or endpoint")
    if plan.get("broker") != "openrouter":
        raise PairError("paired broker must be OpenRouter")
    if plan.get("cumulative_spend_cap_usd") != 0.60:
        raise PairError("paired cumulative cap must be USD 0.60")
    if plan.get("max_attempts_total") != 2 or plan.get("retries") != 0:
        raise PairError("paired plan requires exactly two attempts and zero retries")
    if plan.get("output_tokens") != 1500 or plan.get("allow_fallbacks") is not False or plan.get("require_parameters") is not True:
        raise PairError("paired routing or output guard is not exact")
    if plan.get("automatic_routing") is not False or plan.get("stream") is not False or plan.get("tools") != []:
        raise PairError("paired plan permits an unapproved request option")
    if len(plan.get("jobs", [])) != 2 or {job.get("attempts_max") for job in plan.get("jobs", [])} != {1}:
        raise PairError("paired plan must contain one attempt per model")
    expected_models = {
        "google/gemini-2.5-flash-lite": "google-ai-studio",
        "openai/gpt-4.1-mini": "openai",
    }
    seen_ids = set()
    seen_models = set()
    for job in plan["jobs"]:
        model = job.get("model")
        route = job.get("provider_only")
        if model not in expected_models or route != expected_models[model] or job.get("id") in seen_ids or model in seen_models:
            raise PairError("paired model or route is not exact")
        seen_ids.add(job.get("id"))
        seen_models.add(model)
        if not isinstance(job.get("prompt"), str) or not job["prompt"].startswith("Public synthetic engineering echo only."):
            raise PairError("paired payload is not the reviewed synthetic echo")
        if job.get("response_schema") != {
            "type": "object",
            "properties": {
                "ack": {"type": "string", "enum": ["ready"]},
                "case_id": {"type": "string", "enum": [job["case_id"]]},
            },
            "required": ["ack", "case_id"],
            "additionalProperties": False,
        }:
            raise PairError("paired response schema differs from the reviewed schema")
        if not isinstance(job.get("payload_sha256"), str) or len(job["payload_sha256"]) != 64:
            raise PairError("paired payload hash is missing")
    if seen_models != set(expected_models) or {job["model"] for job in plan["jobs"]} != set(expected_models):
        raise PairError("paired model set is incomplete")
    prior = plan.get("prior_history") or {}
    if prior.get("debit_usd") != HISTORICAL_DEBIT or prior.get("attempt_count") != 2:
        raise PairError("historical Phase A baseline is not preserved")
    if not prior.get("path") or not prior.get("sha256"):
        raise PairError("historical Phase A hash binding is missing")
    if plan.get("inactive_recovery_paths") is None:
        raise PairError("recovery inactivity gate is missing")


def request_for(plan: dict[str, Any], job: dict[str, Any]) -> ProviderRequest:
    request = ProviderRequest(
        prompt=job["prompt"],
        response_schema=job["response_schema"],
        input_tokens_estimate=job["context_length"],
        max_output_tokens=plan["output_tokens"],
        cost_upper_bound_usd=job["reserved_cost_usd"],
        request_id=job["request_id"],
    )
    return request


def config_for(plan: dict[str, Any], job: dict[str, Any], *, live: bool) -> ProviderConfig:
    remaining_cap = plan["cumulative_spend_cap_usd"] - plan["prior_history"]["debit_usd"]
    return ProviderConfig(
        model=job["model"],
        routing_only=[job["provider_only"]],
        allow_fallbacks=plan["allow_fallbacks"],
        require_parameters=plan["require_parameters"],
        max_price={"prompt": job["prompt_usd_per_million"], "completion": job["completion_usd_per_million"]},
        live_enabled=live,
        research_mode=True,
        allow_auto_routing=plan["automatic_routing"],
        max_input_tokens=job["context_length"],
        max_output_tokens=plan["output_tokens"],
        max_total_tokens=sum(item["context_length"] + plan["output_tokens"] for item in plan["jobs"]),
        max_spend_usd=remaining_cap,
        retries=plan["retries"],
        prompt_version=plan["version"],
        config_version=plan_hash(plan),
    )


def validate_pair_approval(plan: dict[str, Any], approval: dict[str, Any] | None, state: str | Path) -> None:
    expected = {
        "approved": True,
        "plan_sha256": plan_hash(plan),
        "models": [job["model"] for job in plan["jobs"]],
        "max_attempts_total": 2,
        "attempts_per_model": 1,
        "retries": 0,
        "cumulative_spend_cap_usd": 0.60,
        "payload_sha256": {job["id"]: job["payload_sha256"] for job in plan["jobs"]},
    }
    if not approval or any(approval.get(key) != value for key, value in expected.items()):
        raise PairError("fresh paired scope approval is missing or does not match the plan")
    if not approval.get("owner_reference") or not approval.get("budget_reference"):
        raise PairError("paired approval must identify owner scope and budget ceiling")
    raw_state = approval.get("state_path")
    if not isinstance(raw_state, str) or not Path(raw_state).is_absolute() or _resolve(raw_state).resolve().as_posix().casefold() != _resolve(state).resolve().as_posix().casefold():
        raise PairError("paired approval is bound to a different state path")
    if approval.get("secret_source") != "existing explicit .env process only":
        raise PairError("paired approval does not bind the approved secret source")


def _check_prior_and_recovery_gates(plan: dict[str, Any]) -> dict[str, Any]:
    prior = _read_prior_history(plan["prior_history"]["path"])
    if prior["sha256"] != plan["prior_history"]["sha256"] or prior["attempt_count"] != plan["prior_history"]["attempt_count"] or abs(prior["actual_debit_usd"] - HISTORICAL_DEBIT) > 1e-12 or prior["unknown_pending"]:
        raise PairError("historical Phase A journal changed or is not terminal")
    for raw in plan["inactive_recovery_paths"]:
        if _resolve(raw).exists():
            raise PairError("Gemini-only recovery path is active; pair ownership is not exclusive")
    return prior


class PairJournal:
    def __init__(self, path: str | Path, plan: dict[str, Any], *, live: bool, prior: dict[str, Any]) -> None:
        self.path = Path(path)
        self.db = sqlite3.connect(self.path)
        self.db.executescript(
            "CREATE TABLE IF NOT EXISTS meta(id INTEGER PRIMARY KEY CHECK(id=1), plan_sha256 TEXT, mode TEXT, prior_sha256 TEXT, prior_debit_usd REAL);"
            "CREATE TABLE IF NOT EXISTS attempts(seq INTEGER PRIMARY KEY, job_id TEXT, model TEXT, config TEXT, request TEXT, payload_sha256 TEXT, reservation TEXT, finished INTEGER DEFAULT 0, response TEXT);"
        )
        row = self.db.execute("SELECT plan_sha256, mode, prior_sha256, prior_debit_usd FROM meta WHERE id=1").fetchone()
        identity = (plan_hash(plan), "live" if live else "mock", prior["sha256"], prior["actual_debit_usd"])
        if row and row != identity:
            raise PairError("paired state plan, mode, or historical binding differs")
        if not row:
            self.db.execute("INSERT INTO meta VALUES(1,?,?,?,?)", identity)
            self.db.commit()

    def rows(self) -> list[dict[str, Any]]:
        result = []
        for seq, job_id, model, config, request, payload_sha256, reservation, finished, response in self.db.execute("SELECT seq, job_id, model, config, request, payload_sha256, reservation, finished, response FROM attempts ORDER BY seq"):
            result.append({
                "seq": seq,
                "job_id": job_id,
                "model": model,
                "config": json.loads(config),
                "request": json.loads(request),
                "payload_sha256": payload_sha256,
                "attempt": ProviderAttempt.model_validate_json(reservation),
                "finished": bool(finished),
                "response": response,
            })
        return result

    def summary(self, plan: dict[str, Any], prior: dict[str, Any], status: str, reason: str | None = None) -> dict[str, Any]:
        rows = self.rows()
        pair_debit = sum(float(row["attempt"].observed_cost_usd or 0.0) for row in rows)
        reserved = sum(float(row["attempt"].reserved_cost_usd or 0.0) for row in rows if row["attempt"].observed_cost_usd is None)
        unknown = [row["seq"] for row in rows if not row["finished"] or row["attempt"].reservation_status != "settled"]
        successes = [row["job_id"] for row in rows if row["finished"] and row["attempt"].status == "success"]
        return {
            "status": status,
            "reason": reason,
            "attempts": len(rows),
            "max_attempts_total": plan["max_attempts_total"],
            "retries": plan["retries"],
            "successful_jobs": successes,
            "failed_jobs": [row["job_id"] for row in rows if row["finished"] and row["attempt"].status != "success"],
            "unknown_pending": unknown,
            "historical_debit_usd": prior["actual_debit_usd"],
            "pair_actual_debit_usd": round(pair_debit, 10),
            "cumulative_actual_debit_usd": round(prior["actual_debit_usd"] + pair_debit, 10),
            "reserved_pair_cost_usd": round(reserved, 10),
            "cumulative_spend_cap_usd": plan["cumulative_spend_cap_usd"],
            "plan_sha256": plan_hash(plan),
        }


class DurablePairLedger(AttemptLedger):
    """Persist the one-attempt gate before transport dispatch."""

    def __init__(self, journal: PairJournal, plan: dict[str, Any], prior: dict[str, Any]) -> None:
        super().__init__()
        self.journal = journal
        self.plan = plan
        self.prior = prior
        self.current_seq: int | None = None
        self.current_job: dict[str, Any] | None = None
        for row in journal.rows():
            config = ProviderConfig.model_validate(row["config"])
            self.configure_cap(config.max_spend_usd)
            restored = super().reserve(config=config, request=ProviderRequest.model_validate(row["request"]), attempt=1)
            old = row["attempt"]
            restored.reservation_id = old.reservation_id
            super().settle(restored, usage={"input_tokens": old.observed_input_tokens, "output_tokens": old.observed_output_tokens, "total_tokens": old.observed_total_tokens}, cost=old.observed_cost_usd, outcome_known=old.reservation_status == "settled")
            restored.status = old.status

    def reserve(self, *, config: ProviderConfig, request: ProviderRequest, attempt: int) -> ProviderAttempt:
        if self.current_job is None:
            raise PairError("paired ledger job context is missing")
        rows = self.journal.rows()
        if len(rows) >= self.plan["max_attempts_total"] or any(row["job_id"] == self.current_job["id"] for row in rows):
            raise BudgetExceededError("paired attempt gate already consumed")
        entry = super().reserve(config=config, request=request, attempt=attempt)
        cursor = self.journal.db.execute(
            "INSERT INTO attempts(job_id, model, config, request, payload_sha256, reservation) VALUES(?,?,?,?,?,?)",
            (self.current_job["id"], self.current_job["model"], config.model_dump_json(), request.model_dump_json(), self.current_job["payload_sha256"], entry.model_dump_json()),
        )
        self.journal.db.commit()
        self.current_seq = cursor.lastrowid
        return entry

    def save(self, entry: ProviderAttempt, *, finished: bool = False, response: ProviderResponse | None = None) -> None:
        if self.current_seq is None:
            return
        self.journal.db.execute("UPDATE attempts SET reservation=?, finished=?, response=? WHERE seq=?", (entry.model_dump_json(), int(finished), response.model_dump_json() if response else None, self.current_seq))
        self.journal.db.commit()

    def settle(self, entry: ProviderAttempt, **kwargs: Any) -> ProviderAttempt:
        result = super().settle(entry, **kwargs)
        self.save(result)
        return result


def _terminal_failure(row: dict[str, Any]) -> bool:
    return row["finished"] and row["attempt"].reservation_status == "settled" and row["attempt"].status != "success"


def run_paired(
    plan: dict[str, Any],
    state: str | Path,
    approval: dict[str, Any] | None,
    transport_factory: Callable[[dict[str, Any]], Any],
    *,
    live: bool = False,
    credential_context: Callable[[], Any] = nullcontext,
    max_new_attempts: int | None = None,
) -> dict[str, Any]:
    validate_pair_plan(plan)
    state = Path(state).resolve()
    validate_pair_approval(plan, approval, state) if live else None
    prior = _check_prior_and_recovery_gates(plan)
    with exclusive_run(state):
        marker = Path(str(state) + ".started.json")
        activation = {"plan_sha256": plan_hash(plan), "state_path": str(state), "mode": "live" if live else "mock", "prior_history_sha256": prior["sha256"]}
        if marker.exists():
            try:
                marker_value = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise PairError("paired activation marker is unreadable") from exc
            if not state.exists() or marker_value != activation:
                raise PairError("paired activation exists but state is missing or differs; refuse reset")
        elif state.exists():
            raise PairError("paired state exists without activation marker; refuse reset")
        else:
            state.parent.mkdir(parents=True, exist_ok=True)
            with marker.open("x", encoding="utf-8") as handle:
                handle.write(canonical(activation))
                handle.flush()
                os.fsync(handle.fileno())
        journal = PairJournal(state, plan, live=live, prior=prior)
        try:
            rows = journal.rows()
            if any(not row["finished"] or row["attempt"].reservation_status != "settled" for row in rows):
                return journal.summary(plan, prior, "BLOCKED_UNKNOWN_PENDING", "billing/outcome evidence required; no automatic replay")
            if any(_terminal_failure(row) for row in rows):
                return journal.summary(plan, prior, "PAIR_FAILED", "known model, routing, schema, or transport failure; no retry")
            ledger = DurablePairLedger(journal, plan, prior)
            new_count = 0
            for job in plan["jobs"]:
                if any(row["job_id"] == job["id"] for row in journal.rows()):
                    continue
                if max_new_attempts is not None and new_count >= max_new_attempts:
                    return journal.summary(plan, prior, "PAUSED")
                ledger.current_job = job
                config = config_for(plan, job, live=live)
                request = request_for(plan, job)
                expected_hash = body_hash(config, request)
                if expected_hash != job["payload_sha256"]:
                    raise PairError("outgoing paired payload hash differs from approved plan")
                adapter = OpenRouterAdapter(
                    config,
                    transport_factory(job),
                    ProviderCapabilities(provider="openrouter", model=job["model"], structured_outputs=True),
                    ledger,
                )
                response = None
                error_name = None
                finished = False
                try:
                    with credential_context() if live else nullcontext():
                        response = adapter.complete(request)
                    finished = True
                except Exception as exc:
                    error_name = type(exc).__name__
                    current = ledger.attempts[-1] if ledger.attempts else None
                    finished = bool(current and current.reservation_status == "settled")
                finally:
                    if ledger.attempts and ledger.current_seq is not None:
                        ledger.save(ledger.attempts[-1], finished=finished, response=response)
                new_count += 1
                if journal.rows() and any(not row["finished"] or row["attempt"].reservation_status != "settled" for row in journal.rows()):
                    return journal.summary(plan, prior, "BLOCKED_UNKNOWN_PENDING", error_name)
                if error_name:
                    if error_name == "BudgetExceededError":
                        return journal.summary(plan, prior, "BLOCKED_BUDGET", error_name)
                    return journal.summary(plan, prior, "PAIR_FAILED", error_name)
            return journal.summary(plan, prior, "PAIR_COMPLETE" if len(journal.rows()) == 2 and all(row["attempt"].status == "success" for row in journal.rows()) else "PAIR_FAILED")
        finally:
            journal.db.close()
