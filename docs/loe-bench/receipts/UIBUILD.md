# UIBUILD | Market Window Dossier production UI (F2 Regulatory agency)

## Result

**PASS for the web app and the landing page. PASS for the desktop app: the Windows NSIS installer built, and the built program opened offline and rendered the app.** Claude executed this card on 28 November 2026 on branch `loe/UIBUILD`, cut from `research/loe-bench` at `35e123a3`. It replaces the visual layer of the PRD2C demo with the owner-chosen F2 design ([DESIGN.md](../../../DESIGN.md), [PRODUCT.md](../../../PRODUCT.md), approved sample `docs/product/design/F2-agency.html`). It also adds a landing page and a Tauri v2 Windows desktop app.

| Deliverable | Path | State |
|---|---|---|
| Web app | [`product/demo/`](../../../product/demo/README.md) | Built on real development data (32 dossiers, 6 queues), checked in headless Chromium at 1440, 1366, 1280, 1100 and 1024 px |
| Landing page | [`product/site/`](../../../product/site/README.md) | Built, Thai and English |
| Desktop app | [`product/desktop/`](../../../product/desktop/README.md) | Built. NSIS installer 1,930,722 bytes, outside Git |
| Screenshots | [`product/screenshots/`](../../../product/screenshots/) | 9 images, each opened and inspected |
| PRD1 exports | `product/demo/dossiers/` | Re-rendered after the data change (`py -3.12 -m product.mwd.render --pdf`: 64 HTML and 64 PDF). Their visual design is still PRD1's. |

The app keeps PRD2C's working logic: index or bundle loading, URL-hash state, the outcome reveal, checklist storage and print. Its rendering is new. Data shown are development data (US cutoffs 2012–2015) and carry the "Development data" chip. No protected test output was opened. Only the committed `SCORE_CPRIME_RESULTS.json` and the SCORE receipt were used for the published figures.

## What was built

**Web app.** The app follows the layout in DESIGN.md. A navy top bar holds Queue, Dossiers, Sources, Settings and the TH/EN toggle. An amber "Decision support only. Not legal advice or an FTO opinion." notice stays visible under it. The workspace has three columns:

1. **Review queue.** Horizon, As of and Show filters (molecules with a dossier, or all 533–545 ranked molecules), a rank, molecule and M3 table, and a navy "Review capacity: 108 of 544 (1 in 5)" divider.
2. **Dossier.** Breadcrumb, a 36 px H1, **Show outcome** and **Print dossier** in the header, chips (In or Outside review queue, Development data) and seven tabs in the required order. Each tab has a stats row and a statements table with Status and Source columns. The Decision summary adds the next action, the key assumption and open items by section. FTO hand-off adds the evaluator checklist (ticks saved in local storage). References lists every source.
3. **Sources.** Numbered entries cited in the open tab, with issuer, edition, publication date, locator, retrieval date, short SHA-256 with a copy button, and link. Selecting a citation highlights the source and every statement that cites it.

