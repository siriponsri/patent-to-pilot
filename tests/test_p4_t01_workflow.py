"""P4-T01: Search, Compare and Inspect on the existing Workbench store (API level, no network, no model).

Every check goes through the loopback HTTP app, i.e. the same routes the bundled UI calls."""
from __future__ import annotations

import base64
import json
import threading
import urllib.error
import urllib.request

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench import relation_search as R
from patent_to_pilot.workbench.guard import loopback_only
from patent_to_pilot.workbench.server import create_server

PID = C.SAMPLE_PROJECT_ID

LETTER = """# Procurement letter (test fixture)

## clause-4
Clause 4. Enclosure units must keep a maximum operating temperature below 50 C.

## clause-5
Clause 5. Enclosure units installed at seaside sites are governed by Annex B.

## annex-b
Annex B. Coastal exception
Coastal enclosures fitted with a salt-mist filter may run up to 60 C.

## thai-1
หน่วยระบายความร้อนต้องเปลี่ยนแยกได้ทันที
"""


@pytest.fixture
def app(tmp_path):
    core = C.EvidenceCore(tmp_path / "store")
    srv = create_server(core, port=0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        with loopback_only():   # any non-loopback connection attempt fails the test
            yield core, url
    finally:
        srv.shutdown()
        srv.server_close()


def call(url, method, path, body=None, raw=False):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data is not None else {})
    try:
        with urllib.request.urlopen(req) as r:
            payload = r.read()
            return (r.status, payload, dict(r.headers)) if raw else (r.status, json.loads(payload))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def owner_project(url, core):
    st, p = call(url, "POST", "/api/projects", {"title": "P4 workflow test",
                                                "candidates": [{"candidate_id": "C1", "label": "Letter set"}]})
    assert st == 200
    pid = p["project_id"]
    st, ing = call(url, "POST", f"/api/projects/{pid}/documents",
                   {"filename": "letter.md", "candidate_id": "C1",
                    "content_base64": base64.b64encode(LETTER.encode("utf-8")).decode("ascii")})
    assert st == 200 and ing["status"] == "ingested"
    return pid


def text_of(core, pid, sid, vid):
    return core.source_version(pid, sid, vid)["text"]


# =========================================================================== Search
def test_search_returns_fts5_results_whose_offsets_resolve(app):
    core, url = app
    call(url, "POST", "/api/demo/bootstrap", {})
    st, r = call(url, "POST", f"/api/projects/{PID}/search", {"query": "supported temperature range"})
    assert st == 200 and r["mode"] == "terms" and r["route"].startswith("sqlite_fts5_bm25")
    assert r["fts_match"] == '"supported" OR "temperature" OR "range"'
    assert r["result_count"] >= 2 and r["paid_model_calls"] == 0 and r["remote_calls"] == 0
    assert r["index"]["source_versions"] == ["DEMO-S1@v1", "DEMO-S2@v1", "DEMO-S3@v1", "DEMO-S4@v1"]
    scores = [h["score_bm25"] for h in r["results"]]
    assert scores == sorted(scores)                                    # BM25 ascending = best first
    for h in r["results"]:
        text = text_of(core, PID, h["source_id"], h["version_id"])
        assert text[h["start_char"]:h["end_char"]] == h["quote"]
        assert text[h["snippet_start_char"]:h["snippet_end_char"]] == h["snippet"]
        assert h["matches"]
        for m in h["matches"]:
            assert text[m["start_char"]:m["end_char"]].lower() in {"supported", "temperature", "range"}
    # exact phrase mode is the G01 expression; a phrase that does not occur returns nothing (and says so)
    st, ph = call(url, "POST", f"/api/projects/{PID}/search", {"query": "range temperature", "mode": "phrase"})
    assert ph["fts_match"] == '"range temperature"' and ph["results"] == [] and ph["notes"]


