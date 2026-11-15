# Paper 2 pre-check: label-free per-query router on DAPFAM dev (pre-declaration)

Status: FROZEN before any router number is computed. Written 2026-11-16 (Asia/Bangkok).
Script: [router/run_router_dev.py](router/run_router_dev.py). It refuses to run unless this file is committed and unchanged, and it refuses a second run.

## Question

Stage 1 (5 Nov 2026, [README](../../audits/ptp-org-adaptive-stage1-20261105/README.md)) found that choosing the best single action per query (an oracle that reads labels) gives strict-OUT Recall@200 0.2557, against 0.1618 for dense R2 (F\*). No fixed or per-IPC-section mix captured any of this. Can a router that never reads labels at decision time capture part of it?

## What was computed before this file

Only a sanity check (`--sanity`), which reproduced Stage 1 exactly from the hash-pinned inputs: F\* = 0.161844 and the one-action oracle = 0.255716 (n = 349 OUT-eligible dev queries). No router output, feature value or per-query statistic was looked at.

## Inputs (dev only)

- The six Stage 1 actions per query, built exactly as in `scripts/healthtech/analyze_dapfam_stage1.py`: R1 BM25, R2 dense (F\*), R3 RRF(R1, R2), Q1 RRF(functional-query dense, functional-query BM25), Q2 IPC-restricted functional dense, Q3 pseudo-document dense. Top-200 families each.
- Files are hash-checked against `inputs_sha256` in `stage1-dev-results.json` before use.
- Qrels (`qrels_all.parquet`) are used only for evaluation and for fitting on training folds. The sealed test folder is never read.

## Features (label-free, from the six Top-200 lists only)

- `ov_k(a, b)` = |Top-k(a) ∩ Top-k(b)| / k.
- `cons(a)` = mean `ov_200(a, b)` over the other non-empty actions b. An empty action (Q1 for 1 query, Q2 for 16) gets `cons = 0` and is never chosen.
- Per non-default action a: `[ov_200(a, R2), ov_50(a, R2), cons(a), cons(R2)]`.
- No scores, no qrels, no IPC of relevant targets.

## Routers (exactly three; each picks ONE action per query, so the reviewed pool stays at 200 families)

- **A. Consensus (parameter-free).** Pick the non-empty action with the highest `cons`. Ties go to R2, then the canonical order R1, R3, Q1, Q2, Q3.
- **B. Thresholded switch.** Let `gap = cons(R2) − max_{a≠R2} cons(a)`, with `best_other` the action attaining that max (ties to canonical order). Choose `best_other` if `gap < τ`, else R2.
  - τ is fitted on the training folds only. Candidates: "never switch" (−∞) plus the 0, 5, …, 100% quantiles of training `gap`.
  - Pick the τ that maximises training-fold OUT R@200; ties go to fewer switches.
- **C. Ridge gain model.** For each non-default action a, a ridge regression predicts `recall_OUT@200(a) − recall_OUT@200(R2)` from the four features.
  - Fitted on training folds only: features standardised with training mean and SD; α = 1.0; intercept = training mean.
  - Choose the action with the largest predicted gain if it is > 0, else R2.
  - An action is modelled only if it has ≥ 10 non-empty training queries.

## Evaluation

- **Cross-fitting:** 5-fold query-level, with the SAME folds as Stage 1 Amendment 1. These come from `assign_folds(first-IPC section of the 349 OUT-eligible dev queries, k = 5, seed 20261105)`. Router A has nothing to fit.
- **Queries without OUT labels:** dev queries with no strict-OUT positive are used only for the IN harm metric. They get B and C fitted on all 349 OUT-eligible queries. Their IN labels are never used in fitting.
- **Primary metric:** cross-fitted strict-OUT Recall@200 (n = 349), router − F\*.
- **Uncertainty:** paired cluster bootstrap by `component` (`split.json`), 10,000 resamples, seed 20261105. Same resampling as `paired_cluster_bootstrap`.
- **Secondary:** a query-level bootstrap, reported as descriptive only. Dev is dominated by one large component, so the component CI is expected to be wide.
- **Harm:** IN Recall@200 (n = 450), router − F\*, with a component bootstrap.
- **Also reported:**
  - share of the oracle headroom captured: (router − F\*) / (0.2557 − F\*);
  - which actions were chosen and the switch rate;
  - wins, losses and ties against F\*.

## Multiplicity

The best of three routers is selected after seeing their cross-fitted scores. To account for that choice, the GO test uses a Bonferroni-adjusted two-sided component-bootstrap interval at level 1 − 0.05/3 (98.33%) for the selected router. The 95% interval is also reported.

## GO rule (fixed now)

Best router = highest cross-fitted OUT R@200.

- **GO** iff all three hold for the best router:
  - its OUT R@200 − F\* ≥ 0.010;
  - the lower bound of its 98.33% component interval is > 0;
  - its IN R@200 − F\* ≥ −0.020.
- Otherwise **NO_GO**.

## Run discipline

- Exactly one `--run`. No added routers, features, thresholds or folds after seeing results.
- A NO_GO is reported as is.
- Per-query rows go only to `../_private_artifacts/healthtech/ptp-paper2-router-dev-20261116-v1/`.
- Public aggregates go to `router-dev-result.json` and `ROUTER-RESULT.md`.
- CPU is metered with `scripts/healthtech/meter_local_cpu.py`. 0 model calls, no downloads, no paid API.

## Known limitations (declared in advance)

- Dev is exposed: Stage 1 and later checks already used it, so this is a feasibility screen, not a confirmatory test.
- One shared-target component holds most dev OUT queries, so component-level uncertainty is large.
- Citation-based qrels are incomplete: unjudged ≠ negative.
- The router's features need all six action lists, so its compute cost is that of running every action (2 LLM calls per query). Only the reviewed pool is capped at 200.
