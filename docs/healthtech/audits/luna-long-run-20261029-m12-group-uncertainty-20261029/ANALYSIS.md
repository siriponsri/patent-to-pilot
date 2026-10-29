# HealthTech long-run descriptive analysis

- Status: `PASS_DESCRIPTIVE_ANALYSIS_NOT_ESTIMABLE`
- Code tested: `d4f4881c6192a0107fac6702909d6970920e3067`
- Protocol hash: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`
- Cohort manifest hash: `1b42b7c4a52b697d9c5c4f7db4f9236b7d5d239d83584863a6ba844591adef75`
- Endpoint: macro known-link recall at K=20 over product-level disclosed links.

This analysis is generated from frozen local artifacts. It reports observed quality-resource relationships and holdout drift; it does not create semantic relevance labels or confirmatory statistical evidence.

## Quality-resource rows

| Split | Method | Macro R@20 | Wall seconds | Query calls | Group min | Group max | Pareto frontier |
|---|---|---:|---:|---:|---:|---:|---|
| development | HT-B0a | 0.9381 | 0.0011 | 5.0000 | 0.8452 | 1.0000 | YES |
| development | HT-B0b | 1.0000 | 0.0334 | 5.0000 | 1.0000 | 1.0000 | YES |
| development | HT-B1 | 1.0000 | 14.1720 | 5.0000 | 1.0000 | 1.0000 | NO |
| development | HT-B2 | 1.0000 | 52.0174 | 20.0000 | 1.0000 | 1.0000 | NO |
| development | HT-B3 | 1.0000 | 8.2567 | 7.0000 | 1.0000 | 1.0000 | NO |
| final_holdout | HT-B0a | 0.8190 | 0.0008 | 3.0000 | 0.6000 | 1.0000 | YES |
| final_holdout | HT-B0b | 0.9524 | 0.0097 | 3.0000 | 0.8571 | 1.0000 | YES |
| final_holdout | HT-B1 | 0.9333 | 9.0929 | 3.0000 | 0.8000 | 1.0000 | NO |
| final_holdout | HT-B2 | 0.9333 | 36.0992 | 12.0000 | 0.8000 | 1.0000 | NO |
| final_holdout | HT-B3 | 0.8857 | 13.5812 | 5.0000 | 0.8000 | 1.0000 | NO |

## Holdout minus development

| Method | Macro recall delta | Wall-time delta seconds | Status |
|---|---:|---:|---|
| HT-B0a | -0.1190 | -0.0003 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B0b | -0.0476 | -0.0237 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B1 | -0.0667 | -5.0791 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B2 | -0.0667 | -15.9182 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B3 | -0.1143 | 5.3245 | DESCRIPTIVE_NOT_ESTIMABLE |

## Paired group diagnostic

Methods are paired by `group_id` against `HT-B0b`. The predeclared minimum effective group threshold is `5`; this diagnostic does not estimate significance or a confirmatory interval.

| Split | Comparison | Groups | Mean delta | Population SD | Min delta | Max delta | Status |
|---|---|---:|---:|---:|---:|---:|---|
| development | HT-B0a minus HT-B0b | 3 | -0.0516 | 0.0730 | -0.1548 | 0.0000 | NOT_ESTIMABLE |
| development | HT-B1 minus HT-B0b | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | NOT_ESTIMABLE |
| development | HT-B2 minus HT-B0b | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | NOT_ESTIMABLE |
| development | HT-B3 minus HT-B0b | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | NOT_ESTIMABLE |
| final_holdout | HT-B0a minus HT-B0b | 3 | -0.1333 | 0.1886 | -0.4000 | 0.0000 | NOT_ESTIMABLE |
| final_holdout | HT-B1 minus HT-B0b | 3 | -0.0190 | 0.1406 | -0.2000 | 0.1429 | NOT_ESTIMABLE |
| final_holdout | HT-B2 minus HT-B0b | 3 | -0.0190 | 0.1406 | -0.2000 | 0.1429 | NOT_ESTIMABLE |
| final_holdout | HT-B3 minus HT-B0b | 3 | -0.0667 | 0.0943 | -0.2000 | 0.0000 | NOT_ESTIMABLE |

## B4 provider-shaped mock comparison

The B4 mock recall delta versus HT-B0b is `0.0000` and versus HT-B2 is `0.0000`. Simulated debit is `$0.0012` and paid cost is `$0.0000`. Status: `MOCK_ONLY_NOT_PROVIDER_EVIDENCE`.

## Interpretation

- HT-B0b is on the observed quality-resource frontier in both frozen views; this is descriptive and does not establish scientific superiority.
- HT-B1, HT-B2, and HT-B3 are dominated by HT-B0b on the observed wall-time/recall coordinates in these views.
- HT-B4 mock recall matches HT-B0b and HT-B2 on development, but the transport was mocked and therefore is not provider evidence.
- Small group counts, product-level disclosure labels, unjudged pairs, and the K=20 ceiling keep confirmatory uncertainty NOT_ESTIMABLE.
- Paired group diagnostics align methods by frozen group_id and report deltas/population SD only; the current effective group count is below the predeclared threshold of five, so uncertainty remains NOT_ESTIMABLE.
