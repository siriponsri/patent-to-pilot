"""Build the comprehensive Thai IS2 report PDF from REPORT-TH.md (layout designed by the main planner).

python build_report.py [--md REPORT-TH.md] [--out MWD-REPORT-TH]
Needs: Python `markdown` 3.7, Google Chrome (headless print), TH Sarabun New installed.
Figures: write a line `{{fig:NN}}` in the Markdown where figure NN goes; if a figure has no marker it is
placed after the first paragraph that mentions "รูปที่ N". Captions come from FIGURE-REQUESTS.md (Thai caption).
"""
import argparse
import re
import subprocess
from datetime import date
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
FIG_FILES = {1: "rfig01.png", 2: "rfig02.png", 3: None, 4: "rfig04.png", 5: "rfig05.png", 6: "rfig06.png",
             7: "rfig07.png", 8: "rfig08.png", 9: "rfig09.png", 10: "rfig10.png", 11: "rfig11.png", 12: "rfig12.png"}
NARROW = {4, 5, 8}

CSS = """
@font-face { font-family: 'THSN'; src: url('file:///C:/Users/User/AppData/Local/Microsoft/Windows/Fonts/THSarabunNew.ttf'); font-weight: 400; }
@font-face { font-family: 'THSN'; src: url('file:///C:/Users/User/AppData/Local/Microsoft/Windows/Fonts/THSarabunNew%20Bold.ttf'); font-weight: 700; }
@font-face { font-family: 'THSN'; src: url('file:///C:/Users/User/AppData/Local/Microsoft/Windows/Fonts/THSarabunNew%20Italic.ttf'); font-style: italic; }
@page { size: A4; margin: 22mm 22mm 24mm 25mm;
  @bottom-center { content: counter(page); font-family: THSN, 'TH Sarabun New', sans-serif; font-size: 13pt; color: #555; }
  @top-right { content: "Market Window Dossier และ LOE-Bench"; font-family: THSN, 'TH Sarabun New', sans-serif;
               font-size: 12pt; color: #8a93a3; } }
@page :first { margin: 0; @bottom-center { content: none; } @top-right { content: none; } }
html { font-family: THSN, 'TH Sarabun New', sans-serif; font-size: 16pt; line-height: 1.38; color: #1d2433; }
body { margin: 0; }
.cover { height: 297mm; box-sizing: border-box; padding: 38mm 28mm 26mm 30mm; display: flex; flex-direction: column;
  border-left: 14mm solid #0b2545; page-break-after: always; }
.cover .kicker { font-size: 15pt; letter-spacing: .04em; color: #13315c; font-weight: 700; }
.cover h1 { font-size: 30pt; line-height: 1.18; margin: 10mm 0 4mm; color: #0b2545; }
.cover .en { font-size: 17pt; color: #13315c; margin-bottom: 18mm; }
.cover .who { font-size: 16pt; line-height: 1.5; }
.cover .foot { margin-top: auto; font-size: 14pt; color: #5b6474; border-top: 1px solid #d5dae1; padding-top: 4mm; }
.cover .note { margin-top: 8mm; font-size: 14pt; background: #fff3d6; border-left: 4px solid #8a5a00; padding: 3mm 4mm; }
h1, h2, h3 { color: #0b2545; line-height: 1.2; break-after: avoid; }
h1 { font-size: 24pt; margin: 0 0 4mm; padding-top: 2mm; border-bottom: 2px solid #0b2545; page-break-before: always; }
h2 { font-size: 19pt; margin: 6mm 0 2mm; }
h3 { font-size: 17pt; margin: 4mm 0 1mm; }
p { margin: 0 0 2.4mm; text-align: justify; text-justify: inter-character; }
ul, ol { margin: 0 0 2.4mm 6mm; padding-left: 4mm; }
li { margin-bottom: 1mm; }
table { border-collapse: collapse; width: 100%; margin: 2mm 0 4mm; font-size: 14pt; line-height: 1.25; break-inside: avoid; }
th { background: #eef1f5; color: #0b2545; text-align: left; font-weight: 700; }
th, td { border-bottom: 1px solid #d5dae1; padding: 1.2mm 2mm; vertical-align: top; }
td:not(:first-child) { font-variant-numeric: tabular-nums; }
blockquote { margin: 3mm 0; padding: 2mm 5mm; background: #f3f5f8; border-left: 4px solid #0b5cad; }
code { font-family: Consolas, monospace; font-size: 12pt; background: #f3f5f8; padding: 0 1mm; }
a { color: #0b5cad; text-decoration: none; }
figure { margin: 4mm 0 5mm; text-align: center; break-inside: avoid; }
figure img { width: 100%; }
figure.narrow img { width: 66%; }
figcaption { font-size: 14pt; color: #3b4456; margin-top: 2mm; text-align: center; }
figcaption b { color: #0b2545; }
.toc { page-break-after: always; }
.cover h1, .toc h1 { page-break-before: avoid; border: none; }
.toc ul { list-style: none; margin-left: 0; padding-left: 0; }
.toc ul ul { padding-left: 7mm; }
.toc li { margin: .6mm 0; }
"""


def captions():
    txt = (HERE / "FIGURE-REQUESTS.md").read_text(encoding="utf-8")
    caps, anchors = {}, {}
    for block in re.split(r"\n(?=## Figure )", txt):
        m = re.match(r"## Figure (\d+)\.", block)
        if not m:
            continue
        n = int(m.group(1))
        c = re.search(r"\*\*Thai caption\*\*\s*(.+?)\n", block + "\n")
        a = re.search(r"\*\*Anchor\*\*\s*(.+?)\n", block + "\n")
        if c:
            caps[n] = c.group(1).strip()
        if a:
            sec = re.findall(r"§+\s*([\d.]+)", a.group(1))
            aid = re.search(r"#([\w-]+)\)", a.group(1))
            anchors[n] = (sec[-1].strip(".") if sec else None, aid.group(1) if aid else None)
    return caps, anchors


