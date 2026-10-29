# Report: multi-company cohort and final holdout

## Objective and scope

The package tests whether the existing offline retrieval controls remain operational when the typed-policy Boston Scientific and Stryker snapshots are composed into one candidate universe with a predeclared untouched holdout.

Inputs are existing local snapshots only. No new raw third-party acquisition, provider transfer, paid inference, clinical analysis, FTO analysis, or public redistribution occurred.

## Deliverable

The new composite contains 5 devices, 20 canonical US-grant patents, 26 product-level disclosed pairs, 74 unjudged distractor pairs, 4 exact-patent groups, and 2 company groups. The full Stryker company group is final holdout; both Boston WATCHMAN rows are development queries. Family mappings remain unknown and are not inferred.

The builder writes full-cohort artifacts plus separate development and final-holdout runtime/reference/group views. Parent manifest hashes are preserved in the composite manifest, while raw parent files remain in their original ignored local locations.

## Evidence

| Criterion | Status | Evidence |
|---|---|---|
| Typed rights binding | PASS | `provenance-verification.json`; 26/26 pairs covered, 0 unresolved policies |
| Runtime/evaluator separation | PASS | composite runtime status sentinel, exclusions, and baseline evaluator-validation receipts |
| Predeclared untouched holdout | PASS | `split_manifest.json`; 3 Stryker queries and 3 exact-patent groups |
| Deterministic composition | PASS | repeated fresh compose produced identical cohort hash |
| Shared offline methods | PASS | both baseline receipts list HT-B0a/B0b/B1/B2/B3, 0 failed queries |
| Cost boundary | PASS | 0 provider calls and `$0.00` paid cost in both runs |

The more informative `K=10` holdout macro known-link recall is 0.4952, 0.7619, 0.7905, 0.7905, and 0.8381 for HT-B0a/B0b/B1/B2/B3. The `K=20` rows are ceiling-limited by the 20-document universe.

## Risks and limitations

- This is known-link recovery against product-level marking relationships, not exhaustive recall or semantic relevance gold.
- Two companies are present, but only one company is held out; uncertainty is not estimable as a stable cross-company generalization interval.
- Family identity is not sourced in these parent snapshots and remains `UNKNOWN_NOT_ASSUMED`.
- The results are offline development evidence, not publication, investment, clinical, FTO, or deployment evidence.

## Handoff

Continue with a larger rights-cleared cohort containing more than two independent companies and sourced family mappings where available. Preserve the company-level holdout rule, freeze the endpoint before any pooled comparison, and keep paid/provider HT-B4 `BLOCKED_LOCAL` until its separate readiness gates pass.
