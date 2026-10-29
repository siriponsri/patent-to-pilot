# HT-M3 family-aware baseline report

## Objective

Run the shared HT-B0a/B0b/B1/B2/B3 methods on the new family-aware cohort manifest so the actual baseline outputs, resource accounting, and family-sensitive rows are bound to the same frozen cohort version.

## Frozen inputs

- Cohort: `results/healthtech/ht-multicompany-20261029-r3-family-r2`
- Development runtime/references/groups: `views/development/{runtime,references,groups}.json`
- Final-holdout runtime/references/groups: `views/final_holdout/{runtime,references,groups}.json`
- Family mapping: `results/healthtech/ht-google-family-mapping-20261029-r1/family-mapping.json`
- Protocol hash: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`
- Code commit: `e84c3c57df2d404aba8b79d89f94e9866002d7df`
- Local model revisions: `all-MiniLM-L6-v2@1110a243fdf4706b3f48f1d95db1a4f5529b4d41` and `ms-marco-MiniLM-L-6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`

## Method results at K=10

| Method | Development exact | Development family | Final holdout exact | Final holdout family |
|---|---:|---:|---:|---:|
| HT-B0a | 0.9381 | 0.9484 | 0.3333 | 0.3333 |
| HT-B0b | 1.0000 | 1.0000 | 0.6667 | 0.6667 |
| HT-B1 | 0.9000 | 0.8333 | 0.7429 | 0.7429 |
| HT-B2 | 0.7762 | 0.7302 | 0.7905 | 0.7905 |
| HT-B3 | 0.9000 | 0.8333 | 0.7905 | 0.7905 |

The exact rows are the primary run metrics. Family rows are evaluator-side group sensitivity projections from the same rankings. No method is declared superior by this package, and no confidence interval is estimated.

## Resource accounting

| Split | Queries | Query calls | Rerank pairs | Embedding tokens | Rerank tokens | Wall seconds | CPU seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| Development | 5 | 42 | 768 | 624 | 196,608 | 74.48 | 459.55 |
| Final holdout | 3 | 26 | 480 | 289 | 122,880 | 58.78 | 316.94 |

All query rows completed. Failures and not-realized queries are retained in the raw/frontier artifacts; both counts are zero for these runs.

## Interpretation

The family-aware re-projection changes the development group-level sensitivity rows for B1/B2/B3 while leaving holdout group rows unchanged. That difference is a diagnostic of grouping sensitivity, not evidence that family membership is semantic relevance or legal family identity. The final holdout remains company-level and small.

The runs used the same runtime views and evaluator separation as the prior offline runner: raw rankings and runtime predictions were written before evaluator references were loaded. No evaluator relation was supplied to the retrieval runtime.

## Boundaries

No provider or network calls occurred. No raw third-party source was copied into this audit folder. No unjudged pair became a negative label. No paid budget reservation or ledger entry was created. The Bridge branch, live HT-B4, public raw-data release, clinical/FTO work, deployment, outreach, and Claude UX/UI remain blocked or paused.

## Next step

Use this as the current offline baseline receipt while preparing a rights-cleared relevance-judgment cohort with multiple independent company/family groups and an untouched final holdout. A future fresh baseline run must bind to that new cohort and its frozen denominator rules.
