"""P4-T02: local, API and self-hosted execution modes (no network, no paid call, no real key).

Checks, through the same loopback routes the bundled UI calls:
* the active execution mode, the exact model id and the missing capabilities are reported without any connection;
* credentials are referenced by environment-variable NAME only: values never appear in a response, the store or the
  terminal, and a key pasted where a name belongs is refused without being echoed;
* with every optional endpoint missing (no key) or unreachable (a closed loopback port, or a self-hosted embedding
  server that goes away mid-project), Search, Compare and Inspect keep working on this computer.

The only model server is a tiny loopback Ollama-format double defined here (deterministic hashed vectors); it is never
offered as a product capability. ``loopback_only`` fails the test on any non-loopback connection attempt.
"""
from __future__ import annotations

import hashlib
import json
import re
import socket
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench import modes as M
from patent_to_pilot.workbench.guard import loopback_only
from patent_to_pilot.workbench.providers import ProviderClient, ProviderProfile, TEMPLATES, looks_like_secret
from patent_to_pilot.workbench.server import create_server

PID = C.SAMPLE_PROJECT_ID
FAKE = "FAKE-test-value-NOT-A-SECRET-p4t02-91c7"
KEY_NAMES = ("OPENROUTER_API_KEY", "TYPHOON_API_KEY", "ANTHROPIC_API_KEY")


def _template(pid: str) -> dict:
    return dict(next(t for t in TEMPLATES if t["profile_id"] == pid))


def _closed_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class EmbedDouble:
    """Loopback Ollama-format embedding server (``/api/tags``, ``/api/embed``)."""

    def __init__(self) -> None:
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                return

            def _out(self, obj):
                b = json.dumps(obj).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):  # noqa: N802
                self._out({"models": [{"name": "fake-embed:latest", "digest": "sha256:p4t02"}]})

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
                vecs = []
                for t in body["input"]:
                    v = [0.01] + [0.0] * 31
                    for tok in re.findall(r"\w+", t.lower()):
                        h = hashlib.sha256(tok.encode()).digest()
                        v[1 + h[0] % 31] += 1.0
                    vecs.append(v)
                self._out({"embeddings": vecs})

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.srv.shutdown()
        self.srv.server_close()


@pytest.fixture
def app(tmp_path, monkeypatch):
    for k in KEY_NAMES:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(M, "windows_user_env_present", lambda name: False)   # never read the real registry
    core = C.EvidenceCore(tmp_path / "store")
    srv = create_server(core, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    attempts: list = []
    try:
        with loopback_only(attempts):
            yield core, url, attempts
    finally:
        srv.shutdown()
        srv.server_close()
    assert attempts == []                       # no non-loopback connection was even attempted


def call(url, method, path, body=None, text=False):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data is not None else {})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode("utf-8")
            return r.status, (raw if text else json.loads(raw))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        return e.code, (raw if text else json.loads(raw))


def _search_inspect_compare(url, pid=PID):
    st, s = call(url, "POST", f"/api/projects/{pid}/search", {"query": "temperature range", "mode": "terms"})
    assert st == 200 and s["results"] and s["paid_model_calls"] == 0 and s["remote_calls"] == 0
    h = s["results"][0]
    st, x = call(url, "GET", f"/api/projects/{pid}/sources/{h['source_id']}/versions/{h['version_id']}"
                             f"/spans/{h['start_char']}/{h['end_char']}")
    assert st == 200 and x["quote"] == h["quote"] and x["stored_text_integrity"] == "verified"
    st, cmp_ = call(url, "POST", f"/api/projects/{pid}/compare", {})
    assert st == 200 and cmp_["run"]["status"] == "completed"
    return cmp_


