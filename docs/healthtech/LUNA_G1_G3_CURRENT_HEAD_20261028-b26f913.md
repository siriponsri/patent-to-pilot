# HealthTech G1–G3 current-head offline revalidation

Run: `luna-g1-g3-20261028-b26f913-current-head`  
Date: 2026-10-28  
Tested code HEAD: `b26f9138d2c36e36195755162c092088f23e9be4`  
Tested `origin/main`: `b26f9138d2c36e36195755162c092088f23e9be4`

This is the clean-head revalidation after the Markdown export contract repair. The code commit is pushed to `main`; owner-only untracked artifacts remain outside the commit.

## Run boundary

- Tested package start/end code and `origin/main`: `b26f9138d2c36e36195755162c092088f23e9be4`; tracked working tree was clean at test time and owner-only untracked artifacts were preserved.
- Python: `3.12.10`; corrected baseline run used the pinned local encoder `sentence-transformers/all-MiniLM-L6-v2@1110a243fdf4706b3f48f1d95db1a4f5529b4d41` and reranker `cross-encoder/ms-marco-MiniLM-L-6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`, with protocol hash `7dab96b735c70bcf60b99f191477c5add04d95c337d437c2d17b546e8b226cf2` and cohort manifest hash `6e793d3b40da983c8829ee88ed96e42df0d5b65109d4e6c8144901d2f6d42787`.
- Main worktree is `main`; the paused Claude worktree remains `claude/healthtech-ux-local-20261028` at `96c63b14a1a2df8e8f8b816edee0dff7feddc3d3`; no frontend or Claude-worktree path was modified.

## Results

```text
rtk proxy python -B -m pytest -p no:cacheprovider tests/test_healthtech_repairs.py -q
6 passed; 0 failed; 0 skipped

rtk proxy python -B scripts/healthtech/verify_offline.py docs/healthtech/evidence/luna-g1-g3-20261028/current-head-b26f913 --suite all
PASS; 281 tests; 0 failures; 0 errors; 0 skipped; 0 network attempts; 0 credential-file reads; 0 provider calls; paid_cost_usd=0

rtk proxy python -B scripts/healthtech/run_dossier.py examples/healthtech/synthetic-device/input.json docs/healthtech/evidence/luna-g1-g3-20261028/current-head-b26f913/synthetic-smoke
ENGINEERING_DRAFT; 2 candidates; provider_calls=0; paid_cost_usd=0; stop_reason=fixed_schedule_complete

rtk proxy python -B scripts/healthtech/run_api_dry_run.py configs/healthtech/api_dry_run.json
DRY_RUN_NOT_EXECUTED; network_attempts=0; provider_calls=0; paid_cost_usd=0; response_schema_valid=null
```

Machine verification: `docs/healthtech/evidence/luna-g1-g3-20261028/current-head-b26f913.json`. The raw verifier receipt is `docs/healthtech/evidence/luna-g1-g3-20261028/current-head-b26f913/verification.json`; its guard scope is Python socket/DNS and repository `.env` access checks, not OS-level packet capture.

## Contract repair

- English and Thai Markdown exports now preserve dossier version, parent version, validation scope, user edits, and source type/synthetic/hash context.
- The repair test covers stale-parent rejection, simultaneous-writer conflict handling, and the bilingual export fields.

## G1/G2/G3 evidence

- G1 parser replay processed `41/41` patent files with zero raw-hash mismatches, normalized-hash mismatches, or field mismatches; all title/abstract/claims fields were nonempty. Three openFDA PMA records and three Abbott disclosure sections were checked, with disclosed patent counts `21/23/17`. Evidence: `docs/healthtech/evidence/luna-g1-g3-20261028/parser-replay-and-source-checks.json`.
- G1 remains partial: the Abbott branch is a three-device, one-applicant development cohort with two exact-patent components, no sourced family map, and no final holdout. Bridge remains `BLOCKED_LOCAL` for missing verified reuse/redistribution terms, per-link disclosure provenance, cohort reconciliation, and recoverable split evidence; the Bridge payload was not downloaded.
- G2 corrected local methods are `HT-B0a`, `HT-B0b`, `HT-B1`, `HT-B2`, and `HT-B3` over 3 devices, 41 patents, and 61 product-level reference pairs. Macro known-link Recall@20 is B0a `0.442739`, B0b `0.662242`, B1 `0.498802`, B2 `0.568912`, B3 `0.498802`; these are descriptive development results, not superiority or generalization claims.
- Realized resource frontier: B0a/B0b `3` query calls each; B1 `3` calls/`123` rerank pairs; B2 `9`/`369`; B3 `5`/`205`; all methods completed with zero failed attempts. Raw ranks, evaluator separation, per-device/group results, resource accounting, prefix diagnostics, and headroom are under `results/healthtech/luna-g1-g3-20261028-200041/corrected-baselines/`.
- G3 backend walkthroughs cover `K121849`, `K163345`, and `K190167`: each has 1 source, 7 evidence items, 0 candidates, 3 unresolved items, 3 next requests, history versions `1→2`, expected-parent checking, exact source-field view, and selected-version JSON/English/Thai export. Machine manifest: `docs/healthtech/evidence/luna-g1-g3-20261028/revalidation-203003.json`; output root: `results/healthtech/luna-g1-g3-20261028-203003-revalidation/g3-three-public-cases/`.
- Fresh current-head CLI smoke also passed `init → edit --expected-version 1 → manifest → export --version 2 → exact source view`, with the user note preserved in version 2 and all three Markdown/JSON exports written under `docs/healthtech/evidence/luna-g1-g3-20261028/current-head-b26f913/cli-history-smoke/`.
- The three public dossiers have empty patent input pools. They are regulatory facts-only cases, not evidence of exhaustive patent absence or device–patent coverage.

## Reused evidence and boundaries

- Parser replay, corrected Abbott baselines, R1–R3 repair evidence, and the three public G3 backend walkthroughs remain at their prior receipts and artifact paths.
- G1 remains `PARTIAL` because the Bridge branch still lacks verified reuse rights, per-link disclosure provenance, and recoverable cohort/split evidence.
- G2 remains `PARTIAL_DEVELOPMENT_ONLY`; the three-device Abbott branch has no final holdout and is not a generalization claim.
- G3 remains `BACKEND_COMPLETE_UI_PENDING`; the Claude UX/UI worktree is paused and untouched. The Luna integration handoff is at `docs/healthtech/integration/luna-g3-20261028-28dfb1d/`.
- Current revalidation used no network acquisition, local model inference, provider dispatch, paid call, credential read, deployment, or outreach. R2 failure paths and R3 prefix controls were exercised with authored mocks; the corrected G2 run is the separate CPU-local execution package described above.
- No clinical, FTO, patent-validity, investment, publication, customer-validation, deployment, or production-readiness claim is made.
