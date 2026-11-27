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

## CP1 co-planner review, adopted 27 November 2026

GPT-6.2 Sol (medium, read-only, commit 5f34a509) reviewed the design and code. Its full review text is in the CP1 child thread. The Orchestrator adopted these changes:

1. **Evidence roles.** Track C (current-snapshot retrospective) becomes exploratory only. Track C′ (as-of historical Orange Book editions) is the IS2 confirmatory set, but only if it passes a coverage gate. The gate counts separable train, calibration and test periods and the number of drug groups with events. Track A becomes the prospective replication. If C′ fails the gate, IS2 reports benchmark feasibility together with the frozen protocol.
2. **Single primary endpoint.** Paired ΔAURC = AURC(M3) − AURC(M1) at 24 months on C′, computed on identical rows with a policy-derived ranking score. It passes if the upper CI bound is below 0, and the result is also reported against a minimum useful effect declared in advance. Only B1, M1 and M3 are confirmatory arms. The 12- and 36-month horizons and the other arms are secondary within a Holm family. VoI is evaluated separately as evidence cost per resolved case, compared with a checklist under an equal budget.
3. **Label definition.** The event is the first *final* FDA approval. Tentative approvals and authorized generics are excluded. A sample is cross-checked against the FDA first-generic lists. 351(k) approvals are grouped by reference product.
4. **G3a/G3b.** G3a also freezes the cohort definition and the publication-date evidence for each source. G3b locks code, model, policy and hashed predictions with an external timestamp, before a declared deadline.
5. **Code defects found by static review** (to be fixed in card FIX1 before any Wave 2 modeling):
   - `dataset.py`: the NME, orphan, priority and route flags aggregate records approved after the cutoff, which leaks into both features and the `only_nme` cohort filter.
   - `dataset.py`: `build_samples` keeps positives whose follow-up window is incomplete but drops such negatives, and it admits approvals after `data_end`.
   - `dataset.py`: `time_split` accepts `t_end == test_first_cutoff` and overlapping boundaries.
   - `metrics.py`: AURC ranks by max(p, 1−p) at a fixed 0.5 threshold, ignores the graph action, and depends on row order when scores tie. The bootstrap evaluates one arm only, with no paired difference.
   - `evidence_graph.decide`: `all([])` returns TRUE when items are missing, and BLOCKED forces a negative prediction.
   - `voi.py`: the reveal probability (0.3) and the prior truth (0.5) are conflated.
   - `trackA_freeze.py`: it can train on outcomes after t0 when the raw data is newer than t0, `data_end` is not a completeness check, and `snapshot_features` ignores t0.
6. **Wave 2 card order and acceptance.** FIX1 comes first. T7 then becomes a stratified audit of 100 development cases with FDA locators and false-merge and false-split rates. T2 compares pooled verdict and missingness features against M1 with a future-invariance test. T1 runs after T2 on a separate validation slice. T4 simulates paired ΔAURC under a cluster structure, including a type-I check. T5 waits for T7, T2, T1, T4 and the C′ gate.

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
| Main planner and reviewer | Claude Opus 5.5 | Briefs, review of every executor branch (receipt, key diffs, full test rerun, spot reproduction of numbers), integration, lane HANDOFF and MEMORY, owner reports in Thai. Only this role manages `docs/owner/` (D40). |
| Co-planner | GPT-6.2 Astra high (owner-approved 27 Nov) | Methodology decisions only, such as the preregistration and the C′ gate. Read-only. Wave 1 CP1 used GPT-6.2 Sol medium. |
| Executor | GPT models via Codex from Wave 2 (owner change, 27 Nov). Owner-approved mapping: GPT-6.2 Sol xhigh for FIX1, T4 and T3; Sol high for T2, T1, the T5 draft and the E4 rerun; GPT-6 Luna high for T7, T9, T12 and Thai demo curation | One task card per session in its own worktree. Wave 1 used Claude Sonnet 5.5. |

**Executor protocol.**

- Start from `research/loe-bench`.
- Create the branch `loe/<task-id>`.
- Write only the paths listed in the card, plus `docs/loe-bench/receipts/<task-id>.md`.
- Commit with explicit paths, push the task branch, and report briefly.
- Leave the lane HANDOFF and MEMORY to the main planner, who updates them at integration.
- Keep raw data outside Git at `../_private_artifacts/loe-bench/`. Record its hashes in Git.
- Use Python's standard library only. Do not use sklearn, pandas or scipy. numpy is optional.

## Dispatch board

| Wave | ID | Card | Executor | Depends on | Status |
|---|---|---|---|---|---|
| 1 | E1 | T0 + fresh openFDA fetch, MANIFEST comparison, profile, G3a S0 input freeze | Sonnet low | none | merged: t0 2026-11-27, tag `loe-S0-input-20261127` |
| 1 | E2 | T6 historical Orange Book editions (G1), as-of parser and leakage test | Sonnet medium | none | merged: 19 editions 2009–2026; gaps 2010, 2017, 2019-01 to 2020-11 |
| 1 | E3 | T8 Purple Book open-access feasibility and monthly download | Sonnet low | none | merged: OPEN_ACCESS_OK, 96 351(k) BLAs, 21 reference products |
| 1 | E4 | T10 dr-train LLM arm, inventory, harness and synthetic smoke (V100 only) | Sonnet medium | none | merged PARTIAL: harness + mock tests; GPU smoke BLOCKED (dr-train offline) |
| 1 | E5 | Thai open-data feasibility for the Thai-context demo | Sonnet low | none | merged: no Thai sample retrieved; curated-link demo recommended |
| 1 | CP1 | Co-planner critique of design, hypotheses and novelty | GPT-6.2 Sol medium | none | adopted (see CP1 section) |
| 2 | FIX1 | Fix CP1 code defects with leakage, censoring and tie tests | GPT-6.2 Sol xhigh | CP1 | dispatched |
| 2 | — | T7 ingredient audit, T1 thresholds, T2 OPEN-conditional model, T4 power simulation (train and validation only) | Sonnet | E1, E2 | waiting |
| 2 | — | T5 preregistration draft, then co-reviewer | Sonnet, then GPT | T4 | waiting |
| G2 | — | Owner approves criteria and submits to OSF | Owner | T5 | waiting |
| 3 | — | G3b prediction freeze, T3 ablation, T9 re-score, T12 table builder, L1 arm run | Sonnet | G2 | waiting |
| 3 | — | Thai-context demo | Claude | E5, G3b | waiting |
| End | — | Owner document pack: expert review, journal check, customer discovery, OSF steps, Paper 53 venue | Orchestrator | G5 | waiting |
