# HT current-head offline baseline and B4 mock audit

- Run ID: `luna-long-run-20261030-current-head-baseline-b4-20261030`
- Date: `2026-10-30`
- Tested baseline code commit: `aeaa8aa20c7840ebcf63f9f92b9d3e4d2f52ef83`
- Protocol hash: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`
- Cohort manifest hash: `d00d12ad7ebb8f37938e094f89b9dd9cedb288eb108718c7947caa991dcfc267`
- Status: `PASS_OFFLINE_BASELINES_AND_PROVIDER_SHAPED_MOCKS`

## Scope

This package refreshes the frozen Philips-family composite at the current backend head. It runs HT-B0a/B0b/B1/B2/B3 on the development and untouched Stryker holdout views, reprojects both views onto the sourced family map, runs HT-B4 in mock mode on the same inputs, and generates a reproducible report and descriptive analysis.

The development view contains 8 devices, 31 patents, and 25 disclosed reference pairs across 6 exact groups. The final holdout contains 3 Stryker devices, the same 31-patent universe, and 13 disclosed reference pairs across 3 exact groups. Family re-projection observes 24 family IDs, maps all 31 patents, and creates 0 exact-group merges in either split.

## Results

Offline macro known-link Recall@20:

| Split | HT-B0a | HT-B0b | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|---:|---:|
| Development | 0.9613 | 1.0000 | 0.9688 | 0.9063 | 0.9688 |
| Final holdout | 0.5429 | 0.8095 | 0.8381 | 0.8857 | 0.8381 |

HT-B4 mock reaches `0.9688` on development with 19 provider-shaped calls and `0.8381` on holdout with 8 calls. Both runs used the existing GPT-4.1-mini snapshot in mock mode, recorded simulated ledger debits of `$0.0019` and `$0.0008`, and incurred `$0.00` paid cost with no unknown or pending billing items.

The report and analysis are generated under [`report/`](report/) and [`analysis/`](analysis/). The corrected report renderer derives cohort counts and B4 comparisons from the supplied artifacts rather than the prior 5-device/24-patent package. The corrected analysis derives frontier interpretation from the observed current-head rows.

## Integrity verification

The current tree passes 50 focused M1 repair/pre-live tests, the report and analysis regressions, and `compileall`. A detached clean worktree at the baseline commit also passes the focused M1 tests and compile check. The typed-rights exact-head reproduction passes F1/F2/F3: restricted evidence is excluded from external projections, runtime patent-text mutation is rejected by the manifest hash, and the network/provider counters remain zero. The sanitized reproduction receipt is [`m1-exact-head-reproduction-summary.json`](m1-exact-head-reproduction-summary.json).

The older `ht-public-cohort-20261029-frozen-r1` input was intentionally rejected by the exact-head adapter because its source registry lacks typed rights. That is recorded as a stale-input diagnosis; the valid typed-rights cohort is `ht-public-cohort-20261029-frozen-r2-typed`.

Machine-readable audit details are in [`verification.json`](verification.json), [`b4-development-verification.json`](b4-development-verification.json), and [`b4-holdout-verification.json`](b4-holdout-verification.json).

## Boundaries

- Provider behavior is mock-only engineering evidence; live HT-B4 remains `BLOCKED_LOCAL`.
- Product-level disclosed links are not semantic relevance gold, exhaustive recall, clinical evidence, FTO, patent validity, investment merit, or publication evidence.
- Unlisted device-patent pairs remain `UNJUDGED` and are not treated as negatives.
- Development and holdout uncertainty remains `NOT_ESTIMABLE`; the holdout is a descriptive company-level transfer check, not an inferential estimate.
- Bridge acquisition remains `BLOCKED_LOCAL`, Zenodo record `21101400` remains restricted, and Claude UX/UI remains paused.

## Next action

Obtain owner authorization and exact schema/rights terms for an admissible semantic device-patent judgment source. Validate it through the existing M23/M25/M24 path, then rerun the frozen controls without changing denominators, holdout membership, or the unjudged policy.
