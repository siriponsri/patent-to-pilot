"""Fake transports and isolated TEMP journals only; no real credentials."""
import copy
import hashlib
import importlib.util
import json
import sqlite3
import sys
from contextlib import nullcontext
from pathlib import Path

import pytest

from patent_to_pilot.providers import MockHTTPResponse, ProviderRequest, TimeoutError
from patent_to_pilot.providers.pilot import PilotError, dispatch, exclusive_run, plan_hash
from patent_to_pilot.providers import recovery

ROOT = Path(__file__).parents[1]


def response(job, *, wrong=False, cost=0.0000132):
    label = "Google AI Studio" if job["model"].startswith("google/") else "OpenAI"
    return MockHTTPResponse(200, {
        "model": "openai/gpt-4.1-mini" if wrong else job["model"], "provider": label,
        "choices": [{"message": {"content": json.dumps(dict(ack="ready", case_id=job["id"]))}}],
        "usage": dict(prompt_tokens=32, completion_tokens=25, total_tokens=57, cost=cost),
    })


def factory(calls, callback=None):
    class FakeTransport:
        is_mock = True

        def __init__(self, job):
            self.job = job

        def send(self, **kwargs):
            calls.append(self.job["id"])
            return callback(self.job) if callback else response(self.job)
    return FakeTransport


@pytest.fixture
def prepared(tmp_path):
    plan = json.loads((ROOT / "configs/provider-pilot-plan.json").read_text(encoding="utf-8"))
    original, state = tmp_path / "original.sqlite3", tmp_path / "recovery.sqlite3"
    old_approval = dict(approved=True, funding_confirmed=True, phase="smoke", phase_attempts_max=2,
                        phase_spend_cap_usd=0.6, plan_sha256=plan_hash(plan),
                        owner_reference="SYNTHETIC TEST ONLY", state_path=str(original.resolve()))
    dispatch(plan, original, "smoke", factory([], lambda j: response(j, wrong=True)), live=True, approval=old_approval)
    result = dispatch(plan, original, "smoke", factory([], lambda j: response(j, cost=0.00006)), live=True, approval=old_approval)
    assert result["status"] == "PHASE_FAILED" and result["actual_debit_usd"] == pytest.approx(0.0000732)
    contract = recovery.recovery_contract(plan, original, state)
    approval = dict(approved=True, funding_confirmed=True, contract_sha256=plan_hash(contract),
                    contract=contract, owner_reference="SYNTHETIC RECOVERY APPROVAL")
    return plan, original, state, approval


def run(prepared, calls, callback=None, **kwargs):
    p, original, state, approval = prepared
    return recovery.run_recovery(p, original, state, approval, factory(calls, callback), **kwargs)


def test_only_one_durable_recovery_preserves_original_and_counts_prior_debit(prepared):
    p, original, state, approval = prepared
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    calls, credentials = [], []

    def credential_context():
        credentials.append("FAKE_CONTEXT_ONLY")
        return nullcontext()

    def observe(job):
        with sqlite3.connect(state) as db:
            raw, finished = db.execute("SELECT reservation,finished FROM attempts WHERE seq=1").fetchone()
        assert json.loads(raw)["reservation_status"] == "pending" and not finished
        return response(job)

    result = run(prepared, calls, observe, credential_context=credential_context)
    assert result["status"] == "RECOVERY_SUCCESS" and result["attempts"] == 1
    assert result["original_status"] == "PHASE_FAILED" and result["total_attempts"] == 3
    assert result["cumulative_actual_debit_usd"] == pytest.approx(0.0000864)
    assert result["cumulative_spend_cap_usd"] == 0.6
    assert hashlib.sha256(original.read_bytes()).hexdigest() == original_hash
    again = run(prepared, calls, credential_context=credential_context)
    assert again["status"] == "RECOVERY_SUCCESS"
    assert calls == ["smoke-1-1"] and len(credentials) == 1


def test_versioned_model_is_still_rejected_and_billing_identity_retained(prepared):
    calls = []

    def alias(job):
        reply = response(job)
        reply.payload["model"] = job["model"] + "-001"
        return reply

    result = run(prepared, calls, alias)
    assert result["status"] == "RECOVERY_FAILED" and result["reason"] == "ModelDriftError"
    assert result["recovery_debit_usd"] == pytest.approx(0.0000132)
    with sqlite3.connect(prepared[2]) as db:
        entry = json.loads(db.execute("SELECT reservation FROM attempts").fetchone()[0])
    assert entry["identity_error"] == "model_mismatch"
    assert entry["reported_provider"] == "Google AI Studio"
    assert entry["reported_model"].startswith("redacted-sha256:")
    assert run(prepared, calls)["status"] == "RECOVERY_FAILED" and len(calls) == 1


