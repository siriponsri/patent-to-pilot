"""Offline identity and resume regressions; every transport below is fake."""
import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from patent_to_pilot.providers import (
    AttemptLedger, MockHTTPResponse, MockHTTPTransport, ModelDriftError,
    OpenRouterAdapter, OpenRouterHTTPTransport, ProviderCapabilities,
)
from patent_to_pilot.providers.pilot import (
    PilotError, config_for, dispatch, plan_hash, request_for, validate_approval,
)

ROOT = Path(__file__).parents[1]
IDENTITY_FIELDS = {
    "requested_provider", "requested_model", "requested_upstream_providers",
    "reported_model", "reported_provider", "reported_upstream_provider", "identity_error",
}


@pytest.fixture
def plan():
    return json.loads((ROOT / "configs/provider-pilot-plan.json").read_text(encoding="utf-8"))


def packet(job, *, provider, model=None, cost=0.0000132):
    body = {
        "model": job["model"] if model is None else model,
        "provider": provider,
        "choices": [{"message": {"content": json.dumps({"ack": "ready", "case_id": job["id"]})}}],
        "usage": {"prompt_tokens": 32, "completion_tokens": 25, "total_tokens": 57, "cost": cost},
    }
    return body


def make_adapter(plan, job, body, ledger=None):
    config = config_for(plan, "smoke", job, False)
    transport = MockHTTPTransport(MockHTTPResponse(200, body))
    caps = ProviderCapabilities(provider="openrouter", model=job["model"], structured_outputs=True)
    return OpenRouterAdapter(config, transport, caps, ledger), transport


@pytest.mark.parametrize("index,label,route", [
    (0, "Google AI Studio", "google-ai-studio"),
    (0, "google-ai-studio", "google-ai-studio"),
    (1, "OpenAI", "openai"),
    (1, "openai", "openai"),
])
def test_pinned_upstream_is_distinct_from_broker(plan, index, label, route):
    job = plan["phases"]["smoke"]["jobs"][index]
    adapter, transport = make_adapter(plan, job, packet(job, provider=label))
    result = adapter.complete(request_for(plan, job))
    assert result.requested_provider == "openrouter"
    assert result.reported_provider == label
    assert result.reported_upstream_provider == route
    assert result.requested_upstream_providers == [route]
    assert result.model == job["model"] and result.response_schema_valid is True
    assert result.attempts[0].reported_model == job["model"]
    assert result.actual_debit_usd == pytest.approx(0.0000132)
    assert len(transport.calls) == 1


@pytest.mark.parametrize("model,provider,reason", [
    (None, "OpenAI", "missing_model"),
    ("", "OpenAI", "model_mismatch"),
    ("google/gemini-2.5-flash-lite", "OpenAI", "model_mismatch"),
    ("openai/gpt-4.1-mini-2025-04-14", "OpenAI", "model_mismatch"),
    ("openai/gpt-4.1-mini", None, "missing_upstream_provider"),
    ("openai/gpt-4.1-mini", "openrouter", "upstream_provider_mismatch"),
    ("openai/gpt-4.1-mini", "Google AI Studio", "upstream_provider_mismatch"),
    ("openai/gpt-4.1-mini", "OpenAI/priority", "upstream_provider_mismatch"),
    ("openai/gpt-4.1-mini", "Azure", "upstream_provider_mismatch"),
])
def test_missing_or_unapproved_identity_rejected_with_charge_retained(plan, model, provider, reason):
    job = plan["phases"]["smoke"]["jobs"][1]
    body = packet(job, provider=provider)
    body["model"] = model
    if model is None:
        del body["model"]
    if provider is None:
        del body["provider"]
    adapter, transport = make_adapter(plan, job, body)
    with pytest.raises(ModelDriftError):
        adapter.complete(request_for(plan, job))
    entry = adapter.attempts[0]
    assert entry.identity_error == reason
    assert entry.requested_provider == "openrouter"
    assert entry.requested_model == job["model"]
    assert entry.requested_upstream_providers == ["openai"]
    assert entry.status == "model_drift" and entry.reservation_status == "settled"
    assert entry.observed_cost_usd == pytest.approx(0.0000132)
    assert adapter.ledger.actual_debit_usd == pytest.approx(0.0000132)
    assert len(transport.calls) == 1


def test_identity_is_sanitized_and_present_before_settlement_and_validation(plan):
    job = plan["phases"]["smoke"]["jobs"][1]
    fake_secret = "FAKE_SECRET_IDENTITY_ONLY_DO_NOT_LOG"
    bad_label = "Authorization: Bearer " + fake_secret + "\r\nextra"

    class ObservingLedger(AttemptLedger):
        def settle(self, entry, **kwargs):
            assert entry.requested_model == job["model"]
            assert entry.reported_model.startswith("redacted-sha256:")
            assert entry.reported_provider.startswith("redacted-sha256:")
            assert entry.identity_error == "model_mismatch"
            return super().settle(entry, **kwargs)

    ledger = ObservingLedger()
    adapter, _ = make_adapter(plan, job, packet(job, provider=bad_label, model=bad_label), ledger)
    with pytest.raises(ModelDriftError):
        adapter.complete(request_for(plan, job))
    encoded = json.dumps([a.model_dump() for a in ledger.attempts])
    assert fake_secret not in encoded and "Authorization" not in encoded
    assert ledger.actual_debit_usd == pytest.approx(0.0000132)


