# IS2AUDIT main-planner audit receipt

**DONE on 28 November 2026.** The main planner audited both IS2 editions against the co-planner critique and the receipts, and applied every blocker and major fix. The drafts are ready for the KMITL template build. Pagination is unverified until the template renders.

## Inputs

- Drafts at `6f803c57`: [English](../../writing/is2/mwd/IS2-DRAFT-EN.md) and [Thai](../../writing/is2/mwd/IS2-DRAFT-TH.md).
- Co-planner critique (GPT-6.2 Astra high, 28 November 2026). Verdict: revise before final audit. The confirmatory numbers and decisions were correct in both editions. It found two blockers, three major issues and one minor group.
- Sources of every number: [SCORE](SCORE.md), [SCORELLM](SCORELLM.md), [FREEZE](FREEZE.md), [C2](C2.md), [C3b](C3b.md), [C4b](C4b.md), [EVP](EVP.md) and [UIBUILD](UIBUILD.md). The planner rechecked each new figure against its receipt table.

## Changes

| Critique item | Disposition |
| --- | --- |
| B1. SCORELLM still reported as pending | New Table 1 gives C′ recall for B1, M1, M3, L1 and L1e at both horizons. §4.3 reports the paired L1e − M3 and L1e − L1 contrasts with intervals, 9,898 schema-valid forecasts, and the single-checkpoint and pretraining-exposure limits. |
| B2. Figure 1 says the test is pending | Both Figure 1 artworks now say "Sealed test (C′): H1 passed". The unbuilt "swappable models (OpenAPI · MCP)" footer was replaced with the decision-support notice. The figures were re-rendered at 3000×1620 and embedded. Figure 2 is embedded, and its caption now gives the event-drug counts (development 67 and 90, C′ 202 at each horizon). |
| M3. Lead with the measured decision | The abstracts and the opening paragraph lead with the assumed capacity, the US approval endpoint, the H1 result and M1 at 65.49%. §4.1 reports C′ before development. H3 is described as descriptive because H2 stopped testing. M1 − B1 is reported with intervals and without a causal reading. The cutoff table moved into §3.2 prose. |
| M4. Scoring lock and amendments | §3.4 describes updates 1–3, their times relative to the 05:12 UTC gate, and that C′ was scored under updates 1–2. §3.2 names the specific prior exposures. |
| M5. Evidence roles and placeholders | C3 Methods cover both the 2013 development cutoff and the 2017–2023 C′ cutoffs. The Track A placeholder is now a dated disposition. The dossier placeholder now reports the C8 audit (1,789/1,789 traceable, 1,757 hash-backed, source integrity only) and the EVP yields (C6 3/5, C7 17/17, Thai status 0/6). |
| m6. References and front matter | [2] cites the program listing without an empirical claim. [30] lists the DOI's deposited creator. [31] is pinned to `3e06537b`. The price ratio is 46.5%. The duplicate Paper 53 sentence was removed. Per D5, the English byline reads "Tuchsanai Ploysuwan", with the title only in footnote 2. Per D6, an AI-use acknowledgment was added. |

Abstract lengths are 190 English words and 246 Thai tokens (PyThaiNLP newmm). The Thai abstract now carries the US-prioritization conclusion. README and `docs/assets/market-window-flow.svg` were brought up to date with the C′ result, the OSF DOI and the product status.

## Limitations and next action

- The English text from §1 to the references is about 4,900 words including tables, so a ten-page overrun is a real risk. The KMITL template build decides it. If it overruns, move Table 4 (development LLM) and the development paragraphs into a short appendix or the IS2 report.
- Track A and C9 results remain pending in the text by design.
- **Next:** build the KMITL docx (TH and EN) with the kmitl-is-paper skill, check pagination and caption placement, then make the IS2 slides.

## Final audit after IS2FIT (28 November 2026)

**DONE.** IS2FIT (merged) cut the body by about 40% and both editions now render at 10 pages in Word. The main planner reread the English body in full and checked numbers mechanically. Against the audited base, the only new numeric strings were sign-formatted forms of existing values: development CIs written with "+", and L1e − M3 written as a signed difference. Both abstracts are unchanged. IS2FIT reported an emphasis difference between the two abstracts. **Correction (28 Nov 2026, night):** the planner dismissed this in error, because it compared each file's own-language abstract only. The Thai abstract inside the English edition was the pre-audit version: it had M1 − B1 +19.01 and lacked the 7B result. The co-planner storytelling review found it. Both editions now carry the identical audited Thai and English abstracts, the Thai one from IS2-DRAFT-TH and the English one from IS2-DRAFT-EN. Rebuild the docx and PDF before delivery. The planner also checked the rendered contact sheets of all 20 pages: captions sit below figures and above tables, the tables are intact and no column ends early.

Deliverables were copied to `C:/Users/User/Desktop/IS2-MWD/` for the owner. They are local only and covered by the build ignore rules.

| File | SHA-256 |
| --- | --- |
| `IS2-MWD-EN.docx` | `682153258ef7df4a819bb805c45daad3814c9905ea334b77ca042beaadafac31` |
| `IS2-MWD-EN.pdf` | `d838230191f4307622016a31f1251a46a4d17030400379d3e92b30a1905c887c` |
| `IS2-MWD-TH.docx` | `8f01a433059dce1286da6e11f8f9ccdbadb558c070b0701b09f6f0a23e6231e3` |
| `IS2-MWD-TH.pdf` | `3cb4e0f4ddbfbdbf991e178db9687171f0df9fd751b4387552751e862d7cc98e` |

**Next:** the IS2 slides (Claude). The C9 and Track A text updates follow the freeze.

## Audit of IS2STORY (28 November 2026, night)

**DONE.** IS2STORY (merged) retells the paper on the owner's choices: the question-form title, opening A from IS1, reader-friendly names with the registered IDs in parentheses, the result order following the reader's questions (H1, then H2 with H3 descriptive, then the 7B model, C3/C4 and one dossier), and a "meaning for a drug team" line after each result. It uses the new Figure 1 (`fig1_decision_*`, Claude design).

- **Mechanical checks.** The only new numbers are the IS1 bridge values (435, 692, 100), the Track A count 651 and its maturity year, the §4.4 heading number, and US patent 6017927 in the solifenacin dossier example (source: EVP).
- **Wording.** None of the forbidden phrases appears. "In progress" refers only to the freeze, which is accurate.
- **Abstracts.** The abstracts are identical across editions (EN 130 words, TH 152 tokens).
- **Layout.** Word renders both editions at 9 pages, within the 8–10 limit. The planner checked the contact sheets.

| File | SHA-256 |
| --- | --- |
| `IS2-MWD-EN.docx` | `b688299e87ed49226753bcec0d26d07c92234db224b34e349de2ce7f28ce9ec0` |
| `IS2-MWD-EN.pdf` | `abe52239b5fd15ef00de53c750f5c5541be748925f85ad582efec7e747f00f89` |
| `IS2-MWD-TH.docx` | `432e109365c332802669157619da21635a244a7eb02755b02e7aa0eaa98d7bf4` |
| `IS2-MWD-TH.pdf` | `40cb1771bf30ab448788b01e636c700b002b455bf6b7a9aa65668d6883a9254f` |

**Next:** update the §5 freeze sentence and the C9 status after TRACKA-FREEZE, then the slides follow this story.

