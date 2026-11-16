# Merged plan for Paper 2 and Paper 3 (owner pack + office-action evidence)

Date: 2026-11-16. Status: **PROPOSED v2, NOT FROZEN.** Merged to main as a proposal.

## v2 changes (after an external review, owner-supplied, 2026-11-16)

1. Paper 2 now carries its own method candidate (E3, claim-element deficit-aware search), not only E0-E2 baselines (section 5.2).
2. The corpus is drawn from a label-independent population. A known-positive-seeded corpus is allowed only as a labelled "closed-world" variant (section 3.2).
3. There are two temporal settings, never mixed: Retrospective Public Discovery and Office-Action Evidence Recovery with 35 USC 102(a)(2) effective dates (section 3.2).
4. The 13/9,480 DAPFAM figure is stated only under its mapping rule and coverage. It is not evidence about DAPFAM label quality (section 1).
5. The primary endpoint is fixed now, not chosen from DEV results. Power is computed from independent clusters (sections 5.4, 5.5).
6. Paper 3 is no longer gated on E2 performing well. Hard stops are only data, tool or evaluation integrity failures (sections 5.6, 6).
7. Claim-version check: the published claims versus the claims the examiner rejected (section 3.1).

This plan grants no authority to dispatch, spend, download or score. Each of those needs a separate owner decision (section 11).

Inputs:
- the owner's planning pack in `docs/owner/` (00-15, revision A, 2026-11-16; owner-local, not committed);
- the Paper 2 pre-check ledger `docs/healthtech/research/paper2-precheck/README.md`;
- the office-action (OA) census `docs/healthtech/research/paper2-precheck/OA-DATA-FEASIBILITY.md` section 9.

Paper 1 (DAPFAM, frozen S8) is out of scope. It finishes under its own protocol, and nothing here changes it.

## 1. What we already know (evidence, not hypotheses)

| Evidence | Source | Implication |
|---|---|---|
| Query rewriting (FA/GR/SACR) fused with dense barely moves cross-domain (OUT) recall on DAPFAM dev; FA harms IN | Paper 1 S5 (dev, descriptive) | Query-side rewriting alone is not the lever |
| Six fixed acquisition actions, any fixed or per-section mix, IPC-restricted queries, a citation-learned class prior, BM25/RRF fusion and a label-free per-query router all fail to beat dense at pool 200 | Pre-check ledger (5-6 Nov, 16 Nov) | Do not repeat these. Label-free acquisition gains on DAPFAM are not demonstrated |
| A per-query oracle over the six actions gains +0.094 OUT R@200, and LLM actions reach 120 OUT positives that no conventional action reaches | Stage 1 (5 Nov), reproduced 16 Nov | Real headroom exists, but no label-free selector has captured it |
| An earlier configuration study found that perfect reordering of a 200 pool adds far less than deepening it to 1,000, and that most cross-domain targets stay unretrieved even at 1,000 | Prior journal draft (not cited by name in study files) | Exposure, not ordering, is the binding constraint |
| A plain patent retriever beats a trained 4B agent on R@100 in PatEx-Gym | arXiv 2610.33503 | A fixed retriever (E0) and a fixed multi-query baseline (E1) are mandatory anchors |
| USPTO OA data 2008 to mid-2017: 6.11M (application, cited US doc) pairs with a 102/103 basis; 1.36M OUT under the IPC3 rule (24.7%), 824k with a section mismatch; 760k applications with at least one OUT pair | OA census, 16 Nov | A large, legally grounded, cross-domain evaluation source exists, with room for temporal holdouts |
| Under an exact-title mapping (precision not measured) and the 2008-2017 OA coverage, only 13 of 9,480 DAPFAM dev positive pairs could be linked to an examiner 102/103 citation | OA census A2 | Says only that DAPFAM labels and OA rejection citations measure different things under this mapping. It is not evidence that DAPFAM labels are low quality. Motivation for a rejection-grounded set, stated with the mapping limits |

## 2. Decision proposed

Two papers in sequence plus one product track. This replaces the pack's single large programme (nine arms x four solvers x transfer).

