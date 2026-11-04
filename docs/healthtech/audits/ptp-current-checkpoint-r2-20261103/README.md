# Patent-to-Pilot current checkpoint R2 — 2026-11-03

Status: `PARTIAL_ENGINEERING_VERIFIED_API_BLOCKED`

This checkpoint continues the original Patent-to-Pilot goal on the existing
dirty candidate. It does not open a new goal, rerun the frozen benchmark, or
combine results from another candidate.

## Candidate

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Owner/Claude/Luna dirty work: preserved

## Completed in this checkpoint

- Repaired five historical audit links in `docs/healthtech/long-runs/README.md`;
  all selected Markdown links now resolve.
- Re-verified the solo computational-study boundary: no participant route,
  recruitment, consent collection, independent user validation, revenue,
  willingness-to-pay, or ROI gate is active for this round.
- Added an explicit manuscript Discussion section that interprets the current
  evidence without converting descriptive results into superiority claims.
- Re-ran current-candidate regression coverage with raw JUnit receipts beside
  this file.

## Verification

- Full suite: `617 tests`, `616 passed`, `1 skipped`, `0 failures`, `0 errors`,
  exit `0`.
- Focused O3/O4/local/vector/generation suite: `85 passed`, `0 skipped`,
  `0 failures`, `0 errors`, exit `0`.
- `compileall`: PASS.
- Selected Markdown link check: PASS, `0 missing`.
- Scoped `git diff --check`: PASS.
- Manuscript figure/table binding: PASS. The current-head Recall@20 figure,
  realized retrieval-units figure, frontier table, and figure manifest exist;
  the manifest binds them to the same candidate HEAD and frozen protocol.

These are engineering/documentation checks only. No new retrieval metric,
semantic gold result, holdout result, paid generation result, or business
validation result was created in this checkpoint.

## API decision

Paid OpenRouter work remains `BLOCKED_BEFORE_RESERVATION`. The existing
read-only metadata receipt still reports lifetime usage `USD0.0001464`, daily,
weekly, and monthly usage `USD0`, and an ordinary non-management key. That is
not a scoped-credit snapshot and does not prove complete R1 history.

The two missing non-secret owner evidence items remain:

1. Existing canonical R1 journal/registry, or an owner-sanctioned sanitized
   all-attempt export suitable for `inspect_r1_history_export.py`.
2. Current scoped account/key credit snapshot through an authorized channel.

The owner-supplied `.env` path was not copied, printed, or persisted in this
checkpoint. No provider call, reservation, attempt, retry, ledger mutation,
zero ledger, budget reset, time-window reset, GPU job, or dataset download
occurred.

A bounded current-worktree recheck of the preserved history found only two
legacy provider-pilot journals. Both are explicitly `r1_compatible=false` and
the registration probe rejected them fail-closed; their aggregate
`USD0.0001464` correspondence with key usage does not prove R1 completeness or
current credit. Details are in [`ptp-r1-history-recheck-20261103`](../ptp-r1-history-recheck-20261103/README.md).

## Resume

When the two evidence items arrive, inspect and reconcile them against the
same canonical R1 ledger, recheck route/price/rights/pending/allocation and
writer quiescence, then run one small paired canary only if every live gate
passes. Until then, continue local/offline and manuscript work independently.

Engineering is current-head verified; scientific evidence remains descriptive
and partial; external business validation remains `NOT_RUN`; manuscript and
WPI submission remain owner-review items.
