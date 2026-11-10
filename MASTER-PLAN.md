# Patent-to-Pilot: master research plan

Updated: 10 November 2026 (Asia/Bangkok). Status: OWNER_DIRECTION_RECORDED / DOCUMENTATION_ONLY / NO_EXPERIMENT_AUTHORIZATION.

## 1. Decision and reading route

Develop **one primary DAPFAM study**, then decide whether MTM transfer and adaptive graph navigation merit independent studies. Three manuscripts are possible outcomes, not three promised journal publications. The owner wants a method contribution; a benchmark audit alone does not replace it. Negative or inconclusive findings must remain reportable.

Start with [actual component/result index](INDEX-PLAN.md), [current takeover](HANDOFF.md), [shared project memory](memory/research/patent-to-pilot/INDEX.md), and the selected detailed plan:

| Study | Question | Current priority | Detailed plan |
|---|---|---|---|
| HT-ST1 | What do query abstraction, structured content, and fixed cross-record traversal each buy on native DAPFAM? | Primary; specification and feasibility first | [Paper 1](docs/healthtech/research/plans/PAPER-1-DAPFAM.md) |
| HT-ST2 | Does a frozen method transfer to a publication-constrained retrospective MedTech setting, and how sensitive is that conclusion to temporal information choices? | Optional; decide external validation versus separate contribution | [Paper 2](docs/healthtech/research/plans/PAPER-2-MTM.md) |
| HT-ST3 | Does bounded adaptive LLM navigation improve quality or stopping/cost over fixed graph traversal and simpler controllers? | Conditional last; graph feasibility and distinct question required | [Paper 3](docs/healthtech/research/plans/PAPER-3-ADAPTIVE.md) |
| HT-PROD | Turn inspected patent candidates into a useful, inspectable Solution Scout workflow | Separate product track; maintain working baseline | [existing product specification](docs/healthtech/research/SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md) |

The selected legacy work-package equivalents are HT-W01/07/18 for this documentation package; future methods use HT-W06/08/09/10/11/14 as appropriate. These identifiers do not relabel historical B0–B4 or G01–G22 results. Root [GOAL](GOAL.md) and [PLAN](PLAN.md) retain product/engineering contracts and historical context; this owner-requested plan narrows the new research sequence. Historical frozen protocols remain immutable. A new prospective declaration is needed for changed experiments.

## 2. Authority and ownership

This session may inspect authorized sources and write/validate documentation in the existing `main` checkout. It may not start experiments, model calls, training, downloads of new corpora, paid APIs, protected evaluation, installations, deployment, commits or pushes. Earlier handoff publication language is superseded by this session's explicit no-push direction. Research plans are not run approvals.

One active writer controls the checkout. The previous long-run session was observed idle with its latest turn completed before this documentation takeover. Recheck current ownership and recorded job status before the next writer starts. Do not resume any consumed smoke or failed curator attempt automatically. Never reset ledgers, discard untracked work, or change access controls.

## 3. What the existing evidence supports

See [INDEX-PLAN](INDEX-PLAN.md) for artifact-level provenance and verification depth. None of these results was rerun for this plan.

- DAPFAM has a strong historical dense development baseline. The previous strict-OUT, claims-inclusive query setting gave R@200 0.1618; generic LLM actions and learned mixes did not improve the fixed-budget result. **That number is not the native TA-query baseline for HT-ST1.** A large shared-target development component also limits independent resampling/folding.
- A native TA-query/TAC-corpus dev evaluator and full-index SACR helpers exist. Their fixture/differential checks establish software behavior. Real curated-input baseline parity, actual SACR retrieval, fidelity observations and scientific comparisons remain NOT_RUN.
- SYN-SACR -001/002/003 are preserved failures. SYN003 produced valid JSON and exact quotations but failed source-order acceptance. CPU004's 14/14 result does not establish viable generation. The single approved new smoke was consumed; no automatic fourth call is authorized.
- No validated cross-record technical-relation retrieval graph was established by this audit. Historical dependency graphs and citation probes solve different tasks. S and G require new executable specifications, extraction-fidelity evidence and a full-corpus resource projection.
- MTM has 899,838 corpus families and recorded dev results. V4's top -30 reranking improves historical P/main/X hit@20 from 0.180 to 0.197, OOF delta +0.017 [0.010, 0.025]. It is neither SACR nor graph discovery evidence. Corrected hybrid/PRF/function-channel attempts were null/negative; the citation-reuse probe was NO_GO. Current R1 integrity gates still matter before a new method comparison.
- Earlier PAR4PC/PI4PC final results and Scout grounding/latency findings are real historical evidence for their own tasks. They do not validate open-corpus DAPFAM discovery, temporal foresight, semantic fidelity, customer benefit or an adaptive controller.

