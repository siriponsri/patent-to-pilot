# Provenance code-review checkpoint — 2026-11-03

## Scope

This checkpoint continues the original Patent-to-Pilot O1–O4 goal on the
existing worktree. It reviews and hardens the dirty working-tree candidate
above `HEAD` `88dc40471cb9078f929c02bb893cfa1e364da841`; unrelated owner,
Claude, Luna, documentation, audit, and generated artifacts remain untouched.

The review focused on the O3 shared payload contract and the HealthTech dossier
source/reference invariants. It did not authorize a paid run, change the
OpenRouter ledger, or alter the existing GPU window.

## Change made

The candidate now fails closed when:

- an evidence row or patent candidate has no source ID;
- an evidence row points to a missing source descriptor;
- an evidence source revision differs from its source descriptor;
- a patent candidate source revision differs from its source descriptor;
- a remote payload would carry a source/candidate provenance mismatch.

The existing candidate-to-disclosed-link rule remains source-backed: a
`disclosed_link` must reference an evidence row whose kind is
`patent_disclosure`. No evaluator gold or semantic relevance claim was added.

## Verification

- Focused regression: `45 passed, 0 failed, 0 skipped`.
- Full Python suite: `616 tests, 615 passed, 0 failed, 0 errors, 1 skipped`.
- Full-suite runtime: `22.664` seconds.
- Compileall: `PASS`.
- `git diff --check`: the touched code/tests pass; the accumulated
  `memory/next-actions.md` trailing-whitespace warnings remain pre-existing
  dirty-worktree content and were not rewritten.
- JUnit receipt: [`full-tests.xml`](full-tests.xml).

## Paid and resource boundary

No provider call, reservation, attempt, retry, ledger mutation, zero ledger,
budget reset, time-window reset, GPU job, or dataset download occurred in this
checkpoint. The OpenRouter branch remains
`BLOCKED_BEFORE_RESERVATION` because the existing canonical R1 journal/history
and current scoped v2 account/key credit snapshot are still unavailable.
The observed lifetime usage `$0.0001464` is metadata only; it is not treated as
account balance or complete R1 history.

## Review disposition

Specification findings addressed: source/candidate provenance could previously
drift from the reviewed descriptor; the new checks cover that boundary with
regression tests.

Standards disposition: no unrelated refactor or formatting normalization was
introduced. The candidate remains dirty and has not been committed, pushed,
merged, or approved for release. This checkpoint is `READY_FOR_OWNER_REVIEW`,
not merge approval.

## Next action

Continue local/offline work independently. If the owner supplies the two
existing non-secret paid-gate evidence items, reconcile them once, recheck
route/price/rights/writer-quiescence and reservation, then run one paired
canary only if every gate passes. Otherwise keep paid dispatch closed and
preserve this checkpoint.
