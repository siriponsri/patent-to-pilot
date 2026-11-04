# Patent-to-Pilot current credit and route recheck

Date: 2026-11-03 (Asia/Bangkok)

## Scope

This checkpoint resumes the existing Patent-to-Pilot goal. It performs a bounded, read-only paid preflight on the current dirty candidate. It does not create a new goal, epoch, budget, zero ledger, retry a pending call, or dispatch a paid request.

Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`

Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`

The worktree is intentionally dirty with owner/Claude/Luna and research changes. No reset, clean, stash, merge, commit, push, or unrelated-file cleanup was performed.

## Accounting evidence

The existing local E2 journal was inspected read-only at `%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`.

- `PRAGMA integrity_check`: `ok`.
- Authorization: `PTP-HT-OR-E2-20261103-USD100`.
- Ledger: `ptp-healthtech-openrouter-local-e2-20261103`.
- Canonical journal attempts: `0`.
- Canonical journal pending/unknown rows: `0`.
- Legacy imported receipts: `4` settled calls, `USD0.0001464` actual debit.
- History completeness: `UNKNOWN_OWNER_ACCEPTED_CUTOVER`.
- Prospective allowance: `USD1.00` only, with no new USD100 budget.
- Epoch duplication or zero-ledger creation: not observed.
- Legacy source journals remain unchanged.

The uncertainty buffer is not treated as measured credit or proof of complete historical coverage. The original legacy spend and unresolved-history boundary remain preserved.

## Current provider observation

The owner-authorized local `.env` was read only through `scripts/healthtech/collect_openrouter_metadata.py`. The sanitized receipt is `metadata-observation.json`.

- `/api/v1/key`: HTTP 200.
- Lifetime usage: `USD0.0001464`.
- Daily/weekly/monthly usage: `USD0`.
- Key type: ordinary non-management key.
- `limit_remaining`: unavailable.
- Account scope: not reconciled.
- Account credit snapshot: not requested/available for this key.
- Live admission: disabled.

This does not satisfy the current scoped v2 credit/limit gate. No key material was printed or persisted in this audit.

## Fresh route pricing observation

The public OpenRouter endpoint snapshot is `public-route-pricing-observation.json`, observed at `2026-11-03T13:18:15.745843Z`.

- Model: `qwen/qwen3-32b`.
- Route: `DeepInfra`.
- Prompt price: `0.00000008` USD/token (`USD0.08/M`).
- Completion price: `0.00000028` USD/token (`USD0.28/M`).
- Context length: `40960`.
- Route status: available in the snapshot (`status=0`, `uptime_last_30m=100`).
- Response hash: `f73b3e462edb46daa667dcf532194f885b64564e35d48f131d6973e635681314`.

This is a current public route observation, not a signed provider quote or a substitute for a fresh observation inside the runner's 300-second admission window. The route must be refreshed immediately before any future reservation.

## Engineering verification

The current-source hashes for the E2/provider/API files in the handoff match exactly. The corrected focused command passed `79` tests with `0` failures, `0` errors, and `0` skips. Receipt: `focused-tests.xml`; SHA-256 `07d7f1f2dcff7527f9c5e9ba031fd2390a5a39f79aef714441c7f64cef64548d`.

The tests cover journal preservation and replay blocking, credit binding, route-price ceilings, rights-cleared payload boundaries, API/environment fail-closed behavior, HTTP history/export lifecycle, local execution locks, and current-head frontier helpers. This is engineering evidence only; it is not a paid model result or a scientific superiority claim.

## Gate result

`PARTIAL_PAID_BLOCKED_BEFORE_RESERVATION`

Journal integrity and source binding pass. Fresh route pricing is observed but must be refreshed at dispatch. Current account/key credit and limit evidence remain unavailable, so no reservation, provider call, attempt, retry, or ledger mutation was made.

## Next action

Owner input is needed once, only if paid comparison is required: provide a non-secret current scoped v2 credit/limit snapshot for the same account/key, or point to an existing sanctioned snapshot. Do not send the API key. After reconciliation, refresh the exact route pricing, verify the rights-cleared frozen payload, and reserve at most the USD0.25 canary phase through the same E2 journal. If the evidence is not available, continue local/offline research and manuscript work without closing the goal.

