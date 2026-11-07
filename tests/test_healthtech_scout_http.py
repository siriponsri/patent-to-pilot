from __future__ import annotations

import json
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread

import pytest

from patent_to_pilot.healthtech.http import create_server
from patent_to_pilot.healthtech.scout_service import ReplayBundle

FIXTURES = Path(__file__).parent / "fixtures" / "scout"
BUNDLE = FIXTURES / "replay-bundle.json"
RAW = json.loads(BUNDLE.read_text(encoding="utf-8"))
BRIEF = {
    "brief_id": "syn-brief-001",
    "text": RAW["searches"][0]["brief_text"],
    "own_ipc3": ["F04", "F16"],
    "own_ipc3_basis": "typed",
    "data_class": "synthetic",
}


def _request(server, method, path, payload=None, headers=None):
    conn = HTTPConnection(*server.server_address[:2], timeout=10)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    conn.request(method, path, body=body, headers={"Content-Type": "application/json", **(headers or {})})
    response = conn.getresponse()
    value = json.loads(response.read().decode("utf-8"))
    conn.close()
    return response.status, value


def _serve(root, **kwargs):
    server = create_server("127.0.0.1", 0, root, code_commit="test-head", **kwargs)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


@pytest.fixture()
def server(tmp_path):
    server, thread = _serve(tmp_path / "data", scout_replay=BUNDLE)
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.healthtech_service.close()


def test_replay_session_lanes_rationale_decision_and_receipt(server):
    status, info = _request(server, "GET", "/scout/replay")
    assert status == 200 and info["mode"] == "replay" and info["paid_dispatch"] == "closed"
    assert info["corpus_bundle_sha256"] == RAW["corpus_bundle_sha256"]

    body = {"brief": BRIEF, "split": {"n_own": 2, "n_other": 2}}
    status, created = _request(server, "POST", "/scout-sessions", body, {"Idempotency-Key": "s-1"})
    assert status == 201 and created["duplicate"] is False
    session = created["session"]
    lanes = [(c["lane"], c["rank_in_lane"], c["family_id"]) for c in session["candidates"]]
    assert lanes == [("own_field", 1, "SYN-F001"), ("own_field", 2, "SYN-F002"),
                     ("other_fields", 1, "SYN-F003"), ("other_fields", 2, "SYN-F005")]
    assert all(c["judgment"] == "not_judged" for c in session["candidates"])
    assert session["candidates"][0]["representative_canonical"] == "US9000001B1"
    assert session["receipt"]["mode"] == "replay" and session["receipt"]["paid_calls"] == 0
    session_id = session["session_id"]

    status, again = _request(server, "POST", "/scout-sessions", body, {"Idempotency-Key": "s-1"})
    assert status == 200 and again["duplicate"] is True and again["session"]["session_id"] == session_id
    status, conflict = _request(server, "POST", "/scout-sessions", {**body, "split": {"n_own": 1, "n_other": 1}},
                                {"Idempotency-Key": "s-1"})
    assert status == 409 and conflict["error"]["code"] == "idempotency_conflict"

    status, fetched = _request(server, "GET", f"/scout-sessions/{session_id}")
    assert status == 200 and fetched["session"] == session

    status, family = _request(server, "GET", f"/scout-sessions/{session_id}/families/SYN-F003")
    assert status == 200 and family["source_text"].startswith("SYNTHETIC.")

    status, good = _request(server, "POST", f"/scout-sessions/{session_id}/rationales/SYN-F003")
    assert status == 200
    rationale = good["rationale"]
    assert rationale["quote_status"] == "all_matched" and rationale["basis"] == "system_inference"
    assert rationale["label"] == "literal match is not semantic support"
    first = rationale["quotes"][0]
    assert family["source_text"][first["start"]:first["end"]] == first["quote"]

    status, flagged = _request(server, "POST", f"/scout-sessions/{session_id}/rationales/SYN-F005")
    assert status == 200 and flagged["rationale"]["quote_status"] == "some_unmatched"
    assert [q["status"] for q in flagged["rationale"]["quotes"]] == ["matched", "not_found"]

    status, missing = _request(server, "POST", f"/scout-sessions/{session_id}/rationales/SYN-F001")
    assert status == 409 and missing["error"]["code"] == "not_recorded"
    status, outside = _request(server, "POST", f"/scout-sessions/{session_id}/rationales/SYN-F006")
    assert status == 404 and outside["error"]["code"] == "family_not_in_session"

    status, decided = _request(server, "POST", f"/scout-sessions/{session_id}/rationales/SYN-F005/decision",
                               {"decision": "rejected", "note": "second quote is not in the source"})
    assert status == 200 and decided["rationale"]["decision"] == "rejected"
    status, bad = _request(server, "POST", f"/scout-sessions/{session_id}/rationales/SYN-F003/decision",
                           {"decision": "maybe"})
    assert status == 400

    status, receipt = _request(server, "GET", f"/scout-sessions/{session_id}/receipt")
    assert status == 200 and receipt["paid_calls"] == 0
    assert receipt["rationales"] == {"count": 2, "llm_calls": 2, "prompt_tokens": 821, "output_tokens": 184,
                                     "latency_seconds": 10.0}


