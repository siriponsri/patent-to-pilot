# Patent-to-Pilot completion audit R4 - 2026-11-03

This additive audit checks the original Patent-to-Pilot O1-O4 objective and
the attached long-run requirements against the current candidate. It does not
replace earlier receipts, merge heads, or convert a conditional/diagnostic
result into a completion claim.

## Candidate boundary

- Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Candidate branch: `codex/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Root `main` HEAD: `0d049802d36bc2eebe60331ec444d62469fd767f`
- Candidate working tree: dirty; Claude/Luna/owner changes preserved
- Root merge: not done

## Decision

Overall status remains `PARTIAL_NOT_COMPLETE`.

The current evidence is strong enough for an owner-review candidate and a
reproducible computational manuscript draft, but not for the requested final
state. O1 engineering is complete. O2 is accepted as a current-head runtime
binding of actual prior remote artifacts without claiming a new remote run. O3
has local generation and API payload preflight, but paid paired generation is
blocked before reservation. O4 has three-case engineering and descriptive
offline research, but no authorized current-head final holdout or powered
equal-total-budget adaptive result.

## Requirement-level result

| Requirement | Status | Evidence boundary |
|---|---|---|
| UI -> HTTP jobs/history/source inspection/edit/reopen/export | COMPLETE | Current-head O1 and local HTTP/vector receipts; engineering only |
| PatEmbed/e5 resumable remote artifacts, Windows import, shared retrieval use | COMPLETE_WITHOUT_RERUN | Prior actual remote receipt, current-head rebind, vector integrity revalidation |
| Local Qwen3-8B generation on frozen evidence | COMPLETE_ENGINEERING | Current-head 3/3 guided schema-valid cases; semantic quality not proven |
| API qwen/qwen3-32b paired generation | BLOCKED_BEFORE_RESERVATION | Rights/schema preflight 3/3; canonical R1 journal and scoped credit absent |
| Three real-device E2E cases | COMPLETE_ENGINEERING | 3/3 source inspection/history/export workflow cases |
| Adaptive vs fixed/multi-query/heuristic research | PARTIAL_DESCRIPTIVE | Current frontier and post-hoc prefix slice; no final holdout/equal total budget |
| Business value evidence | PARTIAL_SCENARIO_ONLY | Observed machine time plus explicit sensitivity assumptions; no external validation |
| Manuscript and WPI preparation | PARTIAL_OWNER_REVIEW | Draft, references, checklist and declarations prepared; guide/owner review/submission pending |
| Canonical shared ledger and paid accounting | BLOCKED_EXTERNAL_EVIDENCE | Known canonical registry/journals absent; no replacement ledger allowed |
| Tested commit/push/merge/cleanup | NOT_RUN | Owner review and candidate-bound acceptance required before merge/delete |

## Current quantitative evidence

- PatEmbed macro/micro Recall@100: `0.422525 / 0.422319`
- multilingual-e5 macro/micro Recall@100: `0.287414 / 0.287296`
- Current-head matched-budget prefix-1 Macro Recall@20 for B1/B2/B3:
  `0.498802` each; adaptive superiority `NOT_ESTABLISHED`
- Current local-vector mean: `33.023` seconds per case
- Current guided local Qwen mean: `38.960` seconds per case
- Combined observed machine time: `71.983` seconds per case
- Business-value scenario: lower/central/upper illustrative unit costs
  `USD12.52 / USD50.06 / USD200.06`; not observed commercial outcomes
- Current full candidate suite: `615 total; 614 passed; 0 failed; 1 skipped`

## Paid gate

The owner has conditional permission to continue OpenRouter in parallel when
all elements are ready. The latest read-only metadata observation still shows
lifetime key usage `USD0.0001464`, daily/weekly/monthly usage `USD0`, an
ordinary non-management key, unreconciled account scope, unproven history
completeness, and no scoped credit snapshot. This is not enough to reserve or
dispatch paid work.

No provider call, reservation, attempt, retry, ledger mutation, zero ledger,
budget reset, time-window reset, GPU job, dataset download, submission, merge,
or branch deletion occurred in this audit.

## Handoff

Keep the goal active and the candidate isolated. The shortest external step is
to provide the existing canonical R1 journal or sanctioned sanitized export and
the current scoped account/key credit snapshot once, without a secret. Then
validate the export, bind the existing ledger, recheck route/price/rights and
writer quiescence, and run only one small paired canary before any batch.
Continue owner manuscript review and offline work independently.
