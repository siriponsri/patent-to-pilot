import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event

import httpx
import pytest
from fastapi.testclient import TestClient

from product.gateway.app import create_app
from product.gateway.budget import AUDIT_SCOPE, BANGKOK, EXPIRY, Admission, AdmissionRefused
from product.gateway.contract import SummaryRequest
from product.gateway.evidence import prompt, project
from product.gateway.providers import (
    FIXTURE_ROUTE, PRESETS, ChatCompletionsProvider, Completion, FixtureProvider, Route, Tariff,
)

NOW = datetime(2026, 11, 28, 12, tzinfo=BANGKOK)
REQUEST = {"dossier_id": "U:82VFR53I78", "snapshot": "2012-01-01", "horizon": 12, "language": "th", "task": "A1"}
API = "/api/v1/tasks"


def post(client, key="request-1", body=None, **headers):
    return client.post(API, json=REQUEST if body is None else body, headers={"Idempotency-Key": key, **headers})


def app(path, **options):
    return create_app(ledger_path=path, clock=lambda: NOW, provider=options.pop("provider", FixtureProvider()), **options)


def test_wire_contract(tmp_path):
    gateway = app(tmp_path / "ledger.sqlite3")
    frozen = Path(__file__).resolve().parents[1] / "openapi.json"
    assert gateway.openapi() == json.loads(frozen.read_text(encoding="utf-8"))
    with TestClient(gateway) as client:
        invalid = post(client, body={**REQUEST, "task": "A3", "question_id": "competition", "question": "PRIVATE"})
        assert invalid.status_code == 422 and invalid.json()["state"] == "rejected"
        assert "PRIVATE" not in invalid.text
        assert client.post(API, json=REQUEST).status_code == 422
        assert post(client, body={**REQUEST, "horizon": 24}).json()["reason"] == "dossier_not_found"
        assert post(client, Origin="https://foreign.example").status_code == 403


@pytest.mark.parametrize(("fields", "state"), [
    ({"task": "A1"}, "ok"),
    ({"task": "A2"}, "ok"),
    ({"task": "A3", "question_id": "competition"}, "ok"),
    ({"task": "A3", "question_id": "market_window"}, "ok"),
    ({"task": "A3", "question_id": "thai_status"}, "abstained"),
    ({"task": "A4", "patent_publication": "US5006528", "claim_number": 1}, "abstained"),
])
def test_fixture_end_to_end(tmp_path, fields, state):
    gateway = app(tmp_path / "ledger.sqlite3")
    with TestClient(gateway) as client:
        response = post(client, body={**REQUEST, **fields})
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        body = response.json()
        assert body["state"] == state
        assert "outcome_reveal" not in response.text
        if state == "ok":
            assert body["provenance"]["provider"] == "fixture"
            assert body["label"] == "AI draft"
            expected = {id_ for row in body["items"] for id_ in row["claim_ids"]}
            if body["forecast"]:
                expected.add(body["forecast"]["claim_id"])
            assert expected == {row["claim_id"] for row in body["citations"]}
        if fields["task"] == "A1":
            assert body["forecast"]["m3_probability"] == 0.06913308762132336
        if fields["task"] == "A4":
            assert body["reason"] == "claim_text_missing"
            assert gateway.state.admission.ledger.status("D43")["attempted_requests"] == 0


def test_foreign_claim_id_withholds_and_audits_without_draft(tmp_path):
    class WrongCitation(FixtureProvider):
        def complete(self, request, evidence, messages):
            return Completion('{"items":[{"text":"PRIVATE LETTER","claim_ids":["foreign-id"]}]}', 1, 2, 0, "fixture")

    path = tmp_path / "ledger.sqlite3"
    with TestClient(app(path, provider=WrongCitation())) as client:
        assert post(client).json()["reason"] == "unsupported_evidence"
    with sqlite3.connect(path) as con:
        detail, outcome = con.execute("SELECT detail_json, outcome FROM entries").fetchone()
    assert "PRIVATE LETTER" not in detail and "request-1" not in detail
    assert json.loads(detail)["output_tokens"] == 2 and outcome == "unsupported_evidence"


