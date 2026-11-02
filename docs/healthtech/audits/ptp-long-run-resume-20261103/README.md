# Patent-to-Pilot long-run resume checkpoint — 2026-11-03

This checkpoint continues the existing research-product long-run goal from the
clean candidate branch `codex/patent-to-pilot-long-run-20261103`. It does not
open a new budget, API key, GPU window, or scientific holdout. The candidate is
based on `main` and the previously reviewed `codex/research-product-o1-o4-20261031`
branch; the dirty long-run, Claude, Luna, and owner worktrees were preserved.

## Candidate and process state

- Candidate HEAD: `b4bc13ccf8a9a71a8f50d16346ae1c6557bc69d0`.
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
