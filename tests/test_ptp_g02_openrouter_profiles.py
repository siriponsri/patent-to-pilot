"""D7/D9 (22 Nov 2026): OpenRouter chat profiles in the Workbench (openai_compatible adapter, envelope E1).

No network: a loopback double stands in for OpenRouter and records the request body.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from patent_to_pilot.workbench.providers import (ProviderClient, ProviderError, ProviderProfile, TEMPLATES,
                                                 request_policy)

OPENROUTER = [t for t in TEMPLATES if t["profile_id"].startswith("openrouter-")]


def test_openrouter_templates_are_capped_paid_remote_with_reasoning_off():
    assert len(OPENROUTER) == 4
    assert sum(t["spend_cap_usd"] for t in OPENROUTER) <= 0.20 + 1e-9          # E1: Workbench checks <= USD 0.20
    for t in OPENROUTER:
        p = ProviderProfile.from_dict(dict(t))
        assert p.paid and not p.local and p.endpoint == "https://openrouter.ai/api/v1"
        assert p.credential_ref == "OPENROUTER_API_KEY" and p.max_requests > 0 and p.spend_cap_usd > 0
        r = p.request_options["reasoning"]
        assert r in ({"enabled": False}, {"effort": "none"})
        assert request_policy(p, True, 0) is None and request_policy(p, True, p.max_requests)


def test_request_options_are_validated():
    base = {"profile_id": "x", "role": "chat", "adapter": "openai_compatible", "model_id": "m",
            "endpoint": "http://127.0.0.1:9/v1"}
    with pytest.raises(ProviderError):
        ProviderProfile.from_dict({**base, "request_options": {"api_key": "nope"}})
    with pytest.raises(ProviderError):
        ProviderProfile.from_dict({**base, "role": "embedding", "request_options": {"temperature": 0}})
    with pytest.raises(ProviderError):
        ProviderProfile.from_dict({**base, "adapter": "ollama", "request_options": {"temperature": 0}})


@pytest.fixture()
def fake_openrouter():
    seen = []

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            return

        def do_POST(self):  # noqa: N802
            n = int(self.headers.get("Content-Length") or 0)
            seen.append({"path": self.path, "auth": self.headers.get("Authorization"),
                         "body": json.loads(self.rfile.read(n) or b"{}")})
            out = json.dumps({"choices": [{"message": {"content": "OK"}}],
                              "usage": {"prompt_tokens": 9, "completion_tokens": 1, "cost": 0.0000123}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/api/v1", seen
    srv.shutdown()
    srv.server_close()


def test_chat_sends_reasoning_off_and_records_cost(fake_openrouter, monkeypatch):
    url, seen = fake_openrouter
    t = dict(OPENROUTER[0], endpoint=url)                       # loopback stand-in, same profile otherwise
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-NOT-A-SECRET")
    events = []
    client = ProviderClient(ProviderProfile.from_dict(t), ledger=events.append)
    out = client.chat([{"role": "user", "content": "ping"}], max_tokens=8)
    assert out["text"] == "OK" and out["usage"]["cost_usd"] == pytest.approx(0.0000123)
    body = seen[0]["body"]
    assert seen[0]["path"] == "/api/v1/chat/completions" and seen[0]["auth"] == "Bearer test-key-NOT-A-SECRET"
    assert body["reasoning"] == t["request_options"]["reasoning"] and body["temperature"] == 0
    assert body["model"] == t["model_id"] and body["max_tokens"] == 8                 # options never override these
    assert events[-1]["status"] == "ok" and events[-1]["usage"]["cost_usd"] == pytest.approx(0.0000123)
