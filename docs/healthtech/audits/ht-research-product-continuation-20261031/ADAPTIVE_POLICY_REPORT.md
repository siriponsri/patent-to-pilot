# Adaptive acquisition policy report

- Status: `PARTIAL_OFFLINE_ADAPTIVE_POLICY_REPORT`
- Code commit: `4f15a2075e3d21c10479daffd4da5bbd932b0d02`
- Parent audit: `docs/healthtech/audits/ht-research-product-20261031`
- Endpoint: macro known-link recall at K=20; descriptive only.

## Fixed controls and provider-shaped adaptive row

| Method | Adaptive | Macro R@20 | Query calls | Rerank pairs | Paid cost | Status |
|---|---:|---:|---:|---:|---:|---|
| HT-B0a | no | 0.8190 | 3 | 0 | $0.0000 | OFFLINE_CONTROL |
| HT-B0b | no | 0.9524 | 3 | 0 | $0.0000 | OFFLINE_CONTROL |
| HT-B1 | no | 0.9333 | 3 | 72 | $0.0000 | OFFLINE_CONTROL |
| HT-B2 | no | 0.9333 | 12 | 288 | $0.0000 | OFFLINE_CONTROL |
| HT-B3 | no | 0.8857 | 5 | 120 | $0.0000 | OFFLINE_CONTROL |
| HT-B4-MOCK | yes | 0.8857 | 5 | 120 | $0.0000 | MOCK_ONLY_NOT_PROVIDER_EVIDENCE |

## Offline deterministic controller

| Cohort | Devices | Macro R@20 | Micro R@20 | Query calls | Provider calls | Paid cost |
|---|---:|---:|---:|---:|---:|---:|
| abbott | 3 | 0.4988 | 0.4754 | 5 | 0 | $0.0000 |
| boston | 2 | 1.0000 | 1.0000 | 2 | 0 | $0.0000 |

## Interpretation

- The fixed-policy HT-B4 mock matches HT-B3 on holdout macro known-link recall in this run.
- The HT-B4 mock is below HT-B0b, HT-B1, and HT-B2 on holdout macro known-link recall in this run.
- Mock provider-shaped calls exercise the action schema and accounting path but are not live-provider evidence.
- The holdout remains a small company-level transfer check with product-level disclosures, unjudged pairs, and NOT_ESTIMABLE generalization.

## Boundaries

- `live_qwen3_controller`: `NOT_RUN_BLOCKED_LOCAL`
- `semantic_relevance_gold`: `NOT_RUN`
- `clinical_f_to_validity_investment`: `OUT_OF_SCOPE`
- `exhaustive_recall`: `NOT_ESTABLISHED`
- `publication_readiness`: `NOT_ESTABLISHED`

## Limitations

- The adaptive provider-shaped row is a mock transport and is not live-provider evidence.
- The offline controller is deterministic; it is not a Qwen3 controller.
- Product-level disclosed links are not claim-level semantic relevance gold.
- The effective independent group count is small and cohort candidate universes differ.
- The current O3 Qwen3-8B versus qwen/qwen3-32b generation comparison remains blocked locally.

Next discriminating test: Freeze a rights-cleared cohort and local Qwen3-8B revision, then compare a live or locally executed bounded controller against the same fixed controls under a frozen protocol.
