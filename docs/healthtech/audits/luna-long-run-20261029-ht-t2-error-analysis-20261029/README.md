# HT-M18 SciFact error analysis

- Run ID: `luna-long-run-20261029-ht-t2-error-analysis-20261029`
- Date: `2026-10-29` (Asia/Bangkok)
- Status: `PASS_COMPONENT_ERROR_ANALYSIS_DEV_ONLY`
- Scope: deterministic evaluator-only analysis of the existing HT-T2 dev run
- Parent package: `../luna-long-run-20261029-ht-t2-lexical-dev-20261029/README.md`

## Objective

Turn the existing 300-claim HT-T2 development score into a reproducible failure profile without changing the frozen prediction manifest, reading labels during runtime generation, or creating any device-patent semantic gold.

## Outcome

The new `scripts/healthtech/analyze_scifact_errors.py` recomputes the evaluator metrics only after the prediction artifact exists, verifies the score’s manifest/prediction/corpus/dev-label hashes, and writes a local analysis over all 300 claims and 5,183 corpus documents.

The measured non-exclusive buckets are:

| Failure mode | Claims | Rate |
|---|---:|---:|
| Abstract retrieval miss | 78 | 0.2600 |
| Abstract partial retrieval | 5 | 0.0167 |
| Abstract rationale mismatch | 20 | 0.0667 |
| Sentence retrieval miss | 59 | 0.1967 |
| Sentence partial selection | 46 | 0.1533 |
| Sentence label mismatch | 38 | 0.1267 |
| No abstract/sentence gold evidence | 112 | 0.3733 |

Bucket counts are intentionally non-exclusive. Claims with no gold evidence are kept separate from retrieval misses. No claim text, abstract text, or evaluator relation is copied into the committed audit package; the per-claim bucket file remains in ignored local results.

## Verification

- Targeted regression: `3 passed` in `tests/test_healthtech_scifact_error_analysis.py`.
- In-memory syntax compilation: the new script and test both compile successfully.
- Real run: `PASS_COMPONENT_ERROR_ANALYSIS_DEV_ONLY`, 300 claims, 5,183 documents.
- Provider calls: `0`; paid cost: `USD 0.00`; network calls: `0`.

The G6 manuscript skeleton now reports this profile as a separate HT-T2 diagnostic. It is not pooled with HT-T1 patent-association recall and does not support hidden-test, clinical, patent-validity, FTO, investment, or publication claims.

## Limits and next step

This package does not resolve the rights-cleared semantic device-patent cohort blocker and does not authorize live/provider HT-B4. The next scientific discriminator remains a rights-cleared device cohort with multiple independent company/family groups, explicit judgments, frozen denominators, and a predeclared untouched holdout.
