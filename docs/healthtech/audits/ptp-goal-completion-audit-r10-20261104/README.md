# Patent-to-Pilot goal completion audit r10

Recorded: 2026-11-03T17:37:07.7239338Z (2026-11-04 Asia/Bangkok)

This is a requirement-by-requirement audit of the existing Patent-to-Pilot
goal. It does not redefine success around tests, a three-case demo, or the
paid branch alone. The goal remains active and is not marked complete or
blocked.

## Candidate and accounting boundary

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Working tree: intentionally dirty; owner/Claude/Luna/research/audit work is
  preserved.
- E2 journal: SQLite integrity `ok`; new attempts `0`; pending/unknown `0`;
  four legacy settled receipts; known legacy actual `USD0.0001464`;
  `UNKNOWN_OWNER_ACCEPTED_CUTOVER`; prospective allowance `USD1`.
- No budget reset, time-window reset, duplicate pending dispatch, provider
  call, GPU job, or ledger mutation occurred in this audit.

## Requirement audit

| Requirement | Status | Evidence boundary |
|---|---|---|
| O1 UI -> HTTP jobs/history/export engineering | COMPLETE_CURRENT_HEAD | Current-head HTTP/browser and three-case local-vector receipts; full suite is 642 total, 640 passed, 0 failed, 0 errors, 2 skipped. Engineering is not deployment or user validation. |
| O2 PatEmbed/E5 and reproducible artifacts | PARTIAL | Fresh V100 and current provider-binding receipts are integrity verified. Main scientific comparison lacks semantic gold and a current final holdout. |
| O3 local/API generation comparison | PARTIAL | Guided local Qwen3-8B is schema-valid on 3/3 frozen cases. Paid qwen/qwen3-32b is not run because current scoped credit/limit evidence is unavailable. |
| O4 three real cases and dossier lifecycle | PARTIAL_RESEARCH | Three named cases complete the engineering lifecycle, but this is not an adaptive-superiority study, user study, or paid comparison. |
| Adaptive fixed-budget research claim | NOT_ESTABLISHED | Current frontier has unequal realized totals; matched prefix is post-hoc first-action only. No powered final holdout is available. |
| Business value | PARTIAL_PROXY_ONLY | Citation/locator integrity, evidence coverage, machine time and scenario sensitivity are measured. Human time, revenue, ROI, willingness-to-pay and independent validation are not measured. |
| Journal package | READY_FOR_OWNER_REVIEW | Manuscript, supplemental methods, checklist and cover-letter draft exist. WPI journal-specific Guide/Aims and owner declarations remain unverified. |
| Release | PARTIAL_DIRTY_CANDIDATE | Current-head tests and compile checks pass, but the worktree is intentionally dirty and has not been reviewed, committed, pushed or merged. |

## G0-G8 status

- G0: `COMPLETE_CONTRACT_AND_SCOPE`.
- G1: `PARTIAL_RIGHTS_AND_SEMANTIC_GOLD_INCOMPLETE`.
- G2: `PARTIAL_DEVELOPMENT_BASELINES_AND_EVALUATOR`.
- G3: `PASS_CURRENT_HEAD_O1_HTTP_UI_ENGINEERING`.
- G4: `PARTIAL_DESCRIPTIVE_FRONTIER_NOT_ESTIMABLE`.
- G5: `OPERATIONAL_POTENTIAL_ONLY_EXTERNAL_VALIDATION_NOT_VALIDATED`.
- G6: `PARTIAL_OWNER_REVIEW_AND_WPI_GUIDE_RECHECK`.
- G7: `PASS_CURRENT_HEAD_OFFLINE_RELEASE_READINESS_DIRTY_CANDIDATE_NOT_RELEASED`.
- G8: `NOT_RUN_FUTURE_SCOPE`.

## Exact remaining actions

1. If the paid comparison remains required, obtain one non-secret current
   scoped credit/remaining-limit snapshot through an approved channel. Then
   reconcile it to E2, refresh exact-route pricing within 300 seconds,
   revalidate the rights-cleared pack, reserve at most the existing
   `USD0.25` canary, and dispatch once. Never replay an unknown or pending call.
2. Owner rechecks the live WPI Guide for Authors and confirms author names,
   affiliations, declarations, funding, conflicts, data/code availability,
   and AI-use disclosure. No submission or agreement is delegated.
3. To support the main adaptive claim, obtain or authorize a rights-cleared
   independent final holdout and freeze its protocol before scoring. Without
   that evidence, retain the descriptive claim boundary.
4. Review dirty candidate ownership and release history before any commit,
   push, merge, or cleanup.

The goal remains `ACTIVE_NOT_COMPLETE_NOT_BLOCKED`: substantial local work is
still possible, but the missing external credit evidence and missing/unauthorized
scientific holdout cannot be fabricated or inferred from existing tests.
