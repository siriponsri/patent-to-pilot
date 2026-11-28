# IS2FIX2 bilingual short-paper corrections

29 November 2026. Applied the [co-planner critique](../../writing/is2/IS2-CRITIQUE-R2.md) and the planner's two audit findings on `loe/IS2FIX2`, from `origin/loe/IS2CRIT2` at `94de21e565ceaef57b07a1224bf05ab33f28b212`. The research dispositions and numerical results follow the [closure record at 5448904e](https://github.com/siriponsri/patent-to-pilot/blob/5448904e/docs/loe-bench/RESEARCH-COMPLETION.md). This receipt records the executor's verification. Final paper acceptance rests with the main planner.

| ID | Status | Change and evidence |
| --- | --- | --- |
| 01 | PASS | Section 5 uses the first attested capture at each horizon. Formal H3 requires the verified first published 12-month panel and both prior tests to pass at the 24-month readout. Revised FDA editions and recomputations after missing or disputed evidence are descriptive. Published decisions are retained. [Readout addendum](../TRACKA-READOUT-ADDENDUM.md) · [READOUT10](TRACKA-READOUT10.md) |
| 02 | PASS | Both editions have the same reference [31], with its title linked to the completion table at `5448904e`. Its text retains `3e06537b` as the historical scoring revision. Section 4.1 links the two supplement receipts at the closure pin. The availability paragraph links the pinned benchmark card. |
| 03 | PASS | Both abstracts disclose prior aggregate exposure to overlapping calendar periods and drug histories with authorized opening of sealed C′ row outcomes. The Thai endpoint specifies the dated approval and 12- and 24-month horizons. Section 3.2 identifies 4,162 rows as the earlier 36-month baseline and discloses the other preflight information. [Registration](../PREREGISTRATION.md) |
| 04 | PASS | Section 5 attributes the ten rounds to the project co-planner acting as external reviewer and reports the verdict at `2cee4a62` and the main planner's concurrence. [Joint sign-off](../JOINT-SIGNOFF.md#final-research-track-closure-29-november-2026-0219-bangkok-by-the-system-clock) |
| 05 | PASS | Both first-page student footnotes start the full institute name on a new line and retain the bottom anchor and wording. References use descriptive hyperlinks and keep publication locators with DOIs. Table 1 column widths keep estimates and intervals on one line. The final all-page orphan check found zero one- or two-word continuations. |
| 06 | PASS | Section 3.3 identifies the paired bootstrap percentile recall intervals and the separate conditional whole-drug Chernoff upper bound used for the 3% safety comparison. [SCORE](SCORE.md#secondary-analyses) |
| 07 | PASS | Section 3.4 attributes 05:12 UTC on 28 November to the start of the blind gate run. The verdict preceded historical scoring. [GATE](GATE.md) |
| 08 | PASS | Section 4.1 separates eligibility, ten-bin calibration, the row-independence assumption for Wilson intervals, small-count and complementary suppression, and zero correct positive predictions at calibrated probability of at least 0.5. [CPRIME-DESC](CPRIME-DESC.md) · [CPRIME-SUPP](CPRIME-SUPP.md) |
| 09 | PASS | The nine signed English limitation entries appear verbatim at their topical locations. The Thai edition preserves the limitations, including possible linkage and eligibility bias in either direction. [Signed wording](../JOINT-SIGNOFF.md#limitations-to-carry-into-is2-and-journal-manuscripts-verbatim) |
| P1 | PASS | Section 5 in each edition states the US-only expansion design and explains why as-of admission under jurisdiction criterion M3 could not be verified for Canada or Japan. Both retain the fixed-calendar ceiling and untested earlier readout caveats and the descriptive Thai/ASEAN scope. [Decision rule](../JURISDICTION-DECISION-RULE.md#final-decision-planner-28-november-2026-2209-bangkok-by-the-system-clock) · [JURIS-COUNT](JURIS-COUNT.md) |
| P2 | PASS | Both editions use plain prose for unrun analyses, unavailable statistics and prospective outcomes. The PDFs contain no `NOT_RUN`, `NOT_ESTIMABLE` or `PENDING` prose tokens. |

## Build and verification

- **PASS, KMITL layout.** Used the [existing builder and Word export](../../writing/is2/mwd/build/README.md). The final English edition has 10 pages and the final Thai edition has 9, including front matter and references. Figures 1 and 2 are on pages 4 and 6. Table 1 fits on page 7 in both editions. The template anchors the front-matter footnotes. The English page 7 left column ends above the bottom margin before the table moves to the right column.
- **PASS, all-page orphan check.** Rendered all 19 final PDF pages with PyMuPDF 2.0, grouped extracted spans on the same line within each column, and flagged lines with at most two word tokens using English whitespace and Node `Intl.Segmenter` for Thai. Reviewed candidates against the page renders, including footnotes, captions, references, and the rasterized figures. Zero wrapped one- or two-word continuations. Standalone headings, table labels, plot identifiers and ticks serve as labels. Intermediate exports showed a spilled footnote, isolated DOI continuations and split table intervals. The final exports were regenerated after those fixes.
- **PASS, citations and content.** The two source editions have identical bilingual abstracts and reference entries. Each first-citation sequence is [1] through [33], including range expansion. Checked all 33 entries in the rendered text and all 36 distinct external link targets per edition in both DOCX relationships and PDF annotations. Compared the inherited decimal and comma-grouped values against the prior published copies and verified the three primary contrasts and the signed bounds. The new wording uses the published aggregate record only.
- **Repository test exception.** CPython 3.12 ran `python -m pytest -o addopts= -q --tb=short --basetemp <fresh local temp path>`. Exit 1 with 2,760 passing, 50 skipped, one expected failure, and only the eight standing SACR r2/r3 supervisor budget exceptions. No new research analysis or paid API or GPU use. Protected TEST data, private artifacts and credentials were outside this task.

## Delivery and handoff

Delivered in `C:/Users/User/Desktop/myDegree/IS/IS_2_new/01_short-paper/revision-20261129/`. Before copying the new files, verified the four originals against the [IS2REV2 receipt](IS2REV2.md), created four matching `-v1` copies, then compared the delivered bytes with the inspected builds.

| File | Pages in Word export | SHA-256 |
| --- | ---: | --- |
| `IS2-MWD-EN.docx` | 10 | `dc048c337defc74ff38246e7ddcca87ecef68577d5bc6055a70e9f44052faade` |
| `IS2-MWD-EN.pdf` | 10 | `29bb2d9c864a2bbf838f43f3c8ba4269edd4f505ede7fdc54a35db69746e4e53` |
| `IS2-MWD-TH.docx` | 9 | `70392e634b19fc1d9afa0e83dc613d9bb3ce8b76dca14541c3ba15473b1b425f` |
| `IS2-MWD-TH.pdf` | 9 | `4654c4c96b5ce3b0d41372bb7dcf2138bd2796314d9b5aa95a03d4c328d5eb1d` |

The main planner can audit the branch and the four local files against these digests. The planner owns the LOE-Bench handoff and memory updates at integration. Include footnotes, bibliography and table cell continuations in subsequent final-PDF line checks. The builder's final-line heuristic alone missed those cases.

## Planner audit (Claude Opus 5.5, 29 November 2026, 03:04 Bangkok)

**PASS.** Delivered hashes match this receipt (TH PDF `4654c4c9…`, EN PDF `29bb2d9c…`, TH DOCX `70392e63…`, EN DOCX `dc048c33…`). Both PDFs carry H1 +20.37 [+14.37, +26.16], H2 +1.36 [−2.20, +3.01] and H3 +16.69 [+9.98, +24.21], the Zenodo DOI and reference [31] at `5448904e`. No code tokens (NOT_RUN, NOT_ESTIMABLE, PROVISIONAL) remain in either PDF. The Thai DOCX text carries the US-only decision with Canada and Japan failing M3, and the co-planner disclosure for the ten review rounds. Thai PDF text extraction with pdftotext is unreliable, so Thai checks used the DOCX XML. A visual orphan check was not repeated because no PDF renderer is installed here; the executor's render-and-segment check and the co-planner critique both report none. Chain: IS2REV2 `f958e044` → IS2CRIT2 `94de21e5` (ACCEPT WITH FIXES) → IS2FIX2 `95c0aebd`.
