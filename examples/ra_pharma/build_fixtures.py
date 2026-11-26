"""Build the fictional RA Pharma demo documents as text-layer PDFs.

Build-time only. Requires Pillow and Playwright with a local Chromium, which are QA
tools and not part of the Workbench runtime. The PDFs are committed under
``src/patent_to_pilot/workbench/sample/ra_pharma/docs`` and pinned by SHA-256 in
``pack.json``. Rebuilding changes their bytes (Chromium writes a creation date), so
update the pack digests after any rebuild.

Every document is invented. The authority, company, people, numbers and results do
not exist. The emblem drawn on the authority letter is a neutral placeholder placed
where Thai government paper prints the Garuda; it is not the state emblem.

    python examples/ra_pharma/build_fixtures.py
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import base64
import sys

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "src" / "patent_to_pilot" / "workbench" / "sample" / "ra_pharma" / "docs"
FONTS = ROOT / "src" / "patent_to_pilot" / "workbench" / "fonts"
DEFAULT_CHROMIUM = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright" / "chromium-1228" / "chrome-win64" / "chrome.exe"

WATERMARK = "เอกสารสมมติเพื่อการสาธิตเท่านั้น ไม่ใช่หนังสือราชการหรือเอกสารของบริษัทจริง"


def png_data_uri(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def placeholder_emblem() -> str:
    """A neutral outline shape. Not the Garuda and not any real emblem."""
    im = Image.new("RGB", (300, 360), "white")
    d = ImageDraw.Draw(im)
    d.polygon([(150, 14), (270, 120), (226, 344), (74, 344), (30, 120)], outline="black", width=10)
    d.line([(150, 60), (150, 300)], fill="black", width=6)
    d.line([(80, 150), (220, 150)], fill="black", width=6)
    d.text((88, 314), "PLACEHOLDER", fill="black")
    return png_data_uri(im)


def company_logo(label: str) -> str:
    im = Image.new("RGB", (360, 360), "white")
    d = ImageDraw.Draw(im)
    d.ellipse([20, 20, 340, 340], outline="black", width=14)
    d.text((150, 168), label, fill="black")
    return png_data_uri(im)


CSS = """
@font-face { font-family: Sarabun; src: url('@REGULAR@'); }
@font-face { font-family: Sarabun; font-weight: 700; src: url('@BOLD@'); }
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
/* Thai mark composition is turned off so that each tone mark keeps its own
   Unicode mapping in the PDF text layer; positioning still uses GPOS marks. */
body { margin: 0; font-family: Sarabun; font-size: 15pt; line-height: 1.25;
       font-variant-ligatures: none; font-feature-settings: "liga" 0, "ccmp" 0, "clig" 0; }
