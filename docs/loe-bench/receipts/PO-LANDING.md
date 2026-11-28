# PO-LANDING | Landing page v1 and repository hygiene (PRD R3, R12)

Branch `loe/PO-LANDING`, cut from `1ff2db22`. Product Owner executor: Claude Sonnet 5.5. No deployment was made. `product/demo/app.js`, `product/mwd/` and `product/demo/data/` were not touched.

## Changes

- `product/site/index.html`, `site.css`, `README.md`: evidence panel rebuilt. Recall always sits beside precision. Added H1 PASS, H2 FAIL (not confirmed), L1e as exploratory in the tested setting, Track A frozen 28 Nov 2026 with outcomes pending and both readout dates, and OSF doi:10.17605/OSF.IO/P2SMD with update 4. The results table gained a Receipt column. The word "accuracy" was removed from the page (navigation, headings, Thai text); the section id `#accuracy` became `#evidence`. Added "AI assistance" (in development; not evaluated) and "MCP connector" (planned), with no performance claims. The download text now says the public site will be on Cloudflare Pages (`*.pages.dev`), not deployed. The "Decision support only" notice and fixed disclaimer are unchanged. The old "freeze before 31 Jan 2027" wording is replaced by the recorded freeze.
- `NOTICE`: Apache-2.0 now covers the whole repository including `product/` and `loe-bench/` (D-L), with third-party terms: FDA public domain, GSRS CC0, Rai et al. CC0, NBER as a recipe only, fonts SIL OFL 1.1, plus the earlier research datasets. `LICENSE` is the stock Apache text and needs no header change.
- Three duplicate images removed (below). `docs/healthtech/ux/implementation/README.md` now links the historical tree.

## Number to receipt

| Number | Receipt (all under `docs/loe-bench/receipts/`) |
|---|---|
| Recall 66.85%, precision 26.62% (M3, 24 months, 20%) | SCORELLM.md, "Exploratory C′ results", row 24 / M3 |
| B1 recall 46.48%, precision 18.51% | SCORELLM.md, same table, row 24 / B1 |
| H1 PASS +20.37 pp, 95% CI +14.37 to +26.16 | SCORE.md, "Primary family" |
| H2 FAIL +1.36 pp, 95% CI −2.20 to +3.01 | SCORE.md, "Primary family" |
| L1e recall 12.36%, precision 4.92% | SCORELLM.md, same table, row 24 / L1e |
| C3 79.8% vs 49.7%, +30.11 (exploratory) | SCORE.md, "C3 \| Competition at launch" |
| Track A frozen 28 Nov 2026, readouts 27 Nov 2027 and 28 Nov 2028 | TRACKA-FREEZE.md (freeze, "Verification, deviations and handoff") |
| OSF update 4 | TRACKA-FREEZE.md, "OSF update 4 verified"; registration doi:10.17605/OSF.IO/P2SMD |

Thai dates use the Buddhist year (28 พ.ย. 2569, 27 พ.ย. 2570, 27 พ.ย. 2571). The 24-month readout date is stated here as 27 Nov 2028 as the task gave it; TRACKA-FREEZE.md says the 24-month window matures on 27 November 2028.

## Link check

Every `href` on the page was checked by script. All 13 fragment links, relative files (`../demo/index.html`, `site.css`, logo, fonts) and GitHub `research/loe-bench` receipt links resolve to existing files in this tree, and the three heading anchors match their headings. External URLs (the OSF DOI and the repository root) were not fetched. Receipt links reach GitHub only once this branch is merged and pushed to `research/loe-bench`.

## Removed files

Each file was byte-identical (SHA-256) to the same-named kept copy in `docs/healthtech/ux/implementation/evidence/readability-pass/after/`.

| Removed path (under `docs/healthtech/ux/implementation/evidence/workspace-redesign/before/`) | SHA-256 |
|---|---|
| E02-overview-th-1280.jpg | 3429bec80181f97bdf0b67245dd08796e15ea1b8a0786a439f9cf880ad383565 |
| E05-conflict-panel.jpg | 2b01cc0c4f76a9ed2f81fe4ac60e23362cd68f2db887c4b67bef9e489266bcff |
| E13-evidence-th-formal-light-320.jpg | 9d1c289b933fc6c5cdb0e1df993e1427816cea672a41f8f9fb7964a9987aee89 |

The grep found one live link (the implementation README, redirected to commit `496ca359`) and path strings inside three historical `verification.json` hash records under `docs/healthtech/audits/ptp-long-run-resume-20261103/`. Those records stay unchanged, as the DOCS2 inventory advised, and an exact-path replay resolves from commit `496ca359`. Strictly, "no remaining reference" does not hold for those records; see open issues.

## Screenshots (viewed one by one; no horizontal overflow at either width)

`product/screenshots/landing-v1-th-1440.png`, `landing-v1-en-1440.png`, `landing-v1-th-390.png`, `landing-v1-en-390.png` (headless Chromium via Playwright).

## Open issues

1. The deleted images are still named in three historical `verification.json` records. The planner may prefer to keep the files instead.
2. The page names Qwen2.5-7B for L1e (from SCORELLM.md); PRD section 3 allows "in the tested setting".
3. Receipt and NOTICE links use GitHub URLs on `research/loe-bench` and fail until the branch is integrated.
4. Thai copy for the new sections is mine and has had no native-speaker or planner review.
5. No check of the 320 px width or of keyboard focus order beyond the existing structure.