def figure_html(n, cap):
    f = FIG_FILES.get(n)
    if not f:
        return ""
    cls = ' class="narrow"' if n in NARROW else ""
    return (f'<figure{cls}><img src="figures/{f}" alt="รูปที่ {n}"><figcaption><b>รูปที่ {n}</b> {cap}'
            f"</figcaption></figure>")


def build(md_path, out_stem):
    src = (HERE / md_path).read_text(encoding="utf-8")
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S)          # source comments stay in Markdown, not in print
    caps, anchors = captions()
    placed = set()

    def marker(m):
        n = int(m.group(1))
        placed.add(n)
        return "\n" + figure_html(n, caps.get(n, "")) + "\n"
    src = re.sub(r"\{\{fig:(\d+)\}\}", marker, src)
    paras = src.split("\n\n")
    for n in sorted(caps):
        if n in placed or not FIG_FILES.get(n):
            continue
        for i, p in enumerate(paras):
            if re.search(rf"รูปที่\s*{n}(?!\d)", p) and not p.lstrip().startswith(("#", "|", "<figure")):
                paras[i] = p + "\n\n" + figure_html(n, caps[n])
                placed.add(n)
                break
    for n in sorted(caps):          # fallback: after the first paragraph of the anchored section
        if n in placed or not FIG_FILES.get(n) or n not in anchors:
            continue
        sec, aid = anchors[n]
        for i, p in enumerate(paras):
            head = p.lstrip()
            if sec:
                hit = re.match(r"#{2,4}\s*" + re.escape(sec) + r"[\s.]", head)
            else:
                hit = aid and f'id="{aid}"' in p
            if hit:
                j = i + 1
                while j < len(paras) and paras[j].lstrip().startswith(("#", "<a ")):
                    j += 1
                if j < len(paras):
                    paras[j] = paras[j] + "\n\n" + figure_html(n, caps[n])
                    placed.add(n)
                break
    src = "\n\n".join(paras)
    # cover: take the first H1 as title; drop it from the body
    m = re.search(r"^# (.+)$", src, re.M)
    title = m.group(1).strip() if m else "รายงานฉบับสมบูรณ์"
    if m:   # the cover replaces the draft's own front block (title line up to the first "##")
        nxt = re.search(r"^## ", src[m.end():], re.M)
        src = src[:m.start()] + (src[m.end() + nxt.start():] if nxt else src[m.end():])
    md = markdown.Markdown(extensions=["tables", "toc", "attr_list", "sane_lists"],
                           extension_configs={"toc": {"toc_depth": "1-2", "title": ""}})
    body = md.convert(src)
    # promote "##" chapters to page-breaking h1 if the draft uses ## for chapters
    if "<h1" not in body:
        body = body.replace("<h2", "<h1").replace("</h2>", "</h1>").replace("<h3", "<h2").replace("</h3>", "</h2>")
    toc = md.toc
    cover = f"""<section class="cover">
<div class="kicker">รายงานการค้นคว้าอิสระ 2 (IS2) · ฉบับสมบูรณ์</div>
<h1>{title}</h1>
<div class="en">Market Window Dossier and LOE-Bench: from cross-domain patent reranking to evidence-traced review queues for generic drug entry</div>
<div class="who">นายศิริพล ศรีเฮงไพบูลย์<br>อาจารย์ที่ปรึกษา ผศ.ดร.ทัศนัย พลอยสุวรรณ<br>
สาขาวิชาปัญญาประดิษฐ์เพื่อการวิเคราะห์เชิงธุรกิจ คณะเทคโนโลยีสารสนเทศ<br>สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง</div>
<div class="note">เอกสารนี้สนับสนุนการตัดสินใจเท่านั้น ไม่ใช่ความเห็นทางกฎหมายหรือความเห็นด้านเสรีภาพในการดำเนินการ (FTO)
ผู้เชี่ยวชาญกฎหมายสิทธิบัตรเป็นผู้ให้ความเห็นต่อผลิตภัณฑ์ กิจกรรม และประเทศที่ระบุ</div>
<div class="foot">ฉบับวันที่ {date.today().day} {['','มกราคม','กุมภาพันธ์','มีนาคม','เมษายน','พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม','กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม'][date.today().month]} {date.today().year + 543}
· การลงทะเบียนล่วงหน้า doi:10.17605/OSF.IO/P2SMD</div></section>"""
    html = (f'<!DOCTYPE html><html lang="th"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style>'
            f'</head><body>{cover}<section class="toc"><h1 style="page-break-before:auto">สารบัญ</h1>{toc}</section>'
            f"{body}</body></html>")
    out_html = HERE / f"{out_stem}.html"
    out_html.write_text(html, encoding="utf-8")
    pdf = HERE / f"{out_stem}.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", out_html.as_uri()], check=True, capture_output=True, timeout=180)
    missing = sorted(set(n for n, f in FIG_FILES.items() if f) - placed)
    print(f"pdf: {pdf}  figures placed: {sorted(placed)}  not placed: {missing}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default="REPORT-TH.md")
    ap.add_argument("--out", default="MWD-REPORT-TH")
    a = ap.parse_args()
    build(a.md, a.out)
