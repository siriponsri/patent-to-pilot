# HealthTech HT-B4 offline controller audit

- Run ID: `luna-long-run-20261029-m4-b4-offline-eea0fb4`
- Date: `2026-10-29` (Asia/Bangkok)
- Base commit: `bd07d29a04420fd45d30ae328cbfe55aee13432d`
- Implementation commit: `eea0fb43df35014210097585940f865e2ba3d67b`
- Scope: bounded deterministic HT-B4 controller seam and two frozen public development cohorts
- Verdict: `PASS_OFFLINE_DEVELOPMENT`
- Provider calls: `0`
- Paid cost: `$0`

## Implemented

- Added a strict `ControllerObservation` / `ControllerAction` contract with no extra response fields.
- Added deterministic observation-based stop/continue policy for `technical_search`, `feature_search`, and `stop`.
- Added fail-closed validation for source availability, step caps, query/candidate budgets, and feature reuse.
- Added an offline runner that reuses the HT-B1/B2/B3 local dense/lexical/reranker stack and writes runtime predictions before loading evaluator references.
- Added focused unit coverage for first-query alignment, novelty/disagreement branching, evaluator-field rejection, invalid feature selection, and hard-budget stopping.

## Cohort results

| Cohort | Devices | Patents | Declared pairs | Macro known-link recall@20 | Micro known-link recall@20 | Query calls | Controller steps | Failed devices |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Boston Scientific WATCHMAN | 2 | 7 | 13 | 1.0000 | 1.0000 | 2 | 4 | 0 |
| Abbott public frozen cohort | 3 | 41 | 61 | 0.4988 | 0.4754 | 5 | 8 | 0 |

Boston is ceiling-limited because `K=20` exceeds its seven-patent universe. Abbott remains a three-device, two-exact-group descriptive slice. These results are not pooled scientific estimates and do not establish method superiority.

## Verification

- Focused controller and cross-cohort tests: `5 passed`.
- Full suite with explicit child import path: exit code `0`; all tests reached `100%`; one pre-existing `fitz` deprecation warning when warnings were enabled.
- Compile check: exit code `0` for `src`, `scripts`, and `tests`.
- Both real-cohort runs completed with zero provider calls, zero paid cost, zero failed eligible devices, and fresh ignored output directories.
- Runtime predictions and raw rankings were written before evaluator validation in both runs; file modification ordering and the runner write order agree.
- Controller observations contain no evaluator, gold, family, split, label, reference, or oracle fields.

Machine-readable details, source/output hashes, exact commands, and boundaries are in [`verification.json`](verification.json). The research-facing synthesis is in [`REPORT.md`](REPORT.md).

## Limits and not-run boundaries

- This is an offline deterministic controller, not a live LLM controller and not a paid-provider result.
- Abbott and Boston remain development-only public disclosure cohorts with no final holdout and insufficient independent groups for generalization uncertainty.
- Declared product-level disclosures are not claim-level semantic relevance gold; unjudged links are not negatives.
- No Bridge corpus acquisition, rights-cleared replacement, live-provider canary, deployment, clinical/FTO analysis, customer validation, or public raw-data release occurred.

## Next action

Keep the paid branch `BLOCKED_LOCAL`. Freeze the HT-T2 prediction manifest only if component predictions exist; otherwise retain `NOT_RUN`. The next scientific discriminator is a rights-cleared cohort with multiple independent company/family groups and a predeclared final holdout. See [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).
