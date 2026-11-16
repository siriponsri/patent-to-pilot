# P2-OA pre-declaration (DRAFT, NOT FROZEN)

Date: 2026-11-16. Status: **DRAFT.** It will be frozen only after the owner has seen the Paper 1 S8 result. Until then any line may change. After the freeze, nothing in sections 2-9 changes.

Source: merged plan **v2** ([PAPER-2-3-MERGED-PLAN-20261116.md](PAPER-2-3-MERGED-PLAN-20261116.md) on main, commit 0ee4d6e), sections 3 and 5. Split and size evidence: [OA-SPLITS.md](../paper2-precheck/oa/OA-SPLITS.md).

This draft grants no authority to download, encode, call a model or spend. Merged plan section 11 lists those owner decisions.

Items marked **[OPEN]** must be settled at the freeze, before any DEV run. Settling them may not use any retrieval number.

## 1. Questions and claims

- **RQ2.1.** On legally grounded cross-domain prior art, does a claim-element deficit-aware search controller (E3) recover more examiner-cited OUT references than strong fixed retrieval (E0) and a generic ReAct agent (E2), under the same per-task caps? E1 and E0-deep are descriptive anchors.
- **RQ2.2.** At which funnel stage (Search, Visit, Select) are OUT references lost? Does that differ for 102 and 103 citations?
- **RQ2.3 (descriptive).** How do citation-based labels relate to rejection-grounded labels?
  - The existing DAPFAM figure (13 of 9,480 dev positive pairs linked to an examiner 102/103 citation) is stated only under its exact-title mapping (precision not measured) and the 2008-2017 OA coverage.
  - It is not evidence about DAPFAM label quality.
  - The OA set's own non-rejection citations (`other_citation`) are described alongside.

The paper claims only what the confirmatory contrasts in section 6 test on P2-TEST. Everything on DEV is descriptive.

**Retrieving one cited document is evidence recovery.** It is not proof of anticipation or obviousness. A 103 rejection may combine several references; combination coverage is a secondary measure.

## 2. Data, tasks and labels (fixed by R1)

Definitions and numbers are in [OA-SPLITS.md](../paper2-precheck/oa/OA-SPLITS.md); its rules were committed before the first run.

- **Task** = a US application whose first non-final rejection (CTNF) was mailed 2008-2017.
  - That action must cite at least 3 US documents under 102/103 with `citation_in_oa = 1`.
  - At least one of them must be OUT under IPC3.
- **K(q)** = those cited US documents. Each carries:
  - its basis: 102 only, 103 only, or both;
  - IN/OUT under IPC3 (primary), IPC4 and section mismatch.
- **Unjudged is not negative.** Other citations of the same application (later actions, PTO-892/1449) are `other_citation`. They count neither as hits nor as negatives, and their share among selected documents is reported.
- **Claim version.** The first CTNF is the first action, so no response amendment can precede it. Preliminary amendments are not recorded in the files used, so they are unobservable here.
  - R1b reports the share of tasks whose first-action 102/103 rejection covers claim 1.
  - **[OPEN]** whether to restrict tasks to that subset; this must be decided without retrieval numbers.
  - The residual mismatch between published claims and rejected claims is reported as a limitation.
- **Splits** (R1 cut-point rule, contiguous complete filing years):
  - DEV for development;
  - P2-TEST, opened once for this paper;
  - P3-TEST, never touched by P2.
- **Evaluated samples.** Each split is a pool. The evaluated sample is the first n tasks by sha256(`p2-oa-split-v1|` + app_id).
  - DEV pilot: n = 20 (G2.1). DEV main: n = 200.
  - P2-TEST: n from the power rule (section 6.4).

### 2.1 Corpus

**Primary: open population.**
- Membership is fixed by document type and publication date only, never by citation status.
- Population = US utility and reissue grants plus utility pre-grant publications, published from the declared start year up to the split's upper date. Pre-grant publication types `utility`, `new` (PatentsView's label for 2001-2004) and `new-utility` are included. **[OPEN]** start year: 1976 or 1990, the only R1b candidates that meet G2.0. The choice is between gold coverage and encoding cost (section 2.4).
  - The choice may use R1b's size and gold-coverage aggregates.
  - It may not use any retrieval number.