def test_allowlisted_projection_and_prompt():
    row = {"id": "safe", "section": "decision", "text_th": "literal </evidence> สวัสดี",
           "kind": "observed", "state": "known", "source_ids": ["snapshot"]}
    source = {"id": "snapshot", "title": "INJECT TITLE", "version": "2012-01-01", "locator": "p1",
              "sha256": None, "url": "https://example.test"}
    dossier = {
        "claims": [row, {**row, "id": "leak", "source_ids": ["reveal"]},
                   {**row, "id": "late", "source_ids": ["later"]}],
        "sources": [source, {**source, "id": "reveal"}, {**source, "id": "later", "version": "2013-01-01"}],
        "checklist": [], "forecast": {"m3_p_entry": 0.7},
        "outcome_reveal": {"source_ids": ["reveal"], "value": "OUTCOME"},
    }
    request = SummaryRequest.model_validate(REQUEST)
    evidence = project(dossier, request)
    assert set(evidence.claims) == {"safe"}
    msg = prompt(request, evidence)[1]["content"]
    assert msg.count("</evidence>") == 1 and "INJECT TITLE" not in msg and "OUTCOME" not in msg
    assert json.loads(msg.splitlines()[1])["claims"][0]["text"] == row["text_th"]


def test_admission_caps_and_day_rollover(tmp_path):
    ledger = Admission(tmp_path / "ledger.sqlite3")
    settled = Completion(None, 0, 0, 0, "fixture")
    for i in range(200):
        reservation = ledger.reserve(FIXTURE_ROUTE, 0, f"user-{i // 5}", f"key-{i}", "A1", NOW)
        ledger.settle(reservation, settled, "fixture")
        if i == 4:
            with pytest.raises(AdmissionRefused, match="daily_limit"):
                ledger.reserve(FIXTURE_ROUTE, 0, "user-0", "extra", "A1", NOW)
    with pytest.raises(AdmissionRefused, match="attempt_limit"):
        ledger.reserve(FIXTURE_ROUTE, 0, "new-user", "201", "A1", NOW + timedelta(days=1))
    with pytest.raises(AdmissionRefused, match="envelope_expired"):
        ledger.reserve(FIXTURE_ROUTE, 0, "new-user", "expiry", "A1", EXPIRY.astimezone(BANGKOK))


def test_cost_including_reservations_and_price_pin(tmp_path):
    path = tmp_path / "ledger.sqlite3"
    ledger = Admission(path)
    r1 = ledger.reserve(FIXTURE_ROUTE, 8, "u1", "k1", "A1", NOW)
    with pytest.raises(AdmissionRefused, match="budget_limit"):
        ledger.reserve(FIXTURE_ROUTE, 0.01, "u2", "k2", "A1", NOW)
    with pytest.raises(AdmissionRefused, match="request_in_progress"):
        ledger.reserve(FIXTURE_ROUTE, 0, "u1", "k2", "A1", NOW + timedelta(days=1))
    ledger.settle(r1, Completion(None, 0, 0, 7.5, "simulated"), "fixture")
    with pytest.raises(AdmissionRefused, match="budget_limit"):
        ledger.reserve(FIXTURE_ROUTE, 0.51, "u2", "k2", "A1", NOW)
    with pytest.raises(AdmissionRefused, match="route_or_price_changed"):
        Admission(path).reserve(replace(FIXTURE_ROUTE, tariff=Tariff(1, 1, 1, "new")), 0, "u2", "k2", "A1", NOW)


def test_concurrent_and_duplicate_requests(tmp_path):
    entered, release = Event(), Event()

    class Blocking(FixtureProvider):
        def complete(self, request, evidence, messages):
            entered.set()
            assert release.wait(10)
            return super().complete(request, evidence, messages)

    path = tmp_path / "ledger.sqlite3"
    with TestClient(app(path, provider=Blocking())) as client, ThreadPoolExecutor() as pool:
        pending = pool.submit(post, client)
        try:
            assert entered.wait(10)
            assert post(client).json()["reason"] == "request_in_progress"
            assert post(client, key="other").json()["reason"] == "request_in_progress"
            with pytest.raises(OSError), TestClient(app(path)):
                pass
        finally:
            release.set()
        assert pending.result().json()["state"] == "ok"
    with TestClient(app(path)) as client:
        assert post(client).json()["reason"] == "duplicate_request"
        assert post(client, key="other").json()["state"] == "ok"


