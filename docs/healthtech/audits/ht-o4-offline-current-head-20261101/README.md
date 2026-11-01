# O4 offline adaptive current-head revalidation — 2026-11-01

Status: `PASS_CURRENT_HEAD_OFFLINE_ADAPTIVE_REVALIDATION_O3_BLOCKED_LOCAL`

This package continues the existing Patent-to-Pilot O1-O4 goal. It reruns the
deterministic offline HT-B4 controller on the already frozen Abbott and Boston
public disclosure cohorts using the current candidate code. It does not create
a new goal, change the cohort, change K/max-steps, use evaluator labels during
runtime, or open the paid/API branch.

## Current candidate and inputs

- Candidate branch: `codex/research-product-o1-o4-20261031`
- Candidate HEAD: `94ce5b10f7b787677ebd11d8c3f193753e4b7d8c`
- Runner: `scripts/healthtech/run_bounded_controller.py`
- Controller: `src/patent_to_pilot/healthtech/controller.py`
- Historical frozen cohorts: Abbott `ht-public-cohort-20261029-frozen-r1` and Boston `ht-boston-watchman-20261028-r4`
- Shared local model bundle: existing MiniLM ONNX files from the root research artifacts; no model download or re-embedding
- Runtime/evaluator separation: runtime predictions and raw rankings are written before evaluator references are loaded

## Results

| Cohort | Devices | Macro Recall@20 | Micro Recall@20 | Query calls | Rerank pairs | Failed devices | Paid cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Abbott | 3 | 0.498802 | 0.475410 | 5 | 205 | 0 | USD0.00 |
| Boston | 2 | 1.000000 | 1.000000 | 2 | 14 | 0 | USD0.00 |

The Abbott group diagnostics are `MitraClip/TriClip = 0.3364389` and
`Tendyne = 0.8235294`. Boston is ceiling-limited because K=20 exceeds its
seven-patent candidate universe. The two cohorts are development/descriptive
views with insufficient independent groups for generalization uncertainty.

## Interpretation boundary

The rerun confirms reproducibility of the deterministic offline controller and
its accounting path on the current candidate. It does not establish adaptive
superiority, semantic claim relevance, exhaustive recall, legal/FTO validity,
clinical suitability, investment merit, or business value. Product-level
disclosed links remain distinct from retrieved candidates and unjudged pairs.
The live Qwen3-32B/API comparison remains gated on the canonical journal,
current credit, route/pricing, transfer-rights and writer-quiescence evidence.

Raw rankings, runtime predictions, evaluator validation, receipts and failures
are retained outside Git at the logical private root
`permitted-local-storage:healthtech/o4-offline-current-head-20261101`. The
tracked checkpoint stores hashes and sanitized summaries only.