- Deduplication: a pre-grant publication and the grant of the same application form one **application-level unit**. The unit's text is the pre-grant publication if one exists, else the grant.
- If the full population is unaffordable to encode, a hash-stratified sample of units is used instead (R1b reports rates 0.25 and 0.5). Gold coverage then drops roughly in proportion, and this is reported.
- OA labels are joined after membership is fixed.
- Gold coverage (`% K in corpus`, by IN/OUT and 102/103) is reported per split. Tasks with zero covered OUT references are counted, not dropped silently.

**Secondary: closed-world variant** (optional, always labelled "OA-derived closed-world"):
- Corpus = the union of K over the evaluated sample, plus distractors at 1:3.
  - Half of the distractors share a primary IPC4 with some cited document; the other half are uniform.
  - They are drawn by sha256 order with a declared salt.
- Used for cheap development and ablations only. It is never presented as open-corpus search.

### 2.2 Temporal settings (reported separately, never mixed)

- **RPD (Retrospective Public Discovery), primary.** A document is visible for task q only if it was published before q's filing date.
  - Cited references excluded by this rule are counted per split (R1b).
- **OAER (Office-Action Evidence Recovery), secondary.** Visible = published before q's filing date, or a US patent document with an earlier filing date that was published later, before q's first-action mail date.
  - This proxies 35 USC 102(a)(2) for AIA tasks (filed on or after 2013-03-16) and 102(e) for pre-AIA tasks.
  - The proxy uses US filing dates. Foreign priority, the pre-AIA invention date and AIA transition applications are not available, and this is stated as a limitation.
  - **[OPEN]** the exact rule text must be verified against USPTO sources (MPEP 2152-2154 and 2136) before the freeze.
- **Both settings:** q itself and every publication or patent of q's own application are never visible.

### 2.3 Coverage and eligibility

- A task is **OUT-eligible** in a setting if at least one OUT K document is in the corpus, visible in that setting and has a text record (K_OUT*).
- Metrics use K_OUT*. Strict recall over all of K_OUT is a secondary measure.
- Query text = title, abstract and claims of the application's pre-grant publication. This needs PatentsView text tables, not yet downloaded or approved. Applications without a pre-grant publication are counted and excluded as tasks.

### 2.4 Facts from R1/R1b that constrain the freeze

See OA-SPLITS.md for all numbers.

**Pools.** DEV = filing year 2011 (52,806 tasks), P2-TEST = 2012 (54,074), P3-TEST = 2013 (55,307).
- Filing year 2010 shows an unexplained completeness dip. Under the declared contiguity rule this excludes 2006-2009 as well.
- P2-TEST is entirely pre-AIA; P3-TEST is 72% AIA (proxy).

**Clusters.** About 570 art units per split, none above 1.5% of tasks. The art unit is the cluster unit; the IPC4 × year fallback is unlikely to trigger.

**Temporal settings.** RPD removes about 6% of K pairs (102(e) / 102(a)(2)-type art); the OAER proxy removes about 0.6%.

**Corpus start year.** OUT3 gold coverage in RPD is 0.93-0.94 for start 1976, 0.85-0.88 for 1990 and 0.68-0.75 for 2001. G2.0 (≥ 80%) therefore requires start 1976 or 1990.

**Encoding cost.** The full RPD population costs about 175-205 V100-h fp32 (5.5-6.5M units), and OAER about 250 h. A random sample of the population cannot meet G2.0. Encoding cost, not task count, is the binding resource for the open-population corpus. The owner decision on GPU or RunPod (merged plan section 11.3) must use these figures, not the plan's earlier 5-20 GPU-h.

**Claim version.** The first action's 102/103 rejection covers claim 1 in about 89% of tasks. Preliminary amendments cannot be observed in the downloaded files.

**Family chains.** Chains cross splits in at least 275 K pairs (a cited document filed later than the task is a later-split task). Exact removal needs the continuity tables (download approval).

## 3. Tools (identical for every arm)

