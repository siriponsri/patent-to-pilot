"""Read the layout of a Thai letter PDF and render an editable reply.

The reader works on the PDF text layer and the drawing operations of each page. It
reports what it found with page coordinates (points, origin at the top-left corner)
and keeps uncertain readings visible. It does not recognise the content of an image:
an image at the Garuda position is reported as such, and its identity stays a review
item. Rendering produces print HTML and a DOCX file with the Sarabun font embedded.
"""
from __future__ import annotations

from datetime import date
import html
import io
import math
from pathlib import Path
import re
import uuid
import zipfile

from patent_to_pilot.workbench.core import Conflict

READER_VERSION = "thai-letter-layout/1.0.0"
CM = 72 / 2.54
FONTS = Path(__file__).resolve().parent / "fonts"
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
          "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
DATE_RE = re.compile(r"^([0-9๐-๙]{1,2})\s+(" + "|".join(MONTHS) + r")\s+([0-9๐-๙]{4})$")
LABELS = {"subject": "เรื่อง", "salutation": "เรียน", "reference": "อ้างถึง", "enclosures": "สิ่งที่ส่งมาด้วย"}


def thai_text(value: str) -> str:
    """Repair the two text-layer artefacts seen in Thai PDFs: NUL glyph mappings and decomposed SARA AM."""
    return value.replace("\x00", "").replace("ํา", "ำ")


def _mul(a, b):
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3], a[2] * b[0] + a[3] * b[2],
            a[2] * b[1] + a[3] * b[3], a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def _images(reader, content, xobjects, ctm, out, depth=0):
    from pypdf.generic import ContentStream
    stack = []
    for operands, op in ContentStream(content, reader).operations:
        if op == b"q":
            stack.append(ctm)
        elif op == b"Q" and stack:
            ctm = stack.pop()
        elif op == b"cm":
            ctm = _mul([float(v) for v in operands], ctm)
        elif op == b"Do":
            obj = xobjects.get(operands[0])
            if obj is None:
                continue
            obj = obj.get_object()
            if obj.get("/Subtype") == "/Image":
                xs = [ctm[4], ctm[4] + ctm[0], ctm[4] + ctm[2], ctm[4] + ctm[0] + ctm[2]]
                ys = [ctm[5], ctm[5] + ctm[1], ctm[5] + ctm[3], ctm[5] + ctm[1] + ctm[3]]
                out.append({"name": str(operands[0]), "x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys),
                            "pixels": [int(obj.get("/Width", 0)), int(obj.get("/Height", 0))]})
            elif obj.get("/Subtype") == "/Form" and depth < 4:
                matrix = [float(v) for v in obj.get("/Matrix", [1, 0, 0, 1, 0, 0])]
                inner = dict((obj.get("/Resources") or {}).get("/XObject") or {})
                _images(reader, obj, inner, _mul(matrix, ctm), out, depth + 1)


def read_layout(data: bytes) -> dict:
    """Text runs and image boxes per page. Requires the optional ``pypdf`` extra."""
    try:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
    except ImportError:
        raise Conflict("ต้องติดตั้งส่วนเสริม pypdf เพื่ออ่านเลย์เอาต์ PDF", "pdf_reader_unavailable") from None
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            width, height = float(page.mediabox.width), float(page.mediabox.height)
            runs = []

            def visit(text, cm, tm, _font, size):
                text = thai_text(text)
                if not text.strip():
                    return
                m = _mul(tm, cm)
                scale = math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))
                runs.append({"text": text.strip(), "x": round(m[4], 1), "y": round(height - m[5], 1),
                             "size": round((size or 0) * scale, 1)})

            page.extract_text(visitor_text=visit)
            images = []
            resources = page.get("/Resources") or {}
            xobjects = dict((resources.get("/XObject") or {}))
            content = page.get_contents()
            if content is not None:
                _images(reader, content, xobjects, [1, 0, 0, 1, 0, 0], images)
            boxes = [{"name": i["name"], "x": round(i["x0"], 1), "y": round(height - i["y1"], 1),
                      "width": round(i["x1"] - i["x0"], 1), "height": round(i["y1"] - i["y0"], 1),
                      "height_cm": round((i["y1"] - i["y0"]) / CM, 2), "pixels": i["pixels"]} for i in images]
            pages.append({"page": number, "width": round(width, 1), "height": round(height, 1),
                          "runs": sorted(runs, key=lambda r: (r["y"], r["x"])), "images": boxes})
    except (PdfReadError, ValueError, KeyError, TypeError) as exc:
        raise Conflict(f"อ่านไฟล์ PDF ไม่ได้: {type(exc).__name__}", "pdf_unreadable") from None
    return {"reader": READER_VERSION, "pages": pages}


