# MTM dev phase 1: BM25, calibrated hybrid, zero-shot cross-encoder

- **Status:** PASS (run). **Scientific result: null/negative on the primary view.** No phase-1 method beats the dense X lane on P/main hit@20 with a lower bound > 0.
- **Split:** dev only (1,985 queries). The test split is sealed; no test file was read or scored.
- **Methods:** declared before the run in the [methods log](../../research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md), entries V1–V3. No setting was changed after results were seen.
- **Code:** `git archive 2feec03`, run on dr-train (Tesla V100-SXM2-32GB) by [run_dev1.sh](run_dev1.sh). Every step exit=0 ([status.log](status.log)), 04:35Z–05:35Z on 8 Nov 2026. No retries.
- **Files:**
  - [dev-phase1.json](dev-phase1.json): all measures, contrasts and CV.
  - [receipt-hybrid-P-dev.json](receipt-hybrid-P-dev.json), [receipt-hybrid-T-dev.json](receipt-hybrid-T-dev.json): V1/V2 settings, input and ranking hashes.
  - [receipt-rerank-ce-P-dev.json](receipt-rerank-ce-P-dev.json), [receipt-rerank-ce-T-dev.json](receipt-rerank-ce-T-dev.json): V3 model revision, weight sha256, 198,500 pairs per view, about 161 pairs/s.
- **Rankings** (DAPFAM-derived text and IDs) stay on dr-train under `/home/chaw/patent-to-pilot-jobs/mtm-20261107/dev1/out`; only their hashes are in the receipts.
- **Sanity check:** hyb-1.0 reproduces the baseline X exactly in all 8 view pairs (delta 0, new/lost 0).

## How to read the columns

- **Δ hit@20** is method − X, with a paired bootstrap 95% CI (5,000 resamples, seed `20261107`).
- **new@100** is the share of queries where X's top 100 had no target but the method's top 100 does. **lost@100** is the reverse.
- The CV row is the honest estimate for V2. λ is chosen on the other 3 folds, and the score is out of fold.

## Primary: query view P, corpus view main (X hit@20 0.180, hit@100 0.313, MRR@100 0.065)

| Method | hit@20 | Δ hit@20 [95% CI] | hit@100 | MRR@100 | new@100 | lost@100 |
|---|---|---|---|---|---|---|
| V1 BM25 | 0.037 | −0.143 [−0.160, −0.126] | 0.070 | 0.016 | 0.013 | 0.255 |
| V2 λ 0.5 | 0.125 | −0.054 [−0.070, −0.039] | 0.248 | 0.047 | 0.041 | 0.105 |
| V2 λ 0.6 | 0.155 | −0.025 [−0.039, −0.011] | 0.289 | 0.055 | 0.047 | 0.071 |
| V2 λ 0.7 | 0.175 | −0.005 [−0.018, +0.007] | 0.307 | 0.062 | 0.041 | 0.047 |
| V2 λ 0.8 | 0.182 | +0.002 [−0.009, +0.013] | 0.321 | 0.068 | 0.034 | 0.026 |
| V2 λ 0.9 | 0.185 | +0.005 [−0.004, +0.014] | 0.322 | 0.067 | 0.021 | 0.011 |
| **V2 CV (out of fold)** | **0.185** | **+0.005 [−0.004, +0.014]** | 0.322 | 0.067 | 0.021 | 0.011 |
| V3 cross-encoder | 0.144 | **−0.036 [−0.052, −0.021]** | 0.313 | 0.048 | 0 | 0 |

The CV picked λ 0.9 in all 4 folds (fold sizes 520/470/511/484), so the out-of-fold estimate equals the full-dev λ 0.9 row.

## Query view T, corpus view main (X hit@20 0.129, hit@100 0.251)

| Method | hit@20 | Δ hit@20 [95% CI] | new@100 | lost@100 |
|---|---|---|---|---|
| V1 BM25 | 0.023 | −0.106 [−0.120, −0.091] | 0.008 | 0.207 |
| V2 λ 0.8 | 0.139 | +0.011 [+0.002, +0.020] | 0.032 | 0.018 |
| V2 λ 0.9 | 0.138 | +0.009 [+0.003, +0.015] | 0.019 | 0.007 |
| **V2 CV (out of fold)** | **0.134** | **+0.006 [−0.004, +0.016]** | 0.033 | 0.022 |
| V3 cross-encoder | 0.124 | −0.005 [−0.017, +0.008] | 0 | 0 |

The CV picked λ 0.8, 0.8, 0.8 and 0.7. The single best full-dev λ rows have CIs above 0, but those rows are selected after seeing dev. The honest out-of-fold CI includes 0.

## Sensitivity views (V2 CV out of fold, Δ hit@20 vs X)

| Query view | main | small | matched | uniform |
|---|---|---|---|---|
| P | +0.005 [−0.004, +0.014] | +0.003 [−0.007, +0.012] | +0.007 [−0.002, +0.015] | +0.002 [−0.007, +0.011] |
| T | +0.006 [−0.004, +0.016] | +0.012 [+0.004, +0.020] | +0.008 [+0.002, +0.015] | +0.016 [+0.005, +0.026] |

BM25 alone is strongly worse than X in every view (Δ −0.11 to −0.24). V3 ran on main only, as declared; its sensitivity views were not run because it did not help on main.

## Findings

1. **Lexical matching does not solve the cross-field lane.** BM25 alone finds a target in the top 100 for only 7% of P queries, versus 31% for dense. When the target sits in another CPC class, it rarely shares the query's words.
2. **The hybrid moves targets in and out at a similar rate.** At λ 0.9 it adds 2.1% new@100 and loses 1.1%. The net hit@20 gain on P/main (+0.005, about 10 of 1,985 queries) is not distinguishable from 0. The hybrid helps the short title query T slightly more, and in three sensitivity views the CV interval is above 0. T is not the primary view.
3. **The zero-shot cross-encoder hurts on the primary view.** On P/main, hit@20 drops by 0.036 and MRR@100 falls from 0.065 to 0.048. On T it is neutral. A plausible reason, not tested here: a general-purpose reranker rewards topical overlap with the query, and in lane X the targets are by design from other fields.
4. **No phase-1 method meets the carry-forward bar on the primary view.** That bar is the rules §9 contrast, method − X with lower bound > 0 after Holm. Whether to carry V2 (λ 0.9) to the single test read is an owner decision. The dev evidence alone predicts low power.

## Limits

- These are dev results for one dataset, one dense model and one reranker. They are not test results.
- A query view P brief is LLM-generated (Qwen3-8B). V3 pairs that brief with a candidate title and abstract only, without claims.
- No hyperparameter was tuned for BM25 or for the reranker. Their defaults are declared in the methods log.
