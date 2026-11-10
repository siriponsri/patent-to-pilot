# Closest-work audit for the three-study programme

Date: 10 November 2026. Status: BOUNDED_REVIEW / NO_REPLICATION / NO_NOVELTY_CLEARANCE.

[Master](../../../../MASTER-PLAN.md) · [Actual component/results](../../../../INDEX-PLAN.md)

## 1. Coverage and evidence levels

The owner-supplied FOPNet (17 pages), Yang et al. (19 pages) and PHAGE v2 (14 pages) PDFs were extracted and read across their complete page ranges, including appendices/references. FOPNet's image-based extraction example on PDF page 15, the Yang prompts on PDF pages 16–17 and PHAGE's input/IN/OUT table on page 14 were visually inspected. FOPNet's metric definition is explicit in section 5/PDF page 11. Text extraction interleaves some two-column lines; figures were not converted into unverified numerical data. No PDF/source text is added to public research artifacts.

All three SHA -256 values match the preserved [paper move manifest](../../audits/ptp-dapfam-dual-track-handoff-20261110/paper-move-manifest.json). That prior worker's move is historical; this session did not move the PDFs again. Exact identities/hashes/page ranges are in this package's [source review manifest](../../audits/ptp-three-study-planning-20261110/source-review.json).

The [supplied advisory note](../PTP_SACR_VS_GRAPH_CONTRIBUTION_ASSESSMENT_20261110_EN.md) was reviewed as **advice/proposal**, not an experiment. Its numerical design ratings are subjective, and its hypothetical extraction hours are arithmetic. Its prior development-only SACR option is superseded by the owner's DAPFAM B0/SACR/S/G direction. Preserve the original note; do not rewrite it as an adopted protocol.

Other sources below were checked at primary metadata/abstract/selected-method level or inherited with explicit limits from the [SACR prior-art audit](../SACR_PRIOR_ART_COMPARISON_20261110_EN.md). This is a targeted review of supplied and directly adjacent work, not a systematic search. Public web checks were made on 10 November 2026; no new corpus, weights or executable was acquired.

## 2. FOPNet: closest structured-content/retrieval precedent

