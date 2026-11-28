# IS2FORMAL | Bilingual formal revision

**PASS** for the drafting card and the local Word layout check. Base: `2b976da1` on fetched `origin/research/loe-bench`. The main planner owns the final figures, Track A update, audit and release build.

## Edits and editorial checks

- Applied the [binding style guide](../../writing/is2/mwd/STYLE-GUIDE.md). Both editions use the owner-selected TH and EN titles, the 12 prescribed rewrites, the two-sentence IS1 continuity, and the historical IS2 comparison. The shared abstracts define the event as the first final approval of an original ANDA and specify the rounded-down one-fifth review limit as part of the evaluation.
- Added the research objectives heading, retained RQ1–RQ3 as declarative objectives, and named the measured quantities in the results headings. Named the researchers, methods and specialists as the actors where applicable. Removed the rhetorical questions, desk metaphor and repeated conversational interpretations. Kept the automatic clearance limitation and the Thai verification requirements.
- Retained the H1 pass, H2 failure to establish incremental gain and sequence stop, and descriptive H3. Kept the historical test, exploratory analyses and retrospectively matched reimbursement subset qualified. In §3.5, both editions define fourth-quarter reimbursement per prescription using the positive prescription count and annual reimbursement as the total over the next four quarters. The Thai text now identifies the +30.16-point C′ sensitivity as the pinned snapshot-sponsor comparison, in line with the [SCORE receipt](SCORE.md#c3--competition-at-launch).
- Applied no-ai-slop in edit mode and checked its `eval.md`. Preserved substantive sentences, tables and source names, and used direct verbs and consistent terminology. Removed conversational framing, repeated interpretation, puffery and decorative punctuation from the edited prose. Applied zero-slop's research/professional mode, performed-register review and fact check. Used thai-natural-writing for the Thai read-through, with particular attention to natural subjects, modifier order and consistent technical terms.
- Updated the [figure plan](../../writing/is2/mwd/FIGURE-TABLE-PLAN.md). The Figure 1 caption follows the guide verbatim in both languages. Figure 1 is introduced in §3.1 and anchored at the start of §3.4 so it appears beside the cutoff methods in Word. Figure 2 retains its assets, states the three test statuses and identifies +10 pp as the prespecified usefulness threshold. Estimates, intervals and event-drug counts appear in the results text. The plan gives the artwork labels and dimensions for the redraw.

## Before and after checks

| Check | Before | After |
| --- | ---: | ---: |
| Zero Slop `--formal`, English abstract and body prose | 11.2/100 | 11.2/100 |
| Zero Slop `--formal`, complete EN Markdown | 10.7/100 | 10.7/100 |
| Performed register, EN rhetorical setups or question headings | 7 | 0 |
| Performed register, TH rhetorical setups or question headings | 7 | 0 |
| Performed register, EN desk metaphor | 2 | 0 |
| Performed register, TH desk metaphor | 1 | 0 |

The prose scoring input includes the English abstract, body headings and captions. It excludes tables, image links, references and embedded link targets. Both scores remained in the tool's clear range. The one located wording flag was “utilization” in the official name State Drug Utilization Data. The other flag was a document-level word-variety diagnostic. The English lexical score was used for English only. For each language, the seven rhetorical findings comprise the introductory setup, the background question, four result headings and the H2 question. Research questions as statement-of-purpose content were not counted. The manual read found zero before and after for antithesis pairs, significance scaffolding, epigrams, one-word drama beats, hyperbole, slang, compressed jargon and meta-taglines.

| Fidelity check | EN | TH |
| --- | --- | --- |
| Raw Zero Slop `--fidelity` | Exit 1, 241 numeric items, 25 quotations and 31 URLs retained | Exit 1, 239 numeric items, 25 quotations and 31 URLs retained |
| Structural changes identified by the checker | Figure 1 path replacement, 23 → 24 headings | Figure 1 path replacement, 23 → 24 headings |
| Name heuristic flags | “Auto” removed, “Reviews Ahead” and “Vertical” added | “Be Reviewed” and “How Well Does Regulatory Evidence Capture First” removed |
| Direct comparison | PASS | PASS |

The name flags are title fragments, a sentence opener in a caption and the expanded automatic-clearance wording. Direct checks confirmed all 12 guide passages, unchanged numerical literals and signs, unchanged tables and reference sections, identical cited links, and verbatim AI acknowledgments. A section-by-section TH/EN read verified the endpoint, scope, comparative claims, confidence intervals and test dispositions against the original drafts and resolved the snapshot-sponsor wording from the aggregate receipt. The English and Thai abstract paragraphs are byte-identical across editions when read as UTF-8 text with normalized line endings.

## Local build

Built both Markdown-backed content modules with the KMITL `make_paper.py` Word renderer from `docs/writing/is2/mwd/build/`, using the existing content modules and figure directory.

| Edition | Abstract length | Word PDF pages | Earliest nonfinal body column end |
| --- | ---: | ---: | ---: |
| EN | 142 whitespace-delimited words | 9 | 698 pt |
| TH | 172 PyThaiNLP 5.4.0 `newmm` tokens excluding whitespace | 9 | 689 pt |

The first render flagged early column ends in both editions. Moving the Figure 1 anchor, shortening the Figure 2 caption and moving Table 2 resolved the Thai flags. A paragraph break in the English reimbursement result resolved the remaining English flag. The final runs exited 0. All nonfinal body columns ended within 40 pt of the 720 pt bottom margin. Visual inspection of pages 5–7 confirmed figure captions below figures and table captions above tables. The builder's separate short-last-line heuristic still flagged nine blocks in each edition; the main planner can check those after the final figures and Track A text are in place. PyThaiNLP was reused from the [IS2STORY tokenizer installation](IS2STORY.md).

## Planner handoff

- Each conclusion contains one `[FREEZE STATUS]` marker. In both editions, 27 November 2026 is the forecast reference date. Replace the marker with the verified package generation and timestamp dates and C9/freeze status from the freeze receipt. The forecast count and follow-up deadlines are retained.
- Figure 1 used local copies of the old decision artwork for measurement. The existing Figure 2 still contains its older artwork labels. The main planner supplies the timeline images, updates the Figure 2 artwork labels and rechecks the pages, caption fit, short lines and embedded image resolution with the final assets. Generated DOCX, PDF and copied PNG files are local build inputs or outputs and are excluded from the commit.
