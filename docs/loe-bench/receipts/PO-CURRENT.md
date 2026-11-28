# PO-CURRENT receipt

Product Owner card PO-CURRENT (R1 and R1b of the [PRD](../../product/prd/PRD-MWD-v1.md)). Executed by Claude Sonnet 5.5 on 28 November 2026 on branch `loe/PO-CURRENT`, cut from `research/loe-bench` at `23af56eb`. The main planner reviews. Nothing was merged.

## Result

**PASS, with open issues listed below.** The current queue (Track A t0 forecast as of 27 November 2026, outcome pending) is committed under `product/demo/data/current/` and wired into the app beside the historical time machine. The app now has search by drug name and a planned launch date that selects the 12- or 24-month window. No forecast is computed in the app, and the current files carry no outcome or reveal field.

## Decision

The data may be committed. The rights check found three sources, all open (see the inventory). No NBER-derived field is shipped. The freeze is verified, so the data was regenerated with the verified-freeze flags and carries the tag and manifest digest in its version. `.gitignore` no longer ignores `/product/demo/data/current/` (the PRODV1-DATA receipt said a publication commit must opt in).

## Commands and outputs

```powershell
py -3.12 -m product.mwd.current --out product/demo/data/current-verified --verified-freeze-tag loe-track-a-freeze-20261127 --verified-freeze-manifest loe-bench/data/TRACKA_FREEZE_MANIFEST.json
py -3.12 -m product.mwd.audit --data-dir product/demo/data/current
python product/demo/bundle.py --current
py -3.12 -m pytest product/mwd/tests
```

| Step | Result |
| --- | --- |
| First generation without freeze flags (`version.freeze = pending`) | exit 0, audit 16,562/16,562. Superseded by the verified generation. |
| Verified generation | exit 0. `version` = `{freeze: verified, tag: loe-track-a-freeze-20261127, manifest_sha256: 8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d, core_manifest_sha256: 6497ab59ba41b0429a6169d5118c6afd14680233076a6a6693c03599d0176628}`. `status` = `TRACK_A_FROZEN`. The tag is an ancestor of the branch base and the manifest exists in the tag. A second run into a new directory was byte-identical (654 files), so generation is deterministic. |
| C8 audit on the committed set | **16,562 claims, 16,562 resolvable (100%), 16,562 with a source hash, 0 future-dated, 0 errors**, across 651 dossiers. |
| Outcome and reveal scan | No `outcome_reveal`, `event`, `first_final_anda_date` or similar field. The only match for "outcome" is the label text "Track A t0 forecast, outcome pending" in all 654 files. `window_end` in the two queue files is the forecast window end date (2027-11-27 and 2028-11-27), not an outcome. |
| `py -3.12 -m pytest product/mwd/tests` | PASS, 17 passed, exit 0 (includes schema validation of the 651 current dossiers). |
| Headless Chromium (Playwright), `http://` and `file://` | No page or console errors. Mode switch, search, launch-date mapping, outside-horizon state, Dossiers view, Settings, tab order and the old-style history link all checked. |

## Rights inventory (R13, field sources of the shipped files)

Every source cited in the 651 dossiers is one of three issuers (13,445 source entries). Display names and the identity crosswalk come from FDA/NCATS GSRS (PREREGISTRATION, CC0 1.0).

