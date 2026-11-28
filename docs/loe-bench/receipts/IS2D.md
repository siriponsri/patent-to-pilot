# IS2D | Bilingual Market Window Dossier short-paper draft

**Status:** Draft ready for the assigned methodological critique and main-planner audit. Both editions include both abstracts, the same manuscript sections, four inline tables and the same bibliography. The figure plan identifies the existing design graphic and the timeline placement. The body remains in Markdown for this card. The KMITL two-column TH SarabunPSK layout and the 8–10 page target require verification when the manuscript is typeset.

**Assignment and basis:** Antigravity Gemini 4 Hydrogen became unavailable after reaching its quota. On 28 November 2026 the owner approved GPT-6.2 Sol high as drafter. Unpublished partial text survived in Gemini's separate worktree and informed this revision. The assigned critique remains with GPT-6.2 Astra high, followed by Claude Opus's final audit. Fetched `research/loe-bench` at `b06a1eec104b2f892f0b75adf3e312f1099b0cfa`, a descendant of `fdf7d03a`. The existing local `loe/IS2D` is checked out in the stopped Gemini worktree and contains its uncommitted partial draft. The final files are committed in the assigned T3 worktree and are published to `refs/heads/loe/IS2D` by explicit refspec. [Owner decision](../../maintenance/OWNER-DECISIONS-20261122.md)

- [Thai manuscript](../../writing/is2/mwd/IS2-DRAFT-TH.md)
- [English manuscript](../../writing/is2/mwd/IS2-DRAFT-EN.md)
- [Figure and table plan](../../writing/is2/mwd/FIGURE-TABLE-PLAN.md)

## Number and identifier ledger

Rows cover both editions, including repeated abstract values and table entries. Structural numbering belongs to the manuscript or template. Bibliographic years, volumes, pages and identifiers reproduce the verified seed entries. No new estimates were computed.

