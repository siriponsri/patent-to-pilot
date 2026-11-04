# Patent-to-Pilot current-candidate release verification R12

Status: `PARTIAL_NOT_COMPLETE_CURRENT_HEAD_OFFLINE_VERIFIED_PAID_BLOCKED`.

This checkpoint resumes the existing Patent-to-Pilot goal at the intentionally
dirty candidate `88dc40471cb9078f929c02bb893cfa1e364da841`. It records the
private full-suite receipt, preserves the E2 journal boundary, and keeps the
paid branch fail-closed. It is not a clean release, publication decision, or
scientific superiority result.

## Candidate and verification

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Worktree: intentionally dirty; owner, Claude, Luna, and research changes preserved.
- Private JUnit receipt: `C:/Users/User/AppData/Local/PatentToPilot/private-artifacts/ptp-current-candidate-full-tests-20261103-r2.xml`
- Private JUnit SHA-256: `1cfd796d5b55aeddc9ee6c7fedcdd836bcdbd147f0a94cc1d597f551472b187b`
- Full Python suite: `642 total; 640 passed; 0 failed; 0 errors; 2 skipped`.
- JUnit duration: `22.451` seconds; timestamp `2026-11-03T23:20:15.253857+07:00`.
- `compileall`: PASS from the current-head release verification.
- Scoped audit/JSON diff check: PASS. Repository-wide `git diff --check`
  still reports pre-existing trailing-whitespace/line-ending noise in the
  owner history file `memory/next-actions.md`; that file was not normalized.

The receipt is kept in private Windows storage and is referenced by hash only;
it is not copied into Git. The historical clean-release receipt remains
separate and is not pooled with this dirty candidate.

## Accounting and paid boundary

The canonical E2 journal was read back without mutation:

- SQLite integrity: `ok`.
- Operational attempts: `0`; pending/unknown: `0`.
- Preserved legacy settled receipts: `4`; known actual spend: `USD0.0001464`.
- Prospective allowance: `USD1`; unknown-history boundary:
  `UNKNOWN_OWNER_ACCEPTED_CUTOVER`.
- No zero ledger, budget reset, time-window reset, retry, reservation, or
  provider generation occurred.

The latest authorized metadata evidence still exposes only lifetime usage from
an ordinary non-management key. It does not provide the current scoped account
credit or remaining key limit required by the live v2 admission contract.
Previously observed public route pricing for `qwen/qwen3-32b` at DeepInfra
(`USD0.08/M` prompt and `USD0.28/M` completion) is not a credit grant and must
be refreshed inside the 300-second admission window before any dispatch.
Therefore paid dispatch remains `BLOCKED_BEFORE_RESERVATION` and no pending
call was retried.

## Goal status and resume

- Engineering: `COMPLETE_CURRENT_HEAD_OFFLINE_WITH_DIRTY_RELEASE_BOUNDARY`.
- Scientific evidence: `PARTIAL_DESCRIPTIVE_NOT_ESTIMABLE`.
- Business validation: `PARTIAL_SCENARIO_ONLY_EXTERNAL_NOT_RUN`.
- Manuscript: `PARTIAL_OWNER_REVIEW_AND_WPI_GUIDE_UNVERIFIED`.
- Paid API: `BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`.
- Goal: active and not closed.

Next action is owner review of the dirty candidate and, only if paid
comparison remains required, one non-secret scoped v2 credit/limit snapshot.
After that evidence exists, refresh exact-route pricing, validate the frozen
rights-cleared payload, and reserve no more than the existing `USD0.25` canary
through the same E2 journal. Continue offline research and manuscript work
without this evidence.
