# Patent-to-Pilot E2 refresh checkpoint

Date: 3 November 2026 (Asia/Bangkok)

This checkpoint resumes the existing Patent-to-Pilot O1-O4 goal at candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. It does not create a goal, paid
epoch, zero ledger, retry, GPU job, or new time window.

## Candidate and verification

- Worktree: `patent-to-pilot-long-run-20261103`.
- Branch: `codex/patent-to-pilot-long-run-20261103`.
- The worktree remains intentionally dirty with owner/Claude/Luna and research
  changes. No reset, clean, stash, merge, commit, or push was performed.
- The existing SSH process (PID 18096, started 3 November 2026 at 18:36:54
  ICT) is the pre-existing inspection session and was left untouched.
- The focused regression ran 74 tests with 0 failures, 0 errors, and 0 skips.
  JUnit evidence is `focused-tests.xml`; its SHA-256 is recorded in
  `verification.json`.

## E2 accounting

The canonical Windows E2 journal was read-only inspected at
`%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`.
SQLite integrity is `ok`. The journal has zero new attempts and zero
pending/unknown rows. The owner-accepted unknown-history boundary remains
unchanged, and the four preserved legacy settled receipts total
`USD0.0001464`. The prospective allowance remains `USD1.00`; no new budget was
created, no history was rewritten, and no unknown call was retried.

## Current OpenRouter observation

The owner-supplied `.env` was used only through the bounded metadata helper;
the key was not printed or persisted. `/api/v1/key` returned HTTP 200 and
reported lifetime usage `USD0.0001464`, with daily/weekly/monthly usage `USD0`.
The key is ordinary non-management, so current scoped account credit and
remaining key limit were not available. This does not satisfy the paid
admission gate.

A fresh public route observation selected `DeepInfra` for `qwen/qwen3-32b` at
`USD0.08/M` prompt tokens and `USD0.28/M` completion tokens, with context
length `40960`, route status `0`, and uptime `100` in the observation. The
route receipt is public metadata only and cannot replace current account/key
credit. Before any future reservation, the exact route price must be refreshed
inside the runner's 300-second admission window.

Paid dispatch therefore remains `BLOCKED_BEFORE_RESERVATION`: 0 provider
calls, 0 reservations, 0 new attempt IDs, 0 retries, and 0 ledger mutations.

## Research and next action

The completed GPU encoder/retrieval artifacts and the prior local guided 3/3
generation artifact remain separate protocol evidence. This checkpoint does
not pool them into a final scientific result and does not claim adaptive
superiority, semantic patent gold, external business validation, revenue,
ROI, willingness-to-pay, or journal acceptance. The existing goal stays open.

Continue local/offline and manuscript work. If the paid comparison is still
needed, obtain one non-secret current scoped v2 credit/limit snapshot or a
sanctioned pointer, then rerun the live gates and reserve at most the USD0.25
canary through the same E2 journal. Do not retry pending calls, reset the
budget/window, rerun the completed GPU job, or close the research goal from
tests/canaries alone.
