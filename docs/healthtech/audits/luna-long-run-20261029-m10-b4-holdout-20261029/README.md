# HT-M10 B4 provider-shaped holdout comparison

Status: `PASS_B4_PROVIDER_SHAPED_HOLDOUT_DESCRIPTIVE`

## Objective

Compare the successful fixed-policy HT-B4 provider-shaped mock run on the untouched final holdout with the frozen offline HT-B0a/B0b/B1/B2/B3 controls. This package is descriptive and does not estimate semantic relevance performance or live-provider behavior.

## Inputs and provenance

- Final holdout: 3 untouched Stryker queries, 24 runtime patents, 3 family-aware groups.
- Offline control frontier: `results/healthtech/ht-multicompany-baselines-20261029-family-r1-holdout/frontier_diagnostics.json`.
- B4 mock frontier: `results/healthtech/ht-b4-r1-mock-20261029-holdout-r2/controller_frontier.json`.
- B4 mock receipt: `results/healthtech/ht-b4-r1-mock-20261029-holdout-r2/receipt.json`.
- Protocol hash: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`.
- Cohort manifest hash: `1b42b7c4a52b697d9c5c4f7db4f9236b7d5d239d83584863a6ba844591adef75`.
- Comparison code commit: `b12ef954a22f30c33e87c6ed78d8d40cc97d4fe3`.

## Result

The HT-B4 mock completed 8 provider-shaped calls, 120 rerank pairs, macro known-link recall@20 of `0.8857142857142857`, micro known-link recall@20 of `0.8461538461538461`, simulated debit of USD `0.0008`, paid cost of USD `0.00`, zero unknown/pending billing items, and no ledger breach.

On the final holdout, HT-B4-MOCK matched HT-B3 at macro recall `0.8857` and was below HT-B0b (`0.9524`), HT-B1 (`0.9333`), and HT-B2 (`0.9333`). It exceeded HT-B0a (`0.8190`) on this descriptive endpoint. These deltas are marked `DESCRIPTIVE_NOT_ESTIMABLE`.

## Verification

Focused comparison tests passed `2/2`; compile checks passed; the real comparison generator returned `PASS_B4_PROVIDER_SHAPED_HOLDOUT_DESCRIPTIVE` and wrote the machine-readable and Markdown outputs in this directory. No live provider request or paid spend was made by this package.

Exact inputs, hashes, command outcomes, and boundaries are in [`verification.json`](verification.json). The generated comparison is in [`COMPARISON.md`](COMPARISON.md), [`comparison.json`](comparison.json), and [`comparison.csv`](comparison.csv).

## Boundaries

- The provider-shaped mock exercises the action schema and accounting path; it is not live-provider evidence.
- Product-level disclosed links are not rights-cleared semantic relevance gold.
- Unjudged query-patent pairs remain unjudged and are not negatives.
- This is a small company-level transfer check, not exhaustive recall, stable generalization, statistical significance, clinical suitability, FTO, patent validity, investment merit, or publication readiness.
- Live HT-B4 remains `BLOCKED_LOCAL` pending explicit provider-transfer rights, credentials/credit, payload, pricing/identity, bound, and reconciliation gates.
