# MTM dev phase 3a: dense vector PRF (Rocchio), negative

- **Status:** PASS (run). **Scientific result: negative.**
  - PRF lowers hit@20, hit@100 and hit@200 on the primary cell.
  - It brings in some new targets, but loses more than it gains.
  - It is not eligible for test.
- **Split:** dev only (1,985 queries). The test split is sealed.
- **Declared before the run:** entry 3a of the [methods log](../../research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md) (`3792f6d`).
- **Code:** `git archive a29610b`, run on dr-train (Tesla V100-SXM2-32GB) by [run_dev3a.sh](run_dev3a.sh). Every step exit=0, 23:49Z on 8 Nov to 00:22Z on 9 Nov 2026 ([status.log](status.log)). No retries.
- **Files:**
  - [dev-phase3a.json](dev-phase3a.json), sha256 `22a4ce10…`;
  - [receipt-prf-P-dev.json](receipt-prf-P-dev.json), sha256 `22a5786e…`, 717 s;
  - [receipt-prf-T-dev.json](receipt-prf-T-dev.json), sha256 `9270b096…`.
  - The rankings stay on dr-train in `dev3a/out`.
- **Sanity checks:**
  - prfK0-1.0 reproduces X exactly in all 8 view pairs (Δ 0; new and lost 0 at both depths).
  - A 5-query smoke test before the run showed the same. PRF changed 15–30% of the top 200.

## Primary: P, main (X hit@20 0.180, hit@100 0.313, hit@200 0.388)

| Variant (k, w) | hit@20 | Δ hit@20 [95% CI] | hit@100 | hit@200 | new@200 | lost@200 |
|---|---|---|---|---|---|---|
| k3, w 0.7 | 0.170 | −0.010 [−0.019, −0.002] | 0.305 | 0.364 | 0.012 | 0.036 |
| k5, w 0.8 | 0.173 | −0.007 [−0.014, −0.001] | 0.305 | 0.376 | 0.009 | 0.021 |
| k10, w 0.9 | 0.177 | −0.003 [−0.008, +0.003] | 0.308 | 0.383 | 0.004 | 0.009 |
| **CV (out of fold)** | **0.177** | **−0.003 [−0.008, +0.003]** | 0.308 | 0.383 | 0.004 | 0.009 |

- **CV choice:** k10, w 0.9 in all 4 folds. That is the weakest feedback in the grid, the one closest to X.
- **All 9 variants:** every one lowers hit@20 (Δ from −0.012 to −0.003) and hit@200 (0.364 to 0.385, against 0.388). Each loses more targets at depth 200 than it gains.

## Other cells (CV out of fold, Δ hit@20)

| Query view | main | small | matched | uniform |
|---|---|---|---|---|
| P | −0.003 [−0.008, +0.003] | −0.011 [−0.018, −0.005] | −0.004 [−0.008, +0.001] | −0.005 [−0.010, 0.000] |
| T | +0.005 [−0.001, +0.011] | −0.001 [−0.007, +0.005] | −0.005 [−0.010, 0.000] | −0.002 [−0.007, +0.004] |

## Findings

1. **PRF pulls the query towards the wrong neighbours.**
   - Only 3.5% of queries have a target at rank 1, and about 13% in the top 10.
   - The feedback documents are therefore mostly non-relevant, so moving the query towards them drifts away from the targets.
   - This matches the evidence that the gain from vector PRF depends on feedback quality (Li et al., SIGIR 2022). Lexical PRF for patent prior art also degraded results (Ganguly et al., CIKM 2011).
2. **Stronger feedback does more damage.** Smaller w (more feedback) is consistently worse, and the CV always picks the setting closest to X.
3. **The title query T shows a small, non-significant gain at w 0.8** (+0.005). T is short, so the feedback may add context. It is secondary and not a claim.

## Limits

- Only one PRF form was tested (the centroid of MaxP-winning passages), with k ≤ 10 and w ≥ 0.7.
- A learned PRF encoder (ANCE-PRF) and multi-vector PRF were not tested.