# =========================================================================== mode, model and missing capabilities
def test_default_is_local_only_with_missing_capabilities_listed(app):
    core, url, _ = app
    call(url, "POST", "/api/demo/bootstrap", {})
    st, m = call(url, "GET", f"/api/projects/{PID}/execution-mode")
    assert st == 200 and m["network_probe"] is False
    a = m["active"]
    assert a["mode"] == "local_only" and a["mode_text"] == "Local only" and a["model_id"] is None
    assert a["retrieval_mode"] == "lexical" and "No model, no network" in a["summary"]
    assert set(m["modes"]) == {"local_only", "self_hosted_endpoint", "api_provider"}
    caps = {c["capability"]: c for c in m["capabilities"]}
    assert caps["local_search_compare_inspect"]["state"] == "available"
    assert caps["embedding"]["state"] == caps["chat"]["state"] == "not_configured"
    joined = "\n".join(m["missing"])
    assert "OPENROUTER_API_KEY not set → API calls that need it are unavailable" in joined
    assert "TYPHOON_API_KEY not set" in joined and "ANTHROPIC_API_KEY not set" in joined
    assert "No ready embedding model → hybrid (dense) retrieval unavailable" in joined
    assert all("local search, compare and inspect still work" in line or "PDF" in line for line in m["missing"])
    st, g = call(url, "GET", "/api/execution-mode")              # no project selected
    assert st == 200 and g["active"]["mode"] == "local_only"
    st, e = call(url, "GET", "/api/projects/no-such/execution-mode")
    assert st == 404


def test_every_optional_endpoint_missing_or_unreachable_does_not_block_local_work(app, monkeypatch):
    core, url, attempts = app
    call(url, "POST", "/api/demo/bootstrap", {})
    dead = f"http://127.0.0.1:{_closed_port()}"
    profiles = [_template("openrouter-qwen3-32b"), _template("api-claude-haiku"),
                {**_template("ollama-bge-m3"), "endpoint": dead},
                {**_template("local-qwen3-rerank-0.6b"), "endpoint": dead + "/v1"},
                {**_template("ollama-qwen3-8b"), "endpoint": dead}]
    for p in profiles:
        st, _ = call(url, "POST", "/api/providers", p)
        assert st == 200
    # the mode view never opens a connection: any provider transport call fails the test
    monkeypatch.setattr(ProviderClient, "_call", lambda *a, **k: pytest.fail("execution mode opened a connection"))
    st, m = call(url, "GET", f"/api/projects/{PID}/execution-mode")
    assert st == 200 and m["active"]["mode"] == "local_only"
    by_id = {p["profile_id"]: p for p in m["profiles"]}
    o = by_id["openrouter-qwen3-32b"]
    assert o["mode"] == "api_provider" and o["provider"] == "OpenRouter" and o["model_id"] == "qwen/qwen3-32b"
    assert not o["usable"] and "OPENROUTER_API_KEY not set for the Workbench server" in o["blockers"]
    assert by_id["api-claude-haiku"]["mode"] == "api_provider"
    assert by_id["api-claude-haiku"]["model_id"] == "claude-haiku-5-5"
    for pid in ("ollama-bge-m3", "local-qwen3-rerank-0.6b", "ollama-qwen3-8b"):
        assert by_id[pid]["mode"] == "self_hosted_endpoint" and "this computer" in by_id[pid]["where"]
        assert by_id[pid]["blockers"] == ["connection not checked yet"]
    caps = {c["capability"]: c for c in m["capabilities"]}
    assert caps["embedding"]["state"] == caps["chat"]["state"] == caps["rerank"]["state"] == "unavailable"
    assert any(line.startswith("Embedding model bge-m3 (ollama-bge-m3, Self-hosted endpoint) unavailable")
               for line in m["missing"])
    monkeypatch.undo()
    for k in KEY_NAMES:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(M, "windows_user_env_present", lambda name: False)
    # checks record the failure; the keyless API profile is blocked before any socket opens
    st, d = call(url, "POST", "/api/providers/ollama-bge-m3/check", {})
    assert st == 200 and d["status"] == "unavailable"
    st, d = call(url, "POST", "/api/providers/openrouter-qwen3-32b/check", {})
    assert st == 200 and d["status"] == "blocked"
    st, m = call(url, "GET", f"/api/projects/{PID}/execution-mode")
    assert {p["profile_id"]: p for p in m["profiles"]}["ollama-bge-m3"]["blockers"] == \
        ["endpoint or model unavailable at the last check"]
    # local work is untouched
    cmp_ = _search_inspect_compare(url)
    assert cmp_["run"]["counters"]["paid_model_calls"] == 0 and cmp_["run"]["counters"]["remote_calls"] == 0
    st, r = call(url, "POST", f"/api/projects/{PID}/runs", {})
    assert st == 200 and r["status"] == "completed"
    assert attempts == []


