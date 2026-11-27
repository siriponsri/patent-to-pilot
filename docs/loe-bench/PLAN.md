# LOE-Bench program plan (D40)

LOE-Bench forecasts whether a first generic (ANDA) or biosimilar (351(k)) approval will occur within 12, 24 or 36 months, using only open public regulatory records. The proposed method combines a three-state (Kleene) evidence graph, a calibrated probability, abstention with referral to a human FTO evaluator, and value-of-information ordering of the next evidence item. The owner's original package is preserved in Thai under [owner-source](owner-source/) with [source hashes](owner-source/SOURCE-SHA256.txt). Code and small data are in [`loe-bench/`](../../loe-bench/).

D40 replaces the RA Pharma mandate as the active program. RA Pharma is folded in as the Thai-context layer: the program must ship a Thai-context demo that applies the triage output to the Thai market using open Thai sources.

## Evidence design (Orchestrator recommendation, owner-delegated)

The owner has no proprietary data, so every source must be publicly accessible. Public access does not imply open reuse: record each source's terms. For example, NBER restricts redistribution and commercial use (E8). The design below aims at the highest credible impact with the fewest avoidable reviewer objections.

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

**Proposed amendment after T4b (awaiting owner approval).** The percentile bootstrap is slightly anti-conservative: at a nominal one-sided α = 0.025 the H1 type-I is 2.81% (MC CI 2.53–3.12%). Use the 98th-percentile bound, a nominal α = 0.020 per step, which gives an empirical type-I of 2.24% (1.99–2.52%) and keeps power ≥ 80% in every simulated scenario.

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

## Confirmatory criteria v3 (owner-approved 27 November 2026; supersedes v2 endpoints)

**Why v2 was replaced.** In development (K20T1), AURC80 with max(p, 1−p) confidence rewarded confident NO-ENTRY calls. At the 24-month and 90% target, M3 answered 991 of 1,083 rows, all of them "no entry", and missed every answered event. Its selective error was still only 5.05%. The metric therefore measured how well a model orders low-risk cases, not whether it helps a scarce evaluator find upcoming entries. Selective-classification literature notes that accepted-set error alone hides silent failures ([Traub et al., NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/047c84ec50bd8ea29349b996fc64af4b-Paper-Conference.pdf)). Under class imbalance, precision-recall views are more informative than accuracy-type views ([Saito & Rehmsmeier, PLOS ONE 2015](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432)). Both were opened by the CP4 co-planner on 27 Nov 2026. The endpoint was chosen on workflow and validity grounds. The development numbers in [CP4](CP4-METRIC-REDESIGN.md) are illustrative only, and the test stays sealed.

**Primary endpoint: entry recall at a 20% review budget.** At each annual cutoff, every arm ranks the eligible rows by its **native** entry-risk score. The top floor(N_t/5) rows go to the evaluator queue. Recall is the number of queued event rows divided by all event rows, pooled over cutoffs, with expected capture at boundary ties.

- Native scores avoid the calibration-induced rank reversal that CP4 found for B1 at 12 months.
- Queue precision and distinct event-drug capture are reported alongside recall.
- The 20% budget represents an evaluator who can review one in five drug-years. It is a design assumption, owner-approved.

**Fixed-sequence family** (FDA [*Multiple Endpoints in Clinical Trials*](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials), 2022, section "The Fixed-Sequence Method"):

1. **H1:** recall@20%(M3) − recall@20%(B1) > 0 at 24 months.
2. **H2:** recall@20%(M3) − recall@20%(M1) > 0 at 24 months.
3. **H3:** recall@20%(M3) − recall@20%(B1) > 0 at 12 months.

