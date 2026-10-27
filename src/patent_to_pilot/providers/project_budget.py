"""Atomic shared USD 5 envelope for new work; historical ledgers are untouched.

This module never loads credentials. Every future scientific/UI dispatch must use
this same database and policy, not the older engineering pilot ledgers.
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from .openrouter import BudgetExceededError

NANO = Decimal(1_000_000_000)
MODELS = {"google/gemini-2.5-flash-lite": "google-ai-studio", "openai/gpt-4.1-mini": "openai"}
OWNER_REFERENCE = "Sentinel_724546b367448191abc0389ac1968fa8"
POLICY = {"version": "ptp-owner-5usd-20261027", "owner_reference": OWNER_REFERENCE,
    "incremental_cap_nano_usd": 5_000_000_000,
    "phase_caps_nano_usd": {"calibration": 1_000_000_000, "subsequent": 4_000_000_000},
    "models": MODELS, "private_data": False, "fallbacks": False}
POLICY_HASH = hashlib.sha256(json.dumps(POLICY, sort_keys=True).encode()).hexdigest()


def money(value) -> int:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("finite nonnegative USD amount required") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError("finite nonnegative USD amount required")
    return int((amount * NANO).to_integral_value(rounding=ROUND_CEILING))


class ProjectBudget:
    """One writer transaction reserves before dispatch; no automatic release.

    A pending/unknown attempt blocks further dispatch. Idempotent settlement
    never duplicates a charge; reserve replay never authorizes another send.
    No raw prompt, key, response body or exception text is stored here.
    """
    def __init__(self, path: Path):
        self.path = Path(path)
        self.db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("CREATE TABLE IF NOT EXISTS budget_meta(policy_hash TEXT NOT NULL); CREATE TABLE IF NOT EXISTS budget_attempts(attempt_id TEXT PRIMARY KEY, phase TEXT NOT NULL, model TEXT NOT NULL, payload_sha256 TEXT NOT NULL, reserved INTEGER NOT NULL, actual INTEGER, state TEXT NOT NULL, breach INTEGER NOT NULL DEFAULT 0);")
        with self.transaction():
            hashes = self.db.execute("SELECT policy_hash FROM budget_meta").fetchall()
            if not hashes:
                self.db.execute("INSERT INTO budget_meta VALUES(?)", (POLICY_HASH,))
            elif hashes != [(POLICY_HASH,)]:
                raise ValueError("budget policy mismatch; cannot reset/rebind history")

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _snapshot(self):
        rows = self.db.execute("SELECT attempt_id,phase,model,payload_sha256,reserved,actual,state,breach FROM budget_attempts ORDER BY attempt_id").fetchall()
        usage = {p: 0 for p in POLICY["phase_caps_nano_usd"]}
        actual, pending, breach = 0, [], False
        for aid, phase, model, sha, reserved, cost, state, overrun in rows:
            usage[phase] += reserved if state != "settled" else cost
            actual += cost or 0
            if state != "settled":
                pending.append(aid)
            breach |= bool(overrun)
        return {"policy_sha256": POLICY_HASH, "attempts": len(rows), "actual_nano_usd": actual,
            "committed_nano_usd": sum(usage.values()), "phase_committed_nano_usd": usage,
            "unknown_or_pending": pending, "breach": breach, "dispatch_blocked": breach or bool(pending)}

    def snapshot(self):
        with self.transaction():
            return self._snapshot()

    def reserve(self, *, attempt_id: str, phase: str, model: str, provider: str,
                payload_sha256: str, upper_bound_usd, bound_verified: bool,
                data_class: str, subsequent_released: bool = False):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", attempt_id) or not re.fullmatch(r"[a-f0-9]{64}", payload_sha256):
            raise ValueError("safe attempt ID and exact payload hash required")
        if phase not in POLICY["phase_caps_nano_usd"] or MODELS.get(model) != provider or data_class not in {"synthetic", "public"}:
            raise ValueError("unapproved phase, model, provider or data class")
        if bound_verified is not True:
            raise BudgetExceededError("verified full-request price/token bound required")
        if phase == "subsequent" and subsequent_released is not True:
            raise BudgetExceededError("subsequent work requires readiness release")
        reserved = money(upper_bound_usd)
        if reserved <= 0:
            raise BudgetExceededError("positive conservative reservation required")
        with self.transaction():
            if self.db.execute("SELECT 1 FROM budget_attempts WHERE attempt_id=?", (attempt_id,)).fetchone():
                raise BudgetExceededError("attempt ID already consumed; replay cannot dispatch")
            state = self._snapshot()
            if state["dispatch_blocked"]:
                raise BudgetExceededError("dispatch blocked by pending billing or breach")
            if state["committed_nano_usd"] + reserved > POLICY["incremental_cap_nano_usd"] or state["phase_committed_nano_usd"][phase] + reserved > POLICY["phase_caps_nano_usd"][phase]:
                raise BudgetExceededError("shared project/phase cap exceeded")
            self.db.execute("INSERT INTO budget_attempts(attempt_id,phase,model,payload_sha256,reserved,state) VALUES(?,?,?,?,?,'pending')", (attempt_id,phase,model,payload_sha256,reserved))
        return attempt_id

    def settle(self, attempt_id: str, actual_usd):
        cost = None if actual_usd is None else money(actual_usd)
        breach = False
        with self.transaction():
            row = self.db.execute("SELECT reserved,actual,state,breach FROM budget_attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
            if row is None:
                raise ValueError("unknown attempt")
            reserved, old_cost, state, old_breach = row
            if state == "settled":
                if cost != old_cost:
                    raise ValueError("conflicting settlement; history cannot be rewritten")
                breach = bool(old_breach)
            else:
                self.db.execute("UPDATE budget_attempts SET actual=?,state=? WHERE attempt_id=?", (cost, "settled" if cost is not None else "unknown_pending", attempt_id))
                totals = self._snapshot()
                breach = cost is not None and (cost > reserved or totals["committed_nano_usd"] > POLICY["incremental_cap_nano_usd"] or any(totals["phase_committed_nano_usd"][p] > cap for p,cap in POLICY["phase_caps_nano_usd"].items()))
                if breach:
                    self.db.execute("UPDATE budget_attempts SET breach=1 WHERE attempt_id=?", (attempt_id,))
        if breach:
            raise BudgetExceededError("observed debit retained; budget/reservation breach blocks future dispatch")


class BudgetedTransport:
    """Single manifest-bound attempt, wrapping the existing adapter transport seam.

    Ledger debit is recorded before the adapter validates schema/model identity.
    Retry needs a new manifest attempt ID and a new wrapper, within the same DB.
    This is a component, not authorization or a complete live scientific runner.
    """
    def __init__(self, transport, budget: ProjectBudget, binding: dict):
        self.transport, self.budget, self.binding = transport, budget, dict(binding)
        self.is_mock = transport.is_mock

    def preflight(self, *, config, request):
        # Existing adapter calls this only for an explicitly enabled live call.
        # Delegate key/HTTPS/config checks before consuming an attempt.
        check = getattr(self.transport, "preflight", None)
        if callable(check):
            check(config=config, request=request)

    def send(self, *, config, request):
        from .paired import body_hash
        binding = self.binding
        if config.retries != 0 or config.routing_only != [MODELS.get(config.model)] or config.allow_fallbacks or not config.require_parameters:
            raise ValueError("exact route, no fallback/retries and required parameters mandatory")
        if request.cost_upper_bound_usd is None or money(request.cost_upper_bound_usd) != money(binding["upper_bound_usd"]):
            raise ValueError("request reservation differs from bound manifest")
        if body_hash(config, request) != binding["payload_sha256"]:
            raise ValueError("request differs from bound manifest")
        self.budget.reserve(model=config.model, provider=config.routing_only[0], **binding)
        try:
            response = self.transport.send(config=config, request=request)
        except Exception:
            self.budget.settle(binding["attempt_id"], None)
            raise RuntimeError("provider transport failed; billing unknown_pending") from None
        payload = response.payload if isinstance(response.payload, dict) else {}
        usage = payload.get("usage")
        cost = usage.get("cost", payload.get("cost")) if isinstance(usage, dict) else payload.get("cost")
        try:
            self.budget.settle(binding["attempt_id"], cost)
        except ValueError:
            self.budget.settle(binding["attempt_id"], None)
            raise RuntimeError("provider accounting invalid; billing unknown_pending") from None
        if cost is None:
            raise BudgetExceededError("billing unknown_pending; future dispatch blocked")
        return response
