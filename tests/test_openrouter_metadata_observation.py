import json
from decimal import Decimal
from pathlib import Path
import pytest

from patent_to_pilot.providers import metadata_observation as m

FAKE = "FAKE_TEST_ONLY_KEY_MUST_NOT_APPEAR"


def key_data(**extra):
    return {"limit": None, "limit_remaining": None, "usage": Decimal("0.0001464"),
            "is_management_key": False, "label": FAKE, "secret_extra": FAKE, **extra}


def test_only_selected_literal_key(tmp_path):
    file = tmp_path / "synthetic.env"
    file.write_text("OTHER_SECRET=never-return-this\nOPENROUTER_API_KEY='" + FAKE + "'\n")
    assert m.selected_key(file) == FAKE
    file.write_text("OPENROUTER_API_KEY=" + FAKE + "\nOPENROUTER_API_KEY=" + FAKE)
    with pytest.raises(m.ObservationError, match="^KEY_FILE_NOT_USABLE$"):
        m.selected_key(file)


def test_scope_usage_not_account_balance_or_history(monkeypatch):
    calls = []
    def request(key, path):
        calls.append(path)
        return {"status": "OBSERVED"}, key_data(creator_user_id=FAKE, organization_id=FAKE)
    monkeypatch.setattr(m, "endpoint_request", request)
    result = m.collect(FAKE, allow_credits_if_management=True)
    assert calls == ["/api/v1/key"]
    assert FAKE not in json.dumps(result)
    assert result["account_scope"] is None and result["history_completeness"] == "NOT_PROVEN"
    assert result["r1_actual_spend_usd"] is None and result["r1_unresolved_exposure_usd"] is None
    assert result["live_admission_enabled"] is False
    assert result["key_metadata"]["usage"] == "0.0001464"
    assert "remaining_credits_usd" not in json.dumps(result)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "1", None])
def test_invalid_usage_rejected(value):
    with pytest.raises(m.ObservationError):
        m.sanitize_key(key_data(usage=value))


def test_negative_availability_preserved_as_blocking_fact():
    data = m.sanitize_key(key_data(limit=2, limit_remaining=-1,
        budgets=[{"scope": "api_key", "limit_usd": 2, "spend_usd": 3, "remaining_usd": -1, "guardrail_id": FAKE}]))
    assert data["limit_remaining"] == "-1" and data["budgets"][0]["remaining_usd"] == "-1"
    assert FAKE not in json.dumps(data)


def test_credits_only_existing_management_key(monkeypatch):
    calls = []
    def request(key, path):
        calls.append(path)
        return {"status": "OBSERVED"}, key_data(is_management_key=True) if path.endswith("key") else {"total_credits": 8, "total_usage": Decimal("1.2")}
    monkeypatch.setattr(m, "endpoint_request", request)
    result = m.collect(FAKE, allow_credits_if_management=True)
    assert calls == ["/api/v1/key", "/api/v1/credits"]
    assert result["account_credits"]["remaining_credits_usd"] == "6.8"
    assert result["r1_actual_spend_usd"] is None


@pytest.mark.parametrize("status", [301, 302, 307, 308, 401, 403, 500])
def test_no_redirect_or_error_body_read_and_no_retries(monkeypatch, status):
    calls = []
    class Response:
        def read(self, *args):
            raise AssertionError("Do not read error body")
    Response.status = status
    class Connection:
        def __init__(self, host, timeout, context):
            assert host == "openrouter.ai" and timeout == 15
        def request(self, method, path, headers):
            assert method == "GET" and path == "/api/v1/key"
            assert headers["Authorization"] == "Bearer " + FAKE
            calls.append(path)
        def getresponse(self):
            return Response()
        def close(self):
            pass
    monkeypatch.setattr(m.http.client, "HTTPSConnection", Connection)
    status_result, data = m.endpoint_request(FAKE, "/api/v1/key")
    assert calls == ["/api/v1/key"] and data is None
    assert status_result == {"status": "HTTP_REJECTED", "http_status": status}
    assert FAKE not in json.dumps(status_result)


def test_unsafe_endpoint_rejected_before_connection(monkeypatch):
    monkeypatch.setattr(m.http.client, "HTTPSConnection", lambda *a, **k: pytest.fail("network called"))
    for path in ("/api/v1/chat/completions", "/api/v1/generation/content", "https://evil.test", "/api/v1/key?url=evil"):
        with pytest.raises(m.ObservationError, match="ENDPOINT_NOT_ALLOWED"):
            m.endpoint_request(FAKE, path)


def test_exception_details_not_exposed(monkeypatch, tmp_path):
    def connection(*args, **kwargs):
        raise RuntimeError(FAKE)
    monkeypatch.setattr(m.http.client, "HTTPSConnection", connection)
    status, data = m.endpoint_request(FAKE, "/api/v1/key")
    assert status == {"status": "TRANSPORT_OR_FORMAT_ERROR", "error_kind": "RESPONSE_FORMAT_ERROR"} and data is None
    monkeypatch.setattr(m, "selected_key", lambda path: FAKE)
    out = tmp_path / "receipt.json"
    assert m.run(tmp_path / "synthetic.env", out) == "TRANSPORT_OR_FORMAT_ERROR"
    assert FAKE not in out.read_text()


def test_existing_output_prevents_secret_read_and_network(monkeypatch, tmp_path):
    out = tmp_path / "existing.json"
    out.write_text("keep")
    monkeypatch.setattr(m, "selected_key", lambda path: pytest.fail("key read"))
    with pytest.raises(m.ObservationError, match="OBSERVATION_FAILED_NO_RAW_DETAILS"):
        m.run(tmp_path / "synthetic.env", out)
    assert out.read_text() == "keep"
