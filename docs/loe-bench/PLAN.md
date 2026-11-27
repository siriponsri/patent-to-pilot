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

## CP2 co-planner review and main-planner decision, 27 November 2026

GPT-6.2 Astra (high, read-only) proposed a strictly clean C′ test, made up of drugs first approved after 1 January 2023, with the 24-month horizon and a cutoff of 2024 only. It also proposed a gate of at least 50 event-bearing drug clusters, edition freshness within six months, a backfill of missing editions, an endpoint normalized over a common 0–80% coverage range, a useful effect of Δ ≤ −0.010, and T4 with at least 5,000 simulations per scenario.

**Main-planner decision.** The strict clean cohort is adopted only as a descriptive sensitivity subset, not as the primary test. The cohort consists of NMEs approved in 2023, and five-year NCE exclusivity blocks ANDA approval within that window by design, so the cohort cannot reach 50 event clusters. Making it primary would guarantee an empty confirmation. That conclusion follows from regulatory structure, and no data were inspected.

The primary retrospective test is therefore **C′ at 24 months over the test cutoffs 2017 and later that the editions cover**, with a disclosed exposure:

- The earlier exposure was limited to aggregate B0–B2 scores at 36 months and aggregate test prevalence.
- No proposed arm has been scored.
- No per-row output was inspected.
- No selection used the test set.

