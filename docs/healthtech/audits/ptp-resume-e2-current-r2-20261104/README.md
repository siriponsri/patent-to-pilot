# Patent-to-Pilot E2 resume checkpoint r2

Recorded: 2026-11-03T17:24:49.7581370Z (2026-11-04 00:24:49 Asia/Bangkok)

## Candidate

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Working tree: intentionally dirty; pre-existing owner/Claude/Luna/research/audit changes were preserved.
- This checkpoint adds verification artifacts only. It does not claim a clean release, merge, or push.

## Engineering verification

- Full current-head test suite: **PASS** — 642 tests, 640 passed, 0 failed, 0 errors, 2 skipped.
- `python -m compileall -q src scripts tests`: **PASS**.
- Scoped `git diff --check` for source, scripts, tests, long-run docs, research docs, and memory: **PASS**; existing CRLF normalization warnings were left untouched.
- Raw test receipt: `current-head-full-tests.xml`.
- Test receipt SHA-256: `76f50be98675d334d74f8b15862fba548133522128d90b5b9696df9a2c9bbecc`.
- The test pass verifies the candidate's engineering behavior only. It is not evidence of paid inference, semantic gold, user validation, revenue, ROI, or publication acceptance.

## E2 accounting verification

Read-only inspection of the existing canonical journal found:

- SQLite `integrity_check`: `ok`.
- Canonical authorization: `PTP-HT-OR-E2-20261103-USD100`.
- New attempts: `0`.
- Pending or unknown attempts: `0`.
- Legacy settled receipts: `4`.
- Known legacy actual spend: `USD0.0001464`.
- History boundary: `UNKNOWN_OWNER_ACCEPTED_CUTOVER`.
- Prospective epoch allowance: `USD1`.
- No budget reset, no new zero ledger, no ledger mutation, and no 24-hour reset occurred in this checkpoint.

The ledger's absence of pending rows does not prove that the missing historical R1 record is complete. Legacy spend and the unknown history remain preserved.

## Paid admission

The latest sanitized metadata receipt remains `ptp-api-metadata-current-20261104-r1/metadata-observation.json`, observed on 2026-11-03T17:06:27.703893Z. It reports HTTP 200 for the ordinary key endpoint, but `account_scope_binding=NOT_RECONCILED`, current account credits were not available through that key, key limit/remaining limit were unavailable, and `live_admission_enabled=false`.

Therefore the paid path remains:

`BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`

No route refresh, reservation, provider call, retry, or cost was made in this checkpoint. The next paid action is permitted only after one non-secret current scoped credit/limit snapshot is supplied through an approved channel. Then the runner must refresh exact-route pricing inside the 300-second admission window, revalidate the rights-cleared input pack, reserve the existing `USD0.25` canary in E2, and dispatch exactly once. An unknown or pending call must never be replayed.

## Runtime checks

- Windows process inspection found no active experiment runner matching the local/API generation or dr-train experiment commands.
- The observed SSH process is the existing Codex app-server proxy, not evidence of a new dr-train job.
- The last stored dr-train preflight is historical and reports `UNKNOWN_NOT_GRANTED_RESOURCE_OBSERVATION_ONLY`; it is not treated as a current allocation grant.
- No new GPU job was launched. Existing fresh GPU retrieval results remain separate from local generation and any future paid API protocol.

## Status and handoff

- Engineering: **COMPLETE_CURRENT_HEAD_VERIFIED**.
- Paid API: **BLOCKED_BEFORE_RESERVATION** on current scoped credit/limit evidence.
- Scientific comparison: **PARTIAL**; existing retrieval diagnostic and local generation contract evidence remain descriptive and are not pooled across protocols.
- Business validation: **PARTIAL/PROXY_ONLY**; no independent users, revenue, ROI, or willingness-to-pay claim.
- Manuscript: **READY_FOR_OWNER_REVIEW**, with paid comparison and broader scientific evidence still pending.

Next action: obtain the one non-secret current credit/limit evidence item, or continue offline manuscript/protocol work without rechecking the same metadata endpoint. Do not read or transmit the key, retry a pending request, start another GPU job, or create another ledger.
