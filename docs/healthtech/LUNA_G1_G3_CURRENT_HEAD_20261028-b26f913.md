# HealthTech G1–G3 current-head offline revalidation

Run: `luna-g1-g3-20261028-b26f913-current-head`  
Date: 2026-10-28  
Tested code HEAD: `b26f9138d2c36e36195755162c092088f23e9be4`  
Tested `origin/main`: `b26f9138d2c36e36195755162c092088f23e9be4`

This is the clean-head revalidation after the Markdown export contract repair. The code commit is pushed to `main`; owner-only untracked artifacts remain outside the commit.

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

## Reused evidence and boundaries

- Parser replay, corrected Abbott baselines, R1–R3 repair evidence, and the three public G3 backend walkthroughs remain at their prior receipts and artifact paths.
- G1 remains `PARTIAL` because the Bridge branch still lacks verified reuse rights, per-link disclosure provenance, and recoverable cohort/split evidence.
- G2 remains `PARTIAL_DEVELOPMENT_ONLY`; the three-device Abbott branch has no final holdout and is not a generalization claim.
- G3 remains `BACKEND_COMPLETE_UI_PENDING`; the Claude UX/UI worktree is paused and untouched. The Luna integration handoff is at `docs/healthtech/integration/luna-g3-20261028-28dfb1d/`.
- No clinical, FTO, patent-validity, investment, publication, customer-validation, deployment, or production-readiness claim is made.