def test_replay_fails_closed(server, tmp_path):
    status, err = _request(server, "POST", "/scout-sessions", {"brief": BRIEF})
    assert status == 400 and err["error"]["code"] == "invalid_idempotency_key"
    unseen = {**BRIEF, "text": "SYNTHETIC. A different problem that was never recorded."}
    status, err = _request(server, "POST", "/scout-sessions", {"brief": unseen}, {"Idempotency-Key": "s-2"})
    assert status == 409 and err["error"]["code"] == "not_recorded"
    status, err = _request(server, "POST", "/scout-sessions", {"brief": {**BRIEF, "data_class": "public"}},
                           {"Idempotency-Key": "s-3"})
    assert status == 422 and err["error"]["code"] == "data_class_mismatch"
    status, err = _request(server, "POST", "/scout-sessions", {"brief": {**BRIEF, "own_ipc3": ["F16"]}},
                           {"Idempotency-Key": "s-4"})
    assert status == 409 and err["error"]["code"] == "not_recorded"
    status, err = _request(server, "GET", "/scout-sessions/not-a-session")
    assert status == 400
    status, err = _request(server, "GET", "/scout-sessions/" + "0" * 32)
    assert status == 404

    plain, thread = _serve(tmp_path / "plain")
    try:
        status, err = _request(plain, "GET", "/scout/replay")
        assert status == 409 and err["error"]["code"] == "scout_unavailable"
    finally:
        plain.shutdown()
        thread.join(timeout=5)
        plain.healthtech_service.close()


class _FakeEncoder:
    def encode(self, text):
        import numpy as np

        return np.array([1.0, 0.0, 0.0], dtype=np.float32)


def test_live_mode_partitions_live_scores_and_replays_book(tmp_path):
    import numpy as np

    from patent_to_pilot.healthtech.scout_live import LiveIndex, source_text
    from patent_to_pilot.healthtech.scout_service import RationaleBook, ScoutService

    rows = [
        {"id": "US20180000001A1", "title": "SYNTHETIC seal", "abstract": "A lip seal.", "claims": "1. A seal.",
         "ipc3": ["F16"], "date_published": "20180104"},
        {"id": "US20180000002A1", "title": "SYNTHETIC stent", "abstract": "Struts recover their shape after "
         "each deformation without any external power.", "claims": "", "ipc3": ["A61"], "date_published": "20180111"},
        {"id": "US20180000003A1", "title": "SYNTHETIC gasket", "abstract": "A gasket.", "claims": "", "ipc3": [],
         "date_published": None},
    ]
    vectors = np.array([[0.5, 0.5, 0], [0.9, 0.1, 0], [0.1, 0.9, 0]], dtype=np.float16)
    index = LiveIndex(rows, vectors, _FakeEncoder(), corpus_sha256="c" * 64, vectors_sha256="v" * 64)
    ranking, _, _ = index.search("anything")
    assert [f for f, _ in ranking] == ["US20180000002A1", "US20180000001A1", "US20180000003A1"]
    assert index.family("US20180000001A1")["publication_date"] == "2018-01-04"
    assert source_text(rows[1]).startswith("SYNTHETIC stent\n\n")

    brief = {**BRIEF, "data_class": "public", "own_ipc3": ["F16"]}
    book = RationaleBook({"format": "ptp-scout-rationales-v1", "corpus_sha256": "c" * 64, "rationales": [
        {"brief_text": brief["text"], "own_ipc3": ["F16"], "family_id": "US20180000002A1", "model": "Qwen/Qwen3-8B",
         "model_revision": "fixture", "prompt_version": "ptp-scout-rationale-v0", "what_it_does": "Holds force.",
         "transferable_mechanism": "Shape recovery.",
         "quotes": ["recover their shape after each deformation without any external power"]}]}, "c" * 64)
    with pytest.raises(ValueError, match="different corpus"):
        RationaleBook({"format": "ptp-scout-rationales-v1", "corpus_sha256": "d" * 64, "rationales": []}, "c" * 64)

    service = ScoutService(tmp_path, live=index, rationale_book=book)
    info = service.describe()
    assert info["mode"] == "live" and info["recorded_rationales"] == 1 and info["demo_briefs"][0]["own_ipc3"] == ["F16"]
    session, duplicate = service.create({"brief": brief, "split": {"n_own": 1, "n_other": 2}}, "live-1")
    assert duplicate is False and session["receipt"]["mode"] == "live"
    assert [(c["lane"], c["family_id"]) for c in session["candidates"]] == [
        ("own_field", "US20180000001A1"), ("other_fields", "US20180000002A1"), ("other_fields", "US20180000003A1")]
    assert session["candidates"][1]["title"] == "SYNTHETIC stent"
    assert session["rationales_available"] == ["US20180000002A1"]
    result = service.rationale(session["session_id"], "US20180000002A1")
    assert result["rationale"]["quote_status"] == "all_matched"
    with pytest.raises(Exception, match="no recorded rationale"):
        service.rationale(session["session_id"], "US20180000001A1")
    with pytest.raises(Exception, match="public data only"):
        service.create({"brief": BRIEF}, "live-2")