| Tool | Definition |
|---|---|
| `dense_search(text, k)` | PatEmbed-large, same weights, pooling and passage windowing as Paper 1 B0; document score = max over passages; k ≤ 200 per call. **[OPEN]** query window rule (single window vs multi-window max), pinned from Paper 1 / DAPFAM stage 0 practice, not from OA results |
| `bm25_search(text, k)` | In-repo BM25 (`evaluation/dapfam_acquisition.py`, the implementation used in the DAPFAM pre-checks) with its defaults k1 = 1.5, b = 0.75, ε = 0.25; no tuning |
| `cpc_filter(ids, codes)` | Keeps candidates whose IPC4 is in `codes` (IPC, since CPC is not downloaded) |
| `citation_expand(id, k)` | Backward citations of a corpus document, only those visible for q in the active setting. It never uses q's own citations, OA data or any forward citation to q |
| `visit(id)` | Returns title, abstract and claims, truncated to 1,024 tokens (pinned tokenizer), with passage locators |

No tool can read OA data, the file wrapper or q's citation records. G2.1 tests this (section 7).

## 4. Arms

All arms share these caps per task:
- surfaced pool **P = 200** documents (deduplicated union of everything returned);
- **V = 20** visits;
- final selection **S = 10** ranked documents;
- at most **8** search calls (search, CPC hop and citation hop each count as one).

Compute differs between arms and is reported (section 5.3).

| Arm | Definition |
|---|---|
| **E0** | One fixed retriever: dense, BM25, or RRF(dense, BM25; k = 60). Chosen on DEV main by OUT Search-R at P = 200; tie goes to dense. One search call, top 200 = pool. Visit = top 20, select = top 10 of that ranking. No LLM |
| **E0-deep** (descriptive) | The E0 retriever with k = 1,000, then a fixed reranker over the 1,000; reranked top 200 = pool, visit = top 20, select = top 10. **[OPEN]** reranker: at most two pre-listed candidates, both pinned before DEV; chosen on DEV main by OUT Search-R. Deep-pool recall@1,000 is reported |
| **E1** (descriptive) | Fixed multi-query schedule, 8 search calls, no LLM: dense and BM25, each on (1) full query, (2) claims only, (3) abstract only, (4) first independent claim. RRF (k = 60) over the 8 lists, top 200 = pool, visit top 20, select top 10 |
| **E2** | Generic static ReAct agent with actions `search` (dense or BM25, own query text, k ≤ 50), `cpc_filter`, `citation_expand`, `visit`, `select`, `stop`. Same caps, no cross-task memory, frozen prompt. Selection may name only visited documents |
| **E3 (method under test)** | **Claim-element deficit-aware search (CEDS).** See below |

E3 (CEDS) works as follows:
- **Elements.** The first independent claim is split into elements by a bounded LLM call, constrained to contiguous spans of the claim text. No gold is used. The split is cached per task and counted in cost.
- **Coverage state.** After every `visit`, a bounded LLM extraction proposes, for each element, a quote from the visited document that discloses it.
  - A quote counts only if it matches the visited text byte-for-byte after the declared normalisation (the mechanical check).
  - An element is covered once any visited document has a valid quote for it.
- **Next action.** Each action targets the least-covered element (ties go to claim order), choosing one of:
  - an element-specific query;
  - a cross-domain reformulation of the element's function (removing domain nouns);
  - a CPC hop to IPC4 classes of documents that covered other elements;
  - a citation hop from the best partial match.

  The action type follows a frozen rule. **[OPEN]** whether the LLM may choose the type within a closed schema.
- **Stop.** All elements are covered, or the caps are spent.
- **Selection.** Up to 10 visited documents, ranked by the number of covered elements, then by retrieval rank.

E3 novelty is not assumed:
- Before the freeze, a literature check must state exactly what E3 adds and cite the closest work: coverage-guided search, claim charting, PatentAgentBench's claim-charting suite, element-wise 103 reasoning.
- If an equivalent method exists, E3 becomes a re-implementation and the contribution is reframed.

