"""Render dossier JSON as Thai and English reports (HTML and Chrome PDF) in the F2 report design.

The layout lives in product/demo/assets/dossier-print.js, the same file the app runs on "Print dossier", so the
generated PDF and the browser print match. This module loads that file in headless Chrome (Playwright) and
passes it one dossier at a time. Current Track A dossiers never carry outcome fields. A historical dossier hides
its development outcome unless --reveal is given, and a revealed export is marked on every page.
"""

import argparse
from contextlib import contextmanager
from pathlib import Path
import re

from .contract import CURRENT, DEMO, read_json

CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
PRINT_JS = DEMO / "assets" / "dossier-print.js"
FONTS_CSS = DEMO / "assets" / "fonts" / "fonts.css"


@contextmanager
def chrome_page(executable=CHROME):
    if not Path(executable).is_file():
        raise ValueError(f"Chrome executable unavailable: {executable}")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(executable), headless=True,
                                             args=["--disable-gpu"])
        try:
            page = browser.new_page()
            page.set_content("<!doctype html><html><body></body></html>")
            page.add_script_tag(content=PRINT_JS.read_text(encoding="utf-8"))
            yield page
        finally:
            browser.close()


def queue_total(dossier, path, horizon):
    """Number of ranked histories in the queue that the dossier belongs to, or None when no queue file sits beside it."""
    if path is None:
        return None
    for file in Path(path).parent.glob(f"queue-{dossier['as_of']}-{horizon}m.json"):
        queue = read_json(file)
        rows = queue.get("ranked_rows") or queue.get("rows") or []
        return len(rows) if isinstance(rows, list) else rows
    return None


def horizons(dossier):
    """Horizons a dossier can be rendered for: both for a current dossier, its own for a historical one."""
    return [12, 24] if "forecast_12m" in dossier else [dossier["forecast"]["horizon_months"]]


def render(dossier, lang, alternate=None, *, page, horizon=None, reveal=False, total=None):
    """Full standalone HTML (fonts and styles inline) for one dossier, language and horizon."""
    options = {"lang": lang, "horizon": horizon, "revealed": reveal, "queueTotal": total, "alternate": alternate,
               "fontsCss": FONTS_CSS.read_text(encoding="utf-8")}
    try:
        return page.evaluate("([dossier, options]) => MWDPrint.document(dossier, options)", [dossier, options])
    except Exception as error:
        message = getattr(error, "message", str(error)).splitlines()[0]
        raise ValueError(re.sub(r"^Error: ", "", message)) from error


def write_pdf(page, html, target):
    page.set_content(html, wait_until="load")
    page.evaluate("document.fonts.ready")
    content = page.pdf(prefer_css_page_size=True, print_background=True)
    if not content.startswith(b"%PDF-"):
        raise ValueError(f"Invalid Chrome PDF: {target.name}")
    target.write_bytes(content)


def render_one(page, dossier, path, lang, horizon, target, *, pdf, reveal=False):
    horizon = horizon or horizons(dossier)[0]
    html = render(dossier, lang, None, page=page, horizon=horizon, reveal=reveal, total=queue_total(dossier, path, horizon))
    target.parent.mkdir(parents=True, exist_ok=True)
    if pdf:
        write_pdf(page, html, target)
    else:
        target.write_text(html, encoding="utf-8", newline="\n")


def render_file(page, path, output_dir, *, pdf, reveal=False):
    dossier = read_json(path)
    stem = path.stem.removeprefix("dossier-")
    many = len(horizons(dossier)) > 1
    count = 0
    for horizon in horizons(dossier):
        name = f"{stem}-{horizon}m" if many else stem
        for lang, other in (("th", "en"), ("en", "th")):
            html = render(dossier, lang, f"{name}.{other}.html", page=page, horizon=horizon, reveal=reveal,
                          total=queue_total(dossier, path, horizon))
            (output_dir / f"{name}.{lang}.html").write_text(html, encoding="utf-8", newline="\n")
            count += 1
            if pdf:
                write_pdf(page, html, output_dir / f"{name}.{lang}.pdf")
                count += 1
    return count


def dossier_path(argument):
    if argument.is_file():
        return argument
    if argument == Path(argument.name) and re.fullmatch(r"[A-Za-z0-9_-]+", argument.name):
        return CURRENT / (f"dossier-{argument.name.removeprefix('dossier-')}.json")
    return argument


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--dossier", type=Path, help="A dossier JSON path, or a drug key under data/current")
    source.add_argument("--data-dir", type=Path, default=DEMO / "data")
    parser.add_argument("--output-dir", type=Path, default=DEMO / "dossiers")
    parser.add_argument("--lang", choices=("th", "en"))
    parser.add_argument("--horizon", type=int, choices=(12, 24))
    parser.add_argument("--out", type=Path, help="Single .html or .pdf export")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--reveal", action="store_true",
                        help="Include the development outcome of a historical dossier and mark every page as revealed")
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
    try:
        with chrome_page(args.chrome) as page:
            if args.out:
                dossier = read_json(paths[0])
                render_one(page, dossier, paths[0], args.lang, args.horizon, args.out,
                           pdf=args.out.suffix.lower() == ".pdf", reveal=args.reveal)
                print(f"Rendered {args.out}")
                return
            args.output_dir.mkdir(parents=True, exist_ok=True)
            total = sum(render_file(page, path, args.output_dir, pdf=args.pdf, reveal=args.reveal) for path in paths)
    except (ImportError, ValueError) as error:
        parser.error(str(error))
    print(f"Rendered {total} files.")


if __name__ == "__main__":
    main()
