"""RA Pharma dossier: evidence roles, snapshots, letters and the skill correction loop.

The fixtures are the shipped fictional pack. Each test states the behaviour from the
evidence contract (docs/ra-pharma/EVIDENCE-CONTRACT.md) that it protects.
"""
import builtins
import io
import shutil
import zipfile

import pytest

pytest.importorskip("pypdf")

from patent_to_pilot.workbench import dossier as D  # noqa: E402
from patent_to_pilot.workbench import letters as L  # noqa: E402
from patent_to_pilot.workbench.core import Conflict, CoreError  # noqa: E402
from patent_to_pilot.workbench.store import Store  # noqa: E402

REPORT_10, REPORT_11 = "applicant-dissolution-report-1.0", "applicant-dissolution-report-1.1"


@pytest.fixture()
def svc(tmp_path):
    return D.DossierService(Store(tmp_path / "store"))


def item(snap, item_id):
    return next(i for i in snap["items"] if i["item_id"] == item_id)


def promote_corrected_skill(svc):
    v1 = svc.build({})
    res = item(v1, "reg.R-P54.applicant-result")
    corr = svc.correct({"snapshot_id": v1["snapshot_id"], "item_id": res["item_id"],
                        "passage_id": "US20120276199A1#example-6", "to_role": "patent_disclosure"})
    spec = svc.propose({"correction_id": corr["id"]})["spec"]
    evaluation = svc.evaluate({"version": spec["version"]})
    svc.promote({"version": spec["version"]})
    return v1, spec, evaluation


def letter_text(snap):
    return "\n".join(b["text"] for b in snap["letter"])


def test_pack_pins_sources_and_rejects_changed_bytes(tmp_path):
    pack = D.load_pack()
    assert {s["source_id"] for s in pack["sources"]} >= {"US20120276199A1", "TH-FDA-ACTR-ACTD-Q-2550", "TH-OPM-SARABAN-2526"}
    assert all(len(d["sha256"]) == 64 for d in pack["documents"])
    copy = tmp_path / "pack"
    shutil.copytree(D.PACK_DIR, copy)
    target = copy / "docs" / "incoming-authority-rfi.pdf"
    target.write_bytes(target.read_bytes() + b"\n%changed")
    with pytest.raises(Conflict) as exc:
        D.load_pack(copy)
    assert exc.value.code == "invalid_pack"


def test_authority_letter_layout_emblem_and_uncertain_readings():
    data = (D.PACK_DIR / "docs" / "incoming-authority-rfi.pdf").read_bytes()
    letter = L.read_letter(data)
    assert letter["document_type"] == "authority_external_letter"
    assert letter["sender"]["kind"] == "authority"
    assert letter["fields"]["number"]["value"] == "ตย ๐๓๑๒/๒๕๖๙"
    assert letter["fields"]["date"]["iso"] == "2026-11-12"
    assert letter["fields"]["subject"]["value"].endswith("เฟโซแคร์ โอดีที ๓๐ มก.")
    assert [r["number"] for r in letter["requests"]] == [1, 2]
    emblem = letter["emblem"]
    assert emblem["position"] == "top_center" and emblem["matches_opm_garuda_layout"]
    assert abs(emblem["height_cm"] - 3.0) < 0.05
    # Layout matching does not identify the picture, and an unsigned copy stays uncertain.
    assert {"emblem_identity", "signature_image", "enclosures"} <= set(letter["uncertain"])


def test_company_letter_is_not_read_as_an_authority_letter():
    letter = L.read_letter((D.PACK_DIR / "docs" / "incoming-licensor-request.pdf").read_bytes())
    assert letter["document_type"] == "company_letter"
    assert letter["sender"]["kind"] == "company"
    assert letter["emblem"]["position"] == "top_left" and not letter["emblem"]["matches_opm_garuda_layout"]
    assert letter["requests"] == []


def test_template_follows_the_actual_sender():
    templates = D.load_pack()["templates"]
    company = L.select_template(templates, "company", "authority")
    assert company["template"]["template_id"] == "company-letterhead-to-authority"
    assert company["template"]["emblem"] is None
    assert any(r["template_id"] == "opm-external-garuda" for r in company["rejected"])
    assert L.select_template(templates, "company", "company")["template"]["template_id"] == "company-letterhead-business"
    assert L.select_template(templates, "authority", "company")["template"]["template_id"] == "opm-external-garuda"


