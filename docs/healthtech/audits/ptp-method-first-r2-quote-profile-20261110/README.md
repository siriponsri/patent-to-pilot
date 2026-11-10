# Versioned exact-quote profile adapter
New quote-profile-v1 prompt/adapter replaces model-generated numeric offsets with deterministic unique exact substring alignment. V0 output cannot enter this path. Raw proposals remain unchanged; canonical profile and proposal digests are separate. Existing structural/source validation is reused after alignment. No fuzzy repair, occurrence guessing or old-output reclassification.

72 targeted tests passed in 0.92s; Ruff passed. Ten new cases cover Unicode, overlapping/repeated ambiguity, absent/case/whitespace variants, immutability, explicit version refusal, hidden-field/source binding and generation/prompt dispatch. Existing 62 regressions pass.

Change record: docs/healthtech/research/SACR_QUOTE_PROFILE_V1_CHANGE_RECORD_20261110_EN.md. Old v0 prompt and synthetic smoke script unchanged. No actual model run, no repair/retry of SYN-SACR-001, no benchmark data or GPU work. Exact quotations do not establish extraction fidelity.

Next separately declare and implement a bounded v1 synthetic check; actual R1 and semantic-review gates still open. Curator/environment response remains pending.
