# IS2R · Bilingual short-paper revision

**Disposition: revised drafts ready for main-planner audit.** `loe/IS2R` starts at `c3327babc813fe6468fb04d5b54025fcff634b17`, verified against `origin/research/loe-bench` after fetch. The card’s writable paths are the [Thai draft](../../writing/is2/mwd/IS2-DRAFT-TH.md), [English draft](../../writing/is2/mwd/IS2-DRAFT-EN.md), [figure and table plan](../../writing/is2/mwd/FIGURE-TABLE-PLAN.md) and this receipt. This receipt is the executor handoff for planner integration.

## Adopted findings

| Finding | Applied in both editions | Evidence |
| --- | --- | --- |
| 1. Figure 1 status | §3.1 and the caption identify the proposed workflow, completed historical development evaluation, pending C′ admission and scoring, pending Track A freeze and pending claim-level audit. Demand and price are scenario outputs. The plan preserves the corrected SVG wording during layout. | [Corrected SVG](../../assets/market-window-flow.svg) · [Protocol](../PREREGISTRATION.md) |
| 2. Practical usefulness and power | Both abstracts and §§3.3, 4.1 restore the +10 pp threshold. Both 24-month estimates fall short on the point estimates (+9.80 and +5.49 pp). At 12 months, M3 gains +13.00 pp over B1 and ties M1 at 61.11% recall. §3.3 gives 49.96% simulated H1 power at +10 pp with 75 event drugs and identifies 50 event drugs as the admission minimum. §5 states that dated regulatory predictors warrant further evaluation and the graph’s incremental value remains uncertain. | [FREEZE](FREEZE.md#development-results) · [T4c](T4c.md) · [Protocol](../PREREGISTRATION.md) |
| 3. Exposure, fixed sequence and timing | §3.2 discloses aggregate B0–B2 exposure from the earlier 36-month evaluation on overlapping periods and drug histories. §§3.3–3.4 and 4.1 call for two-sided intervals for all estimable contrasts, descriptive labels for unreached steps and feasibility only on final gate failure. OSF is pending. Track A’s external timestamp is due before 2027-01-31 23:59 UTC and before any post-origin outcome fetch. | [Protocol](../PREREGISTRATION.md) |
| 4. Measurable opening and gap | Both abstracts and §1 open with event capture at one-in-five review capacity. §1 states 20% is a design assumption and gives the development and specialist-review motivation afterward. §2.1 identifies Hu and Hopefl as external precedents for first ANDA submission and defines the measured endpoint as first final ANDA approval. §5 reserves commercial launch, Thai demand, reviewer time savings and product-specific FTO assessment for future work. | [Protocol](../PREREGISTRATION.md) · [Hu et al.](https://doi.org/10.1002/cpt.1479) · [Hopefl et al.](https://doi.org/10.1111/cts.70365) |
| 5. Exploratory scope and controls | §4.2 gives C3b’s 15.000 versus 9.625 expected event captures out of 21 at the single 2013 development cutoff, with 107 slots per arm, the fractional tie rule and the +25.60 pp [6.25, 45.00] interval for the at-least-three-applicants endpoint within 36 months. Both abstracts identify Qwen2.5-7B-Instruct, development data and the joint evidence/prompt change. §4.2 reports higher MAE after the 0.465 adjustment and adds the queue-linked drift contrasts to the reimbursement table. §3.5 identifies C5 as assumption-based. §4.3 reports C9 as an optional prospective 1.5B GRPO/SFT comparison with training and outcomes `NOT_RUN`. | [C3b](C3b.md) · [C2](C2.md) · [C4b](C4b.md) · [Protocol](../PREREGISTRATION.md) · [C9](C9.md) |
| 6. IS1 bridge and bibliography | §1 attributes near-zero instruction effects to the authors’ prior report and uses the conference listing for title and authorship. The bridge moves from the fixed patent candidate pool to what a reviewer can recover at a fixed cutoff and budget. References [2], [3], [9], [16] and [21] use corrected journal or conference metadata. Both editions retain IEEE first-citation order. | [Paper 53 listing](https://isai-nlp2026.aiat.or.th/program) · [Hu et al.](https://doi.org/10.1002/cpt.1479) · [Hopefl et al.](https://doi.org/10.1111/cts.70365) · [Reiffen and Ward](https://doi.org/10.1162/0034653053327694) · [Paleka et al., ICLR](https://openreview.net/pdf?id=z85kARAoyD) · [Turtel et al., TMLR](https://openreview.net/pdf?id=bbhdeL8EUX) |
| 7. Terminology | Thai §1 uses “ชุดเอกสารสิทธิบัตรที่นำมาจัดอันดับ”; the first Thai use defines “ชุดส่วนออกฤทธิ์ของยา (active-moiety set)” and §2.4 defines “การสุ่มซ้ำแบบจับคู่ระดับตัวยา (paired whole-drug bootstrap).” Both abstracts expand FDA at first use. The English M1 relative clause closes before the main verb. | [Thai draft](../../writing/is2/mwd/IS2-DRAFT-TH.md) · [English draft](../../writing/is2/mwd/IS2-DRAFT-EN.md) |
| 8. Layout and length | §4.1 places Figure 2 where the old recall table appeared. The plan supplies H1/H2/H3 estimates, both interval bounds and distinct event-drug counts of 67/67/90, with reference lines at 0 and +10 pp. §3.4 replaces the timeline figure with a prose sentence. The reimbursement and language-model tables are now Tables 2 and 3. | [FREEZE](FREEZE.md#development-results) · [Figure and table plan](../../writing/is2/mwd/FIGURE-TABLE-PLAN.md) |

## Pending placeholders in both drafts

| Location | Placeholder | Resolution |
| --- | --- | --- |
| §3.4 | `[OSF DOI PENDING]` | Insert the verified registration identifier after registration. |
| §4.1 | `[FIGURE PLACEMENT: development paired-effect plot]` | Main planner renders the plot using the figure plan. |
| §4.1 | `[RESULT PENDING: blinded C′ admission verdict and disposition]` | Enter the authorized blinded verdict. A final failure limits C′ to feasibility reporting. |
| §4.1 | `[RESULT PENDING: C′ H1–H3 estimable contrasts with two-sided 95% intervals, practical-usefulness checks, reached-step decisions and descriptive labels for unreached steps]` | Populate only after authorized scoring. On final gate failure record that H1–H3 remained untested. |
| §4.1 | `[RESULT PENDING: Track A timestamped prediction freeze and outcome readouts]` | Verify the external timestamp and report each readout at maturity. |
| §4.3 | `[RESULT PENDING: dossier claim-level traceability audit]` | Insert the audited traceability finding after the workflow audit. |

## Length and verification

| Language | Abstract words | Body words (§§1–5) |
| --- | ---: | ---: |
| Thai | 239 | 4,767 |
| English | 185 | 3,319 |

Counts use locale-aware Node `Intl.Segmenter` word boundaries. Body counts include headings, captions and table cells. Counts exclude source-link labels, numeric citation markers, pending editorial markers, title and author matter, keywords and references. Both abstracts also remain below 250 with source-link labels counted (Thai 246, English 190). The bilingual front matter is duplicated by design across editions. The word count is the length check for this card. Pagination in the faculty template remains pending until the planner renders Figure 2 and typesets the editions.

**PASS:** Abstract and bibliography parity, matching placeholders, IEEE citation order, source-checked effect values and plot tuples, local links and fragments, and Markdown diff whitespace. Two automated edit passes stopped at unmatched text selectors before writing files. The corrected passes matched and saved the intended sections. No adopted finding was omitted. Figure 2 rendering and final layout are planner work. Test suite and scientific analyses were `NOT_RUN` for this documentation-only card. Review used documentation and aggregate receipts, and the protected test seal remained closed.
