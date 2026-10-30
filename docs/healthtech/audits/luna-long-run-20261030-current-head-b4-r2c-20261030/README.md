# HT current-head r2 offline baseline and B4 mock audit

- Run ID: `luna-long-run-20261030-current-head-b4-r2c-20261030`
- Date: `2026-10-30`
- Tested code commit: `d45faab3bf0fa08bf2818243249b77920401f6f5`
- Protocol hash: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`
- Cohort manifest hash: `d00d12ad7ebb8f37938e094f89b9dd9cedb288eb108718c7947caa991dcfc267`
- Status: `PASS_CURRENT_HEAD_OFFLINE_BASELINES_B4_REPORT`

## Scope

This package refreshes the typed Philips-family composite at the current backend head. It records HT-B0a/B0b/B1/B2/B3 on the development and untouched Stryker holdout views, family-frontier projections, HT-B4 provider-shaped mock execution on the same cohort, and the reproducible report and descriptive analysis.

The development view contains 8 devices, 31 patents, and 25 disclosed pairs. The final holdout contains 3 Stryker devices, the same 31-patent universe, and 13 disclosed pairs. Product-level disclosed links remain source-backed recovery targets, not semantic relevance gold.

## Results

Offline macro known-link Recall@20:

| Split | HT-B0a | HT-B0b | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|---:|---:|
| Development | 0.9613 | 1.0000 | 0.9688 | 0.9063 | 0.9688 |
| Final holdout | 0.5429 | 0.8095 | 0.8381 | 0.8857 | 0.8381 |

HT-B4 mock records 0.9688 on development with 19 provider-shaped calls and 0.8381 on holdout with 8 calls. Simulated debits are USD 0.0019 and USD 0.0008; paid cost is USD 0.00 with no unknown or pending billing items.

The generated report is [`report/REPORT.md`](report/REPORT.md). The descriptive analysis is [`analysis/ANALYSIS.md`](analysis/ANALYSIS.md).

## Verification

The focused HealthTech suite passes, `compileall` passes, `git diff --check` passes, current JSON artifacts parse successfully, and the scoped secret-pattern scan finds no matches. No credentials, `.env` files, restricted raw payloads, network acquisition, live provider calls, semantic labels, or paid calls were used.

Machine-readable audit details are in [`verification.json`](verification.json), [`b4-development-verification.json`](b4-development-verification.json), and [`b4-holdout-verification.json`](b4-holdout-verification.json).

## Boundaries

- HT-B4 is mock-only engineering evidence; live/provider behavior remains `BLOCKED_LOCAL`.
- Known-link recovery is descriptive and does not establish exhaustive recall, semantic relevance, clinical suitability, FTO, patent validity, investment merit, or publication readiness.
- Unlisted device-patent pairs remain `UNJUDGED` and are not treated as negatives.
- Generalization and inferential uncertainty remain `NOT_ESTIMABLE` for this package.
- Bridge remains `BLOCKED_LOCAL`, Zenodo record `21101400` remains restricted, and Claude UX/UI remains paused.

## Next action

Obtain an owner-authorized rights-cleared semantic device-patent judgment source, validate it through M23/M25/M24, and rerun the frozen controls without changing denominators, holdout membership, family/company grouping, or the `UNJUDGED` policy.