This follows the argument that reusing a test set without adaptive selection produces little overfitting ([Recht et al. 2019](https://proceedings.mlr.press/v97/recht19a.html)). The confirmatory test is now sealed in code. Any metric on cutoffs from 2017-01-01 onward requires the hash of the submitted preregistration. Track A remains the fully clean prospective confirmation.

**Adopted from CP2:**

- annual cutoffs from 2010-01-01
- the strict split rule (earlier cutoff + h < next partition start)
- the edition freshness requirement (within six months before each cutoff) and the backfill list
- cluster-resampled paired bootstrap
- AURC normalized over a common 0–80% coverage range, with both arms required to reach 80%
- useful effect Δ ≤ −0.010, reported alongside the CI < 0 superiority rule
- T4 design with at least 5,000 simulations per scenario
- M1 fairness: same rows, evidence, missingness, probability model, calibration and tuning budget, plus a confidence-ranked abstention policy
- a minimum of 50 event-bearing clusters as the gate for the primary test

If the gate fails, C′ is reported as feasibility evidence and confirmation rests with Track A.

**Owner approval (27 November 2026).** The owner approved this design and the full, open disclosure of the earlier exposure in the preregistration and the manuscript.

## Confirmatory criteria v2 (main planner proposal, owner-approved 27 November 2026)

The v2 criteria supersede the single CP1 primary endpoint and the Holm family. T4 and T5 must implement them.

The owner authorized the main planner to propose better criteria grounded in verified references. This proposal uses development (validation) evidence only. The test set remains sealed.

**Development evidence behind it (T2b, 24 months):**

| Contrast | ΔAURC80 | 95% CI |
|---|---|---|
| M1 − B1 | −0.0073 | −0.0153 to −0.00004 |
| M3 − B1 | −0.0032 | −0.0119 to +0.0054 |
| M3 − M1 | +0.0040 | −0.0001 to +0.0099 |

83% of rows are CONTESTED because the challenge leaf has no data. E6 is addressing that.

**Confirmatory family: fixed-sequence testing**, each step one-sided at α = 0.025 and taken only after the previous step succeeds. This is the procedure in FDA guidance [*Multiple Endpoints in Clinical Trials* (2022), section "The Fixed-Sequence Method"](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials), verified by the main planner in the guidance PDF. It replaces Holm because the hypotheses have a natural order of relevance, and each step keeps the full α.

1. **H1:** ΔAURC80(M3 − B1) < 0 at 24 months on the C′ test. The proposed system must beat the strongest incumbent heuristic, the age clock. This restores the owner package's original H1.
2. **H2** (only if H1 succeeds): ΔAURC80(M3 − M1) < 0 at 24 months. This tests the incremental value of the graph and abstention policy over a matched flat model.
3. **H3** (only if H2 succeeds): ΔAURC80(M3 − B1) < 0 at 12 months.

**Secondary, non-confirmatory** (each reported with a CI and no claim):

- M1 − B1, which asks whether as-of regulatory evidence beats the age clock
- E-AURC, which is AURC minus the oracle AURC and separates ranking quality from base error ([Geifman et al. 2019](https://arxiv.org/abs/1805.08206), verified)
- selective risk at 70% coverage, referral rate, Brier score, and ECE with bin counts
- the strict post-2023 cohort and Track B, both descriptive

**Unchanged:**

- AURC80 is normalized over the common 0–80% coverage range, and both arms must reach 80%.
- The paired bootstrap resamples whole drug clusters ([Field & Welsh 2007](https://doi.org/10.1111/j.1467-9868.2007.00593.x), verified), with at least 2,000 draws.
- Δ ≤ −0.010 is reported as the practical-usefulness threshold, separately from statistical success.
- The C′ gate still applies: at least 50 event clusters and fresh, availability-proven editions. Otherwise C′ is reported as feasibility, and confirmation rests with Track A.
- T4 estimates power for H1 at Δ = −0.010 before preregistration.

The Westfall & Krishen (2001) gatekeeping reference could not be verified, so it is not cited.

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
| 2 | FIX1 | Fix CP1 code defects with leakage, censoring and tie tests | GPT-6.2 Sol xhigh | CP1 | merged: 51 tests, 17 regression tests; repo pytest only the 8 accepted SACR failures |
| 2 | CP2 | C′ design: split given editions from 2009-06, exposure of shared labels, coverage gate, minimum useful effect | GPT-6.2 Astra high | FIX1 | decided (see CP2 section) |
| 2 | T7 | Stratified ingredient-key audit | GPT-6.2 Sol high (Luna attempt failed) | FIX1 | merged: 22/100 sampled keys wrong; the population-weighted estimate is about 11% wrong and about 6% unresolved |
| 2 | FIX2 | Systematic active-moiety key (UNII-based) plus a fresh post-fix audit | GPT-6.2 Sol high | T7 | dispatched |
| 2 | E2b | Backfill Orange Book editions per CP2 list | GPT-6.2 Sol high | CP2 | merged: 15/16 cutoffs fresh; 2011-01-01 has no edition |
| 2 | T2 | M1/M2/M3 arms, as-of features, test seal, development validation only | GPT-6.2 Sol high | FIX1, CP2 | merged: seal works; stale editions gave 0 OPEN rows |
| 2 | T2b | Rerun with availability-proven editions and a shared age base | GPT-6.2 Sol high | E2b | merged (development only). At 24 months, M1−B1 = −0.0073 (CI below 0) and M3−M1 = +0.0040 (CI includes 0). 83% of rows are CONTESTED. |
| 2 | FIX2 | UNII active-moiety key | GPT-6.2 Sol high | T7 | not merged: fresh audit 0 false merges, 11/60 false splits |
| 2 | FIX2b | Close FIX2 false splits (name-to-UNII lookup, union-find), fresh audit with seed 20261130 | GPT-6.2 Sol high | FIX2 | fresh audit: 57 correct, 1 false split, 2 unresolved of 60; merge via FIX2c |
| 2 | E6 | As-of FDA Paragraph IV certification list for the challenge leaf | GPT-6.2 Sol high | T2b | merged: 11/16 cutoffs fresh; gaps 2013–2016 and 2024; development name matches about 70% |
| 2 | E6-alt | Alternative challenge sources (litigation dockets and others) | GPT-6.2 Astra high | E6 | merged: EDGAR filings GREEN; Rai et al. CC0 court table (filings 2011–2020) AMBER, usable to fill the 2013–2016 gap |
| 2 | FIX2c | Merge the moiety key with T2b, link OB aliases, rerun development | GPT-6.2 Sol high | FIX2b | merged: NDA links 95.9–99.6% per edition. Development at 24 months: M3−B1 −0.0072 (CI −0.0162 to +0.0010); M3−M1 −0.0001 |
| 2 | E7 | Combined as-of challenge leaf (FDA PIV list + Rai court filings + EDGAR) on moiety keys | GPT-6.2 Sol high | FIX2c, E6, E6-alt | merged: closed-world at 3 cutoffs; Rai name-linked pairs 7; EDGAR NOT_RUN; development CIs include 0 |
| 2 | E7b | Relink Rai cases to drugs through Orange Book patent numbers (as-of editions) | GPT-6.2 Sol high | E7 | dispatched |
| 2 | T4 | Power simulation for criteria v2 (H1 at Δ = −0.010) from the development structure | GPT-6.2 Sol xhigh | FIX2c | merged but NOT ACCEPTED: power about 100% even with 30 clusters, MDE 0.0039, which looks optimistic beside the development CI half-width of about 0.01; type-I 2.75% (MC CI 1.54–4.86%) |
| 2 | T4b | Calibrate generator variance against the empirical development bootstrap; firm up type-I | GPT-6.2 Sol xhigh | T4 | dispatched |
| 2 | — | T7 ingredient audit, T1 thresholds, T2 OPEN-conditional model, T4 power simulation (train and validation only) | Sonnet | E1, E2 | waiting |
| 2 | — | T5 preregistration draft (criteria v2), reviewed by the main planner | GPT-6.2 Sol high, then Claude | T4 | waiting |
| G2 | — | Owner approves criteria and submits to OSF | Owner | T5 | waiting |
| 3 | — | G3b prediction freeze, T3 ablation, T9 re-score, T12 table builder, L1 arm run | Sonnet | G2 | waiting |
| 3 | — | Thai-context demo | Claude | E5, G3b | waiting |
| End | — | Owner document pack: expert review, journal check, customer discovery, OSF steps, Paper 53 venue | Orchestrator | G5 | waiting |