def test_patent_example_cannot_fill_the_missing_applicant_report(svc):
    promote_corrected_skill(svc)
    before = svc.build({})
    example = item(before, "patent.example-6")
    result = item(before, "reg.R-P54.applicant-result")
    assert example["status"] == "supported" and example["evidence_role"] == "patent_disclosure"
    assert result["status"] == "missing" and result["value"] is None
    rejected = result["candidates"][0]
    assert rejected["passage_id"] == "US20120276199A1#example-6" and not rejected["accepted"]
    assert rejected["role"] == "patent_disclosure"
    text = letter_text(before)
    assert "96" not in text and "US2012" not in text   # the reply carries only what concerns the addressee
    assert "อยู่ระหว่างจัดทำรายงาน" in text

    after = svc.build({"attachments": [REPORT_10]})
    result = item(after, "reg.R-P54.applicant-result")
    assert result["status"] == "supported" and result["value"] == "91"
    ref = result["sources"][0]
    assert ref["source_id"] == REPORT_10 and ref["page"] == 2 and ref["kind"] == "applicant_document"
    assert item(after, "patent.example-6")["content_sha256"] == example["content_sha256"]
    diff = svc.diff(before["snapshot_id"], after["snapshot_id"])
    assert [c["item_id"] for c in diff["changed_items"]] == ["reg.R-P54.applicant-result"]
    assert "req-1" in {c["block_id"] for c in diff["letter_changes"]}

    # Reopen both snapshots: historical values and citations still resolve.
    for snap, value in ((before, None), (after, "91")):
        again = svc.snapshot(snap["snapshot_id"])
        assert item(again, "reg.R-P54.applicant-result")["value"] == value
        check = svc.verify(snap["snapshot_id"])
        assert check["citations_ok"] and check["rebuild_matches"]
    page = svc.page(after["snapshot_id"], "reg.R-P54.applicant-result", 0)
    assert page["verified"] and page["open_url"].endswith("#page=2")
    assert "30 นาที" in page["page_text"][ref["start"]:ref["end"]]


def test_claim_branch_change_leaves_the_applicant_assertion_unchanged(svc):
    promote_corrected_skill(svc)
    a = svc.build({"attachments": [REPORT_10], "claim_branch": "15"})
    b = svc.build({"attachments": [REPORT_10], "claim_branch": "18"})
    assert a["branch_status"] == "needs_review" and b["branch_status"] == "does_not_meet"
    diff = svc.diff(a["snapshot_id"], b["snapshot_id"])
    assert "reg.R-P54.applicant-result" in diff["unchanged_items"]
    assert all(c["item_id"].startswith("patent.") for c in diff["changed_items"])
    assert diff["letter_changes"] == []
    fto = item(b, "patent.fto-th")
    assert fto["status"] == "needs_review" and fto["jurisdiction"] == "TH" and fto["missing"]


def test_conflicting_report_editions_block_the_sentence_until_the_operator_chooses(svc):
    promote_corrected_skill(svc)
    both = [REPORT_10, REPORT_11]
    conflict = svc.build({"attachments": both})
    result = item(conflict, "reg.R-P54.applicant-result")
    assert result["status"] == "conflict" and result["value"] is None
    assert [(c["edition"], c["value"]) for c in result["conflict"]] == [("1.0", "91"), ("1.1", "89")]
    block = next(b for b in conflict["letter"] if b["block_id"] == "req-1")
    assert block.get("blocking") and "ต้องเลือกฉบับ" in block["text"]
    chosen = svc.build({"attachments": both, "edition_choice": {"QC-DIS-0459": "1.1"}})
    result = item(chosen, "reg.R-P54.applicant-result")
    assert result["status"] == "supported" and result["value"] == "89"
    assert any(a["kind"] == "operator" for a in chosen["actions"])
    assert "ร้อยละ 89" in letter_text(chosen) and "ฉบับที่ 1.1" in letter_text(chosen)


def test_missing_attachment_stays_listed_after_the_report_arrives(svc):
    promote_corrected_skill(svc)
    snap = svc.build({"attachments": [REPORT_11]})
    coa = item(snap, "reg.R-COA.attachment")
    assert coa["status"] == "missing" and "Certificate of Analysis" in coa["missing"][0]
    req2 = next(b for b in snap["letter"] if b["block_id"] == "req-2")
    assert req2["needs_signer"] and "reg.R-COA.attachment" in req2["item_ids"]


