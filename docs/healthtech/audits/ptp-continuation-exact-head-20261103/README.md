# Patent-to-Pilot exact-head continuation checkpoint — 2026-11-03

This package continues the existing O1–O4 goal and binds the current outcome
state to the same dirty candidate HEAD. It does not start a new goal, rerun a
paid request, rerun the frozen offline benchmark, or pool historical and
current-candidate results.

## Exact-head disposition

| Outcome | Current disposition | Evidence boundary |
|---|---|---|
| O1 | `COMPLETE_CURRENT_HEAD_ENGINEERING` | Browser-to-loopback HTTP source inspection, history/edit/reopen, and JSON/TH/EN export passed on the current candidate. |
| O2 | `PARTIAL_PRIOR_REMOTE_ARTIFACT_BOUND_NEW_ENCODE_NOT_RUN` | Prior PatEmbed/e5 remote artifacts hash-reconciled to private local bundles; no new `dr-train` allocation reference was observed, so no new encode is claimed. |
| O3 | `PARTIAL_LOCAL_PASS_API_BLOCKED` | Local Qwen3-8B completed 3/3 frozen cases with schema-valid outputs; current-head API dry-run passed, but paid generation remains gated before reservation. |
| O4 | `PARTIAL_ENGINEERING_DESCRIPTIVE_RESEARCH_NOT_ESTIMABLE` | Three named cases are operationally covered and the current-head offline frontier is recorded; no semantic gold, final holdout, equal-total-budget comparison, or external validation is claimed. |

## Current offline frontier

The exact-head development receipt records macro Recall@20 of `0.442739`
(HT-B0a), `0.662242` (HT-B0b), `0.498802` (HT-B1), `0.568912` (HT-B2),
`0.498802` (HT-B3), and `0.498802` for offline HT-B4. HT-B4 micro Recall@20
is `0.475410` with eight controller steps. Realized query/rerank budgets are
not equal across the full frontier; the post-hoc first-action slice ties
HT-B1, HT-B2-prefix-1, and HT-B3-prefix-1 at `0.498802`.

These are development-only descriptive results over product-level disclosed
links. They do not establish semantic relevance, exhaustive recall, adaptive
superiority, revenue, ROI, willingness-to-pay, or independent user validation.

## Remaining external gates

- O2 new remote encode: needs an authorized allocation reference/window; idle
  GPU visibility is not sufficient.
- O3 paid branch: needs the existing canonical R1 journal/export and a current
  scoped credit snapshot. The owner authorization is reused; no USD8 approval
  is requested again.

No provider call, reservation, attempt, retry, ledger mutation, zero ledger,
budget reset, time-window reset, GPU job, or dataset download was created by
this checkpoint. Resume from `verification.json` and `CHECKPOINT.json`.