def test_hybrid_with_self_hosted_endpoint_shows_exact_model_then_falls_back_when_it_goes_away(app):
    core, url, _ = app
    call(url, "POST", "/api/demo/bootstrap", {})
    double = EmbedDouble()
    try:
        prof = {"profile_id": "p4t02-embed", "role": "embedding", "adapter": "ollama", "model_id": "fake-embed",
                "endpoint": double.url, "label": "test double"}
        assert call(url, "POST", "/api/providers", prof)[0] == 200
        st, d = call(url, "POST", "/api/providers/p4t02-embed/check", {})
        assert st == 200 and d["status"] == "ready"
        st, _ = call(url, "POST", f"/api/projects/{PID}/index", {"profile_id": "p4t02-embed"})
        assert st == 200
        st, _ = call(url, "POST", f"/api/projects/{PID}/retrieval", {"mode": "hybrid"})
        assert st == 200
        st, m = call(url, "GET", f"/api/projects/{PID}/execution-mode")
        a = m["active"]
        assert a["mode"] == "self_hosted_endpoint" and a["effective"] == "hybrid"
        assert a["model_id"] == "fake-embed" and a["served_model_name"] == "fake-embed:latest"
        assert a["model_digest"] == "sha256:p4t02" and "this computer" in a["where"]
        assert {c["capability"]: c for c in m["capabilities"]}["embedding"]["state"] == "available"
    finally:
        double.stop()
    # the endpoint is gone: the view still reports the recorded check (no probe) and says so
    st, m = call(url, "GET", f"/api/projects/{PID}/execution-mode")
    assert m["active"]["mode"] == "self_hosted_endpoint" and "no connection" in m["reachability_note"]
    cmp_ = _search_inspect_compare(url)                       # Search, Inspect and Compare all still work
    c = cmp_["run"]["counters"]
    assert c["retrieval_effective"] == "lexical_fallback" and "dense channel failed" in c["retrieval_note"]
    st, m = call(url, "GET", f"/api/projects/{PID}/execution-mode")
    assert m["active"]["last_run"]["retrieval_effective"] == "lexical_fallback"
    assert m["active"]["last_run"]["paid_model_calls"] == 0


def test_mode_classification_api_provider_and_remote_self_hosted(monkeypatch):
    monkeypatch.setattr(M, "windows_user_env_present", lambda name: None)
    o = ProviderProfile.from_dict(_template("openrouter-deepseek-v4-flash"))
    assert M.endpoint_mode(o)["mode"] == "api_provider" and M.endpoint_mode(o)["provider"] == "OpenRouter"
    t = ProviderProfile.from_dict({"profile_id": "typhoon", "role": "chat", "adapter": "openai_compatible",
                                   "model_id": "typhoon-test", "endpoint": "https://api.opentyphoon.ai/v1",
                                   "credential_ref": "TYPHOON_API_KEY", "allow_remote": True})
    assert M.endpoint_mode(t)["provider"] == "Typhoon (OpenTyphoon)"
    r = ProviderProfile.from_dict({"profile_id": "gpu-box", "role": "embedding", "adapter": "openai_compatible",
                                   "model_id": "Qwen/Qwen3-Embedding-0.6B", "endpoint": "http://gpu-box.example:8000/v1"})
    em = M.endpoint_mode(r)
    assert em["mode"] == "self_hosted_endpoint" and "another machine" in em["where"]
    st = M.profile_state(r, {"status": "ready", "requests_counted": 0})
    assert not st["usable"] and "non-local endpoint not allowed (allow_remote is off)" in st["blockers"]
    assert any("spending envelope" in b for b in st["blockers"])     # remote route: paid policy still applies


