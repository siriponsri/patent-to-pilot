# SACR versus Technical-Relation Graph Retrieval
## Advisory assessment of wow factor, business impact, and publication impact

**Date:** 10 November 2026  
**Project:** Patent-to-Pilot / Solution Scout  
**Status:** COMPARATIVE_ADVICE / NO_NEW_EXPERIMENT / NO_PROTOCOL_CHANGE  
**Scope:** Compare the attached SACR continuation handoff with the subsequent DAPFAM graph contribution proposal. Preserve the owner's latest direction: DAPFAM is the research track; MTM is the separate product track.

## Executive judgment

The graph proposal offers the more compelling discovery narrative and a potentially broader scientific question. SACR offers the lower incremental corpus-processing burden and a more direct integration path into the existing MTM retrieval product. Neither document establishes a retrieval improvement for its proposed method. The historical V4 gain is not evidence for either SACR or graph retrieval.

My recommendation is not to discard SACR because a graph sounds more advanced. Preserve its reusable infrastructure and, if feasible within a bounded plan, use a frozen SACR configuration as a development comparator. Treat graph construction and navigation as a new hypothesis with a cost/fidelity gate, not an automatic replacement for the current product engine. Do not require MTM research evaluation as a condition for DAPFAM research.

### Relative design ratings

These are advisory judgments on a five-point scale, not measurements, acceptance probabilities, revenue forecasts, or a validated scoring instrument. A score of 3 means a credible but conditional opportunity; 4 means a stronger opportunity if the identified evidence is obtained. No total is calculated because the three dimensions have different objectives.

| Requested dimension | SACR | Graph proposal | Interpretation |
|---|---:|---:|---|
| Wow factor: plausible demonstration and story | 3/5 | 4/5 | A source-backed cross-field discovery path is easier to show than query-side ranking improvements. A decorative graph alone adds no scientific value. |
| Business impact: near-term integration with the existing MTM product | 4/5 | 2/5 | SACR reuses the corpus index; graph retrieval requires an additional corpus-wide extraction and maintenance layer. Both remain unvalidated as product improvements. |
| Publication impact: conditional scientific ceiling | 3/5 | 4/5 | Graphs permit a richer decomposition of representation, topology, and control, but only if strong controls show which component matters. |

Longer-term business potential could reverse the second ranking if a reusable, correct, economical technical knowledge layer supports repeated tasks. The documents provide no customer evidence for that scenario. Under current solo resources, SACR has the clearer route to a completed bounded study; this is not a higher estimated journal acceptance rate.

## 1. What is being compared

### A. Original method-first contribution: SACR

The attached long-run handoff describes selective abstraction that preserves source-linked requirements, searches a frozen dense index with up to three views, and selects a fixed-size result using anchor and local relation/condition coverage. Its proposed acquisition searches the full eligible index, not merely the original top-30 or top-200 list. The maximum union is 600 families, followed by a final depth of 200. [H, sections 12 and 15]

The source-level prior-art note describes the selector as:

`coverage = max_block max_passage [(1-beta) * mean(component similarities) + beta * min(component similarities)]`

The minimum is taken inside one passage before maximizing across passages. Maximizing across blocks permits partial feature matches; it is not a proof that every requirement is satisfied. The local score remains an embedding-similarity proxy. [S]

Its original study plan used MTM for the MedTech context and native DAPFAM as an external anchor. The new owner instruction separates DAPFAM research from MTM product, so the old dual-benchmark continuation is a comparison scenario, not a request to reinstate that scope. [H, section 1; G, section 6]

### B. New contribution proposal: corpus-side technical-relation retrieval

The graph proposal extracts technical relation instances from corpus documents, binds them to source evidence, connects them through declared descriptors/aliases, and searches beyond a dense candidate shortlist. It compares the same extracted information without traversal, fixed graph traversal, and LLM-guided traversal. The proposed contribution is controlled empirical attribution, not merely graph construction. [G, sections 4-8]

The specific traversal and family-scoring operator still needs an executable, frozen specification. The four-system core is a dense baseline B0, structured non-traversing S, fixed graph G, and LLM-guided graph A. [G, section 8]

