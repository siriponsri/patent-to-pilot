"""P4-T01b: requirement Remove / Undo lifecycle (owner fix plan of 23 Nov 2026, section 6).

Small hand-checkable fixtures, local only: no network, no model, no paid call. Each acceptance case of section 6 has a
test: remove before/after assessment, Undo, repeated clicks, source update, reindex, restart, in-flight stale commit,
readable history, zero requirements, no ID reuse and read-only projects."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench import relation_search as R
from patent_to_pilot.workbench.guard import loopback_only
from patent_to_pilot.workbench.server import create_server
from patent_to_pilot.workbench.workflow import Workflow

DOC_A = """# Spec A (test fixture)

## a-temp
The maximum operating temperature is 50 C.

## a-salt
A salt mist filter is fitted to every unit.

## a-module
The fan module is replaceable in the field.
"""

DOC_A2 = """# Spec A (test fixture, revised)

## a-temp
The maximum operating temperature is 55 C after the revision.

## a-salt
A salt mist filter is fitted to every unit.

## a-module
The fan module is replaceable in the field.
"""

DOC_B = """# Spec B (test fixture)

## b-temp
Rated maximum operating temperature: 45 C.

## b-module
A replaceable module slides out of the front.
"""

REQS = [{"requirement_id": "F1", "label": "maximum operating temperature"},
        {"requirement_id": "F2", "label": "salt mist filter"},
        {"requirement_id": "F3", "label": "replaceable module"}]


def b64(text: str) -> bytes:
    return text.encode("utf-8")


@pytest.fixture
def core(tmp_path):
    return C.EvidenceCore(tmp_path / "store")


def make_project(core) -> str:
    pid = core.create_project("Lifecycle test", [{"candidate_id": "A", "label": "Concept A"},
                                                 {"candidate_id": "B", "label": "Concept B"}], REQS)["project_id"]
    assert core.ingest_document(pid, "a.md", b64(DOC_A), "A", "spec-a")["status"] == "ingested"
    assert core.ingest_document(pid, "b.md", b64(DOC_B), "B", "spec-b")["status"] == "ingested"
    return pid


def obligations(core, pid) -> dict:
    with core.store.read() as con:
        return {(r[0], r[1]): r[2] for r in con.execute(
            "SELECT candidate_id, requirement_id, state FROM obligations WHERE project_id=?", (pid,))}


def assessments(core, pid, rid) -> list[dict]:
    with core.store.read() as con:
        return [dict(r) for r in con.execute("SELECT assessment_id, candidate_id, state FROM assessments WHERE "
                                             "project_id=? AND requirement_id=? ORDER BY created_at", (pid, rid))]


def active_ids(core, pid) -> list[str]:
    return [r["requirement_id"] for r in core.project_view(pid)["mission"]["requirements"]]


def cell_keys(core, pid) -> set:
    return {(c["candidate_id"], c["requirement_id"]) for c in core.comparison(pid)["cells"]}


def events(core, pid, kind) -> list[dict]:
    return [c for c in core.available_changes(pid) if c["event_type"] == kind]


# ------------------------------------------------------------------ remove before / after assessment
def test_remove_before_assessment(core):
    pid = make_project(core)
    out = core.archive_requirement(pid, "F2")
    assert out["status"] == "removed" and out["lifecycle_revision"] == 1 and out["mission_revision"] == 1
    assert out["requirement"] == {"requirement_id": "F2", "label": "salt mist filter", "query": "salt mist filter",
                                  "kind": "text", "match": "terms"}
    assert out["content_sha256"] == hashlib.sha256(C.dumps(out["requirement"]).encode("utf-8")).hexdigest()
    assert out["retired_assessments"] == []
    assert active_ids(core, pid) == ["F1", "F3"]
    obl = obligations(core, pid)
    assert obl[("A", "F2")] == obl[("B", "F2")] == "retired"
    run = core.run_comparison(pid)
    assert run["status"] == "completed" and run["counters"]["obligations_planned"] == 4
    assert {a["requirement_id"] for a in run["actions"] if a["requirement_id"]} == {"F1", "F3"}
    assert cell_keys(core, pid) == {("A", "F1"), ("A", "F3"), ("B", "F1"), ("B", "F3")}
    assert assessments(core, pid, "F2") == []
    assert obligations(core, pid)[("A", "F2")] == "retired"


def test_remove_after_assessment_keeps_readable_history(core):
    pid = make_project(core)
    core.run_comparison(pid)
    before = assessments(core, pid, "F1")
    assert [a["state"] for a in before] == ["current", "current"]
    out = core.archive_requirement(pid, "F1", {"expected_revision": 0})
    assert sorted(out["retired_assessments"]) == sorted(a["assessment_id"] for a in before)
    assert out["retired_obligations"] == ["A/F1 (was done)", "B/F1 (was done)"]
    # current reads: no F1 cell; the others are untouched
    assert ("A", "F1") not in cell_keys(core, pid) and ("A", "F2") in cell_keys(core, pid)
    # history: the retired assessments, their citations and a 'retired' event stay readable
    hist = [h for h in core.history(pid) if h["requirement_id"] == "F1"]
    assert {h["state"] for h in hist} == {"retired"} and len(hist) == 2
    a_hist = next(h for h in hist if h["candidate_id"] == "A")
    assert a_hist["citation"]["passage_id"] == "a-temp"
    assert [e["state"] for e in a_hist["events"]] == ["committed", "retired"]
    cit = core.resolve_citation(pid, "spec-a", "v1", "a-temp")
    assert {"candidate_id": "A", "requirement_id": "F1", "state": "retired"}.items() <= cit["used_by"][0].items()
    ev = events(core, pid, "requirement_removed")
    assert len(ev) == 1 and ev[0]["result"]["requirement"]["label"] == "maximum operating temperature"
    # a later full run never re-plans the removed requirement
    run = core.run_comparison(pid)
    assert all(a["requirement_id"] != "F1" for a in run["actions"])
    assert {a["state"] for a in assessments(core, pid, "F1")} == {"retired"}


# ------------------------------------------------------------------ Undo and repeated clicks
def test_undo_restores_same_id_and_content_and_reopens_obligations(core):
    pid = make_project(core)
    core.run_comparison(pid)
    original = core.project_view(pid)["mission"]["requirements"]
    old = {a["assessment_id"] for a in assessments(core, pid, "F2")}
    core.archive_requirement(pid, "F2")
    res = core.restore_requirement(pid, "F2", {"expected_revision": 1})
    assert res["status"] == "restored" and res["lifecycle_revision"] == 2 and res["mission_revision"] == 2
    assert core.project_view(pid)["mission"]["requirements"] == original       # same ID, text and position
    assert res["reopened_obligations"] == ["A/F2", "B/F2"]
    assert obligations(core, pid)[("A", "F2")] == "open"                        # upsert, not a blind INSERT
    # retired assessments stay history until a fresh run checks current sources
    assert {a["state"] for a in assessments(core, pid, "F2")} == {"retired"}
    assert ("A", "F2") not in cell_keys(core, pid)
    run = core.run_comparison(pid)
    assert run["counters"].get("rejected_stale", 0) == 0
    now = assessments(core, pid, "F2")
    current = [a for a in now if a["state"] == "current"]
    assert len(current) == 2 and not ({a["assessment_id"] for a in current} & old)
    assert {a["assessment_id"] for a in now if a["state"] == "retired"} == old
    assert ("A", "F2") in cell_keys(core, pid) and obligations(core, pid)[("A", "F2")] == "done"


def test_repeated_remove_and_restore_are_idempotent(core):
    pid = make_project(core)
    assert core.archive_requirement(pid, "F3")["status"] == "removed"
    again = core.archive_requirement(pid, "F3", {"expected_revision": 0})   # a double click with the stale revision
    assert again["status"] == "already_removed" and again["lifecycle_revision"] == 1
    assert len(events(core, pid, "requirement_removed")) == 1
    with core.store.read() as con:
        assert core.mission_revision(con, pid) == 1
    assert core.restore_requirement(pid, "F3")["status"] == "restored"
    assert core.restore_requirement(pid, "F3")["status"] == "already_active"
    assert len(events(core, pid, "requirement_restored")) == 1
    with core.store.read() as con:
        assert core.mission_revision(con, pid) == 2 and core.requirement_revision(con, pid, "F3") == 2
    with pytest.raises(C.Conflict) as e:                                  # stale expected revision on a live record
        core.archive_requirement(pid, "F3", {"expected_revision": 0})
    assert e.value.code == "revision_conflict"
    with pytest.raises(C.NotFound):
        core.archive_requirement(pid, "NOPE")
    with pytest.raises(C.NotFound):
        core.restore_requirement(pid, "NOPE")
    with pytest.raises(C.ValidationFailed):
        core.archive_requirement(pid, "F3", {"expected_revision": "1"})
    assert active_ids(core, pid) == ["F1", "F2", "F3"]


# ------------------------------------------------------------------ no resurrection: source update, reindex, restart
def test_source_update_and_addition_do_not_resurrect_removed_obligations(core):
    pid = make_project(core)
    core.run_comparison(pid)
    core.archive_requirement(pid, "F1")          # F1/A cites spec-a@v1#a-temp
    rev = core.ingest_document(pid, "a.md", b64(DOC_A2), "A", "spec-a")
    assert rev["event_type"] == "source_revision" and rev["run_id"]
    res = rev["result"]
    assert all("F1" not in k for k in res["reacquired"] + res["revalidated_by_search"] + res["outside_changed_scope"])
    assert obligations(core, pid)[("A", "F1")] == obligations(core, pid)[("B", "F1")] == "retired"
    assert {a["state"] for a in assessments(core, pid, "F1")} == {"retired"}
    add = core.ingest_document(pid, "b2.md", b64("# Extra\n\n## x1\nmaximum operating temperature 40 C\n"), "B",
                               "spec-b2")
    assert add["event_type"] == "source_addition"
    assert obligations(core, pid)[("B", "F1")] == "retired"
    assert ("B", "F1") not in cell_keys(core, pid)
    # restoring after the update assesses against the CURRENT version, not the retired citation
    core.restore_requirement(pid, "F1")
    core.run_comparison(pid)
    cell = next(c for c in core.comparison(pid)["cells"] if c["candidate_id"] == "A" and c["requirement_id"] == "F1")
    assert cell["citation"]["version_id"] == "v2"


class _EmbedDouble:
    """Loopback stand-in for an Ollama embedding endpoint (hashed bag of words); test-only."""

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
                self._out({"models": [{"name": "fake-embed:latest", "digest": "sha256:t"}]})

            def do_POST(self):  # noqa: N802
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                vecs = []
                for t in body["input"]:
                    v = [0.01] + [0.0] * 31
                    for tok in re.findall(r"\w+", t.lower()):
                        h = hashlib.sha256(tok.encode()).digest()
                        v[1 + h[0] % 31] += 1.0
                    vecs.append(v)
                self._out({"embeddings": vecs, "prompt_eval_count": 1})

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.srv.shutdown()
        self.srv.server_close()


def test_reindex_and_retrieval_switch_do_not_resurrect_removed_obligations(core):
    pid = make_project(core)
    core.run_comparison(pid)
    core.archive_requirement(pid, "F2")
    d = _EmbedDouble()
    try:
        core.registry.save({"profile_id": "emb", "role": "embedding", "adapter": "ollama", "model_id": "fake-embed",
                            "endpoint": d.url})
        assert core.registry.check("emb")["status"] == "ready"
        core.build_index(pid, "emb")                                 # new index generation (reindex)
        out = core.set_retrieval_mode(pid, "hybrid")                  # every 'done' search is rechecked
        assert all("F2" not in k for k in out["result"]["reacquired"] + out["result"]["revalidated_by_search"])
        core.build_index(pid, "emb")                                 # rebuilding the same corpus again
        core.run_comparison(pid)
    finally:
        d.close()
    assert obligations(core, pid)[("A", "F2")] == obligations(core, pid)[("B", "F2")] == "retired"
    assert {a["state"] for a in assessments(core, pid, "F2")} == {"retired"}
    assert all(k[1] != "F2" for k in cell_keys(core, pid))


def test_removal_and_restore_survive_restart(tmp_path):
    core = C.EvidenceCore(tmp_path / "store")
    pid = make_project(core)
    core.run_comparison(pid)
    core.archive_requirement(pid, "F1")
    again = C.EvidenceCore(tmp_path / "store")                           # app restart: same data directory
    assert active_ids(again, pid) == ["F2", "F3"]
    lc = again.requirement_lifecycle(pid)
    assert [r["requirement_id"] for r in lc["removed"]] == ["F1"] and lc["mission_revision"] == 1
    assert ("A", "F1") not in cell_keys(again, pid)
    assert again.archive_requirement(pid, "F1")["status"] == "already_removed"
    assert again.restore_requirement(pid, "F1")["status"] == "restored"
    third = C.EvidenceCore(tmp_path / "store")
    assert active_ids(third, pid) == ["F1", "F2", "F3"]
    assert third.requirement_lifecycle(pid)["active"] == {"F1": 2, "F2": 0, "F3": 0}


# ------------------------------------------------------------------ in-flight stale commits
def _hook_search(core, monkeypatch, rid, action):
    """Run ``action`` once, while the first search for ``rid`` is in flight (after planning, before commit)."""
    real = core._search
    fired = []

    def search(con, project_id, candidate_id, query, ctx=None, match=None):
        hits = real(con, project_id, candidate_id, query, ctx, match=match)
        req = next((r for r in REQS if r["label"] == query), None)
        if req and req["requirement_id"] == rid and not fired:
            fired.append(candidate_id)
            action()
        return hits
    monkeypatch.setattr(core, "_search", search)
    return fired


def _commit_details(run, rid):
    return [a["detail"] for a in run["actions"] if a["action_type"] == "commit_assessment" and a["requirement_id"] == rid]


def test_in_flight_result_is_rejected_after_removal(core, monkeypatch):
    pid = make_project(core)
    fired = _hook_search(core, monkeypatch, "F1", lambda: core.archive_requirement(pid, "F1"))
    run = core.run_comparison(pid)
    assert fired == ["A"]
    commits = _commit_details(run, "F1")
    assert commits[0]["committed"] == "rejected_stale" and "not active" in commits[0]["reason"]
    skipped = [a for a in run["actions"] if a["action_type"] == "skip_stale_obligation"]
    assert [(a["candidate_id"], a["requirement_id"]) for a in skipped] == [("B", "F1")]   # planned after removal
    assert run["counters"]["rejected_stale"] == 1 and run["counters"]["skipped_stale"] == 1
    assert assessments(core, pid, "F1") == []
    assert obligations(core, pid)[("A", "F1")] == "retired"
    assert cell_keys(core, pid) == {("A", "F2"), ("A", "F3"), ("B", "F2"), ("B", "F3")}


def test_in_flight_result_is_rejected_after_remove_then_restore_of_identical_text(core, monkeypatch):
    pid = make_project(core)

    def remove_and_undo():
        core.archive_requirement(pid, "F1")
        core.restore_requirement(pid, "F1")
    _hook_search(core, monkeypatch, "F1", remove_and_undo)
    run = core.run_comparison(pid)
    commits = _commit_details(run, "F1")
    assert commits[0]["committed"] == "rejected_stale"
    assert "lifecycle revision moved from 0 to 2" in commits[0]["reason"]       # identical text, newer revision
    plans = [a["detail"] for a in run["actions"] if a["action_type"] == "plan_obligation" and a["requirement_id"] == "F1"]
    assert [p["requirement_lifecycle_revision"] for p in plans] == [0, 2]
    assert commits[1]["committed"] == "new_version"                             # B was planned after the restore
    assert [a["candidate_id"] for a in assessments(core, pid, "F1")] == ["B"]
    assert obligations(core, pid)[("A", "F1")] == "open"                        # still waiting for a fresh run
    core.run_comparison(pid)
    assert {a["candidate_id"] for a in assessments(core, pid, "F1") if a["state"] == "current"} == {"A", "B"}


def test_in_flight_result_is_rejected_after_edit(core, monkeypatch):
    pid = make_project(core)
    wf = Workflow(core)
    _hook_search(core, monkeypatch, "F1",
                 lambda: wf.save_requirement(pid, {"requirement_id": "F1", "label": "maximum operating temperature",
                                                   "query": "operating temperature rating"}))
    run = core.run_comparison(pid)
    commits = _commit_details(run, "F1")
    assert commits[0]["committed"] == "rejected_stale" and "content hash changed" in commits[0]["reason"]
    assert assessments(core, pid, "F1") == []
    assert obligations(core, pid)[("A", "F1")] == "open"


# ------------------------------------------------------------------ zero requirements, no ID reuse
def test_zero_active_requirements_is_a_valid_empty_state(core):
    pid = make_project(core)
    core.run_comparison(pid)
    for rid in ("F1", "F2", "F3"):
        core.archive_requirement(pid, rid)
    assert active_ids(core, pid) == [] and core.comparison(pid)["cells"] == []
    run = core.run_comparison(pid)
    assert run["status"] == "completed" and run["counters"]["obligations_planned"] == 0
    wf = Workflow(core)
    cmp_ = wf.compare(pid, {})
    assert cmp_["run"] is None and cmp_["requirements"] == []
    reqs = wf.requirements(pid)
    assert reqs["requirements"] == [] and [r["requirement_id"] for r in reqs["removed"]] == ["F1", "F2", "F3"]
    rev = core.ingest_document(pid, "a.md", b64(DOC_A2), "A", "spec-a")   # a source update with nothing active
    assert rev["status"] == "ingested" and rev["result"]["reacquired"] == []
    assert len([h for h in core.history(pid) if h["state"] == "retired"]) == 6


def test_removed_ids_are_never_reused(core):
    pid = make_project(core)
    wf = Workflow(core)
    u1 = wf.save_requirement(pid, {"label": "front access panel"})
    assert u1["requirement_id"] == "U1"
    core.archive_requirement(pid, "U1")
    with pytest.raises(C.Conflict) as e:
        wf.save_requirement(pid, {"requirement_id": "U1", "label": "something different"})
    assert e.value.code == "requirement_removed"
    with pytest.raises(C.Conflict):
        wf.save_requirement(pid, {"requirement_id": "U1", "label": "front access panel"})   # restore is the only way
    assert wf.save_requirement(pid, {"label": "another requirement"})["requirement_id"] == "U2"
    res = core.restore_requirement(pid, "U1")
    assert res["requirement"]["label"] == "front access panel"
    # an edit advances the lifecycle revision too
    with core.store.read() as con:
        before = core.requirement_revision(con, pid, "U1")
    wf.save_requirement(pid, {"requirement_id": "U1", "label": "front access panel", "query": "access panel"})
    with core.store.read() as con:
        assert core.requirement_revision(con, pid, "U1") == before + 1


# ------------------------------------------------------------------ HTTP routes, guards, read-only projects, UI
@pytest.fixture
def app(tmp_path):
    core = C.EvidenceCore(tmp_path / "store")
    srv = create_server(core, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        with loopback_only():
            yield core, url
    finally:
        srv.shutdown()
        srv.server_close()


def call(url, method, path, body=None, headers=None, raw=False):
    data = None if body is None else json.dumps(body).encode("utf-8")
    h = {"Content-Type": "application/json"} if data is not None else {}
    h.update(headers or {})
    req = urllib.request.Request(url + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req) as r:
            payload = r.read()
            return (r.status, payload) if raw else (r.status, json.loads(payload))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_http_archive_restore_routes_and_guards(app):
    core, url = app
    pid = make_project(core)
    st, lst = call(url, "GET", f"/api/projects/{pid}/requirements")
    assert st == 200 and [r["lifecycle_revision"] for r in lst["requirements"]] == [0, 0, 0] and lst["removed"] == []
    path = f"/api/projects/{pid}/requirements/F2/archive"
    st, e = call(url, "POST", path, {}, headers={"Origin": "http://evil.example"})
    assert st == 403 and e["error"] == "forbidden_origin"
    st, e = call(url, "POST", path, None, headers={"Content-Type": "text/plain"})
    assert st == 415
    assert obligations(core, pid)[("A", "F2")] == "open"                   # refused requests changed nothing
    st, out = call(url, "POST", path, {"expected_revision": 0})
    assert st == 200 and out["status"] == "removed"
    st, out = call(url, "POST", path, {"expected_revision": 0})
    assert st == 200 and out["status"] == "already_removed"
    st, lst = call(url, "GET", f"/api/projects/{pid}/requirements")
    assert [r["requirement_id"] for r in lst["requirements"]] == ["F1", "F3"]
    assert lst["removed"][0]["requirement_id"] == "F2" and lst["mission_revision"] == 1
    st, e = call(url, "POST", f"/api/projects/{pid}/requirements/F2/restore", {"expected_revision": 0})
    assert st == 409 and e["error"] == "revision_conflict"
    st, out = call(url, "POST", f"/api/projects/{pid}/requirements/F2/restore", {"expected_revision": 1})
    assert st == 200 and out["status"] == "restored"
    st, e = call(url, "POST", f"/api/projects/{pid}/requirements/NOPE/archive", {})
    assert st == 404 and e["error"] == "requirement_not_found"
    st, ch = call(url, "GET", f"/api/projects/{pid}/changes")
    kinds = [c["event_type"] for c in ch["changes"]]
    assert kinds.count("requirement_removed") == 1 and kinds.count("requirement_restored") == 1


def test_sample_and_synthetic_projects_stay_read_only(app):
    core, url = app
    st, _ = call(url, "POST", "/api/demo/bootstrap", {})
    assert st == 200
    before = core.project_view(C.SAMPLE_PROJECT_ID)["mission"]
    for action in ("archive", "restore"):
        st, e = call(url, "POST", f"/api/projects/{C.SAMPLE_PROJECT_ID}/requirements/R1/{action}", {})
        assert st == 409 and e["error"] == "project_is_fixed"
    assert core.project_view(C.SAMPLE_PROJECT_ID)["mission"] == before
    st, _ = call(url, "POST", "/api/synthetic/relation-search", {})
    assert st == 200
    st, e = call(url, "POST", f"/api/projects/{R.PROJECT_ID}/requirements/anything/archive", {})
    assert st == 409 and e["error"] == "project_is_fixed"


def test_ui_offers_remove_undo_and_show_removed(app):
    _core, url = app
    st, js = call(url, "GET", "/app.js", raw=True)
    assert st == 200
    for needle in (b"/archive", b"/restore", b"\"Remove\"", b"\"Undo\"", b"Show removed", b"expected_revision"):
        assert needle in js
