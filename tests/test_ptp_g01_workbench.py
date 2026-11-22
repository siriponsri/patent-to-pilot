"""PTP-2026-11-21/G01 integration checks. The expected outcomes are loaded ONLY here, from
tests/fixtures/ptp_g01/expected_assertions.json; the runtime package never reads them."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench.guard import RemoteCallBlocked, loopback_only
from patent_to_pilot.workbench.server import create_server

REPO = Path(__file__).resolve().parents[1]
ORACLE = json.loads((REPO / "tests/fixtures/ptp_g01/expected_assertions.json").read_text(encoding="utf-8"))
PID = C.SAMPLE_PROJECT_ID


def outcomes(core):
    return {(c["candidate_id"], c["requirement_id"]): c for c in core.comparison(PID)["cells"]}


def check_against(core, block):
    got = outcomes(core)
    for a in block["assessments"]:
        cell = got[(a["candidate_id"], a["requirement_id"])]
        assert cell["outcome"] == a["criterion_outcome"], a
        if "citation" in a:
            assert {k: cell["citation"][k] for k in ("source_id", "version_id", "passage_id")} == a["citation"]
        else:
            assert cell["citation"] is None
    assert core.project_view(PID)["current_versions"] == block["current_versions"]


def sample_copy(tmp_path, edit=None, mission_edit=None, update_hash=True) -> Path:
    """Temporary copy of the runtime sample; edits rewrite a source and its manifest hash."""
    dst = tmp_path / "sample"
    shutil.copytree(C.SAMPLE_DIR, dst)
    man = json.loads((dst / "source_manifest.json").read_text(encoding="utf-8"))
    for rel, (old, new) in (edit or {}).items():
        p = dst / rel
        assert old.encode("utf-8") in p.read_bytes()
        raw = p.read_bytes().replace(old.encode("utf-8"), new.encode("utf-8"))
        p.write_bytes(raw)
        for e in man["initial_sources"] + man["incoming_changes"]:
            if e["path"] == rel and update_hash:
                e["sha256"] = hashlib.sha256(raw).hexdigest()
    (dst / "source_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    if mission_edit:
        m = json.loads((dst / "requirements.json").read_text(encoding="utf-8"))
        mission_edit(m)
        (dst / "requirements.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst


@pytest.fixture
def core(tmp_path):
    return C.EvidenceCore(tmp_path / "store")


def test_runtime_never_references_test_oracle():
    pkg = REPO / "src/patent_to_pilot/workbench"
    for f in list(pkg.rglob("*.py")) + list((pkg / "static").glob("*")) + [REPO / "scripts/ptp_run.py"]:
        text = f.read_text(encoding="utf-8")
        assert "expected_assertions" not in text and "test_only" not in text, f
    assert not (pkg / "sample" / "test_only").exists()


def test_initial_import_excludes_revision(core):
    core.bootstrap_sample()
    idx = core.project_view(PID)["searchable_index"]
    assert idx["source_versions"] == ["DEMO-S1@v1", "DEMO-S2@v1", "DEMO-S3@v1", "DEMO-S4@v1"]
    with core.store.read() as con:
        assert not con.execute("SELECT 1 FROM source_versions WHERE version_id='v2'").fetchone()
    assert core.bootstrap_sample()["reopened"] is True          # reopening never resets


def test_initial_comparison_matches_oracle_and_citations_are_literal(core):
    core.bootstrap_sample()
    with loopback_only():
        run = core.run_comparison(PID, invoked_via="cli")
    assert run["status"] == "completed" and run["counters"]["paid_model_calls"] == 0
    check_against(core, ORACLE["initial"])
    for cell in outcomes(core).values():
        if cell["outcome"] == "unknown":
            continue
        c = cell["citation"]
        r = core.resolve_citation(PID, c["source_id"], c["version_id"], c["passage_id"])
        text = core.source_version(PID, c["source_id"], c["version_id"])["text"]
        assert text[r["start_char"]:r["end_char"]] == r["quote"]
        assert r["text_before"] + r["quote"] + r["text_after"] == text
    thai = core.resolve_citation(PID, "DEMO-S3", "v1", "S3-P1")["quote"]
    raw = (C.SAMPLE_DIR / "sources/DEMO-S3-v1.md").read_bytes().decode("utf-8")
    assert "ชื่อโมดูลตัวอย่าง: แคปซูลกักเก็บความร้อน" in thai and thai in raw
    assert "40 to 70 °C" in core.resolve_citation(PID, "DEMO-S2", "v1", "S2-P1")["quote"]
    kinds = [a["action_type"] for a in run["actions"]]
    assert kinds.count("search_current_sources") == 6 and "commit_assessment" in kinds


@pytest.mark.parametrize("upper,expected", [(69, "does_not_meet"), (70, "meets"), (71, "meets")])
def test_range_follows_the_parsed_numbers(tmp_path, upper, expected):
    sample = sample_copy(tmp_path, {"sources/DEMO-S2-v1.md": ("40 to 70 °C", f"40 to {upper} °C")})
    core = C.EvidenceCore(tmp_path / "store", sample)
    core.bootstrap_sample()
    core.run_comparison(PID)
    cell = outcomes(core)[("CONCEPT-A", "R2")]
    assert cell["outcome"] == expected and f"40–{upper} °C" in cell["explanation"]


@pytest.mark.parametrize("bad,issue", [("70 to 40 °C", "exceeds"), ("40 to 70 degrees", "unit")])
def test_malformed_range_is_a_validation_issue_not_a_guess(tmp_path, bad, issue):
    sample = sample_copy(tmp_path, {"sources/DEMO-S2-v1.md": ("40 to 70 °C", bad)})
    core = C.EvidenceCore(tmp_path / "store", sample)
    core.bootstrap_sample()
    core.run_comparison(PID)
    cell = outcomes(core)[("CONCEPT-A", "R2")]
    assert cell["outcome"] == "unknown" and cell["citation"] is None
    assert issue in json.dumps(cell["validation_issues"])


def test_source_revision_flow_matches_oracle(core):
    core.bootstrap_sample()
    core.run_comparison(PID)
    before = outcomes(core)
    with loopback_only():
        res = core.apply_change(PID, "CHANGE-S2-V2", invoked_via="cli")["result"]
    check_against(core, ORACLE["after_CHANGE_S2_V2"])
    after = outcomes(core)
    exp = ORACLE["after_CHANGE_S2_V2"]
    assert [a["key"] for a in res["affected"]] == exp["affected_requirement_keys"]
    assert res["unchanged"] == sorted(exp["unchanged_requirement_keys"])
    for k in exp["unchanged_requirement_keys"]:                 # unchanged = same committed assessment identity
        key = tuple(k.split("/"))
        assert after[key]["assessment_id"] == before[key]["assessment_id"]
    a2 = after[("CONCEPT-A", "R2")]
    assert a2["supersedes_id"] == before[("CONCEPT-A", "R2")]["assessment_id"]
    assert "40–60 °C" in a2["explanation"]
    with core.store.read() as con:                              # needs_review was persisted before replacement
        ev = [r[0] for r in con.execute("SELECT state FROM assessment_events WHERE assessment_id=? ORDER BY rowid",
                                        (a2["supersedes_id"],))]
        assert ev == ["committed", "needs_review", "superseded"]
        hits = core._search(con, PID, "CONCEPT-A", "Supported temperature range")
    assert [(h["source_id"], h["version_id"]) for h in hits] == [("DEMO-S2", "v2")]   # current search uses v2
    old = core.resolve_citation(PID, "DEMO-S2", "v1", "S2-P1")                         # history still resolves
    assert old["status"] == "historical" and "40 to 70 °C" in old["quote"]
    run = core.run_view(res["run_id"])
    types = [a["action_type"] for a in run["actions"]]
    assert run["strategy"] == "selective_by_dependency" and types.count("reuse_valid_result") == 2
    assert types.count("search_current_sources") == 3            # 2 verification searches + 1 re-acquisition
    assert run["counters"]["acquisition_actions"] == 3


def test_duplicate_and_conflicting_change(tmp_path):
    core = C.EvidenceCore(tmp_path / "store")
    core.bootstrap_sample()
    with pytest.raises(C.Conflict):
        core.apply_change(PID, "CHANGE-S2-V2")                  # needs a completed run first
    core.run_comparison(PID)
    first = core.apply_change(PID, "CHANGE-S2-V2")
    again = core.apply_change(PID, "CHANGE-S2-V2")
    assert again["already_applied"] and again["run_id"] == first["run_id"]
    with core.store.read() as con:
        assert con.execute("SELECT COUNT(*) FROM source_versions WHERE source_id='DEMO-S2'").fetchone()[0] == 2
    with pytest.raises(C.NotFound):
        core.apply_change(PID, "CHANGE-NOPE")
    # incoming bytes that do not match the pinned manifest hash are rejected; nothing is imported
    tampered = sample_copy(tmp_path, {"incoming/DEMO-S2-v2.md": ("40 to 60 °C", "40 to 65 °C")}, update_hash=False)
    core3 = C.EvidenceCore(tmp_path / "store3", tampered)
    core3.bootstrap_sample()
    core3.run_comparison(PID)
    with pytest.raises(C.ValidationFailed) as e:
        core3.apply_change(PID, "CHANGE-S2-V2")
    assert e.value.code == "hash_mismatch"
    assert core3.project_view(PID)["current_versions"]["DEMO-S2"] == "v1"


def test_missing_citation_errors_are_specific(core):
    core.bootstrap_sample()
    for args, code in [(("DEMO-S9", "v1", "S9-P1"), "source_not_found"), (("DEMO-S2", "v9", "S2-P1"), "version_not_found"),
                       (("DEMO-S2", "v1", "S2-P9"), "passage_not_found")]:
        with pytest.raises(C.NotFound) as e:
            core.resolve_citation(PID, *args)
        assert e.value.code == code


def test_budget_limit_stops_honestly(tmp_path):
    sample = sample_copy(tmp_path, mission_edit=lambda m: m["limits"].update(max_acquisition_actions=2))
    core = C.EvidenceCore(tmp_path / "store", sample)
    core.bootstrap_sample()
    run = core.run_comparison(PID)
    assert run["status"] == "stopped" and run["stop_reason"] == "budget_exhausted:max_acquisition_actions"
    assert len(core.comparison(PID)["cells"]) == 2


def test_restart_from_a_new_process(tmp_path):
    store = tmp_path / "store"
    core = C.EvidenceCore(store)
    core.bootstrap_sample()
    run = core.run_comparison(PID)
    core.apply_change(PID, "CHANGE-S2-V2")
    code = ("import json,sys; from patent_to_pilot.workbench.core import EvidenceCore, SAMPLE_PROJECT_ID as P;"
            "c=EvidenceCore(sys.argv[1]); v=c.project_view(P);"
            "print(json.dumps({'runs':[r['run_id'] for r in v['runs']],'cur':v['current_versions'],"
            "'n':len(c.history(P)),'chg':v['changes'][0]['status'],"
            "'thai':c.resolve_citation(P,'DEMO-S3','v1','S3-P1')['quote']},ensure_ascii=False))")
    out = subprocess.run([sys.executable, "-c", code, str(store)], capture_output=True, cwd=REPO,
                         env={**__import__("os").environ, "PYTHONPATH": str(REPO / "src"), "PYTHONIOENCODING": "utf-8"})
    assert out.returncode == 0, out.stderr.decode("utf-8", "replace")
    got = json.loads(out.stdout.decode("utf-8"))
    assert got["runs"][0] == run["run_id"] and len(got["runs"]) == 2 and got["chg"] == "applied"
    assert got["cur"]["DEMO-S2"] == "v2" and got["n"] == 7 and "แคปซูล" in got["thai"]


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_http_and_cli_reach_the_same_core(tmp_path):
    core = C.EvidenceCore(tmp_path / "store")
    srv = create_server(core, "127.0.0.1", 0)
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with loopback_only():
            def post(path, body):
                req = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST",
                                             headers={"Content-Type": "application/json"})
                return json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
            post("/api/demo/bootstrap", {})
            http_run = post(f"/api/projects/{PID}/runs", {})
            cli_run = core.run_comparison(PID, invoked_via="cli")
            assert http_run["invoked_via"] == "http" and cli_run["invoked_via"] == "cli"
            assert http_run["core_identity"] == cli_run["core_identity"] == C.CORE_IDENTITY
            assert http_run["config_sha256"] == cli_run["config_sha256"]
            status, body = _get(base + f"/api/projects/{PID}/sources/DEMO-S3/versions/v1/passages/S3-P1")
            assert status == 200 and "แคปซูลกักเก็บความร้อน" in json.loads(body.decode("utf-8"))["quote"]
            status, body = _get(base + f"/api/projects/{PID}/sources/DEMO-S2/versions/v7/passages/S2-P1")
            assert status == 404 and json.loads(body)["error"] == "version_not_found"
            for path in ("/sample/source_manifest.json", "/tests/fixtures/ptp_g01/expected_assertions.json",
                         "/../tests/fixtures/ptp_g01/expected_assertions.json", "/static/../core.py"):
                assert _get(base + path)[0] == 404, path
            assert _get(base + "/")[0] == 200
            req = urllib.request.Request(base + f"/api/projects/{PID}/runs", data=b"{}", method="POST",
                                         headers={"Content-Type": "application/json", "Origin": "http://evil.example"})
            with pytest.raises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(req, timeout=10)
            assert e.value.code == 403
    finally:
        srv.shutdown()
        srv.server_close()


def test_guard_blocks_remote_connections_and_capabilities_are_lexical_only(core):
    attempts = []
    with loopback_only(attempts):
        with pytest.raises(RemoteCallBlocked):
            socket.create_connection(("203.0.113.5", 443), timeout=1)
    assert attempts
    caps = core.capabilities()
    # G02: model roles exist but nothing is configured by default; paid routes stay blocked without an envelope
    assert caps["lexical"]["state"] == "active" and caps["local_model"]["state"] == "not_configured"
    assert caps["api_model"]["state"] == "blocked_without_envelope"
    assert caps["remote_calls_allowed"] == "per_profile_allow_remote"
    assert not caps["model_downloads_allowed"]


def test_busy_port_is_never_shared(tmp_path):
    """Regression (found in Windows QA): a second server must not bind a port already in use."""
    core = C.EvidenceCore(tmp_path / "store")
    first = create_server(core, "127.0.0.1", 0)
    port = first.server_address[1]
    try:
        with pytest.raises(OSError):
            create_server(core, "127.0.0.1", port)
        sys.path.insert(0, str(REPO / "scripts"))
        import ptp_run
        second = ptp_run.bind_server(core, "127.0.0.1", port)
        assert second.server_address[1] != port
        second.server_close()
    finally:
        first.server_close()
