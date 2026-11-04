# OpenRouter key-path follow-up checkpoint — 2026-11-03

This checkpoint continues the original Patent-to-Pilot O1–O4 goal at candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. The owner supplied the existing
`.env` path for a read-only OpenRouter metadata check. The key value was never
printed, copied, staged, or written to an artifact.

## Result

Status: `PASS_READ_ONLY_METADATA_REFRESH_DISPATCH_BLOCKED`.

- `/api/v1/key` returned HTTP 200.
- Sanitized lifetime usage is `USD0.0001464`; daily usage is `USD0`.
- The key is ordinary, not a management key, so the approved helper cannot
  obtain the scoped v2 account-credit snapshot needed by the live gate.
- The canonical R1 registry is absent at the standard per-user location. The
  live budget constructor failed closed before state creation with
  `canonical ledger registry is missing`.
- The existing rights-cleared 3-case pack and current DeepInfra route snapshot
  remain valid. No provider request was sent.

## Verification

- Focused API/ledger/provider regression: `84 passed, 0 failed, 0 skipped`.
- Full Python suite: `611 tests; 610 passed; 0 failed; 0 errors; 1 skipped`.
- `compileall`: PASS.
- `git diff --check`: PASS.
- Provider calls, reservations, new attempt IDs, retries, ledger mutations,
  budget resets, and window resets: `0`.

The paid branch remains closed before reservation. Continue offline/local and
manuscript work. One owner action is still sufficient: provide the existing
canonical R1 journal location or a sanitized all-attempt export, and a current
scoped v2 credit snapshot if the approved integration cannot provide it. Do not
send a secret or repeat the USD authorization request.