def approval(plan, state):
    receipt = dict(approved=True, funding_confirmed=True, plan_sha256=plan_hash(plan),
                   phase="smoke", phase_spend_cap_usd=plan["phases"]["smoke"]["cumulative_spend_cap_usd"],
                   phase_attempts_max=2, owner_reference="SYNTHETIC OFFLINE TEST ONLY",
                   state_path=str(state.resolve()))
    validate_approval(plan, "smoke", receipt, state)
    return receipt


def factory(calls, *, wrong_model=False):
    class FakeTransport:
        is_mock = True

        def __init__(self, job):
            self.job = job

        def send(self, **kwargs):
            calls.append(self.job["id"])
            provider = "Google AI Studio" if self.job["model"].startswith("google/") else "OpenAI"
            body = packet(self.job, provider=provider)
            if wrong_model:
                body["model"] = "openai/gpt-4.1-mini"
            return MockHTTPResponse(200, body)

    return FakeTransport


def seed_legacy_failure(plan, state, calls):
    receipt = approval(plan, state)
    result = dispatch(plan, state, "smoke", factory(calls, wrong_model=True), live=True, approval=receipt)
    assert result["status"] == "STOPPED_ERROR" and result["attempts"] == 1
    with sqlite3.connect(state) as db:
        raw = json.loads(db.execute("SELECT reservation FROM attempts WHERE seq=1").fetchone()[0])
        assert raw["reported_model"].startswith("redacted-sha256:")
        assert raw["reported_provider"] == "Google AI Studio"
        assert raw["identity_error"] == "model_mismatch"
        # Simulate the historical pre-repair schema in this fake TEMP DB only.
        for field in IDENTITY_FIELDS:
            raw.pop(field)
        db.execute("UPDATE attempts SET reservation=? WHERE seq=1", (json.dumps(raw),))
        first_row = db.execute("SELECT * FROM attempts WHERE seq=1").fetchone()
    return receipt, first_row


def test_remaining_gpt_only_resume_preserves_legacy_failure_debit_and_quota(plan, tmp_path):
    state = tmp_path / "fake-live.sqlite3"
    calls = []
    receipt, original = seed_legacy_failure(plan, state, calls)
    result = dispatch(plan, state, "smoke", factory(calls), live=True, approval=receipt)
    assert calls == ["smoke-1-1", "smoke-1-2"]
    assert result["attempts"] == 2 and result["actual_debit_usd"] == pytest.approx(0.0000264)
    assert result["status"] == "PHASE_FAILED"  # Spent/failed Gemini is never relabeled success.
    assert result["completed_jobs"] == ["smoke-1-2"]
    assert result["unknown_pending"] == [] and result["reserved_cost_usd"] == 0
    with sqlite3.connect(state) as db:
        assert db.execute("SELECT * FROM attempts WHERE seq=1").fetchone() == original
        assert db.execute("SELECT digest,mode FROM meta").fetchone() == (plan_hash(plan), "live")
        c, raw = db.execute("SELECT config,reservation FROM attempts WHERE seq=2").fetchone()
        assert json.loads(c)["max_spend_usd"] == 0.6
        assert json.loads(raw)["reported_upstream_provider"] == "openai"
    again = dispatch(plan, state, "smoke", factory(calls), live=True, approval=receipt)
    assert again["attempts"] == 2 and len(calls) == 2
    with pytest.raises(PilotError, match="live blocked"):
        dispatch(plan, state, "pilot", factory(calls), live=True, approval=receipt)
    assert len(calls) == 2


def test_resume_cap_includes_prior_failed_attempt_debit(plan, tmp_path):
    plan = copy.deepcopy(plan)
    # GPT reservation alone fits; reservation + prior debit does not.
    plan["phases"]["smoke"]["cumulative_spend_cap_usd"] = 0.42144
    state = tmp_path / "fake-live.sqlite3"
    calls = []
    receipt, original = seed_legacy_failure(plan, state, calls)
    result = dispatch(plan, state, "smoke", factory(calls), live=True, approval=receipt)
    assert result["status"] == "BLOCKED_BUDGET"
    assert result["attempts"] == 1 and calls == ["smoke-1-1"]
    assert result["actual_debit_usd"] == pytest.approx(0.0000132)
    with sqlite3.connect(state) as db:
        assert db.execute("SELECT * FROM attempts WHERE seq=1").fetchone() == original


def test_approved_plan_and_outgoing_payloads_unchanged(plan):
    assert plan_hash(plan) == "6cf9bd14059f1df9f11ff6f913d31bcc5e5c60f3f993ac4766621bf1c7c148b2"
    expected = [
        "f31be6bc37b4c522b7bfa38a7e79d17e0000e9e129ee3ad332a90f1133fcadf9",
        "0696c7d66be448776810d1981129ffcf9849388330ec383e6a359bf8722e22ba",
    ]
    for job, digest in zip(plan["phases"]["smoke"]["jobs"], expected):
        payload = OpenRouterHTTPTransport._request_payload(config_for(plan, "smoke", job, True), request_for(plan, job))
        assert hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest() == digest