**Identity:** Nan Wang, Ziyi Wan, Hongyu Zhao, Chang Wang and Yake Wang. *FOPNet: A comprehensive functional semantic knowledge graph for deep technical analysis in patents*. World Patent Information 84 (2026), 102427. Journal article, accepted 6 January/online 17 January 2026. [DOI](https://doi.org/10.1016/j.wpi.2026.102427). Local supplied file: `literature-review/pdfs/1-s2.0-S0172219026000025-main.pdf`, SHA -256`ecfb0fda04dcd0a27aa4e0104f66d066b5d941a7c23e4121acf32fefce73a312`.

**Method, source statement:** sections 3–5 combine Function–Object–Property ontology, UIE/ERNIE span extraction, relation classifiers, WordNet synonym/hyponym extension, knowledge completion using KGE and association mining, then staged candidate recall, RankNet, embeddings/FAISS and optional GPT -4o reranking/explanations. Corpus-side structure and functional patent retrieval are therefore established prior work. This is substantially closer than generic GraphRAG citations.

**Evaluation, source statement:** section 3.2/PDF page 4 describes 500 annotated claim sentences and 8,000 labeled patent pairs, including examiner/PTAB/infringement-derived examples. Section 5 describes retrieving a paired target from a large corpus through multiple stages. KGE link-prediction metrics in Table 4 are a different task from patent retrieval in Table 6/Figures 9–10.

**Critical metric correction:** section 5/PDF page 11 defines **Hit@100 as average target rank within the final top 100, lower is better**. It is not conventional fraction-of-queries hit@100. The handling of unretrieved targets is not sufficiently established for direct comparison here. Do not convert Table 6 values to our hit/recall or reproduce the abstract's percentages as DAPFAM gains.

**Source-specific unresolved issues:** the text refers to “ten million” and 15.7M corpus records; pages 4/11 call the 8,000 pairs held out, while page 12 also describes RankNet training on 8,000 pairs. The abstract's final average rank differs from section 5.2/Figure 10's final value. GPT -2 is motivated as the chosen efficient relation model, while Table 3 and discussion favor BERT/SciBERT. These inconsistencies require supplementary/code clarification before numerical replication; they do not erase the paper's demonstrated conceptual overlap. The data statement on page 15 says on request, and code is described prospectively. Public downloadable data/code availability was **not established** by this audit.

**Implication (our inference):** ST1 must compare S/G over identical extracted information and terminal scoring to determine whether traversal itself adds value. A broad FOP/ontology/knowledge-completion claim is unavailable. We may offer a more controlled native-family recovery experiment, but novelty remains provisional. No FOPNet implementation or benchmark result was reproduced.

## 3. Yang et al.: closest patent LLM path/pruning precedent

**Identity:** Peiyi Yang, Xuewei Wu and Peihan Wen. *Patent technology knowledge recommendation by integrating large language models and knowledge graphs*. Engineering Applications of Artificial Intelligence 169 (2026), 114176. Journal article, accepted 9 February/online 11 February 2026. [DOI](https://doi.org/10.1016/j.engappai.2026.114176). Local file: `1-s2.0-S0952197626004574-main.pdf`, SHA -256`2542cd7e1cad78de5aa3a6dfd9cf4df9a4627a95c13407f8648fc341c361f4be`.

**Method, source statement:** section 3.1 constructs a fine-grained ontology for requirements/purpose, principle, physical structure, activities and benefits, then uses a two-stage LLM YAML extraction -> Cypher construction. Section 3.2 combines patent-adapted ERNIE semantic representations, RGCN structure and ComplEx decoding. Section 3.3 explicitly generates ontology-guided meta-paths, decomposes them into hop-wise queries, and uses LLM relevance/type-continuity pruning. The LangGraph workflow includes intent, query, reasoning, pruning and generator roles. The appendices provide the extraction and graph-construction prompt forms.

**Evaluation, source statement:** section 4 uses 784 Chinese CPU-cooler patents (456 inventions/328 utility models),9,800 entities and 14,743 cleaned triples. KGE is assessed through held-out triple prediction. Recommendation uses 30 R&D-log questions, three domain personnel's preference judgments, plus BLEU/ROUGE/embedding similarity to expert reference answers. Ablations remove ERNIE, meta-paths or KG. These are **not native open-corpus DAPFAM OUT family-recovery results**.

**Uncertainty:** the small single-domain recommendation study, preference rubric and generation-overlap metrics do not establish exhaustive retrieval, transferable engineering correctness or cost-accounted acquisition superiority. Detailed source-span preservation and S/G matched-content discovery controls are not established by the inspected protocol; do not infer they are absent from all associated code. Table 12/13 differ on some removed-KG/RAG values, so do not copy a universal gain percentage without clarification. Data is on request (page 17); a public reproducible package was not verified.

**Implication (our inference):** ST3 cannot claim novelty for LLM graph-path generation, patent ontology or pruning. It needs the fixed G/simple heuristic/non-graph LLM planning controls, actual bounded decision costs and honest stopping/failure evidence. ST1's fixed traversal can be an affordable comparator, but being fixed alone is not algorithmic novelty.

## 4. PHAGE: graph-informed DAPFAM representation precedent

**Identity:** Yongmin Yoo, Qiongkai Xu, Zhangkai Wu and Longbing Cao. *Heterogeneous Dependency Graph-Guided Attention for Patent Representation Learning*. [arXiv:2605.10073v2](https://arxiv.org/abs/2605.10073v2),27 May 2026; **preprint**. Local supplied file: `2605.10073v2.pdf`, SHA -256`6834eefd7ab425d4ea6c6f07f9f4993ed869aabc47d975d9fda9d857dff81bfa`. No peer-review acceptance was verified for this work.

**Method, source statement:** sections 3–4 construct typed **within-patent claim** dependency graphs from explicit claim references, term flows and functional couplings. They inject connectivity masks/relation-aware biases into encoder attention and train with document/claim contrastive objectives. The supplied v2 describes a frozen BERT-for-Patents backbone with 124 additional scalar parameters and graph-free evaluation. It is an encoder intervention, not runtime navigation between corpus relation instances.

**Evaluation, source statement:** classification, clustering and DAPFAM retrieval; Table 2 reports 0.498 NDCG@100 averaged across six input configurations. AppendixJ/Table 13 separates TA/TAC/FullText and native IN/OUT. For TA->TAC it reports overall NDCG 0.494, R@100 0.343 and OUT NDCG 0.061. These values are **paper-reported v2**, not our reproduction and not directly comparable to the project's historical strict-OUT R@200. The paper's graph baselines use embedding-similarity graphs, a different topology from the proposed technical-relation graph.

**Important version gap:** the [primary record](https://arxiv.org/abs/2605.10073v3) identifies v3 dated 31 August 2026. Its abstract says graph-specific attention components are removed at inference, whereas v2's discussion describes retained learned biases. v3 full methods/code were NOT_REVIEWED here. Do not present v2's training/inference account as the verified current implementation or decide comparator reproducibility from it. No weights/code execution or claimed score replication occurred.

**Implication (our inference):** “first graph method on DAPFAM” is false positioning. A possible distinction is runtime **cross-record acquisition under identical extracted-content controls**. Before a direct numerical comparison, obtain executable permitted weights/code and match exact fields, encoder/pooling, preprocessing, corpus, metrics and eligible populations. A copied average over six configurations cannot serve as our primary baseline.

## 5. Comparison matrix

| Work | What is structured? | When graph/LLM affects retrieval | Evaluation signal | Main collision / remaining distinction |
|---|---|---|---|---|
| FOPNet | Functional patent triples, ontology and expansions | Corpus processing + staged retrieval/reranking | Pair retrieval/average rank; KGE separately | Functional structured retrieval established; topology versus same-content attribution still our proposed question |
| Yang et al. | Invention-process ontology and patent KG | LLM paths/pruning + graph inference + generation | Triple prediction,30-question expert/reference-answer study | Agent path/pruning already present; our proposed contribution is controlled family acquisition/cost |
| PHAGE v2 | Claim dependency graph within each patent | Encoder training; graph-free evaluation claimed | DAPFAM NDCG, classification/clustering | Graph-informed DAPFAM established; no equivalence to runtime corpus traversal |
| SACR proposal | Query source-linked relation/condition profile | Query views + full-index acquisition + local selector | No new actual retrieval result yet | Needs generic/source-anchor controls; exact spans alone are insufficient |
| ST1 S/G proposal | Shared corpus records/aliases/local relation text | S direct search versus fixed cross-record expansion | Native known-family recovery, failures/cost | Designed mechanism contrast; implementation/benefit NOT_RUN |
| ST3 proposal | Same frozen graph and evidence | Fixed/heuristic versus bounded LLM action/stop control | New authorized independent comparison required | Control value beyond extra planning must be demonstrated |

## 6. Additional adjacent primary work

| Source / status checked | Inspected depth and supported point | Consequence / gap |
|---|---|---|
| [Query2doc, EMNLP2023](https://aclanthology.org/2023.emnlp-main.585/) | Primary record/abstract; generated pseudo-documents expand queries | Generic expansion must be a credible control; patent gains not established by general IR results |
| [HyDE, ACL2023](https://aclanthology.org/2023.acl-long.99/) | Primary record/abstract; hypothetical-document dense retrieval without labels | Generative query-document matching is prior art; no local reproduction |
| [MemGraph, SIGIR2025 conference entry](https://sigir2025.dei.unipd.it/detailed-program/paper?paper=3c7781a36bcd6cf08c11a970fbe0e2a6), [author preprint](https://arxiv.org/abs/2504.14845) | Peer-reviewed conference record and primary abstract; LLM parametric-memory entity/ontology graph for PatentMatch | Patent matching is a different task from full-corpus family acquisition; no universal graph novelty |
| [DbAKG, AI EDAM2025](https://doi.org/10.1017/S0890060425100103) | Publisher abstract/selected text, not a new full-PDF audit | Functional structured analogy retrieval already exists; detailed controlled-comparison gap remains to inspect |
| [HippoRAG2, ICML2025](https://proceedings.mlr.press/v267/gutierrez25a.html) | Peer-reviewed proceedings abstract; passage integration, PageRank and online LLM in memory retrieval | Graph propagation/online reasoning prior art; QA effects do not transfer to patents automatically |
| [PatenTEB, arXiv2510.22264](https://arxiv.org/abs/2510.22264) | Primary preprint record/abstract; multi-task patent encoders and DAPFAM result | Strong model/provenance comparator; training exposure and exact rights need separate audit |
| [PaECTER primary record](https://arxiv.org/abs/2402.19411), [PLOS ONE DOI](https://doi.org/10.1371/journal.pone.0358188) | Primary record now lists journal publication 2026 and citation-informed training | Do not retain a blanket “preprint only” status; closed candidate ranking differs from our open corpus |
| [ColBERT](https://doi.org/10.1145/3397271.3401075) | Existing SACR audit inspected primary method/equation | Late interaction/aggregation established; SACR uses components/passages, not trained token-level ColBERT |
| [QUEST](https://aclanthology.org/2023.acl-long.784/) | Existing audit: primary abstract only | Conjunction/exclusion and evidence attribution established; complete patent relevance is not provided |

Functional-vector analogy, function-based retrieval and SMFM full-method access remain gaps recorded in the SACR audit. Its Murphy PDF read timed out; Liu function-retrieval/SMFM were publisher previews with access 403. Do not promote those inherited partial reads into a completed full-text review. Later add-on source lists in proposals are leads, not verified claims. No comprehensive temporal-patent literature review or independent scholarly novelty review has been completed.

## 7. What would change the plan

1. A closer paper already performing identical S/G controlled DAPFAM acquisition would narrow the contribution further; inspect it before “first controlled comparison” wording.
2. Runnable permitted PHAGE or functional-retrieval code with compatible inputs could justify a concrete comparator and panel/resource revision.
3. Failure to obtain source-fidelity or affordable corpus extraction would favor a narrower SACR/structured-information question, with the owner's explicit scope decision.
4. A distinct temporal hypothesis plus dated artifacts could support ST2; modern-model and reconstructed-query exposure would still limit foresight claims.
5. No independent evaluation route or no incremental adaptive value would keep ST3 inside an ablation rather than a third paper.

All three studies remain proposed. Passing engineering tests, literature overlap analysis and attractive paths are not research outcomes.
