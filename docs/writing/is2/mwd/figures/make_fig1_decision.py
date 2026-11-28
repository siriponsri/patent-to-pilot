"""IS2 Figure 1: the decision at the cutoff, bridged from IS1 (designed by the main planner, 28 Nov 2026).

Print width 6.5 in = 1000 px, so 1 px = 0.468 pt; every label is >= 13 px (EN) / 19 px (TH) (>= 6 pt).
Sources: IS1 435/692 (docs/evidence-scope/00-organization.md); protocol (docs/loe-bench/PREREGISTRATION.md).
Run: python make_fig1_decision.py  -> fig1_decision_{en,th}.{html,png}
"""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"

T = {
    "en": dict(font="'Segoe UI', system-ui, sans-serif", s=15, h=17, b=19, big=46,
               is1="IS1 · PATENT SEARCH", is1a="of 692 cross-field queries:", is1b="the known target never", is1c="entered the top-100 basket",
               lesson="Lesson: choose what reaches", lesson2="the desk before ranking it",
               is2="IS2 · DRUG CASES, ON ONE CUTOFF DATE", cut="Cutoff date", after="After the cutoff",
               b1=("Eligible", "drugs with no", "generic yet"),
               b2=("Evidence", "public by", "that date"),
               b3=("Queue", "1 in 5 slots", "floor(N/5)"),
               b4=("Dossier", "dated sources", "+ checklist"),
               out=("Outcome", "first final US", "generic approval", "in 12 or 24 months"),
               only=("used for", "scoring only"),
               score="Scoring: what share of later approvals did each queue put on the desk? (recall at 20%)"),
    "th": dict(font="'TH Sarabun New', 'Sarabun', sans-serif", s=21, h=23, b=26, big=62,
               is1="IS1 · การค้นสิทธิบัตร", is1a="จาก 692 คำค้นข้ามสาขา", is1b="เอกสารเป้าหมายไม่เคย", is1c="เข้าตะกร้า 100 อันดับแรก",
               lesson="บทเรียน: เลือกสิ่งที่ขึ้นโต๊ะ", lesson2="ให้ถูกก่อนจัดอันดับ",
               is2="IS2 · กรณียา ณ วันตัดข้อมูลหนึ่งวัน", cut="วันตัดข้อมูล", after="หลังวันตัดข้อมูล",
               b1=("ยาที่เข้าเกณฑ์", "ยังไม่มี", "ยาสามัญ"),
               b2=("หลักฐาน", "ที่เผยแพร่", "ทันวันนั้น"),
               b3=("คิวทบทวน", "1 ใน 5 ช่อง", "floor(N/5)"),
               b4=("แฟ้มหลักฐาน", "แหล่งพร้อมวันที่", "รายการตรวจ"),
               out=("ผลภายหลัง", "อนุมัติยาสามัญ", "ครั้งแรกในสหรัฐฯ", "ใน 12 หรือ 24 เดือน"),
               only=("ใช้ให้คะแนน", "เท่านั้น"),
               score="การให้คะแนน: คิวแต่ละแบบนำรายการที่ต่อมาได้รับอนุมัติขึ้นโต๊ะได้กี่ส่วน (recall ที่ 20%)"),
}


def box(x, y, w, h, lines, t, fill="#ffffff", stroke="#c7cdd8", head="#1f2a44", sub="#4f5d75"):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>']
    yy = y + 34
    for i, ln in enumerate(lines):
        size = t["h"] if i == 0 else t["s"]
        wt = 700 if i == 0 else 400
        col = head if i == 0 else sub
        out.append(f'<text x="{x + 14}" y="{yy}" font-size="{size}" font-weight="{wt}" fill="{col}">{ln}</text>')
        yy += size + 8
    return "".join(out)


