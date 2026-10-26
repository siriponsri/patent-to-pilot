# Factual delta for Pepo: G10 correctness/search readiness

วันที่: 2026-10-27
สถานะ: `READY_FOR_PEPO_AUDIT`
Combined publication: Pepo's `DOCS_READY_FOR_LUNA` handoff received; W11 scoped staging review remains.

## สิ่งที่เปลี่ยน

- `src/patent_to_pilot/evaluation/comparison.py`: bounded P wrapper, runtime output contract/validation, normalized domain validation, explicit persistence `NOT_RUN`, separate failure accounting, dependent `SKIPPED` states, generator-exception capture, search-pool readiness and source/protected-baseline manifest generation.
- `scripts/run_g10_offline_comparison.py`: argparse runner with default run ID `g10-correctness-search-2026-10-27-r1`; refuses the protected old evidence directory.
- `tests/test_g10_offline_comparison.py`: 20 tests, including the required F1-F4 negative/control cases.
- New evidence: `results/development/g10-correctness-search-2026-10-27-r1/`.
- New docs: `docs/handoff/G10_CORRECTNESS_CLOSEOUT.md` and this factual delta.

## Actual result

- Run status: `PASS`.
- Methods: `B0_rules_only`, `B1_full_regeneration`, `B2_direct_revision`, `B3_invalidation_same_generator`, `P_existing_workflow` all `PASS`.
- Mock calls: `9`; mock cost: USD `0.0000000`; retries: `0`.
- Network: declared `0`; observation `NOT_MEASURED`.
- Search readiness: `POOL_NOT_READY`; `B4-RG` and `B4-DR` `NOT_IMPLEMENTED` / `NOT_RUN`.
- Historical old G10 evidence and `results/development/provider-pilot/live.sqlite3` hashes are unchanged.

## Checks

- G10 focused tests: `20 passed`.
- Targeted G09/G10/G11 suite: `57 passed`.
- Compile: `PASS`.
- Scoped `git diff --check`: `PASS`.
- No provider/model/API/GPU/UI/deploy work performed.

## Review boundary

Please audit the candidate source files, new run artifacts and hashes in `candidate-source-manifest.json`. README/assets ownership is now reconciled through `docs/handoff/LUNA_W10_DOCUMENTATION_AUDIT.md`. This delta does not claim scientific validity, search effectiveness, domain feasibility, patentability, FTO, clinical or regulatory approval.