def test_search_candidate_filter_literal_thai_and_validation(app):
    core, url = app
    call(url, "POST", "/api/demo/bootstrap", {})
    st, r = call(url, "POST", f"/api/projects/{PID}/search",
                 {"query": "Powered circulation", "candidate_id": "CONCEPT-B"})
    assert st == 200 and r["results"] and {h["candidate_id"] for h in r["results"]} == {"CONCEPT-B"}
    # literal mode finds Thai inside a longer unsegmented run; offsets resolve to the exact characters
    st, lit = call(url, "POST", f"/api/projects/{PID}/search", {"query": "กักเก็บ", "mode": "literal"})
    assert st == 200 and lit["fts_match"] is None and lit["route"].startswith("literal_substring_scan")
    assert lit["results"]
    for h in lit["results"]:
        text = text_of(core, PID, h["source_id"], h["version_id"])
        assert [text[m["start_char"]:m["end_char"]] for m in h["matches"]] and \
            all(text[m["start_char"]:m["end_char"]] == "กักเก็บ" for m in h["matches"])
    st, th = call(url, "POST", f"/api/projects/{PID}/search", {"query": "กักเก็บ"})
    assert any("Thai" in n for n in th["notes"])                        # the tokenizer limitation is stated
    for bad, code in (({"query": ""}, "bad_query"), ({"query": "x", "mode": "regex"}, "bad_mode"),
                      ({"query": "x", "limit": 0}, "bad_limit"), ({"query": "x", "candidate_id": "NOPE"},
                                                                     "unknown_candidate")):
        st, e = call(url, "POST", f"/api/projects/{PID}/search", bad)
        assert st == 422 and e["error"] == code
    st, e = call(url, "POST", "/api/projects/no-such/search", {"query": "x"})
    assert st == 404


# =========================================================================== Requirements
def test_arbitrary_requirement_create_update_and_validation(app):
    core, url = app
    pid = owner_project(url, core)
    st, r = call(url, "POST", f"/api/projects/{pid}/requirements",
                 {"label": "Maximum operating temperature at seaside sites"})
    assert st == 200 and r["status"] == "added" and r["requirement"]["requirement_id"] == "U1"
    assert r["requirement"] == {"requirement_id": "U1", "label": "Maximum operating temperature at seaside sites",
                                "query": "Maximum operating temperature at seaside sites", "kind": "text",
                                "match": "terms"}
    assert r["reopened_obligations"] == ["C1/U1"]
    st, again = call(url, "POST", f"/api/projects/{pid}/requirements",
                     {"requirement_id": "U1", "label": "Maximum operating temperature at seaside sites"})
    assert again["status"] == "unchanged"
    st, thai = call(url, "POST", f"/api/projects/{pid}/requirements",
                    {"requirement_id": "TH-1", "label": "เปลี่ยนแยกได้", "query": "หน่วยระบายความร้อนต้องเปลี่ยนแยกได้ทันที"})
    assert thai["requirement"]["label"] == "เปลี่ยนแยกได้"                # Thai preserved as typed
    st, up = call(url, "POST", f"/api/projects/{pid}/requirements",
                  {"requirement_id": "U1", "label": "Seaside temperature limit", "query": "seaside temperature",
                   "match": "phrase"})
    assert st == 200 and up["status"] == "edited" and up["fts_match"] == '"seaside temperature"'
    st, lst = call(url, "GET", f"/api/projects/{pid}/requirements")
    ids = [x["requirement_id"] for x in lst["requirements"]]
    assert lst["editable"] and ids == ["R1", "R2", "R3", "U1", "TH-1"]   # template requirements untouched
    u1 = next(x for x in lst["requirements"] if x["requirement_id"] == "U1")
    assert u1["label"] == "Seaside temperature limit" and u1["match"] == "phrase"
    st, ch = call(url, "GET", f"/api/projects/{pid}/changes")
    assert [c["event_type"] for c in ch["changes"]].count("requirement_change") == 3
    bad = [({"label": ""}, "bad_requirement_label"), ({"label": "x" * 201}, "bad_requirement_label"),
           ({"label": "ok", "query": "!!!"}, "bad_requirement_query"),
           ({"label": "ok", "requirement_id": "bad id"}, "bad_requirement_id"),
           ({"label": "ok", "match": "fuzzy"}, "bad_requirement_match"),
           ({"label": "ok", "field": "colour", "predicate": {"operator": "equals", "value": True}},
            "bad_requirement_field"),
           ({"label": "ok", "field": "powered_circulation", "predicate": {"operator": "equals", "value": "no"}},
            "bad_requirement_predicate"),
           ({"label": "ok", "field": "supported_temperature_range",
             "predicate": {"operator": "contains_interval", "minimum": 70, "maximum": 40, "unit": "degC"}},
            "bad_requirement_predicate")]
    for body, code in bad:
        st, e = call(url, "POST", f"/api/projects/{pid}/requirements", body)
        assert st == 422 and e["error"] == code, (body, e)
    # a bounded-field requirement typed by the user still uses the G01 parser
    st, bf = call(url, "POST", f"/api/projects/{pid}/requirements",
                  {"requirement_id": "B1", "label": "No pump", "query": "Powered circulation",
                   "field": "powered_circulation", "predicate": {"operator": "equals", "value": False}})
    assert st == 200 and bf["kind"] == "bounded_field" and bf["fts_match"] == '"Powered circulation"'


