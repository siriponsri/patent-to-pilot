# Patent-to-Pilot E2 current resume R3

Recorded: 2026-11-03T17:47:33.298991+00:00 (2026-11-04, Asia/Bangkok)

## Scope

This checkpoint resumes the existing Patent-to-Pilot goal. It does not create
a goal, reset a budget or time window, create a zero ledger, retry a pending
call, launch a new GPU job, or read the `.env` value into project artifacts.

## Candidate and release boundary

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Working tree: intentionally dirty; owner, Claude, Luna, research, and audit changes were preserved.
- Latest release verification remains `docs/healthtech/audits/ptp-release-verification-r12-20261103/`; it is an offline verification of a dirty candidate, not a clean release or merge.

## Current engineering verification

- Focused current-worktree selection: **35 passed, 0 failed, 0 errors, 0 skipped**.
- JUnit receipt: `focused-current-tests.xml` in this audit directory.
- JUnit SHA-256: `18130b276c91b1fe0a5489d0edf11b6b84ca62c35eea9dee838d7eaf91ae11bf`.
- `python -m compileall -q src scripts tests`: **PASS**.
- Scoped `git diff --check`: no new content defect; pre-existing line-ending warnings remain in owner-maintained documentation.
- The prior current-head full-suite receipt remains valid as historical evidence for this unchanged candidate: `642` total, `640` passed, `0` failed, `0` errors, `2` skipped. This checkpoint does not relabel the focused selection as a full-suite result.

The checks cover API generation/history preservation, fail-closed credit and
ledger behavior, local execution guards, current-head frontier binding, and
O3 generation repair. They are engineering evidence only; they do not prove
paid inference, semantic gold, user validation, adaptive superiority, or
publication acceptance.

## E2 accounting read-back

The canonical Windows journal was read in SQLite read-only mode:

- Path: `%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`
- `PRAGMA integrity_check`: `ok`
- Authorization: `PTP-HT-OR-E2-20261103-USD100`
- Operational attempts: `0`
- Pending or unknown operational rows: `0`
- Preserved legacy settled receipts: `4`
- Known legacy actual debit: `USD0.0001464`
- History boundary: `UNKNOWN_OWNER_ACCEPTED_CUTOVER`
- Prospective E2 allowance: `USD1.00`

No journal mutation, ledger replacement, budget reset, time-window reset, or
historical cost inference occurred. The missing historical R1 boundary remains
unknown; zero operational rows do not prove that the historical record is
complete.

## Paid admission

The latest sanitized metadata receipt remains
`%LOCALAPPDATA%/PatentToPilot/healthtech/private-artifacts/ptp-api-metadata-current-20261104-r1/metadata-observation.json`.
It records HTTP 200 for the ordinary non-management key endpoint, lifetime
usage `USD0.0001464`, and no account-scoped credit or remaining key limit.
The key value was not printed, copied, or persisted in this checkpoint.

Paid status remains:

`BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`

No route-price refresh, reservation, provider call, retry, or cost was made in
this checkpoint. A previously observed public route price is not reused as a
live admission quote. If paid comparison remains required, the next sequence
is exactly once after one non-secret current scoped credit/limit snapshot is
available: reconcile to E2, refresh exact-route pricing inside the runner's
300-second window, revalidate the rights-cleared pack, reserve no more than the
existing `USD0.25` canary, then dispatch once. Never replay an unknown or
pending call.

## Completed GPU evidence kept separate

The completed V100 diagnostic remains a separate retrieval protocol and was not
rerun here. It is bound to the same candidate HEAD and stored in
`docs/healthtech/audits/ptp-fresh-gpu-device-diagnostic-20261103/`.

| Method | Hits / 61 | Macro Recall@20 | Micro Recall@20 | Macro nDCG@20 |
|---|---:|---:|---:|---:|
| Frozen-query BM25 | 21 | 0.392685 | 0.344262 | 0.430022 |
| PatEmbed dense | 24 | 0.430073 | 0.393443 | 0.409533 |
| multilingual E5 dense | 27 | 0.481021 | 0.442623 | 0.455981 |

The saved-vector independent recheck reported maximum absolute metric delta
`0.0` at tolerance `1e-12`. This is a three-device development diagnostic;
unlisted pairs remain unjudged, the two repeated query texts are not independent
queries, and the result is not semantic gold, a final holdout, or an adaptive
superiority claim. It is not pooled with local Qwen generation or a future paid
API comparison.

## Current goal status

- Engineering: `COMPLETE_CURRENT_HEAD_OFFLINE_WITH_DIRTY_RELEASE_BOUNDARY`
- Scientific evidence: `PARTIAL_DESCRIPTIVE_NOT_ESTIMABLE`
- Business validation: `PARTIAL_SCENARIO_ONLY_EXTERNAL_NOT_RUN`
- Manuscript: `READY_FOR_OWNER_REVIEW`
- Paid API: `BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`
- Goal: `ACTIVE_NOT_COMPLETE_NOT_BLOCKED`

The next safe action is either continued offline reproducibility/owner-review
work or one approved non-secret current scoped credit/limit snapshot. Do not
mark the research goal complete from the current tests, canary, or GPU
diagnostic alone.