def test_skill_correction_is_versioned_tested_on_a_separate_family_and_replayable(svc):
    v1, spec, evaluation = promote_corrected_skill(svc)
    wrong = item(v1, "reg.R-P54.applicant-result")
    assert wrong["status"] == "supported" and wrong["value"] == "96"   # the error being corrected
    assert spec["version"] == "1.1.0" and spec["parent"] == "1.0.0"
    assert spec["accept"]["source_kinds"] == ["applicant_document"]
    assert evaluation["passed"] and evaluation["regressions"] == []
    assert evaluation["dev_family"] == "dev-inhaler-fpf"
    families = {c["family"] for c in evaluation["cases"]}
    assert families == {"dev-inhaler-fpf", "dossier-regression"}
    assert evaluation["parent_errors"] > 0 and evaluation["candidate_errors"] == 0
    assert svc.active_skill() == "1.1.0"
    # The previous version is retained and replays its original output.
    check = svc.verify(v1["snapshot_id"])
    assert check["skill_version"] == "1.0.0" and check["rebuild_matches"]
    assert item(svc.snapshot(v1["snapshot_id"]), "reg.R-P54.applicant-result")["value"] == "96"
    old = svc.build({"skill_version": "1.0.0"})
    assert item(old, "reg.R-P54.applicant-result")["value"] == "96"


def test_promotion_requires_a_passing_evaluation(svc):
    with pytest.raises(Conflict):
        svc.promote({"version": "1.0.0"})
    v1 = svc.build({})
    with pytest.raises(CoreError):
        svc.correct({"snapshot_id": v1["snapshot_id"], "item_id": "reg.R-P54.applicant-result",
                     "passage_id": "US20120276199A1#example-6", "to_role": "applicant_result"})


def test_runtime_never_reads_evaluator_labels():
    source = (D.PACK_DIR.parents[1] / "dossier.py").read_text(encoding="utf-8")
    assert "expected.json" not in source


def test_edited_letter_exports_an_editable_docx_with_embedded_font(svc):
    promote_corrected_skill(svc)
    snap = svc.build({"attachments": [REPORT_10]})
    rev = svc.save_letter(snap["snapshot_id"], {"blocks": [{"block_id": "number", "text": "ที่ SCP-RA 045/2569"}]})
    edited = next(b for b in rev["blocks"] if b["block_id"] == "number")
    assert edited["operator_edited"] and edited["original_text"].startswith("ที่ SCP-RA ……")
    data, media, _name = svc.export(snap["snapshot_id"], "docx")
    assert media.endswith("wordprocessingml.document")
    paragraphs = L.docx_text(data)
    assert "ที่ SCP-RA 045/2569" in paragraphs
    assert any("ร้อยละ 91" in p for p in paragraphs)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        font = z.read("word/fonts/font1.odttf")
        assert "w:embedRegular" in z.read("word/fontTable.xml").decode()
    plain = (L.FONTS / "Sarabun-Regular.ttf").read_bytes()
    assert font[32:] == plain[32:] and font[:32] != plain[:32]
    html = svc.export(snap["snapshot_id"], "html")[0].decode("utf-8")
    assert "ที่ SCP-RA 045/2569" in html and "<script" not in html


def test_reader_reports_a_missing_pdf_extra(monkeypatch):
    real = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "pypdf" or name.startswith("pypdf."):
            raise ImportError(name)
        return real(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(Conflict) as exc:
        L.read_layout(b"%PDF-1.4")
    assert exc.value.code == "pdf_reader_unavailable"


def test_company_incoming_letter_gets_a_company_reply_without_regulatory_detail(svc):
    snap = svc.build({"incoming_doc_id": "incoming-licensor-request", "attachments": [REPORT_10]})
    assert snap["incoming"]["document_type"] == "company_letter"
    assert snap["template"]["template"]["template_id"] == "company-letterhead-business"
    text = letter_text(snap)
    assert "เรียน  ผู้จัดการฝ่ายกฎหมาย" in text and "บริษัท ทีแอลเอ็กซ์" in text
    assert "ACTD" not in text and "96" not in text
    assert svc.verify(snap["snapshot_id"])["rebuild_matches"]
