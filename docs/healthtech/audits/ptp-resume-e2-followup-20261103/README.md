# Patent-to-Pilot E2 follow-up checkpoint

Date: 3 November 2026 (Asia/Bangkok)

This checkpoint resumes the existing Patent-to-Pilot O1-O4 goal. It records a
read-only E2/accounting verification and an offline regression rerun on the
dirty candidate. It does not create a goal, budget, ledger, reservation,
provider attempt, retry, GPU job, or time window.

## Candidate and process boundary

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Worktree: intentionally dirty; existing owner/Claude/Luna/research work is preserved.
- Existing SSH inspection PID `18096` started at `2026-11-03 18:36:54 ICT` and was left untouched.
- No active local generation or GPU process was launched by this checkpoint.

## Offline verification

The selected current-head regression suite ran against the existing working
tree source. It covered API-generation gates, rights-cleared payloads, HTTP
history/export, E2 history migration, local execution guards, vector-bundle
verification, and O3 repair tests.

- Tests: `104 passed, 0 failed, 0 errors, 0 skipped`
- JUnit: `focused-tests.xml`
- JUnit SHA-256: `fdaa2094bfee3aa977e45de43cc96eb86b74a441ef6e30f1ac310eef2d0a4d09`
- `compileall`: PASS
- `git diff --check`: PASS; only pre-existing CRLF warnings were reported.

This is engineering evidence for the current dirty candidate. It is not a
paid model result, an adaptive-superiority result, a user study, or a release
commit.

## E2 journal readback

The canonical Windows journal was opened read-only at
`%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`.

- SQLite integrity: `ok`
- Authorization: `PTP-HT-OR-E2-20261103-USD100`
- Ledger: `ptp-healthtech-openrouter-local-e2-20261103`
- Operational attempts: `0`
- Attempt contexts: `0`
- Pending/unknown attempts: `0`
- Legacy settled receipts: `4`
- Preserved legacy actual: `USD0.0001464` (`146400` nano-USD)
- History boundary: `UNKNOWN_OWNER_ACCEPTED_CUTOVER`
- Prospective allowance: `USD1.00`
- Pre-reservation account/key scope binding: empty, as expected before a reservation

No legacy spend was rewritten, no zero ledger was created, no pending or
unknown call was retried, and no budget or time window was reset.

## Paid branch

The latest sanctioned metadata observation remains insufficient for admission:
the ordinary key reports usage but not a current scoped credit or remaining
limit for the same account/key. Public route pricing has been observed for
`qwen/qwen3-32b` through `DeepInfra` at `USD0.08/M` prompt and `USD0.28/M`
completion tokens, but the runner must refresh that route inside its 300-second
admission window after a valid current-credit snapshot exists.

Paid status remains `BLOCKED_BEFORE_RESERVATION`: zero provider calls, zero
reservations, zero new attempt IDs, zero retries, and zero ledger mutations.
The next owner input, if the paid comparison is still required, is one
non-secret current scoped v2 credit/limit snapshot or a sanctioned pointer for
the same account/key. The API key itself is not requested again.

## Research boundary and next action

The completed dr-train GPU artifacts, local guided Qwen3-8B result, three-case
PatEmbed dossier binding, and historical diagnostics remain separate protocol
evidence. They are not pooled into a final adaptive claim. The goal remains
open: engineering is current-head PASS, research is descriptive/PARTIAL,
external business validation is not run for the solo project, and the
manuscript remains draft/owner-review pending.

Continue owner review and offline manuscript/release preparation. If credit
evidence is supplied, refresh route pricing, recheck the frozen rights-cleared
payload, and reserve at most the existing `USD0.25` canary through E2. Do not
retry pending calls, rerun completed GPU work, reset accounting, or close the
research goal from tests/canaries alone.
