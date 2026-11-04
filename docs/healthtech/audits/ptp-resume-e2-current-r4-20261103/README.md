# Patent-to-Pilot E2 current resume R4

Date: 3 November 2026 (Asia/Bangkok)

This checkpoint resumes the existing Patent-to-Pilot goal. It does not create
a goal, reset the budget or time window, create a zero ledger, retry a pending
call, or launch a new GPU job.

## Candidate and release boundary

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- The worktree remains intentionally dirty. Existing owner, Claude, Luna,
  research, and audit changes were preserved.
- The completed V100 encoder/retrieval result remains a separate private
  protocol artifact. No new dr-train job was started in this checkpoint.

## E2 accounting read-back

The canonical Windows journal is
`%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`.

- SQLite integrity: `ok`.
- Operational attempts: `0`.
- Pending/unknown operational rows: `0`.
- Preserved legacy settled receipts: `4`.
- Known legacy actual debit: `USD0.0001464`.
- History boundary: `UNKNOWN_OWNER_ACCEPTED_CUTOVER`.
- Prospective E2 allowance: `USD1.00`.
- No reservation, retry, provider call, zero ledger, budget reset, or window
  reset occurred.

The ledger remains append-only and retains the uncertainty around missing R1
history. The prospective allowance is not a claim that historical spending is
complete and is not a new USD100 budget.

## Current credit observation

A bounded read-only observation was made through the existing project loader
using the owner-provided local `.env`. The key value was not printed, copied,
or persisted. Private receipt:

`%LOCALAPPDATA%/PatentToPilot/healthtech/private-artifacts/ptp-api-metadata-current-20261103-r4/metadata-observation.json`

Receipt SHA-256:
`2fff99680085ab092272039759f785b88304a2adb82dc12e04322ad23d2e1714`.

The provider returned HTTP 200. The observation reports an ordinary
non-management key, lifetime usage `USD0.0001464`, and no `limit` or
`limit_remaining`. Account-scoped credit was not available through this key,
so live admission remains disabled. This observation is not a complete R1
history export and is not billing authority.

## Engineering verification

The full current-candidate suite was run after the metadata observation:

- `642` tests total.
- `640` passed, `0` failed, `0` errors, `2` skipped.
- `compileall` passed.
- Private JUnit receipt:
  `%LOCALAPPDATA%/PatentToPilot/healthtech/private-artifacts/ptp-resume-e2-current-r4-20261103/full-tests.xml`
- JUnit SHA-256:
  `550c191222cc249730bc27ee4132011a31be7807bbb15f37000831af884e17c4`.

This is engineering evidence for the current dirty candidate only. It does not
upgrade the scientific study, the local Qwen schema canary, or the manuscript
to complete status.

## Paid branch disposition

Paid dispatch remains:
`BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`.

The previously observed route price is not reused for admission. If the owner
supplies one non-secret current scoped credit/limit snapshot, the next live
sequence is exactly once: reconcile it to E2, refresh exact route pricing
inside the runner's 300-second window, revalidate the rights-cleared pack,
and reserve no more than the existing `USD0.25` canary within the prospective
`USD1` allowance. Unknown or pending calls must not be replayed.

## Current statuses

- Engineering: `COMPLETE_CURRENT_HEAD_OFFLINE_WITH_DIRTY_RELEASE_BOUNDARY`.
- Scientific evidence: `PARTIAL_DESCRIPTIVE_NOT_ESTIMABLE`.
- Business validation: `PARTIAL_SCENARIO_ONLY_EXTERNAL_NOT_RUN`.
- Manuscript: `PARTIAL_OWNER_REVIEW_WPI_GUIDE_UNVERIFIED`.
- Paid API: `BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`.
- Goal: remains open.

