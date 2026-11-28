# IS2LAYOUT receipt

Card: IS2LAYOUT. Branch `loe/IS2LAYOUT` (cut from `research/loe-bench`). Executor: Claude Sonnet 5.5. Scope: page layout of the IS2 short paper, Thai (TH) and English (EN) editions. Planner review pending.

## Decision

Fix layout only through placement of floats in the Markdown drafts; the builder and template were not changed. No number, result, claim, citation, title or abstract text was altered. One Thai phrase was reworded (listed below) to remove a one-word last line.

## Method

Rendered every page of both PDFs with PyMuPDF at 110 dpi into a scratch folder outside the repo and inspected each image. Builder: `python ~/.claude/skills/kmitl-is-paper/scripts/make_paper.py --content content_{th,en}.py --figdir ../figures --out IS2-MWD-{TH,EN}-v2.docx`, run in `docs/writing/is2/mwd/build/`. Three iterations: Figure 1 move, Figure 2 move, then Table 1 move plus the Thai wording tweak.

## Source changes (all in `docs/writing/is2/mwd/`)

| File | Change |
|---|---|
| `IS2-DRAFT-TH.md`, `IS2-DRAFT-EN.md` | Figure 1 block (image and caption) moved from after the first paragraph of section 3.4 to directly after the single paragraph of section 3.1, where "(รูปที่ 1)" / "(Figure 1)" is first cited. |
| both | Figure 2 block moved from before the first paragraph of 4.1 to after it, so that paragraph fills the end of page 5. One redundant blank line under the 4.1 heading removed. |
| `IS2-DRAFT-EN.md` | Table 1 block (caption and table) moved from after the last paragraph of 4.3 ("We report these comparisons...") to before it, directly after the paragraph that cites Table 1. |
| `IS2-DRAFT-TH.md` | One wording tweak (below). |

## Wording changes (verbatim)

1. TH section 4.2, end of the L1e − M3 paragraph:
   - old: `ผลเชิงสำรวจยังไม่ปรับสำหรับหลายคู่เปรียบเทียบ)`
   - new: `ผลเชิงสำรวจนี้ยังไม่ปรับค่าสำหรับการเปรียบเทียบหลายคู่)`
   - Reason: the old text left `คู่เปรียบเทียบ)` alone on the last line (builder orphan report, p6). Meaning unchanged.

No other wording was changed. EN has no wording changes. The TH and EN abstracts were not touched and remain consistent.

## Per-page findings: Thai edition (before → after)

| Page | Before | Fix | After |
|---|---|---|---|
| 1 | Title, abstract, keywords; about 6 cm empty between keywords and footnote block | None possible: footnotes are anchored to the page bottom by the template (front gap 2456 twips) | Same. Template-inherent |
| 2 | English abstract page; about 8 cm empty above footnotes (3380 twips) | Same as p1 | Same. Template-inherent |
| 3 | Clean; 3.1 cites Figure 1 at the bottom of the right column | None | Clean |
| 4 | Text only (Figure 1 was two pages later) | Figure 1 moved to 3.1 | Figure 1 at top of page, caption directly below, on the page after its first mention |
| 5 | Figure 1 at top; right column ended about 8 cm short before the Figure 2 float | Figure 2 anchored after the first paragraph of 4.1 | Columns end at 698 pt and 640 pt (gap about 2 cm) |
| 6 | Figure 2 at top; last line `คู่เปรียบเทียบ)` was a single word | Wording tweak 1; Figure 2 move | Figure 2 at top with caption below; last line `การเปรียบเทียบหลายคู่)`; 0 orphan lines |
| 7 | Table 1 in left column under 4.3 text; clean | None | Clean, table not split |
| 8 | Conclusion, acknowledgment, references; clean | None | Clean |
| 9 | References; right column ends at 184 pt | None (last page) | Acceptable |

## Per-page findings: English edition (before → after)