**Show outcome** adds an Outcome block below the header (what happened with its source, queue result as Caught, Missed or No event, this queue's capture for M3 and B1, and a development-data note). It also adds an Outcome column to the queue. The B1 capture is computed in the app at the same capacity, sharing slots among molecules tied at the capacity line. That expected-value rule follows the registered analysis. Other states: loading, a "no dossier" panel with a recovery button, a data-error panel naming the fix (`python product/demo/bundle.py`), hover, and a 2 px focus ring with a 2 px offset. The Dossiers, Sources and Settings views use the full width beside the queue. They hold a filterable register of all 32 dossiers, a filterable source register with cited-by counts, and the language, review-capacity, saved-ticks, keyboard and data settings.

**Landing page.** The page has a navy top bar (Overview, Method, Evidence, Download, TH/EN) and a navy-2 workflow-stage bar (Before development, Patent review, Thailand and ASEAN, Accuracy testing) that marks the current section while scrolling. Below them are the hero (H1, plain lead, **Open the app**, **Download for Windows**) and the Evidence summary panel. The sections are How it works, What the dossier contains (including Thailand and ASEAN), How accuracy is tested, Limits and Download, followed by the amber notice and a footer with the KMITL attribution, OSF DOI, GitHub link and licences.

**Published figures and their status.**

| Figure | Status shown | Source |
|---|---|---|
| 66.85% vs 46.48% of upcoming first generic approvals at a 20% review budget, 24 months; +20.37 pp, 95% CI +14.37 to +26.16 | Confirmed | SCORE H1; [OSF](https://doi.org/10.17605/OSF.IO/P2SMD) |
| Evidence graph over a matched model without it: +1.36 pp, 95% CI −2.20 to +3.01 | Not confirmed | SCORE H2 |
| At least three approved generic applicants within 36 months: 79.8% vs 49.7% (+30.11 points) | Exploratory | SCORE C3 |
| Track A frozen before 31 January 2027 | Pending | [PLAN](../PLAN.md) |
| Thai family traces 17/17; Thai members confirmed 0/17 | Development evidence pilot | [EVP](EVP.md) |

No customers, prices, deployments or comparative product claims appear anywhere.

## Decisions

- **EVP evidence merged into the builder.** `product/mwd/build.py` looked for `docs/product/evidence/U:KEY.json` or a slug, but EVP wrote URL-encoded names (`U%3AKEY.json`). The builder therefore used its "Thai status unknown" fallback for all 32 dossiers. The builder now resolves the URL-encoded name and merges, per dossier, only items whose cited sources were public on or before that dossier's as-of date. The merged items are the EVP Thailand and ASEAN claims, the ranked patent checklist (`check-*`) and the Thai checklist (`th-*`). EVP's patent-section claims restate Orange Book rows the builder already lists. Its restriction review uses documents from the outcome window. Both stay out. The contract allows three checklist owners, so the merge maps EVP's Patent reviewer and Thai patent reviewer to FTO evaluator and its Thai regulatory reviewer to R&D. The contract and schema are unchanged. No other builder logic changed. The rebuild produced 32 dossiers and 6 queues, and the audit passed 1,789/1,789 traceable claims (1,757 hash-backed) with no errors. Queue files are unchanged.
- **Data index.** PRD1 writes no `data/index.json`, and its queues use `ranked_rows`. `bundle.py` now writes the index from the data files. The app reads both `ranked_rows` and the older fixture `rows`. On HTTP the loader tries `data/index.json`, then the bundle. Fixtures load only through `bundle.py --source fixtures`.
- **Fonts inlined.** Chromium refuses web fonts from `file://` pages (CORS, seen on the first render). `fonts_css.py` therefore inlines the self-hosted woff2 files into `assets/fonts/fonts.css` as data URIs for the app and the landing page. The woff2 sources and OFL texts sit beside it. Thai text falls through from Source Sans 3 to Noto Sans Thai by `unicode-range`. PRODUCT.md still mentions TH Sarabun New, while DESIGN.md and the card specify Noto Sans Thai, which this card follows.
- **Interface language.** Headings, navigation, labels, table headers, buttons and status column names are English. Statements, checklist items, notes, outcome text and status-tag text follow the content language, and `<html lang>` follows it. English UI regions carry `lang="en"`.
- **Logo refined for F2.** Navy square with a 10/96 radius, a white page with a folded corner, a navy trend line and a light-blue launch-window band. The teal accent and circle are gone. The refined file is `product/demo/assets/logo.svg` and `product/site/assets/logo.svg`. `docs/assets/logo.svg` is unchanged.
- **Tabs at narrow widths.** All seven tabs stay on one row from 1024 to 1440 px. The side columns and tab padding step down at 1399 and 1319 px. Between 1024 and 1279 px the Sources panel stacks below the dossier.
- **Stats row and outcome block.** The detector flagged the bordered stats box and the bordered Outcome block inside the dossier panel as cards inside a card. Both now use a 2 px navy top rule and a 1 px bottom rule.
- **Superseded screenshots removed.** The seven PRD2C screenshots of the rejected UI were deleted from `product/demo/screenshots/`. The PRD2C receipt still describes them as history.

## Toolchain and licences

| Item | Version | Licence | Source and SHA-256 |
|---|---|---|---|
| Source Sans 3 (variable, latin and latin-ext) | Fontsource `@fontsource-variable/source-sans-3` 5.3.1 | SIL OFL 1.1 | npm registry. `source-sans-3-latin-wght-normal.woff2` 19143dca075972bc84e3fd9eab7416dd40cc565dccb2435a044bdfabe060c7d5; `source-sans-3-latin-ext-wght-normal.woff2` a85a7459bdb3cdc1136751e151a506bae653fc29ada3ca86237477df6f1b59e6 |
| Noto Sans Thai (variable, thai) | Fontsource `@fontsource-variable/noto-sans-thai` 5.3.0 | SIL OFL 1.1 | npm registry. `noto-sans-thai-thai-wght-normal.woff2` 1f5a173641bbcb3ca4fb0a986858b6b07f8cd5dd2ed61236b40548c7a3c7292f |
| Rust (GNU host) | rustc 1.100.1, cargo 1.100.1, stable-x86_64-pc-windows-gnu | MIT or Apache-2.0 | `rustup-init.exe` from static.rust-lang.org, f6289656ce42e1099f3cbc6f10ef6321dfde54773faf599dd36fd3b1f07d9103, installed user-level to `%USERPROFILE%\.cargo` without changing PATH |
| MinGW-w64 (gcc, windres, ar) | WinLibs GCC 16.2.0, MinGW-w64 UCRT 14.0.0 r3 | GCC GPL-3.0 with runtime exception; MinGW-w64 runtime ZPL and public domain; binutils GPL-3.0 | github.com/brechtsanders/winlibs_mingw release `16.2.0posix-23.1.3-14.0.0-ucrt-r3`, zip 3c69305081e4a647144339a936244fcf7d3d9e558319e1ad7be2cd2886d4b6a1, unpacked to `%USERPROFILE%\.local\winlibs` |
| Tauri CLI | `@tauri-apps/cli` 2.12.6 (npm) | Apache-2.0 or MIT | `product/desktop/package-lock.json` |
| Tauri runtime | tauri 2.12.7, tauri-build 2.7.6, wry 0.57.4, webview2-com 0.39.1 (433 crates) | Apache-2.0 or MIT | `product/desktop/src-tauri/Cargo.lock` |
| NSIS | 3.13 and nsis_tauri_utils 0.5.3, fetched by the Tauri bundler with hash validation | zlib/libpng | tauri-apps/binary-releases |
| axe-core (checks only) | 4.14.1 | MPL-2.0 | npm registry, session scratch, not committed |

No Visual Studio, administrator rights, paid service or GPU were used. The machine had no Rust toolchain or MSVC build tools at the start, so the GNU host and a user-level MinGW replaced them.

## Desktop build

| Item | Value |
|---|---|
| Command | `npx tauri build` in `product/desktop`, PATH prefixed with `%USERPROFILE%\.cargo\bin` and the WinLibs `mingw64\bin` |
| Installer | `C:/Users/User/Desktop/myProject/_private_artifacts/mwd-desktop/Market Window Dossier_0.1.0_x64-setup.exe` (copied from `src-tauri/target/release/bundle/nsis/`) |
| Size | 1,930,722 bytes (1.84 MiB) |
| SHA-256 | `06e44808097498e060b50060f3473ad3a8ab1d304baad7730137bee380693d43` |
| Program | `market-window-dossier.exe`, SHA-256 `35e0f2e44329e80dd8501bd37946f7f47a830905bffc80aae30b5cba1c6e0e75` |
| Settings | Window title "Market Window Dossier", 1440 × 900 default, minimum 1280 × 800, NSIS per-user install, WebView2 download bootstrapper, CSP limited to bundled files and inline fonts |
| Build times | First build 7 min 33 s (warm-up, older frontend). Final rebuild 1 min 20 s. All five builds exited 0. |
| Linker warning | `ld.exe: .rsrc merge failure: multiple non-default manifests`. The GNU linker kept one of the two manifests (MinGW default and Tauri's). The program still starts, shows its icon and title, and renders. |
| Run check | The built program was started directly from `target/release` (the installer itself was not run, to leave this computer's Start menu unchanged). It opened a native window titled "Market Window Dossier", loaded the bundled data without network access, rendered both fonts under the CSP and was closed after the screenshot. |
| Minimum size | Configured in `tauri.conf.json`. A programmatic `MoveWindow` to 900 × 600 went through, because that call bypasses the minimum tracking size. A drag resize was not tested. |

## Checks

| Check | Result |
|---|---|
| `py -3.12 -m product.mwd.build` | PASS, 32 dossiers and 6 queues |
| `py -3.12 -m product.mwd.audit` | PASS, 1,789/1,789 claims traceable, 1,757 with a source hash, no errors |
| `python product/demo/bundle.py` | 38 files bundled, `data.bundle.js` 2,602,392 bytes, SHA-256 8de2dec64ed2f8ef4231de5a4ffacb8f4e3d61a7b11768128b552e7425432df7; `data/index.json` 6d422a11550991bad31741f8f5c9442d6eac6ee24235c20bba3cdb7971c3dd51 |
| `py -3.12 -m pytest product/mwd/tests -q` | First run after the merge: 1 failure, because `mwd.dossier.v1` allows only the owners FTO evaluator, R&D and BD, while EVP uses Patent reviewer, Thai patent reviewer and Thai regulatory reviewer. After the owner mapping below and a rebuild: 8 passed |
| Impeccable detector, static scan of all six changed UI files | First run: 1 contrast and 9 cramped-padding warnings on the landing page. Fixed the tag padding, gave the navy bars an explicit background and set an explicit hero inset. The last static finding, "hero children flush", comes from the unresolved `max()` inset. The rendered scan below does not report it. |
| Impeccable detector, rendered | Scans called through `impeccable.cmd` passed the URL to `cmd.exe`, which cut it at the first `&` (and ran `view` as a command). Those first scans therefore covered only each page's default state: the landing page in Thai and English, and the app's default dossier. They found Thai stragglers, a card in a card (stats row) and a 98-character line on the landing page, all fixed. The rescans used the `sh` launcher with the full URL. They then found the Outcome block nested as a card and an 88-character lead in the Sources view, both fixed. Final rescan of ten states with no findings: 1440×900 Moxifloxacin with outcome (EN), Solifenacin with outcome (TH), Sources view, Dossiers view, Settings view, Bimatoprost Thailand and ASEAN (EN) and Patents (TH), the no-dossier state; 1280×800 FTO hand-off; 1024×768 References. |
| axe-core 4.14.1, WCAG 2.0/2.1/2.2 A and AA tags, 11 page states | One serious finding on the first run: `label-content-name-mismatch` on 538 queue buttons, whose `aria-label` omitted the visible "No dossier" text. The fix drops `aria-label`, uses the visible name, and adds screen-reader-only rank, M3 and queue status. Final: 0 violations on every state. Incomplete items are colour-contrast cases axe could not compute (text over the select arrow image and highlighted rows) and the hidden Outcome header. |
| Contrast computed from the tokens (WCAG 2 formula) | Ink on page 14.2:1, muted on white 6.0:1, muted on page 5.5:1, muted on selected row 5.2:1, link on white 6.7:1, link on selected row 5.8:1, amber on amber-bg 5.4:1, green on green-bg 5.7:1, red on red-bg 5.7:1, bar text on navy 10.5:1, on navy-2 8.8:1. All text pairs pass AA. |
| Keyboard and state, Playwright | Arrow keys in the queue, Alt+Down, Alt+6, arrow keys between tabs, checklist tick saved across reload, TH→EN switch updates `<html lang>`, Show outcome sets `aria-pressed`, horizon change, Dossiers filter and open. No page errors. |
| Print | Print emulation renders the notice, header, outcome and all seven sections expanded, without the queue, sources panel, tabs or buttons |
| `app.js` syntax | `new Function` parse OK |

## Screenshots

Headless Chromium (Playwright, Python 3.12) captured these, and each was opened and inspected.

| File | State |
|---|---|
| `landing-th.png` | Landing page, Thai, full page, 1440 px |
| `landing-en.png` | Landing page, English, full page, 1440 px |
| `app-th.png` | Moxifloxacin, 24 months, 1 Jan 2014, Decision summary, Thai |
| `app-en.png` | Same dossier, FTO hand-off with checklist, English |
| `app-outcome.png` | Solifenacin (the miss) with the outcome shown: queue Outcome column and Outcome block |
| `app-sources-focus.png` | Bimatoprost Patents tab after selecting citation [6]: source and citing statement highlighted |
| `app-1024.png` | 1024 px, Thailand and ASEAN tab, sources stacked below the dossier, full page |
| `app-dossiers.png` | Dossiers register |
| `desktop-window.png` | Built desktop program, native window at 125% display scaling (1784 × 1117 pixels), captured from the screen |

## Limits

- Accessibility was checked with axe-core, token contrast and keyboard tests. No screen-reader user test was run (NVDA or Narrator).
- Only Chromium was exercised. Firefox, Safari and static hosting were not.
- The app presents the six development examples. The prospective workflow in PRODUCT.md (enter a molecule, dosage form, jurisdiction and launch date) is not built.
- Long citation lists in the statements table show six numbers and "+N more". Every cited source still appears in the Sources panel and the Sources view.
- The installer is unsigned, was not executed on this computer and has no public download page yet. The landing page says so and gives the SHA-256.

## Next action

The main planner reviews the UI against the F2 sample and DESIGN.md, then integrates `loe/UIBUILD`. Decide whether to publish the installer on a release page, sign it, and update PRODUCT.md's Thai font line to Noto Sans Thai. The planner owns the lane HANDOFF and MEMORY at integration.
