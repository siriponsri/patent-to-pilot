# Next actions — HealthTech

Record: HT-NEXT-003 · Scope: research/patent-to-pilot · Date: 2026-10-28 · Status: OBSERVED_LOCAL / DECISION

Supersedes HT-NEXT-002 as the current work order. Owner supplied the HealthTech Pack and authorized migration, recoverable cleanup and commit/push to main. Paid model runs/deployment remain outside this task

Implemented package: R1 native tokenizer repair, R2 durable baseline-attempt preservation, R3 fixed-prefix/frontier controls, 41/41 local patent parser replay with source-specific checks, corrected CPU-local HT-B0a/B0b/B1/B2/B3 development run, and G3 backend history/export concurrency repair. See [historical repair receipt](../docs/healthtech/LUNA_G1_G3_RECEIPT_20261028-200041.md), [current revalidation receipt](../docs/healthtech/LUNA_G1_G3_REVALIDATION_20261028-203003.md), and [machine verification](../docs/healthtech/evidence/luna-g1-g3-20261028/revalidation-203003.json)

Verification: current HEAD `62e96ae9649da842ddead2c1d80e82658b054634` passes the guarded full offline suite at 281 tests with zero failures/errors/skips, zero network attempts, zero credential-file reads, zero provider calls and zero paid cost. The current artifact is `results/healthtech/luna-g3-current-head-20261028-62e96ae-regression/verification.json`; the current synthetic smoke returned 2 candidates with `ENGINEERING_DRAFT`, and the guarded HT API dry-run returned `DRY_RUN_NOT_EXECUTED` with zero network/provider calls. Three real public dossiers also passed backend source-view, edit/history, selected-version TH/EN export, and explicit empty-patent-pool checks. The earlier disposable clean-worktree rerun at `a449ccad7f93771a23018e1abccf28f486f466cd` remains recorded with the model-junction provenance and line-ending hash reconciliation. These remain development outputs, not final scientific generalization or publication results

Next ready package: review/integrate the Luna backend contract recorded in `docs/healthtech/integration/luna-g3-20261028-28dfb1d/` with the paused Claude UX branch when ownership resumes, then resolve the Bridge rights/cohort/split blocker or obtain a licensed replacement with per-link disclosure provenance. Keep the three-device Abbott branch development-only; do not treat product-level disclosure as component-level expert gold or reuse the synthetic fixture as a real device result

Main Bridge study: `BLOCKED_LOCAL` on reuse rights/cohort reconciliation/split reproducibility. Source: pinned upstream `f3990a207949f25012d1070a08ac303e140387e6`, README SHA-256 recorded in `BRIDGE_RIGHTS_COHORT.md`, and supplied pack audit. Other work can continue without substituting the Abbott branch for Bridge gold

Remaining: Bridge or equivalent rights-cleared main corpus, final holdout/generalization design, broader independent groups, live-provider B4 (not authorized), Claude UI integration, clinical/FTO analysis, deployment, customer validation and manuscript. Do not infer COMPLETE from file names or passing development tests

Audit follow-up: public regression selection now includes all published provider security modules; paired tests use mock-seeded tmp journals. Original 262-local/185-clean receipt remains a dated record. See `docs/healthtech/REPRODUCIBILITY_AUDIT.md` for corrected clean-checkout evidence. Research/product next actions above are unchanged.
