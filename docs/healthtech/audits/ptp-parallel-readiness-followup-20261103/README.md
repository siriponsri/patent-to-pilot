# Parallel readiness follow-up — 2026-11-03

This is a continuation receipt for the original Patent-to-Pilot goal. It does
not open a new goal, budget, API key, GPU window, or scientific batch.

## Inputs and process state

- Readiness review: `C:/Users/User/Documents/Codex/2026-11-02/task/ptp-parallel-readiness-review-20261102/READINESS_REVIEW_TH.md`
- Evidence index: `C:/Users/User/Documents/Codex/2026-11-02/task/ptp-parallel-readiness-review-20261102/evidence-index.json`
- Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Candidate source head before this receipt: `612854d1e4d9b492863685af75639da47cbf335f`
- Working tree before receipt generation: clean
- Relevant experiment processes: none
- Existing SSH process: PID `31888`, started `2026-11-02 10:00:03` local time; classified as the Codex remote app-server proxy, not an experiment or GPU/API run.

## Current-head remote preflight

A second read-only inspection was performed at `2026-11-02T19:20:56Z` before
considering any next batch. No local experiment process or experiment lock was
active. On `dr-train`, the only relevant process was the existing HTTP service
PID `1745699` on port `18787`, started at `2026-10-31T08:27:48Z`, with logical
code commit `o4-http-remote`. A zero-byte GPU lock marker was present, but it
does not establish ownership or an authorized allocation. The service was not
killed, modified, relaunched, or used for a new run.

The read-only `/providers` response showed local Qwen3-8B and local PatEmbed
availability, while OpenRouter and paid dispatch remained closed with unknown
remote budget fields. This is component/service observation only. The machine-
readable receipt is [`REMOTE_PREFLIGHT_CURRENT_HEAD_20261103.json`](REMOTE_PREFLIGHT_CURRENT_HEAD_20261103.json).

## Failure-accounting finding

The reviewed implementation is already present in the candidate. The repair
was introduced by `0d092019cd7b9850f9b32988ca8a5c0f9b987eaa` and deterministic
elapsed-time coverage was strengthened by `e63e8a9d8996f805904a019579c405129171353c`.

- Action-level failures preserve the attempt already started.
- Measured wall and CPU elapsed time is retained.
- Unmeasurable fields are explicitly marked `PARTIAL_UNKNOWN`.
- Method-level failures preserve prior attempts and do not append a synthetic
  zero-cost attempt.
- Frontier diagnostics retain method-level and attempt-level failures.

No additional source edit was necessary in this continuation because the
current source already contains the requested repair. The original receipts
were not rewritten and no retrospective cost was inferred.

## Verification

- Focused package: `49 passed, 1 skipped, 1 warning` in `6.15s`.
- Full Python suite: `596 passed, 1 skipped, 2 warnings` in `29.08s`.
- Skip reason: pinned local tokenizer artifact unavailable.
- Failure-accounting JUnit: `failure-accounting-tests.xml`.
- Full-suite JUnit: `full-tests.xml`.
- Source and regression-test hashes are recorded in `verification.json`.

Historical impact remains `NONE_KNOWN` in the inspected audit receipts. This
means no affected completed round was identified; it does not prove that every
unavailable private receipt is complete.

## B2/B3/B4 budget interpretation

The frozen frontier matched corpus, eligible queries, references/groups,
encoder/reranker bundle, `K=20`, and per-call candidate/rerank depth `41/41`.
It did not match total realized retrieval budget:

| Method | Query calls | Rerank pairs | Interpretation |
|---|---:|---:|---|
| HT-B1 | 3 | 123 | one fixed query per device |
| HT-B2 | 9 | 369 | full fixed multi-query schedule |
| HT-B3 | 5 | 205 | heuristic stopping prefix |
| HT-B4 offline | 5 | 205 | deterministic controller calls plus 8 controller steps |

The evidence therefore supports a descriptive realized quality-resource
frontier only. It does not support an equal-total-budget superiority claim for
B2, B3, or B4. B4-RG and B4-DR live generation branches remain
`NOT_IMPLEMENTED`/`NOT_RUN` in the existing release receipt.

## Goal status after this package

- Engineering: `COMPLETE_FOR_FAILURE_ACCOUNTING_PACKAGE`.
- Scientific evidence: `PARTIAL`; semantic gold, equalized final budgets, and
  powered confirmatory inference remain unavailable.
- Business validation: `PARTIAL`; operational-potential proxies only, with no
  external user validation, demand, WTP, revenue, or ROI evidence.
- Manuscript readiness: `PARTIAL`; the budget and claim boundaries are aligned,
  while owner review and WPI-specific submission-detail verification remain.

No API call, GPU job, dataset download, ledger mutation, budget reset, deadline
reset, or new experiment was started by this follow-up.

Machine-readable details are in [`verification.json`](verification.json).