| Field group | Where | Source | Terms | Version or edition | Restricted? |
| --- | --- | --- | --- | --- | --- |
| Drug display name, key, dosage forms | queue rows, `molecule` | FDA Orange Book and Drugs@FDA (S0 manifest); identity from FDA/NCATS GSRS public export dated 6 Aug 2026 | US government work (public domain); GSRS CC0 1.0 | Orange Book 10 Jul 2026 (public 26 Jul 2026); openFDA `last_updated` 26 Nov 2026 | No |
| Patents, exclusivities, approvals, competition statements (11,428 source entries) | `claims`, `sources` | U.S. FDA Orange Book editions incl. archived historical ZIPs (web.archive.org copies of FDA files) | US government work (public domain) | Editions 2013 to 2026-07-10, hash per source | No |
| Court docket statements (64 source entries) | challenge claims | Rai et al. district court table, Harvard Dataverse v1.0, file 4789869 | CC0 1.0 | 1.0 (2021-06-10), SHA-256 `abb54817c8…aa06e5` | No |
| M3, B1, M1, P1, P2 scores, ranks, inclusion probabilities, boundary | queue rows, `forecast`, `forecast_12m` | LOE-Bench frozen Track A native score exports (`score_export_sha256` `551bfe34…`, secondary `8b8610f5…`) | Project-generated from the sources above; frozen Track A bytes. No NBER input (NBER E8 is "prior development only" in the preregistration). Project licence for `product/` is still pending (D-L, R12) | Tag `loe-track-a-freeze-20261127`, core manifest `6497ab59…` | No third-party restriction found |
| Checklist, disclaimer, Thai and English text | `checklist`, `claims.text_*`, `disclaimer` | Project-authored | Project terms (see licence note above) | Same version object | No |

Shipped file digests (SHA-256, LF bytes):

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `data/current/index.json` | 123,981 | `ebe68e6be6007118eb3eea1fe983ede800b93845803768ed5138d7e88d959c80` |
| `data/current/queue-2026-11-27-12m.json` | 283,723 | `3ecdf9fff41ae70c5136a337dcad2e10e9f8922335190c6568d5732e8e90c8f7` |
| `data/current/queue-2026-11-27-24m.json` | 283,234 | `17c04083eeb093fecd2c696b684ccedd47f6dc6d3ebb6708f0503d328c258b39` |
| 651 `data/current/dossier-*.json` | 20,733,083 in total | `1575e8fee6be303752ca175bcc1109108750e08af8f44611f14f1898ea7c3fe6` over the sorted list of `<name>  <sha256>` lines |
| `data.current.bundle.js` | 17,828,527 | `9309e0d7bac6ef0a446438b88ad519b54d7b9323f51e942acdc33ca5d99b940d` |
| `data.bundle.js` (time machine, unchanged) | 2,602,394 | `8de2dec64ed2f8ef4231de5a4ffacb8f4e3d61a7b11768128b552e7425432df7` |

The app shows these three terms in Settings, under "Data rights" in Current queue mode.

## What changed

| File | Change |
| --- | --- |
| `.gitignore` | Removed the ignore line for `/product/demo/data/current/`. |
| `product/demo/data/current/` | New: 654 files (index, 2 queues, 651 dossiers). |
| `product/demo/data.current.bundle.js` | New, generated by `bundle.py --current`. It is loaded only in Current queue mode and only from `file://` or when `data/current/index.json` cannot be fetched. |
| `product/demo/bundle.py` | New `--current` option. The default run is unchanged. |
| `product/demo/index.html` | Mode bar, search box, launch-date field, launch message, "About this queue" details. |
| `product/demo/app.js` | Two data sets with separate caches. A normaliser expands the current index (one dossier file per drug, both horizons) to the shape the app already uses. Mode in the hash (`mode`, `q`, `ld`). Per-horizon dossier view. Search, launch-date window, outside-horizon state, boundary-tie text, mode-aware notice, footer and Settings. |
| `product/demo/styles.css` | Mode bar, inputs, launch message, outside-horizon notice, tie details; print keeps the mode and cutoff line. |
| `product/demo/README.md` | Two modes, data files, hash keys, refresh commands, deploy rule. |
| `docs/product/prd/PRD-MWD-v1.md` | Section 2 status row for the current queue. |
| `product/screenshots/po-current-*.png` | 12 screenshots. |

No `product/mwd/` pipeline code, no `loe_bench/` code and no tests were changed.

## Behavior

