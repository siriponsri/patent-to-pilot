"""Product-only, authored cases. These exercise behavior and contain no research labels."""
from contextlib import contextmanager
from copy import deepcopy
import json
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from patent_to_pilot.workbench import scope_reader as sr
from patent_to_pilot.workbench.core import Conflict, EvidenceCore, sha256
from patent_to_pilot.workbench.server import create_server


def exhibit():
    rows = [
        ("a", "Claim 1", "A loop comprises a copper ring.", "ห่วงมีวงแหวนทองแดง"),
        ("b", "Claim 2", "The loop of claim 1 uses a narrow hinge.", "ห่วงตามข้อถือสิทธิ 1 เพิ่มบานพับแคบ"),
        ("c", "Example A", "A steel clamp in Example A.", "ตัวอย่าง A ใช้ตัวหนีบเหล็ก"),
        ("d", "Table 1", "Table 1 refers to Example A.", "ตารางที่ 1 อ้างถึงตัวอย่าง A"),
    ]
    units = [{"id": uid, "locator": loc, "quote": text, "meaning_th": gloss,
              "kind": "claim" if uid in ("a", "b") else "description"} for uid, loc, text, gloss in rows]
    units[1]["parent"] = "Claim 1"
    units[2]["example"] = "Example A"
    units[3]["references"] = ["Example A"]
    return {"id": "old", "family_id": "fiction", "title_th": "ตัวอย่างสมมติ", "question_th": "ข้อใดเพิ่มขึ้น",
            "domain": "patent", "source_id": "device", "version": "v1", "source_url": "https://example.org/document",
            "text": "\n".join(u["quote"] for u in units), "rights": {"quote": True, "export_quote": True},
            "units": units, "requirements": [
                {"id": "base", "label_th": "ต้นทาง", "locator": "Claim 1", "query": "copper"},
                {"id": "child", "label_th": "ข้อสืบทอด", "locator": "Claim 2", "parent": "Claim 1", "query": "hinge"},
            ]}


def test_keep_exact_unicode_offsets_parent_reference_and_no_invented_geometry():
    entry = exhibit()
    entry["requirements"].extend([
        {"id": "tab", "locator": "Table 1", "query": "Table", "label_th": "ตาราง"},
        {"id": "row", "locator": "Example A", "query": "steel", "example": "Example A", "label_th": "ตัวอย่าง"},
    ])
    trace = sr._evaluate(entry, 0)
    assert trace["status"] == "complete"
    assert {a["action"] for a in trace["actions"]} == {"keep"}
    assert trace["budget"]["used"] == 0
    stated = [(e["from"], e["to"], e["evidence_id"]) for e in trace["edges"] if e["type"] == "stated"]
    assert stated == [("device@v1#b", "device@v1#a", "device@v1#b"), ("device@v1#d", "device@v1#c", "device@v1#d")]
    for ev in trace["evidence"]:
        assert entry["text"][ev["start"]:ev["end"]] == ev["quote"]
        assert sha256(ev["quote"].encode()) == ev["quote_sha256"]
        assert "coordinates" not in ev and "cell" not in ev


def test_rerank_existing_match_acquire_missing_match_and_stop_when_budget_spent():
    entry = exhibit()
    # Two lexical hits for "loop". Both occur once; the shorter first claim ranks higher.
    entry["requirements"][1]["query"] = "loop"
    entry["requirements"].append({"id": "offpool", "locator": "Example A", "query": "copper", "label_th": "ตัวอย่าง A"})
    trace = sr._evaluate(entry, 2)
    assert [a["action"] for a in trace["actions"]] == ["keep", "rerank", "acquire"]
    assert trace["actions"][1]["before"] == trace["actions"][1]["after"][::-1]
    assert trace["actions"][2]["accepted"] == ["device@v1#c"]
    assert trace["budget"]["used"] == 2
    partial = sr._evaluate(entry, 0)
    assert partial["status"] == "qualified"
    assert [r["status"] for r in partial["requirements"]] == ["bound", "unresolved", "unresolved"]
    assert [e["id"] for e in partial["evidence"]] == ["device@v1#a"]


