# Private frontier reconciliation

This package continues the existing Patent-to-Pilot goal with a read-only,
sanitized reconciliation of the current-head private baseline artifacts. It
does not launch GPU work, call a provider, mutate the E2 journal, or rebind a
legacy receipt to a different candidate.

## Candidate and input

- Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Private input: `%LOCALAPPDATA%/PatentToPilot/healthtech/private-artifacts/ptp-current-head-baselines-20261103-r2/`
- Public output: `summary.json`
- Private payload policy: source file names and SHA-256 hashes only; no raw query, patent, or source text is copied into this package.

## Reproducible checks

The new standard-library summarizer reads the saved receipt, method summary,
frontier diagnostics, group results, evaluator separation record, and raw
ranking row count. The focused regression test uses a synthetic fixture and
checks that payload text is omitted, the full-method budget boundary is kept,
and the matched first-action diagnostic is retained.

The first test attempt failed because the fixture assertion matched the word
`private` in the artifact format name rather than a payload value. That failure
was retained in the work log; the assertion was narrowed to the payload marker
and the corrected test passed. The complete focused current-head selection,
including the new regression, passed `44/44` with zero failures and errors.

## Findings

- The receipt is a real current-head public development run over 3 devices, 41 patents, and 61 reference pairs with 5 methods, 15 completed ranking rows, zero provider calls, and USD0.00 paid cost.
- Full-method resource vectors are not equal: HT-B1 used 3 query calls/123 rerank pairs, HT-B2 used 9/369, and HT-B3 used 5/205. Therefore the full-method quality differences remain descriptive and do not support an equal-total-budget superiority claim.
- The observed prefix-1 first-action rows for HT-B1, HT-B2, and HT-B3 share 3 query calls and 123 rerank pairs, all have zero failed/not-realized queries, and each has Macro Recall@20 `0.49880241951853205`. This is a first-action diagnostic, not a completed adaptive-policy comparison.
- The source evaluator records 3 eligible queries and 2 shared exact-patent groups. No final holdout or semantic relevance gold is established by this reconciliation, so confidence intervals and generalization claims remain `NOT_ESTIMABLE`.

## E2 and paid boundary

The canonical E2 journal was not modified. The existing state remains four
legacy settled receipts, known legacy actual spend USD0.0001464, zero
operational/pending/unknown rows, prospective allowance USD1, and unknown
historical completeness. Paid dispatch remains blocked before reservation until
one non-secret current scoped credit/limit observation is available; this
package does not replay pending work or reset the budget/window.

## Status and next action

Status: `READY_FOR_OWNER_REVIEW_OFFLINE`, while the overall goal remains
`ACTIVE_NOT_COMPLETE_NOT_BLOCKED`.

Next action: use this sanitized resource/budget reconciliation in the manuscript
and owner review. If the paid comparison is still required, obtain the one
non-secret current scoped credit/limit snapshot, then refresh route pricing
inside the admission window and reserve only through the existing E2 journal.
