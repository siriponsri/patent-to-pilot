# HT-B4 provider-shaped holdout comparison

- Status: `PASS_B4_PROVIDER_SHAPED_HOLDOUT_DESCRIPTIVE`
- Code tested: `b12ef954a22f30c33e87c6ed78d8d40cc97d4fe3`
- Protocol hash: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`
- Cohort manifest hash: `1b42b7c4a52b697d9c5c4f7db4f9236b7d5d239d83584863a6ba844591adef75`
- Split: `final_holdout`; endpoint: macro known-link recall at K=20.

| Method | Macro known-link R@20 | Calls | Rerank pairs | Paid cost | Status |
|---|---:|---:|---:|---:|---|
| HT-B0a | 0.8190 | 3.0 | 0.0 | $0.0000 | OFFLINE_CONTROL |
| HT-B0b | 0.9524 | 3.0 | 0.0 | $0.0000 | OFFLINE_CONTROL |
| HT-B1 | 0.9333 | 3.0 | 72.0 | $0.0000 | OFFLINE_CONTROL |
| HT-B2 | 0.9333 | 12.0 | 288.0 | $0.0000 | OFFLINE_CONTROL |
| HT-B3 | 0.8857 | 5.0 | 120.0 | $0.0000 | OFFLINE_CONTROL |
| HT-B4-MOCK | 0.8857 | 8 | 120.0 | $0.0000 | MOCK_ONLY_NOT_PROVIDER_EVIDENCE |

HT-B4 mock simulated debit: `$0.0008`; unknown/pending billing items: `0`; ledger breach: `False`.

## B4 minus fixed controls

| Control | Macro recall delta | Status |
|---|---:|---|
| HT-B0a | 0.0667 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B0b | -0.0667 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B1 | -0.0476 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B2 | -0.0476 | DESCRIPTIVE_NOT_ESTIMABLE |
| HT-B3 | 0.0000 | DESCRIPTIVE_NOT_ESTIMABLE |

## Interpretation

- The fixed-policy HT-B4 mock matches HT-B3 on holdout macro known-link recall in this run.
- The HT-B4 mock is below HT-B0b, HT-B1, and HT-B2 on holdout macro known-link recall in this run.
- Mock provider-shaped calls exercise the action schema and accounting path but are not live-provider evidence.
- The holdout remains a small company-level transfer check with product-level disclosures, unjudged pairs, and NOT_ESTIMABLE generalization.