| Track | Question | Contribution type | Enters when |
|---|---|---|---|
| **Paper 2 (P2-OA)** | Does an interactive agent acquire legally grounded cross-domain prior art better than strong fixed retrieval at the same budget, and at which funnel stage does it gain or lose? | Resource (OA-derived cross-domain set with 102/103 and IN/OUT labels) + **within-task search method E3 (claim-element deficit-aware search)** against strong baselines E0/E1/E2 | Now (planning); execution after the downloads and compute below are approved |
| **Paper 3 (P3-EGSHE)** | Does stage-specific, dev-verified harness patching (EG-SHE, `docs/owner/14`) beat uniform harness evolution (AAH-style) and feedback-in-prompt on a fresh temporal holdout, and does it transfer to a smaller frozen solver? (Learning **across** tasks; Paper 2 is search **within** a task) | Method | When the integrity gate G2.3 passes; not dependent on E2/E3 results |
| **Product (HT-PROD)** | Source-linked HealthTech Solution Scout dossier | Engineering | In parallel, as in `docs/owner/03`; independent of research outcomes |

The MTM temporal transfer study (old ST2) becomes optional external validation and is not forced into a paper. Graph navigation (old ST3) stays closed (feasibility negative).

## 3. Shared data foundation: the OA-derived cross-domain set

### 3.1 Units and labels
- **Task (query):** one US application with a first (or earliest available) non-final rejection mailed 2008 to mid-2017 that cites at least 3 US documents under 102/103 (`citation_in_oa = 1`). At least one cited document must be OUT under the IPC3 rule.
- **Known references K(q):** all examiner-cited US documents in that office action with a 102 or 103 basis. Each pair is labelled by basis (102 only / 103 only / both) and domain under three rules (IPC3, IPC4, section mismatch). **IPC3 is primary**, to stay comparable with DAPFAM.
- **Unjudged is not negative.** Documents cited by the applicant (PTO-1449) or in later actions are recorded as `other_citation`. They are never counted as negatives.
- **One reference is not a rejection.** A 103 rejection may combine several references. Retrieving one cited document is evidence recovery, not proof of obviousness or anticipation. Combination coverage (all references of one rejection retrieved) is reported as a secondary measure.
- **Claim-version check.** Examiners reject the claims as they stood when the action was mailed, which can differ from the published claims.
  - Measure the share of tasks whose first action precedes any amendment, using the `rejections` claim numbers and the application timeline.
  - Prefer first actions on the claims as filed.
  - Report the remaining mismatch rate as a limitation.

### 3.2 Query text and corpus
- **Query text:** the application as published (pre-grant publication): title, abstract and claims. This needs the PatentsView `pg_*` text tables (download not yet approved; section 11).
- **Primary corpus (open-population):** a population fixed before any label is used. For example, all US grants and pre-grant publications in a declared date window, or a declared random sample stratified by CPC section. Membership never depends on whether a document is cited.
  - OA labels are joined afterwards.
  - Gold coverage (`% K in corpus`, by IN/OUT and 102/103) is reported per split.
  - Tasks with zero covered references are reported as such, not dropped silently.
- **Closed-world variant (optional, labelled as such):** the union of the cited documents plus distractors, used only for cheap development or ablations.
  - Distractors are drawn by CPC subclass and at random, at a ratio fixed before scoring.
  - Results are called "OA-derived closed-world" and are never presented as open-corpus search.
- **Two temporal settings, reported separately, never mixed:**
  - **Retrospective Public Discovery (RPD):** only documents published before the task's filing date. Cited references excluded by this rule are counted, not hidden.
  - **Office-Action Evidence Recovery (OAER):** documents eligible as prior art at the task's effective filing date under the stated rule. Under AIA 35 USC 102(a)(2), this includes US patent documents with an earlier effective filing date that were published later. Pre-AIA tasks use the corresponding pre-AIA rule. The exact rule text and the AIA/pre-AIA split come from USPTO sources and must be verified before the freeze.
- **Corpus size:** measured, not assumed. The planning range is 0.3-1.5M documents; it bounds encoding cost (section 8) and is re-measured on a sample first.

### 3.3 Splits (three-way temporal, fixed before any scoring)
| Split | Filing years (proposal; final cut points set from the year histogram before any retrieval run) | Used by |
|---|---|---|
| DEV | earliest window | P2 and P3 development only |
| P2-TEST | middle window | P2 confirmatory comparison, opened once |
| P3-TEST | latest window, never touched by P2 | P3 confirmatory comparison, opened once |

