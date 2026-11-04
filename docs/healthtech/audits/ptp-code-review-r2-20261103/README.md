# Current-head source patch review r2 — 2026-11-03

## Review boundary

This is a serial code-review pass over the current dirty candidate above HEAD
`88dc40471cb9078f929c02bb893cfa1e364da841`. It covers the goal-specific
source/test patch inventoried in
[`ptp-source-patch-inventory-20261103`](../ptp-source-patch-inventory-20261103/README.md),
including provenance checks, rights-cleared payload construction, canonical E2
ledger binding, local GPU-window/slot guards, vector verification, and their
regressions. Owner/Claude/Luna and unrelated documentation/audit changes remain
untouched.

The review is not independent of the implementation author. It is therefore a
candidate-bound pre-owner review, not merge approval.

## Specification axis

No new specification finding was found in this pass. The inspected candidate
continues to fail closed for source/candidate revision drift, missing source
descriptors, non-rights-cleared model-visible fields, route substitution,
duplicate attempt IDs, pending/unknown billing, alternate canonical ledgers,
GPU-window violations, and shared-slot conflicts. Existing focused tests cover
these boundaries, and the current full suite exercises the integrated source
patch.

The `disclosed_link` rule remains source-backed by `patent_disclosure` evidence;
retrieved candidates, evaluator labels, semantic gold, and unjudged pairs are
not promoted by the patch.

## Standards axis

No unrelated refactor, formatting normalization, secret handling change, or
external side effect was introduced by this review. The candidate remains
intentionally dirty and no commit, push, merge, release tag, paid request, GPU
job, or dataset download was performed.

## Verification

- Full Python suite: `642 total; 640 passed; 0 failed; 0 errors; 2 skipped`.
- JUnit: `full-tests.xml`.
- JUnit SHA-256: `35abe40008571a877b23194024c1151023f8e7462bf932a2cc875a4ab4277852`.
- `compileall`: PASS.
- `git diff --check`: PASS; pre-existing CRLF warnings remain in dirty documentation files.
- Skips: native DuckDB integration requires `PTP_TEST_DUCKDB`; the pinned local tokenizer artifact is unavailable.

The test receipt belongs to the exact current dirty candidate and is not pooled
with historical clean-release or older-candidate receipts.

## Paid/resource boundary

The canonical E2 journal remains outside the repository at
`%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`.
No provider call, reservation, attempt, retry, ledger mutation, budget reset,
time-window reset, or GPU job occurred during this review. Paid dispatch remains
`BLOCKED_BEFORE_RESERVATION` until one non-secret current scoped credit/limit
snapshot or sanctioned pointer is available; route pricing must then be
refreshed inside the runner admission window.

## Disposition

`READY_FOR_OWNER_REVIEW_NOT_MERGE`.

Owner review is still required before staging or committing the scoped patch.
The research goal remains open because scientific evidence is descriptive and
not estimable for adaptive superiority, external business validation was not
run, the WPI Guide for Authors still needs an authorized live recheck, and the
paid local/API comparison has not been dispatched.
