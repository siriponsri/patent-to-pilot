# DAPFAM first: SACR and technical-relation graph retrieval
## A bounded research direction and continuation contract

**Date:** 10 November 2026  
**Status:** OWNER_DIRECTION_CAPTURED / PROTOCOL_PROPOSAL / NO_NEW_EXPERIMENT  
**Inspected checkout:** main at 287fabae65291d8f805b4bf48380ffb922552df0.  
**Purpose:** Give the existing long-run session one coherent research question, explicit comparison arms, honest stopping rules, and a separate MTM transfer path.

## 1. Decision

Run SACR and fixed graph retrieval as competing approaches inside **one DAPFAM study**, not as two independent full research programmes. Use shared input/evaluation infrastructure, retain a same-content non-traversing control, and measure offline construction as well as online retrieval costs.

The owner's latest direction is:
1. Develop and compare SACR and Graph on DAPFAM.
2. Make DAPFAM the primary research scope.
3. Later transfer SACR to MTM.
4. Consider Graph on MTM only if measured time, fidelity and resource requirements fit.
5. Clarify whether the older MTM “back to future” contribution survives.

This supersedes the assessment's earlier binary choice between closing SACR first and pivoting fully to graphs, and its earlier suggestion that SACR might be development-only. It does not rewrite historical protocols or authorize unlimited computation.

There can be **three sequential candidate studies plus one product track**, but only Study A is the active paper-sized scope. Three papers are a possibility, not a commitment:
- **Study A, primary now:** Which representation/search intervention earns its cost on native DAPFAM: query-side selective abstraction or corpus-side relation retrieval? Does traversal add value beyond the same extracted information?
- **Study B, conditional later:** Does a frozen method transfer to the temporally constrained MTM setting under a defensible information cutoff? This is a separate question only if it has distinct hypotheses and sufficient evidence. Otherwise it is an extension/appendix or product validation, not another paper by default.
- **Study C, conditional last:** Does adaptive LLM navigation improve quality or stopping/cost decisions over the frozen fixed graph? Proceed only after Study A establishes a reliable, affordable graph and Study B is completed, deferred or explicitly separated. Include a non-graph LLM-planning control and matched available information/search budgets. If the incremental evidence is only a small navigation ablation, keep it within Study A instead of manufacturing a third paper.
- **Product track:** Solution Scout workflow, source inspection, latency, maintenance and user usefulness. Engineering and commercial claims need their own evidence.

The sequence is Study A first, a decision on Study B second, and a decision on Study C last. Do not run three full studies at once or reserve three publication claims in advance.

Do not split SACR and Graph into nearly identical papers sharing the same question, split and results. Do not attach unrelated product features simply to enlarge a research manuscript.

## 2. What is actually ready

The live checkout agrees with local origin/main at the inspected commit. The existing “Pepo: Patent to pilot” desktop session was idle with its last turn completed when inspected. This preparation session is the sole temporary documentation writer; it does not start the long run. Recheck ownership and jobs before resuming.

| Component | Evidence inspected | Consequence |
|---|---|---|
| SACR infrastructure | research/sacr_* modules exist for profiles, views, full-index acquisition, selection, source bindings and durable outcomes | Reuse these components; existence and fixture counts are not real retrieval gains. |
| Native DAPFAM evaluator | evaluation/dapfam_native.py and dapfam_acquisition.py exist; earlier native synthetic differential checks recorded | Actual staged-input baseline parity remains a gate. |
| CPU-ESCAPE-004 | Historical receipt: 14/14 cases passed | Grammar/CPU evidence only. |
| SYN-SACR-003 | Historical result: normal exit and valid JSON, 18 exact quotes, but blocks were not in source order | Remains FAILED. One approved generation smoke consumed; no automatic retry, output sorting or relabelling. |
| Curator staging | Owner-curator code deployed; owner execution and real dev staging pending at latest checkpoint | Agent must not read mixed source/test to perform owner-only staging. |
| Solo fidelity | Adopted prospective policy, sampling/review implementation incomplete | Keep the existing cumulative human cap and the exact narrower gate label. |
| Graph retrieval | Proposal and attached prior art, not an implemented validated pipeline established here | Specify the retrieval operator and feasibility gate before corpus-scale extraction. |
| Protected evaluation | R5/test remains unauthorized and closed | No test read, scoring, exploratory diagnostics or repeated selection. |

Remote GPU/process state was **not re-verified in this document-only session**. The older checkpoint reports no running new GPU job after SYN003. That is a historical observation, not a live launch clearance.

The pre-existing untracked November 9 research/Claude handoff is preserved. No source code, historical result, original failure receipt, protected split or baseline ranking was changed by this package.

## 3. What the four supplied files change

The exact supplied SACR-versus-Graph note is retained beside this document:
[Original advisory assessment](PTP_SACR_VS_GRAPH_CONTRIBUTION_ASSESSMENT_20261110_EN.md).

### 3.1 FOPNet

Wang et al., *FOPNet: A comprehensive functional semantic knowledge graph for deep technical analysis in patents*, World Patent Information 84 (2026), 102427.  
DOI: https://doi.org/10.1016/j.wpi.2026.102427