def test_missing_date_wrong_example_and_ambiguous_locator_cannot_assert():
    entry = exhibit()
    entry["requirements"] = [
        {"id": "date", "label_th": "วันมีผล", "locator": "Claim 1", "date": "2020-01-01", "query": "copper"},
        {"id": "wrong", "label_th": "ตัวอย่าง B", "locator": "Example A", "example": "Example B", "query": "steel"},
        {"id": "ambiguous", "label_th": "ข้อถือสิทธิ", "locator": "Claim 2", "query": "hinge"},
    ]
    entry["issue_date"] = "2020-01-01"
    entry["units"][3]["locator"] = "Claim 2"
    trace = sr._evaluate(entry, 4)
    assert trace["status"] == "qualified" and not trace["evidence"]
    assert trace["effective_date"] is None and trace["budget"]["used"] == 2


def test_restricted_export_and_unverifiable_reference():
    entry = exhibit()
    entry["rights"]["export_quote"] = False
    entry["units"][1]["references"] = ["Claim 10"]
    trace = sr._evaluate(entry, 0)
    assert trace["status"] == "qualified" and trace["unresolved_relations"]
    for unit in trace["evidence"]:
        assert unit["quote"] is None and unit["meaning_th"] is None
        assert unit["sha256"] and unit["start"] >= 0
    assert entry["units"][0]["quote"] not in json.dumps(trace, ensure_ascii=False)


