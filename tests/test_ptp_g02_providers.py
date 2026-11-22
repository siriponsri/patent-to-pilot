"""G02 contract tests: provider ports, policy, index generations, hybrid retrieval and ingestion.

Model endpoints are replaced by ``ContractTestDouble``: a loopback HTTP server that speaks the Ollama,
OpenAI-compatible and Anthropic wire formats with deterministic hashed bag-of-words vectors. It exists only in this
test file and is never offered as a product capability. Real-model routes are checked separately (G02 STATUS).
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import re
import socket
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench.guard import RemoteCallBlocked, loopback_only
from patent_to_pilot.workbench.providers import ProviderError, ProviderProfile
from patent_to_pilot.workbench.server import create_server

FAKE_KEY = "test-key-NOT-A-SECRET-7f3a"


def _vec(text: str, salt: str, dim: int) -> list[float]:
    v = [0.0] * dim
    v[0] = 0.01
    for tok in re.findall(r"\w+", text.lower()):
        h = hashlib.sha256((salt + tok).encode("utf-8")).digest()
        v[1 + h[0] % (dim - 1)] += 1.0 if h[1] % 2 else -1.0
    return v


class ContractTestDouble:
    def __init__(self) -> None:
        self.salt, self.dim, self.down = "m1", 64, False
        self.hits: dict[str, int] = {}
        self.headers: list[dict] = []
        double = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                return

            def _out(self, code, obj):
                b = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def _body(self):
                n = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(n) or b"{}")

            def do_GET(self):  # noqa: N802
                double.hits[self.path] = double.hits.get(self.path, 0) + 1
                double.headers.append(dict(self.headers))
                if self.path == "/api/tags":
                    return self._out(200, {"models": [{"name": "fake-embed:latest", "digest": "sha256:" + double.salt},
                                                      {"name": "fake-chat:latest", "digest": "sha256:c"}]})
                if self.path in ("/v1/models",):
                    return self._out(200, {"data": [{"id": "fake-embed"}, {"id": "fake-rerank"}, {"id": "fake-chat"},
                                                    {"id": "claude-fake"}]})
                return self._out(404, {"error": "no route"})

            def do_POST(self):  # noqa: N802
                double.hits[self.path] = double.hits.get(self.path, 0) + 1
                double.headers.append(dict(self.headers))
                if double.down and self.path in ("/api/embed", "/v1/embeddings"):
                    return self._out(503, {"error": "model unloaded"})
                b = self._body()
                if self.path == "/api/embed":
                    return self._out(200, {"embeddings": [_vec(t, double.salt, double.dim) for t in b["input"]],
                                           "prompt_eval_count": 3})
                if self.path == "/v1/embeddings":
                    return self._out(200, {"data": [{"index": i, "embedding": _vec(t, double.salt, double.dim)}
                                                    for i, t in enumerate(b["input"])][::-1],
                                           "usage": {"prompt_tokens": 4, "total_tokens": 4}})
                if self.path == "/v1/rerank":
                    q = set(re.findall(r"\w+", b["query"].lower()))
                    return self._out(200, {"results": [
                        {"index": i, "relevance_score": len(q & set(re.findall(r"\w+", d.lower())))}
                        for i, d in enumerate(b["documents"])]})
                if self.path == "/api/chat":
                    content = json.dumps({"ok": True}) if b.get("format") else "OK"
                    return self._out(200, {"message": {"role": "assistant", "content": content},
                                           "prompt_eval_count": 5, "eval_count": 1})
                if self.path == "/v1/chat/completions":
                    content = json.dumps({"ok": True}) if b.get("response_format") else "OK"
                    return self._out(200, {"choices": [{"message": {"content": content}}],
                                           "usage": {"prompt_tokens": 5, "completion_tokens": 1}})
                if self.path == "/v1/messages":
                    if self.headers.get("x-api-key") != FAKE_KEY or not self.headers.get("anthropic-version"):
                        return self._out(401, {"error": "auth"})
                    if b.get("tools"):
                        blocks = [{"type": "tool_use", "name": "ptp_output", "input": {"ok": True}}]
                    else:
                        blocks = [{"type": "text", "text": "OK"}]
                    return self._out(200, {"content": blocks, "usage": {"input_tokens": 7, "output_tokens": 1}})
                return self._out(404, {"error": "no route"})

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


@pytest.fixture()
def double():
    d = ContractTestDouble()
    yield d
    d.close()


@pytest.fixture()
def core(tmp_path):
    return C.EvidenceCore(tmp_path / "store")


def embed_profile(double, pid="emb", **kw):
    return {"profile_id": pid, "role": "embedding", "adapter": "ollama", "model_id": "fake-embed",
            "endpoint": double.url, **kw}


def ready_hybrid(core, double, pid):
    core.registry.save(embed_profile(double))
    assert core.registry.check("emb")["status"] == "ready"
    core.build_index(pid, "emb")
    return core.set_retrieval_mode(pid, "hybrid")


def n_passages(core, pid):
    with core.store.read() as con:
        return len(core.generations.corpus_rows(con, pid))


def literal_citations_hold(core, pid):
    for cell in core.comparison(pid)["cells"]:
        c = cell["citation"]
        if c:
            r = core.resolve_citation(pid, c["source_id"], c["version_id"], c["passage_id"])
            sv = core.source_version(pid, c["source_id"], c["version_id"])
            assert sv["text"][r["start_char"]:r["end_char"]] == r["quote"]


# ------------------------------------------------------------------ profiles and policy
def test_profile_rejects_a_pasted_key_and_unknown_fields():
    with pytest.raises(ProviderError) as e:
        ProviderProfile.from_dict({"profile_id": "x", "role": "chat", "adapter": "anthropic_native",
                                   "model_id": "claude-fake", "credential_ref": "sk-ant-api03-abc"})
    assert e.value.kind == "config" and "NAME" in str(e.value)
    with pytest.raises(ProviderError):
        ProviderProfile.from_dict({"profile_id": "x", "role": "rerank", "adapter": "ollama", "model_id": "m"})
    with pytest.raises(ProviderError):
        ProviderProfile.from_dict({"profile_id": "x", "role": "chat", "adapter": "ollama", "model_id": "m",
                                   "api_key": "abc"})


def test_remote_endpoint_is_blocked_before_any_socket(core):
    core.registry.save({"profile_id": "remote", "role": "embedding", "adapter": "openai_compatible",
                        "model_id": "m", "endpoint": "http://203.0.113.5:8000/v1"})
    attempts: list = []
    with loopback_only(attempts):
        d = core.registry.check("remote")
    assert d["status"] == "blocked" and attempts == []
    assert "allow_remote" in d["last_check"]["items"][0]["detail"]


def test_paid_route_needs_an_envelope_and_the_key_never_reaches_the_store(core, double, monkeypatch, tmp_path):
    monkeypatch.setenv("PTP_TEST_ANTHROPIC_KEY", FAKE_KEY)
    base = {"profile_id": "claude", "role": "chat", "adapter": "anthropic_native", "model_id": "claude-fake",
            "endpoint": double.url, "credential_ref": "PTP_TEST_ANTHROPIC_KEY"}
    core.registry.save(base)
    d = core.registry.check("claude")
    assert d["status"] == "blocked" and double.hits.get("/v1/messages", 0) == 0
    assert any(i["check"] == "chat" and "spending envelope" in i["detail"] for i in d["last_check"]["items"])
    core.registry.save({**base, "spend_cap_usd": 1.0, "max_requests": 3})
    d = core.registry.check("claude")
    assert d["status"] == "ready", d["last_check"]
    states = {i["check"]: i["state"] for i in d["last_check"]["items"]}
    assert states["structured_output"] == "pass" and states["usage_reporting"] == "pass"
    assert d["requests_counted"] == 2 and d["credential_present"] is True
    client = core.registry.client("claude")
    client.chat([{"role": "user", "content": "hi"}], max_tokens=4)          # third request: allowed
    with pytest.raises(ProviderError) as e:
        client.chat([{"role": "user", "content": "hi"}], max_tokens=4)      # fourth: cap reached, no network
    assert e.value.kind == "blocked" and double.hits["/v1/messages"] == 3
    # the key went out only in the request header; nothing at rest contains it
    assert any({k.lower(): v for k, v in h.items()}.get("x-api-key") == FAKE_KEY for h in double.headers)
    core.store.backup(tmp_path / "copy.sqlite3")
    for f in list(core.store.data_dir.rglob("*")) + [tmp_path / "copy.sqlite3"]:
        if f.is_file():
            assert FAKE_KEY.encode() not in f.read_bytes(), f
    assert FAKE_KEY not in json.dumps(core.registry.list()) + json.dumps(core.registry.usage("claude"))


def test_missing_credential_is_a_clear_blocked_state(core, double, monkeypatch):
    monkeypatch.delenv("PTP_TEST_ABSENT_KEY", raising=False)
    core.registry.save({"profile_id": "c", "role": "chat", "adapter": "anthropic_native", "model_id": "claude-fake",
                        "endpoint": double.url, "credential_ref": "PTP_TEST_ABSENT_KEY"})
    d = core.registry.check("c")
    assert d["status"] == "blocked" and "PTP_TEST_ABSENT_KEY is not set" in d["last_check"]["items"][0]["detail"]
    assert d["credential_present"] is False


def test_each_role_and_adapter_is_checked_honestly(core, double):
    core.registry.save({"profile_id": "chat-o", "role": "chat", "adapter": "ollama", "model_id": "fake-chat",
                        "endpoint": double.url})
    core.registry.save({"profile_id": "chat-c", "role": "chat", "adapter": "openai_compatible", "model_id": "fake-chat",
                        "endpoint": double.url + "/v1"})
    core.registry.save({"profile_id": "emb-c", "role": "embedding", "adapter": "openai_compatible",
                        "model_id": "fake-embed", "endpoint": double.url + "/v1", "query_prefix": "Query: "})
    core.registry.save({"profile_id": "rr", "role": "rerank", "adapter": "openai_compatible", "model_id": "fake-rerank",
                        "endpoint": double.url + "/v1"})
    core.registry.save({"profile_id": "missing", "role": "chat", "adapter": "ollama", "model_id": "not-served",
                        "endpoint": double.url})
    for pid in ("chat-o", "chat-c", "emb-c", "rr"):
        d = core.registry.check(pid)
        assert d["status"] == "ready", (pid, d["last_check"])
        assert any(i["check"] == "streaming" or i["check"] == "context_limit" for i in d["last_check"]["items"])
    assert core.registry.check("missing")["status"] == "unavailable"
    rr = core.registry.check("rr")["last_check"]
    assert next(i for i in rr["items"] if i["check"] == "rerank")["ordered"] is True
    emb = core.registry.check("emb-c")["last_check"]
    assert emb["facts"]["dimension"] == 64
    # editing a checked profile invalidates its readiness until it is checked again
    core.registry.save({"profile_id": "emb-c", "role": "embedding", "adapter": "openai_compatible",
                        "model_id": "fake-embed", "endpoint": double.url + "/v1", "query_prefix": "Q: "})
    assert core.registry.status("emb-c") == "changed_since_check"
    caps = core.capabilities()
    assert caps["chat"]["state"] == "ready" and caps["rerank"]["state"] == "ready"


# ------------------------------------------------------------------ lexical path unchanged
def test_lexical_mode_is_the_default_and_unchanged(core):
    pid = core.bootstrap_sample()["project_id"]
    run = core.run_comparison(pid)
    assert core.retrieval_status(pid)["retrieval_mode"] == "lexical"
    assert not any(a["action_type"] == "retrieval_setup" for a in run["actions"])
    assert all("retrieval" not in a["detail"] for a in run["actions"])


def test_hybrid_needs_an_index_generation(core):
    pid = core.bootstrap_sample()["project_id"]
    with pytest.raises(C.Conflict):
        core.set_retrieval_mode(pid, "hybrid")


# ------------------------------------------------------------------ index generations
def test_generation_build_activate_and_hybrid_run(core, double):
    pid = core.bootstrap_sample()["project_id"]
    core.run_comparison(pid)
    with pytest.raises(C.Conflict):          # unchecked profile cannot build
        core.registry.save(embed_profile(double))
        core.build_index(pid, "emb")
    out = ready_hybrid(core, double, pid)
    st = core.retrieval_status(pid)
    gen = st["active_generation_id"]
    assert st["retrieval_mode"] == "hybrid" and st["active_freshness"] == "fresh"
    g = st["generations"][0]
    assert g["status"] == "active" and g["n_vectors"] == n_passages(core, pid) and g["dimension"] == 64
    assert (core.store.data_dir / g["vectors_path"] / "vectors.f32").stat().st_size == n_passages(core, pid) * 64 * 4
    # switching to hybrid re-ran the searches through the selective path
    assert out["result"]["retrieval"]["effective"] == "hybrid"
    run = core.run_comparison(pid)
    assert run["actions"][0]["action_type"] == "retrieval_setup" and run["actions"][0]["status"] == "ok"
    searches = [a for a in run["actions"] if a["action_type"] == "search_current_sources"]
    assert searches and all(a["detail"]["retrieval"] == {"used": "hybrid", "generation_id": gen} for a in searches)
    assert all("channels" in h for a in searches for h in a["detail"]["hits"])
    with core.store.read() as con:
        n = con.execute("SELECT COUNT(*) FROM dependencies d JOIN assessments a USING (assessment_id) WHERE "
                        "a.state='current' AND d.kind='index_generation' AND d.source_id=?", (gen,)).fetchone()[0]
    assert n == 6
    literal_citations_hold(core, pid)


def test_embedding_change_creates_a_new_generation_and_never_mixes_spaces(core, double):
    pid = core.bootstrap_sample()["project_id"]
    core.run_comparison(pid)
    ready_hybrid(core, double, pid)
    first = core.retrieval_status(pid)["active_generation_id"]
    same = core.build_index(pid, "emb")
    assert same["generation"]["generation_id"] == first and same["generation"]["reused_generation"] is True
    double.salt = "m2"                         # the server now serves a different model build (new digest)
    core.registry.check("emb")
    out = core.build_index(pid, "emb")
    second = out["generation"]["generation_id"]
    assert second != first and out["previous_generation_id"] == first
    assert out["generation"]["reused_vectors"] == 0 and out["generation"]["embedded_vectors"] == n_passages(core, pid)
    st = core.retrieval_status(pid)
    by_id = {g["generation_id"]: g for g in st["generations"]}
    assert by_id[first]["status"] == "retired" and by_id[second]["status"] == "active"
    assert by_id[first]["embedding_space_id"] != by_id[second]["embedding_space_id"]
    assert (core.store.data_dir / by_id[first]["vectors_path"] / "vectors.f32").exists()   # old one kept
    # searches bound to the old generation were re-executed under the new one
    assert set(out["result"]["revalidated_by_search"]) | set(out["result"]["reacquired"]) == {
        f"{c}/{r}" for c in ("CONCEPT-A", "CONCEPT-B") for r in ("R1", "R2", "R3")}
    with core.store.read() as con:
        kinds = {r[0] for r in con.execute(
            "SELECT DISTINCT d.source_id FROM dependencies d JOIN assessments a USING (assessment_id) WHERE "
            "a.state='current' AND d.kind='index_generation'")}
    assert second in kinds


def test_source_revision_refreshes_the_generation_and_reuses_unchanged_vectors(core, double):
    pid = core.bootstrap_sample()["project_id"]
    core.run_comparison(pid)
    ready_hybrid(core, double, pid)
    before = core.retrieval_status(pid)["active_generation_id"]
    embeds_before = double.hits.get("/api/embed", 0)
    out = core.apply_change(pid, "CHANGE-S2-V2")
    r = out["result"]
    s2_v2 = len(core.source_version(pid, "DEMO-S2", "v2")["passages"])
    assert r["retrieval"]["refreshed_from"] == before and r["retrieval"]["effective"] == "hybrid"
    st = core.retrieval_status(pid)
    new = next(g for g in st["generations"] if g["generation_id"] == st["active_generation_id"])
    assert new["generation_id"] != before and st["active_freshness"] == "fresh"
    assert new["embedded_vectors"] == s2_v2 and new["reused_vectors"] == n_passages(core, pid) - s2_v2  # only DEMO-S2 v2's passages
    assert double.hits["/api/embed"] > embeds_before
    cells = {f"{c['candidate_id']}/{c['requirement_id']}": c for c in core.comparison(pid)["cells"]}
    assert cells["CONCEPT-A/R2"]["outcome"] == "does_not_meet"
    assert cells["CONCEPT-A/R2"]["citation"]["version_id"] == "v2"
    # Concept B's vectors are unchanged: its searches are re-executed under the new generation and reused
    assert {k for k in r["revalidated_by_search"] if k.startswith("CONCEPT-B")} == {
        "CONCEPT-B/R1", "CONCEPT-B/R2", "CONCEPT-B/R3"}, r
    literal_citations_hold(core, pid)


def test_provider_failure_falls_back_to_lexical_with_a_recorded_reason(core, double):
    pid = core.bootstrap_sample()["project_id"]
    core.run_comparison(pid)
    ready_hybrid(core, double, pid)
    double.down = True
    run = core.run_comparison(pid)
    assert run["status"] == "completed"
    assert run["counters"]["retrieval_effective"] == "lexical_fallback"
    assert "dense channel failed" in run["counters"]["retrieval_note"]
    double.close()
    run = core.run_comparison(pid)            # endpoint gone entirely: still a working lexical run
    assert run["status"] == "completed" and run["counters"]["retrieval_effective"] == "lexical_fallback"


def test_profiles_and_generations_survive_restart(core, double, tmp_path):
    pid = core.bootstrap_sample()["project_id"]
    core.run_comparison(pid)
    ready_hybrid(core, double, pid)
    gen = core.retrieval_status(pid)["active_generation_id"]
    again = C.EvidenceCore(tmp_path / "store")
    assert again.registry.status("emb") == "ready"
    st = again.retrieval_status(pid)
    assert st["retrieval_mode"] == "hybrid" and st["active_generation_id"] == gen
    run = again.run_comparison(pid)
    assert run["counters"]["retrieval_effective"] == "hybrid"


# ------------------------------------------------------------------ ingestion
THAI_DOC = ("# บันทึกแนวคิด C\n\nโมดูลระบายความร้อนแบบพาสซีฟ\nไม่มีปั๊ม\n\n"
            "Powered circulation: no.\n").encode("utf-8")


def test_owner_project_ingestion_preserves_text_and_offsets(core):
    with pytest.raises(C.Conflict):
        core.ingest_document(C.SAMPLE_PROJECT_ID if core.bootstrap_sample() else "", "a.md", b"x", "CONCEPT-A")
    pid = core.create_project("My thermal review")["project_id"]
    out = core.ingest_document(pid, "concept-c notes.md", THAI_DOC, "CONCEPT-A")
    assert out["status"] == "ingested" and out["event_type"] == "source_addition" and out["version_id"] == "v1"
    assert out["source_id"] == "concept-c-notes" and out["passage_rule"] == "paragraph_blocks_v1"
    sv = core.source_version(pid, "concept-c-notes", "v1")
    assert sv["text"].encode("utf-8") == THAI_DOC and sv["data_origin"] == "owner_files"
    for p in sv["passages"]:
        r = core.resolve_citation(pid, "concept-c-notes", "v1", p["passage_id"])
        assert sv["text"][r["start_char"]:r["end_char"]] == r["quote"]
    assert core.ingest_document(pid, "concept-c notes.md", THAI_DOC, "CONCEPT-A")["status"] == "unchanged"
    for name, data, code in (("x.pdf", b"%PDF", "pdf_unavailable"), ("x.docx", b"abc", "unsupported_type"),
                             ("x.txt", "ไทย".encode("cp874"), "not_utf8"), ("x.txt", b"", "empty_file")):
        with pytest.raises(C.ValidationFailed) as e:
            core.ingest_document(pid, name, data, "CONCEPT-A")
        assert e.value.code == code
    with pytest.raises(C.ValidationFailed):
        core.ingest_document(pid, "y.md", THAI_DOC, "NO-SUCH-CANDIDATE")


def test_a_new_uncited_document_can_overturn_nothing_found(core):
    pid = core.create_project("Range review")["project_id"]
    core.ingest_document(pid, "a1.md", b"# A note\n\nPowered circulation: no.\n", "CONCEPT-A")
    core.run_comparison(pid)
    cells = {f"{c['candidate_id']}/{c['requirement_id']}": c for c in core.comparison(pid)["cells"]}
    assert cells["CONCEPT-A/R1"]["outcome"] == "meets"
    assert cells["CONCEPT-A/R2"]["outcome"] == "unknown"           # nothing found yet
    out = core.ingest_document(pid, "a2.md", b"# Range\n\nSupported temperature range: 35 to 75 \xc2\xb0C.\n",
                               "CONCEPT-A")
    r = out["result"]
    assert out["event_type"] == "source_addition"
    assert "CONCEPT-A/R2" in r["reacquired"] and "CONCEPT-A/R1" in r["revalidated_by_search"]
    assert all(k.startswith("CONCEPT-B") for k in r["outside_changed_scope"])
    cells = {f"{c['candidate_id']}/{c['requirement_id']}": c for c in core.comparison(pid)["cells"]}
    assert cells["CONCEPT-A/R2"]["outcome"] == "meets"
    assert cells["CONCEPT-A/R2"]["citation"]["source_id"] == "a2"
    # a revision of the same source through ingestion keeps v1 and cites v2
    out = core.ingest_document(pid, "a2.md", b"# Range\n\nSupported temperature range: 45 to 75 \xc2\xb0C.\n", "CONCEPT-A")
    assert out["event_type"] == "source_revision" and out["version_id"] == "v2"
    cells = {f"{c['candidate_id']}/{c['requirement_id']}": c for c in core.comparison(pid)["cells"]}
    assert cells["CONCEPT-A/R2"]["outcome"] == "does_not_meet" and cells["CONCEPT-A/R2"]["citation"]["version_id"] == "v2"
    assert core.source_version(pid, "a2", "v1")["status"] == "historical"
    events = [e["event_type"] for e in core.available_changes(pid)]
    assert events == ["source_addition", "source_addition", "source_revision"]


# ------------------------------------------------------------------ HTTP
def _req(base, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_http_routes_reach_the_same_core(core, double):
    srv = create_server(core, "127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        s, d = _req(base, "GET", "/api/providers")
        assert s == 200 and d["profiles"] == [] and len(d["templates"]) >= 5
        s, d = _req(base, "POST", "/api/providers", {"profile_id": "bad", "role": "chat", "adapter": "nope",
                                                     "model_id": "m"})
        assert s == 422 and d["error"] == "provider_config"
        s, d = _req(base, "POST", "/api/providers", embed_profile(double))
        assert s == 200 and d["status"] == "unchecked"
        s, d = _req(base, "POST", "/api/providers/emb/check", {})
        assert s == 200 and d["status"] == "ready"
        s, d = _req(base, "POST", "/api/projects", {"title": "HTTP project"})
        pid = d["project_id"]
        content = base64.b64encode(THAI_DOC).decode()
        s, d = _req(base, "POST", f"/api/projects/{pid}/documents",
                    {"filename": "c.md", "content_base64": content, "candidate_id": "CONCEPT-A"})
        assert s == 200 and d["status"] == "ingested"
        s, d = _req(base, "POST", f"/api/projects/{pid}/runs", {})
        assert s == 200 and d["status"] == "completed"
        s, d = _req(base, "POST", f"/api/projects/{pid}/index", {"profile_id": "emb"})
        assert s == 200 and d["generation"]["n_vectors"] >= 3
        s, d = _req(base, "POST", f"/api/projects/{pid}/retrieval", {"mode": "hybrid"})
        assert s == 200 and d["retrieval_mode"] == "hybrid"
        s, d = _req(base, "GET", f"/api/projects/{pid}/retrieval")
        assert d["retrieval_mode"] == "hybrid" and d["active_freshness"] == "fresh"
        s, d = _req(base, "GET", "/api/providers/emb/usage")
        assert s == 200 and d["events"] and all(e["cost_usd"] == "unknown" for e in d["events"])
    finally:
        srv.shutdown()
        srv.server_close()
