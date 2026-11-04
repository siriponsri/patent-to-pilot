# Patent-to-Pilot current-head offline frontier — 2026-11-03

This package continues the original Patent-to-Pilot O1–O4 goal. It records a
fresh offline rerun on candidate `88dc40471cb9078f929c02bb893cfa1e364da841`
after the Pepo readiness review. The paid/API branch was not opened, no ledger
was created or mutated, and no historical receipt was rewritten.

The run uses the existing frozen Abbott development cohort, the existing local
MiniLM encoder/reranker bundle, `candidate_depth=41`, `rerank_depth=41`, and
`K=20`. Raw outputs remain in the private artifact store identified in
`verification.json`; this repository package contains only sanitized results,
hashes, commands, and claim boundaries.

Status: `PASS_CURRENT_HEAD_OFFLINE_DESCRIPTIVE_FRONTIER`

Read next:

- `verification.json` for machine-readable commands, hashes, and results.
- `CHECKPOINT.json` for G0–G8 and O1–O4 disposition.
- `REPORT_TH.md` for the Thai handoff and limitations.
- `analysis-current-head-20261103/` for current-candidate development-only
  figures and the CSV/manifest used by the manuscript. These artifacts are
  descriptive and do not imply a final holdout, semantic gold, or equal-total-
  budget superiority claim. `renderer-tests.xml` records the fresh current-
  candidate regression pass (`615` tests, `614` passed, `1` skipped).
