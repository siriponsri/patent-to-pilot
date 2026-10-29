# M21 report

## Decision

Integrate the completed M20 company-holdout sensitivity into the G6 manuscript
skeleton as descriptive offline evidence. Keep the scientific and rights
boundaries unchanged.

## Changes

- Added a G6 section for four leave-one-company-out views.
- Recorded the frozen `11`-device / `31`-patent / `38`-disclosed-pair cohort.
- Recorded M20's `K=20`, candidate depth `31`, and rerank depth `31` setting.
- Added the exact four-company macro known-link Recall@20 table.
- Preserved the `303` explicitly unjudged distractor policy from M20.
- Added a regression that checks the G6 narrative against the M20 audit.

## Evidence

M20 completed all eight development/holdout splits with zero failed devices,
zero provider/network calls, and USD `0.00` paid cost. Its rows remain
product-level known-link recovery measurements. The G6 addition explicitly
states that repeated company rows are not independent samples and that the
result does not establish semantic relevance, stable generalization,
statistical significance, clinical suitability, FTO, validity, investment
merit, or publication readiness.

## Verification

The focused G6 test passed `2/2`; the adjacent report, analysis, and M20
holdout tests passed `8/8`; targeted compilation and `git diff --check` passed.
The implementation commit is `aaecb92`. Artifact hashes and exact commands are
in `verification.json`.

## Not run

No new data acquisition, semantic adjudication, provider dispatch, paid
inference, public release, user/commercial study, clinical/FTO review, or
pooled final inference was run.
