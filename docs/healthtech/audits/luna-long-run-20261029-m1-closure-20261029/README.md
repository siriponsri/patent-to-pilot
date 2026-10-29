# HT M1 closure audit

- Run ID: `luna-long-run-20261029-m1-closure-20261029`
- Date: `2026-10-29`
- Tested source commit: `82e2bd5258eba5da0f582d9e2c2ab75f9abca645`
- Verdict: `PASS_ENGINEERING`
- Scope: current-head closure probes for F1 restricted export leakage, F2 frozen Abbott runtime integrity, and F3 typed-rights resolution.
- Tree state: unrelated owner changes were present and preserved; only the scoped audit, progress pointer, and next-actions entry belong to this package.

## Result

The fresh offline reproduction passes all three M1 boundaries.

- F1: Markdown, redistribution JSON, and product-display source view exclude restricted nested and encoded evidence values. Reviewed structured evidence is rebuilt from the source payload; quote-only and unsupported nested evidence are omitted. Local research still retains the authored evidence.
- F2: Synthetic and real frozen Abbott copies reject a runtime patent-text mutation with `CohortIntegrityError: runtime JSON hash does not match manifest`. The real copy builds 3 cases with 41 patents each before mutation.
- F3: unknown, blank, mismatched, and ambiguous typed rights policies all return `PASS_WITH_UNRESOLVED_RIGHTS` with `UNRESOLVED_TYPED_POLICY` and no resolved policy IDs.

The historical portable probe was not edited. Its setup overwrites the valid synthetic manifest with a legacy two-field manifest, so the current adapter correctly stops at `manifest is missing the required runtime integrity format` before reaching its intended checks. This is recorded as a stale-probe diagnosis, not as a current-head defect.

## Verification

- Focused repair/pre-live suite: `46 passed`.
- Full repository suite with propagated `PYTHONPATH=src`: `346 passed`.
- Compile check: `rtk proxy python -m compileall -q src scripts tests` exited `0`.
- Fresh reproduction: `reproduction/reproduce_current_head.py` exited `0`; receipt is `reproduction-summary.json`.
- Network attempts: `0`; provider calls: `0`; neural model calls: `0`; paid cost: `$0.00`.

## Limits and next action

This is engineering evidence for source integrity, typed rights handling, and export boundaries. It does not establish semantic relevance, exhaustive recall, clinical suitability, FTO, patent validity, investment merit, publication readiness, live provider behavior, or public redistribution rights. Abbott, Boston, Stryker, and Cook remain development-only; Bridge and live/provider HT-B4 remain `BLOCKED_LOCAL`.

Next action is the existing offline research path: add sourced family mappings or a licensed relevance-judgment cohort with multiple independent groups and a predeclared final holdout. Do not spend against the paid branch from this receipt.

Machine-readable details are in [`verification.json`](verification.json), [`experiment-ledger.json`](experiment-ledger.json), and [`reproduction-summary.json`](reproduction-summary.json).
