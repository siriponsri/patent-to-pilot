"""Check a dossier's PDF against the app screen and the app's browser print (card PO-PDF, PRD R2).

For each (drug, language, horizon) it
  1. renders the PDF with product.mwd.render,
  2. opens the app on file:// at the same drug, language and horizon and reads the screen fields,
  3. fires the app's beforeprint hook and prints the page with Chrome (the browser-print path),
  4. compares drug, jurisdiction, date, horizon, version, forecast, disclaimer and open tasks, and compares the
     browser print to the PDF page by page (page count and text).
Needs Playwright, Chrome and PyMuPDF. Usage:  py -3.12 -m product.mwd.pdf_check KEY [KEY ...] [--lang th en] [--horizon 12 24]
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote

from .contract import CURRENT, DEMO, read_json
from .render import CHROME, chrome_page, queue_total, render, write_pdf

SCREEN_JS = """() => {
  const t = (s) => { const e = document.querySelector(s); return e ? e.textContent : null; };
  const all = (s) => [...document.querySelectorAll(s)].map((e) => e.textContent);
  return { name: t('.d-head h1'), meta: all('.d-meta span'), disclaimer: t('.dossier-disclaimer'),
           stats: all('#panel-decision .stats .v'), tasks: all('#panel-handoff .checklist .task-text'),
           modebar: t('.modebar'), chips: all('.chips .chip') };
}"""


def squash(text):
    """Text without any whitespace, so line breaks in a PDF do not matter."""
    return re.sub(r"\s+", "", text or "")


def pdf_text(path):
    import pymupdf

    with pymupdf.open(path) as doc:
        return [page.get_text() for page in doc]


def screen_fields(browser, key, lang, horizon, mode="current"):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(DEMO.joinpath("index.html").as_uri() + f"#mode={mode}&view=queue&lang={lang}&h={horizon}&m={quote(key, safe='')}")
    page.wait_for_selector(".d-head h1", timeout=60000)
    return page, page.evaluate(SCREEN_JS)


def browser_print(page, target):
    """Print through the app's own hook: beforeprint mounts the report, Chrome prints it, afterprint removes it."""
    page.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
    pdf = page.pdf(prefer_css_page_size=True, print_background=True)
    page.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
    target.write_bytes(pdf)


def check(playwright_browser, pdf_page, path, lang, horizon, out_dir):
    dossier = read_json(path)
    key = dossier["molecule"]["key"]
    stem = f"{path.stem.removeprefix('dossier-')}-{horizon}m.{lang}"
    pdf_file, print_file = out_dir / f"{stem}.pdf", out_dir / f"{stem}.browser-print.pdf"
    html = render(dossier, lang, None, page=pdf_page, horizon=horizon, total=queue_total(dossier, path, horizon))
    write_pdf(pdf_page, html, pdf_file)
    page, screen = screen_fields(playwright_browser, key, lang, horizon)
    browser_print(page, print_file)
    page.close()
    pages, printed = pdf_text(pdf_file), pdf_text(print_file)
    body = squash("".join(pages))
    h12 = horizon == 12
    forecast = dossier["forecast_12m" if h12 else "forecast"]
    stat = lambda i: squash(screen["stats"][i])
    version = dossier["version"]["tag"]
    rows = {
        "drug": (squash(screen["name"]), squash(screen["name"]) in body),
        "jurisdiction": (dossier["jurisdiction"], f"Jurisdiction{dossier['jurisdiction']}" in body),
        "date": (screen["meta"][0], squash(screen["meta"][0]) in body),
        "horizon": (screen["meta"][1], squash(f"{horizon} months") in body and squash(screen["meta"][1]).endswith(squash(f"{horizon}months"))),
        "version": (version, version in screen["modebar"].replace(" ", "") and squash(version) in body),
        "forecast M3": (stat(0), stat(0) in body and stat(0) == f"{forecast['m3_p_entry'] * 100:.1f}%"),
        "forecast B1": (stat(1), stat(1) in body and stat(1) == f"{forecast['b1_p_entry'] * 100:.1f}%"),
        "disclaimer": (squash(screen["disclaimer"]).removeprefix("Disclaimer")[:24] + "…",
                       squash(screen["disclaimer"]).removeprefix("Disclaimer") in body),
        "open tasks": (f"{len(screen['tasks'])} tasks", all(squash(task)[:40] in body for task in screen["tasks"])
                       and f"{len(dossier['checklist'])}inthe" in body),
    }
    same_text = [squash(a) == squash(b) for a, b in zip(pages, printed)]
    rows["browser print = PDF"] = (f"{len(printed)} pages", len(pages) == len(printed) and all(same_text))
    return {"stem": stem, "pages": len(pages), "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keys", nargs="+", help="Dossier file stems or drug keys under data/current, such as U-DKO1W9H7M1")
    parser.add_argument("--lang", nargs="+", default=["th", "en"])
    parser.add_argument("--horizon", nargs="+", type=int, default=[12, 24])
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    failed = 0
    with chrome_page(CHROME) as pdf_page:
        browser = pdf_page.context.browser
        for key in args.keys:
            path = CURRENT / f"dossier-{key.removeprefix('dossier-').removesuffix('.json')}.json"
            if not path.name.endswith("2026-11-27.json"):
                path = CURRENT / f"dossier-{key}-2026-11-27.json"
            for lang in args.lang:
                for horizon in args.horizon:
                    result = check(browser, pdf_page, path, lang, horizon, args.out_dir)
                    bad = [name for name, (_, ok) in result["rows"].items() if not ok]
                    failed += bool(bad)
                    print(f"{result['stem']}: {result['pages']} pages, " + ("PASS" if not bad else "FAIL " + ", ".join(bad)))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
