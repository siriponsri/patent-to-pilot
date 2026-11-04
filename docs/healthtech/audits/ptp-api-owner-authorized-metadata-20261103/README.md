# Owner-authorized OpenRouter metadata refresh — 2026-11-03

This package records a bounded, read-only metadata observation for the
existing Patent-to-Pilot O1–O4 goal. The owner authorized continuing the
OpenRouter branch in parallel only if every existing paid gate is ready. The
observation used the owner-supplied `.env` path through the approved metadata
helper; the credential value was not printed, copied, staged, or persisted.

## Result

The key endpoint returned HTTP `200`. The observed lifetime usage remains
`USD0.0001464`; daily, weekly, and monthly usage are `USD0`. The key is an
ordinary non-management key, so the helper could not obtain a scoped v2
account/key credit snapshot. Account scope remains unreconciled and history
completeness remains unproven.

The paid branch therefore remains `BLOCKED_BEFORE_RESERVATION`. The current
rights-cleared three-case pack and current route/price preflight remain valid,
but they do not replace the missing existing canonical R1 journal/export and
current scoped credit evidence. No provider call, reservation, attempt, retry,
ledger mutation, zero ledger, budget reset, or time-window reset occurred.

## Verification

- Candidate: `88dc40471cb9078f929c02bb893cfa1e364da841`.
- Metadata receipt: `metadata-observation.json`.
- Metadata file SHA-256:
  `b514bcbe94be8103c4b2da7afc3d2157b32cb1e42e3e1ce012b090b1bc078f02`.
- Focused O3/provenance/local-contract tests: `58 passed, 0 failed, 0 errors, 0 skipped`.
- Full Python suite: `616 total; 615 passed, 1 skipped, 0 failed, 0 errors`.
- `compileall`: PASS.
- JSON readback: PASS.

Raw JUnit receipts are retained as `focused-tests.xml` (SHA-256
`b1e3e3a16a5299e0325754e2f86a76169574d3803a84597d0c44cb6562cb5c12`) and
`full-tests.xml` (SHA-256
`3e56a5f88e1d4eca890b01ea5f24422dc07619a7959c2cc264fe24a8508c7a24`).

The known skip is the existing pinned local tokenizer artifact limitation. It
does not change the paid gate decision.

## Next action

Continue local/offline and manuscript work. If the owner supplies the existing
canonical R1 journal or sanctioned sanitized all-attempt export and a current
scoped credit snapshot through an approved channel, bind/reconcile them once,
recheck route, price, rights, writer quiescence, and pending attempts, and run
one small paired canary only if every gate passes. Do not ask again for the
original budget approval or the API key.
