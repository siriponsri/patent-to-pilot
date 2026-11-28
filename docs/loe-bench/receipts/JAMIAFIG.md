# JAMIAFIG | JAMIA figures and audit fixes F1–F5

Executor: Claude Sonnet 5.5 (medium), branch `loe/JAMIAFIG` cut from `23f7f7d4`. Audit source: [JAMIA-AUDIT-v2](JAMIA-AUDIT-v2.md). Manuscript text and figure files stay outside Git by owner decision (public repository); only [make_figs_jamia.py](../../writing/journal/jamia/make_figs_jamia.py) and this receipt are committed. No protected TEST data, `.env`, paid service or GPU was touched.

## Fixes applied (v2.1; v2 unchanged)

| ID | Result |
|---|---|
| F1 | Reference 3 now links `https://doi.org/10.1111/cts.70365`. |
| F2 | OSF API `registrations/p2smd/contributors/` lists one contributor, the first author. Reference 9 already has that single author, so no change was needed. The second author is not an OSF contributor; the planner should decide whether to add them to the registration or leave as is. |
| F3 | Byline now lists both authors with degrees as given ("PhD" for the second; the first author's degree is a `[degree]` placeholder) and ORCID and corresponding-author placeholders. Nothing was invented. |
| F4 | Three-sentence informatics-contribution paragraph added in Discussion after the recall and precision paragraph (admission rule with separate content and availability dates; explicit unknown states; fixed-capacity queue estimand with fractional boundary ties; reusable for other time-stamped regulatory sources). |
| F5 | Figures 1 and 2 built from the specifications and embedded in the Word file after first mention with the existing alt text. The specification blocks were removed from v2.1. |

## Figure files

Location: `C:/Users/User/Desktop/myDegree/IS/IS_2_new/04_journals/JAMIA/manuscript/figures/`. Size 6.5 × 6.5 in (Figure 1) and 6.5 × 2.25 in (Figure 2). PNG at 600 dpi, PDF with embedded fonts, SVG with text as paths. Arial, all text at least 7 pt, lines 0.25–1 pt, one blue accent with redundant marker and line-style coding. The script asserts at run time that no text is under 7 pt, no multi-line label has a one-word line and no text boxes overlap or clip.

| File | SHA-256 |
|---|---|
| fig1.png | `0521c97d3ab04a337f86e35d7068f9a3d33d22cd720e87bc3ddbab3748bc5c37` |
| fig1.pdf | `d635b3edda8f9593a6c206b376580db50ba7d820137d8b53de8e8ffb91b65a99` |
| fig1.svg | `4da97b1bda6a1531f370e84f9e17918de7a9c64a85eaa67682032a3637f95c35` |
| fig2.png | `9f95c940079a36c842fb2d3caed0909949cf46994b0d7d495927c4e1f5dc60e4` |
| fig2.pdf | `7ad26e52e5c4b1cae3e6c439eafbe2bf54afe7eb56f32fb6976232cb39192994` |
| fig2.svg | `46c30eab0b2880b8247ead958f54bfa1c5db605659be49d04ba3c675f9d0663f` |

Manuscript files (outside Git): `MANUSCRIPT-JAMIA-v2.1.md` `c7ec10c8…0028`, `MANUSCRIPT-JAMIA-v2.1.docx` `adf351d3…c631`. Script SHA-256 `ac6b3cb4…64f9`.

## Data coordinates

Figure 2 reads `loe-bench/data/SCORE_CPRIME_RESULTS.json` (`horizons/{12,24}/contrasts/<pair>/recall`, rounded to two decimals of a percentage point) and asserts equality with the manuscript values: H1 M3−B1 at 24 months +20.37 [14.37, 26.16]; H2 M3−M1 at 24 months +1.36 [−2.20, 3.01]; H3 M3−B1 at 12 months +16.69 [9.98, 24.21]; practical threshold +10; zero draws undefined. Figure 1 dates: cutoffs 2010 (fit), 2012–2015 and 2013–2014 (validation), 2017–2025 and 2017–2024 (C′), Track A reference 27 Nov 2026, freeze 28 Nov 2026 11:18:44 UTC and OSF update 4 at 11:30:06 UTC ([TRACKA-FREEZE](TRACKA-FREEZE.md)), windows ending 27 Nov 2027 and 27 Nov 2028. The inset uses the invented Supplement S1 values (cutoff 1 Jan 2024, OB-A proof 15 Nov 2023, OB-B proof 5 Jan 2024, scores 0.62, 0.62, 0.31, 0.22, 0.08, one slot, weights 0.5, event 1 Jun 2025).

## Word count and checks

Background through Conclusion including tables, captions and alt text, excluding figure specifications and images: 3,771 words (limit 4,000). The same method gives 3,683 for v2, so the v2 header figure of 3,903 used a different counting rule; the v2.1 header states the rule. Word rendering: LibreOffice converted the docx to a 12-page PDF; Figure 1 appears on page 4 right after its first mention, Figure 2 on page 8 after the Results paragraph, and tables are native editable Word tables. `py -3.12 -m pytest tests/test_org_adaptive_terminology.py -q` passed.

## Open issues

- First author's degree, both ORCIDs and corresponding-author details need the owner.
- Second author is absent from the OSF contributor list (see F2).
- The docx was generated with python-docx (no pandoc installed) and uses default Word styles; tables wrap interval cells and may need final typesetting. The figure panels use the full 6.5 in text width; OUP print width was not stated in the saved guidance.
- Ring and callout positions in Figure 1 panel a depend on the 2024 cutoff being the S1 example year; if the planner prefers a different example year the script needs one constant changed.
