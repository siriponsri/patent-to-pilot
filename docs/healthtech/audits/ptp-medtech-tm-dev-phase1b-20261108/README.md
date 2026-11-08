# MTM dev phase 1b: corrected BM25, hybrid and zero-shot cross-encoder

- **Status:** PASS (run). **Scientific result: null/negative on the primary view, as in the defective phase 1.**
  - The hybrid helps the title query T, which is not primary. It does not help the primary P/main cell.
- **What changed from phase 1:** only the query text given to BM25 and to the reranker. The PatEmbed instruction prefix is now stripped (see the defect note in the [phase-1 audit](../ptp-medtech-tm-dev-phase1-20261108/README.md)). The dense side is unchanged.
- **Split:** dev only (1,985 queries). The test split is sealed.
- **Methods:** entries V1b–V3b in the [methods log](../../research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md), declared before this run and approved by the owner on 8 Nov 2026.
- **Code:** `git archive 14263c9`, run on dr-train (Tesla V100-SXM2-32GB) by [run_dev1b.sh](run_dev1b.sh). Every step exit=0, 05:51Z–06:51Z on 8 Nov 2026 ([status.log](status.log)). No retries.
- **Files:**

  | File | sha256 | Contents |
  |---|---|---|
  | [dev-phase1b.json](dev-phase1b.json) | `a61d09c9…` | all measures, contrasts and CV |
  | [receipt-hybrid-P-dev.json](receipt-hybrid-P-dev.json) | `96861d57…` | V1b/V2b, P |
  | [receipt-hybrid-T-dev.json](receipt-hybrid-T-dev.json) | `25426e27…` | V1b/V2b, T |
  | [receipt-rerank-ce-P-dev.json](receipt-rerank-ce-P-dev.json) | `233f8fde…` | V3b, P |
  | [receipt-rerank-ce-T-dev.json](receipt-rerank-ce-T-dev.json) | `58bb0688…` | V3b, T |

  - Every receipt records `"query": "dense instruction prefix stripped"`. The hybrid receipts add the stripped-query hash, the reranker receipts the private raw-score hash.
- **Private files:** rankings and raw reranker scores stay on dr-train under `/home/chaw/patent-to-pilot-jobs/mtm-20261107/dev1b/`. The scores feed V5.
- **Sanity check:** hyb-1.0 reproduces X exactly in all 8 view pairs.

Columns are as in the phase-1 audit: Δ is method − X on hit@20 with a paired bootstrap 95% CI (5,000 resamples, seed `20261107`). new@100 and lost@100 are measured against X's top 100.

## Primary: query view P, corpus view main (X hit@20 0.180, hit@100 0.313, MRR@100 0.065)

| Method | hit@20 | Δ hit@20 [95% CI] | hit@100 | MRR@100 | new@100 | lost@100 | Phase 1 (defective) Δ |
|---|---|---|---|---|---|---|---|
| V1b BM25 | 0.044 | −0.136 [−0.153, −0.119] | 0.083 | 0.017 | 0.016 | 0.246 | −0.143 |
| V2b λ 0.8 | 0.183 | +0.003 [−0.008, +0.014] | 0.322 | 0.068 | 0.035 | 0.025 | +0.002 |
| V2b λ 0.9 | 0.183 | +0.004 [−0.006, +0.013] | 0.322 | 0.068 | 0.021 | 0.011 | +0.005 |
| **V2b CV (out of fold)** | **0.181** | **+0.002 [−0.008, +0.011]** | 0.321 | 0.067 | 0.025 | 0.016 | +0.005 |
| V3b cross-encoder | 0.153 | **−0.027 [−0.043, −0.013]** | 0.313 | 0.051 | 0 | 0 | −0.036 |

The CV chose λ 0.8 in fold 0 and λ 0.9 in folds 1–3. The full-dev choice is λ 0.9.

## Query view T, corpus view main (X hit@20 0.129)

| Method | hit@20 | Δ hit@20 [95% CI] | new@100 | lost@100 | Phase 1 (defective) Δ |
|---|---|---|---|---|---|
| V1b BM25 | 0.072 | −0.057 [−0.072, −0.042] | 0.035 | 0.160 | −0.106 |
| **V2b CV (out of fold)** | **0.143** | **+0.014 [+0.008, +0.021]** | 0.020 | 0.008 | +0.006 |
| V3b cross-encoder | 0.124 | −0.004 [−0.017, +0.009] | 0 | 0 | −0.005 |

The CV chose λ 0.9 in all 4 folds.

## V2b CV out of fold, all views (Δ hit@20 vs X)

| Query view | main | small | matched | uniform |
|---|---|---|---|---|
| P | +0.002 [−0.008, +0.011] | +0.004 [−0.005, +0.013] | +0.008 [−0.001, +0.016] | +0.003 [−0.006, +0.012] |
| T | +0.014 [+0.008, +0.021] | +0.012 [+0.004, +0.021] | +0.013 [+0.002, +0.023] | +0.017 [+0.006, +0.028] |

## Findings

1. **The defect mostly hurt the short title query.** With the prefix removed, BM25 on T rises from 0.023 to 0.072 hit@20, and the hybrid on T becomes reliably positive in all 4 corpus views. On P the brief has about 50 words, so 5 extra prefix tokens changed little: BM25 0.037 → 0.044.
2. **On the primary cell the conclusion does not change.**
   - The hybrid adds and loses targets at similar rates: +2.5% new@100, −1.6% lost@100 out of fold. Its out-of-fold gain is +0.002, not distinguishable from 0.
   - The zero-shot cross-encoder still lowers hit@20 by 0.027 and MRR@100 from 0.065 to 0.051.
3. **Why T and P differ, as an interpretation that has not been tested:**
   - A title is short, so dense retrieval on it is weak, and exact rare words add signal.
   - The LLM brief P already paraphrases the problem in general words. That helps dense retrieval and gives BM25 less to add.
4. **No phase-1b method is eligible for test carry-forward.** The fixed rule needs a CV out-of-fold lower bound > 0 on P/main. The T result is reported as secondary and is not a test claim.

## Limits

- These are dev results only, with one dense model, one reranker and no tuning of BM25 or of the reranker.
- The phase-1 numbers stay on record as defective; this table supersedes them.
