# HT-M39 current-head OpenRouter R1 offline readiness revalidation

- Run ID: `luna-long-run-20261030-openrouter-r1-readiness-current-head-20261030`
- Date: `2026-10-30` (Asia/Bangkok local execution)
- Parent audit: `docs/healthtech/audits/luna-long-run-20261030-openrouter-r1-readiness-20261030/README.md`
- Tested code commit: `23886b2194704ae521470f8e2af7e1024790e1b0`
- `origin/main` at verification: `23886b2194704ae521470f8e2af7e1024790e1b0`
- Status: `PASS_CURRENT_HEAD_OFFLINE_R1_READINESS_LIVE_BLOCKED`

## Scope

This package revalidates the existing HealthTech OpenRouter Round-1 policy,
durable budget boundary, provider regressions, offline dispatcher behavior, and
guarded repository verification at the current HEAD. It does not refresh live
provider metadata, read credentials, inspect account credit, transfer payloads,
or send provider requests.

## Results

- Focused R1/provider suite: `122 passed`.
- Direct full repository suite: `451 passed`, `2 warnings`.
- Guarded `verify_offline.py --suite all`: `451/451` passed, `0` failures,
  `0` errors, `0` skipped, `0` network attempts, and `0` credential-file read
  attempts.
- `compileall` and `git diff --check`: pass.
- Dispatcher dry-run: `READY_AWAITING_FUNDING_AND_BUDGET_APPROVAL`.
- Explicit unapproved live invocation: `BLOCKED` before any live result.
- Provider calls: `0`; paid cost: `USD 0.00`.

The guarded verification had one initial scratch-location failure when its
output directory was placed inside the repository. The failing path-smoke test
correctly treats repository-relative paths as internal. A clean rerun with the
output directory outside the repository passed all `451` tests; the failed
attempt is retained only as execution context, not as a product regression.

## Policy boundary

The R1 policy remains the existing versioned `$8.00` envelope with a `$7.00`
admission threshold, phase caps of `$0.40` canary, `$5.40` paired pilot, and
`$1.20` robustness, concurrency `1`, zero automatic retries, and unknown
billing blocked. This revalidation does not create new spend authorization.

## Verification

Machine-readable evidence is in [`verification.json`](verification.json) and
the cross-check receipt is in [`checks.json`](checks.json). The guarded test
output was run in a temporary directory outside the repository and is not
copied into this audit folder.

## Boundaries and blockers

- Current model/provider metadata and pricing refresh: `NOT_RUN`.
- Credential readiness, account credit, live compatibility, payload-transfer
  rights, and billing reconciliation: `NOT_RUN`.
- Live HT-B4: `BLOCKED_LOCAL`; no scientific adaptive-benefit claim is made.
- Semantic device-patent judgment source: `BLOCKED_LOCAL`; Zenodo record
  `21101400` remains restricted and lacks the owner-authorized schema/rights
  manifest needed for M23/M25/M24.
- Mock receipts, if used by the existing tests, are synthetic accounting only;
  they are not provider billing or scientific evidence.

## Next action

Keep live/provider HT-B4 blocked. The next information-gaining step is to
obtain an owner-authorized rights-cleared semantic judgment source, validate it
through M23, M25, and M24, and only then rerun frozen controls without changing
the denominator, holdout membership, family/company grouping, or `UNJUDGED`
policy.
