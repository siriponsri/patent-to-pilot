# LOE-Bench program plan (D40)

LOE-Bench forecasts whether a first generic (ANDA) or biosimilar (351(k)) approval will occur within 12, 24 or 36 months, using only open public regulatory records. The proposed method combines a three-state (Kleene) evidence graph, a calibrated probability, abstention with referral to a human FTO evaluator, and value-of-information ordering of the next evidence item. The owner's original package is preserved in Thai under [owner-source](owner-source/) with [source hashes](owner-source/SOURCE-SHA256.txt). Code and small data are in [`loe-bench/`](../../loe-bench/).

D40 replaces the RA Pharma mandate as the active program. RA Pharma is folded in as the Thai-context layer: the program must ship a Thai-context demo that applies the triage output to the Thai market using open Thai sources.

## Evidence design (Orchestrator recommendation, owner-delegated)

The owner has no proprietary data, so every source must be open. The design below aims at the highest credible impact with the fewest avoidable reviewer objections.

| Tier | Track | Role | Why reviewers accept it |
|---|---|---|---|
| 1 | A, prospective | Primary confirmatory evidence | Predictions are hashed, tagged and timestamped before outcomes exist. No hindsight or leakage is possible. |
| 2 | C′, as-of retrospective | Confirmatory if G1 succeeds | Patent and exclusivity features come from historical Orange Book editions dated before each cutoff. |
| 3 | C, retrospective without as-of patent features | Confirmatory with disclosed exposure | Large n for statistics. The test split is exposed (see below). |
| 4 | B, biologics | Descriptive only | n is below about 100 351(k) originals. |

**Test exposure disclosure.** The owner package smoke run scored B0–B2 on the Track C test split (cutoffs from 2017). That split is recorded as **baseline-exposed**. No proposed arm (M1–M4, L1) has been scored on it. Under standing rule 1 it never selects a method. All thresholds, features and model choices are selected on a temporal validation slice of the training period. The preregistration states the exposure and the already-known baseline numbers.

**Track A clock.** t0 is the date of the first verified fresh fetch (target 28 November 2026). Freeze in two steps:

1. G3a, immediately after the fetch: S0 input snapshot with SHA-256, Git tag and receipt.
2. G3b, after preregistration and before any outcome re-fetch: hashed predictions from every preregistered arm, computed only from S0.

The earliest 12-month label is due in November 2027. The IS2 report presents Tracks C′/C and B as results, and Track A as the frozen protocol and any interim result.

**Negative-result plan.** If ΔAURC CIs include zero at both horizons, report it honestly and submit the benchmark as a data descriptor. Results remain publishable either way.

## Planner evidence (D32)

| Claim or task | Primary paper | Benchmark or competitor | Status |
|---|---|---|---|
| Abstention and AURC as the main metric | [Geifman & El-Yaniv 2017, selective classification](https://arxiv.org/abs/1705.08500); [Geifman et al. 2019, AURC](https://arxiv.org/abs/1805.08206) | B1 age-hazard table. The exposed smoke AURC is 0.0449. | External reference. Head-to-head comparison not yet run. |
| Prospective freeze as the strongest evidence | [Karger et al. 2024, ForecastBench](https://arxiv.org/abs/2409.19839) | Track A against B1 and B3 | Untested hypothesis |
| Leakage control in time splits | [Kapoor & Narayanan 2023, leakage in ML-based science](https://arxiv.org/abs/2207.07048) | Track C against C′ | Design rule |
| First generic entry prediction | [CPT 2019 first-ANDA prediction](https://doi.org/10.1002/cpt.1479); [Value in Health 2018](https://doi.org/10.1016/j.jval.2018.04.1827) | DrugPatentWatch generic-entry prediction (vendor) | External reference |
| Biosimilar entry | [CPT 2020 biosimilar vs generic onset](https://doi.org/10.1002/cpt.1981) | Track B descriptive | External reference |

The co-planner verifies and extends this table. Every paper in the [package ledger](owner-source/package-docs/10-REFERENCES-AND-EVIDENCE-LEDGER.md) was read only at abstract level, so verify full texts before citing them in a manuscript.

## Roles

| Role | Model | Scope |
|---|---|---|
| Orchestrator (Planner) | Claude Opus 5.5 | Briefs, integration, the `research/loe-bench` branch, the lane HANDOFF and MEMORY, owner reports in Thai. Only the Orchestrator manages files in `docs/owner/` (owner approval, D40). |
| Co-planner and co-reviewer | GPT-6.2 Sol, medium (Codex) | Critiques plans and preregistration, checks novelty and leakage, and reviews every executor branch before merge. It does not commit. |
| Executor | Claude Sonnet 5.5, low or medium effort | Completes one task card per session in its own worktree. |

**Executor protocol.**

- Start from `research/loe-bench`.
- Create the branch `loe/<task-id>`.
- Write only the paths listed in the card, plus `docs/loe-bench/receipts/<task-id>.md`.
- Commit with explicit paths, push the task branch, and report briefly.
- Leave the lane HANDOFF and MEMORY to the Orchestrator, who updates them at integration.
- Keep raw data outside Git at `../_private_artifacts/loe-bench/`. Record its hashes in Git.
- Use Python's standard library only. Do not use sklearn, pandas or scipy. numpy is optional.

## Dispatch board

| Wave | ID | Card | Executor | Depends on | Status |
|---|---|---|---|---|---|
| 1 | E1 | T0 + fresh openFDA fetch, MANIFEST comparison, profile, G3a S0 input freeze | Sonnet low | none | dispatched |
| 1 | E2 | T6 historical Orange Book editions (G1), as-of parser and leakage test | Sonnet medium | none | dispatched |
| 1 | E3 | T8 Purple Book open-access feasibility and monthly download | Sonnet low | none | dispatched |
| 1 | E4 | T10 dr-train LLM arm, inventory, harness and synthetic smoke (V100 only) | Sonnet medium | none | dispatched |
| 1 | E5 | Thai open-data feasibility for the Thai-context demo | Sonnet low | none | dispatched |
| 1 | CP1 | Co-planner critique of design, hypotheses and novelty | GPT-6.2 Sol medium | none | dispatched |
| 2 | — | T7 ingredient audit, T1 thresholds, T2 OPEN-conditional model, T4 power simulation (train and validation only) | Sonnet | E1, E2 | waiting |
| 2 | — | T5 preregistration draft, then co-reviewer | Sonnet, then GPT | T4 | waiting |
| G2 | — | Owner approves criteria and submits to OSF | Owner | T5 | waiting |
| 3 | — | G3b prediction freeze, T3 ablation, T9 re-score, T12 table builder, L1 arm run | Sonnet | G2 | waiting |
| 3 | — | Thai-context demo | Claude | E5, G3b | waiting |
| End | — | Owner document pack: expert review, journal check, customer discovery, OSF steps, Paper 53 venue | Orchestrator | G5 | waiting |
