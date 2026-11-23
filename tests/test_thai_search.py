"""P4-T01a: normal Thai search works by default (owner plan 23 Nov 2026, section 4).

Authored engineering fixtures only (no benchmark, no TEST data, no network, no model). Every returned citation and every
highlight offset is checked against the stored canonical text."""
from __future__ import annotations

import base64
import json
import sqlite3
import threading
import urllib.request

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench import product_lexical as PL
from patent_to_pilot.workbench import thai_analyzer as TA
from patent_to_pilot.workbench.guard import loopback_only
from patent_to_pilot.workbench.server import create_server
from patent_to_pilot.workbench.workflow import Workflow

THAI_DOC = """# ประกาศทดสอบ (authored fixture)

## p1
ผู้ประกอบธุรกิจต้องยื่นคำขอตามข้อ ๕(๒) ภายในสามสิบวัน เว้นแต่ได้รับอนุญาตเป็นหนังสือ

## p2
ห้ามผู้ใดใช้เครื่องหมายนี้ ไม่ว่ากรณีใด ๆ ค่าธรรมเนียมคำขอละ ๕๐๐ บาท ตามข้อ 52

## p3
The heat-sink module must be replaceable. หน่วยระบายความร้อนต้องเปลี่ยนแยกได้ทันที

## p4
😀𠀀 ต้องแจ้ง ต้องแจ้ง และต้องแจ้งอีกครั้ง

## p5
Café crème éclair (Latin with a combining acute accent)
"""
OTHER_DOC = """# Other supplier (authored fixture)

## q1
ผู้ประกอบธุรกิจต้องยื่นคำขอภายในเจ็ดวัน
"""


@pytest.fixture
def thai():
    pytest.importorskip("pythainlp")
    return TA.analyzer()


def new_project(core, title="Thai search", candidates=(("C1", "Supplier one"), ("C2", "Supplier two"))):
    return core.create_project(title, candidates=[{"candidate_id": c, "label": l} for c, l in candidates])["project_id"]