def test_unknown_billing_preserves_full_reservation_and_never_replays(prepared):
    calls = []

    def timeout(job):
        raise TimeoutError("FAKE_SECRET_MUST_NOT_BE_LOGGED")

    result = run(prepared, calls, timeout)
    assert result["status"] == "BLOCKED_UNKNOWN_PENDING" and result["unknown_pending"] == [1]
    assert result["cumulative_actual_debit_usd"] == pytest.approx(0.0000732)
    assert result["reserved_cost_usd"] == pytest.approx(0.1054576)
    with sqlite3.connect(prepared[2]) as db:
        raw = db.execute("SELECT reservation FROM attempts").fetchone()[0]
    assert "FAKE_SECRET_MUST_NOT_BE_LOGGED" not in raw
    assert run(prepared, calls)["status"] == "BLOCKED_UNKNOWN_PENDING" and len(calls) == 1


def test_power_loss_consumes_gate_and_does_not_replay(prepared):
    class PowerLoss(BaseException):
        pass

    def crash(job):
        raise PowerLoss()

    calls = []
    with pytest.raises(PowerLoss):
        run(prepared, calls, crash)
    assert run(prepared, calls)["status"] == "BLOCKED_UNKNOWN_PENDING" and len(calls) == 1


def test_deleted_recovery_database_cannot_reset_consumed_receipt(prepared):
    calls = []
    run(prepared, calls)
    prepared[2].unlink()
    with pytest.raises(PilotError, match="refuse reset"):
        run(prepared, calls)
    assert len(calls) == 1


def test_changed_history_or_relocated_receipt_blocks_before_key(prepared, tmp_path):
    p, original, state, approval = prepared

    def forbidden():
        raise AssertionError("credential context must not be entered")

    with pytest.raises(PilotError, match="approval"):
        recovery.run_recovery(p, original, tmp_path / "different.sqlite3", approval, factory([]), credential_context=forbidden)
    with sqlite3.connect(original) as db:
        entry = json.loads(db.execute("SELECT reservation FROM attempts WHERE seq=1").fetchone()[0])
        entry["observed_cost_usd"] = None
        db.execute("UPDATE attempts SET reservation=? WHERE seq=1", (json.dumps(entry),))
    with pytest.raises(PilotError, match="unresolved"):
        recovery.run_recovery(p, original, state, approval, factory([]), credential_context=forbidden)
    assert not state.exists()


def test_absent_approval_and_concurrent_writer_do_not_load_key(prepared):
    p, original, state, approval = prepared

    def forbidden():
        raise AssertionError("credential context must not be entered")

    with pytest.raises(PilotError, match="approval"):
        recovery.run_recovery(p, original, state, None, factory([]), credential_context=forbidden)
    assert not state.exists()
    with exclusive_run(state):
        with pytest.raises(PilotError, match="another dispatcher"):
            recovery.run_recovery(p, original, state, approval, factory([]), credential_context=forbidden)


def test_budget_reservation_includes_historical_debit(prepared, monkeypatch):
    real_request = recovery.request_for

    def expensive(*args):
        return real_request(*args).model_copy(update={"cost_upper_bound_usd": 0.6})

    monkeypatch.setattr(recovery, "request_for", expensive)
    calls = []
    result = run(prepared, calls)
    assert result["status"] == "RECOVERY_BLOCKED_PRE_DISPATCH" and result["reason"] == "BudgetExceededError"
    assert calls == [] and result["attempts"] == 0
    assert result["cumulative_actual_debit_usd"] == pytest.approx(0.0000732)


def test_default_cli_reads_no_key_and_creates_no_recovery_state(prepared, monkeypatch, capsys):
    p, original, state, approval = prepared
    path = ROOT / "scripts/run_provider_recovery.py"
    spec = importlib.util.spec_from_file_location("recovery_cli", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

    def forbidden(*a, **k):
        raise AssertionError("secret or transport accessed during preflight")

    monkeypatch.setattr(module, "scoped_env_file_key", forbidden)
    monkeypatch.setattr(module, "OpenRouterHTTPTransport", forbidden)
    monkeypatch.setattr(sys, "argv", [str(path), "--original-state", str(original), "--state", str(state), "--env-file", str(ROOT / ".env")])
    assert module.main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PREFLIGHT_ONLY"
    assert not state.exists()