Common to E2 and E3:
- **Solvers.**
  - The confirmatory solver is **Qwen3-8B local** (pinned weights, fp16/eager, greedy): reproducible and with no API cost.
  - One API solver (route and price pinned on the dispatch day) is secondary and descriptive.
- **Decoding.** Strict JSON from a closed schema: grammar-constrained decoding locally, JSON schema for the API. No repair: an invalid action stops the controller.
- **LLM caps per task:** ≤ 30 LLM calls; ≤ 60,000 prompt tokens + declared output caps; wall time ≤ 900 s. A refused call is never retried.
- **Fallback (intention-to-treat).**
  - On an invalid action, an empty pool or a budget refusal with an empty own pool, the arm's output is the **E1 ranking** for that task.
  - The fallback's compute is charged to the arm.
  - The fallback rate is reported per split.

## 5. Metrics and denominators

### 5.1 Funnel recall
For task q and arm a:
- Search set = the surfaced pool (≤ 200).
- Visit set = the visited documents (≤ 20). For E0/E0-deep/E1 this is the top 20.
- Select set = the final ≤ 10.

- **Search-R(q)** = |K_OUT* ∩ Search set| / |K_OUT*|. **Visit-R** and **Select-R** are defined the same way.
- Query-macro over **OUT-eligible tasks of the evaluated sample**. A missing or failed output scores 0 and stays in the denominator.
- **Primary endpoint (fixed now, plan v2 section 5.4): OUT Select-R in RPD on the open-population corpus.**
- Each recall is also reported:
  - stratified by 102-only / 103-only / both;
  - for IN (harm check, own IN-eligible denominator) and ALL;
  - in OAER (secondary setting);
  - on the closed-world corpus (labelled).

### 5.2 Secondary
- Search-R and Visit-R (funnel losses), micro recall.
- nDCG@10 of the Select list, binary gain on K (unjudged = 0, disclosed).
- **Strict recall**: denominator = all of K_OUT, including documents not covered.
- **Combination coverage:** the share of tasks whose Select set holds all K documents of the first action.
- Share of `other_citation` documents in the Select set (descriptive, not relevance).
- OUT recall under section mismatch instead of IPC3.
- For E3: element coverage rate and quote validity rate.

### 5.3 Cost
Per task and per arm, reported for every run, failed runs included:
- tool calls, LLM calls, prompt and output tokens;
- encoder passages, GPU seconds, wall seconds, USD;
- fallback count.

Cost-effectiveness = OUT K documents found per GPU-hour and per USD (descriptive).

### 5.4 Grounding (mechanical; no LLM judge)
For every E2/E3 `select`:
- the document exists in the corpus;
- it was visited;
- every quoted span matches the visited text byte-for-byte after the declared normalisation (Unicode NFC, collapsed whitespace), with a valid locator.

## 6. Confirmatory analysis (P2-TEST only)

### 6.1 Endpoint
OUT Select-R, RPD, open-population corpus, Qwen3-8B solver. It is fixed now and is not chosen from DEV results.

### 6.2 Contrasts
Two-sided α = 0.05, Holm correction over two contrasts:
- **C1 (primary):** E3 − E0.
- **C2 (secondary):** E3 − E2.

E1 − E0, E0-deep − E0 and E2 − E0 are descriptive anchors, with intervals but no multiplicity claim.

### 6.3 Inference
- **Unit:** paired per-task differences on the identical evaluated sample.
- **Interval:** cluster bootstrap with clusters = art unit of the task's first action; 10,000 resamples, percentile 95% CI, seed declared at the freeze.
  - Cluster fallback: if DEV shows more than 20% of tasks in one art unit, or fewer than 30 art units in the sample, clusters become IPC4 subclass × filing year. This rule is fixed now; the choice is mechanical.
- **p-value (for Holm):** cluster-level paired sign-flip randomization test, 10,000 draws, two-sided.
- **Interpretation:** δ = 0.010 absolute, as in Paper 1.
  - **Superiority** if the Holm-adjusted p < 0.05 and the CI lies above 0.
  - **Practical equivalence** if the whole CI lies within ±δ.
  - **Inconclusive** otherwise.
- **Harm check:** non-inferiority on IN Select-R, margin −0.020.

