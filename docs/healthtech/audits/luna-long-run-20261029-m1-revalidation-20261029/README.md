# HT M1 current-head revalidation

- Run ID: `luna-long-run-20261029-m1-revalidation-20261029`
- Tested implementation commit: `00bca8edf3baedb2212085d4bda091f780c7ecb4`
- Parent implementation commit: `759b93726f25e0ace0e267a4ab7c4938ecb8ba3c`
- Verdict: `PASS_ENGINEERING`
- Scope: current-head regression closure for F1/F2/F3 and corrected portable reproduction

This package closes the remaining M1 evidence gap. The regression suite now injects
tampered structured and literal evidence at the export boundary, verifies that
reviewed structured evidence is rebuilt from the source payload, and exercises a
runtime patent-text mutation through the real Abbott adapter path.

The portable probe uses authored synthetic data and a local copy of the frozen
2026-10-29 Abbott development cohort. It copies every path declared by
`manifest.json["raw_files"]`, never copies evaluator relations into runtime inputs,
and writes only hashes/counts to the audit record. The baseline adapter build
completed for 3 cases with 41 patents each; the mutated runtime was rejected with
`CohortIntegrityError: runtime JSON hash does not match manifest`.

## Verification

- `tests/test_healthtech_repairs.py`: 29 tests collected and passed.
- `tests/test_healthtech_prelive.py`: 13 tests collected and passed.
- Exact-head detached worktree rerun: exit code `0`.
- `python -m compileall -q src scripts tests`: exit code `0`.
- Provider calls: `0`; neural model calls: `0`; paid cost: `$0`.
- Network guard: no attempts observed in the reproduction probe.

Machine-readable details are in [`verification.json`](verification.json).
The sanitized probe receipt is [`reproduction-summary.json`](reproduction-summary.json).
The portable script is under [`reproduction/`](reproduction/).

## Limits

This is engineering evidence for source integrity and rights-aware export behavior.
It does not establish semantic relevance, clinical suitability, FTO, patent validity,
investment merit, exhaustive recall, generalization, publication readiness, or live
provider behavior. Abbott and Boston remain development-only cohorts. The Bridge
branch remains `BLOCKED_LOCAL`, and the paid/provider branch remains `BLOCKED_LOCAL`.

## Next action

Proceed to the next bounded offline package: freeze HT-T2 prediction/denominator
rules only if predictions exist, then expand to a rights-cleared cohort with
multiple independent company/family groups and a predeclared final holdout.