## 4. Contributions and nearest prior work

The provisional contribution is a controlled comparison of **query-side requirement preservation, corpus-side structured information, and traversal over that same information**, with full failure and cost accounting. Do not claim the first patent KG, functional patent search, LLM path generation, source-grounded representation, or graph method on DAPFAM.

[Full closest-work audit](docs/healthtech/research/plans/RELATED-WORK-AUDIT.md) covers the supplied FOPNet, Yang et al. and PHAGE v2 PDFs plus the advisory note. FOPNet already combines functional ontology/extraction and retrieval. Yang already has ontology, LLM-generated meta-paths, multi-hop expansion and pruning. PHAGE already evaluates a graph-informed encoder on DAPFAM; it is an intra-document training intervention, rather than cross-record runtime traversal. PHAGE v3 exists and changes the inference description; it was identified, not fully audited here. Published scores are context, not local reproductions.

## 5. Study gates and sequence

| Gate | Concrete deliverable | Acceptance / stop |
|---|---|---|
| HT-GATE0: evidence and scope | Component index, literature matrix, unchanged historical results, selected study | Owner direction captured; unknowns explicit; no new compute |
| HT-GATE1: safe native baseline | Curated dev-only input manifest, pinned release/evaluator, source/vector/query identities, exact ranking parity or explained declared new baseline | Stop dependent comparisons on missing/failed identity or leakage gates; do independent specifications |
| HT-GATE2: viable SACR | One fixed generation contract, accepted failure implementation, adopted fidelity procedure and measured resources | Failed smoke remains failed; no repair/refill or retries without fresh authority; if infeasible, revise panel explicitly before test |
| HT-GATE3: feasible S/G | One relation schema, aliases, fixed operator, source/fidelity sample, extraction/index projection and approved envelope | Do not launch corpus extraction if forecast exceeds remaining resources or semantic review is inadequate |
| HT-GATE4: bounded development | Prospective small pilot then allowed dev comparisons; identical S/G content, fixed budget controls, all attempts | No repeated search until significance; one predeclared revision at most as a planning ceiling, subject to actual run authority |
| HT-GATE5: final freeze | At most four systems, endpoints/margins, cohort, grouping, inference, resources and failure rules in dated reviewed commit | Requires explicit owner authorization and approved publication path; this session does not open test |
| HT-GATE6: ST1 report | All positive, negative, failed and inconclusive findings; reproducibility/rights review | Finish a scoped result before expanding questions |
| HT-GATE7: MTM decision | Distinct contribution and temporal/resource feasibility assessment | Frozen-method replication only -> external validation in ST1; substantial temporal question -> optional ST2 |
| HT-GATE8: agent decision | Reliable affordable graph, fixed-controller result, remaining dev data and budget, independent question | Small tuning ablation -> ST1 extension; no graph value or no fair controls -> defer ST3 |

These gates are dependency conditions, not a new service goal or a reset of R0–R6. Existing R1 repairs map mainly to GATE1, R2 to GATE2, R3/R4 to GATE4, R5 to GATE5 and R6 to reporting. GATE3 is additional graph work, not completed by existing SACR fixtures.

## 6. Common experimental contract

1. Preserve original dev/test assignments and exposure history. Native DAPFAM IN/OUT partitions qrels while keeping the full candidate corpus. Do not apply MTM's CPC-X mask or reuse strict-OUT denominators as native counts.
2. Runtime gets permitted query text, corpus data and label-free artifacts only. Gold-derived edges, aliases, queries, target-neighbor expansion and evaluator summaries must not guide retrieval. Inspect only aggregate authorized metadata here.
3. Pin source bytes, exact member IDs/kind codes, family mapping, dates, field coverage, preprocessing, token truncation, passage ownership/order, weights/tokenizer, prompts, decoder, extraction/index revisions and tie handling.
4. Missing eligible output scores zero under the declared evaluator; retain failure reasons and unavailable costs. Unlisted relations are unjudged. Known-link recall is neither exhaustive recall nor a certified lower bound on relevance recall.
5. Match content and available information for S/G; measure extra work separately. Same top-k alone is not fair computation. Separate acquisition-union rescue, displacement, final ranking and end-to-end quality.
6. Use paired family/shared-target component uncertainty. Report number and dominance of components. Seed repeats are not independent query populations; query-level CV is not a cure for a giant shared component.
7. Freeze effect margins and multiplicity before protected evaluation. A nonsignificant estimate does not prove equivalence. Do not relabel an exploratory result confirmatory.
8. Account for initial construction, maintenance/rebuild, online search, failed attempts, CPU/GPU wall time, memory/disk, tokens and actual/unknown billing. Zero paid calls does not mean zero compute cost.

