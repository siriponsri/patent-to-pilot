# Patent-to-Pilot O1–O4 completion audit r20

Recorded: 4 November 2026 (Asia/Bangkok),
`2026-11-04T07:30:09.7294230+07:00`.

This is a current-state requirement audit of the existing Patent-to-Pilot
goal. It does not create a goal, rerun successful GPU/model work, retry paid
requests, reset the accounting epoch, or merge the dirty candidate.

## Decision

Status: `ACTIVE_NOT_COMPLETE_NOT_BLOCKED`.

Candidate HEAD is `88dc40471cb9078f929c02bb893cfa1e364da841` on
`codex/patent-to-pilot-long-run-20261103`. No independent Qwen/OpenRouter,
encoder, pytest, dr-train, or SSH experiment process was found by the scoped
process inspection. The worktree remains intentionally dirty with owner,
Claude, Luna, source, and audit changes preserved.

## Requirement audit

| Area | Current status | Evidence and limit |
|---|---|---|
| G0 contract/scope | `COMPLETE` | `LONG_RUN_GOAL.md`, `EXECUTION_PLAN.md` |
| G1 rights/gold | `PARTIAL` | Product-level disclosed links are not semantic relevance gold; Bridge/final semantic gold remains unavailable or restricted. |
| G2 baselines/evaluator | `PARTIAL_DEVELOPMENT` | Offline baselines and evaluator are real and descriptive; no powered final adaptive comparison. |
| G3 UI/HTTP engineering | `PASS_CURRENT_HEAD` | Loopback HTTP/browser retrieval, source inspection, edit/history/reopen, and JSON/TH/EN export are verified. |
| G4 adaptive frontier | `PARTIAL_DESCRIPTIVE_NOT_ESTIMABLE` | Only the 3-query/123-rerank matched diagnostic is equal-budget; larger slices have unequal realized budgets and no final holdout. |
| G5 business value | `PARTIAL_OPERATIONAL_POTENTIAL_ONLY` | Machine latency, citation/locator, evidence coverage, and scenario measures exist; human time, independent validation, revenue, ROI, and willingness-to-pay are not measured. |
| G6 manuscript/WPI | `PARTIAL_OWNER_REVIEW` | Manuscript and checklist are prepared; WPI journal-specific Guide/Aims remain owner recheck items; nothing was submitted. |
| G7 release | `PASS_ENGINEERING_DIRTY_CANDIDATE` | Current candidate has offline regression/release evidence, but it is not a clean released commit and owner review is pending. |
| G8 future scope | `NOT_RUN` | Outside the current solo computational study. |
| O1 | `COMPLETE_ENGINEERING` | UI → HTTP → retrieval/evidence → source/history/edit/reopen/export current-head evidence. |
| O2 | `COMPLETE_ENGINEERING_PARTIAL_RESEARCH` | PatEmbed and multilingual-e5 remote/resumable shards are bound to the shared engine; semantic endpoint remains partial. |
| O3 | `LOCAL_PASS_API_BLOCKED` | Local Qwen3-8B is 3/3 schema-valid on the frozen pack; paid qwen/qwen3-32b has no provider result because admission stops before reservation. |
| O4 | `ENGINEERING_PASS_RESEARCH_PARTIAL` | Three named device cases and current-head workflow pass; adaptive research remains descriptive. |

## Current accounting and paid gate

The owner-set first-round OpenRouter MCP/provider limit is USD30.00, recorded
as provider-side metadata separate from the project USD100 cumulative ceiling
and E2 prospective USD1 allowance. The latest account-level MCP receipt still
reports `total_credits=10` and `total_usage=0.0001464`; the latest sanitized
`.env` observation reports HTTP 200 for an ordinary non-management key but
`limit=null`, `limit_remaining=null`, empty budgets, and
`live_admission_enabled=false`.

The E2 journal remains authoritative for the accepted cutover: four legacy
settled receipts totaling USD0.0001464, unknown R1 history preserved, and no
operational/pending/unknown rows. Missing R1 completeness is not a separate
current E2 gate. The paid branch remains
`BLOCKED_BEFORE_RESERVATION` until a permitted current scoped credit/remaining
limit or explicit unlimited observation binds the dispatch key. Route pricing
must then be refreshed by the runner inside the admission window.

Evidence:

- `docs/healthtech/audits/ptp-api-openrouter-mcp-recheck-r2-20261104/verification.json`
- `docs/healthtech/audits/ptp-api-metadata-recheck-r12-20261104/verification.json`
- `docs/healthtech/audits/ptp-offline-regression-r19-20261104/verification.json`
- `docs/healthtech/long-runs/CURRENT_ACCEPTANCE_MATRIX.json`

## Current engineering verification

- Full offline regression: `657 collected; 655 passed; 2 skipped; 0 failed; exit 0`.
- Focused metadata observer regression: `20 passed; 0 failed; 0 skipped`.
- JSON readback: PASS for the current receipts, matrix, progress, and owner-review manifest.
- `git diff --check`: PASS.
- Resource mutations in this audit: paid calls `0`, reservations `0`, retries `0`, ledger writes `0`, GPU jobs `0`, dataset downloads `0`, budget/window resets `false`.

## Next discriminating action

Do not rerun the metadata observer or call paid API without new permitted
evidence. If the owner provides one current scoped credit/remaining-limit
snapshot through an approved non-secret channel, reconcile it to E2, refresh
exact-route pricing, revalidate the rights-cleared payload, and reserve only
the existing prospective canary through the canonical ledger. Otherwise keep
working on owner review and manuscript/release preparation without claiming
paid comparison, adaptive superiority, user validation, revenue, ROI, or
publication acceptance.