def svg(lang):
    t = T[lang]
    A, D, R = "#0072B2", "#1f2a44", "#D55E00"
    parts = [f'<svg viewBox="0 0 1000 470" xmlns="http://www.w3.org/2000/svg" font-family="{t["font"]}">',
             '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0,0 L10,5 L0,10 z" fill="#4f5d75"/></marker>'
             '<marker id="r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             f'<path d="M0,0 L10,5 L0,10 z" fill="{R}"/></marker></defs>']
    # IS1 inset
    parts.append('<rect x="14" y="44" width="214" height="300" rx="10" fill="#f4f6f9" stroke="#c7cdd8"/>')
    parts.append(f'<text x="28" y="34" font-size="{t["s"]}" font-weight="700" fill="#5a6580" letter-spacing="0.03em">{t["is1"]}</text>')
    parts.append(f'<text x="30" y="{106 + (6 if lang == "th" else 0)}" font-size="{t["big"]}" font-weight="700" fill="#6e6e6e">435</text>')
    parts.append(f'<text x="30" y="140" font-size="{t["s"]}" fill="{D}">{t["is1a"]}</text>')
    parts.append(f'<text x="30" y="{140 + t["s"] + 6}" font-size="{t["s"]}" fill="{D}">{t["is1b"]}</text>')
    parts.append(f'<text x="30" y="{140 + 2 * (t["s"] + 6)}" font-size="{t["s"]}" fill="{D}">{t["is1c"]}</text>')
    # basket glyph with dots outside
    parts.append('<path d="M60 250 L190 250 L176 318 L74 318 Z" fill="#ffffff" stroke="#6e6e6e" stroke-width="2"/>')
    for i in range(6):
        parts.append(f'<circle cx="{86 + i * 17}" cy="300" r="5" fill="{A}"/>')
    for (cx, cy) in [(40, 232), (210, 236), (52, 214), (198, 214), (222, 262), (30, 270)]:
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="#bdbdbd"/>')
    # lesson arrow
    parts.append('<line x1="230" y1="196" x2="268" y2="196" stroke="#4f5d75" stroke-width="1.6" marker-end="url(#a)"/>')
    parts.append(f'<text x="14" y="378" font-size="{t["s"]}" font-weight="700" fill="{A}">{t["lesson"]}</text>')
    parts.append(f'<text x="14" y="{378 + t["s"] + 6}" font-size="{t["s"]}" font-weight="700" fill="{A}">{t["lesson2"]}</text>')
    # IS2 main
    parts.append(f'<text x="276" y="34" font-size="{t["s"]}" font-weight="700" fill="#5a6580" letter-spacing="0.03em">{t["is2"]}</text>')
    xs, w, y0, h = [276, 404, 532, 660], 116, 120, 150
    names = ["b1", "b2", "b3", "b4"]
    for i, (x, n) in enumerate(zip(xs, names)):
        if n == "b3":
            parts.append(box(x, y0, w, h, t[n], t, fill=A, stroke=A, head="#ffffff", sub="#e8f1f8"))
        else:
            parts.append(box(x, y0, w, h, t[n], t))
        if i < 3:
            parts.append(f'<line x1="{x + w + 1}" y1="{y0 + h / 2}" x2="{x + w + 11}" y2="{y0 + h / 2}" stroke="#4f5d75" stroke-width="1.4" marker-end="url(#a)"/>')
    # cutoff line
    parts.append(f'<line x1="796" y1="58" x2="796" y2="352" stroke="{R}" stroke-width="2" stroke-dasharray="6 5"/>')
    parts.append(f'<text x="788" y="76" text-anchor="end" font-size="{t["s"]}" font-weight="700" fill="{R}">{t["cut"]}</text>')
    parts.append(f'<text x="808" y="76" font-size="{t["s"]}" font-weight="700" fill="{R}">{t["after"]}</text>')
    parts.append(box(808, y0, 178, h, t["out"], t, fill="#fff4ec", stroke=R))
    # scoring bar
    parts.append(f'<rect x="276" y="368" width="710" height="62" rx="8" fill="#e8f1f8" stroke="{A}"/>')
    parts.append(f'<text x="292" y="{405 + (3 if lang == "th" else 0)}" font-size="{t["h"]}" font-weight="700" fill="{D}">{t["score"]}</text>')
    # outcome feeds scoring only; queue feeds scoring
    parts.append(f'<line x1="840" y1="{y0 + h}" x2="840" y2="364" stroke="{R}" stroke-width="1.6" marker-end="url(#r)"/>')
    for k, ln in enumerate(t["only"]):
        parts.append(f'<text x="852" y="{y0 + h + 40 + k * (t["s"] + 6)}" font-size="{t["s"]}" font-style="italic" fill="{R}">{ln}</text>')
    parts.append(f'<line x1="590" y1="{y0 + h}" x2="590" y2="364" stroke="#4f5d75" stroke-width="1.4" stroke-dasharray="4 4" marker-end="url(#a)"/>')
    parts.append("</svg>")
    return "".join(parts)


def main():
    for lang in ("en", "th"):
        html = (f'<!DOCTYPE html><html lang="{lang}"><head><meta charset="UTF-8"><title>IS2 Figure 1</title>'
                '<style>@font-face{font-family:"TH Sarabun New";src:url("file:///C:/Users/User/AppData/Local/Microsoft/Windows/Fonts/THSarabunNew.ttf")}'
                '@font-face{font-family:"TH Sarabun New";font-weight:700;src:url("file:///C:/Users/User/AppData/Local/Microsoft/Windows/Fonts/THSarabunNew%20Bold.ttf")}'
                'body{margin:0;background:#fff}svg{width:1000px;height:470px;display:block}</style></head>'
                f'<body>{svg(lang)}</body></html>')
        p = HERE / f"fig1_decision_{lang}.html"
        p.write_text(html, encoding="utf-8")
        png = HERE / f"fig1_decision_{lang}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=3",
                        "--window-size=1000,470", f"--screenshot={png}", p.as_uri()], check=True, capture_output=True)
    print("ok")


if __name__ == "__main__":
    main()