# =========================================================================== credentials: names only
def test_credential_values_never_leave_the_environment(app, monkeypatch, capsys, tmp_path):
    core, url, _ = app
    monkeypatch.setenv("OPENROUTER_API_KEY", FAKE)
    call(url, "POST", "/api/demo/bootstrap", {})
    assert call(url, "POST", "/api/providers", _template("openrouter-qwen3-32b"))[0] == 200
    bodies = []
    for path in ("/api/providers", "/api/credentials", "/api/execution-mode", f"/api/projects/{PID}/execution-mode",
                 "/api/capabilities"):
        st, raw = call(url, "GET", path, text=True)
        assert st == 200
        bodies.append(raw)
    assert all(FAKE not in b for b in bodies)
    creds = {c["name"]: c for c in json.loads(bodies[1])["credentials"]}
    assert creds["OPENROUTER_API_KEY"]["state"] == "set" and creds["OPENROUTER_API_KEY"]["present_in_server"] is True
    assert creds["OPENROUTER_API_KEY"]["used_by"][0] == "profile openrouter-qwen3-32b"
    assert creds["TYPHOON_API_KEY"]["state"] == "not_set"
    m = json.loads(bodies[3])
    o = {p["profile_id"]: p for p in m["profiles"]}["openrouter-qwen3-32b"]
    assert o["credential_present"] and o["blockers"] == ["connection not checked yet"]
    assert not any(line.startswith("OPENROUTER_API_KEY") for line in m["missing"])
    # there is no route that accepts a credential value
    st, e = call(url, "POST", "/api/credentials", {"name": "OPENROUTER_API_KEY", "value": FAKE})
    assert st == 404
    # a key pasted into the name field is refused and not echoed
    for pasted in ("sk_live_51HxQabcdefghijklmnop", "abcdef0123456789abcdef0123456789", FAKE):
        bad = {**_template("openrouter-qwen3-32b"), "profile_id": "pasted", "credential_ref": pasted}
        st, raw = call(url, "POST", "/api/providers", bad, text=True)
        assert st == 422 and pasted not in raw and "NAME, not a key" in raw
    store_bytes = b"".join(f.read_bytes() for f in tmp_path.rglob("*") if f.is_file())   # SQLite, WAL, files
    assert FAKE.encode() not in store_bytes and b"OPENROUTER_API_KEY" in store_bytes
    out = capsys.readouterr()
    assert FAKE not in out.out and FAKE not in out.err


def test_restart_needed_state_and_setup_steps_carry_the_name_only(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(M, "windows_user_env_present", lambda name: name == "OPENROUTER_API_KEY")
    c = M.credential_status("OPENROUTER_API_KEY", ["profile x"])
    assert c["state"] == "set_restart_needed" and c["present_in_server"] is False
    steps = c["setup"]
    assert '"OPENROUTER_API_KEY"' in steps["set_powershell"] and "-AsSecureString" in steps["set_powershell"]
    assert '"User"' in steps["set_powershell"] and "Start-PTP.cmd" in steps["after"]
    with pytest.raises(ValueError):
        M.setup_steps('X"; Remove-Item C:\\ -Recurse; "')
    assert looks_like_secret("sk_test_abc") and looks_like_secret("hf_abc")
    assert not looks_like_secret("OPENROUTER_API_KEY") and not looks_like_secret("PTP_TEST_ANTHROPIC_KEY")
    assert not looks_like_secret("HF_TOKEN") and not looks_like_secret("SK_SERVICE_KEY_NAME")


def test_real_registry_helper_refuses_non_names():
    assert M.windows_user_env_present("not a name") is None


def test_ui_shows_mode_label_and_mode_panel(app):
    core, url, _ = app
    st, html = call(url, "GET", "/", text=True)
    assert st == 200 and 'id="exec-mode"' in html and "Providers and execution mode" in html
    st, js = call(url, "GET", "/app.js", text=True)
    assert "/execution-mode" in js and "renderMode" in js and "mode-label" in js
    assert "value" not in re.findall(r'api\("POST", "/api/credentials"[^)]*\)', js)   # UI never posts a key