## 7. Solo resources and feasibility

The historical 10 November bounded continuation permits one V100 job, CPU <=8 threads, RAM <=32 GiB, incremental disk <=40 GiB, cumulative GPU <=72 h, within the recorded window ending 31 December 2026 16:59 UTC. Baseline <=4 h/benchmark, fidelity generation <=8 h combined, 20-query pilots <=2 h combined and full dev <=48 h combined were recorded for the **older declared continuation**. Remaining consumption was not recalculated here. **These are not an allocation to new graph extraction or three studies.**

The adopted fidelity cap is 60 owner cards total across both benchmarks and all configurations, <=30/benchmark, category caps 20 escalations +10 sentinels per benchmark. It is not per configuration. No new allowance is created by separating papers. Graph extraction/aliases would require their own declared fidelity population and budget; do not silently consume or extend this cap.

Hypothetical one-call-per-family extraction at 10 s would take about 126 h for 45,336 DAPFAM families and 2,500 h for 899,838 MTM families, before validation or retries. This is arithmetic, **not measured throughput**, and already exceeds the old 72 h ceiling for DAPFAM. Therefore start with an authorized small engineering measurement and consider deterministic extraction or existing reusable representations; no corpus-scale LLM plan is accepted on family counts alone.

Use one study at a time. Proposed effort blocks, not delivery promises: baseline/integrity closure; SACR viability decision; S/G feasibility decision; bounded dev; freeze; one final report. Estimate hours from measured throughput before booking compute. Human card shortage stops that configuration, not the entire documentation/product track.

## 8. Paper boundaries and result-dependent routing

| Observed outcome | Appropriate claim / route |
|---|---|
| SACR improves B0 but not generic multi-query | System-level multi-query result; no special preservation claim |
| S improves B0; G does not clearly improve S | Structured information may suffice; report interval against practical margin; no topology superiority |
| G improves S under matched information/work controls | Evidence for the declared traversal operator in this setting |
| More positives enter the union but top -200 does not improve | Acquisition/selection mismatch; no fixed-depth gain |
| MTM only repeats frozen-method ordering | External validation subsection/appendix of ST1 |
| MTM exposes substantive cutoff/version sensitivity and transfer findings | Candidate independent temporal-transfer study with separate hypotheses |
| Agent's gain disappears against non-graph planning or matched heuristic | No agent-specific contribution; retain ablation/negative evidence |
| Null result with broad intervals or unreliable method | Inconclusive; no equivalence or automatic publishability claim |

An independent ST2/ST3 must identify its new estimand, newly authorized evaluation evidence, relationship to ST1, and reuse/citation of shared resources. Do not reuse a once-opened test set as a fresh untouched holdout for later method selection. Journal/venue choice follows the completed contribution and current author guidance; no acceptance/impact/fee promise is made.

## 9. Product, rights and release

Solution Scout may reuse reliable components after an engineering integration decision. Its existing two-lane retrieval, source viewer/export and grounding mechanism are separate from the three research questions. A graph picture is not evidence that graph traversal generated a result. Source matches do not establish engineering feasibility, clinical suitability, FTO or customer value.

Data/model/paper/code/derived-graph licenses are separate. Retain DAPFAM/PatEmbed non-commercial restrictions as recorded until exact current terms are reviewed. Do not stage supplied PDFs, raw corpora, generated source text, evaluator-only relations or private journals. The repository's own LICENSE does not license third-party inputs. Local reading rights do not imply redistribution rights.

## 10. Completion and continuation

This planning package is complete when all three detailed plans, component/result index, related-work audit, memory workflow and archive decision record have valid links and honest statuses, and AGENTS/CLAUDE/HANDOFF all require index updates. Scientific studies remain incomplete.

Maintain [INDEX-PLAN](INDEX-PLAN.md) at each substantive work event; maintain [shared decisions](memory/research/patent-to-pilot/DECISIONS.md) when directions change. Detailed evidence stays in immutable audit run folders. The [documentation audit](docs/healthtech/audits/ptp-three-study-planning-20261110/README.md) records actual checks and restrictions. [Archive review](archives/INDEX.md) preserves historical references without moving uncertain active evidence.
