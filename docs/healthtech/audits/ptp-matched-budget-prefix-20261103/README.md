# Matched-budget prefix diagnostic — 2026-11-03

This package adds a reproducible post-hoc analysis to the original
Patent-to-Pilot goal. It consumes the existing private O4 frontier receipt and
does not rerun retrieval, download data, start a GPU job, call an API, or alter
the ledger.

## Source and provenance

- Source receipt: `C:/Users/User/Documents/Codex/2026-10-31/task/ptp-o4-matched-20261101/abbott-baselines/frontier_diagnostics.json`
- Source receipt SHA-256: `5bbccccb10ae21679679efc29041cc00ec52581bda1bbb50a983c97f90626647`
- Source run candidate: `891f3b3`, as recorded by the companion baseline receipt
- Cohort: Abbott development slice, 3 devices, 41 patents, 61 disclosed pairs
- Analysis script: `scripts/healthtech/analyze_matched_budget_prefix.py`

## Result

The selected budget is exactly 3 query calls and 123 rerank pairs. The slice
contains the first action of HT-B1, HT-B2, and HT-B3:

| Condition | Prefix | Query calls | Rerank pairs | Macro Recall@20 |
|---|---:|---:|---:|---:|
| HT-B1 | 1 | 3 | 123 | 0.498802 |
| HT-B2 | 1 | 3 | 123 | 0.498802 |
| HT-B3 | 1 | 3 | 123 | 0.498802 |

All selected rows have zero failed and zero not-realized queries. The observed
range is `0.0`.

## Interpretation boundary

This is a post-hoc descriptive first-action budget control, not a preregistered
final endpoint. It does not evaluate the completed adaptive behavior of HT-B3
and does not establish adaptive superiority. HT-B4 is excluded because its
controller-step count is not interchangeable with query/rerank units and the
existing receipt does not expose a predeclared same-unit final slice. The
source has no final holdout and uses product-level disclosed links rather than
semantic relevance gold.

The machine-readable result is in [`verification.json`](verification.json).
The manuscript update is in
[`MANUSCRIPT_ADAPTIVE_EVIDENCE_ACQUISITION_EN.md`](../../research/MANUSCRIPT_ADAPTIVE_EVIDENCE_ACQUISITION_EN.md).

## Verification

- New analysis tests: `2 passed`.
- Full Python suite after the change: `598 passed, 1 skipped, 2 warnings`.
- The optional skip is the existing unavailable pinned local tokenizer artifact.
- No paid/API/GPU/dataset/ledger mutation occurred.