- Each split is grouped by art unit / CPC subclass so the cluster bootstrap can respect dependence.
- A family (or continuation) chain never crosses splits.
- The newest window goes to P3 because it is least likely to appear in model training data. Leakage cannot be excluded, and this is stated as a limitation.

### 3.4 Sanity anchors
- **PANORAMA PAR4PC/PI4PC** (already local; CC BY-NC) as a claim-level consistency check of the 102/103 labelling, not as a test set.
- **PatEx-Gym public 100 tasks** as a compatibility pilot for the agent interface. Results are labelled "PatEx-style, modified environment" and are not leaderboard-comparable.

## 4. Models, tools and budget

| Role | Model | Notes |
|---|---|---|
| Local frozen solver | Qwen3-8B (existing on dr-train, fp16/eager on V100) | Available after S8 finishes, or in parallel under the owner's parallel-GPU approval if memory allows |
| Low-cost API solver | e.g. `qwen/qwen3.8-flash` | Pin route and price on the dispatch day |
| Cross-family API solver | e.g. `deepseek/deepseek-v3.2` | Same |
| Evolver (P3 only) | Choose at the P3 freeze among current frontier models (the pack names Sonnet 4.6; newer releases exist, so re-check capability and price) | Bounded proposals only |
| Retrievers (tools) | PatEmbed-large dense (repo pins), BM25 (in-repo implementation), CPC filter, citation expansion | Same tools for every arm |

- **No LLM judge.** All metrics are mechanical: reference recall, and source ID / locator / quote-match validity for grounding. The "judge calls" term in the pack's cost formula is set to zero.
- **Second local model (Qwen3-14B):** not on the V100 while S8 runs (fp16 needs about 28 GB, and many int4 kernels need newer GPUs than V100). If needed, use RunPod under a separate budget amendment.
- **API ceiling: USD 100 in total for P2 + P3** (owner pack).

| Envelope | Ceiling (USD) |
|---|---|
| Connection and schema smoke | 5 |
| P2 dev pilot and P2-TEST | 30 |
| P3 evolution (dev) | 25 |
| P3 ablations | 15 |
| P3-TEST and transfer | 15 |
| Reserve | 10 |

- Local GPU time is metered separately, never treated as free.
- No paid call happens before the owner approves the exact model, provider, task count and per-dispatch cap.

## 5. Paper 2 (P2-OA): resource + strong-baseline funnel study

### 5.1 Research questions
- **RQ2.1:** On legally grounded cross-domain prior art, how much do E1 (fixed multi-query) and E2 (interactive ReAct agent) add over E0 (best fixed retriever) at equal budget?
- **RQ2.2:** Where in the funnel (Search, Visit, Select) do OUT references get lost, and does that differ for 102 versus 103 citations?
- **RQ2.3 (descriptive):** How do DAPFAM-style citation labels relate to rejection-grounded labels? This uses the existing 13/9,480 finding and the OA set's own non-rejection citations.

### 5.2 Arms (taken from the pack, cut to what P2 needs)
| Arm | Definition |
|---|---|
| E0 | Fixed retrieval: best of dense / BM25 / hybrid, chosen on DEV only, fixed top-k |
| E0-deep | E0 with a deeper pool (500-1,000) and a fixed reranker, budget-matched. This is the untested lever from the ledger |
| E1 | Fixed multi-query schedule (pre-declared query templates), same maximum actions as E2 |
| E2 | Static ReAct agent (search / visit / select / stop), same tools and budget, no cross-task memory; run with Qwen3-8B local and one API solver |
| **E3 (method under test)** | **Claim-element deficit-aware search (CEDS).** The query's independent claim is split into elements. For each element the controller tracks whether any visited document has a source-located passage matching it, using a mechanical check plus a bounded LLM extraction with a quote. Each next action targets the least-covered element: element-specific query, cross-domain reformulation of that element's function, CPC hop, or citation hop. It stops when all elements are covered or the budget is spent. Gold is never used. The legal motivation is that 103 rejections combine references element by element |

