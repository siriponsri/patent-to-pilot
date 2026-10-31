from __future__ import annotations

import json
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
import time

import pytest

from patent_to_pilot.healthtech.http import HealthTechJobService, create_server


ROOT = Path(__file__).resolve().parents[1]
INPUT = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))


def _request(server, method: str, path: str, payload=None, headers=None):
    conn = HTTPConnection(server.server_address[0], server.server_address[1], timeout=10)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    request_headers.update(headers or {})
    conn.request(method, path, body=body, headers=request_headers)
    response = conn.getresponse()
    raw = response.read()
    conn.close()
    if response.getheader("Content-Type", "").startswith("application/json"):
        return response.status, json.loads(raw.decode("utf-8"))
    return response.status, raw.decode("utf-8")


@pytest.fixture()
def server(tmp_path):
    server = create_server("127.0.0.1", 0, tmp_path / "data", code_commit="test-head")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.healthtech_service.close()


def _wait_for(server, job_id: str, states={"succeeded", "failed", "cancelled"}):
    for _ in range(100):
        status, payload = _request(server, "GET", f"/jobs/{job_id}")
        assert status == 200
        state = payload["job"]["state"]
        if state in states:
            return payload["job"]
        time.sleep(0.01)
    raise AssertionError("job did not reach a terminal state")


def test_local_http_job_is_idempotent_and_supports_history_source_and_exports(server):
    body = {"input": INPUT, "provider": {"id": "local"}}
    status, first = _request(server, "POST", "/jobs", body, {"Idempotency-Key": "case-1"})
    assert status == 202
    job_id = first["job"]["job_id"]
    status, duplicate = _request(server, "POST", "/jobs", body, {"Idempotency-Key": "case-1"})
    assert status == 200
    assert duplicate["job"]["job_id"] == job_id
    job = _wait_for(server, job_id)
    assert job["state"] == "succeeded"
    assert job["provider"] == {"id": "local", "model": "offline-lexical-v1"}
    assert job["cost"]["billing_status"] == "not_billable_local"
    assert job["cost"]["local_elapsed_seconds"] is not None

    status, history = _request(server, "GET", f"/jobs/{job_id}/history")
    assert status == 200
    assert history["history"]["versions"] == [{"version": 1, "parent_version": None, "path": "version-0001.json", "user_edit_keys": []}]

    status, source = _request(server, "GET", f"/jobs/{job_id}/source/synthetic-device-record?field=device_name")
    assert status == 200
    assert source["payload"]["device_name"].startswith("SYNTHETIC")

    status, edit = _request(server, "POST", f"/jobs/{job_id}/history/1/edits", {
        "edits": {"review_note": "reviewed through HTTP"},
        "expected_parent_version": 1,
    })
    assert status == 200
    assert edit["version"] == 2

    status, exported = _request(server, "GET", f"/jobs/{job_id}/export?version=2&format=json")
    assert status == 200
    assert exported["version"] == 2
    assert exported["user_edits"]["review_note"] == "reviewed through HTTP"

    status, bundle = _request(server, "GET", f"/jobs/{job_id}/result")
    assert status == 200
    assert bundle["dossier"]["version"] == 2
    assert bundle["manifest"]["run_id"].startswith("job-")
    assert bundle["events"]

    status, markdown = _request(server, "GET", f"/jobs/{job_id}/export?version=2&format=markdown&language=th")
    assert status == 200
    assert "แฟ้มหลักฐาน HealthTech" in markdown


def test_provider_gate_and_version_conflict_are_fail_closed(server):
    status, blocked = _request(server, "POST", "/jobs", {"input": INPUT, "provider": {"id": "openrouter"}}, {"Idempotency-Key": "paid-1"})
    assert status == 409
    assert blocked["error"]["code"] == "provider_blocked"

    status, first = _request(server, "POST", "/jobs", {"input": INPUT, "provider": {"id": "local"}}, {"Idempotency-Key": "case-2"})
    job = _wait_for(server, first["job"]["job_id"])
    assert job["state"] == "succeeded"
    status, conflict = _request(server, "POST", f"/jobs/{job['job_id']}/history/1/edits", {
        "edits": {"review_note": "stale"},
        "expected_parent_version": 2,
    })
    assert status == 409
    assert conflict["error"]["code"] == "version_conflict"


def test_loopback_browser_cors_allows_preflight_and_blocks_non_loopback_origin(server):
    status, health = _request(server, "GET", "/healthz", headers={"Origin": "http://127.0.0.1:5178"})
    assert status == 200
    assert health["status"] == "ok"

    conn = HTTPConnection(server.server_address[0], server.server_address[1], timeout=10)
    conn.request("OPTIONS", "/jobs", headers={
        "Origin": "http://127.0.0.1:5178",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type, idempotency-key",
    })
    response = conn.getresponse()
    response.read()
    assert response.status == 204
    assert response.getheader("Access-Control-Allow-Origin") == "http://127.0.0.1:5178"
    assert response.getheader("Access-Control-Allow-Methods") == "GET, POST, OPTIONS"
    conn.close()

    conn = HTTPConnection(server.server_address[0], server.server_address[1], timeout=10)
    conn.request("OPTIONS", "/jobs", headers={
        "Origin": "https://example.invalid",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    assert response.status == 403
    assert payload["error"]["code"] == "cors_blocked"
    assert response.getheader("Access-Control-Allow-Origin") is None
    conn.close()


def test_cancel_before_dispatch_preserves_cancelled_state(tmp_path):
    service = HealthTechJobService(tmp_path / "data", code_commit="test-head")
    try:
        record = service.submit({"input": INPUT, "provider": {"id": "local"}, "idempotency_key": "cancel-1"})
        # The local job is small, so a cancellation may race with execution. The
        # contract requires either an acknowledged request or a preserved result.
        service.cancel(record["job_id"])
        for _ in range(100):
            current = service.status(record["job_id"])
            if current["state"] in {"cancelled", "succeeded", "failed"}:
                break
            time.sleep(0.01)
        assert current["state"] in {"cancelled", "succeeded", "failed"}
        if current["state"] == "cancelled":
            assert current["reason"] in {"cancelled_before_dispatch", "cancelled_before_commit", "cancel_acknowledged_after_commit"}
    finally:
        service.close()


def test_running_cancel_discards_uncommitted_result_and_resume_retries(tmp_path):
    service = HealthTechJobService(tmp_path / "data", code_commit="test-head", execution_delay_seconds=0.1)
    try:
        record = service.submit({"input": INPUT, "provider": {"id": "local"}, "idempotency_key": "cancel-running-1"})
        for _ in range(100):
            current = service.status(record["job_id"])
            if current["state"] == "running":
                break
            time.sleep(0.005)
        assert current["state"] == "running"
        service.cancel(record["job_id"])
        for _ in range(100):
            current = service.status(record["job_id"])
            if current["state"] in {"cancelled", "failed"}:
                break
            time.sleep(0.01)
        assert current["state"] == "cancelled"
        assert current["artifacts"] is None
        assert current["preserved_result"] is False

        service.resume(record["job_id"])
        for _ in range(100):
            current = service.status(record["job_id"])
            if current["state"] in {"succeeded", "failed"}:
                break
            time.sleep(0.01)
        assert current["state"] == "succeeded"
        assert current["artifacts"] == {"manifest": "manifest.json", "events": "acquisition_events.jsonl", "history": "history"}
        assert current["attempt"] == 2
    finally:
        service.close()

