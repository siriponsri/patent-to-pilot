# G6 SciFact component integration audit

- Run ID: `luna-long-run-20261029-m9-g6-scifact-20261029`
- Date: `2026-10-29` (Asia/Bangkok)
- Status: `PASS_G6_COMPONENT_INTEGRATED`
- Scope: integrate the existing HT-T2 SciFact development result into the G6 manuscript skeleton while keeping it separate from HT-T1 device-patent association claims.
- Source commit for the manuscript/test update: `8a20e60`
- Tree state: unrelated owner artifacts were preserved; Claude UX/UI worktree was not touched.

## Outcome

The G6 skeleton now records the actual HT-T2 development denominator, release rights, prediction completeness, and component metrics: 300 claims over 5,183 corpus documents, 300 prediction rows, no missing prediction claim IDs, and abstract label-only F1 `0.203787`, abstract rationalized F1 `0.167719`, sentence-selection F1 `0.107071`, and sentence-label F1 `0.073401`.

The text explicitly states that SciFact is a separate evidence-verification component, not device-patent gold or clinical truth. Hidden/test scoring, adaptive inference, provider inference, statistical significance, user validation, and publication acceptance remain `NOT_RUN` or `NOT_VALIDATED`.

## Inputs and provenance

- G6 manuscript skeleton: `docs/healthtech/research/G6_MANUSCRIPT_METHODS_SKELETON_20261029.md`, SHA-256 `b6599849874f83f96ed65d37a9a379a8a584186396b1c7290a5d3bc68194533f`.
- HT-T2 verification: `docs/healthtech/audits/luna-long-run-20261029-ht-t2-lexical-dev-20261029/verification.json`, SHA-256 `b00543a0340761d139e0cb427781e20c669d2bcb161fa3d9f9d9891c47ee4d2e`.
- HT-T2 report: `docs/healthtech/audits/luna-long-run-20261029-ht-t2-lexical-dev-20261029/REPORT.md`, SHA-256 `67219851e2e1f8b4f6693bb59752fe24903f463af8d264b43973728a4544b4a7`.