**E3 novelty is not assumed.** Coverage-guided search, claim charting and PatentAgentBench's claim-charting suite are close prior work.
- Before the freeze, a literature check must state exactly what E3 adds (element-deficit targeting for cross-domain acquisition under a budget, judged on rejection-grounded labels) and cite the closest work.
- If an equivalent method exists, E3 becomes a re-implementation baseline and the contribution is reframed honestly.

### 5.3 Metrics
- **Primary family:**
  - Search-R, Visit-R and Select-R on OUT references (query-macro, eligible queries only);
  - each stratified by 102 / 103 and reported for IN as harm checks.
- **Secondary:** micro recall, nDCG@10 of the final ranked list, actions/tokens/seconds/USD per query, and coverage of K in the corpus.
- **Grounding** (mechanical only): the cited source exists, the locator is valid, and the quote matches byte-for-byte after declared normalisation.

### 5.4 Primary endpoint (fixed now, v2)
- **Primary:** OUT Select-R at the fixed per-task budget, i.e. the share of examiner-cited OUT references that appear in the system's final selected evidence set. This is query-macro over eligible tasks (at least one covered OUT reference), in the RPD setting on the open-population corpus.
- Select-R is chosen because it is the end-to-end quantity a searcher receives. Search-R and Visit-R are secondary and explain where the losses happen.
- **Confirmatory contrasts:** E3 − E0 (primary) and E3 − E2 (secondary). E1 − E0 and E0-deep − E0 are descriptive anchors.
- Margin δ = 0.010 absolute. Superiority, non-inferiority (IN Select-R harm margin −0.020) and inconclusive are interpreted as in Paper 1.

### 5.5 Statistics
- Paired differences.
- Cluster bootstrap by art unit (10,000 resamples, fixed seed).
- Holm correction across the 2 confirmatory contrasts.
- Power and precision are computed from the number of **independent clusters** (art units, or CPC subclass × filing year if art units are too coarse), not from the task count. This uses the DEV between-cluster variance, before P2-TEST is opened. If the achievable MDE exceeds 0.010, the report states the achievable precision; δ is not silently changed.

### 5.6 Gates
| Gate | Rule | If it fails |
|---|---|---|
| G2.0 data | Query text and corpus built; K-in-corpus coverage ≥ 80% for OUT references | Fix the corpus design once (pre-declared), else report the resource with its limits only |
| G2.1 engineering | E0/E1/E2 run on 20 DEV tasks with full cost accounting, no leakage of K into runtime | Engineering fix only; no outcome-driven tuning |
| G2.2 DEV headroom (informative, not a stop) | Oracle-per-query over E0-E3 on DEV, reported | Recorded. P2 still runs its fixed contrasts; P3 is not affected |
| G2.3 P3 entry (integrity only) | (1) the Search→Visit→Select trace logging is complete and replayable; (2) DEV feedback separates stage failures; (3) patches can be replayed without exposing gold at runtime; (4) an unused P3-TEST cohort exists | P3 waits until these are fixed. It is never stopped because E2 or E3 performed badly |

### 5.7 Deliverables
- The dataset construction code and manifest (counts, hashes, licences: USPTO public domain, PatentsView free).
- An aggregate-only public release of task IDs and labels, if the licences allow.
- P2 results with all negative and failed runs, and the cost table.

## 6. Paper 3 (P3-EGSHE): stage-specific harness evolution

Entry depends only on the integrity gate G2.3. A weak E2 is a reason to study learning from failures, not a reason to stop.

The core claim to test is: stage-localised failure feedback leads to a constrained harness repair, which gives a verified cross-task gain and transfers across models. It must beat generic (non-localised) feedback at an equal budget. The pack's own collision list already covers Adaptive Auto-Harness (arXiv 2606.01770), Harness-Delta Attribution (arXiv 2610.22466) and Meta² (arXiv 2611.05139). Those claims are not yet verified by this session and must be checked before the freeze.

This follows `docs/owner/02` sections 4-5 and `docs/owner/14`, with three changes:
1. **Data:** P3 develops on DEV and confirms once on P3-TEST (newest years). It never uses P2-TEST for selection.
2. **Primary contrast:** E5 − E4 on the stage frozen at the P2 endpoint decision (section 5.4). Secondary: E5 − E2.
3. **Transfer:** the frozen E5 patch set is applied to Qwen3-8B local and one cross-family API solver on P3-TEST. Report the grouped paired interval and the worst-group harm.

