# Patent-to-Pilot O1-O4 completion audit r18

Recorded: 4 November 2026 (Asia/Bangkok), `2026-11-04T07:10:24.2835353+07:00`

This requirement-level audit rebinds the active Patent-to-Pilot goal to the
current candidate HEAD and incorporates the owner-configured OpenRouter MCP
credit receipt. It does not pool candidates, rerun successful GPU work, retry
paid calls, or turn account-level credit into key-level admission evidence.

## Decision

The goal remains `ACTIVE_NOT_COMPLETE_NOT_BLOCKED`.

- O1 engineering is complete on the current candidate.
- O2 engineering is complete for the remote PatEmbed and multilingual-e5
  shards bound to the shared engine; scientific evidence remains descriptive.
- O3 local generation is `3/3` schema-valid on the frozen rights-cleared pack.
  The paid API branch remains before reservation because exact remaining limit
  and scope for the `.env` dispatch key are unresolved.
- O4 engineering passes for the three named cases. The adaptive-research
  evidence remains descriptive because the main final semantic holdout and
  device-patent gold are unavailable.
- Business evidence is solo operational potential and scenario analysis only.
- The manuscript/journal package is ready for owner review and is not
  submitted.

## Paid evidence and accounting

OpenRouter MCP `get-credits` returned account-level
`total_credits=10` and `total_usage=0.0001464`. A read-only E2 reconciliation
returned SQLite integrity `ok`, four legacy settled receipts totaling
`USD0.0001464`, zero operational attempt rows, and zero attempt-context rows.
The usage values match, but the MCP response did not provide the dispatch
key's exact remaining limit, key scope, or response timestamp. The owner-
supplied `USD30` MCP cap remains separate provider-key metadata and is not
treated as project spend authorization.

No reservation, provider generation, retry, ledger mutation, budget reset, or
window reset occurred. The canonical E2 journal and unknown-history boundary
remain unchanged.

## Research and publication boundary

The only matched-budget adaptive slice remains the post-hoc `3 query calls /
123 rerank pairs` comparison with macro Recall@20 `0.49880241951853205` for
the matched first-action policies. No adaptive-superiority or significance
claim is made. PANORAMA/Helmers remain component diagnostics rather than the
main adaptive device-patent endpoint.

The manuscript now binds the MCP account-credit evidence while preserving the
exact-key and paid-comparison limitation. The current manuscript has 76
checked relative links and zero missing. Owner author/declaration fields,
live journal-specific Guide/Aims review, release/archive decisions, and
submission remain owner-controlled.

## Current evidence

- Candidate: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Paid/MCP receipt: `docs/healthtech/audits/ptp-api-openrouter-mcp-recheck-r2-20261104/verification.json`
- E2/MCP receipt: `docs/healthtech/audits/ptp-api-openrouter-mcp-recheck-r2-20261104/mcp-get-credits.json`
- Manuscript rebind: `docs/healthtech/audits/ptp-manuscript-mcp-credit-rebind-20261104/verification.json`
- O2 completion: `docs/healthtech/audits/ptp-o2-current-head-completion-r16-20261104/verification.json`
- Local O3/O4 cases: `docs/healthtech/audits/ptp-local-qwen-patent-run-20261104/verification.json`

