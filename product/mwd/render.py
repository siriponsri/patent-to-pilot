"""Render dossier JSON as standalone Thai and English HTML, and optionally Chrome PDFs."""

import argparse
from html import escape
from pathlib import Path

from .audit import web_url
from .contract import DEMO, DISCLAIMER, read_json

CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
CSS = """
:root { color-scheme: light; --ink:#182c34; --muted:#395863; --line:#b7c9cc; --paper:#fff; --teal:#0b675f; }
* { box-sizing:border-box; }
body { margin:0; background:#e9f2f2; color:var(--ink); font:17px/1.6 "Segoe UI", sans-serif; }
html:lang(th) body { font:23px/1.38 "TH Sarabun New", "Segoe UI", sans-serif; }
main { max-width:960px; margin:2rem auto; background:var(--paper); padding:clamp(1rem, 5vw, 4rem); }
header { border-top:6px solid var(--teal); padding-top:1rem; }
header p, nav { margin:.45em 0; }
h1, h2 { line-height:1.08; letter-spacing:-.015em; margin:.4em 0; }
h1 { font-size:2.35em; overflow-wrap:anywhere; }
h2 { font-size:1.5em; }
a { color:#085952; text-underline-offset:.15em; }
nav { display:flex; gap:.5em 1em; flex-wrap:wrap; }
section { border-top:1px solid var(--line); margin-top:1.4em; padding-top:.75em; }
.disclaimer { border-left:4px solid var(--teal); background:#eaf5f2; padding:.55em .85em; margin:1em 0; }
.claim { margin:.6em 0; }
.chip { display:inline-block; padding:.08em .45em; border:1px solid #8dafb2; border-radius:4px;
        color:#204b53; font-size:.84em; line-height:1.25; }
.unknown { background:#fff1d6; border-color:#b27b21; color:#694201; }
.facts { color:var(--muted); }
.references { font-size:.87em; }
.references li { overflow-wrap:anywhere; margin:.55em 0; }
code { font-size:.76em; overflow-wrap:anywhere; }
.outcome { border:1px solid var(--line); padding:.45em .75em; margin-top:1em; }
summary { cursor:pointer; font-weight:700; }
@page { size:A4; margin:15mm 16mm; }
@media print {
  body, html:lang(th) body { background:#fff; font-size:11pt; }
  html:lang(th) body { font-size:15pt; }
  main { max-width:none; padding:0; margin:0; }
  nav { display:none; }
  h1, h2, summary { break-after:avoid; }
  .claim, li { break-inside:avoid; }
  a { color:inherit; text-decoration:none; }
  details:not([open]) > :not(summary) { display:block; }
}
"""
LABELS = {
    "en": {
        "known": "Known", "unknown": "Unknown", "not_applicable": "Not applicable",
        "observed": "Observed", "estimate": "Estimate", "assumption": "Assumption",
        "current_lookup": "Current lookup", "retrospective_scenario": "Retrospective scenario",
        "retrospective_demand": "Retrospective demand", "FTO evaluator": "FTO evaluator",
        "R&D": "R&D", "BD": "BD", "basis": "Development only", "cutoff": "As of",
        "horizon": "months", "country": "US", "reveal": "Development outcome reveal",
        "first": "First final ANDA in window", "no_event": "No event observed in window",
        "end": "Window end", "public": "Public date or dated evidence basis", "retrieved": "Retrieved",
    },
    "th": {
        "known": "ทราบ", "unknown": "ยังไม่ทราบ", "not_applicable": "ไม่เกี่ยวข้อง",
        "observed": "ข้อมูลที่พบ", "estimate": "ค่าประมาณ", "assumption": "สมมติฐาน",
        "current_lookup": "ผลตรวจปัจจุบัน", "retrospective_scenario": "สมมติฐานย้อนหลัง",
        "retrospective_demand": "ข้อมูลความต้องการย้อนหลัง", "FTO evaluator": "ผู้ประเมิน FTO",
        "R&D": "ฝ่ายวิจัยและพัฒนา", "BD": "ฝ่ายพัฒนาธุรกิจ", "basis": "ข้อมูลชุดพัฒนา",
        "cutoff": "วันตัดข้อมูล", "horizon": "เดือน", "country": "สหรัฐอเมริกา",
        "reveal": "เปิดดูผลจริงในชุดพัฒนา", "first": "ANDA ขั้นสุดท้ายครั้งแรกในช่วงที่ประเมิน",
        "no_event": "ไม่พบเหตุการณ์ในช่วงที่ประเมิน", "end": "วันสิ้นสุดช่วงที่ประเมิน",
        "public": "วันที่เผยแพร่หรือวันที่ใช้อ้างอิง", "retrieved": "วันที่เข้าถึง",
    },
}