### Changes that must not be conflated

There are four independent choices: research dataset, model capability, retrieval architecture, and product/research separation. A smaller DAPFAM research scope also benefits SACR. A larger LLM can also be used in a SACR development variant. Neither benefit is evidence for graph topology.

| Design property | SACR | Graph proposal |
|---|---|---|
| Primary intervention | Query representation and candidate selection | Corpus representation and acquisition/navigation |
| Corpus index | Existing PatEmbed passage index | Additional technical relation index/graph |
| Can retrieve families missing from the original pool? | Yes, through full-index searches of new views | Yes, through corpus-wide entry and traversal |
| Dependence on dense similarity | Central to acquisition and coverage scoring | Not required by the proposed primary entry; must be disclosed if added |
| Technical fidelity risk | Query abstraction, condition attachment, local matching | Those risks plus corpus extraction, alias merging, graph edges, and search paths |
| Natural experimental contrast | Generic versus preserving views; mean versus bottleneck selection | Same information without traversal; fixed versus LLM traversal |
| Current scientific status in the supplied material | Real pilot/full-dev effects absent | Proposal, not preregistered, not run |

The historical V4 result, MTM dev hit@20 0.180 to 0.197, is a top-30 reranking result. It is not a lower bound on SACR or graph effectiveness. [H, lines 59-66]

## 2. Wow factor

### SACR: less theatrical, potentially clear practical intelligence

A credible demonstration would show a user's original need, which contextual terms were generalized, which roles and requirements were retained, and which newly retrieved families survive selection. Its most persuasive story is not a query rewrite but a controlled counterexample: generic abstraction loses an important relation, while the source-preserving variant finds a useful candidate without that distortion.

This is a proposed demonstration, not an observed result. A source-span match proves where words came from, not that an abstraction retained their meaning.

SACR can also have an attractive relational UI. A graph-shaped visualization is not exclusive to a graph retrieval backend. A displayed explanation must disclose whether it is an actual search trace or a subsequent interpretation.

### Graph retrieval: a more visible discovery story

A grounded path from a technical requirement through a shared function/mechanism to an unexpected field is inherently easier to narrate. A good demonstration would expose the source supporting each edge, identify inferred aliases separately, and show a real family outside the baseline pool. It should also expose dead ends and missed targets rather than display only selected success cases.

The stronger story carries a larger trust burden: a correct quotation at each end does not prove that the intermediate equivalence or whole path is valid. Navigation into a related function is not proof of engineering feasibility or an inventive connection.

### Novelty discount

Function-effect-structure knowledge graphs for design-by-analogy are already represented by DbAKG. MemGraph combines LLM-derived entities/ontologies with patent matching, although that is not the same corpus-navigation task. Therefore, "LLM plus patent graph" has limited research novelty even when the demo is visually impressive. [W1-W2]

**Verdict:** graph retrieval wins the demonstration ceiling; neither wins scientific novelty merely through presentation.

## 3. Business impact

### 3.1 Define business value as a hypothesis

For an MTM-based Solution Scout, useful product hypotheses are: better candidates within a limited reading budget, less source-checking effort, clear uncertainty, acceptable latency, and inexpensive updates. No document provides customer interviews, willingness-to-pay evidence, validated time savings, or ROI. Scores below therefore concern architectural fit, not proven commercial impact. [H, section 19]

### 3.2 Why SACR has the nearer integration path

SACR reuses existing corpus vectors and concentrates additional semantic work at query time. This avoids a second extraction pass over every MTM document and permits a source-preserving query/coverage component to be introduced without replacing the whole document representation.

This is a relative advantage, not proof of low latency. Generating profiles, embedding components, making several full-index searches, and scoring unions can still be expensive. Invalid views and fallback behavior must remain visible. The product should retain a working baseline until a challenger demonstrates a useful quality-cost trade-off. [H, sections 12, 15]

### 3.3 Where graph retrieval could add longer-term value

