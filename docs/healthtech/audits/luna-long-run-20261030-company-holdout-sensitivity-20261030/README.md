# HT-M20 company holdout sensitivity

- Run ID: `luna-long-run-20261030-company-holdout-sensitivity-20261030`
- Run date: `2026-10-29` (Asia/Bangkok local execution)
- Handoff date: `2026-10-30`
- Status: `PASS_OFFLINE_COMPANY_HOLDOUT_SENSITIVITY`
- Source head at experiment start: `47aeefcd190ee109f9fb9b9f1ac5c8f37e9bdafe`
- Scope: four leave-one-company-out reruns over the existing typed-policy Boston/Stryker/Cook/Philips local cohort

## Result

The new reusable runner created four frozen company-held-out views over the same
11-device, 31-patent, 38 disclosed-pair development corpus. Each view ran the
same HT-B0a/B0b/B1/B2/B3 controls at candidate and rerank depth 31, with the
held-out company kept untouched until scoring. All eight baseline splits
completed with zero failed devices, zero provider calls, zero network calls,
and USD 0.00 paid cost.

| Held-out company | Development devices | Holdout devices | B0a | B0b | B1 | B2 | B3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Boston Scientific Corp | 9 | 2 | 0.845238 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| Stryker Neurovascular | 8 | 3 | 0.542857 | 0.809524 | 0.838095 | 0.885714 | 0.838095 |
| Cook Medical | 8 | 3 | 1.000000 | 1.000000 | 1.000000 | 0.833333 | 1.000000 |
| Philips Image Guided Therapy | 8 | 3 | 1.000000 | 1.000000 | 0.916667 | 0.916667 | 0.916667 |

Values are macro known-link Recall@20 against product-level disclosure
relationships. Across the four holdouts, the observed ranges are B0a
`0.542857–1.000000`, B0b `0.809524–1.000000`, B1 `0.838095–1.000000`, B2
`0.833333–1.000000`, and B3 `0.838095–1.000000`.

## Interpretation

This is a sensitivity analysis of the existing development proxy. It reduces
dependence on the single Stryker holdout, but the four rows reuse the same local
companies and product-disclosure relations; they are not independent samples.
Product marking is not semantic relevance gold, unlisted pairs remain
unjudged, and ceiling effects remain possible when a small patent universe is
ranked at `K=20`.

The Stryker holdout is the lowest observed transfer case for B0a, B0b, B1, and
B3; Cook is lowest for B2. That pattern is descriptive and does not establish
method superiority, stable generalization, exhaustive recall, or statistical
significance.

## Verification and limits

- Runner: `scripts/healthtech/run_company_holdout_sensitivity.py`.
- Focused regression: `2 passed`; targeted compilation passed.
- Baseline runner hash: `fd2f5275214d50b9129fed28f76fbbb7a8a8c15d517bf587185feac5689f7fcb`.
- Composite builder hash: `ebed14ef5a9699b2db556a35921549b5cc6ea074abaf3a052b5792d6e17d04f7`.
- Post-run orchestrator hash after logging-only path sanitization: `ca5dc806b319d379f6327a19a6b4ad1335b32fabd76a69abec0bdfd7cff5e7f8`.
- Machine-readable artifact hashes and command outcomes are in `verification.json`.
- The experiment did not acquire new raw sources, create semantic labels, dispatch HT-B4, or transfer data externally.

The next scientific discriminator remains a rights-cleared semantic device-
patent judgment source with explicit labels, source revision/hash, locators,
multiple independent company/family groups, and a predeclared untouched final
holdout. Keep Bridge, paid HT-B4, deployment, outreach, clinical/FTO, public
raw-data release, and Claude UX/UI paused.