.page { position: relative; width: 210mm; height: 297mm; page-break-after: always; overflow: hidden; }
.page:last-child { page-break-after: auto; }
.abs { position: absolute; margin: 0; }
.body { position: absolute; left: 30mm; right: 20mm; }
.body p { margin: 0 0 2mm; }
.indent { text-indent: 25mm; }
.mark { position: absolute; left: 30mm; right: 20mm; bottom: 8mm; font-size: 11pt; text-align: center;
        border-top: 0.3mm solid #777; padding-top: 1mm; color: #333; }
table { border-collapse: collapse; width: 100%; font-size: 14pt; }
td, th { border: 0.3mm solid #444; padding: 1mm 2mm; text-align: left; vertical-align: top; }
"""


def page(inner: str) -> str:
    return f'<div class="page">{inner}<p class="mark">{WATERMARK}</p></div>'


def doc(pages: list[str]) -> str:
    css = (CSS.replace("@REGULAR@", (FONTS / "Sarabun-Regular.ttf").as_uri())
           .replace("@BOLD@", (FONTS / "Sarabun-Bold.ttf").as_uri()))
    return f'<!doctype html><html lang="th"><head><meta charset="utf-8"><style>{css}</style></head><body>{"".join(pages)}</body></html>'


def incoming_authority() -> str:
    # Layout follows the external-letter element order of the OPM Saraban regulation 2526, clause 11.
    # The emblem is 30 mm high at the top centre (clauses 71.1 and 75).
    return doc([page(f"""
<img class="abs" src="{placeholder_emblem()}" style="left:92.5mm; top:15mm; height:30mm; width:25mm">
<div class="body" style="top:50mm">
<div style="display:flex; justify-content:space-between"><p>ที่ ตย ๐๓๑๒/๒๕๖๙</p>
<p style="width:68mm">สำนักงานกำกับยาตัวอย่าง<br>(หน่วยงานสมมติ)<br>๙๙ ถนนตัวอย่าง อำเภอเมือง<br>จังหวัดนนทบุรี ๑๑๐๐๐</p></div>
<p style="margin-left:75mm; margin-bottom:4mm">๑๒ พฤศจิกายน ๒๕๖๙</p>
<p>เรื่อง  ขอเอกสารเพิ่มเติมประกอบคำขอขึ้นทะเบียนตำรับยา เฟโซแคร์ โอดีที ๓๐ มก.</p>
<p>เรียน  กรรมการผู้จัดการ บริษัท สยามแคร์ ฟาร์มา จำกัด (สมมติ)</p>
<p>อ้างถึง  คำขอขึ้นทะเบียนตำรับยา เลขรับที่ ตย-๖๙-๐๐๔๕๑ ลงวันที่ ๓ ตุลาคม ๒๕๖๙</p>
<p>สิ่งที่ส่งมาด้วย  แบบแจ้งรายการเอกสารที่ต้องส่งเพิ่มเติม จำนวน ๑ ฉบับ</p>
<p class="indent">ตามที่บริษัทได้ยื่นคำขอขึ้นทะเบียนตำรับยาตามที่อ้างถึง สำนักงานได้ตรวจสอบเอกสารด้านคุณภาพแล้ว ขอให้บริษัทจัดส่งเอกสารเพิ่มเติม ดังนี้</p>
<p class="indent">๑. ผลการวิเคราะห์รุ่นการผลิต (batch analyses) ตามหัวข้อ P 5.4 ของ ACTD ซึ่งรวมผลการทดสอบการละลายของผลิตภัณฑ์ของบริษัทที่เวลา ๓๐ นาที</p>
<p class="indent">๒. หนังสือรับรองผลการวิเคราะห์ (Certificate of Analysis) ของรุ่นการผลิตที่ใช้ทดสอบตามข้อ ๑</p>
<p class="indent">ทั้งนี้ ขอให้จัดส่งภายใน ๓๐ วันนับจากวันที่ได้รับหนังสือฉบับนี้</p>
<p class="indent">จึงเรียนมาเพื่อโปรดดำเนินการ</p>
<p style="margin:6mm 0 0 75mm">ขอแสดงความนับถือ</p>
<p style="margin:10mm 0 0 55mm; width:90mm; text-align:center">(นางสาวตัวอย่าง ทดสอบระบบ)<br>ผู้อำนวยการกองตัวอย่างทะเบียนยา<br>ปฏิบัติราชการแทนเลขาธิการ (สมมติ)</p>
<p style="margin-top:4mm; font-size:13pt">กองตัวอย่างทะเบียนยา<br>โทร. ๐ ๒๐๐๐ ๐๐๐๐</p>
</div>
""")])


def incoming_company() -> str:
    return doc([page(f"""
<img class="abs" src="{company_logo('TLX')}" style="left:30mm; top:12mm; height:16mm; width:16mm">
<p class="abs" style="left:50mm; top:13mm; font-weight:700">บริษัท ทีแอลเอ็กซ์ ไลเซนส์ซิ่ง จำกัด (สมมติ)</p>
<p class="abs" style="left:50mm; top:22mm; font-size:13pt">๘ ถนนสมมติ แขวงตัวอย่าง เขตทดสอบ กรุงเทพมหานคร ๑๐๑๑๐</p>
<div class="body" style="top:40mm">
<p>ที่ TLX-LG 118/2569</p>
<p style="margin-left:75mm; margin-bottom:4mm">๑๘ พฤศจิกายน ๒๕๖๙</p>
<p>เรื่อง  ขอสำเนาผลการทดสอบการละลายของผลิตภัณฑ์ภายใต้สัญญาอนุญาตให้ใช้สิทธิ</p>
<p>เรียน  ผู้จัดการฝ่ายขึ้นทะเบียนยา บริษัท สยามแคร์ ฟาร์มา จำกัด (สมมติ)</p>
<p class="indent">ตามสัญญาอนุญาตให้ใช้สิทธิระหว่างบริษัททั้งสอง บริษัทขอสำเนาผลการทดสอบการละลายของผลิตภัณฑ์ เฟโซแคร์ โอดีที ๓๐ มก. ที่บริษัทจะยื่นต่อหน่วยงานกำกับดูแล เพื่อใช้ประกอบการติดตามตามสัญญา</p>
<p class="indent">จึงเรียนมาเพื่อโปรดพิจารณา</p>
<p style="margin:6mm 0 0 75mm">ขอแสดงความนับถือ</p>
<p style="margin:16mm 0 0 55mm; width:90mm; text-align:center">(นายสมมติ ตัวอย่าง)<br>ผู้จัดการฝ่ายกฎหมาย</p>
</div>
""")])


APPLICANT_HEADER = """
<p class="abs" style="left:30mm; top:12mm; font-weight:700">บริษัท สยามแคร์ ฟาร์มา จำกัด (สมมติ)</p>
<p class="abs" style="left:30mm; top:20mm; font-size:12pt">Siam Care Pharma Co., Ltd. (fictional) · ฝ่ายควบคุมคุณภาพ · ๑๒๓ ถนนสมมติ จังหวัดปทุมธานี ๑๒๐๐๐</p>
"""


def formulation_record() -> str:
    rows = [("Intragranular", "Fexofenadine hydrochloride", "30"),
            ("Intragranular", "Microcrystalline cellulose (MCC)", "45"),
            ("Intragranular", "Hydroxypropyl cellulose (HPC)", "6"),
            ("Intragranular", "Magnesium stearate", "3"),
            ("Extragranular", "Citric acid anhydrous", "20"),
            ("Extragranular", "Sodium bicarbonate", "10"),
            ("Extragranular", "Mannitol", "250"),
            ("Extragranular", "Crospovidone", "40"),
            ("Extragranular", "Sucralose", "4"),
            ("Extragranular", "Magnesium stearate", "4")]
    table = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
    return doc([page(APPLICANT_HEADER + f"""
<div class="body" style="top:36mm">
<p style="font-weight:700">บันทึกสูตรตำรับ เลขที่ FR-0117 ฉบับที่ 2.0 ลงวันที่ 1 ตุลาคม 2569</p>
<p>ผลิตภัณฑ์: เฟโซแคร์ โอดีที 30 มก. (สมมติ) ยาเม็ดกลบรสชนิดแตกตัวในปาก</p>
<p>ผู้จัดทำ: บริษัท สยามแคร์ ฟาร์มา จำกัด (สมมติ)</p>
<table><tr><th>Portion</th><th>Ingredient</th><th>mg/tablet</th></tr>{table}</table>
<p style="margin-top:3mm">หมายเหตุ: บันทึกนี้ไม่ระบุอัตราส่วนโมลของกรดต่อด่างในคู่สารฟู่</p>
</div>""")])


def dissolution_report(edition: str, date_th: str, value: str, rsd: str, note: str) -> str:
    return doc([
        page(APPLICANT_HEADER + f"""
<div class="body" style="top:36mm">
<p style="font-weight:700">รายงานผลการทดสอบการละลาย (Dissolution Test Report)</p>
<p>เลขที่รายงาน: QC-DIS-0459 ฉบับที่ {edition} ลงวันที่ {date_th}</p>
<p>ผู้จัดทำ: บริษัท สยามแคร์ ฟาร์มา จำกัด (สมมติ)</p>
<p>ผลิตภัณฑ์: เฟโซแคร์ โอดีที 30 มก. (สมมติ)</p>
<p>รุ่นการผลิต: SC-2511-03</p>
<p>วิธีทดสอบ: USP apparatus 2 (paddle) 50 rpm ตัวกลาง 0.001 N HCl ปริมาตร 500 mL อุณหภูมิ 37.0 องศาเซลเซียส</p>
<p>{note}</p>
</div>"""),
        page(APPLICANT_HEADER + f"""
<div class="body" style="top:36mm">
<p style="font-weight:700">ผลการทดสอบ รุ่นการผลิต SC-2511-03 (n = 12)</p>
<table><tr><th>เวลา (นาที)</th><th>ร้อยละการละลายเฉลี่ย</th><th>RSD (%)</th></tr>
<tr><td>10</td><td>68</td><td>3.4</td></tr>
<tr><td>15</td><td>79</td><td>2.8</td></tr></table>
<p style="margin-top:3mm">ผลที่เวลา 30 นาที: ร้อยละการละลายเฉลี่ย {value} (RSD {rsd}%)</p>
<p>ผู้ตรวจสอบรายงาน: หัวหน้าฝ่ายควบคุมคุณภาพ (สมมติ)</p>
</div>"""),
    ])


DOCUMENTS = {
    "incoming-authority-rfi.pdf": incoming_authority,
    "incoming-licensor-request.pdf": incoming_company,
    "applicant-formulation-record.pdf": formulation_record,
    "applicant-dissolution-report-1.0.pdf": lambda: dissolution_report(
        "1.0", "20 พฤศจิกายน 2569", "91", "2.1", "สถานะ: ฉบับอนุมัติ"),
    "applicant-dissolution-report-1.1.pdf": lambda: dissolution_report(
        "1.1", "24 พฤศจิกายน 2569", "89", "2.3",
        "สถานะ: ฉบับแก้ไข แทนฉบับที่ 1.0 เนื่องจากคำนวณค่าเฉลี่ยใหม่"),
}


def main() -> int:
    executable = Path(os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or DEFAULT_CHROMIUM)
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_build.html"
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(executable))
        page_ = browser.new_page()
        try:
            for name, build in DOCUMENTS.items():
                tmp.write_text(build(), encoding="utf-8")
                page_.goto(tmp.resolve().as_uri())
                page_.evaluate("document.fonts.ready")
                page_.pdf(path=str(OUT / name), width="210mm", height="297mm", print_background=True)
                digest = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
                print(f"{name} {digest}")
        finally:
            browser.close()
            tmp.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
