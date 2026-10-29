# HT-M13 Philips expansion audit

- Run ID: `luna-long-run-20261029-m13-philips-expansion-20261029`
- Date: `2026-10-29`
- Base commit: `fa5b85a9c782ef7d1d0d70606df8c42f845f7248`
- Tested source state: `working-tree` with the Philips adapter, tests, rights matrix, composite, and baseline outputs described below
- Status: `PASS_DESCRIPTIVE_ANALYSIS_NOT_ESTIMABLE`

## Outcome

This package adds a bounded Philips cardiovascular development cohort to the existing Boston Scientific, Stryker Neurovascular, and Cook Medical composite. The family-aware composite contains `11` devices, `31` patents, `38` disclosed pairs, and `303` unjudged distractor pairs. The untouched Stryker final holdout remains `3` queries. Typed provenance passes for all `38/38` disclosed pairs under Boston, Stryker, Cook, and Philips disclosure policies.

The offline runner completed all `40/40` development and `15/15` holdout method-query rows for HT-B0a/B0b/B1/B2/B3 with `0` failures, `0` provider calls, and `$0.00` paid cost. The primary `K=20` exact/family-aware macro recall is:

| Method | Development | Stryker holdout |
|---|---:|---:|
| HT-B0a | 0.9613 | 0.5429 |
| HT-B0b | 1.0000 | 0.8095 |
| HT-B1 | 0.9688 | 0.8381 |
| HT-B2 | 0.9063 | 0.8857 |
| HT-B3 | 0.9688 | 0.8381 |

Family projection finds `6` exact and family-aware groups in development and `3` in holdout, with `0` exact groups merged by the sourced family mapping. Confidence intervals and stable generalization estimates remain `NOT_ESTIMABLE`.

## Philips cohort

The selected official Philips marking rows are AngioSculpt Scoring Balloon Catheter, Thromcat Thrombectomy Catheter System, and Turbo-Elite Laser Atherectomy Catheter. The adapter preserves raw and canonical patent IDs, source revisions/hashes, locators, typed rights policy IDs, evaluator/runtime separation, and unjudged distractors. The valid `r2` cohort records `3` devices, `7` patents, `7` disclosed pairs, `14` unjudged distractors, `4,709,140` transferred bytes, `4,927,625` stored bytes, `0` provider calls, and `$0.00` paid cost.

The earlier Philips acquisition `r1` is retained as a failed attempt because its manifest omitted `distractors_path`; it was not used for composition or baseline claims. The corrected `r2` output passed typed provenance and is the only Philips input used here.

## Reproduction anchors

- Philips source adapter: `scripts/healthtech/fetch_philips_cardiovascular_cohort.py`
- Philips tests: `tests/test_healthtech_philips_cohort.py`
- Philips cohort: `results/healthtech/ht-philips-cardiovascular-20261029-r2/`
- Family-aware composite: `results/healthtech/ht-multicompany-20261029-r4-philips-family/`
- Family mapping: `results/healthtech/ht-google-family-mapping-20261029-r2-philips/family-mapping.json`
- Development baseline: `results/healthtech/ht-multicompany-baselines-20261029-philips-family-r1-dev/`
- Final holdout baseline: `results/healthtech/ht-multicompany-baselines-20261029-philips-family-r1-holdout/`
- Development family projection: `results/healthtech/ht-family-frontier-20261029-r3-philips-development`
- Holdout family projection: `results/healthtech/ht-family-frontier-20261029-r3-philips-holdout`
- Machine-readable summary: [`baseline-summary.json`](baseline-summary.json)
- Machine-readable verification: [`verification.json`](verification.json)

## Interpretation limits

- Product-level patent marking is source-backed disclosure evidence, not independent semantic relevance gold.
- Unlisted device-patent pairs remain unjudged and are not false negatives.
- Google-derived patent text and third-party marking payloads remain local-only; the rights matrix does not grant redistribution rights.
- The family mapping is evaluator-side metadata and does not change runtime inputs.
- The final holdout is a single-company transfer check with only `3` eligible queries; no stable generalization or statistical claim is supported.
- K=50 reaches `1.0` on both splits because it is ceiling-limited by the `31`-patent universe; it is not a meaningful method discriminator.
- No clinical/FTO, patent-validity, investment, live-provider, user, or publication claim is supported.

## Verification

Focused HealthTech tests pass (`39` tests, one existing `fitz` deprecation warning), compile checks pass, the Philips-only provenance check passes, the composite typed-policy provenance check passes, both offline baseline splits pass, and the family projections pass. Full-suite rerun, paid provider dispatch, semantic gold, and publication readiness are not claimed by this package.

The canonical continuation note is [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).
