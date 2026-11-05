# Solution-scout feasibility plan (dev only), 5 Nov 2026

Status: pre-declared before any brief or scout output was generated. Background: [novelty check](SOLUTION_SCOUT_NOVELTY_CHECK_20261105_EN.md).

Outcome (6 Nov 2026): `PARTIAL_LANE_ONLY`. The scout pool was below the lane-only pool. A post-hoc check found that the lane gain comes mainly from the IPC3 mask, which matches the strict-OUT definition. See the [feasibility audit](../audits/ptp-solution-scout-feasibility-20261105/README.md). The plan text below is unchanged.

## 1. Question

When the query is a short problem brief rather than a full patent, does LLM function abstraction plus a cross-domain retrieval lane expose more known cross-domain (strict-OUT) prior art than dense retrieval on the brief, at the same 200-family budget?

## 2. Data and split

- DAPFAM, using the existing Stage 0 split.
- Dev only: 474 queries, 349 of them strict-OUT eligible. The test split is not read.
- Corpus, passages, encoder (PatEmbed-large with the `retrieval_OUT` prompts) and passage vectors are those of Stage 0.

## 3. Briefs and LLM actions

Model: Qwen3-8B, greedy decoding, fp16, thinking off. Prompt version `ptp-solution-scout-v1` in `scripts/healthtech/run_qwen_scout_actions.py`.

**Briefs**
- **T, title brief:** the family title, with no LLM involved.
- **P, problem brief (primary):** 40–80 words written by Qwen from the title, the abstract and the first 3,000 characters of the description. The prompt forbids mechanisms, components, materials and claimed features.

**Actions on each brief.** Each action sees only the brief, never the patent.
- **F, function:** 40–80 words restating the required function in generic terms.
- **S, solution sketch:** a 100–150-word abstract of a hypothetical patent from another industry.

**Failure handling.** An output outside its word bounds is a failure; there are no retries. A failed action contributes an empty list for that query.

## 4. Arms, pools and the pre-declared comparison

**Arms** (Top-200 families each, for each brief type):

| Arm | What it retrieves |
|---|---|
| D | Dense on the brief |
| X | Cross-domain lane on the brief: dense with every family sharing any IPC3 code with the query removed. The query's own codes are metadata known at search time |
| B | BM25 on the brief |
| FD, FX | F text, plain and cross-domain lane |
| SD, SX | S text, plain and cross-domain lane |

**Pools** (200 families each; `lane_merge` keeps the first 100 of D, fills from the other arms, then falls back to the rest of D):

| Pool | Contents |
|---|---|
| base | D |
| lane | D[:100] + X |
| scout | D[:100] + FX and SX, round-robin |
| llm_no_lane | D[:100] + FD and SD, round-robin |

**Primary endpoint.** Strict-OUT Recall@200 on brief P.

**Statistic.** Paired query bootstrap, 5,000 resamples, seed `20261105`. Dev is dominated by one large component, so component resampling is not informative.

**Stop rule**

| Status | Condition | Consequence |
|---|---|---|
| **PASS** | scout − base ≥ 0.02 with 95% lower bound > 0, **and** scout − lane has 95% lower bound > 0 | The study proceeds to a frozen protocol and one test run |
| **PARTIAL_LANE_ONLY** | Not PASS, but lane − base has 95% lower bound > 0 | The lane helps without the LLM. Reported as such; the LLM claim is not carried forward |
| **FAIL** | Otherwise | Reported as a negative feasibility result; no test run for this direction |

**Secondary and descriptive only, with no decisions attached:**
- brief T;
- every single arm;
- scout − llm_no_lane;
- IN Recall@200, for the cost of the cross-domain lane;
- Recall@100 and hit@200;
- the full-patent dense reference (R2) as an upper reference.

## 5. Leakage and validity notes, reported with the result

- **Brief P is written from the patent's own text.** The prompt forbids solution content. Brief T needs no LLM and serves as the leakage-free control.
- **The LLM may recall target patents** (Yoon et al. 2025). This feasibility check does not probe for that. If the check passes, the frozen protocol will add a probe.
- **Embedding training overlap.** The PatenTEB `retrieval_OUT` test split contains 1 of the 5,193 DAPFAM strict-OUT pairs (in either direction). Its families overlap 48 DAPFAM queries and 376 corpus families. The PatenTEB training split is not released.

## 6. Compute

- About 2,370 Qwen calls on the approved V100; the output is written query by query.
- Fourteen dense runs that reuse the Stage 0 passage vectors.
- BM25 on the CPU.
- USD 0 in paid calls.