### 6.4 Sample size from independent clusters
Computed after DEV main and before opening P2-TEST:
1. Aggregate per-task differences of the endpoint to cluster means on DEV main, for each contrast.
2. Estimate the between-cluster SD σ_c.
3. Required number of clusters G = ((z₀.₉₈₇₅ + z₀.₈₀) · σ_c / 0.010)², with z₀.₉₈₇₅ = 2.241 (Holm worst case, α/2 two-sided).
4. Tasks are drawn from P2-TEST in sha256 order until the sample spans G clusters, subject to the approved GPU/USD envelopes.
5. If the envelope binds, the achievable MDE from the cluster count actually reached is stated. δ is not changed.

## 7. Gates

| Gate | Rule | If it fails |
|---|---|---|
| **G2.0 data** | Query text and the open-population corpus built for DEV main. K_OUT gold coverage in RPD ≥ 80% (documents in corpus, visible, with text) | Fix the corpus design once (pre-declared: earlier start year or full instead of sampled population), else publish the resource with its limits only |
| **G2.1 engineering** | E0-E3 run on 20 DEV tasks with full cost accounting. Leakage audit passes: no tool response contains q's own documents, OA data or q's citation records (checked by ID); the visibility filter is verified on every returned ID in both settings | Engineering fix only; no outcome-driven tuning |
| **G2.2 DEV headroom** (informative, not a stop) | Oracle per task over E0-E3 on DEV main, reported | Recorded. P2 still runs its fixed contrasts; P3 is not affected |
| **G2.3 P3 entry** (integrity only) | (1) the Search→Visit→Select trace logging is complete and replayable; (2) DEV feedback separates stage failures; (3) patches can be replayed without exposing gold at runtime; (4) an unused P3-TEST cohort exists | P3 waits until these are fixed. It is never stopped because E2 or E3 performed badly |

## 8. Leakage probe (limitation check, mechanical)

- **Input:** for each task, the solver gets only the application title and filing year.
- **Task:** list up to 10 US patent or publication numbers that an examiner would cite.
- **Score:** exact-ID hits in K after number normalisation.
- **Run on:** DEV main (n = 200), and on P2-TEST at its single opening, as part of the same run.
- Reported as hit rate and the share of tasks with ≥ 1 hit, for each solver.
- It is a limitation check only: it does not gate or change any confirmatory result.
- P3-TEST holds the newest years because they are the least exposed. Even so, leakage cannot be excluded.

## 9. Stop rules and honesty

- Every run, failed or not, is kept with its cost. There are no retries of a consumed task attempt and no output repair.
- No arm, prompt, tool, cap, metric or endpoint changes after the freeze.
- An engineering fix after the freeze is documented, re-qualified on DEV, and never informed by P2-TEST.
- P2-TEST is opened once, after the power computation and the owner's go.

## 10. What stays NOT_RUN at this draft

- Query and corpus text: not downloaded; download not approved.
- Open-population corpus, closed-world variant and BM25 index: not built.
- Encoding: not run. OA-SPLITS.md sizes the cost and shows that the open population is far larger than the closed-world corpus.
- E0, E0-deep, E1, E2 and E3 on any split: not run. Reranker, query window and E3 action-type details are [OPEN].
- E3 literature check: not done.
- Leakage probe, cluster statistics and power: not computed.
- PANORAMA cross-check of the 102/103 labels: not run.
- PatEx-Gym compatibility pilot: not cloned (download not approved).
- OAER rule text: not verified against USPTO sources.
- P3 (EG-SHE): not started; it depends only on G2.3.

## 11. To settle at the freeze

1. The [OPEN] items: open-population start year (and sampling rate if needed), the claim-1 restriction, the OAER rule text, reranker candidates, query window, E3 action-type rule, bootstrap seed.
2. Exact model pins: Qwen3-8B revision, API route, price, per-dispatch USD cap.
3. The per-task LLM caps in section 4, if the G2.1 pilot shows they are infeasible. They may change only at G2.1, and only on cost and engineering evidence.
4. The owner's go after the Paper 1 S8 report.