def test_replay_bundle_integrity_checks():
    with pytest.raises(ValueError, match="corpus hash"):
        ReplayBundle({**RAW, "corpus_bundle_sha256": "0" * 64}, "x")
    with pytest.raises(ValueError, match="synthetic or public"):
        ReplayBundle({**RAW, "data_class": "private"}, "x")
    bad_search = {**RAW["searches"][0], "ranking": [{"family_id": "NOPE", "score": 1.0}]}
    with pytest.raises(ValueError, match="unknown families"):
        ReplayBundle({**RAW, "searches": [bad_search]}, "x")


# Shared with frontend/healthtech-web/tests/unit/scout.test.mjs: the client key must equal
# "scout-" + the first 24 hex digits of the request hash the server compares.
KEY_VECTOR_BRIEF = {"brief_id": "ui-brief", "text": "แผ่นเซนเซอร์ \"patch\" ลอกออก\tง่าย", "own_ipc3": ["A61", "C09"],
                    "own_ipc3_basis": "typed", "data_class": "public", "language": "th"}
KEY_VECTOR_SPLIT = {"n_own": 5, "n_other": 15}
KEY_VECTOR_SHA256 = "0daf7e22e34c3c809a3f293ee369f8412b252f898c6c9c6bd1bfe5af08d2bd2a"


def test_idempotency_hash_matches_client_key_vector():
    from patent_to_pilot.healthtech.scout import LaneSplit, ScoutBrief
    from patent_to_pilot.healthtech.scout_service import _hash

    brief = ScoutBrief.model_validate(KEY_VECTOR_BRIEF).model_dump(mode="json")
    split = LaneSplit.model_validate(KEY_VECTOR_SPLIT).model_dump(mode="json")
    assert _hash({"brief": brief, "split": split}) == KEY_VECTOR_SHA256
    # Every brief field counts: a key reused for the same text with another UI language is a conflict.
    assert _hash({"brief": {**brief, "language": "en"}, "split": split}) != KEY_VECTOR_SHA256


def test_same_key_with_other_language_conflicts_and_client_style_keys_do_not(server):
    body = {"brief": {**BRIEF, "language": "th"}, "split": {"n_own": 2, "n_other": 2}}
    status, first = _request(server, "POST", "/scout-sessions", body, {"Idempotency-Key": "old-style"})
    assert status == 201
    english = {**body, "brief": {**BRIEF, "language": "en"}}
    status, err = _request(server, "POST", "/scout-sessions", english, {"Idempotency-Key": "old-style"})
    assert status == 409 and err["error"]["code"] == "idempotency_conflict"
    # Keys derived from the full request hash (the client rule) never collide across languages.
    key_th = "scout-" + first["session"]["receipt"]["input_sha256"][:24]
    status, again = _request(server, "POST", "/scout-sessions", body, {"Idempotency-Key": key_th})
    assert status == 201 and again["session"]["receipt"]["input_sha256"] == first["session"]["receipt"]["input_sha256"]
    status, replay = _request(server, "POST", "/scout-sessions", body, {"Idempotency-Key": key_th})
    assert status == 200 and replay["duplicate"] is True
    assert replay["session"]["session_id"] == again["session"]["session_id"]
    status, created = _request(server, "POST", "/scout-sessions", english, {"Idempotency-Key": "scout-en-key"})
    assert status == 201 and created["session"]["receipt"]["input_sha256"][:24] != key_th[6:]
