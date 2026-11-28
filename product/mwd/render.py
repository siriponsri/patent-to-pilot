"""Render dossier JSON as standalone Thai and English HTML, and optionally Chrome PDFs."""

import argparse
from contextlib import contextmanager
from html import escape
from pathlib import Path
import re

from .audit import web_url
from .contract import CURRENT, DEMO, DISCLAIMER, read_json

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


def render(dossier, lang, alternate, *, for_print=False, horizon=None):
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
        for field in ("public_date", "evidence_cutoff", "retrieved"):
            if source.get(field):
                label = labels["retrieved" if field == "retrieved" else "public"]
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

    def task_markup(task):
        text = esc(task[f"text_{lang}"])
        if web_url(task.get("lookup_url")):
            text = f'<a href="{esc(task["lookup_url"])}">{text}</a>'
        if "search_terms" in task:
            unknown = labels["unknown"]
            terms = ", ".join(task["search_terms"])
            wo = ", ".join(task["wo_numbers"]) or unknown
            priority = ", ".join(task["priority_numbers"]) or unknown
            metadata = (f"คำค้น {terms} · เลข WO {wo} · เลขคำขอที่ใช้อ้างสิทธิครั้งแรก {priority}"
                        if lang == "th" else f"Search terms {terms} · WO numbers {wo} · Priority numbers {priority}")
            text += f" · {esc(metadata)}"
        return f'<li><strong>{esc(labels[task["owner"]])}</strong> · {text} {citations(task["source_ids"])}</li>'

    forecast = dossier["forecast"]
    if horizon is not None and horizon != forecast["horizon_months"]:
        if horizon != 12 or "forecast_12m" not in dossier:
            raise ValueError(f"Dossier cannot be rendered for the {horizon}-month horizon")
        forecast = dossier["forecast_12m"]
    sections = []
    for section in dossier["sections"]:
        section_id = section["id"]
        content = [claim_markup(c) for c in dossier["claims"] if c["section"] == section_id]
        if section_id == "decision":
            content.append(reveal_markup())
        elif section_id == "handoff":
            tasks = map(task_markup, dossier["checklist"])
            content.append(f"<ol>{''.join(tasks)}</ol>")
        elif section_id == "references":
            content.append(f'<ol class="references">{"".join(map(reference_markup, sources))}</ol>')
        sections.append(f'<section id="{esc(section_id)}"><h2>{esc(section[f"title_{lang}"])}</h2>'
                        f'{"".join(content)}</section>')
    title = esc(dossier["molecule"]["display_name"])
    alternate_name = "English" if lang == "th" else "ภาษาไทย"
    status = dossier.get("label", labels["basis"] if forecast["status"] == "DEVELOPMENT_ONLY" else "Track A frozen")
    version_markup = ""
    if version := dossier.get("version"):
        stamp = (f"freeze: {version['tag']} · manifest SHA-256 {version['manifest_sha256']}"
                 if version["freeze"] == "verified" else "freeze: pending")
        version_markup = (f'<p class="facts"><code>{esc(stamp)} · '
                          f'core SHA-256 {esc(version["core_manifest_sha256"])}</code></p>')
    links = "".join(f'<a href="#{esc(s["id"])}">{esc(s[f"title_{lang}"])}</a>' for s in dossier["sections"])
    if alternate:
        other_lang = "en" if lang == "th" else "th"
        links = f'<a href="{esc(alternate)}" hreflang="{other_lang}">{alternate_name}</a>{links}'
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Market Window Dossier</title><style>{CSS}</style></head>
<body><main><header><p>Market Window Dossier</p><h1>{title}</h1>
<p class="facts">{esc(status)} · {esc(labels["country"])} · {esc(labels["cutoff"])}
{esc(dossier["as_of"])} · {esc(forecast["horizon_months"])} {esc(labels["horizon"])}</p>
{version_markup}<p class="disclaimer">{esc(dossier.get("disclaimer", DISCLAIMER)[lang])}</p>
<nav>{links}</nav>
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
            write_pdf(page, render(dossier, lang, alternate, for_print=True), output_dir / f"{filename}.pdf")


def write_pdf(page, html, target):
    page.set_content(html, wait_until="load")
    page.evaluate("document.fonts.ready")
    content = page.pdf(prefer_css_page_size=True, print_background=True)
    if not content.startswith(b"%PDF-"):
        raise ValueError(f"Invalid Chrome PDF: {target.name}")
    target.write_bytes(content)


@contextmanager
def chrome_page(executable):
    if not executable.is_file():
        raise ValueError(f"Chrome executable unavailable: {executable}")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(executable), headless=True,
                                             args=["--disable-gpu"])
        try:
            yield browser.new_page()
        finally:
            browser.close()


def dossier_path(argument):
    if argument.is_file():
        return argument
    if argument == Path(argument.name) and re.fullmatch(r"[A-Za-z0-9_-]+", argument.name):
        return CURRENT / (f"dossier-{argument.name.removeprefix('dossier-')}.json")
    return argument


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--dossier", type=Path)
    source.add_argument("--data-dir", type=Path, default=DEMO / "data")
    parser.add_argument("--output-dir", type=Path, default=DEMO / "dossiers")
    parser.add_argument("--lang", choices=("th", "en"))
    parser.add_argument("--horizon", type=int, choices=(12, 24))
    parser.add_argument("--out", type=Path, help="Single .html or .pdf export")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--chrome", type=Path, default=CHROME)
    args = parser.parse_args()
    if args.out:
        if not args.dossier or not args.lang or args.out.suffix.lower() not in {".html", ".pdf"}:
            parser.error("--out requires --dossier, --lang and an .html or .pdf suffix")
    elif args.lang or args.horizon:
        parser.error("--lang and --horizon require --out")
    paths = [dossier_path(args.dossier)] if args.dossier else sorted(args.data_dir.glob("dossier-*.json"))
    if not paths:
        parser.error("No dossier JSON files found")
    if args.dossier and not paths[0].is_file():
        parser.error(f"Dossier not found: {paths[0]}")
    if args.out:
        pdf = args.out.suffix.lower() == ".pdf"
        try:
            html = render(read_json(paths[0]), args.lang, None, for_print=pdf, horizon=args.horizon)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            if pdf:
                with chrome_page(args.chrome) as page:
                    write_pdf(page, html, args.out)
            else:
                args.out.write_text(html, encoding="utf-8", newline="\n")
        except (ImportError, ValueError) as error:
            parser.error(str(error))
        print(f"Rendered {args.out}")
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        try:
            with chrome_page(args.chrome) as page:
                for path in paths:
                    render_file(path, args.output_dir, page)
        except (ImportError, ValueError) as error:
            parser.error(str(error))
    else:
        for path in paths:
            render_file(path, args.output_dir)
    print(f"Rendered {len(paths) * 2} HTML files" + (f" and {len(paths) * 2} PDFs." if args.pdf else "."))


if __name__ == "__main__":
    main()