def test_sample_project_stays_fixed_and_g01_results_are_unchanged(app):
    core, url = app
    call(url, "POST", "/api/demo/bootstrap", {})
    before = json.loads(C.dumps(core._project(core.store.connect(), PID)["mission"]))
    st, e = call(url, "POST", f"/api/projects/{PID}/requirements", {"label": "anything"})
    assert st == 409 and e["error"] == "project_is_fixed"
    st, lst = call(url, "GET", f"/api/projects/{PID}/requirements")
    assert lst["editable"] is False and [r["match"] for r in lst["requirements"]] == ["phrase"] * 3
    assert json.loads(C.dumps(core._project(core.store.connect(), PID)["mission"])) == before
    st, cmp_ = call(url, "POST", f"/api/projects/{PID}/compare", {})
    assert st == 200 and cmp_["run"]["status"] == "completed"
    cells = {(c["candidate_id"], c["requirement_id"]): c["outcome"] for c in core.comparison(PID)["cells"]}
    assert len(cells) == 6 and set(cells.values()) <= {"meets", "does_not_meet", "unknown"}
    run = core.run_view(cmp_["run"]["run_id"])
    assert all(a["detail"]["fts_match"] == C.fts_phrase(a["detail"]["query"])
               for a in run["actions"] if a["action_type"] == "search_current_sources")


