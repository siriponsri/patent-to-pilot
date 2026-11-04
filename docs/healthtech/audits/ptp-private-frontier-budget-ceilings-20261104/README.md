# Current-head private frontier budget-ceiling reconciliation

This audit records a post-hoc, descriptive reconciliation of the saved
current-head private frontier. It adds budget-ceiling slices to the existing
sanitized receipt; it does not rerun retrieval, encode vectors, call a provider,
reserve budget, or alter the canonical journal.

## Binding

- Goal: existing Patent-to-Pilot O1-O4; no new goal, budget, or time window.
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`.
- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`.
- Sanitized input: `summary.json` in this audit, derived from the saved private frontier receipt.
- Source receipt candidate: `88dc40471cb9078f929c02bb893cfa1e364da841`.

## Results

The exact equal-realized slice is 3 query calls and 123 rerank pairs:

| Method | Selected prefix | Query calls | Rerank pairs | Macro known-link Recall@20 | Failed | Not realized |
|---|---:|---:|---:|---:|---:|---:|
| HT-B1 | 1 | 3 | 123 | 0.498802 | 0 | 0 |
| HT-B2 | 1 | 3 | 123 | 0.498802 | 0 | 0 |
| HT-B3 | 1 | 3 | 123 | 0.498802 | 0 | 0 |

The at-most ceilings are:

| Ceiling | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|
| 5 / 205 | 0.498802 (3/123) | 0.498802 (3/123) | 0.224293 (5/205; 1 not-realized) |
| 6 / 246 | 0.498802 (3/123) | 0.498802 (6/246) | 0.224293 (5/205; 1 not-realized) |
| 9 / 369 | 0.498802 (3/123) | 0.568912 (9/369) | 0.224293 (5/205; 1 not-realized) |

The larger rows are sensitivity views with different realized resources. They
are not equal-budget comparisons and do not establish that adaptive acquisition
is better or worse.

## Claim boundary

The receipt covers three eligible queries, 61 product-level disclosed pairs,
two shared exact-patent groups, and no final holdout or semantic relevance gold.
Unlisted relations remain unjudged. Confidence intervals and confirmatory
adaptive-effect estimates are not estimable from this slice.

## Resource and privacy boundary

No GPU job, provider call, reservation, retry, ledger mutation, dataset
download, budget reset, or time-window reset occurred. The audit stores only
aggregates, hashes, and relative paths; raw query, patent, source, and private
credential payloads remain outside Git.

## Reproduction

The summary was produced by
`scripts/healthtech/summarize_private_frontier.py` from the already saved
private receipt. The exact source and regression hashes are recorded in
`verification.json`.

