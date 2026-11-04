# Manuscript MCP credit-evidence rebind

Date: 2026-11-04 (Asia/Bangkok)

## Scope

This is a documentation-only rebind on the existing Patent-to-Pilot
candidate. It updates the paid-evidence boundary to reflect the new
account-level OpenRouter MCP observation and E2 reconciliation. It does not
change metrics, cohorts, model configurations, endpoints, project budget,
ledger history, or scientific claims.

Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`

## Changes

The manuscript now states that:

- OpenRouter MCP `get-credits` returned account-level `total_credits=10` and
  `total_usage=0.0001464`.
- The usage matches four legacy settled E2 receipts and zero operational
  attempt/context rows.
- The response did not provide the `.env` dispatch key's exact remaining
  limit, key scope, or response timestamp.
- The owner-supplied `USD30` MCP cap is a separate provider-key setting and is
  not treated as project spend authorization.
- Paid API dispatch remains unrun and blocked before reservation.

The manuscript continues to distinguish account credit from key-level
admission and does not claim a live model comparison, adaptive superiority,
business validation, revenue, ROI, or journal acceptance.

## Verification

- Manuscript SHA-256: `A99155A5013899036A19E1DC6F1E34DE96F8CC6237D98E44EF5FF876BD58D4AF`
- Manuscript bytes: `76764`
- Relative links checked: `76`
- Missing relative links: `0`
- Targeted stale-credit phrase check: `0` matches
- `git diff --check`: `PASS`
- Code/tests: `NOT_RUN` because this package changes documentation only

No provider call, reservation, retry, GPU job, dataset download, ledger
mutation, budget reset, or time-window reset occurred.

