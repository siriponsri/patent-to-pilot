# HT-T1 relevance-judgment contract report

## Objective

Create a reusable evaluator-side intake boundary for future semantic relevance judgments without turning product-level patent marking, retrieval hits, or unlisted pairs into gold labels.

## Contract

Module: `src/patent_to_pilot/evaluation/healthtech/judgments.py`
CLI: `scripts/healthtech/validate_relevance_judgments.py`
Format: `ht-relevance-judgment-cohort-v1`

The validator binds each explicit label to a registered source with a source revision, SHA-256, rights policy, intended use, use decision, and locator. It accepts only `relevant` and `not_relevant` labels; absence means `unjudged`. `product_disclosure` is rejected as a semantic basis. Synthetic authored fixtures must be marked `synthetic=true` and are never treated as real gold by the report.

Runtime validation is separate from evaluator labels. The CLI reads a runtime-only cohort, validates query and canonical patent membership, and compares the runtime file hash to the manifest. Required runtime exclusions make the separation auditable.

## Split and group checks

Every runtime query must have one split row with a company group and an optional sourced family group. Under the declared holdout policy, company and family IDs cannot overlap across splits, and a final holdout can require complete family mapping. The report exposes overlap diagnostics and returns `NOT_ESTIMABLE` unless the structure is descriptive-holdout-ready; it does not produce confidence intervals.

## Evidence

The authored CLI smoke used the existing family-aware development runtime only as a universe. It created two synthetic fixture labels and preserved the remaining `118` query-patent pairs as unjudged. The focused tests cover valid counts, duplicate/conflicting pairs, product-disclosure rejection, cross-split company/family leakage, source hash mismatch, missing runtime exclusions, and runtime hash mismatch.

## Boundaries

No third-party content, credentials, evaluator-only relations, or real expert labels were added. No provider call or paid action occurred. This is engineering readiness for a future rights-cleared cohort, not a scientific judgment dataset.

## Next step

Apply the contract to an actual permitted relevance source, then freeze the source registry, query universe, judgment denominator, company/family groups, and final holdout before rerunning HT-B0a/B0b/B1/B2/B3 or considering a paid HT-B4 pilot.