def page_text(layout: dict, number: int) -> str:
    page = layout["pages"][number - 1]
    lines, last = [], None
    for run in page["runs"]:
        if last is not None and abs(run["y"] - last) < 2:
            lines[-1] += "  " + run["text"]
        else:
            lines.append(run["text"])
        last = run["y"]
    return "\n".join(lines)


def _field(value, run=None, status="read", note_th=None, page=1):
    out = {"value": value, "status": status, "page": page if run or value else None,
           "x": run["x"] if run else None, "y": run["y"] if run else None}
    if note_th:
        out["note_th"] = note_th
    return out


def read_letter(data: bytes) -> dict:
    """Identify the letter parts on page 1 and classify the sender from layout evidence."""
    layout = read_layout(data)
    page = layout["pages"][0]
    width, height = page["width"], page["height"]
    runs = page["runs"]
    fields, uncertain = {}, []

    def starts(prefix):
        return next((r for r in runs if r["text"].startswith(prefix + " ") or r["text"] == prefix), None)

    consumed = set()

    def continued(run, stop_prefixes):
        """Join wrapped lines that follow at the body margin until the next labelled part.

        A browser drops the space at a line break. Thai words are written without spaces,
        so a space is restored only when a digit or Latin letter meets the break.
        """
        text, y = run["text"], run["y"]
        margin = min(r["x"] for r in runs)
        for nxt in runs:
            if nxt["y"] <= y or nxt["y"] - y > run["size"] * 1.7 + 2:
                continue
            if abs(nxt["x"] - margin) > 5 or any(nxt["text"].startswith(p) for p in stop_prefixes):
                break
            thai = lambda ch: "ก" <= ch <= "๎"
            glue = "" if thai(text[-1]) and thai(nxt["text"][0]) else " "
            text, y = text + glue + nxt["text"], nxt["y"]
            consumed.add(id(nxt))
        return text

    stops = list(LABELS.values()) + ["ตามที่", "ที่ "]
    number = next((r for r in runs if r["text"].startswith("ที่ ") and r["x"] < width / 2), None)
    fields["number"] = _field(number["text"][4:].strip() if number else None, number, "read" if number else "absent")
    date_run = next((r for r in runs if DATE_RE.match(r["text"])), None)
    fields["date"] = _field(date_run["text"] if date_run else None, date_run, "read" if date_run else "absent")
    if date_run:
        d, month, year = DATE_RE.match(date_run["text"]).groups()
        fields["date"]["iso"] = (f"{int(year.translate(THAI_DIGITS)) - 543:04d}-{MONTHS.index(month) + 1:02d}-"
                                 f"{int(d.translate(THAI_DIGITS)):02d}")
    for key, label in LABELS.items():
        run = starts(label)
        fields[key] = _field(continued(run, stops)[len(label):].strip() if run else None, run,
                             "read" if run else "absent")

    # Sender block of an official letter sits on the right, level with the number line.
    top = number["y"] - 2 if number else 0
    bottom = date_run["y"] if date_run else height / 3
    block = [r for r in runs if r["x"] > width * 0.45 and top <= r["y"] < bottom]
    letterhead = [r for r in runs if r["y"] < (number["y"] if number else height / 4) - 4]
    images = page["images"]
    emblem = None
    for image in images:
        center = image["x"] + image["width"] / 2
        if image["y"] < height * 0.25:
            centred = abs(center - width / 2) <= 0.5 * CM
            garuda_size = abs(image["height_cm"] - 3.0) <= 0.2
            emblem = {**image, "position": "top_center" if centred else ("top_left" if center < width / 3 else "top"),
                      "matches_opm_garuda_layout": centred and garuda_size,
                      "note_th": ("ภาพอยู่กึ่งกลางส่วนบนและสูง %.2f ซม. ตรงกับตำแหน่งและขนาดตราครุฑตามข้อ 71.1 และ 75 "
                                  "ระบบไม่ได้ตรวจว่าภาพเป็นตราครุฑจริง" % image["height_cm"]) if centred and garuda_size
                      else "ภาพที่หัวกระดาษไม่ตรงตำแหน่งหรือขนาดตราครุฑ อาจเป็นตราบริษัท"}
            break
    closing = starts("ขอแสดงความนับถือ")
    signer = next((r for r in runs if closing and r["y"] > closing["y"] and r["text"].startswith("(")), None)
    positions = []
    if signer:
        for r in runs:
            if r["y"] > signer["y"] and abs((r["x"] + 0) - signer["x"]) < 60 and r["y"] - signer["y"] < 3 * signer["size"] * 1.4:
                positions.append(r)
    sign_images = [i for i in images if closing and signer and closing["y"] < i["y"] < signer["y"]]
    fields["closing"] = _field(closing["text"] if closing else None, closing, "read" if closing else "absent")
    fields["signer"] = _field(signer["text"].strip("() ") if signer else None, signer, "read" if signer else "absent")
    fields["signer_position"] = _field(" / ".join(r["text"] for r in positions) or None, positions[0] if positions else None,
                                       "read" if positions else "absent")
    fields["signature_image"] = _field("present" if sign_images else None, None, "read" if sign_images else "uncertain",
                                       None if sign_images else "ไม่พบภาพลายมือชื่อในไฟล์ อาจเป็นสำเนาก่อนลงนาม ต้องตรวจฉบับจริง")
    if not sign_images:
        uncertain.append("signature_image")

    requests = []
    for run in runs:
        match = re.match(r"^([0-9๐-๙]+)\.\s*(.+)", run["text"])
        if match and closing and run["y"] < closing["y"] and id(run) not in consumed:
            text = continued(run, stops + ["๑.", "๒.", "๓.", "ทั้งนี้", "จึงเรียน"])
            requests.append({"number": int(match.group(1).translate(THAI_DIGITS)),
                             "text": re.sub(r"^[0-9๐-๙]+\.\s*", "", text), "page": 1, "x": run["x"], "y": run["y"]})
    watermark = next((r for r in runs if "เอกสารสมมติ" in r["text"]), None)

    authority_like = bool(emblem and emblem["matches_opm_garuda_layout"] and number and block)
    company_head = next((r for r in letterhead if r["text"].startswith("บริษัท")), None)
    if authority_like:
        sender = {"kind": "authority", "name": block[0]["text"] if block else None,
                  "address": " ".join(r["text"] for r in block[1:]), "basis_th":
                  "ตราที่ตำแหน่งครุฑ เลขที่หนังสือ และส่วนราชการเจ้าของหนังสือทางขวา ตรงกับแบบหนังสือภายนอก"}
        names = [r for r in block if not re.search(r"[0-9๐-๙]", r["text"])]
        sender["name"] = " ".join(r["text"] for r in names) or sender["name"]
        sender["address"] = " ".join(r["text"] for r in block if r not in names)
        doc_type = "authority_external_letter"
    elif company_head:
        sender = {"kind": "company", "name": company_head["text"], "address": " ".join(
            r["text"] for r in letterhead if r is not company_head), "basis_th": "หัวกระดาษขึ้นต้นด้วยชื่อบริษัทและไม่มีตราที่ตำแหน่งครุฑ"}
        doc_type = "company_letter"
    else:
        sender = {"kind": "unknown", "name": None, "address": None, "basis_th": "ไม่พบหลักฐานพอระบุประเภทผู้ส่ง"}
        doc_type = "unknown"
        uncertain.append("sender")
    if emblem and emblem["matches_opm_garuda_layout"]:
        uncertain.append("emblem_identity")
    if fields["enclosures"]["value"] and len(layout["pages"]) == 1:
        fields["enclosures"]["status"] = "uncertain"
        fields["enclosures"]["note_th"] = "หนังสืออ้างสิ่งที่ส่งมาด้วย แต่ไฟล์มีเพียงหน้าหนังสือ ไม่พบเอกสารแนบ"
        uncertain.append("enclosures")
    addressee_kind = "company" if (fields["salutation"]["value"] or "").find("บริษัท") >= 0 else "authority"
    return {"reader": READER_VERSION, "page_count": len(layout["pages"]), "page_size_pt": [width, height],
            "document_type": doc_type, "sender": sender, "addressee_kind": addressee_kind, "fields": fields,
            "requests": requests, "emblem": emblem, "images": images,
            "fictional_marker": watermark["text"] if watermark else None, "uncertain": uncertain,
            "layout": layout}


