# First-Stage Substitution to Diagnose Candidate-Exposure Limits in Instruction-Driven Cross-Domain Patent Reranking

**IS2 short paper.** English editorial edition of the AI4BA faculty-template draft v0.2 dated 22 November 2026. The authors and advisor should review the manuscript before submission. The Paper 53 DOI remains unverified. The 2026 draft records the faculty Word file `IS2-short-paper-draft.docx` and the bilingual `paper/IS2-paper-th` and `paper/IS2-paper-en` Word/PDF releases as its output names.

**Source correction.** On 22 November the draft withheld the Paper 53 exposure estimate pending verification of its denominator. The [subsequent PDF inventory](../../evidence-scope/00-organization.md#original-source-corrections) checked Table II and Figure 3 against the original paper and confirmed 257 of 692. The B53 analysis has a separate denominator of 905. The original list of 692 queries remains unavailable. The B53 numbers below come from the [Stage 1 receipt](results/B53-STAGE1-RESULTS.md) and [Stage 2 receipt](results/B53-STAGE2-RESULTS.md). Version 0.2 incorporated Stage 2 in the abstract, Section 4.2 and the conclusions, and aligned follow-up work with PTP-2026-11-21.

## Title (EN)

First-Stage Substitution to Diagnose Candidate-Exposure Limits in Instruction-Driven Cross-Domain Patent Reranking

Siripon Srihangpiboon¹\* and Tuchsanai Ploysuwan²
School of Information Technology, King Mongkut's Institute of Technology Ladkrabang, 1 Chalong Krung 1 Alley, Lat Krabang, Bangkok 10520

¹ Postgraduate Student, Artificial Intelligence for Business Analytics Program.
² Assistant Professor, School of Information Technology.
\* Corresponding author: 68076060@kmitl.ac.th

## Abstract

In IS1, patent-specific instructions barely changed cross-domain patent reranking quality relative to a generic instruction. Only 257 of 692 eligible queries exposed a known relevant cross-domain patent family in the first 100 candidates. Following the committee's recommendation, we varied the first-stage retriever on DAPFAM while holding the reranker, instructions, text and evaluation fixed. Among 905 eligible B53 queries, patembed-base exposed a known relevant cross-domain family in the top 100 for 37.1%. BM25 lowered exposure by 10.5 percentage points (95% CI −13.6 to −7.5). Reciprocal rank fusion of BM25 and patembed-base changed exposure by +0.4 points, and Arctic-embed lowered it by 5.4 points. In Stage 2, Qwen3-Reranker-0.6B reranked the candidates for 153 queries exposed under every primary first stage. None of the 10 instruction contrasts reached significance (Δ nDCG@100 from +0.001 to +0.009, Holm-adjusted p ≥ 0.69). The small instruction contrasts persisted across the first stages examined here.

**Keywords:** patent retrieval, cross-domain retrieval, reranking, first-stage retrieval, candidate exposure

## 1. Introduction

Prior-art search can require finding the same technical mechanism in another field that uses different vocabulary. A multistage retrieval system first selects candidate documents and then reranks them. Paper 53 tested whether patent-specific instructions improved cross-domain ranking within a fixed pool. Compared with Generic, average strict OUT nDCG@100 changed by +0.0008 for Patent-aware and −0.0007 for Claim-focused. Only 37.1% of the eligible queries had a known relevant cross-domain family in their candidate pool [1].

The IS1 committee asked us to justify choosing patembed-base, test BM25 and hybrid alternatives, and guard against causal interpretations of the exposure decomposition (K1). It also asked IS2 to substitute the first stage directly and explain the practical implications for readers (K2). The B53 study varies the first stage on DAPFAM [2] and addresses three questions.

- **RQ1.** At a fixed retrieval depth, how much does first-stage substitution change exposure to known relevant cross-domain families?
- **RQ2.** How do instruction contrasts vary by first-stage retriever?
- **RQ3.** How does exposure change between depths 100, 200 and 1,000?

## 2. Background

**2.1 DAPFAM**

DAPFAM contains 1,247 query families and 45,336 target patent families. The dataset distinguishes within-domain (IN) from cross-domain (OUT) relevance using three-digit International Patent Classification codes. A cross-domain pair shares no such code [2]. The original study reported substantially worse cross-domain performance. BM25 and reciprocal rank fusion did not close that gap.

**2.2 First-stage retrieval**

BM25 is a standard lexical comparator [3]. The PatenTEB project trained the patent-specific patembed models on 13 tasks [4]. Arctic-embed-m-v2.0 [5] and Qwen3-Embedding [6] are general-purpose retrieval embeddings. Reciprocal rank fusion (RRF) combines ranked lists [7]. Prior cross-domain patent retrieval work found that neural retrievers do not consistently outperform BM25 and emphasized reproducibility [8].

**2.3 Reranking instructions**

Qwen3-Reranker-0.6B scores query–document pairs given an instruction [9]. A reranker can reorder only candidates returned by the first stage. A query with no known relevant OUT family in the pool contributes zero to strict OUT nDCG under every instruction.

**2.4 Exposure decomposition**

On a shared pool, the mean paired instruction difference across all queries equals the exposure rate multiplied by the mean difference among exposed queries: Δ_all = π·Δ_exp. This follows from the zero scores of unexposed queries. The identity alone does not identify a causal effect [1].

## 3. Methods

**3.1 Data**

We used DAPFAM revision `a59a74ce`, whose data matched `780f4011`. Both query and candidate text followed the title–abstract–claims (TAC) representation used in Paper 53. Pairs with `relevance_score > 0` counted as relevant. There were 905 queries with at least one known OUT family, 1,217 IN-eligible queries and 1,247 queries overall. The original 692-query list from Paper 53 could not be recovered, so B53 is a reimplementation on its reported cohort.

**3.2 First stage**

The five primary configurations were F0 patembed-base (revision `244ba452`, MIXED prompt), F1 BM25 (k1 = 1.5, b = 0.75), F2 RRF(F1, F0), F3 Arctic-embed-m-v2.0 and F4 RRF(F1, F3). Prespecified secondary configurations included F0 with the OUT prompt, F6 patembed-large and F7 Qwen3-Embedding-0.6B. The retrieval depth was 1,000. The embedding configuration used exact inner-product retrieval and a 512-token input limit.

**3.3 Second stage**

We used Qwen3-Reranker-0.6B revision `e61197ed` and the four instructions from Paper 53, Table I: Generic, Patent-aware, Claim-focused and Scrambled. Instruction strings came directly from the Paper 53 source. Query and document limits were 2,048 and 4,096 tokens, respectively. Controls used the original first-stage ranking and BGE-reranker-v2-m3. All first stages shared the reranker and instructions.

**3.4 Measurements and inference**

The primary first-stage outcome, π@100, was the fraction of eligible queries with at least one known relevant OUT family in the first 100 candidates. Secondary measures were π@200, π@1000, first known OUT rank, OUT Recall@100 and @200, and strict OUT nDCG@100. We compared each primary alternative with F0 using a paired bootstrap (10,000 resamples, seed 20261119), exact McNemar tests and Holm adjustment over the four comparisons [10]. In Stage 2, the common-exposure cohort C comprised queries exposed under every primary first stage. We adjusted for 10 instruction contrasts using Holm's procedure. The experimental plan preceded outcome measurement.

## 4. Results

**4.1 First-stage exposure (RQ1 and RQ3)**

Table 1. Proportion of queries with a known relevant OUT family in the top k (n = 905).

| Retriever | π@100 | π@200 | π@1000 |
|---|---|---|---|
| F0 patembed-base | 0.371 | 0.471 | 0.733 |
| F1 BM25 | 0.266 | 0.344 | 0.548 |
| F2 RRF(F1, F0) | 0.376 | 0.469 | 0.701 |
| F3 Arctic-embed | 0.317 | 0.419 | 0.632 |
| F4 RRF(F1, F3) | 0.336 | 0.431 | 0.643 |

For F0 through F4, OUT Recall@100 was 0.160, 0.107, 0.170, 0.125 and 0.141. Strict OUT nDCG@100 was 0.061, 0.041, 0.063, 0.048 and 0.052, respectively.

Table 2. Differences in π@100 relative to F0.

| Retriever | Δπ@100 | 95% CI | Holm p |
|---|---|---|---|
| F1 BM25 | −0.105 | [−0.136, −0.075] | < 0.001 |
| F2 RRF(F1, F0) | +0.004 | [−0.015, +0.024] | 0.75 |
| F3 Arctic-embed | −0.054 | [−0.077, −0.032] | < 0.001 |
| F4 RRF(F1, F3) | −0.035 | [−0.061, −0.010] | 0.017 |

For F1 through F4, the numbers of queries gaining/losing exposure relative to F0 were 55/150, 46/42, 34/83 and 54/86, respectively. BM25 alone reduced exposure. The BM25–patembed-base fusion showed no significant improvement over patembed-base. In the secondary comparisons, patembed-large differed by +0.002 and Qwen3-Embedding by −0.024. Switching only the patembed-base prompt to OUT increased exposure by 3.0 points in the descriptive analysis.

With F0 at depth 1,000, approximately 27% of queries still had no known relevant OUT family in the pool. F0 π@100 in B53 (0.371) numerically matches Paper 53's 37.1%, but the cohorts and pipelines differ.

**4.2 Instruction contrasts by first-stage retriever (RQ2)**

Table 3. Paired differences in strict OUT nDCG@100 on cohort C (n = 153). Gained/lost counts refer to the paired instruction contrast.

| Retriever | Patent-aware − Generic [95% CI] (gained/lost) | Holm p | Claim-focused − Generic [95% CI] (gained/lost) | Holm p |
|---|---|---|---|---|
| F0 patembed-base | +0.004 [−0.005, +0.014] (78/71) | 1.000 | +0.006 [−0.003, +0.016] (74/74) | 1.000 |
| F1 BM25 | +0.001 [−0.007, +0.012] (62/74) | 1.000 | +0.004 [−0.005, +0.014] (64/72) | 1.000 |
| F2 RRF(F1, F0) | +0.003 [−0.006, +0.013] (77/70) | 1.000 | +0.006 [−0.003, +0.016] (76/70) | 1.000 |
| F3 Arctic-embed | +0.007 [−0.003, +0.017] (84/64) | 1.000 | +0.009 [−0.000, +0.019] (81/65) | 0.695 |
| F4 RRF(F1, F3) | +0.005 [−0.004, +0.016] (84/64) | 1.000 | +0.007 [−0.001, +0.018] (77/66) | 1.000 |

Table 4. Descriptive mean strict OUT nDCG@100 across all 905 OUT-eligible queries. Queries without known OUT exposure contribute zero.

| Retriever | Generic | Patent-aware | Claim-focused | Scrambled | BGE (no instruction) | No reranking |
|---|---|---|---|---|---|---|
| F0 patembed-base | 0.062 | 0.063 | 0.063 | 0.063 | 0.054 | 0.061 |
| F1 BM25 | 0.043 | 0.043 | 0.044 | 0.043 | 0.039 | 0.041 |
| F2 RRF(F1, F0) | 0.064 | 0.065 | 0.066 | 0.065 | 0.057 | 0.063 |
| F3 Arctic-embed | 0.052 | 0.054 | 0.054 | 0.053 | 0.044 | 0.048 |
| F4 RRF(F1, F3) | 0.056 | 0.057 | 0.058 | 0.057 | 0.048 | 0.052 |

The smallest Holm-adjusted p value across the 10 contrasts was 0.695 (unadjusted 0.070). All estimates were slightly positive and their confidence intervals included zero. Scrambled instructions performed similarly to the meaningful instructions: their differences from Generic were +0.0002 to +0.0010 across all queries. Changing the instruction nevertheless changed outcomes for 91–98% of exposed queries. The instruction-free BGE baseline scored below Generic under every first stage (differences −0.004 to −0.008, with confidence intervals excluding zero).

Absolute nDCG values ranged from 0.04 to 0.07 and varied with π@100. The accounting identity Δ_all = π·Δ_exp held in every arm. As a consistency check, each no-reranking value matched its Stage 1 strict OUT nDCG@100, and Stage 1 and Stage 2 both yielded 153 common-exposure queries. Intervals of approximately ±0.01 leave room for small effects. These comparisons do not establish a causal effect of exposure.

## 5. Conclusions

- **K1a.** Paper 53 used a domain-specific retriever from PatenTEB [4]. Patembed-base had the highest π@100 among the primary standalone retrievers. Its hybrid with BM25 was numerically 0.004 higher, within uncertainty. Patembed-large gave similar exposure, while Qwen3-Embedding and Arctic-embed were lower.
- **K1b.** Neither BM25 alone nor the tested hybrid relieved the roughly 37% cross-domain exposure ceiling at depth 100 in this setting.
- **K1c.** The inference that first-stage substitution changes exposure follows from the substitution experiment. The decomposition describes how exposure enters the endpoint.
- **K2a.** The first-stage pool bounds which families a reranker can recover. With the reranker fixed, instruction differences remained near zero across the tested retrievers (Table 3). The results offer little support for attributing Paper 53's small instruction contrasts specifically to patembed-base. The exposure ceiling constrains the endpoint arithmetically.
- **K2b.** User-oriented measures include the proportion of queries with no known OUT hit (1 − π), the rank of the first known OUT family (median 22 under F0) and the reading depth required. Actual user benefit remains unmeasured.
- **Limitations.** The 512-token cap truncated 92% of texts. Relevance judgments derive from citations and are incomplete. The experiment used one benchmark.
- **Follow-up as proposed in November 2026.** Patent-to-Pilot would extend fixed-pool reranking to evidence acquisition and maintenance using a common engine for research and a local Workbench, with matched lexical, dense and hybrid comparisons. Development experiments with examiner-citation training (BridgeRet) had yet to outperform zero-shot retrieval, so the draft did not advance it as the main method. These follow-ups had no published results at the time of the draft.

**Acknowledgments.** The authors used Claude (Anthropic) to help draft text, write experimental code and prepare tables. The authors reviewed and take responsibility for the content and results.

## References

[1] S. Srihangpiboon and T. Ploysuwan, "Diagnosing near-zero instruction effects in cross-domain patent reranking," in *Proc. iSAI-NLP 2026* (accepted; presented 20 Nov 2026; DOI pending).
[2] I. Ayaou, D. Cavallucci, and H. Chibane, "DAPFAM: A domain-aware family-level dataset to benchmark cross-domain patent retrieval," *Array*, vol. 29, p. 100720, 2026.
[3] S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," *Foundations and Trends in Information Retrieval*, vol. 3, no. 4, pp. 333–389, 2009.
[4] I. Ayaou and D. Cavallucci, "PatenTEB: A comprehensive benchmark and model family for patent text embedding," arXiv:2510.22264, 2025.
[5] P. Yu, L. Merrick, G. Nuti, and D. Campos, "Arctic-embed 2.0: Multilingual retrieval without compromise," arXiv:2412.04506, 2024.
[6] Y. Zhang *et al.*, "Qwen3 embedding: Advancing text embedding and reranking through foundation models," arXiv:2506.05176, 2025.
[7] G. V. Cormack, C. L. A. Clarke, and S. Buettcher, "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods," in *Proc. SIGIR*, 2009, pp. 758–759.
[8] S. Althammer, S. Hofstätter, and A. Hanbury, "Cross-domain retrieval in the legal and patent domains: A reproducibility study," in *Proc. ECIR*, 2021.
[9] Qwen Team, "Qwen3-Reranker-0.6B," Hugging Face model card, revision e61197ed, 2025.
[10] S. Holm, "A simple sequentially rejective multiple test procedure," *Scand. J. Stat.*, vol. 6, no. 2, pp. 65–70, 1979.
