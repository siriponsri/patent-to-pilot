# HealthTech G1–G3 current-head offline revalidation

Run: `luna-g1-g3-20261028-210230-current-head`  
Date: 2026-10-28  
Tested code HEAD: `62e96ae9649da842ddead2c1d80e82658b054634`  
Tested `origin/main`: `62e96ae9649da842ddead2c1d80e82658b054634`

This is a current-head addendum after the G3 integration-handoff commit. The backend source is unchanged from the prior verified candidate; this run confirms that the current tracked candidate still passes the required offline boundaries.

## Results

```text
rtk proxy python -B scripts/healthtech/verify_offline.py results/healthtech/luna-g3-current-head-20261028-62e96ae-regression --suite all
PASS; 281 tests; 0 failures; 0 errors; 0 skipped; 0 network attempts; 0 credential-file reads; 0 provider calls; paid_cost_usd=0

rtk proxy python -B scripts/healthtech/run_dossier.py examples/healthtech/synthetic-device/input.json results/healthtech/luna-g3-current-head-20261028-62e96ae-synthetic
ENGINEERING_DRAFT; 2 candidates; provider_calls=0; paid_cost_usd=0; stop_reason=fixed_schedule_complete

rtk proxy python -B scripts/healthtech/run_api_dry_run.py configs/healthtech/api_dry_run.json
DRY_RUN_NOT_EXECUTED; network_attempts=0; provider_calls=0; paid_cost_usd=0; response_schema_valid=null
```

Machine verification: `docs/healthtech/evidence/luna-g1-g3-20261028/current-head-210230.json`. The verifier reported `source_unchanged=true`; its scope is Python socket/DNS and repository `.env` access guards, not OS-level packet capture.

## Reused evidence and boundaries

- Parser replay, corrected Abbott baselines, R1–R3 repair evidence, and the three public G3 backend walkthroughs remain at the prior receipts and artifact paths; no acquisition or corrected baseline rerun was needed for this documentation-only commit.
- G1 remains `PARTIAL` because the Bridge branch still lacks verified reuse rights, per-link disclosure provenance, and recoverable cohort/split evidence.
- G2 remains `PARTIAL_DEVELOPMENT_ONLY`; the three-device Abbott branch has no final holdout and is not a generalization claim.
- G3 remains `BACKEND_COMPLETE_UI_PENDING`; the Claude UX/UI worktree is paused and untouched. The new Luna integration handoff is at `docs/healthtech/integration/luna-g3-20261028-28dfb1d/`.
- No clinical, FTO, patent-validity, investment, publication, customer-validation, deployment, or production-readiness claim is made.
