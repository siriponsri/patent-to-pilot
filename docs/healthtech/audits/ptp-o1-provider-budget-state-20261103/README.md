# O1 provider and budget state checkpoint - 2026-11-03

Status: `PASS_CURRENT_WORKTREE_HTTP_PROVIDER_BUDGET_VISIBILITY_REVIEW_REQUIRED`.

This package records a scoped O1 repair on top of candidate HEAD
`88dc40471cb9078f929c02bb893cfa1e364da841`. The working tree remains dirty;
the repair is intentionally recorded as an uncommitted source/test patch and
must be retested after any scoped commit or merge.

## Change

The loopback HTTP provider catalog now exposes `estimated_usd` and an explicit
`estimate_basis` for local, vector, generation, and OpenRouter providers. It
also exposes the paid `budget_gate` estimate, actual, reserved, and
unknown/pending fields. Local providers report a measured non-billable zero;
OpenRouter reports unavailable values and remains fail-closed until route,
price, ledger, and authorization gates are reconciled.

The browser backend panel now displays provider availability, model, estimate,
billing status, actual USD, reserved USD, unknown/pending USD, and the paid
dispatch gate. The OpenRouter option remains disabled in the current server
configuration. No credential is exposed to the browser.

## Verification

- Python HTTP contract suite: `7 passed, 0 failed`.
- Frontend unit suite: `74 passed, 0 failed`.
- Browser loopback HTTP acceptance: `PASS_BROWSER_HTTP_BACKEND_HISTORY_EXPORT`.
- Browser assertions included provider-state rendering, disabled OpenRouter,
  and `paid_dispatch=closed`, in addition to source inspection, cancel,
  resume, edit/history, reopen, and JSON/TH/EN export.
- Python `compileall`: PASS.
- Scoped `git diff --check`: PASS.

The browser receipt is still an engineering result. It does not establish a
paid API comparison, semantic retrieval quality, market validation, or
commercial cost outcome.

## Resource and ownership boundary

This repair made no provider call, reservation, attempt, retry, GPU job,
dataset download, ledger mutation, budget reset, or time-window reset. The
existing owner/Claude/Luna work remains in place. No commit, push, merge, or
branch deletion was performed.

## Next action

Review and stage only the seven files listed in `verification.json` when the
owner accepts this scoped O1 repair. Commit/push and rerun the same backend,
frontend, browser, compile, and diff checks at the new exact commit before
claiming current-HEAD O1 acceptance. Keep O3 paid/API and O4 scientific
limitations unchanged.

