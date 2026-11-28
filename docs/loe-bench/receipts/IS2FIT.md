# IS2FIT pagination and draft handoff

**PASS for pagination and layout.** Microsoft Word rendered the [English draft](../../writing/is2/mwd/IS2-DRAFT-EN.md) and [Thai draft](../../writing/is2/mwd/IS2-DRAFT-TH.md) at 10 pages each, including two front-matter pages and the references. The dispatched builds were 14 pages in English and 13 in Thai, as recorded in the [lane handoff](../HANDOFF.md). This card starts at `00fe70dc`, which includes the [main-planner audit](IS2AUDIT.md) and build tooling.

| Edition | Pages before | Pages after | Body length before | Body length after | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| English | 14 | 10 | 4,684 words | 2,741 words | 41.5% |
| Thai | 13 | 10 | 6,095 tokens | 3,835 tokens | 37.1% |

Body length covers §1 through §5, including headings, captions and table cells, with Markdown syntax, citation markers and internal receipt links removed. English uses whitespace-delimited words. Thai uses lexical and numeric tokens from PyThaiNLP 5.4.0 with the `newmm` engine. Removing the development table and repeated procedure, moving floats and restoring a separate start for the body brought both editions to the limit.

## Editorial changes

| Section | Change |
| --- | --- |
| §1 | Condensed the product motivation and contributions. Kept the measured opening, the price comparison, the prior-work citation and all three research questions. |
| §2 | Replaced individual study summaries with short syntheses covering distinct entry endpoints, dated evidence, competition and prices, specialist hand-off, Thai applicability, and the evaluation design. Condensed the gap to two sentences. |
| §3 | Referred detailed linkage, model, bootstrap and admission procedures to the OSF protocol [30]. Kept eligibility, endpoint, Orange Book and challenge availability, prior exposure, queue recall, fixed sequence, verdict-only admission with at least 50 distinct 24-month event drugs, the three OSF updates and the Track A deadline. Condensed the exploratory methods while retaining endpoints, comparators and evidence roles. |
| §4.1 | Removed repeated development arm recalls. Kept panel sizes, the three development contrasts with intervals, and the failed auto-clear diagnostic. Tables 1 and 2 and the sealed-test results remain, with H3 descriptive because H2 stopped testing. |
| §4.2 | Condensed the single-cutoff C3b result and the Medicaid scope and availability caveats. Kept the C′ C3 result and all of Table 3. |
| §4.3 | Replaced development Table 4 and its companion paragraphs with one sentence giving the exploratory L1e − M3 recall contrasts and intervals. Kept the C′ language-model paragraph verbatim. |
| §5 | Gave each research question a short answer followed by one limitations paragraph and one future-work paragraph. Kept data availability and the acknowledgment verbatim. |

All 31 references were retained in the same IEEE first-appearance order in both editions, with zero removals or renumberings. Tables 1–3 retain their original cells. The artwork and both abstracts are verbatim from the audited base. The supplied Thai abstract summarizes M1 − B1, while the English abstract includes the C′ 7B result. This existing emphasis difference awaits the main planner's final audit.

Cross-checked the retained values against [SCORE](SCORE.md), [SCORELLM](SCORELLM.md), [FREEZE](FREEZE.md), [C2](C2.md), [C3b](C3b.md), [C4b](C4b.md), [EVP](EVP.md) and [UIBUILD](UIBUILD.md). The M1 − B1 comparison remains descriptive. Source-integrity counts and semantic support remain distinct.

## Build and layout verification

Run from [the build directory](../../writing/is2/mwd/build/README.md).

```powershell
python C:/Users/User/.claude/skills/kmitl-is-paper/scripts/make_paper.py --content content_en.py --figdir ../figures --out IS2-MWD-EN.docx
python C:/Users/User/.claude/skills/kmitl-is-paper/scripts/make_paper.py --content content_th.py --figdir ../figures --out IS2-MWD-TH.docx
```

The first cut rendered at 11 pages in English and 10 in Thai. Word left gaps ahead of figures and tables and began the introduction below the English front matter. The converter now starts the body on page 3. The float anchors were adjusted separately to fit each edition, and the short Table 3 captions keep each table together with its caption.

English `make_paper.py` output

```text
pages: 10  front gaps (twips): {"p1": 1774, "p2": 2014}
  p3: left col ends 703 pt, right col ends 696 pt
  p4: left col ends 692 pt, right col ends 709 pt
  p5: left col ends 696 pt, right col ends 708 pt
  p6: left col ends 703 pt, right col ends 689 pt
  p7: left col ends 708 pt, right col ends 705 pt
  p8: left col ends 706 pt, right col ends 701 pt
  p9: left col ends 707 pt, right col ends 706 pt
  p10: left col ends 706 pt, right col ends 122 pt
```

Thai `make_paper.py` output

```text
pages: 10  front gaps (twips): {"p1": 1434, "p2": 2014}
  p3: left col ends 703 pt, right col ends 696 pt
  p4: left col ends 707 pt, right col ends 709 pt
  p5: left col ends 696 pt, right col ends 696 pt
  p6: left col ends 703 pt, right col ends 705 pt
  p7: left col ends 708 pt, right col ends 706 pt
  p8: left col ends 701 pt, right col ends 698 pt
  p9: left col ends 706 pt, right col ends 706 pt
  p10: left col ends 321 pt, right col ends 0 pt
```

**PASS.** Rendered all 20 PDF pages to PNG with PyMuPDF. Inspected both page grids and the table pages at full size. Each figure caption sits below its artwork and each table caption above its rows. Table 3 wraps between numbers in confidence intervals, with every number intact. All non-final body columns end within 40 pt of the bottom margin. The final reference pages are partial as permitted. No requested layout issue remains.

| Local PDF | SHA-256 |
| --- | --- |
| `IS2-MWD-EN.pdf` | `ebcf82926f6d26aef198b176cc1fd57d8ec610c981c88b8703f598f7bdf662e8` |
| `IS2-MWD-TH.pdf` | `2eda230c6b4d88c92ef6b102aa6fc06e17a19fe2ec62e2433a75140f2a187c8c` |

**Repository checks.** `python -m pytest` (Python 3.12.10) exited 1 with 2,760 passed, 50 skipped, 1 xfailed and the 8 documented SACR r2/r3 supervisor budget failures. `git diff --check` passed. The local DOCX and PDF files are covered by the build ignore rules.

**Next action.** Claude performs the final audit of both editions. The main planner records integration in the lane handoff and memory.
