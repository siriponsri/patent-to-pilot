# Business and research evidence checkpoint - 2026-11-03

Status: `PARTIAL_EVIDENCE_BOUND_OPERATIONAL_COMPLETE_RESEARCH_NOT_ESTIMABLE`.

This checkpoint aggregates existing receipts already bound to candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. It is an inspection-only
checkpoint. No model, benchmark, dataset, GPU, provider, ledger, budget, or
time-window mutation was performed while creating it.

## Engineering and operational evidence

The current-head local HTTP/vector receipt covers three named cases:
MitraClip, Tendyne, and TriClip. All three completed source inspection with
HTTP status 200, returned five evidence records, reached history version 2
through the recorded edit path, and exported JSON, Thai, and English forms at
version 2. Candidate counts were `34`, `34`, and `41`; dense candidate counts
were `33`, `33`, and `41`; vector errors were empty for all cases.

This supports `O1 COMPLETE_CURRENT_HEAD_ENGINEERING` and the three-case
application slice. Citation/locator handling and source inspection were
exercised operationally. The receipt does not establish semantic entailment,
relevance correctness, patent validity, clinical suitability, FTO, or
investment merit.

The exact-head local Qwen/Qwen3-8B guided run produced schema-valid outputs
for `3/3` cases. Prompt tokens were `3,073` total, output tokens were `1,054`
total, and generation latency averaged `38.960` seconds per case. Total run
elapsed time was `120.954` seconds, with zero provider calls and USD `0.00`
paid cost. This is a generation-contract smoke test, not a semantic quality
evaluation.

## Research evidence currently supported

The current-head offline development receipt reports:

| Method | Macro Recall@20 | Query calls | Rerank pairs | Status |
|---|---:|---:|---:|---|
| HT-B0a | 0.442739 | 3 | 0 | descriptive |
| HT-B0b | 0.662242 | 3 | 0 | descriptive |
| HT-B1 | 0.498802 | 3 | 123 | descriptive |
| HT-B2 | 0.568912 | 9 | 369 | descriptive |
| HT-B3 | 0.498802 | 5 | 205 | descriptive |
| HT-B4-offline | 0.498802 | 5 | 205 | descriptive |

The matched first-action diagnostic has three query calls and 123 rerank
pairs. HT-B1, HT-B2 prefix-1, and HT-B3 prefix-1 all have Macro Recall@20
`0.498802`, with observed range `0.0`. This is a post-hoc diagnostic only.
The realized totals of the full policies are not equal, so it does not prove
adaptive superiority under equal total budget.

The component diagnostics remain useful but bounded. PatEmbed-base reports
macro/micro Recall@100 `0.422525/0.422319` and macro nDCG@100 `0.348830`;
multilingual-e5-base reports `0.287414/0.287296` and `0.244781`. PANORAMA
component holdouts report PAR4PC validation/test hit@1 `0.733575/0.715124`,
PI4PC `0.377699/0.401235`, macro hit@8 `1.0` on all four splits, and Helmers
macro AP/AUC `0.885450/0.880012` on 10 targets and 450 judged pairs. These are
component diagnostics and are not semantic device-patent gold for the main
study.

The research status therefore remains
`O4 PARTIAL_DESCRIPTIVE_NOT_ESTIMABLE`: the available cohort is development
only, the main semantic gold/final holdout is absent, and independent group
count is insufficient for a confirmatory adaptive comparison.

## Business-value evidence boundary

Observed machine-side time is `71.983` seconds per named case, composed of a
mean local-vector HTTP time of `33.023` seconds and mean guided local-Qwen
generation time of `38.960` seconds. Human review time, GPU rate, and paid API
cost were not observed. The lower/central/upper unit-cost rows (`12.51999528`,
`50.05998583`, and `200.05998583` USD) are scenario calculations from explicit
labor and infrastructure assumptions, not measured business outcomes.

No independent user validation, customer productivity, willingness-to-pay,
revenue, ROI, or production unit-cost claim is made. The owner is running a
solo computational study, so any self-use remains developer self-evaluation.

## Paid API branch

The paired paid branch remains `BLOCKED_BEFORE_RESERVATION`. The latest
read-only metadata observation reports lifetime usage `USD0.0001464`, daily,
weekly, and monthly usage `USD0`, but history completeness is unproven, the
canonical R1 journal/registry is unavailable at the sanctioned path, and the
current scoped v2 credit snapshot is unavailable. The `.env` file was not read
or persisted in this checkpoint.

No provider call, reservation, attempt ID, retry, ledger mutation, zero ledger,
budget reset, or 24-hour window reset occurred. The two missing non-secret
inputs remain: the existing canonical R1 journal/history or sanitized
all-attempt export, and the current scoped account/key credit snapshot. Once
both exist, rebind them once and run only the bounded paired canary if every
route, rights, writer-quiescence, reservation, and price gate passes.

## Reproducibility and handoff

The machine-readable summary is `verification.json`; the short resume pointer
is `CHECKPOINT.json`, and the remaining actions are in `NEXT_ACTIONS.md`.
Source receipt hashes and byte counts are recorded in `verification.json`.
The working tree remains intentionally dirty; owner, Claude, and Luna work was
preserved and no merge or push was performed.

