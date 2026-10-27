import copy
import hashlib
import json
import sqlite3
from contextlib import nullcontext
from pathlib import Path

import pytest

from patent_to_pilot.providers import MockHTTPResponse, TimeoutError
from patent_to_pilot.providers.paired import (
    PairError,
    body_hash,
    config_for,
    plan_hash,
    request_for,
    run_paired,
    validate_pair_plan,
)
from patent_to_pilot.providers.pilot import dispatch, exclusive_run
from patent_to_pilot.providers.pilot import plan_hash as pilot_plan_hash
from patent_to_pilot.providers.pilot import PilotError


ROOT = Path(__file__).parents[1]
PLAN_PATH = ROOT / "configs/provider-paired-revalidation-plan.json"


@pytest.fixture
def published_plan():
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def plan(published_plan, tmp_path):
    """Behavior tests bind to an isolated authored journal, never live receipts.

    The published plan/hash contract is tested separately without changing it.
    Seed the historical shape through the real ledger with mock-only transport;
    no journal bytes, credentials, or untracked data are imported.
    """
    pilot = json.loads((ROOT / "configs/provider-pilot-plan.json").read_text(encoding="utf-8"))
    original = tmp_path / "synthetic-prior.sqlite3"
    seed_approval = dict(approved=True, funding_confirmed=True, phase="smoke",
        phase_attempts_max=2, phase_spend_cap_usd=0.6, plan_sha256=pilot_plan_hash(pilot),
        owner_reference="SYNTHETIC UNIT TEST ONLY", state_path=str(original.resolve()))

    def history_response(job, *, wrong=False, cost=0.0000132):
        return MockHTTPResponse(200, {
            "model": "openai/gpt-4.1-mini" if wrong else job["model"],
            "provider": "Google AI Studio" if job["model"].startswith("google/") else "OpenAI",
            "choices": [{"message": {"content": json.dumps({"ack": "ready", "case_id": job["id"]})}}],
            "usage": {"prompt_tokens": 32, "completion_tokens": 25, "total_tokens": 57, "cost": cost},
        })

    dispatch(pilot, original, "smoke", factory([], lambda job: history_response(job, wrong=True)),
        live=True, approval=seed_approval)
    seeded = dispatch(pilot, original, "smoke", factory([], lambda job: history_response(job, cost=0.00006)),
        live=True, approval=seed_approval)
    assert seeded["status"] == "PHASE_FAILED" and seeded["attempts"] == 2
    assert seeded["actual_debit_usd"] == pytest.approx(0.0000732)
    result = copy.deepcopy(published_plan)
    result["prior_history"]["path"] = str(original)
    result["prior_history"]["sha256"] = hashlib.sha256(original.read_bytes()).hexdigest()
    result["inactive_recovery_paths"] = [str(tmp_path / "absent-recovery.sqlite3")]
    return result


def approval(plan, state):
    return {
        "approved": True,
        "owner_reference": "synthetic test approval",
        "budget_reference": "USD 0.60 cumulative cap including historical debit",
        "plan_sha256": plan_hash(plan),
        "models": [job["model"] for job in plan["jobs"]],
        "max_attempts_total": 2,
        "attempts_per_model": 1,
        "retries": 0,
        "cumulative_spend_cap_usd": 0.6,
        "payload_sha256": {job["id"]: job["payload_sha256"] for job in plan["jobs"]},
        "state_path": str(state.resolve()),
        "secret_source": "existing explicit .env process only",
    }


def response(job, *, model=None, provider=None, cost=None):
    if provider is None:
        provider = job["provider_only"]
    if cost is None:
        cost = 0.0000132 if provider == "google-ai-studio" else 0.00006
    return MockHTTPResponse(200, {
        "model": job["model"] if model is None else model,
        "provider": provider,
        "choices": [{"message": {"content": json.dumps({"ack": "ready", "case_id": job["case_id"]})}}],
        "usage": {"prompt_tokens": 32, "completion_tokens": 25, "total_tokens": 57, "cost": cost},
    })


def factory(calls, callback=None, on_send=None):
    def make(job):
        class Transport:
            is_mock = True

            def send(self, **kwargs):
                calls.append(job["id"])
                if on_send:
                    on_send(job)
                return callback(job) if callback else response(job)

        return Transport()

    return make


def test_plan_and_payloads_match_approved_contract(published_plan):
    plan = published_plan
    validate_pair_plan(plan)
    assert plan_hash(plan) == "36a54d85884094a3e4a04c2ca149e8c3eb2b568af194446718751965e08f1ab2"
    assert [body_hash(config_for(plan, job, live=True), request_for(plan, job)) for job in plan["jobs"]] == [
        "f31be6bc37b4c522b7bfa38a7e79d17e0000e9e129ee3ad332a90f1133fcadf9",
        "0696c7d66be448776810d1981129ffcf9849388330ec383e6a359bf8722e22ba",
    ]