A reusable technical relation layer could support mechanism browsing, evidence-linked comparisons, aliases across disciplines, inspection of design constraints, and revisiting a knowledge area without re-parsing every document. These are potential capabilities, not existing product features or validated demand.

The expensive part is not necessarily graph storage. It is obtaining reliable relations, deciding what can be normalized together, preserving source/version history, handling new documents, and detecting that an error in a widely used alias changes many retrieval paths. A public patent corpus and a standard graph stack are not an exclusive business asset by themselves.

### 3.4 Scale: family counts are not token counts

The proposal uses 45,336 DAPFAM families; the handoff reports 899,838 MTM families. The latter is approximately 19.85 times as many families. Different document lengths and source fields prevent treating this as a measured runtime multiplier. [G, section 6; H, section 3]

The following is hypothetical arithmetic only: one extraction call per family, identical average seconds per call, no batching effect, no alias construction, no retries, and no update costs.

| Assumed average per-family generation | DAPFAM, 45,336 families | MTM, 899,838 families |
|---|---:|---:|
| 10 seconds | 125.9 GPU-hours | 2,499.6 GPU-hours |
| 30 seconds | 377.8 GPU-hours | 7,498.7 GPU-hours |

Multiple windows, longer claims, qualification extraction, and normalization can increase this substantially; efficient non-LLM components or batching can alter it. These are not measured V100 rates or promised completion times. The small-corpus research study must not be presented as evidence that corpus-wide product deployment is affordable.

For measured costs expressed in a common unit, a simple accounting identity is:

`total_cost(method, Q) = initial_index_cost + update_cost + Q * mean_online_query_cost`.

If updates are ignored and graph online cost is lower, the break-even query volume is:

`Q* = (graph_index_cost - SACR_index_cost) / (SACR_online_cost - graph_online_cost)`.

If the denominator is zero or negative and graph indexing is more expensive, query volume alone does not create a compute-cost advantage. Greater quality could still justify greater cost, but that is a different business case. No numerical break-even volume can be justified from the supplied evidence.

### 3.5 Rights and transfer boundaries

The handoff records DAPFAM and PatEmbed as non-commercial research resources. A derived DAPFAM graph is not automatically a shippable MTM business asset, and using MTM documents does not change the encoder's terms. Review exact data, model, code, and derived-artifact rights separately before release. This is a documented project constraint, not a new legal determination. [H, lines 445-454]

A DAPFAM method win would justify an MTM engineering-transfer investigation, not a claim of product effectiveness. That transfer can be a product task later; it does not have to become a second research benchmark now.

**Verdict:** SACR has the stronger near-term architectural fit. The graph has a potentially larger reusable-knowledge opportunity, with significantly more unproven cost and maintenance assumptions.

## 4. Publication impact

### 4.1 Separate ceiling, maturity, and acceptance

Publication impact is not identical to a journal's impact factor. Here it means the importance and distinctiveness of the question, the strength of the answer, and the possibility that others can reuse the findings or instrument. No acceptance probability or future citation count is estimated.

The two proposals are at different implementation stages, but neither has an established retrieval result. Many passing engineering tests do not increase the estimated effect size. Likewise, a failed structured-output example does not demonstrate that the scientific hypothesis is false. [H, sections 3 and 19; G, status]

### 4.2 SACR's strongest defensible contribution

A credible claim would be a tested query-side mechanism: preserve source-linked relations and conditions during selective abstraction, then test whether local joint evidence scoring adds recovery beyond ordinary multi-query acquisition while reusing the same corpus index.

This is more specific than "LLM query rewriting improves retrieval." Query2doc already establishes LLM-generated query expansion. ColBERT establishes fine-grained interaction over precomputed document representations, though its token-level scoring is different. SACR's own prior-art note also acknowledges functional-analogy and conjunction precedents. [W3-W4; S]

The decisive evidence is the matched generic/preserving by mean/bottleneck panel, plus the source-anchor/lexical control. A gain only over the original anchor would not isolate the proposed source-preservation or bottleneck mechanism. [H, section 12]

