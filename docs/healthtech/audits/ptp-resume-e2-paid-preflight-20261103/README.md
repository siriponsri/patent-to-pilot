# Patent-to-Pilot E2 resume paid preflight

Date: 3 November 2026 (Asia/Bangkok)

This checkpoint resumes the existing Patent-to-Pilot goal. It does not create a goal, reset the budget or time window, recreate the E2 journal, retry a pending call, or launch a new GPU job.

## Candidate and process boundary

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Worktree remains intentionally dirty; owner, Claude, Luna, and research changes were preserved.
- The existing SSH inspection process `18096` started at `18:36:54 ICT` and was left untouched. No new pytest, experiment, GPU, or provider job remained active after verification. See `process-check.json`.

## Bounded provider preflight

The owner-supplied Windows `.env` was read only through the repository helper. The API key was not printed, copied to the remote host, or persisted in this audit. The sanitized receipt is `metadata-observation.json`.

- `/api/v1/key`: HTTP 200.
- Lifetime usage: `USD0.0001464`; daily, weekly, and monthly usage: `USD0`.
- Key class: ordinary non-management.
- Current scoped credit: unavailable from this key.
- Remaining key limit: unavailable.
- Account scope: not reconciled.
- Therefore paid dispatch remains `BLOCKED_BEFORE_RESERVATION`.

A public route snapshot was also taken for `qwen/qwen3-32b`. The selected healthy route was DeepInfra at `USD0.08/M` prompt and `USD0.28/M` completion. The receipt is `public-route-pricing-observation.json`. This observation is not a credit grant and must be refreshed inside the runner's 300-second admission window before any future reservation.

## E2 journal readback

The canonical journal was opened read-only at `%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`; see `journal-readback.json`.

- SQLite integrity: `ok`.
- Operational attempts and contexts: `0` and `0`.
- Pending or unknown operational rows: `0`.
- Preserved legacy settled receipts: `4`, totaling `USD0.0001464`.
- History boundary: `UNKNOWN_OWNER_ACCEPTED_CUTOVER`.
- Prospective allowance: `USD1.00`.
- Account scope binding remains empty because no reservation has occurred.
- No legacy source, ledger, budget, or time-window reset occurred.

The uncertainty boundary is retained. The known legacy spend is not treated as complete history, and the prospective allowance is not evidence of provider credit.

## Release verification

The exact current dirty candidate passed the full Python suite: `642` total, `640` passed, `0` failed, `0` errors, and `2` documented skips. `compileall` passed. The raw JUnit receipt is `full-tests.xml`; its SHA-256 is recorded in `CHECKPOINT.json`.

`git diff --check` returned only the known line-ending and trailing-whitespace noise in the pre-existing `memory/next-actions.md` and line-ending warnings for existing edited files. This is recorded as a release hygiene issue, not converted into a source-test failure.

## Decision and next step

Status: `PARTIAL_PAID_BLOCKED_BEFORE_RESERVATION`.

No paid request, reservation, attempt ID, retry, ledger mutation, budget reset, GPU launch, or research-goal closure occurred. The single remaining paid prerequisite is a non-secret current scoped v2 credit/limit snapshot for the same account/key, or a sanctioned pointer to one. Once present, reconcile it against E2, refresh the exact route pricing immediately before dispatch, revalidate the frozen rights-cleared payload, and reserve at most the existing `USD0.25` canary. Until then, continue local/offline and manuscript work and keep research status descriptive rather than claiming paid comparison results.