Retained from the pack:
- the editable-field registry;
- the at most N proposals per cycle;
- paired DEV replay;
- the placebo and wrong-stage patch ablations (E6/E7);
- rollback;
- break-even cost.

Stop rules:
- If no candidate patch passes paired DEV replay after the declared cycle cap, P3 reports a negative method result and stops.
- No extra cycles are added after a failure.

## 7. Product track

Unchanged from `docs/owner/03`. It shares the evidence layer (source IDs, locators, versions) but never sees evaluator labels. It ships a static baseline first; adaptive features stay behind a feature flag until P3 evidence exists.

## 8. Compute plan (estimates, to be re-measured)

| Item | Where | Estimate |
|---|---|---|
| OA set construction (joins, IPC labelling, splits) | dr-train CPU (72 threads, 125 GB RAM; the census already ran there in 14 min) | about 1 h CPU |
| Corpus encoding with PatEmbed-large passages (0.3-1.0M documents) | V100 after S8, or RunPod | about 5-20 GPU-h on V100 (scaled from DAPFAM: 189k passages took well under 1 h); re-measure on a 10k sample first |
| BM25 index | dr-train CPU | under 1 h |
| E2 agent on DEV (Qwen3-8B local) | V100 | at about 10-25 s per call and about 8 calls per task: 200 DEV tasks ≈ 4-11 GPU-h |
| API runs | OpenRouter | within section 4 envelopes |

## 9. Risks

| Risk | Mitigation |
|---|---|
| Training-data leakage (models may have seen 2008-2017 citations) | Newest window for P3-TEST; report a leakage probe (title-only recall of cited IDs) as a limitation check |
| Corpus does not contain the cited documents (coverage) | Gate G2.0; report coverage per split |
| 102/103 parsing errors (`citation_in_oa`, US-only cited art) | Validate against PANORAMA claim-level labels on the overlap; report the agreement rate |
| P2 headroom absent (as on DAPFAM) | P2 reports its fixed contrasts honestly (resource + method result, possibly negative); P3 continues if the integrity gate passes |
| Closed-world corpus inflates results | Primary results only on the open-population corpus; closed-world is labelled and secondary |
| Temporal rule removes valid prior art | RPD and OAER reported separately, with counts of excluded cited references |
| API price / model drift | Pin the route and price per dispatch; the reserve envelope; hard stop at USD 100 |
| Scope creep | Two papers only; product separate; no new arms after the freezes |

## 10. Do-not-repeat list

Everything in `docs/healthtech/research/paper2-precheck/README.md`: DAPFAM-dev BM25/RRF, fixed or per-section mixes, IPC-restricted queries, the class prior, and the label-free router. These ideas may be re-tested on the OA set only as part of a pre-declared arm (E0/E1), not as new tuning.

## 11. Owner decisions needed before execution (one package)

1. **Download** the PatentsView pre-grant text tables (`pg_published_application` abstract/claims text and the granted-patent text tables for the cited side). Exact files and sizes will be listed before transfer.
2. **Disk:** create `/data/ptp-paper2/` quotas, outside the Paper 1 52 GiB study cap (separate study ledger).
3. **GPU:** corpus encoding on the V100 after S8 finishes (or in parallel, if memory allows), or on RunPod with a USD cap.
4. **API:** approve the USD 100 sub-ledger and the first envelope (connection smoke, USD 5) with exact model IDs.
5. **PatEx-Gym public 100 tasks:** clone the repo (download approval).
6. **Freeze of this plan** after the S8 result is reported. The Paper 1 outcome goes into the P2 introduction as the confirmatory "query rewriting is not enough" evidence.

## 12. Immediate next steps (no approval needed; CPU, docs only)

1. Year histogram of eligible tasks from the existing OA files, then fix the split cut points (no retrieval run).
2. Measure the cited-document set size per split, to size the corpus and encoding cost.
3. Draft the P2 pre-declaration (arms, endpoint rule, gates) for freeze after the S8 report.
