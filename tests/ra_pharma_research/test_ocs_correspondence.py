from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/research/ra_pharma"))
from ocs_correspondence import ARMS, Document, binding, normal, run_query
from ocs_correspondence_score import evaluate


def test_header_requires_same_agency_and_reference_with_thai_digit_normalization():
    query = {"id": "q", "agency": "กรมทดสอบ", "reference": "ทด 12/44", "question": "ส่งคืนของได้หรือไม่"}
    assert binding(normal("กรมทดสอบได้มีหนังสือที่ ทด ๑๒/๔๔"), query)
    assert not binding(normal("กรมอื่นได้มีหนังสือที่ ทด ๑๒/๔๔"), query)
    assert not binding(normal("กรมทดสอบได้มีหนังสือที่ ทด ๑๒/๔๔๕"), query)


def test_dispositive_extract_must_be_read_and_bind_to_the_independent_issue():
    query = {"id": "q", "agency": "กรมทดสอบ", "reference": "ทด 12/44", "question": "ส่งคืนกระถางได้หรือไม่"}
    pages = ["เรื่องเสร็จที่ 9/2560 กรมทดสอบมีหนังสือที่ ทด 12/44 ถามว่าส่งคืนกระถางได้หรือไม่",
             "คณะกรรมการกฤษฎีกาได้พิจารณาแล้วเห็นว่า เจ้าหน้าที่ส่งคืนกระถางได้เมื่อทำทะเบียนครบถ้วน"]
    doc = Document.index("p", pages)
    key = [{"id": "q", "adjudication": "adjudicated", "request_provenance": "recited",
            "agency": query["agency"], "reference": query["reference"], "opinion": "9/2560",
            "source_case": "p", "requirements": [{"page": 2, "quote": "ส่งคืนกระถางได้เมื่อทำทะเบียนครบถ้วน"}]}]
    traces = {"q": {arm: run_query(query, [doc], arm) for arm in ARMS}}
    summary = evaluate({"traces": traces}, key, {"p": pages})
    assert all(metrics["complete"] == 1 for metrics in summary["totals"].values())
    key[0]["opinion"] = "10/2560"
    summary = evaluate({"traces": traces}, key, {"p": pages})
    assert all(metrics["unsupported_issued"] == 1 for metrics in summary["totals"].values())

def test_three_distinct_requirements_can_fit_in_two_returned_spans():
    first = "one-dispositive-fragment"
    second = "a-separate-qualification"
    third = "another-essential-qualifier"
    pages = [first + "." + second, third]
    identity = {"source": "p", "opinion": "9/2560", "agency": "a", "reference": "ref"}
    record = {"identity": identity, "status": "issued", "windows_ranked": 2,
              "actions": [{"source": "p", "page": n} for n in (1, 2)],
              "spans": [{"page": n, "start": 0, "end": len(page), "quote": page}
                        for n, page in enumerate(pages, 1)]}
    row = {"id": "q", "adjudication": "adjudicated", "request_provenance": "recited_in_opinion",
           "agency": "a", "reference": "ref", "opinion": "9/2560", "source_case": "p",
           "requirements": [{"page": 1, "quote": first}, {"page": 1, "quote": second},
                            {"page": 2, "quote": third}]}
    result = evaluate({"traces": {"q": {arm: record for arm in ARMS}}}, [row], {"p": pages})
    assert result["totals"]["exact_conflict"]["complete"] == 1


def test_adaptive_ranks_unopened_descriptors_without_accessing_page_text():
    query = {"id": "q", "agency": "กรมทดสอบ", "reference": "ทด 12/44", "question": "ลงทะเบียนกระถางอย่างไร"}
    doc = Document.index("p", [
        "เรื่องเสร็จที่ 9/2560 กรมทดสอบมีหนังสือที่ ทด 12/44 ถามเรื่องกระถาง",
        "คณะกรรมการกฤษฎีกาได้พิจารณาแล้วเห็นว่า " + "ต้องลงทะเบียนกระถางก่อนส่งคืน" * 16,
        "ดังนั้นให้ลงทะเบียนกระถางไว้เป็นหลักฐานก่อนส่งคืน" * 16,
        "แนวทางจัดรายการภาชนะหมายเลขเดิมและลงทะเบียน" * 16,
        "ข้อควรพิจารณาในการดำเนินการเกี่ยวกับรายการภาชนะ" * 16,
    ])
    observed = []
    pages = doc.pages

    class AuditPages:
        def __getitem__(self, offset):
            observed.append(offset + 1)
            return pages[offset]

    doc.pages = AuditPages()
    result = run_query(query, [doc], "adaptive_page")
    opened = {a["page"] for a in result["actions"]}
    assert set(observed) == opened and len(opened) == 3
    assert result["windows_ranked"] == sum(map(len, doc.windows.values()))
    assert set(doc.windows) - opened
