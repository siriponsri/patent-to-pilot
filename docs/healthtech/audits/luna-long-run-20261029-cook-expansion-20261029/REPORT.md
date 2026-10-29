# Cook Zenith cohort expansion report

## Boundary

This package is a descriptive offline research artifact. Product-level patent-marking rows are disclosed relationships, not independent claim-level relevance judgments. Unlisted device-patent pairs remain unjudged and are not treated as negatives. Google-derived patent HTML and Cook marking material remain local-only.

## Cohort freeze

| View | Devices | Patents | Disclosed pairs | Unjudged distractors | Exact groups | Company groups | Holdout |
|---|---:|---:|---:|---:|---:|---:|---|
| Cook parent | 3 | 4 | 5 | 7 | 2 | 1 | none |
| Composite development | 5 | 24 | 18 | 102 | 3 | 3 | none |
| Composite final holdout | 3 | 24 | 13 | 59 | 3 | 1 | Stryker Neurovascular |
| Composite total | 8 | 24 | 31 | 161 | 4 | 3 | 3 queries |

The Cook Flex and Renu rows share exact patent `US7335224B2`; no patent-family merge is inferred. The full Stryker company group is held out before baseline execution.

## Offline baselines at K=10

| Method | Development | Stryker holdout |
|---|---:|---:|
| HT-B0a | 0.9381 | 0.3333 |
| HT-B0b | 1.0000 | 0.6667 |
| HT-B1 | 0.9000 | 0.7429 |
| HT-B2 | 0.7762 | 0.7905 |
| HT-B3 | 0.9000 | 0.7905 |

All scheduled queries completed without failure. The runner recorded `0` provider calls and `$0.00` paid cost in both views. `K=20` is ceiling-limited by the 24-patent universe and is not the primary comparison.

## Interpretation

- Cook expands the development slice to a third typed-policy company group without changing the Stryker holdout assignment.
- The holdout is a single-company transfer check, not a stable generalization estimate.
- The lower holdout scores reflect the fixed 24-document universe and the Stryker product rows; they do not establish method superiority or semantic relevance.
- This package does not resolve family identity, Bridge rights, live-provider readiness, clinical/FTO questions, patent validity, investment merit, or publication readiness.

## Reproduction anchors

- Cook parent: `results/healthtech/ht-cook-zenith-20261029-r1/`
- Composite: `results/healthtech/ht-multicompany-20261029-r2/`
- Development run: `results/healthtech/ht-multicompany-baselines-20261029-r2-dev-cook-k10/`
- Holdout run: `results/healthtech/ht-multicompany-baselines-20261029-r2-holdout-cook-k10/`
- Machine-readable verification: [verification.json](verification.json)
