# M18 report

## Decision

The existing HT-T2 development run now has a reproducible evaluator-only error profile. The output is suitable for the G6 methods/results skeleton as a descriptive diagnostic and does not change the scientific or provider readiness gates.

## Inputs and outputs

- Prediction manifest: `results/healthtech/ht-t2-scifact-lexical-dev-20261029-r3/prediction_manifest.json`.
- Score: `results/healthtech/ht-t2-scifact-lexical-dev-20261029-r3/score.json`.
- Analysis output: `results/healthtech/ht-t2-scifact-lexical-dev-20261029-r4-error-analysis/analysis.json` and `ANALYSIS.md`.
- Per-claim bucket rows remain local under the ignored results directory.

## Interpretation

The lexical baseline has 78 abstract retrieval misses and 59 sentence retrieval misses among 300 dev claims. The 20 abstract rationale mismatches and 38 sentence label mismatches show a second failure mode after retrieval. The 112 no-gold-evidence claims are reported separately and are not treated as retrieval failures. Because these counts overlap by design and the split is development-only, they are diagnostic rather than inferential.
