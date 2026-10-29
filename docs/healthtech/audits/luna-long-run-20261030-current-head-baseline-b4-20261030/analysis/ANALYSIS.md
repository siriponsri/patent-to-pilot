# HealthTech long-run descriptive analysis

- Status: `PASS_DESCRIPTIVE_ANALYSIS_NOT_ESTIMABLE`
- Code tested: `aeaa8aa20c7840ebcf63f9f92b9d3e4d2f52ef83`
- Protocol hash: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`
- Cohort manifest hash: `d00d12ad7ebb8f37938e094f89b9dd9cedb288eb108718c7947caa991dcfc267`
- Endpoint: macro known-link recall at K=20 over product-level disclosed links.

This analysis is generated from frozen local artifacts. It reports observed quality-resource relationships and holdout drift; it does not create semantic relevance labels or confirmatory statistical evidence.

## Quality-resource rows

| Split | Method | Macro R@20 | Wall seconds | Query calls | Group min | Group max | Pareto frontier |
|---|---|---:|---:|---:|---:|---:|---|
| development | HT-B0a | 0.9613 | 0.0155 | 8.0000 | 0.8452 | 1.0000 | YES |
| development | HT-B0b | 1.0000 | 0.2497 | 8.0000 | 1.0000 | 1.0000 | YES |
| development | HT-B1 | 0.9688 | 63.3225 | 8.0000 | 0.7500 | 1.0000 | NO |
| development | HT-B2 | 0.9062 | 273.1108 | 32.0000 | 0.5000 | 1.0000 | NO |
| development | HT-B3 | 0.9688 | 93.7396 | 11.0000 | 0.7500 | 1.0000 | NO |
| final_holdout | HT-B0a | 0.5429 | 0.0008 | 3.0000 | 0.2000 | 1.0000 | YES |
| final_holdout | HT-B0b | 0.8095 | 0.0122 | 3.0000 | 0.4286 | 1.0000 | YES |
| final_holdout | HT-B1 | 0.8381 | 22.6533 | 3.0000 | 0.7143 | 1.0000 | YES |
| final_holdout | HT-B2 | 0.8857 | 101.1710 | 12.0000 | 0.8000 | 1.0000 | YES |
| final_holdout | HT-B3 | 0.8381 | 41.3900 | 5.0000 | 0.7143 | 1.0000 | NO |

## Holdout minus development

| Method | Macro recall delta | Wall-time delta seconds | Status |
|---|---:|---:|---|
| HT-B0a | -0.4185 | -0.0147 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B0b | -0.1905 | -0.2375 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B1 | -0.1307 | -40.6691 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B2 | -0.0205 | -171.9398 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B3 | -0.1307 | -52.3496 | DESCRIPTIVE_NOT_ESTIMABLE |

## Paired group diagnostic

Methods are paired by `group_id` against `HT-B0b`. The predeclared minimum effective group threshold is `5`; this diagnostic does not estimate significance or a confirmatory interval.

| Split | Comparison | Groups | Mean delta | Population SD | Min delta | Max delta | Status |
|---|---|---:|---:|---:|---:|---:|---|
| development | HT-B0a minus HT-B0b | 6 | -0.0258 | 0.0577 | -0.1548 | 0.0000 | DESCRIPTIVE_ONLY |
| development | HT-B1 minus HT-B0b | 6 | -0.0417 | 0.0932 | -0.2500 | 0.0000 | DESCRIPTIVE_ONLY |
| development | HT-B2 minus HT-B0b | 6 | -0.1250 | 0.1909 | -0.5000 | 0.0000 | DESCRIPTIVE_ONLY |
| development | HT-B3 minus HT-B0b | 6 | -0.0417 | 0.0932 | -0.2500 | 0.0000 | DESCRIPTIVE_ONLY |
| final_holdout | HT-B0a minus HT-B0b | 3 | -0.2667 | 0.3771 | -0.8000 | 0.0000 | NOT_ESTIMABLE |
| final_holdout | HT-B1 minus HT-B0b | 3 | 0.0286 | 0.1993 | -0.2000 | 0.2857 | NOT_ESTIMABLE |
| final_holdout | HT-B2 minus HT-B0b | 3 | 0.0762 | 0.2622 | -0.2000 | 0.4286 | NOT_ESTIMABLE |
| final_holdout | HT-B3 minus HT-B0b | 3 | 0.0286 | 0.1993 | -0.2000 | 0.2857 | NOT_ESTIMABLE |

## B4 provider-shaped mock comparison

The B4 mock recall delta versus HT-B0b is `-0.0312` and versus HT-B2 is `0.0625`. Simulated debit is `$0.0019` and paid cost is `$0.0000`. Status: `MOCK_ONLY_NOT_PROVIDER_EVIDENCE`.

## Interpretation

- Observed development quality-resource frontier methods are HT-B0a, HT-B0b; this is descriptive and does not establish scientific superiority.
- Observed final-holdout quality-resource frontier methods are HT-B0a, HT-B0b, HT-B1, HT-B2; frontier membership is descriptive for the frozen groups.
- HT-B4 mock recall matches HT-B1, HT-B3 on development; it is above HT-B0a, HT-B2 and below HT-B0b. The transport was mocked and therefore is not provider evidence.
- Small group counts, product-level disclosure labels, unjudged pairs, and the K=20 ceiling keep confirmatory uncertainty NOT_ESTIMABLE.
- Paired group diagnostics align methods by frozen group_id and report deltas/population SD only; the current effective group count is below the predeclared threshold of five, so uncertainty remains NOT_ESTIMABLE.
