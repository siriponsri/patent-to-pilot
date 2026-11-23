"""P4-T03: useful expansion without an annex keyword (owner fix plan of 23 Nov 2026, section 5).

Authored engineering fixtures imported through the real owner-import path (text/Markdown, and the PDF text layer when
pypdf is installed). No network beyond loopback, no model, no paid call. These are mechanism checks, not retrieval
results: nothing here measures or claims an effectiveness gain."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench import relation_search as R
from patent_to_pilot.workbench import structure as S
from patent_to_pilot.workbench.guard import loopback_only
from patent_to_pilot.workbench.server import create_server
from patent_to_pilot.workbench.workflow import Workflow

NOTICE = """# ประกาศกรมทดสอบ เรื่อง เงื่อนไขเครื่องทดสอบ

ข้อ ๑ ผู้ยื่นคำขอต้องมีคุณสมบัติตามที่กำหนดในประกาศนี้

ข้อ ๒ อุณหภูมิใช้งานของเครื่องต้องเป็นไปตามข้อ ๔(๒)

ข้อ ๓ ผู้ยื่นคำขอต้องเป็นนิติบุคคล

ข้อ ๔ เงื่อนไขการใช้งาน
(๑) ค่าธรรมเนียมคำขอ ฉบับละ ๕๐๐ บาท
(๒) ช่วงอุณหภูมิ
Supported temperature range: 5 to 60 °C.
"""
TEMP_REQ = {"requirement_id": "T1", "label": "ช่วงอุณหภูมิใช้งาน 10-50 องศา", "query": "อุณหภูมิใช้งาน",
            "field": "supported_temperature_range",
            "predicate": {"operator": "contains_interval", "minimum": 10, "maximum": 50, "unit": "degC"}}
PLAIN = """# Supplier note (no references)

## Cooling

The heat-sink module must be replaceable in the field.

## Packaging

Units ship in recyclable crates.
"""
FEES = """# ประกาศกรมทดสอบ เรื่อง การยื่นคำขอ

ข้อ ๑ ผู้ยื่นคำขอต้องเป็นนิติบุคคลที่จดทะเบียนในประเทศไทย