| Page | Before | Fix | After |
|---|---|---|---|
| 1 | Title, abstract; same template gap as TH p1 | None possible | Same |
| 2 | English front page; same template gap as TH p2 | None possible | Same |
| 3 | Clean | None | Clean |
| 4 | Text only (Figure 1 was two pages later) | Figure 1 moved to 3.1 | Figure 1 at top, caption directly below, on the page after its first mention |
| 5 | Figure 1 at top; right column ended about 5.6 cm short before the Figure 2 float | Figure 2 anchored after the first paragraph of 4.1 | Columns end at 698 pt and 688 pt |
| 6 | Figure 2 at top, 4.1 heading below it | Same fix | Figure 2 with caption below; 4.1 continues |
| 7 | Left column ended about 3.7 cm early because Table 1 did not fit under the last paragraph and jumped to the right column | Table 1 moved before the "We report" paragraph | Columns end at 706 pt and 705 pt; Table 1 whole, caption above, directly after the paragraph that cites it |
| 8 | Conclusion, acknowledgment, references begin | None | Clean |
| 9 | References; right column ends at 408 pt | None (last page) | Acceptable |

## Builder output (final)

TH:

```
pages: 9  front gaps (twips): {"p1": 2456, "p2": 3380}
orphan lines (last line of a block <= 2 words or < 18% of block width): 0
  p3: left col ends 704 pt, right col ends 700 pt
  p4: left col ends 705 pt, right col ends 705 pt
  p5: left col ends 698 pt, right col ends 640 pt  <-- white space
  p6: left col ends 709 pt, right col ends 697 pt
  p7: left col ends 706 pt, right col ends 701 pt
  p8: left col ends 708 pt, right col ends 706 pt
  p9: left col ends 706 pt, right col ends 184 pt
```

EN:

```
pages: 9  front gaps (twips): {"p1": 2456, "p2": 3380}
orphan lines (last line of a block <= 2 words or < 18% of block width): 0
  p3: left col ends 704 pt, right col ends 700 pt
  p4: left col ends 705 pt, right col ends 705 pt
  p5: left col ends 698 pt, right col ends 688 pt
  p6: left col ends 709 pt, right col ends 697 pt
  p7: left col ends 706 pt, right col ends 705 pt
  p8: left col ends 706 pt, right col ends 706 pt
  p9: left col ends 706 pt, right col ends 408 pt
```

Page counts: TH 9, EN 9 (KMITL limit 10). The TH p5 right column flag (640 pt, about 2 cm above the margin) is the only remaining builder white-space flag and is under the 3 cm threshold used for this card.

## Final files (SHA-256)

Outputs are in `docs/writing/is2/mwd/build/`. `*.docx` and `*.pdf` there are git-ignored, so they are not committed; the hashes identify the builds.

```
1ba0e4075cd41fe968ec6a98871ffe6aad9a5567c729935aa393e2026bcaaeae  IS2-MWD-EN-v2.docx
647a0fcd1a75a14b2355b7ed95fddc0fd139e29a961cb590d78c6d88af55de2e  IS2-MWD-TH-v2.docx
30902c6c99339202a338bfbc9ee5d1e2c213093d4366c25c0d91fcf587e604e7  IS2-MWD-EN-v2.pdf
18cf2e7f8e2df0d781051353c45508127be17163208f32394a4f9110592c281a  IS2-MWD-TH-v2.pdf
```

Docx and pdf hashes can differ across rebuilds because Word embeds timestamps; page counts and the orphan report are the stable checks.

## Not fixed / limitations

- Pages 1 and 2 (both editions) keep a visible gap between the keywords or abstract and the footnote block. The builder fits footnotes to the bottom margin by design, and the template requires single-column front matter with footnotes on each of these two pages. Filling the gap would need extra content or a template change, outside this card.
- Reference [17] (`wipo_pub_946.pdf`) breaks the URL as `...946.pd` / `f.` in both editions. This is Word's character-level wrap of an unbroken URL, and the builder's orphan check does not flag it. Fixing it means inserting an invisible break character into a citation URL, which I did not do without planner approval.
- Reference [31] shows "(C′" tight against the column edge in the TH page 9 render; cosmetic, not changed.
- Placement depends on the Word renderer and may shift if the text changes again.
- Closeout: the lane HANDOFF and lane memory are Orchestrator-owned and not edited here; this receipt is the closeout record for the card.
