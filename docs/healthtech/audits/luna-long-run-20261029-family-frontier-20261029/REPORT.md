# HT-M3 family-aware frontier report

## Objective and scope

The family mapping package established sourced Google family IDs but did not yet expose family-aware group rows in the frozen baseline outputs. This package adds a deterministic evaluator-side analyzer that reprojects those outputs onto sourced family groups.

Included:

- the five-method HT-B0a/B0b/B1/B2/B3 development frontier for the Boston Scientific/Cook view;
- the three-query Stryker final-holdout frontier;
- exact-patent versus family-aware group rows at `K=10`, `K=20`, and `K=50`;
- family-aware rows for every observed frontier prefix.

Excluded:

- runtime retrieval, ranking, controller observations, and source acquisition;
- new judgments, negative labels, or family inference for unmapped patents;
- live/provider calls, paid inference, Bridge acquisition, clinical/FTO work, and public release.

## Deliverable

`scripts/healthtech/analyze_family_frontier.py` loads the frozen baseline outputs only after the baseline has already written predictions, reads the separate sourced mapping, and emits a compact family-aware analysis artifact. The existing exact-group metrics remain in the output for direct comparison. Group identity is compared by normalized query-set membership, so differences in numeric group ordering cannot create a false mismatch.

## Evidence

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| Keep baseline rankings and exact metrics unchanged | PASS | Analyzer reads `per_device_group_results.json` and `frontier_diagnostics.json`; no runtime files are mutated |
| Apply only sourced family links | PASS | Mapping status `SOURCED_LOCAL_EVALUATOR_MAPPING`; 24 mapped patents and 19 families |
| Reproject every method/cutoff | PASS | 5 methods x 3 cutoffs on both splits; normalized family/exact group rows match |
| Reproject every frontier prefix | PASS | 9 frontier rows per split; normalized family/exact group rows match |
| Preserve uncertainty limits | PASS | Both outputs report `NOT_ESTIMABLE`; no interval or pooled claim is produced |
| Keep resource boundary closed | PASS | 0 provider calls, 0 network acquisition, 0 neural calls, `$0.00` paid cost |
| Full repository regression | PASS | Controlled `PYTHONPATH=src` run -> `351 passed`, one existing `fitz` deprecation warning |

## Results

| Split | Queries | Exact groups | Family-aware groups | Family merges | Frontier rows | Group-set equality |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Development | 5 | 3 | 3 | 0 | 9 | PASS |
| Final holdout | 3 | 3 | 3 | 0 | 9 | PASS |

The family-aware rows preserve the existing group metrics because the sourced family mapping introduces no cross-exact-group connection in this cohort. The result is a confirmed sensitivity outcome, not evidence that future cohorts can omit family mapping.

## Input matrix

| Input | Path | Hash or binding |
| --- | --- | --- |
| Family mapping | `results/healthtech/ht-google-family-mapping-20261029-r1/family-mapping.json` | file SHA-256 `7510b2f3fc18cef00419297e73f05985ed4aac25c58f6374274b98ff43d89dfd`; mapping SHA-256 `e4baa2e4eb1295c4abf9314fe5f2a60dd853151c7089f032801dc7fdef31f898` |
| Development baseline | `results/healthtech/ht-multicompany-baselines-20261029-r2-dev-cook` | receipt SHA-256 `aaa27d7125d60a41cbe2574b0aaab3032b1d00ce56a6c2843308c3fd05c3b5b9` |
| Holdout baseline | `results/healthtech/ht-multicompany-baselines-20261029-r2-holdout-cook` | receipt SHA-256 `8c3871678fa6c83a69ca52688c0bb2d4eeecc1e9dea092ba157070cdff13e78e` |
| Development analysis | `results/healthtech/ht-family-frontier-analysis-20261029-r1/development.json` | file SHA-256 `b0e2edf4088fe0c95bc505a23f68c6354e6e5e9bb0de177aa2380592faadbb7d` |
| Holdout analysis | `results/healthtech/ht-family-frontier-analysis-20261029-r1/final_holdout.json` | file SHA-256 `675451f9cf0b4cdfb05a0e135698cefac0a486f88bf6691e821fac65eddfdda3` |

## Risks and limitations

- Family IDs are explicit page metadata, not legal family opinions or semantic relevance labels.
- The current product-level disclosure relations are source-backed associations, not independent expert relevance gold.
- Three family-aware groups in development and three in holdout do not support stable confidence intervals or generalization claims.
- The analyzer does not add a licensed relevance-judgment cohort or make Bridge usable.

## Handoff

Status is `READY_FOR_REVIEW` for this offline M3 package. The next actor should acquire or receive a rights-cleared relevance-judgment cohort, freeze group/split rules before scoring, and preserve unjudged pairs as unjudged.
