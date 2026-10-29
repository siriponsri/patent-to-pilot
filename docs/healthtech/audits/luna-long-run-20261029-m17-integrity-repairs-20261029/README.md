# HT-M17 typed-rights migration and offline baseline

- Run ID: `luna-long-run-20261029-m17-integrity-repairs-20261029`
- Date: `2026-10-29` (Asia/Bangkok)
- Status: `PASS_OFFLINE_DEVELOPMENT_TYPED_RIGHTS`
- Audit head: `7def4ff` (`healthtech: migrate legacy cohorts to typed rights`)
- Parent package: `../luna-long-run-20261029-m16-review-tasks-20261029/README.md`

## Objective

Close the remaining operational gap from the M1 integrity findings by migrating the legacy local Abbott development cohort to declared typed rights policies, exercise every external boundary, and rerun the five offline HealthTech baselines on the derived cohort. The original legacy cohort remains untouched.

## Implementation

The new migration utility `scripts/healthtech/migrate_legacy_cohort_rights.py` creates a fresh derived directory, copies runtime/raw/evaluator/group artifacts, changes only the typed source-registry policy declarations and manifest metadata that pins that registry, and enforces per-file and total-storage limits. The migration changed 45 of 45 source rows, copied 64,389,947 bytes, and bound the reviewed policy IDs `abbott-product-patent-disclosures`, `google-patents-pages`, and `openfda-pma-records`.

The new regression coverage exercises Markdown EN/TH, `product_display`, `redistribution`, JSON serialization, source-view access, history reload, and restricted structured/literal evidence mutation. The focused exact-head suite passes 57 tests with zero failures. In-memory syntax compilation covers 147 Python files; a separate `compileall` attempt was not used as evidence because the disposable worktree had a pre-existing `__pycache__` permission collision.

## Development freeze and baseline

The derived development freeze is `results/healthtech/ht-abbott-development-20261029-m17-r1/`:

- 3 devices: MitraClip, Tendyne, and TriClip.
- 41 candidate patents, 61 disclosed product-level reference pairs, and 62 explicitly unjudged distractor pairs.
- No final holdout; two exact-patent groups; family identity remains unknown and unassumed.
- Protocol hash: `0718518a13dccbd369ed0408fe82e04a7f245db61106cfd7c6f0c972911ccbe4`.

The corrected real offline run is `results/healthtech/ht-real-baselines-20261029-m17-r2/` and completed HT-B0a, HT-B0b, HT-B1, HT-B2, and HT-B3 for all three devices with zero errors, zero provider calls, and USD 0.00 paid cost. Macro known-link recall@20 was:

| Method | Recall@20 | Query calls | Rerank pairs | Rerank tokens |
| --- | ---: | ---: | ---: | ---: |
| HT-B0a | 0.442739 | 3 | 0 | 0 |
| HT-B0b | 0.662242 | 3 | 0 | 0 |
| HT-B1 | 0.498802 | 3 | 123 | 31,488 |
| HT-B2 | 0.568912 | 9 | 369 | 94,464 |
| HT-B3 | 0.498802 | 5 | 205 | 52,480 |

These are realized local resource units and descriptive development results only. The cohort is one company, has two exact-patent groups, has no final holdout, and does not support a stable uncertainty or generalization estimate. Product-level disclosure is not semantic relevance gold, claim construction, FTO, clinical evidence, patent validity, or investment evidence.

## Integrity reproduction

The corrected M1 reproduction summary is preserved at `after-reproduction-summary.json`. It records three real cases with 41 patents each, 45 manifest-declared raw files, 48 copied files, no network/provider/neural calls, exclusion of restricted values from external outputs, and rejection of a runtime patent-text mutation with `CohortIntegrityError: runtime JSON hash does not match manifest`. That reproduction was recorded against source commit `1ed830a`; the exact-head 57-test suite above verifies the current audit head `7def4ff`.

## Failed attempt retained

The first baseline attempt is preserved locally at `results/healthtech/ht-real-baselines-20261029-m17-r1/`. It failed before scoring because `group_evidence.json` was supplied where the runner contract requires `groups.json`. Its partial runtime/raw outputs are not a result and are excluded from all reported metrics.

## Limits and next step

No paid inference, live provider request, public raw-data release, Bridge acquisition, clinical/FTO analysis, deployment, external outreach, or Claude UX/UI work occurred. Keep Abbott development-only. The next information-gaining step is a rights-cleared independent cohort with multiple company/family groups and a predeclared untouched holdout, followed by explicit relevance judgments through `ht-relevance-judgment-cohort-v1` before any pooled scientific claim.
