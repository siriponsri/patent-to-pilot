# Normal-round E2 admission audit addendum

- Parent audit: `ptp-e2-admission-recheck-20261104`
- Round: `Normal`, existing `main` checkout only
- Base HEAD before this round: `a8c8e229e6489bb29ae6f88f310f7307c8a09441`
- Scope: documentation correction, current-instruction repair, offline fixtures, and isolated test-ledger verification
- Exclusions: no goal resume, long run, new worktree, paid dispatch, reservation, GPU job, provider retry, ledger mutation, push, merge, or branch/worktree cleanup

## Fixed

- Corrected the credit-hash reference in the parent audit README and verification record. The actual private snapshot file hashes to `9c7a92b1048b73cd6af71dfbe6cd42aa1567c485a1d094b4bf0dc1f85072c603` over raw bytes. Its embedded and normalized v2 content hash remains `87ca37f6789519fdd1184afaa157423fedea33b61b6a3eb80408f9e9a5f06c5d`. The snapshot file and `as_of_utc=2026-11-04T11:21:09.628375+00:00` were not changed.
- Disambiguated the recorded pricing snapshot the same way: raw file SHA-256 `c128af4d377d3cec07d7d27af6bd4d406bb17a595c512e418978be40ff3e8aea`, canonical content hash `c680da332b86a8b153824758316a1168a5006068093306a386168f2ab743496a`. At the Normal check it was `6164.941` seconds old, so it was not treated as fresh.
- Clarified that `key_limit_unlimited=true` plus `key_remaining_usd=null` is an explicit `UNLIMITED` observation, not a missing value. Account scope is owner-asserted and the account/key binding is not provider-verified.
- Rebound current guidance to the existing `main` checkout and paused state. Historical push, cleanup, candidate-worktree, and long-run instructions remain identifiable as historical receipts.

## Tested

- Credit normalization fixture: PASS. UTC timestamp accepted; canonical normalized hash equals the embedded hash; explicit unlimited state preserved; missing/false unlimited marker rejected.
- Timezone fixture: PASS through the existing offset-normalization and naive-timestamp rejection tests.
- Scope binding fixture: PASS through the existing E2 authorization/account/key checks; mismatched scope does not create an attempt.
- Pricing freshness: PASS as a code-gate check in offline fixtures; the recorded route snapshot was fresh at the original E2 checkpoint but is not re-declared fresh for this later Normal round.
- Rights: PASS through the rights-cleared payload fixtures; blocked or stale source provenance is rejected.
- Output journal: PASS through private-journal persistence, invalid-output retention, sink-failure stop, and sanitized-receipt tests.
- Isolated ledger: PASS. A temporary test ledger began with zero `budget_epoch_scope` rows, accepted the first valid reservation, bound the scope in that transaction, and left the real ledger untouched.
- Focused command result after patch: `70 passed`, `0 failed`, `0 skipped`; isolated ledger subset: `7 passed`; `git diff --check`: PASS. Exact commands and exit codes are recorded in `normal-verification.json` in this same audit directory.

## Pending

- Paid admission remains stopped before credit refresh/reservation. The next paid gate, only after a new owner goal prompt, is one fresh non-secret snapshot for the existing dispatch key, then same-window exact-route pricing, rights, writer quiescence, and existing-ledger reservation checks.
- Legacy history remains four settled calls totaling `USD0.0001464`; history completeness remains unknown; project ceiling remains `USD100`; prospective E2 allowance remains `USD1`.
- World Patent Information direction, scientific acceptance, external business validation, WPI-specific author checks, and owner review remain partial or pending.

## Command and evidence log

The commands for this addendum are all local/offline and use the repository RTK prefix. The canonical machine-readable result is `normal-verification.json` in this same audit directory. Private paths are recorded only as sanitized `%LOCALAPPDATA%` references; no credential or `.env` content is included.