Risks to publication value include small unstable gains, dominance by a generic multi-query control, collapse to the unchanged anchor through generation failures, and no measured advantage over a simpler source-preserving method. A strong negative result can still delimit the method, but does not guarantee publication.

### 4.3 Graph retrieval's strongest defensible contribution

The proposal's larger scientific opportunity is the separation of content representation, cross-record relations, and search control. It could show that structured content is enough; that fixed traversal adds value; or that LLM control has an incremental benefit worth its cost. Each conclusion changes what a patent-search system should build.

The novelty burden is correspondingly greater. PHAGE already evaluates graph-informed patent representations on DAPFAM; HippoRAG 2 already studies graph propagation with online LLM use. Thus the dataset, a graph, and an LLM controller do not independently establish originality. The paper needs the qualified-relation operator and its matched comparisons, not merely a new combination of component names. [W5-W6]

The new document is strongest as a controlled empirical study. Its algorithmic novelty remains provisional because entry, edge qualification, stopping, family aggregation, and scoring still require a complete executable specification. [G, sections 4 and 8]

### 4.4 What reviewers need to distinguish

| Reviewer question | SACR evidence needed | Graph evidence needed |
|---|---|---|
| Is the gain caused by additional generated text? | Generic versus preserving views with matched information and model budget | Same extracted content searched without traversal; serialized-text control |
| Is the method just doing more retrieval? | Same final k; union and selection outcomes; actual search costs | Same final k and declared frontier/visit budget; deeper-search control |
| Does the named mechanism matter? | Same union/profile/passages, mean versus bottleneck | Fixed traversal versus non-traversing search; relation perturbations |
| Is the agent necessary? | Do not make an agent claim if not tested | LLM versus fixed navigation; LLM planning over structured non-graph search |
| Did the new model or text coverage cause the gain? | Pin model and allowed/actually read text | Share extraction outputs across S/G/A; coverage-matched diagnostics |
| Is the evidence transferable? | Do not conflate MTM and native DAPFAM | A DAPFAM-only result remains dataset-scoped; no automatic MedTech/time-machine claim |

Identical final output size is not identical computation or information exposure. Both must be reported. A graph extractor reading full claims while the dense baseline truncates them creates a coverage confound, not proof of topology value.

### 4.5 Venue fit, as an advisory assessment

World Patent Information explicitly covers IP information retrieval, search, text mining, system evaluation and benchmarking. Both proposals fit that topical scope if they answer a useful patent-information question with appropriate evidence. A graph is not a prerequisite for relevance to the journal. [W7]

For an engineering-design audience, the graph proposal has a natural conceptual connection to analogy search, but citation recovery alone does not establish improved design creativity or engineering feasibility. DbAKG is simultaneously a positioning reference and a close competitor. [W1]

For a general IR methods audience, either proposal would need strong comparisons and a clearly specified mechanism. A single DAPFAM study limits breadth; it does not automatically make publication impossible or require that MTM be restored as a research benchmark. Strong within-dataset controls can support a scoped claim. Venue-specific acceptance cannot be inferred from the idea alone.

**Verdict:** the graph has the higher conditional scientific ceiling; SACR has the narrower and cheaper hypothesis to close. Evidence quality can reverse the ranking. A well-executed SACR study is stronger than an incompletely specified graph proposal.

## 5. Outcomes and honest contribution claims

| Result pattern | Defensible interpretation |
|---|---|
| SACR beats generic views and the matched source-anchor control | Evidence for the specific query-preservation/selection design, within the tested setting |
| SACR helps versus baseline but not generic multi-query | A multi-query system gain; the special SACR mechanism is not established |
| Structured S beats B0, without demonstrated G-over-S benefit | Structured information may help; topology benefit remains unresolved |
| Fixed G beats S, without demonstrated A-over-G benefit | Traversal may help; the LLM controller is not yet justified by effectiveness |
| A beats G and suitable planning controls at comparable budgets | Evidence for search-control value in the tested graph |
| Larger union improves, final top-200 does not | Candidate discovery/selection mismatch; no fixed-depth improvement |
| No method improves | A scoped negative empirical result, if implementation/fidelity/controls were adequate |