FOP extraction, normalization, ontology/knowledge graph construction, evidence-oriented representations and ranking are established precedents. “Function/object/property graph for patents” cannot be the novelty claim.

Its datasets and evaluation are not native DAPFAM. The paper's quantity named Hit@100 is described as mean target rank, with lower better, rather than the conventional hit rate. Do not compare that value directly with project hit@k or Recall@k. The paper's data-availability statement is on-request; abstract language about open benchmarks is not proof that a downloadable reproducible package is available.

### 3.2 Yang et al.

Yang, Wu and Wen, *Patent technology knowledge recommendation by integrating large language models and knowledge graphs*, Engineering Applications of Artificial Intelligence 169 (2026), 114176.  
DOI: https://doi.org/10.1016/j.engappai.2026.114176

Sections 3.1–3.3 already combine ontology, two-stage extraction including YAML-to-Cypher conversion, graph representation, semantic entry, LLM-generated meta-paths, hop expansion and LLM pruning. This is a close methodological comparison, not a passing related-work mention.

Its case study uses 784 Chinese CPU-cooler patents and 30 R&D questions evaluated by three experts. Those outcomes are not native DAPFAM family Recall@200. A possible distinction for this project is the **controlled attribution and full-corpus known-link discovery experiment**, not the general combination of patent KG, LLM and paths.

### 3.3 PHAGE

Yoo et al., *Heterogeneous Dependency Graph-Guided Attention for Patent Representation Learning*, arXiv:2605.10073v2 (27 May 2026), preprint.  
Source: https://arxiv.org/abs/2605.10073v2

PHAGE injects typed within-patent claim-dependency structure into an encoder and evaluates on DAPFAM. It prevents a “first graph on DAPFAM” claim. It is distinct from online traversal between corpus relation instances. Appendix J's input-field configurations and IN/OUT metrics must be matched before any numerical comparison; a score copied from that paper is context, not an in-house reproduction.

### 3.4 Consequence

A defensible provisional contribution is:

> We compare query-side source-preserving abstraction with corpus-side technical-relation retrieval on native DAPFAM, and isolate whether fixed graph traversal improves known cross-domain family recovery beyond the same extracted content. We report fidelity failures, acquisition and selection effects, and offline/online costs rather than assuming graph superiority.

This is a bounded empirical question. Algorithmic novelty and absence of closer prior art remain unproved. The broader graph proposal in Downloads is useful background, but its earlier B0/S/G/A panel and native-OUT denominator claims are not silently adopted here.

## 4. One paper-sized system panel

Use at most four final systems, selected and frozen **before** protected evaluation:

| Arm | Definition | Question it answers |
|---|---|---|
| B0 | Frozen strong native-input dense baseline, with exact encoder/index/passage/family aggregation recorded | How much does any added machinery buy over the existing retriever? |
| SACR | One bounded frozen selective-abstraction configuration, retaining source-linked requirements and existing full-index acquisition/selection | Can query-side structure deliver useful recovery without corpus-wide extraction? |
| S | Source-grounded structured corpus records, searched without cross-record traversal | What does extracted/normalized content buy on its own? |
| G | The identical S records, aliases and query inputs, plus one deterministic bounded relation traversal operator | Does traversal contribute beyond the same information? |

**Do not add adaptive LLM controller A to the core.** It would add another question, model-call budget and final comparison. It can be a later development-only experiment after G is feasible and useful. A separate final agent claim requires a new prospective panel decision, not a fifth system slipped into the table.

SACR is a **system comparator**, not a magically information-matched ablation of G. Its query-side and corpus-side processing differ. Primary mechanism attribution comes from G versus S. Practical system choice comes from G versus SACR together with their measured quality-cost trade-off.

### Proposed inferential plan, not a test authorization

- Candidate primary endpoint: native OUT known-positive family Recall@200 over the actual eligible development/protected populations, using the pinned native evaluator.
- Prespecify G−S as the topology contrast and G−SACR as the practical system contrast. If both are confirmatory, control their multiplicity together, for example Holm over the two hypotheses; choose compatible interval reporting before test.
- Use B0 comparisons and IN/overall results as declared secondary results, not a replacement primary endpoint after seeing outcomes.
- Prespecify a practically meaningful margin, paired analysis, missing/failure treatment, multiplicity procedure and cost reporting before protected access.
- Report Recall@20/100/200, hit@k, ranking metrics and native results only where their definitions are exact. Hit@k is “at least one known positive”; recall is the fraction of known positives recovered.
- A positive point estimate, passing fixtures or a visually appealing path is insufficient for a confirmatory claim.

### Essential development controls

Keep this small and predeclared:
1. SACR generic versus preserving query views and mean versus bottleneck selection, using the same unions/profiles/passages where the mechanism comparison requires them.
2. Source-anchor/lexical coverage control already called for by the existing plan.
3. S versus G with identical extracted records, aliases, text coverage, model versions and terminal family scorer.
4. One graph perturbation that destroys the claimed cross-record relation while preserving declared nuisance structure. Record what the perturbation changes; do not interpret arbitrary corruption as a perfect causal control.
5. A deeper non-traversing search or serialized-record control if G otherwise receives more information/search opportunities. This is a development diagnostic, not automatically another final system.

