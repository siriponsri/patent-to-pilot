# Market Window Dossier app

The working web app of Market Window Dossier. Browse the current queue of 651 drugs (the frozen Track A forecast of 27 November 2026) or the historical time machine. Choose a forecast horizon and an as-of date, review the first-generic review queue at 1-in-5 capacity, open the seven-part dossier for a molecule, follow each statement to its dated source, and show what happened afterwards. It is decision support for BD, R&D and FTO evaluators, not legal advice or an FTO opinion.

The visual system is F2, Regulatory agency, defined in [DESIGN.md](../../DESIGN.md) and chosen by the owner on 28 November 2026. The same files run in a browser, on a static host and inside the [Windows desktop app](../desktop/README.md). The [landing page](../site/README.md) links here.

![App, Thai content, 1440 px](../screenshots/app-th.png)

## Data status

The app has two modes, shown on every view in the mode bar under the notice (mode, reference date or cutoff, horizon, source edition).

**Current queue** (default). The Track A t0 forecast as of 27 November 2026, labelled "Track A t0 forecast, outcome pending": 651 drugs at 12 and 24 months, 130 review slots per horizon, the Orange Book edition of 10 July 2026, and the freeze tag `loe-track-a-freeze-20261127`. Search a drug by active moiety or display name (partial, not case-sensitive, English names). A planned launch date picks the 12-month window (to 27 Nov 2027) or the 24-month window (to 27 Nov 2028) that covers it. A date beyond 24 months shows "Outside the forecast horizon" and no number. No forecast is computed in the app, and no outcome field exists in this data. The data is built by `product.mwd.current` ([PRODV1-DATA](../../docs/loe-bench/receipts/PRODV1-DATA.md)) and committed under `data/current/` ([PO-CURRENT](../../docs/loe-bench/receipts/PO-CURRENT.md) has the audit and the rights inventory).

**Historical time machine.** **Development data**: six example molecules at US cutoffs from 2012 to 2015, built by [PRD1](../../docs/loe-bench/receipts/PRD1.md) with the [EVP](../../docs/loe-bench/receipts/EVP.md) Thai and ASEAN evidence merged by [UIBUILD](../../docs/loe-bench/receipts/UIBUILD.md). The six cases include four catches, one false alarm and one miss. Each dossier carries the "Development data" chip. No sealed-test or Track A material is in `data/`.

## Open it

Double-click `index.html`, or open it in a browser. No server, build step or network access is needed. From `file://` the app reads `data.bundle.js` (time machine) and `data.current.bundle.js` (current queue, about 17 MB, loaded only in Current queue mode). On a web server it reads `data/index.json` and the files it lists, and falls back to the bundle.

The URL hash records the view, so a link reopens the same state:

```text
index.html#mode=current&view=queue&lang=en&h=24&q=semag&ld=2027-06-30
index.html#view=queue&lang=th&h=24&c=2014&m=U%3AU188XYD42P
index.html#view=queue&lang=en&h=24&c=2014&m=U%3AU188XYD42P&tab=patents&reveal=1
index.html#view=queue&lang=en&h=24&c=2014&m=U%3AQXS94885MZ&tab=patents&src=challenge-1
index.html#view=dossiers
```

`mode` is `current` or `history` (a link with a four-digit `c` and no `mode` opens the time machine). `q` is the search text and `ld` the planned launch date (current mode only). `view` is `queue`, `dossiers`, `sources` or `settings`. `tab` is one of `decision`, `market`, `competition`, `patents`, `thai_asean`, `handoff` and `references`. `reveal=1` shows the outcome, `show=all` lists every ranked molecule, and `src` highlights one source.

## What is on screen

