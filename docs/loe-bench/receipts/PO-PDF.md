# PO-PDF receipt

Product Owner card PO-PDF (R2 of the [PRD](../../product/prd/PRD-MWD-v1.md)). Executed by Claude Sonnet 5.5 on 28 November 2026 on branch `loe/PO-PDF`, cut from `research/loe-bench` at `1ff2db22`. The main planner reviews. Nothing was merged.

## Result

**PASS, with open issues listed below.** The dossier print and PDF now use one report layout in the F2 "Regulatory agency" style. Page one is the decision summary. The seven sections follow in the app's order, and the long statement, checklist and source tables move to appendices. The app's **Print dossier** (and Ctrl+P and the browser menu) prints the same layout as the generated PDF. A current export never carries an outcome field. A historical export hides its development outcome unless asked, and a revealed export is marked on every page. No pipeline data (`product/mwd` builders and adapters) was changed.

## Decision

One implementation, not two. The layout is `product/demo/assets/dossier-print.js`, a pure function from a dossier JSON to HTML. The app runs it on `beforeprint`. `product/mwd/render.py` loads the same file in headless Chrome for the PDF and HTML files. So screen print and PDF cannot drift, and the parity check below compares real output. The cost: HTML rendering now needs Playwright and Chrome (before, only PDFs did).

## What changed

| File | Change |
| --- | --- |
| `product/demo/assets/dossier-print.js` | New. The report layout (DESIGN.md tokens, Source Sans 3 and Noto Sans Thai, English headings and labels, TH or EN body), page-one decision summary, appendices, running header and footer with page numbers (`@page` margin boxes), reveal rules, mount and unmount for the app. Scoped under `.pd-doc` so the app's styles do not leak in. |
| `product/mwd/render.py` | Rewritten around the shared layout. Same CLI, plus `--reveal`. A current dossier renders both horizons (`<drug>-12m`, `<drug>-24m`). `render()` now takes a Chrome `page`. |
| `product/mwd/pdf_check.py` | New. Renders the PDF, reads the app screen on `file://`, fires the app's `beforeprint` hook and prints with Chrome, then compares the fields and the two PDFs page by page. |
| `product/mwd/tests/test_dossier.py` | The three old render tests replaced by five that run the real renderer (skipped when Chrome or Playwright is missing). |
| `product/demo/app.js`, `index.html`, `styles.css` | Disclaimer block on every dossier (screen and PDF now show the identical fixed text), `beforeprint` and `afterprint` hooks that mount the report, the new script tag. |
| `product/demo/README.md`, `docs/product/PRD1.md`, `docs/product/prd/PRD-MWD-v1.md` | Print and PDF section, render commands, status row. |
| `product/demo/dossiers/current-samples/` | 6 sample PDFs (see below). |
| `product/screenshots/po-pdf-*.png` | 9 PNGs of pages (see below). |

Not changed: `product/mwd` builders, adapters, schema, `data/`, the 651 current dossiers, `tests/`, `loe_bench/`.

## Page one and sections

Page one (always one page, followed by a forced page break): drug, jurisdiction, as-of date, horizon with its end date, mode label ("Track A t0 forecast, outcome pending" or "Development data"), M3 and B1 forecast, queue position of N and capacity, statements to verify, the forecast event (first final US generic approval, not launch, demand or Thai permission), uncertainty (the registered test: M3 found 66.85% with precision 26.62%, always together; outcomes pending until the scorer runs in November 2027 and 2028), next action with its owner, version (freeze tag and manifest digest), open tasks, and the fixed disclaimer (Thai text in TH, the English equivalent in EN, both from `docs/loe-bench/ENDGAME-PLAN.md` and `contract.py`).

Sections 1 to 7 keep the app's order (Decision summary, Market window, Competition, Patents, Thailand and ASEAN, FTO hand-off, References). A section keeps 8 statements in the body; the rest go to **Statements continued**. The FTO hand-off keeps every agency lookup (Thai DIP, ASEAN IP, Thai FDA NDI, regulators: search terms, WO numbers, priority numbers, agency, owner, status "unknown" when unverified) and 6 other tasks; the rest go to **Further checklist items**. References show the table inline up to 12 sources, else an appendix **Sources** with the full SHA-256. Runs of citations print as ranges such as [28–31].

## Commands and outputs

```powershell
py -3.12 -m product.mwd.render --dossier product/demo/data/current/dossier-U-DKO1W9H7M1-2026-11-27.json --lang th --horizon 24 --out <file>.pdf
py -3.12 -m product.mwd.pdf_check <16 drug stems> --out-dir <scratch>      # 16 drugs x 2 horizons x TH and EN
py -3.12 -m pytest product/mwd/tests
```

