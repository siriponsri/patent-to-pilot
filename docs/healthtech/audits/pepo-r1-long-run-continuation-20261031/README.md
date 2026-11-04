# Patent-to-Pilot R1 long-run continuation - 2026-10-31

Status: `PASS_ENGINEERING_MIGRATION_PAID_RESEARCH_BLOCKED`.

This continuation starts from candidate base `9ac38720d219b83acccaa92dcabc4480283914c4` on branch `codex/r1-owner-evidence-20261031` and accepts `r1-owner-evidence-recovery.patch` exactly once after `git apply --check`. Claude/Luna/source worktrees were not modified. No push, merge, credential read, provider call, GPU job, or owner-ledger mutation occurred.

## Engineering completed

- Added an append-only reviewed migration for an existing R1 SQLite journal. It rejects missing files, legacy/mock namespaces, rebinds, copied paths, invented attempt rows, and alternate registries.
- Added a typed `budget_pre_r1_carryover` record. The supplied `USD0.0001464` can be counted against the existing USD8 cap without rewriting legacy dates, phases, models, payload hashes, or attempt IDs.
- Live transport now requires the reviewed history anchor, verified writer quiescence, zero reviewed unresolved exposure, matching carryover scope, and the one canonical registry before reservation.
- Carryover remains present after an exact pricing snapshot refresh. Settlement remains idempotent and unknown/pending reservations remain blocking.
- Added a CLI seam for the reviewed migration; it accepts sanitized review/carryover JSON and never reads credentials.

## Evidence state

- Owner evidence remains: one OpenRouter key, visual UI receipt `USD10.00` received at `2026-10-31T14:09:42Z`, and sanitized key metadata observation at `2026-10-31T14:17:41Z` with cumulative usage `USD0.0001464` and today `USD0`.
- Those facts reconcile the four known legacy attempts, but do not prove complete R1 history or absence of in-flight requests. The real R1 journal location/export is still unavailable in this candidate.
- A project-filtered process check observed an `ssh.exe` child of `rtk.exe`; command lines were not logged. This is compatible with the tool transport, but it is not proof that all external writers/jobs are quiescent. No process was killed or bypassed.
- The current rights-cleared FDA pack has three cases and three exact message records. Its pack hash is recorded in `pack-receipt.json`; raw messages and source payloads remain private.

## O3/O4 outcome

- O3 engineering: `PASS`. Migration, shared-ledger counting, live fail-closed gate, metadata observation, rights-cleared payload, and API runner regressions pass.
- O3 API branch: `NOT_RUN/BLOCKED`. No paid request was sent because the real R1 all-attempt completeness/quiescence evidence and a current authorized account/key credit snapshot are not both present in the runtime gate.
- Local Qwen3-8B on the current rights-cleared pack: `NOT_RUN`. This executor has no `torch` or `transformers`; the known local model root has no visible model files. The historical local receipt for pack `d2a91ce...` is retained as prior evidence and is not promoted to the current pack `e033456a...`.
- O4 product-path engineering: existing three-case Abbott browser/HTTP/local-generation receipt remains valid as parent evidence. A new matched fixed/adaptive research run is `NOT_RUN` because evaluator references/groups for the current private runtime cohort are absent; the old Stryker frontier is not substituted.

## Verification

- Full Python suite: exit `0`, `558` collected, `557` passed, `1` skipped, warnings only.
- Focused migration/ledger/budget/generation/metadata suite: `115 passed`.
- Compileall and `git diff --check`: pass.
- Paid/provider calls: `0`; paid cost: `USD0.00`; production/private ledger mutations: `0`.

See `REPORT.md`, `REPORT_TH.md`, `verification.json`, `CHECKPOINT.json`, `pack-receipt.json`, and `paper-appendix.md`.