@contextmanager
def serving(data_dir):
    server = create_server(EvidenceCore(data_dir), port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def request(url, path, body=None):
    payload = json.dumps(body).encode() if body is not None else None
    req = Request(url + path, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=5) as response:
        return json.load(response)


def test_http_restart_and_amended_edition_replay_original_citations(tmp_path, monkeypatch):
    source = tmp_path / "bundle.json"
    monkeypatch.setattr(sr, "BUNDLE", source)
    old = exhibit()
    old.update(source_id="thai-act", version="old", domain="law", question_th="มาตรา ๙ กำหนดอะไร")
    old["text"] = "มาตรา ๙ ให้แจ้งทางจดหมาย\nมาตรา ๑๐ ระบุตัวบุคคล"
    old["units"] = [{"id": str(i), "locator": loc, "kind": "section", "quote": text, "meaning_th": text}
                    for i, (loc, text) in enumerate(zip(["มาตรา ๙", "มาตรา ๑๐"], old["text"].splitlines()))]
    old["requirements"] = [{"id": str(i), "label_th": loc, "locator": loc, "query": loc}
                           for i, loc in enumerate(["มาตรา 9", "มาตรา 10"])]
    source.write_text(json.dumps({"examples": [old]}), encoding="utf-8")
    data_dir = tmp_path / "store"
    with serving(data_dir) as url:
        assert request(url, "/api/scope/catalog")["examples"][0]["id"] == "old"
        for invalid in ({"budget": True}, {"budget": 5}, {"question_th": "คนละคำถาม"}, {"gold": "secret"}):
            with pytest.raises(HTTPError) as err:
                request(url, "/api/scope/run", {"example_id": "old", **invalid})
            assert err.value.code == 400
        first = request(url, "/api/scope/run", {"example_id": "old"})
        assert first["status"] == "complete"
    newer = deepcopy(old)
    newer.update(id="amendment", version="new")
    newer["text"] = newer["text"].replace("จดหมาย", "อีเมล")
    newer["units"][0].update(quote=newer["text"].splitlines()[0], meaning_th="ให้แจ้งทางอีเมล")
    source.write_text(json.dumps({"examples": [newer]}), encoding="utf-8")
    with serving(data_dir) as url:
        assert request(url, "/api/scope/run/" + first["id"]) == first
        second = request(url, "/api/scope/run", {"example_id": "amendment"})
        assert first["source_sha256"] != second["source_sha256"]
        for i, stable in enumerate((False, True)):
            prior, later = first["evidence"][i], second["evidence"][i]
            assert (prior["quote_sha256"] == later["quote_sha256"]) == stable
            assert newer["text"][later["start"]:later["end"]] == later["quote"]
        assert len(request(url, "/api/scope/catalog")["runs"]) == 2
        newer["version"] = "old"
        source.write_text(json.dumps({"examples": [newer]}), encoding="utf-8")
        with pytest.raises(HTTPError) as err:
            request(url, "/api/scope/run", {"example_id": "amendment"})
        assert err.value.code == 409
        with pytest.raises(HTTPError) as err:
            request(url, "/api/scope/run/missing")
        assert err.value.code == 404


def test_bad_offsets_fail_before_any_trace():
    entry = exhibit()
    entry["units"][0]["start"] = 1
    with pytest.raises(Conflict, match="excerpt"):
        sr._evaluate(entry, 4)


def test_reference_boundaries_follow_thai_provision_numbers_and_english_words():
    assert sr._mentions("ภายใต้บังคับมาตรา ๕๖การโฆษณา", "มาตรา 56")
    assert sr._mentions("ตามมาตรา๕๖/๑ให้ดำเนินการ", "มาตรา 56/1")
    for longer in ("มาตรา ๕๖๐", "มาตรา๕๖/๑", "มาตรา 56 / 1", "มาตรา ๕๖ ทวิ", "มาตรา ๕๖ตรี"):
        assert not sr._mentions(longer, "มาตรา ๕๖")
    assert sr._mentions("according to claim 2, the lid", "Claim 2")
    assert not sr._mentions("reclaim 2", "Claim 2")
    assert not sr._mentions("claim 22", "Claim 2")


def test_public_examples_through_http_persist_attribution_and_exact_source(tmp_path):
    entries = {e["id"]: e for e in json.loads(sr.BUNDLE.read_text(encoding="utf-8-sig"))["examples"]}
    with serving(tmp_path) as url:
        traces = {e["id"]: request(url, "/api/scope/run", {"example_id": e["id"]})
                  for e in request(url, "/api/scope/catalog")["examples"]}
    assert set(traces) >= {"eta-2544", "eta-2562-no3", "eta-case", "paperclip-3", "paperclip-4"}
    with serving(tmp_path) as url:
        for eid, t in traces.items():
            e = entries[eid]
            assert t == request(url, "/api/scope/run/" + t["id"])
            assert t["contract"] == sr.CONTRACT and t["data_origin"] == "public_source"
            assert t["source_sha256"] == e["canonical_sha256"]
            assert t["originals"] and all(original["url"].startswith("https://") and len(original["sha256"]) == 64
                                          for original in t["originals"])
            for ev in t["evidence"]:
                assert e["text"][ev["start"]:ev["end"]] == ev["quote"]
                assert ev["sha256"] == t["source_sha256"] and ev["version"] == e["version"]

    old, amended = traces["eta-2544"], traces["eta-2562-no3"]
    assert old["status"] == amended["status"] == "complete" and old["version"] != amended["version"]
    def by_requirement(trace):
        evidence = {e["id"]: e for e in trace["evidence"]}
        return {r["id"]: evidence[r["evidence_id"]] for r in trace["requirements"] if r["evidence_id"]}
    before, after = by_requirement(old), by_requirement(amended)
    assert before["identity"]["quote_sha256"] == after["identity"]["quote_sha256"]
    assert before["message"]["quote_sha256"] != after["message"]["quote_sha256"]
    assert [r["status"] for r in traces["eta-case"]["requirements"]] == ["bound", "unresolved"]
    claim3, claim4 = (by_requirement(traces[name]) for name in ("paperclip-3", "paperclip-4"))
    assert claim3["base"]["id"] == claim4["base"]["id"]
    assert claim3["material"]["id"] != claim4["material"]["id"]
    for name in ("paperclip-3", "paperclip-4"):
        assert traces[name]["status"] == "complete"
        assert any(edge["type"] == "stated" for edge in traces[name]["edges"])
