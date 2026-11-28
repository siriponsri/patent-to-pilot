# Track IS2: Independent Study 2 (KMITL)

IS2 covers **Market Window Dossier**, with **LOE-Bench** as its research benchmark. Authors are **Siripon Srihangpiboon** and **Asst. Prof. Dr. Tuchsanai Ploysuwan**. Use the KMITL template for the Thai and English draft due by 31 December 2026. The final is due by 31 January 2027. [D41 plan and weekly schedule](../../loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026).

## Current study and dossier

P1 addresses scarce freedom-to-operate (FTO) evaluators with a review queue, a dated evidence pack and a verification checklist. The dossier supports the evaluator's decision. Qualified counsel gives any FTO opinion. P2 addresses demand lost before launch by forecasting entry timing, competition, price erosion and demand before bioequivalence or comparative trials.

Start with an ingredient, form, jurisdiction, decision date and planned launch date. The planned workflow forecasts the launch window, assembles competition and patent evidence, fills Thai and ASEAN status rows, generates the evaluator checklist and produces a one-molecule dossier. The Thai decision page is followed by bilingual technical sections.

| Component | IS2 evidence and status |
|---|---|
| C1 · First-generic review queue | Confirmatory design with H1 → H2 → H3 at a 20% review budget. Configuration frozen on development data. |
| C2 · L1e | Exploratory LLM arm with the same as-of evidence as M3. Freeze before OSF. |
| C3 · Competition at launch | Exploratory endpoint of at least three distinct approved ANDA applicants within 36 months, scored on frozen queues. Freeze before OSF. |
| C4 · Demand baseline and volume forecast | Exploratory CMS Medicaid SDUD analysis with a naïve-with-drift baseline. Use verified as-of release vintages where available. Label the other analyses retrospective and vintage-uncontrolled. Freeze endpoint and baseline before OSF. |
| C5 · Price erosion | Scenario using FDA medians by number of producers, with assumptions stated. |
| C6 · Patent evidence pack | Development-only descriptive pilot with a document-backed restricting patent label, patent type and a ranked checklist. |
| C7 · Thai and ASEAN status | Descriptive family and status trace from regional and Thai sources. Mark failed lookups as unknown. |
| C8 · Report generator | Scripted audit with a 100% traceability target. Each claim has a citation, a known/unknown/not-applicable state and an observed/estimate/assumption label. |
| C9 · RL arm | Exploratory, pending the co-planner plan and week-one decision. Track A is the clean test. |
| C10 · Novice reader test | AI4BA volunteers only if KMITL ethics clearance arrives in time. |

Use these seven dossier sections in order.

1. BD/R&D decision page
2. Market window
3. Competitive landscape
4. Patent and exclusivity landscape
5. Thailand and ASEAN
6. FTO evaluator hand-off checklist
7. References and reproducibility appendix

Use the [lane handoff](../../loe-bench/HANDOFF.md) and [FREEZE receipt](../../loe-bench/receipts/FREEZE.md) for current evidence. Frozen development recall differences in percentage points (95% CIs) are H1 +9.80 [+0.14, +19.65], H2 +5.49 [−2.00, +11.25] and H3 +13.00 [+3.27, +23.17]. There is no confirmatory result. L1 received only ingredient identity, cutoff and horizon, so its comparison cannot answer how an evidence-matched prompt performs. [L1DEV receipt](../../loe-bench/receipts/L1DEV.md).

The [weekly schedule](../../loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026) covers development and preregistration v2 by 6 December, owner OSF submission on 7–13 December, blinded C′ gate and scoring as permitted on 14–20 December, and traceability and reproduction on 21–27 December. Mark unrun analyses in the December draft. Retrain on matured windows and freeze Track A in January before fetching any later outcomes. Verify the freeze before 2027-01-31 23:59 UTC for the final IS2.

## Earlier IS2 materials

The earlier IS2 direction covered the IS1 committee response on Paper 53, the B53 first-stage substitution study on DAPFAM and possible use of the owner's unpublished conference work. Paper 86 is allowed only in IS2. See the [original-source record](../../evidence-scope/00-organization.md#original-source-corrections), the [English short-paper draft](IS2-SHORT-PAPER-DRAFT-EN.md) and the [B53 results](results/). The [bilingual draft](IS2-SHORT-PAPER-DRAFT.md) is an input to the previous faculty-template exporter, which parses specific Thai section headings.

| File | Content | Status recorded on 19 November 2026 |
|---|---|---|
| `COMMITTEE-RESPONSE-DRAFT.md` | point-by-point response K1a-K2b with measured evidence and limits (moved from `plans/` 19 Nov) | draft |
| `K1a-PATEMBED-RATIONALE.md` | why Paper 53 used patembed-base (Thai + English): Paper 53's own record (refs [5],[18]) + model card + labelled retrospective evidence; v2 removes the withdrawn arXiv:2605.24297 | draft v2, ready for owner review |
| B53 plan | `docs/healthtech/research/plans/B53-FIRST-STAGE-SUBSTITUTION-DRAFT.md`; readiness receipt `paper1-bridgeret/b53-readiness-20261119.json` | not frozen, NOT_RUN |
| `PAPER86-AND-P1DAPFAM-SELECTION.md` | which Paper 86 parts enter IS2 (S1 exposure, S2 retriever ordering, S3 window accounting; S4 context only) and the one-paragraph P1-DAPFAM reference | done 19 Nov (agent, owner-delegated) |
| Paper 86 sources | outside this repo: `C:/Users/User/Desktop/myDegree/IS/IS_2/` (Paper 86 withdrawn from IEEE; unpublished own work), `myIS` repo | referenced only |

Historical outline proposed on 19 November 2026:
1. Introduction: Paper 53 recap and the committee's comments.
2. First-stage choice and its limits (K1a, K1c language policy).
3. B53: what changes when only the first stage changes (K1b, K2a); B53.0 comparison with the DAPFAM benchmark paper.
4. Paper 86 material (owner to decide which parts).
5. Implications for patent examiners (K2b; proxy measures only, no user study yet).
6. Link to the journal track (one paragraph pointing to Paper 1 as follow-on work; no Paper 86 text flows back).

The 19 November proposal selected Paper 86 sections in the file above and allocated one short reference to P1-DAPFAM. Repository-authored documents use English.