def test_pair_reserves_before_send_preserves_history_and_is_idempotent(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    calls = []
    original_hash = hashlib.sha256((ROOT / plan["prior_history"]["path"]).read_bytes()).hexdigest()

    def observe(job):
        with sqlite3.connect(state) as db:
            raw, finished = db.execute("SELECT reservation, finished FROM attempts ORDER BY seq DESC LIMIT 1").fetchone()
        assert json.loads(raw)["reservation_status"] == "pending"
        assert finished == 0

    result = run_paired(plan, state, approval(plan, state), factory(calls, on_send=observe), live=False)
    assert result["status"] == "PAIR_COMPLETE"
    assert result["attempts"] == 2 and calls == ["paired-1-gemini", "paired-1-gpt"]
    assert result["historical_debit_usd"] == pytest.approx(0.0000732)
    assert result["pair_actual_debit_usd"] == pytest.approx(0.0000732)
    assert result["cumulative_actual_debit_usd"] == pytest.approx(0.0001464)
    assert result["reserved_pair_cost_usd"] == 0
    assert hashlib.sha256((ROOT / plan["prior_history"]["path"]).read_bytes()).hexdigest() == original_hash

    again = run_paired(plan, state, approval(plan, state), factory(calls), live=False)
    assert again["status"] == "PAIR_COMPLETE" and again["attempts"] == 2 and len(calls) == 2


def test_known_identity_failure_stops_pair_without_retry_or_second_model(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    calls = []

    def wrong_identity(job):
        return response(job, model="openai/gpt-4.1-mini")

    result = run_paired(plan, state, approval(plan, state), factory(calls, wrong_identity), live=False)
    assert result["status"] == "PAIR_FAILED"
    assert result["attempts"] == 1 and calls == ["paired-1-gemini"]
    assert result["pair_actual_debit_usd"] == pytest.approx(0.0000132)
    assert result["failed_jobs"] == ["paired-1-gemini"]


def test_timeout_keeps_unknown_reservation_and_resume_does_not_replay(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    calls = []

    def timeout(job):
        raise TimeoutError("synthetic timeout with secret omitted")

    result = run_paired(plan, state, approval(plan, state), factory(calls, timeout), live=False)
    assert result["status"] == "BLOCKED_UNKNOWN_PENDING"
    assert result["unknown_pending"] == [1] and result["attempts"] == 1
    assert result["cumulative_actual_debit_usd"] == pytest.approx(0.0000732)
    assert result["reserved_pair_cost_usd"] == pytest.approx(0.1054576)

    again = run_paired(plan, state, approval(plan, state), factory(calls), live=False)
    assert again["status"] == "BLOCKED_UNKNOWN_PENDING" and len(calls) == 1


def test_power_loss_consumes_attempt_gate_and_does_not_replay(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    calls = []

    class PowerLoss(BaseException):
        pass

    def crash(job):
        raise PowerLoss()

    with pytest.raises(PowerLoss):
        run_paired(plan, state, approval(plan, state), factory(calls, crash), live=False)
    result = run_paired(plan, state, approval(plan, state), factory(calls), live=False)
    assert result["status"] == "BLOCKED_UNKNOWN_PENDING" and calls == ["paired-1-gemini"]


def test_live_approval_and_key_context_are_checked_before_dispatch(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    calls = []

    def forbidden(*args, **kwargs):
        raise AssertionError("transport or key context must not run")

    bad = approval(plan, state)
    bad["cumulative_spend_cap_usd"] = 10.0
    with pytest.raises(PairError, match="approval"):
        run_paired(plan, state, bad, forbidden, live=True, credential_context=forbidden)
    assert not state.exists() and not calls


def test_live_credential_context_is_callable_and_pair_still_uses_mock_transport(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    calls = []
    entered = []

    def context():
        entered.append(True)
        return nullcontext()

    result = run_paired(plan, state, approval(plan, state), factory(calls), live=True, credential_context=context)
    assert result["status"] == "PAIR_COMPLETE"
    assert entered == [True, True] and calls == ["paired-1-gemini", "paired-1-gpt"]


def test_changed_history_binding_is_fail_closed_before_state_creation(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    changed = copy.deepcopy(plan)
    changed["prior_history"]["sha256"] = "0" * 64
    with pytest.raises(PairError, match="historical Phase A"):
        run_paired(changed, state, approval(changed, state), factory([]), live=False)
    assert not state.exists()


def test_recovery_activity_blocks_pair_ownership(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    recovery_marker = tmp_path / "recovery.sqlite3.started.json"
    recovery_marker.write_text("active", encoding="utf-8")
    blocked = copy.deepcopy(plan)
    blocked["inactive_recovery_paths"] = [str(recovery_marker)]
    with pytest.raises(PairError, match="recovery path is active"):
        run_paired(blocked, state, approval(blocked, state), factory([]), live=False)
    assert not state.exists()


def test_concurrent_writer_and_marker_mismatch_fail_closed(plan, tmp_path):
    state = tmp_path / "pair.sqlite3"
    with exclusive_run(state):
        with pytest.raises(PilotError, match="another dispatcher"):
            run_paired(plan, state, approval(plan, state), factory([]), live=False)

    calls = []
    run_paired(plan, state, approval(plan, state), factory(calls), live=False, max_new_attempts=1)
    marker = Path(str(state) + ".started.json")
    marker.write_text(json.dumps({"plan_sha256": "wrong"}), encoding="utf-8")
    with pytest.raises(PairError, match="activation"):
        run_paired(plan, state, approval(plan, state), factory(calls), live=False)
    assert calls == ["paired-1-gemini"]