A nonsignificant difference is not equivalence. Interpret interval width against a prospectively selected practical margin; a weakly powered null result is inconclusive rather than proof that a component is useless.

## 6. Corrections and common risks visible across the two documents

### Native population caution

The new graph proposal repeats 349 OUT-eligible development queries and 556 OUT-eligible protected queries from older project records. The attached handoff explicitly warns that the 349 count belongs to a project-filtered setting and must not be assumed to be the native OUT denominator. Preserve the split assignments, but determine the actual native eligible counts under the pinned release through the authorized curator. This comparison does not silently reconcile those numbers. [H, lines 61-66 and section 9; G, section 6]

### Grouped development uncertainty

The graph proposal records a large shared-target component of 374 queries in a 474-query development set. If confirmed for the staged split, balanced four-fold component-disjoint CV is not available. Do not split that component simply to obtain convenient folds, or treat query-level resampling as independent evidence. This is a dataset/evaluation issue shared by SACR and graph research, not a graph-specific defect. [G, section 9.3]

### Current state versus historical handoff

The attached handoff is a snapshot at commit 85de9268; the graph proposal names 287fabae. This assessment compares their research designs. Pending approvals and job states in those snapshots are not asserted as the current live server state.

### Prior exposure and contamination

Historical baseline exposure must remain disclosed. No explicit citation edge does not imply that pretrained models never saw those patents. Incomplete citation judgments measure known-link recovery, not exhaustive relevance or real engineering transfer. [G, sections 6 and 10; H, section 15]

## 7. Reuse without confusing the contributions

Reusable foundations include source spans and hashes, typed relation records, failure and cost accounting, the native evaluator, family identity, and isolated data staging. Corpus alias management, technical relation connectivity, traversal, and graph-scale update policy are additional work.

Reusing a SACR profile for graph extraction does not validate corpus-side extraction: long claims and many document instances change both the cost and the failure surface. Conversely, a successful graph experiment does not retroactively validate SACR.

The owner can retain DAPFAM-only research and MTM-only product under either method. The dataset decision should not force the algorithm decision.

## 8. Decision recommendation for a solo researcher

1. Keep the owner's two-track separation. Maintain MTM's useful product workflow independently of whether the new research wins.
2. Preserve SACR rather than erasing it. A bounded fixed configuration on the same DAPFAM input is a useful development reference if its generation path is viable; do not rebuild every historical dual-benchmark panel just to obtain that reference.
3. Make the graph pivot conditional on source-fidelity and full-corpus cost feasibility. A corpus subset is appropriate for engineering measurements, not a smaller easier retrieval benchmark used to claim a DAPFAM win.
4. Test the value of the same structured information before attributing anything to edges. Implement fixed traversal before adding an adaptive controller; the expensive agent should answer an incremental question.
5. Choose the final scientific claim and limited panel before protected evaluation. Do not carry B0, SACR, S, G, A and a published comparator as six systems while calling it a four-system study.

One permissible planning example is to keep SACR as development-only reference while final B0/S/G/A isolates the graph question. That would not support a new confirmatory test claim of beating SACR. Another is final B0/SACR/S/G, dropping the agent claim. These are panel design examples, not adopted protocols or permission to open test.

If the overriding objective is a finished bounded paper plus the next MTM product increment, prioritize closing SACR evidence. If the objective is a higher-ceiling research question and its extra indexing budget is feasible, prioritize the controlled graph study, retaining the simpler methods as references. Neither route justifies unlimited model/schema search.

## 9. Bottom line

- **Wow factor:** graph, provided the discovery path and sources are real.
- **Near-term business impact:** SACR or the already functioning baseline, not an untested full-corpus graph migration.
- **Publication ceiling:** graph's controlled question; **lower-risk completion:** SACR's narrower intervention.

The best contribution is not the system with the most sophisticated diagram. It is the smallest defensible answer showing what extra structure or computation actually buys, and when it does not.

## Sources and verification boundaries