def render(dossier, lang, alternate, *, for_print=False):
    def esc(value):
        return escape(str(value), quote=True)

    labels = LABELS[lang]
    sources = dossier["sources"]
    numbers = {source["id"]: i for i, source in enumerate(sources, 1)}

    def citations(ids):
        return " ".join(f'<a href="#ref-{numbers[id]}">[{numbers[id]}]</a>' for id in ids)

    def claim_markup(claim):
        tags = [claim["state"], claim["kind"]]
        if context := claim.get("time_basis"):
            tags.append(context)
        chips = " ".join(f'<span class="chip {esc(tag)}">{esc(labels[tag])}</span>' for tag in tags)
        return f'<p class="claim">{chips} {esc(claim[f"text_{lang}"])} {citations(claim["source_ids"])}</p>'

    def reference_markup(source):
        title = esc(source["title"])
        if web_url(source["url"]):
            title = f'<a href="{esc(source["url"])}">{title}</a>'
        metadata = [esc(source["issuer"]), title, esc(source["version"]), esc(source["locator"])]
        for field in ("public_date", "retrieved"):
            if source[field]:
                label = labels["public" if field == "public_date" else field]
                metadata.append(f"{esc(label)} {esc(source[field])}")
        if source["sha256"]:
            metadata.append(f'<code>SHA-256 {esc(source["sha256"])}</code>')
        return f'<li id="ref-{numbers[source["id"]]}">{" · ".join(metadata)}</li>'

    def reveal_markup():
        reveal = dossier.get("outcome_reveal")
        if not reveal:
            return ""
        outcome = reveal["first_final_anda_date"] or labels["no_event"]
        state = " open" if for_print else ""
        refs = citations(reveal.get("source_ids", []))
        return (f'<details class="outcome"{state}><summary>{esc(labels["reveal"])}</summary>'
                f'<p>{esc(labels["first"])} · {esc(outcome)} {refs}<br>'
                f'{esc(labels["end"])} · {esc(reveal["window_end"])}</p></details>')

    sections = []
    for section in dossier["sections"]:
        section_id = section["id"]
        content = [claim_markup(c) for c in dossier["claims"] if c["section"] == section_id]
        if section_id == "decision":
            content.append(reveal_markup())
        elif section_id == "handoff":
            tasks = (f'<li><strong>{esc(labels[t["owner"]])}</strong> · {esc(t[f"text_{lang}"])} '
                     f'{citations(t["source_ids"])}</li>' for t in dossier["checklist"])
            content.append(f"<ol>{''.join(tasks)}</ol>")
        elif section_id == "references":
            content.append(f'<ol class="references">{"".join(map(reference_markup, sources))}</ol>')
        sections.append(f'<section id="{esc(section_id)}"><h2>{esc(section[f"title_{lang}"])}</h2>'
                        f'{"".join(content)}</section>')
    title = esc(dossier["molecule"]["display_name"])
    alternate_name = "English" if lang == "th" else "ภาษาไทย"
    status = labels["basis"] if dossier["forecast"]["status"] == "DEVELOPMENT_ONLY" else "Track A frozen"
    links = "".join(f'<a href="#{esc(s["id"])}">{esc(s[f"title_{lang}"])}</a>' for s in dossier["sections"])
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Market Window Dossier</title><style>{CSS}</style></head>
<body><main><header><p>Market Window Dossier</p><h1>{title}</h1>
<p class="facts">{esc(status)} · {esc(labels["country"])} · {esc(labels["cutoff"])}
{esc(dossier["as_of"])} · {esc(dossier["forecast"]["horizon_months"])} {esc(labels["horizon"])}</p>
<p class="disclaimer">{esc(DISCLAIMER[lang])}</p>
<nav><a href="{esc(alternate)}" hreflang="{'en' if lang == 'th' else 'th'}">{alternate_name}</a>{links}</nav>
</header>{"".join(sections)}</main></body></html>
"""


def render_file(dossier_path, output_dir, page=None):
    dossier = read_json(dossier_path)
    stem = dossier_path.stem.removeprefix("dossier-")
    for lang, other in (("th", "en"), ("en", "th")):
        filename = f"{stem}.{lang}"
        alternate = f"{stem}.{other}.html"
        html = output_dir / f"{filename}.html"
        html.write_text(render(dossier, lang, alternate), encoding="utf-8", newline="\n")
        if page is not None:
            pdf = output_dir / f"{filename}.pdf"
            page.set_content(render(dossier, lang, alternate, for_print=True), wait_until="load")
            page.evaluate("document.fonts.ready")
            content = page.pdf(prefer_css_page_size=True, print_background=True)
            if not content.startswith(b"%PDF-"):
                raise ValueError(f"Invalid Chrome PDF: {pdf.name}")
            pdf.write_bytes(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--dossier", type=Path)
    source.add_argument("--data-dir", type=Path, default=DEMO / "data")
    parser.add_argument("--output-dir", type=Path, default=DEMO / "dossiers")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--chrome", type=Path, default=CHROME)
    args = parser.parse_args()
    paths = [args.dossier] if args.dossier else sorted(args.data_dir.glob("dossier-*.json"))
    if not paths:
        parser.error("No dossier JSON files found")
    if args.pdf and not args.chrome.is_file():
        parser.error(f"Chrome executable unavailable: {args.chrome}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            parser.error("PDF rendering requires the Python playwright package")
        # A single headless Chrome session avoids Windows process and profile churn.
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=str(args.chrome), headless=True,
                                                 args=["--disable-gpu"])
            try:
                page = browser.new_page()
                for path in paths:
                    render_file(path, args.output_dir, page)
            finally:
                browser.close()
    else:
        for path in paths:
            render_file(path, args.output_dir)
    print(f"Rendered {len(paths) * 2} HTML files" + (f" and {len(paths) * 2} PDFs." if args.pdf else "."))


if __name__ == "__main__":
    main()