def select_template(templates: list[dict], sender_kind: str, addressee_kind: str) -> dict:
    """Pick the outgoing template for the actual sender, and say why the others do not apply."""
    chosen, rejected = None, []
    for t in templates:
        if t["sender_kind"] != sender_kind:
            rejected.append({"template_id": t["template_id"], "reason_th":
                             "แบบนี้สำหรับผู้ส่งที่เป็นส่วนราชการ ผู้ส่งจริงเป็นบริษัทจึงใช้ตราครุฑไม่ได้"
                             if t["sender_kind"] == "authority" else "แบบนี้สำหรับผู้ส่งประเภทอื่น"})
        elif t["addressee_kind"] not in (addressee_kind, "any"):
            rejected.append({"template_id": t["template_id"], "reason_th": "ผู้รับไม่ตรงกับแบบนี้"})
        elif chosen is None:
            chosen = t
        else:
            rejected.append({"template_id": t["template_id"], "reason_th": "มีแบบที่ตรงกว่าแล้ว"})
    if chosen is None:
        raise Conflict("ไม่มีแบบหนังสือสำหรับผู้ส่งและผู้รับนี้", "no_template")
    return {"template": chosen, "rejected": rejected, "sender_kind": sender_kind, "addressee_kind": addressee_kind}


def thai_date(iso: str, thai_digits: bool = False) -> str:
    d = date.fromisoformat(iso)
    text = f"{d.day} {MONTHS[d.month - 1]} {d.year + 543}"
    return text.translate(str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")) if thai_digits else text


def arabic_digits(text: str) -> str:
    return text.translate(THAI_DIGITS)


# ------------------------------------------------------------------ rendering
LAYOUT_CLASS = {"letterhead": "lh", "letterhead_sub": "lhs", "number": "num", "date": "date", "subject": "label",
                "salutation": "label", "reference": "label", "enclosures": "label", "enclosure_item": "encl",
                "paragraph": "para", "ending": "para", "closing": "closing", "signature_space": "sigspace",
                "signer": "signer", "signer_position": "signer", "contact": "contact"}

PRINT_CSS = """
@font-face { font-family: Sarabun; src: url('/fonts/Sarabun-Regular.ttf'); }
@font-face { font-family: Sarabun; font-weight: 700; src: url('/fonts/Sarabun-Bold.ttf'); }
@page { size: A4; margin: 20mm 20mm 20mm 30mm; }
body { font-family: Sarabun, "TH Sarabun New", sans-serif; font-size: 14pt; line-height: 1.3; margin: 0; color: #000; }
.sheet { width: 160mm; margin: 0 auto; }
p { margin: 0; }
.lh { font-weight: 700; font-size: 16pt; } .lhs { font-size: 11pt; border-bottom: 0.4mm solid #000; padding-bottom: 2mm; margin-bottom: 6mm; }
.date { margin: 3mm 0 4mm 75mm; } .label { margin-bottom: 1mm; } .encl { margin-left: 25mm; }
.para { text-indent: 25mm; margin-top: 2mm; } .closing { margin: 6mm 0 0 75mm; }
.sigspace { height: 18mm; } .signer { margin-left: 55mm; width: 90mm; text-align: center; }
.contact { margin-top: 8mm; font-size: 12pt; }
.draft { font-size: 11pt; color: #555; border-top: 0.3mm solid #999; margin-top: 8mm; padding-top: 1mm; }
"""


def render_html(blocks: list[dict], title: str, notice: str) -> str:
    body = "".join(f'<p class="{LAYOUT_CLASS.get(b["kind"], "para")}" data-block="{html.escape(b["block_id"])}">'
                   f'{html.escape(b["text"]) if b["text"] else "&nbsp;"}</p>' for b in blocks)
    return (f'<!doctype html><html lang="th"><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f'<style>{PRINT_CSS}</style></head><body><div class="sheet">{body}'
            f'<p class="draft">{html.escape(notice)}</p></div></body></html>')


def _font_key():
    guid = str(uuid.uuid4()).upper()
    hexes = guid.replace("-", "")
    key = bytes(int(hexes[i:i + 2], 16) for i in range(30, -1, -2))
    return "{" + guid + "}", key


def _obfuscate(font: bytes, key: bytes) -> bytes:
    head = bytes(b ^ key[i % 16] for i, b in enumerate(font[:32]))
    return head + font[32:]


def _run(text, bold=False, size=None):
    props = "<w:b/><w:bCs/>" if bold else ""
    if size:
        props += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    return (f'<w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">{html.escape(text, quote=False)}</w:t></w:r>')


DOCX_PARA = {  # (indent left twips, first line twips, alignment, space before, bold, size half-points)
    "letterhead": (0, 0, "left", 0, True, 32), "letterhead_sub": (0, 0, "left", 0, False, 22),
    "number": (0, 0, "left", 240, False, None), "date": (4252, 0, "left", 120, False, None),
    "enclosure_item": (1418, 0, "left", 0, False, None), "paragraph": (0, 1418, "both", 120, False, None),
    "ending": (0, 1418, "left", 120, False, None), "closing": (4252, 0, "left", 360, False, None),
    "signature_space": (0, 0, "left", 480, False, None), "signer": (3118, 0, "center", 0, False, None),
    "signer_position": (3118, 0, "center", 0, False, None), "contact": (0, 0, "left", 360, False, 24)}


def render_docx(blocks: list[dict], title: str, notice: str) -> bytes:
    """A4 DOCX that Word and LibreOffice can edit, with Sarabun embedded (SIL OFL 1.1)."""
    paras = []
    for b in blocks:
        left, first, jc, before, bold, size = DOCX_PARA.get(b["kind"], (0, 0, "left", 60, False, None))
        ppr = (f'<w:pPr><w:spacing w:before="{before}" w:after="0"/><w:ind w:left="{left}" w:firstLine="{first}"/>'
               f'<w:jc w:val="{jc}"/></w:pPr>')
        paras.append(f'<w:p>{ppr}{_run(b["text"] or "", bold, size)}</w:p>')
    paras.append('<w:p><w:pPr><w:spacing w:before="480"/></w:pPr>' + _run(notice, False, 20) + "</w:p>")
    section = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" '
               'w:left="1701" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>')
    ns = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {ns}><w:body>{"".join(paras)}{section}</w:body></w:document>'
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {ns}><w:docDefaults><w:rPrDefault><w:rPr>'
              '<w:rFonts w:ascii="Sarabun" w:hAnsi="Sarabun" w:cs="Sarabun" w:eastAsia="Sarabun"/>'
              '<w:sz w:val="28"/><w:szCs w:val="28"/><w:lang w:val="th-TH" w:bidi="th-TH"/></w:rPr></w:rPrDefault>'
              '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="252" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
              '</w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style></w:styles>')
    reg_key, reg = _font_key()
    bold_key, bold = _font_key()
    font_table = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:fonts {ns}><w:font w:name="Sarabun">'
                  '<w:charset w:val="DE"/><w:family w:val="auto"/><w:pitch w:val="variable"/>'
                  f'<w:embedRegular r:id="rIdF1" w:fontKey="{reg_key}"/><w:embedBold r:id="rIdF2" w:fontKey="{bold_key}"/>'
                  '</w:font></w:fonts>')
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    files = {
        "[Content_Types].xml": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                                '<Default Extension="xml" ContentType="application/xml"/>'
                                '<Default Extension="odttf" ContentType="application/vnd.openxmlformats-officedocument.obfuscatedFont"/>'
                                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                                '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                                '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
                                '<Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>'
                                '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                                '</Types>'),
        "_rels/.rels": (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                        f'<Relationship Id="rId1" Type="{rel}/officeDocument" Target="word/document.xml"/>'
                        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                        '</Relationships>'),
        "docProps/core.xml": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties '
                              'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                              'xmlns:dc="http://purl.org/dc/elements/1.1/">'
                              f'<dc:title>{html.escape(title)}</dc:title><dc:creator>Patent-to-Pilot Workbench (draft)</dc:creator>'
                              '</cp:coreProperties>'),
        "word/_rels/document.xml.rels": (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                         f'<Relationship Id="rId1" Type="{rel}/styles" Target="styles.xml"/>'
                                         f'<Relationship Id="rId2" Type="{rel}/settings" Target="settings.xml"/>'
                                         f'<Relationship Id="rId3" Type="{rel}/fontTable" Target="fontTable.xml"/></Relationships>'),
        "word/_rels/fontTable.xml.rels": (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                          f'<Relationship Id="rIdF1" Type="{rel}/font" Target="fonts/font1.odttf"/>'
                                          f'<Relationship Id="rIdF2" Type="{rel}/font" Target="fonts/font2.odttf"/></Relationships>'),
        "word/document.xml": document, "word/styles.xml": styles, "word/fontTable.xml": font_table,
        "word/settings.xml": (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings {ns}>'
                              '<w:embedTrueTypeFonts/><w:defaultTabStop w:val="720"/></w:settings>'),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items():
            z.writestr(name, text.encode("utf-8"))
        z.writestr("word/fonts/font1.odttf", _obfuscate((FONTS / "Sarabun-Regular.ttf").read_bytes(), reg))
        z.writestr("word/fonts/font2.odttf", _obfuscate((FONTS / "Sarabun-Bold.ttf").read_bytes(), bold))
    return buf.getvalue()


def docx_text(data: bytes) -> list[str]:
    """Paragraph texts of a DOCX, used to check that an export reopens with the reviewed wording."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    return [html.unescape("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p))) for p in re.findall(r"<w:p>.*?</w:p>", xml)]