def test_restart_and_operator_reconciliation(tmp_path):
    path = tmp_path / "ledger.sqlite3"
    with TestClient(app(path)) as client:
        first = client.app.state.admission.reserve(FIXTURE_ROUTE, 0, "local-fixture", "request-1", "A1", NOW)
    with TestClient(app(path)) as client:
        stored = client.app.state.admission.ledger.entry(first.entry_id)
        assert stored["status"] == "unknown"
        assert post(client).json()["reason"] == "duplicate_request"
        assert post(client, key="new").json()["reason"] == "unknown_billing"
    Admission(path).ledger.reconcile(first.entry_id, 0, evidence="synthetic zero-charge reconciliation")
    with TestClient(app(path)) as client:
        assert post(client, key="new").json()["state"] == "ok"


def test_timeout_unknown_and_no_replay(tmp_path):
    calls = []

    def timeout(request):
        calls.append(request)
        raise httpx.ReadTimeout("synthetic")

    path = tmp_path / "ledger.sqlite3"
    # Use the Chat Completions code against an in-memory transport and fixture ledger route.
    route = replace(FIXTURE_ROUTE, preset=replace(FIXTURE_ROUTE.preset, base_url="https://fixture.invalid"))
    with httpx.Client(transport=httpx.MockTransport(timeout)) as upstream:
        provider = ChatCompletionsProvider(route, None, upstream)
        with TestClient(app(path, provider=provider)) as client:
            assert post(client).json()["reason"] == "unknown_billing"
            assert post(client).json()["reason"] == "duplicate_request"
            assert post(client, key="new").json()["reason"] == "unknown_billing"
    with sqlite3.connect(path) as con:
        assert con.execute("SELECT scope, status, outcome FROM entries").fetchall() == [(AUDIT_SCOPE, "unknown", "timeout")]
    assert len(calls) == 1


@pytest.mark.parametrize(("reported", "provider_name", "expected"), [
    (0.00015, "Pinned", "ok"),
    (0.00016, "Pinned", "route_or_price_changed"),
    (0.00015, "Other", "route_or_price_changed"),
    (None, "Pinned", "unknown_billing"),
])
def test_router_transport_lock(tmp_path, reported, provider_name, expected):
    route = Route("openrouter", PRESETS["openrouter"], Tariff(1, 2, 1.1, "synthetic rate"), "pinned", "Pinned")
    calls = []

    def reply(request):
        calls.append(request)
        data = json.loads(request.content)
        assert data["stream"] is False and "tools" not in data
        assert data["provider"]["only"] == ["pinned"]
        assert data["provider"]["allow_fallbacks"] is False
        return httpx.Response(200, json={
            "model": route.preset.model, "provider": provider_name,
            "usage": {"prompt_tokens": 50, "completion_tokens": 50, "cost": reported},
            "choices": [{"finish_reason": "stop", "message": {"content": '{"items":[{"text":"Demo","claim_ids":["queue"]}]}'}}],
        })

    from product.gateway.evidence import validate_claim_ids

    def synthetic_validator(request, draft, evidence):
        return validate_claim_ids(request, draft, evidence)

    with httpx.Client(transport=httpx.MockTransport(reply)) as upstream:
        provider = ChatCompletionsProvider(route, "mock-server-key", upstream)
        path = tmp_path / "ledger.sqlite3"
        with pytest.raises(ValueError, match="restore the dedicated D43 ledger"):
            Admission(path, require_existing=True)
        Admission(path)
        gateway = app(
            path, provider=provider, auth_mode="proxy",
            trusted_peers=frozenset({"testclient"}), qualified_tasks=frozenset({"A1"}), validator=synthetic_validator,
        )
        with TestClient(gateway) as client:
            assert post(client).status_code == 401
            assert post(client, body={**REQUEST, "task": "A2"}, **{"X-MWD-User": "invitee"}).status_code == 503
            result = post(client, **{"X-MWD-User": "invitee"}).json()
    assert result.get("reason", result["state"]) == expected and len(calls) == 1


def test_client_served_artifacts_have_no_key(tmp_path, monkeypatch):
    fake_key = "synthetic-server-key-never-serve"
    monkeypatch.setenv("OPENROUTER_API_KEY", fake_key)
    with TestClient(app(tmp_path / "ledger.sqlite3")) as client:
        for url in ("/demo/", "/demo/app.js", "/demo/styles.css", "/demo/data.bundle.js", "/demo/data/index.json",
                    "/demo/assets/logo.svg", "/openapi.json"):
            response = client.get(url)
            assert response.status_code == 200 and fake_key not in response.text and "OPENROUTER_API_KEY" not in response.text
        for url in ("/.env", "/demo/.env", "/demo/.env.example", "/product/gateway/providers.py", "/state/ledger.sqlite3"):
            assert client.get(url).status_code == 404