| Step | Result |
| --- | --- |
| `py -3.12 -m pytest product/mwd/tests` | **PASS, 20 passed**, exit 0 (includes the 651-dossier schema validation and the 5 render tests). |
| `pdf_check` over 16 drugs, both horizons, TH and EN | **64 of 64 combinations PASS**, exit 0. Each runs ten checks (the nine rows below, with the forecast counted as M3 and B1 separately), including the browser print against the PDF. |
| Automated page scan of the final PDFs (70 PDFs, 956 pages: the 64 renders and the 6 samples) | 0 pages with under 60 characters of body text, 0 headings left alone at the foot of a page, 0 title lines ending in one short word. An earlier run found one near-empty page (a single pointer line spilling over); it is fixed with `break-before: avoid` and the scan above ran after the fix. |
| Current outcome rule | `render` raises "A current export never contains outcome fields" for a current dossier with `--reveal` or with an `outcome_reveal` object (tested). |
| Historical rule | Hidden by default: the Moxifloxacin 2014 PDF has no "2014-02-18" and no outcome text. Revealed: the date, the Outcome section, "Revealed export" chip, and "REVEALED: development outcome shown" in the header of every page. |

## Page counts

The 24-month Thai and English exports with the old renderer (HEAD, same machine, TH Sarabun New installed) against the new one. The new count is for the same 24-month export. The 12-month and 24-month counts are equal for every drug here, because only the forecast statements differ.

| Drug | 12m TH | 12m EN | 24m TH | 24m EN | Old 24m TH / EN | Screen, PDF, print check |
|---|---|---|---|---|---|---|
| Semaglutide (`U-53AXN4NNHX`) | 30 | 31 | 30 | 31 | 59 / 51 | PASS |
| Dolutegravir (`U-DKO1W9H7M1`) | 9 | 9 | 9 | 9 | 11 / 9 | PASS |
| Vortioxetine (`U-3O2K1S3WQV`) | 25 | 25 | 25 | 25 | 45 / 38 | PASS |
| Teduglutide (`U-7M19191IKG`) | 5 | 5 | 5 | 5 | 4 / 4 | PASS |
| Alogliptin (`U-JHC049LO86`) | 7 | 7 | 7 | 7 | 6 / 5 | PASS |
| Delafloxacin (`U-6315412YVF`) | 8 | 8 | 8 | 8 | not rendered | PASS |
| Belinostat (`U-F4H96P17NZ`) | 4 | 4 | 4 | 4 | not rendered | PASS |
| Naloxegol (`U-44T7335BKE`) | 5 | 5 | 5 | 5 | not rendered | PASS |
| Rotigotine (`U-87T4T8BO2E`) | 10 | 10 | 10 | 10 | not rendered | PASS |
| Ixazomib (`U-71050168A2`) | 8 | 8 | 8 | 8 | not rendered | PASS |
| Fluciclovine F-18 (rank 130, boundary) (`U-38R1Q0L1ZE`) | 7 | 7 | 7 | 7 | not rendered | PASS |
| Lenvatinib (`U-EE083865G2`) | 10 | 10 | 10 | 10 | not rendered | PASS |
| Patiromer (`U-1FQ2RY5YHH`) | 9 | 9 | 9 | 9 | not rendered | PASS |
| Dabrafenib (24m rank 130, boundary) (`U-QGP4HA4G1B`) | 11 | 11 | 11 | 11 | not rendered | PASS |
| Sulfur hexafluoride microspheres (key without a moiety ID, rank 129 at 12m) (`SULFUR-HEXAFLUORIDE-LIPID-TYPE-A-MICROSPHERES`) | 5 | 5 | 5 | 5 | 4 / 4 | PASS |
| Largest dossier (1,005 statements, 1,000 sources) (`U-OYN3CCI6QE`) | 67 | 67 | 67 | 67 | 150 / 127 | PASS |

- The export the PRD calls "~59 pages in Thai" is Semaglutide: **59 pages before, 30 now** (English 51 before, 31 now). The largest dossier went from 150 to 67 pages. Range over the 64 renders: 4 to 67 pages.
- Small dossiers grew by one page where page one now stands alone (Teduglutide, Alogliptin, Sulfur hexafluoride). That is the cost of a one-page decision summary.
- Most of the remaining length is the appendix of a few large dossiers: repeated Orange Book rows (one statement and one source each). Shortening that needs grouped statements from the pipeline, which this card may not change.

## Parity check (screen, PDF, browser print)

`pdf_check` reads the screen fields from the app DOM (current mode, same drug, language and horizon), then looks for each in the PDF text. Example for Dolutegravir, 24 months, TH (the same nine rows passed for all 64 renders).