- **Mode bar on every view** (Queue, Dossiers, Sources, Settings): mode, reference date or cutoff, Orange Book edition (read from the open dossier's sources), horizon and freeze tag. The notice body and the footer follow the mode, so "development data" text never appears in the current view. A link with a four-digit `c` and no `mode` still opens the time machine, so older links keep working.
- **Current queue**: 651 rows per horizon, 130 review slots, the divider reads "Review capacity: 130 of 651 (1 in 5)". The dossier chips show "Track A t0 forecast, outcome pending". Each dossier holds both horizons, so the app picks `forecast` (24 months) or `forecast_12m` and drops the other horizon's `queue-*` and `entry-*` statements.
- **Boundary ties**: tied M3 scores share a rank, and a drug at the boundary shares the remaining slots. The text is built from the queue's `boundary` object. In this edition both horizons have 129 scores above the boundary and one at it with inclusion probability 100%, so no drug is included fractionally. A fractional probability would be shown in the queue-position cell.
- **Search** (R1b): substring match on display name and key, every word must match, `NFKC` and lower case. Examples checked: "gluTIDE" 2 matches, "tide" 29, "u:53axn" 1, "zzzz" 0. Enter opens the first result, the down arrow moves into the list. Names in the data are English only, so Thai-script input finds nothing and the empty state says so.
- **Launch date** (R1b): on or before 27 Nov 2026 asks for a later date; to 27 Nov 2027 selects the 12-month window; to 27 Nov 2028 selects the 24-month window; later shows "Outside the forecast horizon". The boundary dates 27 Nov and 28 Nov of 2026, 2027 and 2028 were checked. In the outside state the queue lists drugs alphabetically with dashes for rank and M3, the dossier statistics show dashes, and every statement with a forecast number is removed. The message says the number is the chance of the first final US generic approval, not a launch date.
- **Claims wording**: the decision tab says the event is the first final US generic approval, not launch, demand or Thai permission, and shows "M3 found 66.85% of first generic approvals, with precision 26.62%" as one sentence (24-month registered test, 1-in-5 capacity), with outcomes pending until the scorer runs in November 2027 and 2028.

## Screenshots

Each was opened and inspected. All are headless Chromium over `http://`.

| File | State |
| --- | --- |
| `po-current-queue-th-1440.png`, `po-current-queue-en-1440.png`, `po-current-queue-en-1024.png` | Current queue, 24 months |
| `po-current-search-th-1440.png`, `po-current-search-en-1024.png` | Search "SEMAG" (1 of 651) |
| `po-current-launch12-th-1024.png` | Launch 30 Jun 2027 selects the 12-month window (Thai message) |
| `po-current-outside-en-1440.png`, `po-current-outside-th-1024.png` | Launch 15 Mar 2029, outside the forecast horizon |
| `po-current-dossier-en-1440.png`, `po-current-dossier-th-1440.png` | Semaglutide, Patents tab |
| `po-current-dossiers-en-1440.png` | Dossiers view in current mode |
| `po-current-history-en-1440.png` | Time machine still works, with its mode bar |

Not screenshotted: Thai at 1440 for the outside state and English at 1024 for it (same code path as the pairs above), and the Sources view in current mode.

## Open issues

1. **Size.** `data/current/` is 23 MB and `data.current.bundle.js` is 17.8 MB. The bundle exists only for double-clicking `index.html` from a file. The planner should decide whether it ships in the desktop installer, which would add the same weight (the desktop copy of the app was not rebuilt or checked in this card).
2. **Licence of project outputs.** The forecast scores and project text have no recorded licence yet (D-L, R12 NOTICE for `product/`). No third-party restriction was found, but R13 sign-off needs the owner decision.
3. **No accessibility re-run.** I did not re-run axe-core. The new controls are native (`input type=search`, `input type=date`, `button aria-pressed`, `details`), labelled, and operable from the keyboard. The launch message is a polite live region. The 1280 px width and the desktop window were not rechecked. Needs PO-QA.
4. **Thai drug names.** Search matches English names only because the data has no Thai names. Say so if the owner expects Thai-script search.
5. **Date input locale.** The native date field follows the browser locale (dd/mm/yyyy here). A year typed digit by digit briefly reads as a date before the reference date.
6. **Not changed.** PDF (R2), landing page (R3), "Print dossier" layout for the current dossier, desktop rebuild and the Sources view tweaks are other cards.

## Next action

The main planner reviews `loe/PO-CURRENT`, then PO-PDF starts from the current dossiers. The Orchestrator owns the lane HANDOFF and MEMORY at integration.
