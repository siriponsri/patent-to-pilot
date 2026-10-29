# HT-M3 family-aware baseline audit

- Run ID: `luna-long-run-20261029-family-baselines-20261029`
- Date: `2026-10-29`
- Tested source commit: `e84c3c57df2d404aba8b79d89f94e9866002d7df`
- Candidate package commit: `c0887f6a210d598b0f604badd5a4e6fbd8911852`
- Status: `PASS_OFFLINE_DEVELOPMENT_WITH_FINAL_HOLDOUT`
- Scope: fresh HT-B0a/B0b/B1/B2/B3 runs on the family-aware Boston/Stryker/Cook composite, followed by sourced family-group re-projection.

## Result

The shared offline methods were rerun against the frozen family-aware manifest rather than reusing earlier baseline outputs. The development view contains `5` queries and the untouched Stryker final holdout contains `3` queries; both use the same `24`-patent universe, protocol hash, local model revisions, candidate depth `24`, and rerank depth `24`.

At `K=10`, exact-patent macro known-link recall is:

- Development: `0.9381 / 1.0000 / 0.9000 / 0.7762 / 0.9000` for HT-B0a/B0b/B1/B2/B3.
- Final holdout: `0.3333 / 0.6667 / 0.7429 / 0.7905 / 0.7905` for HT-B0a/B0b/B1/B2/B3.

Family-aware group rows are also present in the re-projection. Development K=10 family-group macro recall is `0.9484 / 1.0000 / 0.8333 / 0.7302 / 0.8333`; holdout family-group rows equal the exact-group rows because no family merges cross the three holdout groups. These are descriptive sensitivity rows, not semantic gold or confidence intervals.

All `40` scheduled method/query rows completed with `0` failures. Provider calls, network acquisition, neural provider calls, and paid cost were `0` / `0` / `0` / `$0.00`. Local model inference used `74.48` wall seconds / `459.55` CPU seconds on development and `58.78` wall seconds / `316.94` CPU seconds on holdout.

## Artifacts

- Development baseline: `results/healthtech/ht-multicompany-baselines-20261029-family-r1-dev`
- Final-holdout baseline: `results/healthtech/ht-multicompany-baselines-20261029-family-r1-holdout`
- Development family projection: `results/healthtech/ht-family-frontier-20261029-r2-development`
- Final-holdout family projection: `results/healthtech/ht-family-frontier-20261029-r2-final-holdout`
- Frozen cohort manifest SHA-256: `1b42b7c4a52b697d9c5c4f7db4f9236b7d5d239d83584863a6ba844591adef75`
- Protocol SHA-256: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`

Machine-readable details are in [`REPORT.md`](REPORT.md), [`verification.json`](verification.json), [`experiment-ledger.json`](experiment-ledger.json), and [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).

## Limits

The product-level disclosure references are structural source-backed links, not independent expert relevance judgments. Unlisted device-patent pairs remain unjudged and are not recoded as negatives. Family IDs are sourced Google Patents metadata, not legal family adjudication. The Stryker company holdout is a single-company transfer check, so generalization uncertainty remains `NOT_ESTIMABLE`.

This package is an offline development comparison only. It does not open the paid provider branch, resolve the Bridge rights/cohort blocker, establish patent validity/FTO/clinical suitability, or support publication or investment claims.

## Handoff

The next information-gaining package is a rights-cleared relevance-judgment cohort with multiple independent company/family groups, auditable positive judgments, frozen denominators, and a predeclared untouched final holdout.