# =========================================================================== Compare
def test_compare_runs_assessment_path_and_one_bounded_relation_search_with_real_membership(app):
    core, url = app
    pid = owner_project(url, core)
    call(url, "POST", f"/api/projects/{pid}/requirements",
         {"requirement_id": "U1", "label": "Maximum operating temperature at seaside sites"})
    st, r = call(url, "POST", f"/api/projects/{pid}/compare", {})
    assert st == 200 and r["run"]["status"] == "completed" and r["paid_model_calls"] == 0
    u1 = next(x for x in r["requirements"] if x["requirement"]["requirement_id"] == "U1")
    cell = u1["assessments"][0]["cell"]
    assert cell["outcome"] == "evidence_found" and "does not judge" in cell["explanation"]
    ci = cell["citation"]
    text = text_of(core, pid, ci["source_id"], ci["version_id"])
    assert text[ci["start_char"]:ci["end_char"]] == ci["quote"]
    # the assessment is the committed one in the store (same core path as the Workbench)
    assert core.comparison(pid)["cells"] and any(c["assessment_id"] == cell["assessment_id"]
                                                 for c in core.comparison(pid)["cells"])
    sb = u1["side_by_side"]
    assert sb["label"] == "ENGINEERING DEMO" or sb["label"].startswith("ENGINEERING DEMO")
    assert sb["policy"] == {"name": R.POLICY_V1.name, "sha256": R.POLICY_V1_SHA256}
    assert sb["outcome"] == "searched" and sb["search_calls"] == 2 and sb["budget"]["spent"] == [
        "seed_search", "relation_search"]
    assert sb["issued_query"] == '"annex b" OR "seaside" OR "sites"'
    assert [t["origin"] for t in sb["query_terms"]] == ["source_copy", "original_requirement", "original_requirement"]
    assert sorted(sb["baseline"]["ids"]) == ["letter@v1#clause-4", "letter@v1#clause-5"]   # BM25 order checked below
    assert sb["action"]["new_ids"] == ["letter@v1#annex-b"]
    assert sb["action"]["after_ids"] == sb["baseline"]["ids"] + sb["action"]["new_ids"]
    assert sb["requirement_status_before"] == "unresolved" and sb["requirement_status_after"] == "supported"
    assert sb["recorded_in_store"] is False
    # real membership: the baseline is exactly the FTS5 seed result and the new candidate was not in it
    with core.store.read() as con:
        seed = core._lexical(con, pid, "C1", "", 50, match=sb["seed_query"])
    assert [f"{h['source_id']}@{h['version_id']}#{h['passage_id']}" for h in seed][:5] == sb["baseline"]["ids"]
    new = next(c for c in sb["action"]["candidates"] if c["is_new"])
    assert text[new["start_char"]:new["end_char"]] == new["quote"] and new["quote"].startswith("Annex B.")
    # template requirements: no explicit cross-reference in their seeds -> no extra search, said plainly
    r2 = next(x for x in r["requirements"] if x["requirement"]["requirement_id"] == "R2")["side_by_side"]
    assert r2["outcome"] == "no_unresolved_relation" and r2["issued_query"] is None and r2["search_calls"] == 1
    # one requirement only, without re-running the assessment
    st, only = call(url, "POST", f"/api/projects/{pid}/compare", {"requirement_ids": ["U1"], "run": False})
    assert only["run"] is None and [x["requirement"]["requirement_id"] for x in only["requirements"]] == ["U1"]
    st, e = call(url, "POST", f"/api/projects/{pid}/compare", {"requirement_ids": ["NOPE"]})
    assert st == 422 and e["error"] == "unknown_requirement"


def test_synthetic_example_uses_the_workbench_form_and_inspect_shows_pages(app):
    core, url = app
    st, s = call(url, "POST", "/api/synthetic/relation-search", {})
    assert st == 200 and s["created"] is True and s["project_id"] == R.PROJECT_ID
    sb = s["side_by_side"]
    assert sb["form"].startswith("relation_search.RelationSearchSlice") and sb["recorded_in_store"]
    assert sb["outcome"] == "searched" and sb["action"]["new_ids"]
    assert core.run_view(sb["run_id"])["kind"] == "relation_search"
    st, again = call(url, "POST", "/api/synthetic/relation-search", {})
    assert again["created"] is False and again["side_by_side"]["action"]["new_ids"] == sb["action"]["new_ids"]
    st, e = call(url, "POST", f"/api/projects/{R.PROJECT_ID}/requirements", {"label": "x"})
    assert st == 409
    st, cmp_ = call(url, "POST", f"/api/projects/{R.PROJECT_ID}/compare", {})
    assert cmp_["requirements"][0]["runtime_assessment"]["status"] == "supported"
    new = next(c for c in sb["action"]["candidates"] if c["is_new"])
    st, x = call(url, "GET", f"/api/projects/{R.PROJECT_ID}/sources/{new['source_id']}/versions/{new['version_id']}"
                             f"/spans/{new['start_char']}/{new['end_char']}")
    assert st == 200 and x["quote"] == new["quote"] and x["page_mapping"]["state"] == "regions"
    assert x["page_mapping"]["pages"] == [1] and x["page_mapping"]["regions"][0]["node_id"] == new["node_id"]
    o = x["original_artifact"]
    assert o["state"] == "kept" and o["media_type"] == "application/pdf" and o["integrity"] == "verified"
    assert o["same_bytes_as_canonical_text"] is False
    st, pdf, headers = call(url, "GET", o["url"], raw=True)
    assert st == 200 and pdf.startswith(b"%PDF-") and C.sha256(pdf) == o["sha256"]
    assert headers["Content-Type"] == "application/pdf" and headers["Content-Security-Policy"] == "sandbox"


