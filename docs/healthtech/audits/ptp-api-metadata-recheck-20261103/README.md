# OpenRouter metadata recheck — 2026-11-03

This checkpoint re-ran the existing bounded read-only metadata helper for the
owner-supplied `.env` path. The helper parsed only `OPENROUTER_API_KEY`; the
secret value was not printed, copied, persisted, or staged.

Observed facts:

- `/api/v1/key` returned HTTP 200.
- Lifetime key usage was `USD0.0001464`; daily, weekly, and monthly usage were
  `USD0`.
- The key is an ordinary key, not a management key. The helper therefore did
  not request or fabricate account credits.
- Account scope and complete R1 history remain unreconciled; live admission is
  false.
- No provider generation, reservation, attempt ID, retry, ledger mutation,
  budget reset, or time-window reset occurred.

The machine-readable observation is in `verification.json`. It is a private
sanitized receipt and is not an account-balance attestation or proof that the
historical journal is complete.

Next action remains one-time owner evidence for the location of the existing
canonical R1 journal or a sanitized all-attempt export, plus a current scoped
account/key credit snapshot through an authorized channel. No secret is
requested.

## R2 follow-up

The same bounded helper was rerun at `2026-11-03T02:51:28.554157+00:00`.
The sanitized receipt is `metadata-observation-r2.json` and the continuation
checkpoint is `CHECKPOINT_R2.json`. It recorded the same lifetime usage
`USD0.0001464`, no scoped credit snapshot, and no canonical journal at the
known checked paths. The paid branch remains
`BLOCKED_BEFORE_RESERVATION`; no provider call, reservation, attempt, retry,
or ledger mutation occurred. The full candidate suite after the checkpoint
update was `615 total; 614 passed; 0 failed; 1 skipped`.
