# OpenRouter metadata recheck R5 — 2026-11-03

Status: `PASS_READ_ONLY_METADATA_PAID_GATE_UNCHANGED`

The owner-supplied `.env` path was passed only to the existing bounded
metadata observer. The credential was not printed, copied, staged, or written
to the repository. This was a read-only key metadata observation; it did not
reserve budget, dispatch a model request, or mutate the ledger.

## Observed

- Key endpoint: HTTP 200.
- Lifetime usage: `USD0.0001464`.
- Daily, weekly, and monthly usage: `USD0`.
- Key class: ordinary non-management key.
- Account scope: not reconciled.
- Current scoped credit: unavailable through this key class.
- R1 history completeness: not proven.

Receipt: `metadata.json` in this directory.

## Decision

Paid OpenRouter remains `BLOCKED_BEFORE_RESERVATION`. The existing canonical
R1 journal/export and the current scoped credit evidence are still missing.
The previously known USD8 authorization is unchanged; no new budget approval,
zero ledger, budget reset, time-window reset, retry, or provider call was made.

## Next action

Obtain the two non-secret evidence items once, inspect the history export with
`scripts/healthtech/inspect_r1_history_export.py`, resolve the one canonical
registry/ledger, recheck route/pricing/rights/pending/writer state, and run one
small paired canary only if every live gate passes.