| Location | Numbers and identifiers used | Repository evidence |
| --- | --- | --- |
| Front matter | Author markers 1 and 2, No. 1 and Soi Chalong Krung 1, Bangkok 10520, 68076060@kmitl.ac.th | Owner's IS2D task card and owner-local KMITL `docs/owner/short-paper/Template-short-Paper-IS1-2 (AI4BA).docx`. The task card supplies the author details and email. |
| Introduction and RQ1 | H1 M3 − B1 at 24 months, H2 M3 − M1 at 24 months, H3 M3 − B1 at 12 months, fixed sequence, 20% queue, one-sided α = 0.025 | [FREEZE](FREEZE.md), [T4c](T4c.md), [PREREG2](PREREG2.md), [protocol](../PREREGISTRATION.md#research-questions-and-hypotheses) |
| RQ2 and methods | At least 3 approved applicants within 36 months, 24-month frozen queue at the 2013 cutoff and up to 12 months to locate an applicant listing | [C3b](C3b.md), [C3](C3.md), [protocol](../PREREGISTRATION.md#secondary-and-exploratory-analyses) |
| Introduction and Reference [1] | Paper 53, iSAI-NLP 2026, near-zero instruction contrasts, original run records unavailable | [IS2 bridge](../owner-source/package-docs/02-IS2-LINK-TO-PAPER53.md), [verified bibliography, theme T8](../../writing/is2/mwd/LIT-REVIEW-BRIEF.md#t8--authors-prior-work-and-the-is1-bridge) |
| Methods and Table 1 | Exact TYPE 1 and ORIG/AP eligibility and endpoint, six-calendar-month edition window, 1 January cutoffs, TRAIN 2010, validation 2012–2015 and 2013–2014, sealed schedules 2017–2025 and 2017–2024, observation end 27 November 2026 | [FREEZE](FREEZE.md), [FIX1](FIX1.md), [FIX2c](FIX2c.md), [E2b](E2b.md), [PREREG2](PREREG2.md), [protocol](../PREREGISTRATION.md#splits-and-blinded-admission) |
| Methods | B1, M1 and M3, L2 logistic fit, three graph states, capacity equal to one fifth rounded down, 2,000 paired draws and two-sided 95% intervals | [FREEZE](FREEZE.md), [T4c](T4c.md), [PREREG2](PREREG2.md), [frozen model configuration](../../../loe-bench/data/FROZEN_CONFIG.json) |
| Methods, planning power | About +14 pp to reach 80% power at 75 event-drug clusters for H1, conditional on the simulated design | [T4c](T4c.md) |
| Admission, Track A and Figure 2 | All-cutoff edition coverage, at least 50 distinct 24-month event drugs, one technical retry, B3, origin 27 November 2026, freeze before 31 January 2027 23:59 UTC, maturities 27 November 2027 and 27 November 2028 | [FREEZE](FREEZE.md), [PREREG2](PREREG2.md), [protocol and release rules](../PREREGISTRATION.md#track-a-prospective-protocol) |
| Methods, Medicaid scenario | 12-month queue, next year and fourth-quarter targets, 0.465 multiplier with two producers | [C4b](C4b.md), [protocol](../PREREGISTRATION.md#secondary-and-exploratory-analyses) |
| Methods, LLM and optional RL | L1/L1e Qwen2.5-7B-Instruct identity and evidence cards, optional paired GRPO versus SFT on Track A at 24 months | [L1DEV](L1DEV.md), [C2](C2.md), [C9](C9.md), [PREREG2](PREREG2.md) |
| Abstracts and Table 2 | 24-month B1/M1/M3 recall 39.65/43.96/49.45%, 12-month 48.11/61.11/61.11%. Paired H1 +9.80 [+0.14, +19.65], H2 +5.49 [−2.00, +11.25], H3 +13.00 [+3.27, +23.17] pp. Development 12-month: 2,161 rows, 90 events, 90 event drugs, 430 slots. Development 24-month: 1,083 rows, 91 events, 67 event drugs, 215 slots | [FREEZE development results](FREEZE.md#development-results) and [machine receipt](../../../loe-bench/data/FREEZE_dev_report.json) |
| RQ2 results | 2013: 539 rows, 107 slots, 21 event drugs. M3 71.43%, B1 45.83%, +25.60 [+6.25, +45.00] pp, same sensitivity result | [C3b development queue result](C3b.md#c3-development-queue-result) |
| RQ2, Table 3 | Four linked origins. Q4: 160 pairs, 68 ingredients, B1 +372.05 [193.27, 587.26] and M3 +381.24 [203.61, 606.77] USD per prescription. Annual: 150 pairs, 64 ingredients, B1 +4.98 [2.24, 8.29] and M3 +21.43 [4.07, 53.21] million USD. Gross per-prescription rise is a descriptive reading of the observed linked data and signed underprediction | [C4b](C4b.md), [lane memory, 28 Nov](../MEMORY.md) |
| RQ3, Table 4 | All eight rows are copied from the C2 recall, queue precision and grouped AP table. L1e − M3: −36.87 [−47.40, −23.92] and −30.37 [−43.08, −16.44] pp. L1e − L1: −10.68 [−17.96, −3.63] and −9.51 [−16.26, −2.43] pp | [C2 development results](C2.md#development-results) and [machine receipt](../../../loe-bench/data/L1E_DEV_RESULTS.json) |
| Dossier and figure labels | Figure 1 follows the existing system flow. Figure 2 follows the design milestones. Tables 1–4 index the schedules and outputs above. No product audit-rate target is reported as an observed result | [D41 plan](../PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026), [E5](E5.md), [Thai open-data report](../THAI-OPEN-DATA.md), [technique ledger](../TECHNIQUE-LEDGER.md), [system graphic](../../assets/market-window-flow.svg) |
| References [1]–[21] | Years, identifiers, volumes, issues and pages copied by source. Draft-to-seed order: 47, 2, 1, 5, 8, 12, 14, 13, 18, 16, 21, 23, 24, 43, 46, 32, 33, 36, 38, 39, 28 | [Verified seed bibliography](../../writing/is2/mwd/LIT-REVIEW-BRIEF.md#seed-bibliography-by-theme) |

The project framing was checked against the [README](../../../README.md), [D41](../PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026), [handoff](../HANDOFF.md) and [lane memory](../MEMORY.md). The KMITL template text, local `kmitl-is-paper` guide and audit checklist, and the prior short-paper preview informed the structure and style. A registration reference will be added once the assigned team has the official record.

## Open markers and conditional fields

Seven result placeholders occur once in each language edition, for fourteen total occurrences.

- Blinded C′ admission verdict and disposition.
- H1 C′ recall difference, 95% interval and decision.
- H2 C′ recall difference, 95% interval and decision if reached.
- H3 C′ recall difference, 95% interval and decision if reached.
- Track A timestamped freeze and matured outcomes.
- Dossier claim-level traceability.
- Optional GRPO versus SFT comparison if admitted.

Each edition also contains one OSF DOI marker, one timeline placement marker and one citation-needed marker. That yields ten distinct open markers and twenty occurrences across both drafts. The citation-needed item is empirical evidence on FTO reviewer capacity in Thai generic and biosimilar development. The text treats limited capacity as a project design concern. No independent IS1 bibliographic entry is included pending verified metadata, and Paper 53 is cited as a conference-program listing.

## Editorial checks and handoff

| Check | Thai body edition | English body edition |
| --- | ---: | ---: |
| Body prose, sections 1–5 | 4,794 words | 3,615 words |
| Section 2 prose | 989 words | 717 words |
| Thai abstract | 222 words | 222 words |
| English abstract | 154 words | 154 words |

Counts use locale-aware ICU word segmentation and include word-like numeric tokens. They exclude headings, captions, tables, front matter, bibliography, inline source links and editorial markers from body counts. This is an editorial estimate. Actual page count, final line breaks, typesetting and figure readability have status `NOT_RUN`.

- **PASS** for the Markdown checks on section order, matched abstracts, reference order, numeric parity, local links, caption text and placeholder parity. Development values come from the frozen sources and the result slots remain open. No experiment or protected test data was accessed.
- At layout, localize the existing system figure and revise its evaluation labels and accessible description to reflect the still-pending sealed test and prospective freeze. Both Markdown editions already explain that the current graphic depicts a design. The timeline also needs typesetting. No image file was created or modified.
- Before finalization, the main planner should confirm the approved author metadata and template page geometry. The template's prose and skill describe different paper sizes. Verify the rendered template sections at export.
- Replace Section 2 with the owner-supplied SciSpace review after checking the evidence and renumbering the references in both editions. Keep the FTO capacity citation open until a suitable empirical source is available.
- After the OSF-issued PDF, blinded verdict and authorization are available, the analysis lead can fill the C′ fields from released results. A final gate failure leaves the C′ hypotheses untested. Record the prospective timestamp separately from any outcome result. Fill the dossier audit and optional paired-arm fields only from their own receipts.

This receipt is the executor handoff and project-memory entry. The lane handoff and memory remain with the main planner at integration.
