# HT-M28 OpenRouter R1 offline readiness revalidation

- Run ID: `luna-long-run-20261030-openrouter-r1-readiness-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Parent audit: `luna-long-run-20261029-m4-r1-4c863d0`
- Source head at start: `e71ab26689b2a93da5b20a052aeeefe9df582363`
- Candidate commit: `74d6b7e` (`test: propagate source path to budget workers`)
- Status: `PASS_OFFLINE_R1_READINESS_LIVE_BLOCKED`

## Purpose

Revalidate the versioned HealthTech OpenRouter Round-1 policy, shared durable
budget boundary, provider regressions, and offline dispatcher behavior at the
current code head. This package does not open credentials, refresh current
provider metadata, send live requests, inspect account balance, or claim a
scientific HT-B4 result.

## Result

- The R1 policy seam remains versioned at
  `ptp-ht-openrouter-r1-20261028-usd8-v1` with authorization
  `PTP-HT-OR-R1-20261028-USD8`.
- The configured envelope remains `$8.00` total with a `$7.00` admission
  threshold, phase caps of `$0.40` canary, `$5.40` paired pilot, and `$1.20`
  robustness, one concurrent dispatcher, zero automatic retries, and unknown
  billing blocking further dispatch.
- The focused provider/R1 regression suite passes `122` tests. The complete
  repository suite passes `433` tests with one existing `fitz` deprecation
  warning.
- Offline dispatcher smoke, pilot continuation, and resume all complete using
  the mock transport. Resume does not duplicate completed jobs.
- An unapproved live invocation returns `BLOCKED` before transport creation.
  No credential was read, no provider request was sent, and paid cost remains
  `USD 0.00`.

## Implementation change

The cross-process budget tests now propagate the repository `src` directory to
their child interpreter through `PYTHONPATH`. `pyproject.toml` already adds
`src` to the pytest parent interpreter, but that setting is not inherited by
the worker subprocess. The repair is test-harness-only and preserves the
production provider and accounting code.

## Evidence

Machine-readable results, commands, source hashes, policy boundaries, mock
receipts, and NOT_RUN gates are in `verification.json`. Continuation actions
are in `NEXT_ACTIONS.md`.

## Limits

This is offline engineering evidence only. Current model/provider availability,
pricing freshness, account credits, credential readiness, provider-transfer
rights for a future payload, live compatibility, actual debit reconciliation,
and scientific adaptive benefit remain unverified. Keep live/provider HT-B4
`BLOCKED_LOCAL` until those gates are separately evidenced.
