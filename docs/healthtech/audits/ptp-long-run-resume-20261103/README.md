# Patent-to-Pilot long-run resume checkpoint — 2026-11-03

This checkpoint continues the existing research-product long-run goal from the
clean candidate branch `codex/patent-to-pilot-long-run-20261103`. It does not
open a new budget, API key, GPU window, or scientific holdout. The candidate is
based on `main` and the previously reviewed `codex/research-product-o1-o4-20261031`
branch; the dirty long-run, Claude, Luna, and owner worktrees were preserved.

## Candidate and process state

- Runtime-tested code/test/receipt head for this continuation: `e63e8a9d8996f805904a019579c405129171353c`.
- The final checkpoint update after this package is documentation-only; it does
  not change the runtime-tested source or test result.
- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`.
- Base relationship: `main` at `0d049802d36bc2eebe60331ec444d62469fd767f` is an ancestor.
- The only SSH process observed was the Codex remote app-server proxy; no
  baseline, Qwen, embedding, generation, GPU, or dataset runner was active.
- No credentials, `.env`, private journal, restricted payload, or model weight
  was read or staged.

## Current verification

- Python focused HealthTech/O1-O4 contracts: exit `0`.
- Full Python suite: exit `0`; one optional tokenizer skip and warnings only.
- Frontend unit suite: `74 passed, 0 failed`.
- Loopback HTTP integration: PASS for job submit/status, source inspection,
  history edit/reopen, and JSON/TH/EN export; provider calls `0`, paid cost
  `USD 0.00`.
- `compileall`: PASS.
- `git diff --check`: PASS.
- Named Abbott browser integration: `BLOCKED_ASSET_GATED` before execution
  because `HEALTHTECH_ABBOTT_COHORT` and its permitted rights/vector inputs are
  absent from this clean candidate. No synthetic fixture was promoted to a
  real-case result.

## Outcome status

| Outcome | Status | Evidence boundary |
|---|---|---|
| O1 | `PASS_CURRENT_HEAD_LOOPBACK_ENGINEERING` | Current candidate passes real loopback HTTP job/history/export integration. |
| O2 | `PARTIAL_PRIOR_REMOTE_RUNTIME_NOT_RERUN` | Prior PatEmbed/e5 remote shards and imports are preserved receipts; no new remote run is allowed after the original 24-hour window. |
| O3 | `PARTIAL_LOCAL_PASS_API_BLOCKED_LOCAL` | Prior local Qwen3-8B receipt is 3/3 schema-valid; API remains closed pending canonical R1/current credit/rights/route evidence. |
| O4 | `PARTIAL_REAL_CASE_RECEIPT_NOT_EXACT_HEAD` | Prior three-case receipt exists, but relevant HTTP/generation code changed afterward; current exact-head loopback is verified while the permitted real-case pack is absent. |

The scientific comparison remains descriptive rather than confirmatory. Product
disclosure links are not semantic device-patent gold, unlisted pairs remain
unjudged, and no external user, revenue, ROI, willingness-to-pay, clinical,
FTO, or journal-acceptance claim is made.

## Resource accounting

This resume check started no paid request, remote job, model/dataset download,
ledger mutation, reservation, or new 24-hour window. Paid API remains bounded
by the original cumulative USD8 authorization and the existing canonical ledger;
the missing current evidence blocks only that branch. The approved GPU window
is treated as expired for new work rather than reset.

## Next action

Continue offline engineering and manuscript/reproducibility work. For O4 exact-
head real-case rerun, use only an already authorized cohort, rights matrix,
vector bundle, and model/runtime manifest when the owner exposes those specific
paths. For O3 API, reconcile the existing canonical R1 history, current credit,
  outbound prompt rights, and route/pricing binding through the permitted channel;
  do not ask for the USD8 approval again and do not create a replacement ledger.

## Readiness review follow-up — 2026-11-03

The parallel readiness review at
`C:/Users/User/Documents/Codex/2026-11-02/task/ptp-parallel-readiness-review-20261102/`
was read before this checkpoint. Its two actionable findings were handled as
an offline engineering/documentation package; no baseline, GPU, API, dataset,
ledger, or new 24-hour run was started.

### Failure accounting repair

`scripts/healthtech/run_real_baselines.py` now carries one execution state per
method. An unexpected method-level exception preserves completed/failed
attempts, records measured method wall/CPU time, and avoids appending a
synthetic attempt. Action-level failures retain measured elapsed time and mark
unavailable fields (`returned_candidates`, `rerank_pairs`, embedding/rerank
tokens) as `PARTIAL_UNKNOWN` instead of writing zero values. Frontier errors
also include method-level failures, so a partial run remains visible to the
evaluator and report layer.

The focused regression package is in
`tests/test_healthtech_real_baselines.py`. The current candidate passed the
targeted baseline/analysis/report/controller/cross-cohort suite (`49 passed,
1 skipped`) and the failure regression now uses deterministic clock ticks to
prove that failed attempts retain measured wall/CPU elapsed time rather than
literal zero values. The package also passed `compileall` and `git diff
--check`; the full Python suite exited `0` with one optional tokenizer skip and
warnings only.

Historical impact was checked without rewriting artifacts: no tracked
`run_real_baselines.py` receipt in the current candidate has a non-zero
`failed_query_count`, `error_count`, or `failed_device_count`. The affected
rounds are therefore `NONE_KNOWN`; this repair is prospective. Historical
zero-failure receipts and all recorded costs remain unchanged. No retrospective
cost is inferred from the old handler.

### Budget interpretation for B2/B3/B4

The 1 November frontier used the same frozen corpus, eligible queries,
references/groups, encoder/reranker bundle, K=20, and candidate/rerank depth
`41/41`. That is matched evidence access and per-call configuration, not a
matched total budget. The realized retrieval units were:

| Method | Query calls | Rerank pairs | Budget interpretation |
|---|---:|---:|---|
| HT-B1 | 3 | 123 | one fixed query per device |
| HT-B2 | 9 | 369 | full fixed multi-query schedule |
| HT-B3 | 5 | 205 | heuristic stopping prefix |
| HT-B4 offline | 5 | 205 | deterministic controller retrieval calls; 8 separate controller steps |

Accordingly, the package is a descriptive realized quality-resource frontier.
It is not evidence of equal-total-budget superiority for B2, B3, or B4, and the
manuscript now states that boundary. The original receipts remain immutable;
the current audit is the canonical interpretation for the continuation.

### Checkpoint status

- Engineering: `COMPLETE_FOR_FAILURE-ACCOUNTING-PACKAGE`; current O1 loopback and prior engineering receipts remain separately bound.
- Scientific evidence: `PARTIAL`; the frozen frontier is descriptive, total budgets are not equalized, semantic gold and powered confirmatory inference remain unavailable.
- Business validation: `PARTIAL`; operational-potential proxies only; no external user, demand, WTP, revenue, or ROI evidence.
- Manuscript readiness: `PARTIAL`; claim boundary and budget interpretation were corrected, while WPI-specific submission details and owner review remain open.

The paid/API and new compute branches remain gated by the existing canonical
evidence. This checkpoint does not request the prior USD8 authorization again,
reset any ledger/window, or add AI4AI as a goal condition.

## Exact-head verification follow-up — 2026-11-03

The runtime-tested continuation candidate is
`e63e8a9d8996f805904a019579c405129171353c` on the same branch and worktree.
The subsequent checkpoint edit is documentation-only. No experiment, provider
call, GPU job, dataset download, ledger mutation, or participant route was
started.

Fresh checks on this exact HEAD:

- Targeted failure-accounting/frontier/controller/report package: `49 passed,
  1 skipped` (the skip is the unavailable pinned local tokenizer artifact).
- Full Python suite: `596 passed, 1 skipped, 2 warnings`.
- O2 transformer/vector contract and evaluator suite: `17 passed`; the O2
  runtime paths have no source diff from the candidate bound to the prior full
  PatEmbed/e5 encode, import, and DAPFAM evaluation receipts. This is a
  current-head contract rebind, not a second remote encoding run.
- Guarded offline verification: the first attempt is retained as a failure
  receipt (`597` tests, `13` failures, `3` errors) because the verifier denied
  loopback HTTP and used a path-sensitive basetemp. The verifier was repaired
  to allow only loopback sockets and to use a short-lived system-temp basetemp;
  the r2 rerun passed `597` tests with `0` failures, `0` errors, `1` optional
  skip, `0` blocked network attempts, and `0` credential reads. After the
  deterministic failure-accounting regression was tightened, r3 reproduced
  the same `597/0/0/1` result on code head `e63e8a9`.
- Frontend unit suite: `74 passed, 0 failed`.
- Loopback HTTP integration: `PASS_BROWSER_HTTP_BACKEND_HISTORY_EXPORT`, with
  source inspection, history `1 -> 2`, edit/reopen, JSON/TH/EN export, zero
  provider calls, and paid cost `USD 0.00`.
- `compileall`, JSON parsing, and `git diff --check`: pass.

This revalidation strengthens the engineering and failure-accounting evidence
only. It does not create a new scientific batch, convert the descriptive
frontier into an equal-total-budget comparison, or change the existing O2/O3/O4
external gates. The exact-head real-case rerun remains asset-gated; the API
branch remains fail-closed pending the existing canonical journal, credit,
route/pricing, and outbound-rights evidence.

O2 is therefore `PASS_PRIOR_RUNTIME_CURRENT_HEAD_CONTRACTS_PASS`: the prior
remote artifacts remain authoritative for the completed encode/import/evaluation
work, while a new remote rerun is `NOT_RUN_EXPIRED_24H_WINDOW`. O3 local
generation and O4 real-case receipts are not promoted in the same way because
their relevant generation/HTTP source paths changed after their prior runs.

The guarded verification receipts are retained under
[`offline-verification-20261103-r2`](./offline-verification-20261103-r2/),
[`offline-verification-20261103-r3`](./offline-verification-20261103-r3/),
and the failed first attempt under
[`offline-verification-20261103`](./offline-verification-20261103/). This is
current-checkout offline reproducibility evidence; it is not a fresh install
or independent deployment validation.

The machine-readable current-head record is
[`CHECKPOINT_CURRENT_HEAD.json`](./CHECKPOINT_CURRENT_HEAD.json).