| Region | Contents |
|---|---|
| Top bar | Queue, Dossiers, Sources and Settings views, and the TH/EN content toggle |
| Notice | "Decision support only. Not legal advice or an FTO opinion." It is always visible. |
| Review queue | Horizon, as-of and show filters, the ranked table (rank, molecule, M3) and the review-capacity divider. After **Show outcome**, an Outcome column marks catches, misses and molecules with no event. |
| Dossier | Breadcrumb, molecule name, **Show outcome** and **Print dossier**, chips, and seven tabs: Decision summary, Market window, Competition, Patents, Thailand and ASEAN, FTO hand-off and References. Each tab has a stats row and a statements table with Status and Source. |
| Sources | Numbered sources cited in the open tab, with issuer, edition, publication date, locator, retrieval date, SHA-256 and link. Selecting a citation highlights the source and the statements that cite it. |

Headings, navigation, labels and buttons are English. Statements, checklist items and notes follow the TH/EN toggle, Thai by default, and `<html lang>` follows the content language. Settings, the language choice and checklist ticks are stored in this browser only.

**Keyboard.** Arrow keys, Home and End move through the queue when it has focus. Alt+Down and Alt+Up open the next or previous molecule that has a dossier. Arrow keys move between tabs, and Alt+1 to Alt+7 open a section. Ctrl+P prints the open dossier with every section expanded.

**Layouts.** Three columns from 1280 px. Between 1024 and 1279 px the sources panel moves below the dossier. Below 1024 px the regions stack.

## Refresh the data

```powershell
py -3.12 -m product.mwd.build     # PRD1 builder; needs the private inputs under _private_artifacts
py -3.12 -m product.mwd.audit     # claim traceability and as-of dates
python product/demo/bundle.py     # writes data/index.json and data.bundle.js
py -3.12 -m product.mwd.current --out <new dir> --verified-freeze-tag loe-track-a-freeze-20261127 --verified-freeze-manifest loe-bench/data/TRACKA_FREEZE_MANIFEST.json   # current queue; needs the private inputs
python product/demo/bundle.py --current   # writes data.current.bundle.js from data/current/
python product/demo/fonts_css.py  # only after replacing a font file
```

`bundle.py` uses `data/` when it holds dossier files, and `fixtures/` otherwise (`--source fixtures` forces the old FIXTURE set). Commit the regenerated `data/index.json` and `data.bundle.js` with the data.

## Files

| File | Purpose |
|---|---|
| [`index.html`](index.html) | Page shell |
| [`styles.css`](styles.css) | Tokens and layout from DESIGN.md, responsive and print rules |
| [`app.js`](app.js) | Data loading, hash state, queue, dossier, sources, views, checklist storage |
| [`bundle.py`](bundle.py) | Builds `data/index.json` and `data.bundle.js`; `--current` builds `data.current.bundle.js` |
| `data/current/` | Current queue: 2 queue files, 651 dossiers, `index.json` (frozen Track A, outcome pending) |
| [`fonts_css.py`](fonts_css.py) | Inlines the self-hosted fonts into `assets/fonts/fonts.css` for the app and the landing page |
| `assets/fonts/` | Source Sans 3 and Noto Sans Thai (SIL OFL 1.1), with licence files |
| `assets/logo.svg` | Logo, refined for F2 |
| `fixtures/` | The earlier FIXTURE data set (synthetic), kept for tests of the loader |

## Deploy

The folder is a static site with relative paths. Publish `product/` so that `site/` and `demo/` sit side by side, because the landing page links to `../demo/index.html`. Publishing makes the data public, so only open data may be deployed: the development data and the frozen Track A t0 forecast in `data/current/` (rights inventory in the [PO-CURRENT receipt](../../docs/loe-bench/receipts/PO-CURRENT.md)). Protected test material, sealed outcomes and Track A outcomes must never go into `data/`.

## Limits

- Historical dossiers are development examples. The current queue holds only the frozen t0 forecast: no new forecast is computed, and Thai status stays unknown. The prospective product (molecule, dosage form, jurisdiction and launch date as inputs) is not built.
- Thai patent and registration status stays "verify" until a person checks the registers.
- Accessibility was checked with axe-core and keyboard tests, not with a screen-reader user study.