### Requested project sources

**[H]** Owner-uploaded `PTP_MTM_DAPFAM_LONG_RUN_HANDOFF_20261110_TH_EN.md`, prepared 10 November 2026. Especially sections 1, 3, 9, 12, 14-15 and 19. Snapshot: `85de926818e8f9ed5a162386c9de57e5d0ab0648`. This is a planning handoff, not a new execution receipt.

**[G]** `DAPFAM_GRAPH_RETRIEVAL_GAP_AND_CONTRIBUTION_20261110_EN.md`, supplied in this conversation. Especially sections 4-12. Status proposal/not run. This comparison does not independently re-verify every reference in its 24-item literature list.

**[S]** [SACR targeted prior-art comparison, pinned to the handoff snapshot](https://github.com/siriponsri/patent-to-pilot/blob/85de926818e8f9ed5a162386c9de57e5d0ab0648/docs/healthtech/research/SACR_PRIOR_ART_COMPARISON_20261110_EN.md). Read through the connected GitHub tool for this comparison. Its limited-access literature statements are not treated as novelty clearance.

### Primary sources checked for this assessment

**[W1]** Jing, L., et al. (2025). *Knowledge graph-assisted design-by-analogy: promoting product innovation through structured analogical knowledge retrieval.* AI EDAM 39, e20. [Publisher](https://www.cambridge.org/core/journals/ai-edam/article/knowledge-graphassisted-designbyanalogy-promoting-product-innovation-through-structured-analogical-knowledge-retrieval/9A6F1AFD04B956722EAFB62DEDC9ECFD). DOI: 10.1017/S0890060425100103. Primary abstract and selected method/conclusion text checked; no numerical comparison with our proposals.

**[W2]** Xiong, Q., et al. (2025). *Enhancing the Patent Matching Capability of Large Language Models via the Memory Graph.* SIGIR 2025, 337-347. [Official conference entry](https://sigir2025.dei.unipd.it/detailed-program/paper?paper=3c7781a36bcd6cf08c11a970fbe0e2a6); [author text](https://arxiv.org/html/2504.14845v1). DOI: 10.1145/3726302.3729970. Used as a scope/novelty collision, not proof of patent-family recall.

**[W3]** Wang, L.; Yang, N.; Wei, F. (2023). *Query2doc: Query Expansion with Large Language Models.* EMNLP 2023. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.585/). Primary record/abstract checked. No general-domain gain is extrapolated to patents.

**[W4]** Khattab, O.; Zaharia, M. (2020). *ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT.* SIGIR 2020. [Author record](https://arxiv.org/abs/2004.12832). DOI: 10.1145/3397271.3401075. Late interaction is prior art; SACR is not represented as an implementation of ColBERT.

**[W5]** Yoo, Y.; Xu, Q.; Wu, Z.; Cao, L. (2026). *Heterogeneous Dependency Graph-Guided Attention for Patent Representation Learning.* arXiv:2605.10073v2, preprint. [Author full text](https://arxiv.org/html/2605.10073v2). Method and DAPFAM evaluation passages checked. Intra-document graph-informed encoding is distinguished from corpus-graph navigation; no cross-paper score comparison is used.

**[W6]** Jimenez Gutierrez, B., et al. (2025). *From RAG to Memory: Non-Parametric Continual Learning for Large Language Models.* ICML 2025, PMLR 267:21497-21515. [Proceedings](https://proceedings.mlr.press/v267/gutierrez25a.html). HippoRAG 2; primary abstract checked. No QA/associative-memory effect is treated as patent retrieval evidence.

**[W7]** Elsevier. *World Patent Information: journal description.* [Official publisher page](https://shop.elsevier.com/journals/world-patent-information/0172-2190), accessed for this assessment. Used for topical scope only; no acceptance rate, journal metric, fee, or submission guarantee is asserted.

---

**Actions performed:** read the two supplied Markdown documents, inspect the pinned SACR prior-art note, and check the selected primary sources above. Create this comparison note. No repository edits, model deployment, protected data access, experiments, publication, or resource reservation.
