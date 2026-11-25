# IS1 committee response matrix for Paper 53 and IS2 (v2)

> **Historical correction, 22 November 2026.** The 37.1% figure was held pending inspection of the original table. The subsequent [source-page check](../../evidence-scope/00-organization.md#original-source-corrections) confirmed 257/692 queries for Paper 53. B53 independently measured exposure of 0.371 at rank 100 on 905 queries.

The 19 November 2026 draft drew on the following records.
- Individual IS1 assessment on 15 November 2026, score 85/100, grade S.
- Owner files `owner-note-19112026/09_PAPER53_BRIDGE_AND_COMMITTEE_RESPONSE.md` and `PTP_IS2_Paper53_Research_Program_University_Impact_2026-11-19.md`.
- Recorded repository measurements.

Each number carries an evidence label from section 3. The original Paper 53 judgments, pools and per-query records were unavailable for replication.

## 1. Responses for IS2 Appendix D

| ID | Committee comment | IS2 response | Evidence | Classification | Chapter | Status at draft |
|---|---|---|---|---|---|---|
| K1a | Explain the choice of patembed-base as the sole first stage. | Identify the rationale recorded in Paper 53 (PatenTEB and the model card), label retrospective evidence, then report the B53 direct comparison. | `K1a-PATEMBED-RATIONALE.md` v2 | HISTORICAL RECORD + MEASURED on a different cohort | 2, 6 | Draft complete, awaiting owner review |
| K1b | Only 37.1% of queries exposed a relevant item in the top 100. Try BM25 and hybrid retrieval. | B53 F1 = BM25, F2 = RRF(BM25, F0), F4 = RRF(BM25, F3), at K=100 (primary) and 200. Measure exposure, first-hit rank and zero-exposure rate. | B53 Stage 1 (`results/B53-STAGE1-RESULTS.md`): F0 exposure at 100 was 0.371; BM25 −0.105, RRF(BM25,F0) +0.004 (not significant), Arctic −0.054, RRF(BM25,Arctic) −0.035. | MEASURED | 3–4 | Measured 19 November |
| K1c | Avoid a causal interpretation of the RQ2 identity. | Use Δ_all = π·Δ_exp for accounting only, when unexposed contributions are zero for every arm sharing a pool. B53.1 intervenes on the first stage and measures the resulting exposure change. | Owner file 09, section 6, language policy | METHOD | 3, 6 | Wording agreed |
| K2a | Change the first stage to test whether retrieval limits performance. | B53 varies the first stage while fixing the reranker (Qwen3-Reranker-0.6B, four Table I instructions plus BGE plain), depth, TAC rendering, labels and evaluator. | B53 Stage 2 (`results/B53-STAGE2-RESULTS.md`): none of 10 instruction contrasts reached significance on C = 153 (Δ +0.001 to +0.009, Holm p ≥ 0.695). Scrambled ≈ Generic. Instruction effects were near zero for every first stage. | MEASURED | 3–4 | Measured 22 November |
| K2b | What does an examiner gain? | Report zero-exposure rate (1−π), first OUT-hit rank, reading depth at K=100 and 200, and cost per recovered citation. Demonstrate Solution Scout and document the proposed interviews. User benefit remains NOT_MEASURED. | B53 metrics and demo | HYPOTHESIS / NOT_USER_VALIDATED | 5 | Designed |

## 2. Available measurements and limits

| Question | Observation | Source | Limitation |
|---|---|---|---|
| K1b, BM25 and hybrid on DAPFAM | DAPFAM DEV (349 OUT): dense B0 (PatEmbed-large) OUT R@200 0.1477, BM25 0.0690, RRF −0.0197 (IN −0.0555). | `paper2-precheck/HEADROOM-RESULT.md` | Different encoder (large), depth 200 and cohort from the 692 queries. |
| K1b, exposure | B0 top 200 exposed 136/349 queries (39.0%). The BM25+dense union at 400 added 12 queries. | `audits/ptp-native-exposure-20261111` | Coarse bins and incomplete judgments. |
| K1b/K2a, authors’ unpublished Paper 86 | The PatEmbed-large top-200 pool omitted 78.3% of strict-OUT pairs. Ideal reordering moved the result from 0.188 to 0.260. | `PAPER86-AND-P1DAPFAM-SELECTION.md` S1 | Different system and depth. No replication claim. |
| K2a, separate dataset | P1-DEV (USPTO OA, 1M), OUT R@200: BM25 0.1727, Arctic 0.2248, Qwen3 0.2741, PatEmbed-large 0.3282. | `paper1-bridgeret/dev-results/` | Different benchmark; descriptive only. |

Supported wording: “In this setting, adding BM25 through RRF did not increase cross-domain (OUT) exposure on DAPFAM DEV.”
Avoid claims that exposure caused the near-zero instruction effect, that instructions never matter, or that the experiment proved retrieval is the bottleneck.

## 3. Evidence labels for every number and figure
`MEASURED / REPOSITORY RECEIPT` · `HISTORICAL PROJECT RECORD` · `ENGINEERING VALIDATED / SYNTHETIC` · `DESIGNED / NOT_RUN` ·
`HYPOTHESIS / NOT_USER_VALIDATED` · `PUBLISHED / ACCEPTED` (publication requires a publication record; the owner had yet to provide the DOI for Paper 53).

## 4. Open items for the owner
- DOI or IEEE Xplore record for Paper 53. The PDF carries proceedings ISBN 979-8-3195-1044-0/26 and no DOI.
- O17: instruction bodies were copied verbatim from Paper 53 LaTeX source `IS_1/revision_05/source/main.tex`, lines 102–105. Qwen3-Reranker token counts were Generic 13 (matches), Patent-aware 28 (table 29), Claim-focused 113 (table 119) and Scrambled 113 (matches). Table I reports submitted counts without retokenizing; whitespace or line breaks may differ. Confirm use of the source bodies.
