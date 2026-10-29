# HT-M22 source landscape screen

- Run ID: `luna-long-run-20261030-source-landscape-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Status: `PASS_OFFLINE_SOURCE_SCREENING_NOT_ADMISSIBLE`
- Parent evidence: `luna-long-run-20261030-g6-m20-integration-20261030`
- Source head at review: `991e9720e04fbf73d8ff29a0e9cf6452fbb81f1e`

## Purpose

Screen public candidates for a rights-cleared semantic device-patent judgment
source without downloading restricted payloads, treating a repository badge as
a data license, or reopening the blocked Bridge branch.

## Screened candidates

| Candidate | Pinned source | Decision | Reason |
|---|---|---|---|
| Bridge-MedDevKG | `f3990a207949f25012d1070a08ac303e140387e6` | `BLOCKED_LOCAL` | Existing audit records missing distinct data-license verification, unresolved cohort reconciliation, and absent final split rules. No payload was acquired. |
| PatSnap PatentBench | `b8e059081883fe2411c308221434842950846f8c` | `REJECTED_FOR_HT_T1_TASK_MISMATCH` | The public benchmark covers patent-query prior-art/design-FTO tasks, not named medical-device/product-to-patent relevance judgments. Its license does not cure the task mismatch. No data was downloaded. |
| Current public cohorts | Existing typed Boston/Stryker/Cook/Philips records | `DEVELOPMENT_ONLY` | Product-level disclosure relations support known-link sensitivity only; they are not independent semantic gold. |

## Decision

This bounded screen found no admissible replacement for HT-T1 semantic gold.
It narrows the blocker but does not claim an exhaustive search. The existing
review packet, 341-pair unjudged policy, and untouched holdout remain the
active intake boundary. No candidate is promoted to runtime input or evaluator
gold from this screen.

## Verification

- Bridge remote pin check: `f3990a207949f25012d1070a08ac303e140387e6`.
- PatSnap remote pin check: `b8e059081883fe2411c308221434842950846f8c`.
- Local payload acquisition: `0`.
- Provider/network calls for project execution: `0`.
- Paid cost: `USD 0.00`.
- Existing Bridge rights/cohort evidence: [`BRIDGE_RIGHTS_COHORT.md`](../../research/BRIDGE_RIGHTS_COHORT.md).
- Exact source URLs, screen scope, and decisions: `verification.json`.

## Next action

Obtain or authorize a source that is both rights-cleared for the intended use
and semantically aligned with named device–patent relevance. It must provide
explicit `relevant` / `not_relevant` labels, source revision and SHA-256,
rights/intended-use decisions, adjudicator role, exact locators, independent
company/family groups, and a predeclared untouched holdout. Then run the
existing judgment adapter without changing the frozen denominator.
