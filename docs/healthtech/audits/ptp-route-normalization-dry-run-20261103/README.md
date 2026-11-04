# Route normalization and parallel-path checkpoint — 2026-11-03

This package continues the existing Patent-to-Pilot O1–O4 goal. It does not
open a new goal, create a budget ledger, reset a budget/window, or dispatch a
paid provider request.

## Scope

- Restore the local execution guard that was present in the earlier worktree
  but absent from the current worktree.
- Add the shared local GPU slot and receipt-preservation regressions.
- Normalize route spelling only at the rights-cleared payload boundary so
  `deepinfra` and `DeepInfra` bind to the same exact route identity without
  adding aliases, fallback routing, or auto-routing.
- Re-run the real owner-private FDA-only pack in API `dry-run` mode.

## Outcome

`PASS_PAYLOAD_DRY_RUN_API_DISPATCH_BLOCKED_LEDGER_CREDIT`

The rights-cleared payload now validates all three frozen cases. The sanitized
manifest records the canonical route `deepinfra`; the model/pricing snapshot
still reports the provider route as `DeepInfra`. The runner stopped before any
transport dispatch and reported `DRY_RUN_NOT_EXECUTED` with zero provider calls
and zero paid cost.

The live API branch remains closed because the canonical R1 registry/journal is
not present in the current user profile and a current authorized credit
snapshot was not available. No replacement registry or zero ledger was made.

## Local path

`local_execution.py` and its regression test were added from the earlier
worktree's guard delta only. The current local generation runner now checks the
approved GPU UUID and authorization end time, holds a nonblocking OS slot,
rechecks the output path after lock acquisition, records message hashes and
timestamps, and opens receipts without overwrite. A new model inference was
not started: no current model root was available in the permitted task pack,
and the previously observed remote allocation remained unknown.

## Verification

- Focused local/payload suite: `26 passed, 0 failed, 0 skipped`.
- Full Python suite on this worktree: `611 passed, 0 failed, 0 errors, 1 skipped`.
- `compileall`: pass.
- `git diff --check`: pass.
- Active experiment processes: none observed.
- API calls: `0`.
- GPU jobs: `0`.
- Dataset downloads: `0`.
- Ledger mutations: `0`.
- Budget reset: `false`.
- 24-hour window reset: `false`.

Machine-readable details are in `verification.json` and `CHECKPOINT.json`.
The raw pack, exact messages, generated outputs, and credentials remain
outside Git in the owner-private artifact store.

## Required owner evidence before a live canary

Provide once, through an authorized local channel, either the exact existing
canonical R1 journal location or a sanitized all-attempt export that can be
reviewed and bound without creating a replacement, plus a current sanitized
account-credit/billing snapshot if the approved integration cannot provide it.
Do not send a key or secret. Existing historical debit evidence remains
`USD 0.0001464`; it is not a substitute for the canonical journal or current
credit gate.