Each step uses a paired whole-drug cluster bootstrap with at least 2,000 draws ([Field & Welsh 2007](https://doi.org/10.1111/j.1467-9868.2007.00593.x)). A step succeeds when the lower percentile bound is strictly above 0. The family stops at the first failed or unevaluable step, and any undefined replicate means no confirmatory result.

**α rule (pre-declared).** The T4 rerun estimates the H1 type-I error with at least 12,000 null datasets. Use one-sided α = 0.025 if the Monte Carlo 95% upper bound is 2.5% or less, otherwise 0.020. The choice is fixed before preregistration.

**Practical usefulness.** A difference of at least +10 percentage points of recall counts as useful. It is reported next to statistical success, and it is not a gate.

**Secondary (non-confirmatory).** Average precision; expected decision loss with illustrative costs (missed clear 10, false flag 1, referral 0.5); AURC80 and E-AURC for continuity with v2; calibration (Brier, ECE); auto-clear safety, meaning missed events among auto-cleared rows; referral workload; and a descriptive analysis of the strict post-2023 cohort and of Track B.

**Policy.** Asymmetric thresholds: auto-clear when p ≤ lo and flag entry when p ≥ hi, with lo and hi chosen on an inner development slice to meet the review budget and an auto-clear safety target. The symmetric lo = 1 − hi rule is retired.

**No external domain expert (owner statement, 27 Nov 2026).** The planned expert review of exclusivity and patent assumptions (G6) cannot take place. Mitigation:

- An executor verifies every regulatory rule the code uses against primary legal and FDA sources: NCE 5-year exclusivity, 30-month stay, 180-day exclusivity, pediatric exclusivity, and the 12-year reference-product exclusivity for biologics.
- The co-planner cross-checks that verification.
- The manuscript states the absence of expert adjudication as a limitation.
- The output remains a triage aid, not a legal opinion.

## Planner evidence (D32)

| Claim or task | Primary paper | Benchmark or competitor | Status |
|---|---|---|---|
| Abstention and AURC as the main metric | [Geifman & El-Yaniv 2017, selective classification](https://arxiv.org/abs/1705.08500); [Geifman et al. 2019, AURC](https://arxiv.org/abs/1805.08206) | B1 age-hazard table. The exposed smoke AURC is 0.0449. | External reference. Head-to-head comparison not yet run. |
| Prospective freeze as the strongest evidence | [Karger et al. 2024, ForecastBench](https://arxiv.org/abs/2409.19839) | Track A against B1 and B3 | Untested hypothesis |
| Leakage control in time splits | [Kapoor & Narayanan 2023, leakage in ML-based science](https://arxiv.org/abs/2207.07048) | Track C against C′ | Design rule |
| Closest recent competitor study (forward time-split) | [Hopefl et al. 2025, Clin Transl Sci, doi:10.1111/cts.70365](https://doi.org/10.1111/cts.70365): random survival forest vs Cox/AFT for first ANDA **submission** in orphan drugs; C-index 0.675–0.754; uses closed IQVIA sales and FDA-internal complexity | LOE-Bench differs: open-only as-of inputs, first final **approval**, abstention and AURC | External reference (SciSpace full-text read, owner report 27 Nov) |
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
| 2 | E7b | Relink Rai cases to drugs through Orange Book patent numbers (as-of editions) | GPT-6.2 Sol high | E7 | merged: development M1−B1 at 24 months −0.0096 (CI below 0); M3−M1 about 0 |
| 2 | E8 | Ingest the NBER Orange Book Dataset 1985–2016 (K20) to extend the training window | GPT-6.2 Sol high | — | merged: 31 editions; 22 extra training years possible; editions about 12 months stale; licence restricts redistribution and commercial use |
| 2 | E9 | As-of FDA product-specific guidance dates (K19) | GPT-6.2 Sol high | — | not merged: K19 rejected (high survivorship; 12-month development result worse) |
| 2 | DEVX | Fixed-order development trials of K07, K09, K10, K08 and K06 under one budget | GPT-6.2 Sol high | E7b | merged: K07 adopted; K06, K08, K09 and K10 rejected |
| 2 | DOCS | Project-wide documentation review | GPT-6.2 Sol high | — | dispatched |
| 2 | T4 | Power simulation for criteria v2 (H1 at Δ = −0.010) from the development structure | GPT-6.2 Sol xhigh | FIX2c | merged but NOT ACCEPTED: power about 100% even with 30 clusters, MDE 0.0039, which looks optimistic beside the development CI half-width of about 0.01; type-I 2.75% (MC CI 1.54–4.86%) |
| 2 | T4b | Calibrate generator variance against the empirical development bootstrap; firm up type-I | GPT-6.2 Sol xhigh | T4 | merged: variance passes 6/6 (simulated SD 0.91–1.04× empirical); H1 power ≥ 80% from 30 event clusters at Δ = −0.010; MDE about 0.0039 at 75 clusters; type-I 2.81% (2.53–3.12) at α = 0.025 and 2.24% (1.99–2.52) at α = 0.020 |
| 2 | — | (Superseded by the separate T7, T2, T4 and T1 rows. Executors are GPT models from Wave 2.) | — | — | superseded |
| 2 | K20+T1 | Long-window trial (pre-declared rule), then threshold and policy freeze | GPT-6.2 Sol high | E8, T4b | merged: K20 rejected. T1 failed acceptance: coverage targets met at 3/12, and every confident answer is NO ENTRY (class imbalance) |
| 2 | CP4 | Co-planner: metric and policy redesign under about 5% prevalence (criteria v3 options) | GPT-6.2 Astra high | K20T1 | merged; criteria v3 owner-approved |
| 2 | T1v3 | Asymmetric policy freeze (lo/hi) for the review budget and auto-clear safety, with native-score queues | GPT-6.2 Sol high | CP4 | dispatched |
| 2 | T4c | Power and type-I for recall@20% (applies the α rule) | GPT-6.2 Sol xhigh | CP4 | dispatched |
| 2 | K22 | Legally faithful graph trial (M3 only, pre-declared rule) | GPT-6.2 Sol xhigh | REG | dispatched |
| 2 | FREEZE | Rebuild the frozen config on merged code (REG fix, K22 decision); T1v3 rule unchanged | GPT-6.2 Sol high | T1v3, K22 | waiting |
| 2 | REG | Verify regulatory rules in code against primary legal and FDA sources (replaces the expert review) | GPT-6.2 Sol high | — | merged: [REGULATORY-RULES.md](REGULATORY-RULES.md). One fix: undated matched PIV rows now give UNKNOWN instead of FALSE. T1v3 and T4c started before it, so the frozen config must be rebuilt on the merged code |
| 2 | — | T5 preregistration draft (criteria v2), reviewed by the main planner | GPT-6.2 Sol high, then Claude | T4 | waiting |
| G2 | — | Owner approves criteria and submits to OSF | Owner | T5 | waiting |
| 3 | — | G3b prediction freeze, T3 ablation (GPT-6.2 Sol xhigh), T9 re-score and T12 table builder (GPT-6 Luna high, scripted), L1 arm run (GPU proposal to the owner first) | GPT | G2 | waiting |
| 3 | — | Thai-context demo | GPT-6.2 Sol high, reviewed by Claude | E5, G3b | waiting |
| End | — | Owner document pack: expert review, journal check, customer discovery, OSF steps, Paper 53 venue, NBER commercial-use clearance, Thai data access | Main planner | G5 | waiting |