# =========================================================================== Inspect
def test_inspect_resolves_spans_and_reports_missing_page_mapping_honestly(app):
    core, url = app
    pid = owner_project(url, core)
    text = text_of(core, pid, "letter", "v1")
    s = text.index("seaside sites")
    e = s + len("seaside sites")
    st, x = call(url, "GET", f"/api/projects/{pid}/sources/letter/versions/v1/spans/{s}/{e}")
    assert st == 200 and x["quote"] == "seaside sites" and x["text_before"] + x["quote"] + x["text_after"] == text
    assert [p["passage_id"] for p in x["passages"]] == ["clause-5"] and x["stored_text_integrity"] == "verified"
    assert x["page_mapping"]["state"] == "none" and x["page_mapping"]["reason"]
    o = x["original_artifact"]
    assert o["state"] == "kept" and o["same_bytes_as_canonical_text"] is True and o["integrity"] == "verified"
    st, raw, headers = call(url, "GET", o["url"], raw=True)
    assert raw == LETTER.encode("utf-8") and headers["Content-Type"].startswith("text/plain")
    # Thai span resolves exactly
    t = text.index("เปลี่ยนแยกได้")
    st, th = call(url, "GET", f"/api/projects/{pid}/sources/letter/versions/v1/spans/{t}/{t + len('เปลี่ยนแยกได้')}")
    assert th["quote"] == "เปลี่ยนแยกได้"
    # the G01 sample keeps no separate original file: said so, not invented
    call(url, "POST", "/api/demo/bootstrap", {})
    st, smp = call(url, "GET", f"/api/projects/{PID}/sources/DEMO-S1/versions/v1/spans/0/3")
    assert smp["original_artifact"]["state"] == "not_kept" and smp["page_mapping"]["state"] == "none"
    st, e1 = call(url, "GET", f"/api/projects/{PID}/sources/DEMO-S1/versions/v1/original")
    assert st == 404 and e1["error"] == "original_not_kept"
    for a, b in ((5, 5), (10, 10 ** 7), ("x", 3)):
        st, err = call(url, "GET", f"/api/projects/{pid}/sources/letter/versions/v1/spans/{a}/{b}")
        assert st == 422 and err["error"] == "bad_span"
    st, err = call(url, "GET", f"/api/projects/{pid}/sources/letter/versions/v9/spans/0/1")
    assert st == 404


def test_inspect_pdf_page_from_text_layer_markers(app):
    pytest.importorskip("pypdf")
    from patent_to_pilot.workbench.trace_slice import FIXTURE_DIR
    core, url = app
    st, p = call(url, "POST", "/api/projects", {"title": "PDF inspect", "candidates": [{"candidate_id": "C1",
                                                                                         "label": "PDF"}]})
    pid = p["project_id"]
    pdf = (FIXTURE_DIR / "letter_v1.pdf").read_bytes()
    st, ing = call(url, "POST", f"/api/projects/{pid}/documents",
                   {"filename": "letter.pdf", "candidate_id": "C1", "content_base64": base64.b64encode(pdf).decode()})
    assert st == 200, ing
    st, r = call(url, "POST", f"/api/projects/{pid}/search", {"query": "seaside"})
    h = r["results"][0]
    st, x = call(url, "GET", f"/api/projects/{pid}/sources/{h['source_id']}/versions/{h['version_id']}"
                             f"/spans/{h['start_char']}/{h['end_char']}")
    assert x["page_mapping"]["state"] == "page_only" and x["page_mapping"]["pages"] == [1]
    assert x["page_mapping"]["regions"] == [] and x["original_artifact"]["same_bytes_as_canonical_text"] is False
    st, raw, _ = call(url, "GET", x["original_artifact"]["url"], raw=True)
    assert raw == pdf


def test_page_serves_search_compare_and_inspect_ui(app):
    _core, url = app
    st, page, _ = call(url, "GET", "/", raw=True)
    html = page.decode("utf-8")
    for needle in ('data-view="search"', 'data-view="compare"', 'id="search-form"', 'id="req-form"',
                   'id="load-synthetic"', "Patent-to-Pilot Workbench"):
        assert needle in html
    st, js, _ = call(url, "GET", "/app.js", raw=True)
    assert b"/spans/" in js and b"/compare" in js and b"/search" in js
