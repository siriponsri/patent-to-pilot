# HT-M29 current-head backend integration contract refresh

- Run ID: `luna-long-run-20261030-integration-contract-refresh-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Parent contract: `docs/healthtech/integration/luna-g3-20261028-28dfb1d/adapter-contract.json`
- Parent contract head: `b26f9138d2c36e36195755162c092088f23e9be4`
- Candidate code commit: `8f2e0fe1c913ab3acc78869c82bd6f729e01b596`
- Status: `PASS_CURRENT_HEAD_BACKEND_CONTRACT_UI_PENDING`

## Purpose

Refresh the backend integration contract after detecting that the historical
G3 handoff no longer matched the current HealthTech backend. The historical
contract remains unchanged. The new contract is generated from it, binds the
current code head and backend source hashes, and verifies the existing
sanitized fixture hashes before writing.

## Drift found

- The historical contract pointed to `b26f913`, while the current head before
  this package was `4a1ec5b`.
- All six recorded backend source hashes had drifted.
- All three sanitized fixture hashes still matched.
- The paused Claude UX/UI worktree was not read or modified.

## Implementation

Added `scripts/healthtech/refresh_integration_contract.py`. It fails closed on
missing or unsafe paths, malformed hashes, fixture drift, invalid Git heads,
and attempts to overwrite an existing output. It creates a new contract rather
than mutating the historical handoff. Four focused tests cover refresh,
fixture-drift rejection, overwrite rejection, and path-escape rejection.

## Current artifact

The refreshed contract is:

`docs/healthtech/integration/luna-g3-current-head-20261030-8f2e0fe/adapter-contract.json`

Its SHA-256 is
`a199bf3bb71b82e3f55629af1c278b580c339131543a06790c549dd87e974fb9`.

## Verification

- Contract refresh tests: `4 passed`.
- Backend, repair, dossier, and pilot-task regressions: `82 passed, 1 warning`.
- CLI refresh: `6` backend hashes recomputed and `3` fixture hashes verified.
- JSON parsing and `git diff --check`: `PASS`.
- Provider calls, network acquisition, credentials, and paid cost: `0`.

## Limits

This refresh makes the backend handoff current; it does not implement or merge
the paused UI, create an HTTP service, validate browser behavior, run a live
provider, acquire semantic judgment labels, or establish clinical/FTO,
commercial, or publication readiness.
