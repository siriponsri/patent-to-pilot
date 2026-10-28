# HealthTech clean-checkout backend reproducibility audit

Date: 2026-10-29 (Asia/Bangkok)

Status: `PASS_ENGINEERING`; real ignored-corpus integration `NOT_RUN`

Tested base commit: `43ba0e7d637ed5ee1ae601b75addb947f4db48d0`

Implementation commit: `3177478c67f654f3f4d7c891e055a8ae72541162`

## Finding and repair

The clean-checkout baseline used:

`rtk python -B -m pytest -q -p no:cacheprovider tests/test_healthtech_repairs.py`

It failed with `s..........FF..FFF` because five tests depended on ignored
`results/healthtech` artifacts. The failures were fixture availability failures,
not backend contract failures.

This package replaces those dependencies with authored temporary fixtures for the
Abbott adapter, development protocol, typed/legacy provenance verifier, and the
negative uncovered-pair path. The fixture deliberately contains malformed
`manifest.json` and evaluator references; the adapter continues to ignore those
surfaces by contract and reads only runtime inputs, source registry rows, raw PMA
snapshots, and disclosure HTML.

The repair also closes a real rights-boundary defect. `SourceRights.displayable_fields`
is now enforced by `healthtech.history.source_view`: externally visible mapping
payloads are filtered to reviewed fields and an explicitly requested restricted
field raises `RightsBoundaryError`. Local research views retain the full local
payload.

## Verification

- Main-worktree focused repairs: `18 passed`; one existing `fitz` deprecation warning.
- Main-worktree scoped backend suite: `58 passed`; one existing `fitz` deprecation warning.
- Fresh clean-worktree focused repairs: `17 passed`, `1 skipped` because the pinned tokenizer is absent.
- Fresh clean-worktree scoped backend suite: `57 passed`, `1 skipped` for the same tokenizer condition.
- Compile checks: PASS for `src`, `tests`, and `scripts` in both worktrees.
- Fresh clean-worktree status: CLEAN; `results/healthtech` absent; model cache absent.
- `rtk git diff --check`: PASS.
- Provider calls, paid inference, network acquisition, deployment, Bridge, final
  holdout, and UI work: `NOT_RUN`.

The full scoped suite is reproducible from a clean checkout without ignored
`results/healthtech` data or the local model cache. The tokenizer regression
remains an expected skip when its pinned local tokenizer artifact is unavailable.

## Limits and next action

This is engineering and contract evidence only. It does not establish semantic
relevance, clinical suitability, regulatory approval, FTO, patent validity,
investment merit, publication readiness, or scientific generalization. The
authored fixtures are not real device results and do not replace the real local
cohort integration.

Next: keep this backend package bounded, preserve the audit pointer, and run a
separately authorized real-corpus integration only when the ignored cohort and
model-cache availability are explicitly in scope.

Machine-readable details are in `verification.json`; continuation notes are in
`NEXT_ACTIONS.md`.
