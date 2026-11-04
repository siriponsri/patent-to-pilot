# Patent-to-Pilot E2 resume checkpoint r10 — 4 November 2026

This checkpoint resumes the existing Patent-to-Pilot goal. It does not create a
new goal, reset the budget, replay a pending request, or replace the canonical
E2 journal.

## Candidate and runtime state

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Worktree remains dirty with owner/Claude/Luna/research/audit changes preserved.
- No active project, `dr-train`, OpenRouter, or duplicate baseline process was found.
- The latest failure-accounting patch release `323bcc5` was inspected. Its four
  regression tests remain present and pass; no patch was reapplied.
- The candidate is not a clean release: this checkpoint binds evidence to the
  recorded HEAD plus the dirty-file boundary.

## Canonical E2 accounting

The read-only SQLite check resolved the single canonical journal at
`%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`.

- SQLite integrity: `ok`.
- Ledger binding: one canonical `PTP-HT-OR-E2-20261103-USD100` ledger.
- Legacy settled receipts: 4; known historical actual: `USD0.0001464`.
- New operational attempts: 0; pending/unknown attempts: 0.
- Prospective allowance: `USD1.00`.
- Historical completeness: `UNKNOWN_OWNER_ACCEPTED_CUTOVER`.
- No reservation, provider call, retry, ledger mutation, zero ledger, budget
  reset, or time-window reset occurred in this checkpoint.

The legacy receipts and unknown history remain preserved. The budget journal is
not evidence of current provider credit.

## Current paid preflight

The owner-supplied local `.env` was consumed only by the bounded metadata
observer; the key value was not printed or persisted. The fresh observation is
stored privately at:

`C:/Users/User/AppData/Local/PatentToPilot/healthtech/private-artifacts/ptp-resume-e2-current-r10-20261104/metadata-observation.json`

Observed result:

- `/api/v1/key`: HTTP 200.
- Key class: ordinary non-management key.
- Lifetime usage: `USD0.0001464`; daily, weekly, and monthly usage: `USD0`.
- Account credit / remaining key limit: unavailable through this key class.
- Live admission: disabled before reservation.

The exact public route was refreshed separately at
`.../public-route-observation.json` and bound into
`.../model-snapshot.json`:

- Model: `qwen/qwen3-32b`.
- Active route: `DeepInfra`, `deepinfra/fp8`.
- Prompt price: `USD0.08/M`.
- Completion price: `USD0.28/M`.
- Route status: active (`0`).
- Snapshot time: `2026-11-03T20:49:19.3317048Z`.

The route price is current enough for a five-minute admission window when a
valid scoped credit/limit snapshot becomes available. The paid branch remains
`BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`; no API request
was sent.

## Local and GPU evidence

The completed local Qwen run was reused, not rerun:

- Artifact: `%LOCALAPPDATA%/PatentToPilot/healthtech/private-artifacts/ptp-local-qwen-patent-run-20261104-r1/generation-receipt-guided.json`.
- `Qwen/Qwen3-8B`, revision `b968826d9c46dd6066d109eabc6255188de91218`.
- Frozen 3-case FDA factual pack: 3/3 schema-valid outputs.
- Provider calls: 0; paid cost: `USD0.00`.
- This is an FDA factual canary and not the device-patent study result.

The completed V100 run was also reused under the original protocol:

- GPU: `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`, concurrency 1.
- Candidate source hashes match the receipt for `local_execution.py` and
  `transformer_encoders.py`.
- Provider calls: 0; paid cost: `USD0.00`; lock released: true.
- Saved-vector independent verification already reports exact metric
  agreement at tolerance `1e-12`; no new GPU scoring was launched.
- Development diagnostic over 3 queries / 61 known links:
  - BM25: macro Recall@20 `0.392685`, micro `0.344262`, macro nDCG@20 `0.430022`.
  - PatEmbed: macro Recall@20 `0.430073`, micro `0.393443`, macro nDCG@20 `0.409533`.
  - multilingual-e5: macro Recall@20 `0.481021`, micro `0.442623`, macro nDCG@20 `0.455981`.

These values remain descriptive, development-only, and not evidence of causal
adaptive superiority, semantic gold quality, or final-holdout generalization.

## Verification performed

- Fresh API dry-run with the current route snapshot: `DRY_RUN_NOT_EXECUTED`,
  manifest unchanged, provider calls `0`.
- API/provider/history/security-focused tests: `84 passed`.
- Failure-accounting regression tests from `323bcc5`: `4 passed`.
- `python -m compileall -q src scripts tests`: pass.

One independent GPU verifier invocation was attempted with the wrong reference
file (`input-source-manifest.json`). It failed before writing output because
the evaluator hash did not match; no existing receipt was modified. The prior
private `independent-fresh-verification.json` remains the valid verification
artifact and is the result reported above.

## Status and continuation

- Engineering: `COMPLETE_CURRENT_HEAD_WITH_DIRTY_RELEASE_BOUNDARY`.
- Scientific evidence: `PARTIAL_DESCRIPTIVE_NOT_ESTIMABLE`.
- Business validation: `PARTIAL_OPERATIONAL_POTENTIAL_ONLY`; no external user,
  revenue, ROI, willingness-to-pay, or independent validation claim.
- Manuscript: `READY_FOR_OWNER_REVIEW_NOT_SUBMITTED`; WPI journal-specific
  Guide/Aims remains unverified.
- Paid API: `BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`.
- Overall goal: `ACTIVE_NOT_COMPLETE_NOT_BLOCKED`.

The shortest next action for the paid branch is one sanitized current
account-credit and remaining-key-limit observation from an authorized channel,
without sending a secret. Once present, reconcile it to E2, refresh the exact
route price inside the five-minute window, reserve only the existing `$0.25`
canary, and keep all outputs in a new private Windows directory. Until then,
continue offline/manuscript work and do not close the research goal from tests
or canary results alone.

