"""D8 (22 Nov 2026): PDF ingestion through the optional pypdf adapter (src/patent_to_pilot/workbench/ingest.py).

Hand-checkable fixtures: a two-page PDF is written byte by byte here (Helvetica text, correct xref offsets), so the test
needs no PDF generator beyond pypdf itself.
"""
from __future__ import annotations

import io

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench import ingest as I

pypdf = pytest.importorskip("pypdf")


def make_pdf(pages: list[list[str]]) -> bytes:
    """A minimal valid PDF; each page draws its lines top-down with Helvetica 12."""
    objs: list[bytes] = []
    n_pages = len(pages)
    page_ids = [3 + 2 * i for i in range(n_pages)]
    font_id = 3 + 2 * n_pages
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [" + b" ".join(f"{p} 0 R".encode() for p in page_ids)
                + f"] /Count {n_pages} >>".encode())
    for i, lines in enumerate(pages):
        ops = ["BT /F1 12 Tf 72 720 Td 16 TL"]
        for line in lines:
            esc = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"({esc}) Tj T*")
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {page_ids[i] + 1} 0 R "
                    f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>".encode())
        objs.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for k, body in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(f"{k} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


DOC = make_pdf([["Thermal concept C", "", "Powered circulation: no."],
                ["Supported temperature range: 35 to 75 C."]])


def test_capability_reports_pypdf_active():
    cap = I.pdf_capability()
    assert cap["state"] == "active" and cap["module"] == "pypdf" and cap["rule"] == "pdf_text_layer_v1"


def test_prepare_pdf_keeps_offsets_pages_and_provenance():
    prep = I.prepare("concept.pdf", DOC, C.extract_passages)
    text = prep["text"]
    assert prep["passage_rule"] == "pdf_text_layer_v1" and prep["source_kind"] == "owner_pdf"
    assert prep["stored_raw"] == text.encode("utf-8")
    assert text.startswith("[page 1]\n") and "[page 2]\n" in text
    assert prep["pdf"]["pages"] == 2 and len(prep["pdf"]["pdf_sha256"]) == 64
    for p in prep["passages"]:
        assert text[p["start_char"]:p["end_char"]] == p["quote"]
        assert not p["quote"].startswith("[page ")                 # markers are never passages
    pages = {p["page"] for p in prep["passages"]}
    assert pages == {1, 2}
    assert any("Powered circulation: no." in p["quote"] for p in prep["passages"] if p["page"] == 1)
    assert any("35 to 75" in p["quote"] for p in prep["passages"] if p["passage_id"].startswith("p002-"))
    assert I.prepare("again.pdf", DOC, C.extract_passages)["text"] == text   # deterministic


@pytest.mark.parametrize("data,code", [
    (b"not a pdf at all", "not_pdf"),
    (b"%PDF-1.4\nthis is broken", "pdf_unreadable"),
    (b"", "empty_file"),
])
def test_bad_pdfs_are_refused(data, code):
    with pytest.raises(I.IngestError) as e:
        I.prepare("x.pdf", data, C.extract_passages)
    assert e.value.code == code


def test_scanned_and_encrypted_pdfs_are_refused():
    w = pypdf.PdfWriter()
    w.add_blank_page(width=612, height=792)
    blank = io.BytesIO(); w.write(blank)
    with pytest.raises(I.IngestError) as e:
        I.prepare("scan.pdf", blank.getvalue(), C.extract_passages)
    assert e.value.code == "pdf_no_text"
    w = pypdf.PdfWriter(clone_from=pypdf.PdfReader(io.BytesIO(DOC)))
    w.encrypt("owner-test-password-not-a-secret")
    enc = io.BytesIO(); w.write(enc)
    with pytest.raises(I.IngestError) as e:
        I.prepare("locked.pdf", enc.getvalue(), C.extract_passages)
    assert e.value.code in ("pdf_encrypted", "pdf_unreadable")


def test_without_pypdf_a_pdf_is_refused(monkeypatch):
    monkeypatch.setattr(I, "pdf_capability", lambda: {"state": "unavailable"})
    with pytest.raises(I.IngestError) as e:
        I.prepare("x.pdf", DOC, C.extract_passages)
    assert e.value.code == "pdf_unavailable"


def test_core_ingests_pdf_with_resolvable_citations_and_selective_recheck(tmp_path):
    core = C.EvidenceCore(tmp_path / "store")
    pid = core.create_project("PDF review")["project_id"]
    out = core.ingest_document(pid, "concept c.pdf", DOC, "CONCEPT-A")
    assert out["status"] == "ingested" and out["passage_rule"] == "pdf_text_layer_v1" and out["pdf"]["pages"] == 2
    sv = core.source_version(pid, out["source_id"], "v1")
    assert sv["source_kind"] == "owner_pdf" and "#pdf_sha256=" in sv["origin_path"] and "pypdf=" in sv["origin_path"]
    for p in sv["passages"]:
        r = core.resolve_citation(pid, out["source_id"], "v1", p["passage_id"])
        assert sv["text"][r["start_char"]:r["end_char"]] == r["quote"]
    assert core.ingest_document(pid, "concept c.pdf", DOC, "CONCEPT-A")["status"] == "unchanged"
    core.run_comparison(pid)
    cells = {f"{c['candidate_id']}/{c['requirement_id']}": c for c in core.comparison(pid)["cells"]}
    assert cells["CONCEPT-A/R1"]["outcome"] == "meets"          # "Powered circulation: no." read from page 1
    v2 = make_pdf([["Thermal concept C", "", "Powered circulation: yes."]])
    out2 = core.ingest_document(pid, "concept c.pdf", v2, "CONCEPT-A")
    assert out2["status"] == "ingested" and out2["event_type"] == "source_revision" and out2["version_id"] == "v2"