@pytest.fixture
def setup(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    pid = new_project(core)
    assert core.ingest_document(pid, "thai.md", THAI_DOC.encode("utf-8"), "C1")["status"] == "ingested"
    assert core.ingest_document(pid, "other.md", OTHER_DOC.encode("utf-8"), "C2")["status"] == "ingested"
    return core, Workflow(core), pid


def text_of(core, pid, sid, vid):
    return core.source_version(pid, sid, vid)["text"]


def check_exact(core, pid, r):
    """Every result quote, snippet and highlight resolves exactly in the canonical text (code points)."""
    for h in r["results"]:
        text = text_of(core, pid, h["source_id"], h["version_id"])
        assert text[h["start_char"]:h["end_char"]] == h["quote"]
        assert text[h["snippet_start_char"]:h["snippet_end_char"]] == h["snippet"]
        for m in h["matches"]:
            assert h["start_char"] <= m["start_char"] < m["end_char"] <= h["end_char"]


def marked(core, pid, h):
    text = text_of(core, pid, h["source_id"], h["version_id"])
    return [text[m["start_char"]:m["end_char"]] for m in h["matches"]]


# =========================================================================== analyzer contract
def test_analyzer_alignment_offsets_negation_and_identity(thai):
    text = "ห้ามเว้นแต่ได้รับอนุญาต ต้องยื่น ไม่ว่ากรณีใด 😀𠀀ข้อ๕"
    toks = thai.tokens(text)
    assert all(text[s:e] == t for t, s, e in toks)                      # half-open code-point offsets
    words = [t for t, _s, _e in toks]
    for w in ("ห้าม", "เว้นแต่", "ไม่", "ต้อง"):                          # negation / modal words are kept
        assert w in words
    terms, fell_back = thai.terms(text)
    assert not fell_back and "5" in [t.norm for t in terms]            # Thai digit folded to its ASCII key
    assert all(len(TA.fold(text[t.start:t.end])) == t.end - t.start for t in terms)
    ident = thai.identity
    assert ident["engine"] == "newmm-safe" and ident["pythainlp_version"].startswith("5.4")
    assert len(ident["dictionary_sha256"]) == 64 and ident["domain_terms"]["words"] == len(TA.DOMAIN_TERMS)
    assert thai.identity_id.startswith("ptp-thai-lexical/1.0.0;newmm-safe;")
    assert TA.analyzer() is thai                                         # built once per process
    # identifiers keep the original spelling; Thai and ASCII digits share one key; sub-items match, 52 does not
    ids = TA.identifiers("ตามข้อ ๕(๒) และข้อ 5(2) และข้อ 52 และ Annex B และข้อความ")
    assert [(i.text, i.key) for i in ids] == [("ข้อ ๕(๒)", "ข้อ:5(2)"), ("ข้อ 5(2)", "ข้อ:5(2)"),
                                              ("ข้อ 52", "ข้อ:52"), ("Annex B", "annex:b")]
    assert TA.key_matches("ข้อ:5", "ข้อ:5(2)") and not TA.key_matches("ข้อ:5", "ข้อ:52")


def test_misaligned_tokenizer_output_is_never_indexed(thai, monkeypatch):
    monkeypatch.setattr(thai, "_word_tokenize", lambda text, **kw: [text.replace("ต้อง", "ตอง")])
    with pytest.raises(TA.AlignmentError):
        thai.tokens("ต้องแจ้ง")
    terms, fell_back = thai.terms("ต้องแจ้ง abc")
    assert fell_back and [t.norm for t in terms] == ["ต้องแจ้ง", "abc"]     # declared fallback: indexable runs


def test_mark_categories_keep_thai_words_whole_in_the_derived_index(setup):
    core, _wf, pid = setup
    con = sqlite3.connect(":memory:")
    con.execute("CREATE VIRTUAL TABLE legacy USING fts5(body, tokenize='unicode61')")
    con.execute(f"CREATE VIRTUAL TABLE derived USING fts5(body, tokenize=\"{TA.FTS_TOKENIZE}\")")
    for t in ("legacy", "derived"):
        con.execute(f"INSERT INTO {t} VALUES ('ผู้ ประกอบ ธุรกิจ')")
        con.execute(f"CREATE VIRTUAL TABLE {t}_v USING fts5vocab({t}, row)")
    legacy = {r[0] for r in con.execute("SELECT term FROM legacy_v")}
    derived = {r[0] for r in con.execute("SELECT term FROM derived_v")}
    assert derived == {"ผู้", "ประกอบ", "ธุรกิจ"} and legacy != derived   # default unicode61 breaks at marks
    with core.store.read() as c:
        c.execute(f"CREATE VIRTUAL TABLE temp.v USING fts5vocab(main, {PL.INDEX_NAME}, row)")
        vocab = {r[0] for r in c.execute("SELECT term FROM temp.v")}
    assert {"ต้อง", "ผู้ประกอบธุรกิจ", "เว้นแต่", "ไม่", "ห้าม", "5", "2"} <= vocab


# =========================================================================== search behaviour
def test_unspaced_thai_query_finds_the_right_passage_with_exact_quote(setup):
    core, wf, pid = setup
    r = wf.search(pid, {"query": "ยื่นคำขอภายในสามสิบวัน"})
    assert r["mode"] == "auto" and r["route"].startswith(PL.PROFILE) and r["paid_model_calls"] == 0
    top = r["results"][0]
    assert (top["source_id"], top["passage_id"], top["route"]) == ("thai", "p1", "all_words")
    assert "ยื่นคำขอตามข้อ" in top["quote"] and marked(core, pid, top) == ["ยื่นคำขอ", "ภายในสามสิบวัน"]
    check_exact(core, pid, r)
    assert r["lexical_trace"]["index"] == PL.INDEX_NAME and r["lexical_trace"]["generation"] >= 1
    # the legacy unicode61 route stays available as an advanced mode (historical control)
    assert wf.search(pid, {"query": "ยื่นคำขอภายในสามสิบวัน", "mode": "terms"})["route"].startswith("sqlite_fts5")


def test_combining_marks_and_mixed_thai_english(setup):
    core, wf, pid = setup
    r = wf.search(pid, {"query": "heat sink ระบายความร้อน"})
    top = r["results"][0]
    assert top["passage_id"] == "p3" and top["route"] == "all_words"
    assert marked(core, pid, top) == ["heat", "sink", "ระบายความร้อน"]
    r = wf.search(pid, {"query": "ต้องแจ้ง"})                            # Thai marks inside the word
    assert r["results"][0]["passage_id"] == "p4"
    r = wf.search(pid, {"query": "éclair"})                       # Latin combining acute accent (M*)
    assert r["results"][0]["passage_id"] == "p5" and "éclair" in marked(core, pid, r["results"][0])
    r = wf.search(pid, {"query": "CAFÉ"})
    assert r["results"][0]["passage_id"] == "p5"
    check_exact(core, pid, r)


def test_thai_and_arabic_digits_in_section_identifiers(setup):
    core, wf, pid = setup
    for q in ("ข้อ 5(2)", "ข้อ ๕(๒)", "ข้อ 5", "ข้อ๕"):
        r = wf.search(pid, {"query": q})
        top = r["results"][0]
        assert (top["passage_id"], top["route"]) == ("p1", "identifier"), q
        assert "ข้อ ๕(๒)" in marked(core, pid, top)                        # original spelling is highlighted
        assert all(h["route"] != "identifier" or h["passage_id"] == "p1" for h in r["results"])
        assert r["lexical_trace"]["identifiers"][0]["key"].startswith("ข้อ:5")
        check_exact(core, pid, r)
    r = wf.search(pid, {"query": "ข้อ ๕๒"})                                # Thai digits find ASCII 52, not 5(2)
    assert [(h["passage_id"], h["route"]) for h in r["results"] if h["route"] == "identifier"] == [("p2", "identifier")]
    r = wf.search(pid, {"query": "500 บาท"})                               # ASCII query, Thai-digit source
    assert r["results"][0]["passage_id"] == "p2" and "๕๐๐ บาท" in marked(core, pid, r["results"][0])


@pytest.mark.parametrize("q", ['"', 'ต้อง"', 'a OR b', 'ต้อง AND', 'NOT ห้าม', 'NEAR(ต้อง แจ้ง)', 'ต้อง*', 'body:ต้อง',
                               "'; DROP TABLE passages; --", "^ห้าม", "(", "-", "{body}: x"])
def test_query_quotes_and_operators_are_inert(setup, q):
    core, wf, pid = setup
    r = wf.search(pid, {"query": q})
    for x in r["lexical_trace"]["issued"]:
        if x["route"] != "substring":
            assert x["match"].count('"') % 2 == 0
    check_exact(core, pid, r)
    with core.store.read() as con:                                        # nothing was dropped or altered
        assert con.execute("SELECT COUNT(*) FROM passages WHERE project_id=?", (pid,)).fetchone()[0] == 6


def test_short_and_hidden_word_queries_use_the_bounded_fallback(setup):
    core, wf, pid = setup
    r = wf.search(pid, {"query": "ธุรกิจ"})       # inside the dictionary word ผู้ประกอบธุรกิจ: word index has no hit
    fb = r["lexical_trace"]["fallback"]
    assert fb["triggered"] and "no_word_hits" in fb["reasons"] and fb["scanned"] == 6 and not fb["capped"]
    assert {(h["passage_id"], h["route"]) for h in r["results"]} == {("p1", "substring"), ("q1", "substring")}
    assert all(marked(core, pid, h) == ["ธุรกิจ"] for h in r["results"]) and r["notes"]
    r = wf.search(pid, {"query": "ห", "limit": 2})
    fb = r["lexical_trace"]["fallback"]
    assert "short_query" in fb["reasons"] and len(r["results"]) == 2 and fb["returned"] == 2
    check_exact(core, pid, r)
    r = wf.search(pid, {"query": "replaceable"})                          # English with hits: no fallback reason
    assert r["lexical_trace"]["fallback"]["reasons"] == [] and r["results"][0]["route"] == "any_word"


def test_repeated_words_and_supplementary_characters_in_spans(setup):
    core, wf, pid = setup
    r = wf.search(pid, {"query": "ต้องแจ้ง"})
    h = next(x for x in r["results"] if x["passage_id"] == "p4")
    text = text_of(core, pid, h["source_id"], h["version_id"])
    assert h["quote"].startswith("😀𠀀")                                  # two supplementary-plane code points
    assert marked(core, pid, h) == ["ต้องแจ้ง", "ต้องแจ้ง", "ต้องแจ้ง"]
    first = h["matches"][0]["start_char"]
    assert first == text.index("ต้องแจ้ง") and first - h["start_char"] == 3   # code points, not UTF-16 units
    starts = [m["start_char"] for m in h["matches"]]
    assert starts == sorted(set(starts))
    x = wf.inspect(pid, h["source_id"], h["version_id"], h["matches"][2]["start_char"], h["matches"][2]["end_char"])
    assert x["quote"] == "ต้องแจ้ง" and x["stored_text_integrity"] == "verified"


def test_project_version_and_candidate_isolation(setup):
    core, wf, pid = setup
    r = wf.search(pid, {"query": "ผู้ประกอบธุรกิจต้องยื่นคำขอ"})
    assert {h["candidate_id"] for h in r["results"]} == {"C1", "C2"}
    r = wf.search(pid, {"query": "ผู้ประกอบธุรกิจต้องยื่นคำขอ", "candidate_id": "C2"})
    assert {h["candidate_id"] for h in r["results"]} == {"C2"} and {h["passage_id"] for h in r["results"]} == {"q1"}
    other = new_project(core, "Other project", (("C1", "Elsewhere"),))
    assert wf.search(other, {"query": "ผู้ประกอบธุรกิจ"})["results"] == []      # no cross-project leakage
    revised = OTHER_DOC.replace("ภายในเจ็ดวัน", "ภายในสิบห้าวัน")
    out = core.ingest_document(pid, "other.md", revised.encode("utf-8"), "C2", source_id="other")
    assert out["version_id"] == "v2"
    assert all(h["version_id"] != "v1" or h["source_id"] != "other"
               for h in wf.search(pid, {"query": "เจ็ดวัน"})["results"])
    assert not any("เจ็ดวัน" in h["quote"] for h in wf.search(pid, {"query": "เจ็ดวัน"})["results"])
    r = wf.search(pid, {"query": "สิบห้าวัน"})
    top = r["results"][0]
    assert (top["source_id"], top["version_id"], top["route"]) == ("other", "v2", "all_words")
    assert [h["route"] for h in r["results"][1:]] == ["any_word"] * (len(r["results"]) - 1)
    with core.store.read() as con:
        rows = {(x[0], x[1]) for x in con.execute(f"SELECT source_id, version_id FROM {PL.INDEX_NAME} WHERE "
                                                  "project_id=?", (pid,))}
        st = PL.ProductLexical.state(con, pid)
        kinds = [x[0] for x in con.execute("SELECT kind FROM lexical_index_generations WHERE project_id=? ORDER BY "
                                           "generation", (pid,))]
    assert rows == {("thai", "v1"), ("other", "v2")} and st["generation"] == 3
    assert kinds == ["full_rebuild", "incremental", "incremental"]


def test_rebuild_on_demand_and_restart(setup):
    core, wf, pid = setup
    before = wf.search(pid, {"query": "ห้ามใช้เครื่องหมาย"})
    gen = before["lexical_trace"]["generation"]
    core2 = C.EvidenceCore(core.store.data_dir)                         # restart: same store, new process objects
    again = Workflow(core2).search(pid, {"query": "ห้ามใช้เครื่องหมาย"})
    assert again["lexical_trace"]["generation"] == gen
    assert [h["node_id"] for h in again["results"]] == [h["node_id"] for h in before["results"]]
    with core2.store.tx() as con:                                         # an index built by another analyzer
        con.execute("UPDATE lexical_index_state SET analyzer_id='ptp-thai-lexical/0.9' WHERE project_id=?", (pid,))
    r = Workflow(core2).search(pid, {"query": "ห้ามใช้เครื่องหมาย"})
    assert r["lexical_trace"]["generation"] == gen + 1
    assert [h["node_id"] for h in r["results"]] == [h["node_id"] for h in before["results"]]
    with core2.store.read() as con:
        last = con.execute("SELECT kind, reason FROM lexical_index_generations WHERE project_id=? ORDER BY generation "
                           "DESC LIMIT 1", (pid,)).fetchone()
    assert last[0] == "full_rebuild" and "analyzer identity changed" in last[1]
    # an existing store from before P4-T01a (no derivative tables) migrates additively and rebuilds on demand
    with core2.store.tx() as con:
        for t in (PL.INDEX_NAME, "lexical_index_state", "lexical_index_generations"):
            con.execute(f"DROP TABLE {t}")
    core3 = C.EvidenceCore(core.store.data_dir)
    r = Workflow(core3).search(pid, {"query": "ห้ามใช้เครื่องหมาย"})
    assert r["lexical_trace"]["generation"] == 1 and r["index"]["lexical_index"]["status"] == "active"
    assert "on demand" in r["index"]["lexical_index"]["reason"]
    assert [h["node_id"] for h in r["results"]] == [h["node_id"] for h in before["results"]]


def test_legacy_index_and_g01_sample_are_untouched(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    core.bootstrap_sample()
    with core.store.read() as con:
        sql = con.execute("SELECT sql FROM sqlite_master WHERE name='passage_fts'").fetchone()[0]
        legacy_before = [tuple(r) for r in con.execute("SELECT * FROM passage_fts ORDER BY rowid")]
    assert "tokenize='unicode61'" in sql
    wf = Workflow(core)
    wf.search(C.SAMPLE_PROJECT_ID, {"query": "temperature"})
    run = core.run_comparison(C.SAMPLE_PROJECT_ID)
    with core.store.read() as con:
        assert [tuple(r) for r in con.execute("SELECT * FROM passage_fts ORDER BY rowid")] == legacy_before
    searches = [a for a in run["actions"] if a["action_type"] == "search_current_sources"]
    assert searches and all("lexical" not in a["detail"] for a in searches)        # the sample keeps the legacy route
    assert all("lexical" not in h for a in searches for h in a["detail"]["hits"])
    assert all(a["detail"]["fts_match"] == C.fts_phrase(a["detail"]["query"]) for a in searches)


# =========================================================================== owner requirement matching
def test_owner_thai_requirement_is_matched_through_the_product_analyzer(setup):
    core, wf, pid = setup
    out = wf.save_requirement(pid, {"requirement_id": "TH1", "label": "ยื่นคำขอภายในสามสิบวัน"})
    assert out["status"] == "added"
    run = core.run_comparison(pid)
    cell = next(c for c in core.comparison(pid)["cells"] if (c["candidate_id"], c["requirement_id"]) == ("C1", "TH1"))
    assert cell["outcome"] == "evidence_found" and cell["citation"]["passage_id"] == "p1"
    cit = cell["citation"]
    text = text_of(core, pid, cit["source_id"], cit["version_id"])
    assert text[cit["start_char"]:cit["end_char"]].startswith("ผู้ประกอบธุรกิจต้องยื่นคำขอ")
    act = next(a for a in run["actions"] if a["action_type"] == "search_current_sources"
               and (a["candidate_id"], a["requirement_id"]) == ("C1", "TH1"))
    lex = act["detail"]["lexical"]
    assert lex["index"] == PL.INDEX_NAME and lex["mode"] == "auto" and lex["analyzer"].startswith("ptp-thai-lexical/")
    assert act["detail"]["hits"][0]["lexical"]["route"] == "all_words"


# =========================================================================== without PyThaiNLP
def test_without_the_analyzer_search_degrades_to_legacy_plus_bounded_check(tmp_path, monkeypatch):
    def unavailable():
        raise TA.AnalyzerUnavailable("PyThaiNLP is not installed (simulated)")
    monkeypatch.setattr(TA, "analyzer", unavailable)
    core = C.EvidenceCore(tmp_path / "store")
    pid = new_project(core)
    core.ingest_document(pid, "thai.md", THAI_DOC.encode("utf-8"), "C1")
    wf = Workflow(core)
    r = wf.search(pid, {"query": "ธุรกิจ"})
    assert r["lexical_trace"]["index"] == PL.LEGACY_INDEX and "analyzer_unavailable" in r["lexical_trace"]["fallback"][
        "reasons"]
    assert [h["passage_id"] for h in r["results"]] == ["p1"] and any("not installed" in n for n in r["notes"])
    check_exact(core, pid, r)
    assert core.capabilities()["lexical"]["product_thai"]["state"] == "analyzer_unavailable"


# =========================================================================== owner acceptance over HTTP
def test_owner_acceptance_import_type_unspaced_thai_open_result(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    srv = create_server(core, port=0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"

    def call(method, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"} if data else {})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    try:
        with loopback_only():
            p = call("POST", "/api/projects", {"title": "Thai acceptance",
                                               "candidates": [{"candidate_id": "C1", "label": "Supplier"}]})
            pid = p["project_id"]
            call("POST", f"/api/projects/{pid}/documents", {
                "filename": "thai.md", "candidate_id": "C1",
                "content_base64": base64.b64encode(THAI_DOC.encode("utf-8")).decode("ascii")})
            r = call("POST", f"/api/projects/{pid}/search", {"query": "หน่วยระบายความร้อนต้องเปลี่ยนแยกได้"})
            assert r["mode"] == "auto"
            h = r["results"][0]
            x = call("GET", f"/api/projects/{pid}/sources/{h['source_id']}/versions/{h['version_id']}/spans/"
                            f"{h['start_char']}/{h['end_char']}")
            assert x["quote"] == h["quote"] and "หน่วยระบายความร้อนต้องเปลี่ยนแยกได้ทันที" in x["quote"]
            assert x["text_before"] + x["quote"] + x["text_after"] == text_of(core, pid, h["source_id"],
                                                                              h["version_id"])
    finally:
        srv.shutdown()
        srv.server_close()