ข้อ ๒ ค่าธรรมเนียมการยื่นคำขอ ฉบับละ ๕๐๐ บาท
"""
FEE_REQ = {"requirement_id": "F1", "label": "อัตราค่าธรรมเนียมคำขอ", "match": "phrase"}
ELIG_REQ = {"requirement_id": "E1", "label": "คุณสมบัติผู้ยื่นคำขอ", "query": "นิติบุคคลที่จดทะเบียน"}


@pytest.fixture
def thai():
    pytest.importorskip("pythainlp")


def project(core, reqs, candidates=(("C1", "Supplier one"),)):
    return core.create_project("P4-T03 test", [{"candidate_id": c, "label": l} for c, l in candidates],
                               reqs)["project_id"]


def ingest(core, pid, name, text, cand="C1", sid=None):
    out = core.ingest_document(pid, name, text.encode("utf-8") if isinstance(text, str) else text, cand, sid)
    assert out["status"] == "ingested", out
    return out


def cell(core, pid, cand, rid):
    return next((c for c in core.comparison(pid)["cells"] if (c["candidate_id"], c["requirement_id"]) == (cand, rid)),
                None)


def receipts(run, cand=None, rid=None):
    return [a["detail"] for a in run["actions"] if a["action_type"] == "structural_acquisition"
            and (cand is None or a["candidate_id"] == cand) and (rid is None or a["requirement_id"] == rid)]


def quote_is_exact(core, pid, cit):
    text = core.source_version(pid, cit["source_id"], cit["version_id"])["text"]
    with core.store.read() as con:
        q = con.execute("SELECT quote FROM citations WHERE source_id=? AND version_id=? AND passage_id=? AND "
                        "start_char=?", (cit["source_id"], cit["version_id"], cit["passage_id"],
                                         cit["start_char"])).fetchone()[0]
    return text[cit["start_char"]:cit["end_char"]] == q


# =========================================================================== policy and pure operator
def test_policy_v1_unchanged_and_v2_is_new_pinned_and_separate():
    assert R.POLICY_V1.fingerprint() == R.POLICY_V1_SHA256 == \
        "e4ea084cd572e4fdda37838451c9d2838f7af61bc5c68b7cec4468411265629c"
    assert R.POLICY_V2.name == "ptp-structural-acquisition/2.0.0" and R.POLICY_V2.max_expansion_searches == 1
    assert R.POLICY_V2.fingerprint() == R.POLICY_V2_SHA256 == R.PINNED_POLICY_SHA256[R.POLICY_V2.name]
    changed = R.SelectionPolicy(**{**R.POLICY_V2.describe(), "max_expansion_searches": 2})
    with pytest.raises(C.ValidationFailed) as e:
        R.select_structural_action(changed, [])
    assert e.value.code == "policy_unknown"
    with pytest.raises(C.ValidationFailed) as e:      # each family keeps its own operator
        R.select_structural_action(R.POLICY_V1, [])
    assert e.value.code == "policy_family"
    qr = R.QueryRequirements("q", "need", (R.Requirement("r", 0, 4, "need"),))
    with pytest.raises(C.ValidationFailed) as e:
        R.select_relation(R.POLICY_V2, qr, [], [], R.EvidenceRegistry())
    assert e.value.code == "policy_family"


def test_policy_v2_1_is_pinned_and_changes_only_the_no_hit_anchor_rule():
    """D25: 2.1.0 is a new pinned version; 2.0.0 stays byte-identical and selectable; only S1 (anchor) changes."""
    v2, v21 = R.POLICY_V2, R.POLICY_V2_1
    assert v21.name == "ptp-structural-acquisition/2.1.0" and v21.max_expansion_searches == 1
    assert v21.fingerprint() == R.POLICY_V2_1_SHA256 == R.PINNED_POLICY_SHA256[v21.name] == \
        "b632a2ca67e5037850312789e6ca1c6d6e5abb858b4ab00390269640d7686df4"
    assert R.POLICY_V2_SHA256 == "124909017ac6a77daa253585399a202540f2dc01756fc41d28ae6bd4815fdd89"
    assert R.CURRENT_STRUCTURAL_POLICY is v21 and R.STRUCTURAL_POLICY_NAMES == {v2.name, v21.name}
    assert v21.query_rule == v2.query_rule and v21.rerank_rule == v2.rerank_rule
    assert v21.selection_rule[0] == v2.selection_rule[0] and v21.selection_rule[3:] == v2.selection_rule[2:]
    assert "cited most often" in v2.selection_rule[1] and "cited" not in v21.selection_rule[1]
    assert v21.selection_rule[2].startswith("S1a ") and "never read" in v21.selection_rule[2]
    assert R.select_structural_action(v21, [])["selected"] is None      # a known structural policy
    with pytest.raises(C.ValidationFailed) as e:
        R.select_relation(v21, R.QueryRequirements("q", "need", (R.Requirement("r", 0, 4, "need"),)), [], [],
                          R.EvidenceRegistry())
    assert e.value.code == "policy_family"


def _cand(key, action, rank, start=None, actionable=True, uid="d2@v1#p1"):
    return R.ActionCandidate(key, "r", action, "unresolved_reference" if action in ("resolve_reference",
                                                                                     "recover_context") else "no_hit",
                             "resolved" if actionable else "ambiguous", actionable, "test", rank, start,
                             target=({"unit_id": uid},))


def test_pure_step_runs_at_most_one_action_and_splits_same_and_new_document_gain():
    qr = R.QueryRequirements("q", "fee amount", (R.Requirement("r", 0, 10, "fee amount"),))
    fp = qr.sha256()
    mask = R.EligibilityMask("m", exclude_groups=frozenset({"other"}), grouping="doc",
                             group_of=lambda u: u.split("@", 1)[0])
    calls = []

    def execute(c, fetch):
        calls.append(c.action_key)
        return {"ranked": [("d1@v1#p9", 2.0), ("d3@v1#p1", 1.0), ("other@v1#p1", 9.0)], "query": "q",
                "scope": {"x": 1}, "index_generation": "g"}
    cands = [_cand("b", "search_eligible_corpus", 1), _cand("a", "resolve_reference", 0, 50),
             _cand("z", "resolve_reference", 0, 10, actionable=False)]
    rec = R.structural_action_step(requirements=qr, candidates=cands, pool_before=["d1@v1#p1"], execute=execute,
                                   rerank=lambda req, ids: {i: float(len(i)) for i in ids},
                                   budget=R.ActionBudget(1), eligibility=mask,
                                   unit_document=lambda u: u.split("@", 1)[0], gaps=["unresolved_reference"],
                                   result_limit=5, fetch_limit=5)
    assert calls == ["a"] and rec["action"] == "resolve_reference" and rec["search_calls"] == 1
    assert rec["selection"]["skipped"] == [{"action_key": "z", "reason": "state_ambiguous"}]
    assert rec["new_unit_ids"] == ["d1@v1#p9", "d3@v1#p1"] and rec["same_document_unit_ids"] == ["d1@v1#p9"]
    assert rec["new_document_ids"] == ["d3"] and rec["excluded_ineligible"][0]["unit_id"] == "other@v1#p1"
    assert rec["budget_after"] == {"limit": 1, "used": 1, "spent": ["resolve_reference"]}
    assert rec["outcome"] == "acquired" and qr.sha256() == fp == rec["requirement_version"]
    assert rec["rerank"]["request"]["requirement_texts"] == ["fee amount"]        # the original requirement only
    empty = R.structural_action_step(requirements=qr, candidates=cands, pool_before=[], execute=execute,
                                     rerank=lambda *_: {}, budget=R.ActionBudget(0), eligibility=mask,
                                     unit_document=lambda u: u, result_limit=5)
    assert empty["outcome"] == "budget_exhausted" and calls == ["a"]
    none = R.structural_action_step(requirements=qr, candidates=[], pool_before=[], execute=execute,
                                    rerank=lambda *_: {}, budget=R.ActionBudget(1), eligibility=mask,
                                    unit_document=lambda u: u)
    assert none["outcome"] == "no_gap" and none["search_calls"] == 0
    with pytest.raises(R.IneligibleCandidate):
        R.structural_action_step(requirements=qr, candidates=[], pool_before=["other@v1#p1"], execute=execute,
                                 rerank=lambda *_: {}, budget=R.ActionBudget(1), eligibility=mask,
                                 unit_document=lambda u: u)


# =========================================================================== structure adapter (pure)
def _build(text, kind="owner_markdown"):
    from patent_to_pilot.workbench import ingest as I
    prep = I.prepare("x.md" if kind == "owner_markdown" else "x.txt", text.encode("utf-8"), C.extract_passages)
    return prep, S.build(prep["text"], prep["passages"], kind)


def test_structure_thai_digits_nested_numbering_paragraphs_footnotes_and_tables():
    text = NOTICE + "\nวรรคสองของข้อ ๔ ใช้บังคับตามวรรคหนึ่ง[^1]\n\n| รายการ | อัตรา |\n|---|---|\n| คำขอ | ๕๐๐ |\n\n" \
                    "[^1]: หมายเหตุ\n"
    prep, b = _build(text)
    by = {n["section_path"]: n for n in b["nodes"] if n["section_path"]}
    assert {"ข้อ:1", "ข้อ:2", "ข้อ:3", "ข้อ:4", "ข้อ:4(1)", "ข้อ:4(2)", "ข้อ:4/วรรค:1", "ข้อ:4/วรรค:2"} <= set(by)
    n42 = by["ข้อ:4(2)"]
    assert prep["text"][n42["start"]:n42["end"]].startswith("(๒) ช่วงอุณหภูมิ")      # exact span, original spelling
    assert n42["rule"] == "nested_parenthesized_item_v1" and n42["confidence"] == S.RULES[n42["rule"]]
    kinds = {n["kind"] for n in b["nodes"]}
    assert {"footnote", "table", "table_header", "heading"} <= kinds            # Markdown exposes them
    assert all(e["rule"] in S.RULES and e["confidence"] == S.RULES[e["rule"]] for e in b["edges"])
    refs = {e["span_text"]: e for e in b["edges"] if e["kind"] == "reference"}
    assert refs["ข้อ ๔(๒)"]["state"] == "resolved" and refs["ข้อ ๔(๒)"]["to_node"] == n42["node_key"]
    assert refs["วรรคหนึ่ง"]["to_node"] == by["ข้อ:4/วรรค:1"]["node_key"]
    # Thai and ASCII digits share one key; the reference keeps its spelling
    nodes = b["nodes"]
    for spelled in ("ตามข้อ ๔(๒)", "ตามข้อ 4(2)"):
        (ref,) = S.parse_references(spelled)
        assert ref.key == "ข้อ:4(2)" and ref.text == spelled[3:]
        res = S.resolve_in_version(nodes, ref)
        assert res["state"] == "resolved" and res["targets"][0]["node_key"] == n42["node_key"]
    (r53,) = S.parse_references("ตามข้อ ๔(๓)")                     # no (๓): the enclosing numbered unit, lower confidence
    res = S.resolve_in_version(nodes, r53)
    assert res["state"] == "resolved_parent" and res["targets"][0]["section_path"] == "ข้อ:4" and res["confidence"] < 0.9
    assert S.parse_references("ข้อมูล ส่วนลด ข้อความ") == []          # words that merely start like a kind


def test_structure_ambiguity_external_instruments_and_plain_text_limits():
    text = "ข้อ ๓ ฉบับแรก\n\nข้อ ๓ ฉบับซ้ำ\n\nข้อ ๑ ให้ทำตามข้อ ๓\n"
    _prep, b = _build(text, "owner_text")
    (ref,) = [r for r in S.parse_references("ให้ทำตามข้อ ๓")]
    res = S.resolve_in_version(b["nodes"], ref)
    assert res["state"] == "ambiguous" and len(res["targets"]) == 2           # visible, never guessed
    (ext,) = S.parse_references("ตามมาตรา ๑๒ แห่งพระราชบัญญัติสิทธิบัตร พ.ศ. ๒๕๒๒")
    assert ext.external and ext.instrument == "พระราชบัญญัติสิทธิบัตร พ.ศ. ๒๕๒๒"
    (own,) = S.parse_references("ตามบัญชีท้ายประกาศนี้")
    assert own.annex_type and own.internal_marker and not own.external
    (en,) = S.parse_references("see Section 5 of the Patent Act 1999")
    assert en.external and en.instrument == "the Patent Act 1999"
    (en2,) = S.parse_references("under Annex B of this Regulation")
    assert en2.key == "annex:b" and not en2.external
    _prep, plain = _build("[^1]: not a footnote in plain text\n\n| a | b |\n|---|---|\n", "owner_text")
    assert not {n["kind"] for n in plain["nodes"]} & {"footnote", "table", "heading"}   # not exposed: not built


# =========================================================================== the key integration test
def test_acquired_passage_changes_the_committed_assessment_quote_is_exact_and_trace_survives_reload(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [TEMP_REQ])
    ingest(core, pid, "notice.md", NOTICE, sid="notice")
    with core.store.read() as con:
        assert core.structure.build_state(con, pid, "notice", "v1") == "built"   # persisted at import
    mission_before = C.dumps(core.project_view(pid)["mission"]["requirements"])
    base = core.run_comparison(pid, acquisition="baseline")
    b = cell(core, pid, "C1", "T1")
    assert b["outcome"] == "unknown" and b["citation"] is None
    (rb,) = receipts(base)
    assert rb["outcome"] == "baseline_no_action" and rb["search_calls"] == 0
    assert rb["gaps"] == ["unresolved_reference", "absent_bounded_field"]      # observed, but no action in baseline
    run = core.run_comparison(pid)                                             # default: structural
    a = cell(core, pid, "C1", "T1")
    assert a["outcome"] == "meets" and a["supersedes_id"] == b["assessment_id"]
    (rec,) = receipts(run)
    assert rec["action"] == "resolve_reference" and rec["outcome"] == "acquired"
    assert rec["policy_version"] == R.POLICY_V2_1.name and rec["policy_sha256"] == R.POLICY_V2_1_SHA256   # D25
    assert rec["query"] == "structural lookup: 'ข้อ ๔(๒)' -> notice@v1#ข้อ:4(2)"
    assert rec["anchors"][0]["text"] == "ข้อ ๔(๒)"
    text = core.source_version(pid, "notice", "v1")["text"]
    an = rec["anchors"][0]
    assert text[an["start"]:an["end"]] == "ข้อ ๔(๒)"
    assert rec["scope"] == {"project_id": pid, "candidate_id": "C1", "source_id": "notice", "version_id": "v1"}
    cited = f"notice@v1#{a['citation']['passage_id']}"
    assert rec["new_unit_ids"] == [cited] and rec["same_document_unit_ids"] == [cited] and rec["new_document_ids"] == []
    assert rec["gain"]["same_document_context_units"] == 1 and rec["gain"]["new_document_units"] == 0
    assert quote_is_exact(core, pid, a["citation"])
    assert "Supported temperature range: 5 to 60 °C." in text[a["citation"]["start_char"]:a["citation"]["end_char"]]
    assert "acquired after the seed search" in a["explanation"]
    assert run["counters"]["structural_actions"] == 1 and rec["budget_after"]["used"] == 1      # one-action bound
    # original requirements unchanged
    assert C.dumps(core.project_view(pid)["mission"]["requirements"]) == mission_before
    assert rec["requirements"]["requirements"][0]["text"] == TEMP_REQ["query"]
    assert rec["requirement_sha256"] == core.requirement_sha256(core.project_view(pid)["mission"]["requirements"][0])
    # persisted receipt linked to the committed assessment, search-scope dependency recorded
    with core.store.read() as con:
        row = con.execute("SELECT * FROM acquisition_receipts WHERE run_id=?", (run["run_id"],)).fetchone()
        deps = {(d[0], d[1], d[2]) for d in con.execute("SELECT kind, source_id, version_id FROM dependencies WHERE "
                                                        "assessment_id=?", (a["assessment_id"],))}
    assert row["assessment_id"] == a["assessment_id"] and row["commit_status"] == "new_version"
    assert {("citation", "notice", "v1"), ("search_scope", "notice", "v1"), ("acquisition_scope", "notice", "v1")} <= deps
    # reload: a new process on the same data directory reads the same persisted trace
    again = Workflow(C.EvidenceCore(tmp_path / "store"))
    cmp_ = again.compare(pid, {"run": False})
    (tr,) = cmp_["requirements"][0]["acquisition"]
    assert tr["matches_current_assessment"] and tr["integrity"] == "verified"
    assert tr["receipt_sha256"] == row["receipt_sha256"] == hashlib.sha256(
        C.dumps(tr["receipt"]).encode("utf-8")).hexdigest()
    assert tr["new_units"][0]["unit_id"] == cited and tr["new_units"][0]["gain"] == "same_document"
    assert tr["new_units"][0]["quote"] == text[tr["new_units"][0]["start_char"]:tr["new_units"][0]["end_char"]]
    assert cmp_["run"] is None and cmp_["counters_source"] == "no run in this request"


def test_real_import_without_references_takes_no_structural_action(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [{"requirement_id": "M1", "label": "replaceable heat-sink module"}])
    ingest(core, pid, "plain.md", PLAIN, sid="plain")
    with core.store.read() as con:
        nodes = core.structure.nodes(con, pid, "plain", "v1")
        build = core.structure.summary(con, pid, "plain", "v1")
    assert {n["kind"] for n in nodes} == {"heading"} and build["detail"]["exposed"]["geometry"] is False
    base = core.run_comparison(pid, acquisition="baseline")
    b = cell(core, pid, "C1", "M1")
    run = core.run_comparison(pid)
    (rec,) = receipts(run)
    assert rec["outcome"] == "no_gap" and rec["search_calls"] == 0 and rec["gaps"] == []
    a = cell(core, pid, "C1", "M1")
    assert a["assessment_id"] == b["assessment_id"] and a["outcome"] == "evidence_found"     # identical to baseline
    assert receipts(base)[0]["final_ids"] == rec["final_ids"]


def test_missing_requirement_is_searched_within_the_same_instrument_without_any_reference(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [ELIG_REQ, FEE_REQ])
    ingest(core, pid, "fees.md", FEES, sid="fees")
    core.run_comparison(pid, acquisition="baseline")
    assert cell(core, pid, "C1", "F1")["outcome"] == "unknown"
    run = core.run_comparison(pid)
    (rec,) = receipts(run, rid="F1")
    assert rec["gaps"] == ["no_hit"] and rec["action"] == "search_within_source"
    # policy 2.1.0 (D25): the anchor is E1's current seed unit, not E1's stored citation
    assert rec["anchors"][0]["kind"] == "sibling_seed_unit" and rec["anchors"][0]["requirement_id"] == "E1"
    assert rec["policy_version"] == "ptp-structural-acquisition/2.1.0"
    assert rec["scope"]["source_id"] == "fees" and rec["index_generation"].startswith("passage_fts_th_v1:")
    f1 = cell(core, pid, "C1", "F1")
    assert f1["outcome"] == "evidence_found" and "does not judge" in f1["explanation"]       # never a verdict
    text = core.source_version(pid, "fees", "v1")["text"]
    assert "ค่าธรรมเนียม" in text[f1["citation"]["start_char"]:f1["citation"]["end_char"]]
    assert quote_is_exact(core, pid, f1["citation"])
    (e1,) = receipts(run, rid="E1")
    assert e1["outcome"] == "no_gap" and cell(core, pid, "C1", "E1")["outcome"] == "evidence_found"


def test_policy_2_0_0_stays_selectable_and_keeps_its_stored_citation_anchor(tmp_path, thai):
    """D25 keeps 2.0.0 for reproduction only: on explicit request it still anchors on the stored sibling citation."""
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [ELIG_REQ, FEE_REQ])
    ingest(core, pid, "fees.md", FEES, sid="fees")
    core.run_comparison(pid, acquisition="baseline")             # E1's citation now exists in the store
    run = core.run_comparison(pid, acquisition={"policy": R.POLICY_V2.name})
    (rec,) = receipts(run, rid="F1")
    assert rec["policy_version"] == R.POLICY_V2.name and rec["policy_sha256"] == R.POLICY_V2_SHA256
    assert rec["anchors"][0]["kind"] == "sibling_citation" and rec["anchors"][0]["requirement_id"] == "E1"
    assert run["counters"]["acquisition_policy"] == R.POLICY_V2.name
    assert "sibling_seed_searches" not in run["counters"]       # 2.0.0 never runs the S1a sibling seeds


def test_scope_isolation_another_candidates_document_never_satisfies_this_requirement(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [FEE_REQ], candidates=(("C1", "Company one"), ("C2", "Company two")))
    ingest(core, pid, "main.md", "# หลัก\n\nข้อ ๑ ผู้ยื่นคำขอต้องเป็นนิติบุคคล\n", "C1", "main")
    ingest(core, pid, "fees.md", "# ค่าธรรมเนียม\n\nค่าธรรมเนียมคำขอรายปี ๑,๐๐๐ บาท\n", "C1", "fees")
    ingest(core, pid, "other.md", "# อีกบริษัท\n\nอัตราค่าธรรมเนียมรายปี ๒,๐๐๐ บาท\n", "C2", "other")
    run = core.run_comparison(pid)
    (r1,) = receipts(run, cand="C1")
    assert r1["action"] == "search_eligible_corpus" and r1["gaps"] == ["no_hit"]
    assert sorted(r1["eligible_scope"]) == ["fees@v1", "main@v1"]
    assert "other@v1" in r1["eligibility"]["exclude_groups"]
    every = r1["new_unit_ids"] + r1["final_ids"] + [x["unit_id"] for x in r1["backend_ranked"]]
    assert every and all(not u.startswith("other@") for u in every)
    assert set(r1["new_document_ids"]) <= {"fees", "main"}
    c1 = cell(core, pid, "C1", "F1")
    assert c1["citation"]["source_id"] == "fees" and quote_is_exact(core, pid, c1["citation"])
    (r2,) = receipts(run, cand="C2")
    assert r2["eligible_scope"] == ["other@v1"]
    c2 = cell(core, pid, "C2", "F1")
    assert c2 is None or c2["citation"] is None or c2["citation"]["source_id"] == "other"
    # the commit boundary refuses a foreign citation even if a route ever produced one
    with core.store.read() as con:
        p = con.execute("SELECT p.*, v.sha256 FROM passages p JOIN source_versions v USING (project_id, source_id, "
                        "version_id) WHERE p.project_id=? AND p.source_id='other'", (pid,)).fetchone()
    cit = {k: p[k] for k in ("source_id", "version_id", "passage_id", "start_char", "end_char", "quote", "sha256")}
    mission = core.project_view(pid)["mission"]
    with pytest.raises(C.ValidationFailed) as e:
        core._commit(pid, run["run_id"], mission, "C1", mission["requirements"][0], "evidence_found", "x", None, [],
                     [], [], cit)
    assert e.value.code == "citation_candidate_scope"


def test_source_and_version_disambiguation_with_thai_digits(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [TEMP_REQ])
    other = NOTICE.replace("อุณหภูมิใช้งานของเครื่องต้องเป็นไปตาม", "ความชื้นต้องเป็นไปตาม").replace(
        "5 to 60 °C.", "30 to 40 °C.")
    ingest(core, pid, "b.md", other, sid="b-notice")                 # same clause numbers, another instrument
    ingest(core, pid, "a.md", NOTICE.replace("ข้อ ๔(๒)", "ข้อ 4(2)"), sid="a-notice")   # ASCII digits in the reference
    core.run_comparison(pid)
    c = cell(core, pid, "C1", "T1")
    assert c["outcome"] == "meets" and c["citation"]["source_id"] == "a-notice"   # never b-notice's ข้อ ๔(๒)
    v2 = NOTICE.replace("ข้อ ๔(๒)", "ข้อ 4(2)").replace("5 to 60 °C.", "20 to 40 °C.")
    out = ingest(core, pid, "a.md", v2, sid="a-notice")
    assert out["version_id"] == "v2" and "C1/T1" in out["result"]["reacquired"]
    c2 = cell(core, pid, "C1", "T1")
    assert c2["outcome"] == "does_not_meet" and (c2["citation"]["source_id"], c2["citation"]["version_id"]) == \
        ("a-notice", "v2")
    rec = core.acquisition.receipts(pid, "C1", "T1")[0]["receipt"]
    assert rec["new_unit_ids"][0].startswith("a-notice@v2#") and "a-notice@v1" not in C.dumps(rec["final_ids"])
    with core.store.read() as con:   # each version keeps its own persisted structure
        assert core.structure.build_state(con, pid, "a-notice", "v1") == "built"
        assert core.structure.build_state(con, pid, "a-notice", "v2") == "built"


def test_external_instrument_stays_unresolved_until_an_eligible_source_identifies_it(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [TEMP_REQ])
    ingest(core, pid, "notice.md", "# ประกาศทดสอบ\n\nข้อ ๑ อุณหภูมิใช้งานของเครื่องให้เป็นไปตามมาตรา ๑๒ "
                                   "แห่งพระราชบัญญัติเครื่องทดสอบ พ.ศ. ๒๕๖๐\n", sid="notice")
    run = core.run_comparison(pid)
    (rec,) = receipts(run)
    ref = next(c for c in rec["selection"]["candidates"] if c["action"] == "resolve_reference")
    assert ref["state"] == "external_unidentified" and not ref["actionable"]          # visible, not guessed
    assert rec["action"] == "search_within_source" and cell(core, pid, "C1", "T1")["outcome"] == "unknown"
    out = ingest(core, pid, "act.md", "# พระราชบัญญัติเครื่องทดสอบ พ.ศ. ๒๕๖๐\n\nมาตรา ๑๒ ช่วงอุณหภูมิของเครื่อง\n"
                                      "Supported temperature range: 0 to 70 °C.\n", sid="act")
    assert "C1/T1" in out["result"]["reacquired"]
    c = cell(core, pid, "C1", "T1")
    assert c["outcome"] == "meets" and c["citation"]["source_id"] == "act"
    rec2 = core.acquisition.receipts(pid, "C1", "T1")[0]["receipt"]
    assert rec2["action"] == "resolve_reference" and rec2["new_document_ids"] == ["act"]
    assert rec2["selection"]["candidates"][0]["target"][0]["rule"] == "external_instrument_title_v1"


def test_pdf_text_layer_import_resolves_annex_in_another_source_and_follows_its_revision(tmp_path, thai):
    pytest.importorskip("pypdf")
    from patent_to_pilot.workbench.trace_slice import FIXTURE_DIR
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [{"requirement_id": "S1", "label": "seaside sites"}])
    for name, sid in (("letter_v1.pdf", "letter"), ("annex_a_v1.pdf", "annex-a"), ("annex_b_v1.pdf", "annex-b")):
        ingest(core, pid, name, (FIXTURE_DIR / name).read_bytes(), sid=sid)
    with core.store.read() as con:
        b = core.structure.summary(con, pid, "letter", "v1")
        kinds = {n["kind"] for n in core.structure.nodes(con, pid, "letter", "v1")}
    assert b["source_kind"] == "owner_pdf" and b["detail"]["exposed"]["footnotes"] is False
    assert kinds == {"unit"}                         # 'Clause N.' lines only; the '[1]' marker is not a parsed footnote
    run = core.run_comparison(pid)
    (rec,) = receipts(run)
    assert rec["action"] == "resolve_reference" and rec["anchors"][0]["text"] == "Annex B"
    assert rec["new_unit_ids"] == ["annex-b@v1#p001-001"] and rec["new_document_ids"] == ["annex-b"]
    states = {c["anchors"][0]["text"]: c["state"] for c in rec["selection"]["candidates"]}
    assert states["Clause 4"] == "resolved_in_pool" and states["Annex A"] == "resolved"
    c = cell(core, pid, "C1", "S1")
    assert c["citation"]["source_id"] == "letter" and "annex-b@v1#p001-001" in c["explanation"]   # context, not cited
    out = ingest(core, pid, "annex_b_v2.pdf", (FIXTURE_DIR / "annex_b_v2.pdf").read_bytes(), sid="annex-b")
    assert "C1/S1" in out["result"]["reacquired"]     # rests on the action's scope: re-acquired, not reused
    rec2 = core.acquisition.receipts(pid, "C1", "S1")[0]["receipt"]
    assert rec2["new_unit_ids"] == ["annex-b@v2#p001-001"]


def test_declared_missing_item_date_scope_and_option_validation(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [ELIG_REQ, FEE_REQ])
    ingest(core, pid, "fees.md", FEES, sid="fees")
    ingest(core, pid, "old.md", "# เก่า\n\nอัตราค่าธรรมเนียมคำขอเดิม ฉบับละ ๑๐๐ บาท\n", sid="old")
    run = core.run_comparison(pid, acquisition={"declared_missing": [{"candidate_id": "C1", "requirement_id": "E1"}],
                                                "date_cutoff": "2026-01-01", "date_field": "effective",
                                                "source_dates": {"fees": {"effective": "2025-06-01",
                                                                          "publication": "2025-05-01"},
                                                                 "old": {"effective": "2027-01-01"}}})
    (e1,) = receipts(run, rid="E1")
    assert "user_declared_missing" in e1["gaps"] and e1["action"] == "search_within_source"
    assert e1["eligible_scope"] == ["fees@v1"] and e1["eligibility"]["date_cutoff"] == "2026-01-01"
    (f1,) = receipts(run, rid="F1")
    assert all(not u.startswith("old@") for u in f1["new_unit_ids"] + f1["final_ids"])
    setup = next(a for a in run["actions"] if a["action_type"] == "acquisition_setup")["detail"]
    assert setup["date_field"] == "effective" and setup["policy_sha256"] == R.POLICY_V2_1_SHA256
    assert setup["policy"] == R.POLICY_V2_1.name
    for bad, code in (({"mode": "wide"}, "bad_acquisition_mode"), ({"date_cutoff": "2026-01-01"}, "bad_acquisition_date"),
                      ({"policy": "ptp-relsel-first-unresolved/1.0.0"}, "bad_acquisition_policy"),
                      ({"declared_missing": [{"candidate_id": "C1", "requirement_id": "NOPE"}]}, "unknown_requirement"),
                      ({"surprise": 1}, "bad_acquisition")):
        with pytest.raises(C.ValidationFailed) as e:
            core.run_comparison(pid, acquisition=bad)
        assert e.value.code == code


# =========================================================================== lifecycle rules still hold
def test_archive_restore_and_stale_commit_rules_hold_with_acquisition_in_the_path(tmp_path, thai, monkeypatch):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [TEMP_REQ])
    ingest(core, pid, "notice.md", NOTICE, sid="notice")
    real = core.acquisition._execute
    fired = []

    def execute(*a, **k):
        if not fired:
            fired.append(1)
            core.archive_requirement(pid, "T1")          # removed while the action is in flight
        return real(*a, **k)
    monkeypatch.setattr(core.acquisition, "_execute", execute)
    run = core.run_comparison(pid)
    commit = next(a["detail"] for a in run["actions"] if a["action_type"] == "commit_assessment")
    assert fired and commit["committed"] == "rejected_stale" and "not active" in commit["reason"]
    (row,) = core.acquisition.receipts(pid, "C1", "T1")
    assert row["commit_status"] == "rejected_stale" and row["assessment_id"] is None
    assert cell(core, pid, "C1", "T1") is None
    monkeypatch.setattr(core.acquisition, "_execute", real)
    core.restore_requirement(pid, "T1")
    core.run_comparison(pid)
    c = cell(core, pid, "C1", "T1")
    assert c["outcome"] == "meets"
    out = core.archive_requirement(pid, "T1")
    assert out["retired_assessments"] == [c["assessment_id"]] and cell(core, pid, "C1", "T1") is None
    run3 = core.run_comparison(pid)
    assert receipts(run3) == [] and run3["counters"]["obligations_planned"] == 0
    assert core.restore_requirement(pid, "T1")["status"] == "restored"


# =========================================================================== provider dispatch and counters
class _EmbedDouble:
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
                    v = [0.01] + [0.0] * 15
                    for tok in re.findall(r"\w+", t.lower()):
                        v[1 + hashlib.sha256(tok.encode()).digest()[0] % 15] += 1.0
                    vecs.append(v)
                self._out({"embeddings": vecs, "prompt_eval_count": 1})
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.srv.shutdown()
        self.srv.server_close()


def test_provider_dispatch_is_measured_and_counters_are_propagated_not_hardcoded(tmp_path, thai, monkeypatch):
    core = C.EvidenceCore(tmp_path / "store")
    pid = project(core, [TEMP_REQ])
    ingest(core, pid, "notice.md", NOTICE, sid="notice")
    wf = Workflow(core)

    def no_dispatch(*_a, **_k):
        raise AssertionError("the lexical/local-only profile must not dispatch to any provider")
    monkeypatch.setattr(core.registry, "client", no_dispatch)
    lex = wf.compare(pid, {})
    assert lex["run"]["provider_dispatch"]["provider_requests"] == 0 and lex["paid_model_calls"] == 0
    assert lex["remote_calls"] == 0 and lex["counters_source"] == "run counters of this request's run"
    monkeypatch.undo()
    d = _EmbedDouble()
    try:
        core.registry.save({"profile_id": "emb", "role": "embedding", "adapter": "ollama", "model_id": "fake-embed",
                            "endpoint": d.url})
        assert core.registry.check("emb")["status"] == "ready"
        core.build_index(pid, "emb")
        core.set_retrieval_mode(pid, "hybrid")
        hyb = wf.compare(pid, {})
    finally:
        d.close()
    cnt = hyb["run"]["counters"]
    assert cnt["query_embeddings"] >= 1 and hyb["run"]["provider_dispatch"]["provider_requests"] >= cnt[
        "query_embeddings"]                                   # dispatch really happened and is reported
    assert hyb["paid_model_calls"] == cnt["paid_model_calls"] == 0 and hyb["remote_calls"] == cnt["remote_calls"] == 0
    assert cell(core, pid, "C1", "T1")["outcome"] == "meets"        # the action still runs in hybrid mode


# =========================================================================== HTTP: the UI reads the persisted trace
def test_compare_over_http_returns_the_persisted_trace_and_the_ui_renders_it(tmp_path, thai):
    core = C.EvidenceCore(tmp_path / "store")
    srv = create_server(core, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"

    def call(method, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(url + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"} if data else {})
        with urllib.request.urlopen(req) as r:
            return r.read()
    try:
        with loopback_only():
            pid = project(core, [TEMP_REQ])
            call("POST", f"/api/projects/{pid}/documents", {"filename": "notice.md", "candidate_id": "C1",
                                                             "content_base64": base64.b64encode(
                                                                 NOTICE.encode()).decode()})
            base = json.loads(call("POST", f"/api/projects/{pid}/compare", {"acquisition": "baseline"}))
            assert base["requirements"][0]["acquisition"][0]["mode"] == "baseline"
            r = json.loads(call("POST", f"/api/projects/{pid}/compare", {}))
            (tr,) = r["requirements"][0]["acquisition"]
            assert tr["outcome"] == "acquired" and tr["matches_current_assessment"] and tr["mode"] == "structural"
            assert r["requirements"][0]["assessments"][0]["cell"]["outcome"] == "meets"
            assert "side_by_side" not in r["requirements"][0]
            assert r["acquisition_policy"] == {"name": R.POLICY_V2_1.name, "sha256": R.POLICY_V2_1_SHA256}
            js = call("GET", "/app.js")
            html = call("GET", "/")
            assert b"acquisitionTrace" in js and b"compare-baseline" in js and b'id="compare-baseline"' in html
            sid, vid = "notice", "v1"
            text = core.source_version(pid, sid, vid)["text"]
            s = text.index("(๒) ช่วงอุณหภูมิ")
            x = json.loads(call("GET", f"/api/projects/{pid}/sources/{sid}/versions/{vid}/spans/{s}/{s + 5}"))
            assert any(n["section_path"] == "ข้อ:4(2)" for n in x["structure"]["nodes"])
            assert x["structure"]["build"]["ruleset"] == S.RULESET
    finally:
        srv.shutdown()
        srv.server_close()
