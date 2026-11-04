# OpenRouter owner-key metadata recheck — 2026-11-03

This audit continues the original Patent-to-Pilot O1–O4 goal at candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. The owner supplied the existing
`.env` path for a bounded read-only metadata observation. The key value was
selected internally by the approved observer and was not printed, copied,
staged, or persisted.

The observation completed at `2026-11-03T11:21:38.060778+07:00` with HTTP 200.
The sanitized key metadata reports lifetime usage `USD0.0001464` and
daily/weekly/monthly usage `USD0`. The key is ordinary rather than a
management key, so the observer could not obtain the scoped v2 account-credit
snapshot. Account scope remains unreconciled and history completeness remains
unproven.

This is metadata evidence only. It does not prove account balance, complete R1
history, or paid-run authorization by itself. The paid branch therefore remains
`BLOCKED_BEFORE_RESERVATION` until the existing canonical R1 journal or
sanitized all-attempt export and the current scoped credit snapshot are
available. No provider generation, reservation, attempt, retry, ledger
mutation, budget reset, or time-window reset occurred.

Verification receipt: [`metadata-observation.json`](metadata-observation.json).

The exact candidate full Python suite was rerun after this checkpoint: `615`
tests, `0` failures, `0` errors, and `1` skip in `21.892` seconds. The skip is
the existing pinned local-tokenizer-artifact availability condition. JUnit
receipt: [`full-tests.xml`](full-tests.xml).