Freeze these choices prospectively. Do not search combinations until one beats B0. Preserve negative results.

## 5. Fairness and native data contract

The reported DAPFAM resource has 1,247 query families and 45,336 corpus families; verify exact revision, IDs and bytes through the authorized staging route. Preserve the project's existing development/protected assignments and exposure history.

- Native queries use title plus abstract; corpus records use title, abstract and claims according to the pinned native adapter.
- Do not silently reuse a legacy TAC query cache for native TA evaluation.
- OUT is an evaluator partition, not a rule to delete same-field candidates from the universe.
- Do not assume that 349 development OUT queries or 556 protected OUT queries are native denominators. The advisory note identifies a filtered-setting conflict. Have the authorized curator/native evaluator reconcile the counts without exposing test material to runtime.
- Do not use citation labels, qrels, target IDs or protected outputs to create aliases, graph edges, entry points, prompts or retrieval control.
- Both SACR new views and graph entry must access the full eligible corpus, not merely rerank B0's top-200. Existing SACR design allows up to three views and a union up to 600 families before final depth 200; verify the actual adopted configuration rather than silently enlarging it.
- Match allowed source fields and **actually consumed coverage**. If graph extraction sees full claims while dense encoding truncates them, report the difference and include a coverage-matched diagnostic.
- Match final k, family identity and evaluation. Also report visited records, unique candidate families, passages, tokens, wall time, memory and model calls. Equal final k does not mean equal computation.
- Keep all query failures in the declared population. Missing outputs, rejected generated families, anchor fallback and infra failures must remain separately visible.
- Unlisted links are unjudged, not proven negatives. Known-link recovery is not exhaustive prior-art recall, engineering feasibility or legal validity.

The proposal reports a 374-query shared-target component in a 474-query development split. Verify this from permitted development metadata. If present, ordinary balanced four-fold component-disjoint CV is not possible. Do not split it for convenient folds. Choose a dependence-aware analysis, disclose effective information and sensitivity, and do not use independent-query bootstrap as if the dependency disappeared. Do not inspect test labels to redesign grouping.



## 6. Completion of the partial direction note (10 November 2026)

Sections 1-5 above are preserved from the prior preparation worker. This continuation completes the routing/contract; the canonical detailed programme is now [MASTER-PLAN](../../../MASTER-PLAN.md) and [INDEX-PLAN](../../../INDEX-PLAN.md), with [ST1](plans/PAPER-1-DAPFAM.md), [ST2](plans/PAPER-2-MTM.md), [ST3](plans/PAPER-3-ADAPTIVE.md) and [closest-work audit](plans/RELATED-WORK-AUDIT.md). No result or prior advisory assessment was overwritten.

## 7. Gates and temporal-transfer boundary

Real curated native TA baseline parity, SACR viability/fidelity and affordable S/G construction remain separate gates. SYN003 remains FAILED; its consumed smoke is not retried automatically. G must be compared with S over identical extracted records, aliases and terminal scoring, with deeper-search/work controls. Actual graph/SACR retrieval is NOT_RUN.

MTM is a conditional later transfer. Exact indexed publication versions, family members, graph nodes/edges, aliases and corpus statistics must obey the declared availability rule. Query briefs reconstructed from later patent text and modern pretrained models prevent a claim of uncontaminated historical foresight. If MTM merely validates a frozen method, include it in ST1 rather than manufacturing a second article.

## 8. Third-study and solo-resource decision

Adaptive navigation is conditional on reliable/affordable fixed G and a distinct independent evaluation route. A once-opened ST1 holdout is not a fresh untouched ST3 test. Include fixed G, a simple label-free heuristic and non-graph LLM planning under matched information/budgets. Do not add an agent to ST1's four-system final panel by implication.

No new graph compute allocation is inherited from the old 72-hour continuation. Reconcile remaining journals/card caps before any proposal. Initial graph extraction, alias validation, rebuild and online costs all count. Existing model/data/derived-artifact rights remain separate.

## 9. Memory, provenance and archive

Both agent instruction files and HANDOFF require maintaining INDEX-PLAN at substantive work/checkpoint events. [Shared project memory](../../../memory/research/patent-to-pilot/INDEX.md) is an explicit Markdown workflow, not shared private assistant memory or an installed service. [Archive review](../../../archives/INDEX.md) moved/deleted no existing files because relevant historical/uncertain work remains in place. The original advisory note, 9 Nov handoff and paper-move manifest remain unchanged.

## 10. Actual session outcome and continuation

This completion is documentation only: no jobs, experiments, protected reads, paid calls, installs, commit or push. Local HEAD/origin tracking was verified at 287fabae; live remote verification failed network connectivity, so synchronization is not asserted. The prior session's idle state was observed, not taken as future job-launch clearance. Exact checks, source hashes and the copy-ready long-run prompt are in the [documentation audit](../audits/ptp-three-study-planning-20261110/README.md). Next: recheck one-writer takeover, sanitized curator partial status, safe native baseline, then bounded SACR/S/G feasibility.