| Field | Screen (app) | PDF | Result |
| --- | --- | --- | --- |
| Drug | `Dolutegravir` (h1) | page one title | match |
| Jurisdiction | `US` | `Jurisdiction US` | match |
| Date | `As of 27 Nov 2026` | same | match |
| Horizon | `24 months` | `24 months (to 27 Nov 2028)`; the screen has no end date | match (PDF adds the end date) |
| Version | mode bar `Freeze tag loe-track-a-freeze-20261127` | `Freeze tag loe-track-a-freeze-20261127 (verified) · manifest SHA-256 8a78b318a8791649…`, full digests in the last appendix | match |
| Forecast | M3 `48.5%`, B1 `28.0%` (equal to the data) | same | match |
| Disclaimer | `.dossier-disclaimer`, the fixed Thai text (new on screen) | same text, verbatim | match |
| Open tasks | 9 checklist rows | 9 tasks, text of each present, `9 of 9 in the FTO hand-off checklist` | match |
| Browser print vs PDF | `beforeprint` hook, Chrome print | PDF | same page count and same text on every page |

Wording differences that are by design: the screen lets you tick tasks (stored in the browser only), so an in-app print shows ticked boxes and "N open of M". The PDF file has no ticks, so every task is open.

## Screenshots

All are PNG renders of PDF pages from PyMuPDF (75 dpi), except the first. Each was opened and looked at.

| File | State |
| --- | --- |
| `po-pdf-app-dossier-th-1440.png` | The app screen with the new disclaimer block (Dolutegravir, 24 months, TH) |
| `po-pdf-p1-dolutegravir-24m-th.png` | Page one, TH, rank 1 |
| `po-pdf-p1-semaglutide-12m-th.png` | Page one, TH, the old 59-page case |
| `po-pdf-appendix-statements-semaglutide-12m-th.png`, `po-pdf-appendix-sources-semaglutide-12m-th.png` | Appendix pages (statements; sources with SHA-256) |
| `po-pdf-p1-fluciclovine-boundary-12m-th.png` | Page one, boundary case (rank 130 of 651, 12 months) |
| `po-pdf-p1-history-hidden-th.png` | Historical Moxifloxacin 2014, outcome hidden |
| `po-pdf-p1-history-revealed-en.png`, `po-pdf-history-revealed-outcome-en.png` | Same, revealed: chip, header and the Outcome section |

Also looked at during the work (not kept): page one of Semaglutide EN, Vortioxetine TH and Sulfur hexafluoride TH (the unknown-identity case), pages 2 to 4 and the checklist page of Semaglutide TH, a Dolutegravir TH checklist page at 110 dpi (Thai glyphs, tone marks and vowels render correctly, no tofu).

## Samples committed (6 files, 3.7 MB)

`product/demo/dossiers/current-samples/`: `dolutegravir-rank1-24m.th.pdf`, `dolutegravir-rank1-24m.en.pdf`, `semaglutide-rank1-12m.th.pdf`, `fluciclovine-boundary130-12m.th.pdf`, `history-moxifloxacin-2014-hidden.th.pdf`, `history-moxifloxacin-2014-revealed.en.pdf`. No hundreds of generated files; the 128 older historical files under `product/demo/dossiers/` are untouched.

## Open issues

1. **Early reveal in the app's References tab (historical mode, before this card).** The References table lists every source, including the outcome source whose locator reads "ORIG/AP 2014-02-18", while "Show outcome" is off. I confirmed it in headless Chromium. The print and PDF leave that source out until the reveal, but the screen still shows it. A fix (hide `outcome_reveal.source_ids` until revealed, keeping the numbering) belongs with R6 (PO-WOW); I did not touch it.
2. **128 older historical HTML and PDF files** under `product/demo/dossiers/` were made by the previous renderer and show the outcome by default in the PDF. Regenerating them would rewrite 128 tracked files, so I left them. The planner should choose: regenerate hidden, or delete.
3. **Menu print and other browsers.** Page numbers and the running header use `@page` margin boxes (Chromium 131 or later; checked on Chrome 158). Firefox and Safari were not tested. The Tauri desktop app (WebView2, Chromium) was not rebuilt or tested; `prepare-frontend.mjs` copies `assets/`, so the new script goes with it, but the installer must be rebuilt.
4. **Appendix length** for a few large dossiers (largest 67 pages) because the data has one statement and one source per Orange Book row. Needs grouping in the pipeline.
5. **English date format on page one for TH too**, to match the screen (`27 Nov 2026`). Thai Buddhist-era dates appear only inside body sentences.
6. **"Fluciclovine f-18"** and similar: the display-name tidy (shared with the app) lowercases the suffix. Same on screen.
7. **Scores are native model scores** shown as percentages with the app's labels; page one says "First generic within N months (M3)" as the app does. The claim text still says "native score". A wording review is for the planner.
8. **"Key assumption" is a dash** for all current dossiers (the data has no assumption claim in the current set).
9. **`render()` needs Chrome now.** HTML rendering was stdlib-only. The PRD1 README and the app README say so.
10. No accessibility or tagged-PDF work (R11 is PO-QA). Chrome writes an untagged PDF.

## Next action

The main planner reviews `loe/PO-PDF`. Then PO-WOW (R6 reveal rule, issue 1 above) and PO-QA (R11) can start from this layout. The Orchestrator owns the lane HANDOFF and MEMORY at integration.
