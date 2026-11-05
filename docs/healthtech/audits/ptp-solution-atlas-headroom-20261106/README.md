# Solution-atlas headroom check (development split): GO_ORACLE_ONLY

Status: `PARTIAL`. The pre-declared gate returned `GO_ORACLE_ONLY`. Dev only (474 queries, 349 strict-OUT eligible); the test split was not read. CPU only; no new data; USD 0 paid.

Plan: [SOLUTION_ATLAS_HEADROOM_PLAN_20261106_EN.md](../../research/SOLUTION_ATLAS_HEADROOM_PLAN_20261106_EN.md). The plan and code were committed at `fc47cdb` before any number was computed.

## Decision

Knowing the true far classes would move more targets into the first 50 (oracle +0.059 R@50). A class-transition prior learned from the other folds instead moved targets **out** of the first 50 (−0.044, CI −0.070 to −0.017). Under the plan the status is `GO_ORACLE_ONLY`, so building the external citation prior is an owner decision.

The evidence below argues against building it for retrieval:

- **The upper bound is small.** The oracle already knows each query's exact target classes and still gains only 0.06 at R@50.
- **The prior's problem is precision, not sparsity.** It names at least one true target class for 79% of queries at m = 5. Promoting those classes still pushes non-relevant families ahead of the dense order.

## Results ([headroom-dev-results.json](headroom-dev-results.json))

Strict-OUT recall on dev, n = 349, with stable class-first reordering of the IPC3-masked Top-200. R@200 does not change by construction.

| Ranking | Order | R@20 | R@50 | R@200 |
|---|---|---|---|---|
| Brief P, masked (primary) | dense | 0.1123 | 0.1770 | 0.2919 |
| | oracle classes | 0.1835 | 0.2361 | 0.2919 |
| | prior m = 3 | 0.0739 | 0.1339 | 0.2919 |
| | prior m = 5 | 0.0760 | 0.1334 | 0.2919 |
| | prior m = 10 | 0.0859 | 0.1553 | 0.2919 |
| Brief T, masked | dense | 0.0886 | 0.1556 | 0.2634 |
| | oracle | 0.1539 | 0.2227 | |
| | prior m = 5 | 0.0730 | 0.1295 | |
| Full patent, masked | dense | 0.1479 | 0.2182 | 0.3341 |
| | oracle | 0.2119 | 0.2797 | |
| | prior m = 5 | 0.1010 | 0.1696 | |

**Paired query bootstrap** (5,000 resamples, seed 20261105), R@50 − dense:

| Ranking | Oracle | Prior m = 3 | Prior m = 5 (gate) | Prior m = 10 |
|---|---|---|---|---|
| Brief P | +0.059 (+0.038, +0.083) | −0.043 (−0.068, −0.018) | −0.044 (−0.070, −0.017) | −0.022 (−0.046, +0.001) |
| Brief T | +0.067 (+0.047, +0.091) | −0.027 (−0.055, −0.001) | −0.026 (−0.051, −0.002) | −0.013 (−0.035, +0.009) |
| Full patent | +0.062 (+0.042, +0.082) | −0.052 (−0.082, −0.022) | −0.049 (−0.078, −0.019) | −0.029 (−0.054, −0.004) |

R@20 shows the same pattern. On brief P the oracle gain is +0.071 and the prior m = 5 change is −0.036.

## Concentration (descriptive)

- **Target classes per query:** mean 5.8, median 5, max 23.
- **Prior hit rate:** the cross-fitted prior names at least one true target class for 71% (m = 3), 79% (m = 5) and 89% (m = 10) of queries.
- **By the query's first IPC section:**
  - 30–87 distinct target classes per section;
  - normalized entropy 0.61–0.77;
  - the top 5 target classes cover 52–67% of strict-OUT pairs.

Cross-domain targets are moderately concentrated by section, but each query spreads across several broad classes.

## Reading

1. **Class knowledge is a weak lever next to a strong encoder.** Even perfect class knowledge adds only 0.06–0.07 to R@50. Any hard class-level policy is bounded by this oracle.
2. **A learned prior is worse than no prior.** Predicted classes are broad, and promoting them displaces targets the encoder had already ranked well. The same was seen with Qwen-proposed classes in Stage 1 (Q2).
3. **An external citation prior would fix sparsity, not precision.** It may still be useful as a descriptive map in a product view. That would be a visualization, not a retrieval claim.
4. **Limits.**
   - Reordering within the masked Top-200 cannot test deeper class-restricted search.
   - The cross-fitted prior is somewhat optimistic, because shared targets appear across folds. Even so, it was negative.

## Command

`python scripts/healthtech/analyze_solution_atlas_headroom.py --ranking briefP_masked=<private>/scout/rankings/rankings-x-P-dev.jsonl --ranking briefT_masked=<private>/scout/rankings/rankings-x-T-dev.jsonl --ranking fullpatent_masked=<private>/scout/rankings/rankings-x-R2-dev.jsonl --records <private>/scout/scout-dev-records.jsonl --family-ipc3 <private>/stage1/action-inputs/family-ipc3.jsonl --split <private>/split.json --output docs/healthtech/audits/ptp-solution-atlas-headroom-20261106/headroom-dev-results.json` (exit 0)

Input hashes are in the results JSON: masked rankings `42db52e1`, `7b1a1e30`, `6ec5f011`; family-ipc3 `b401e1d0`; split `dd76c019`. Code revision `fc47cdb`.
