# HT-ST3: conditional adaptive LLM graph navigation

Updated: 10 November 2026. Status: CONDITIONAL_DETAILED_PLAN / NO_CONTROLLER_RESULT / NOT_FROZEN / NOT_RUN.

[Master](../../../../MASTER-PLAN.md) · [Index](../../../../INDEX-PLAN.md) · [Literature](RELATED-WORK-AUDIT.md)

## 1. Entry decision and distinct contribution

Working title: **When Is LLM Control Worth Its Cost in Evidence-Linked Patent Graph Search?**

This is a later question about **search control**, not another claim that structured patent representations help. Begin only after ST1 establishes a reliable, affordable fixed S/G pipeline and a defensible reason to navigate it. ST2 must be completed, deferred or explicitly separated so one solo researcher is not running three programmes simultaneously.

If fixed G is unreliable, too expensive or offers no useful signal beyond S, defer this study. If the incremental result is only a small navigation ablation on ST1's already used test, keep it within ST1 as an exploratory extension. A separate manuscript requires distinct hypotheses, adequate fair controls and new authorized confirmatory evidence. Do not promise publication.

RQ1: Does an adaptive LLM choose more useful next actions than fixed traversal or a simple label-free heuristic under the same information and search budget?

RQ2: Does adaptive stopping reduce work at a prospectively acceptable quality loss?

RQ3: Is any gain caused by graph control rather than extra model reasoning, query expansion, richer observed text or a larger candidate budget?

Candidate H1: adaptive A improves native OUT Recall@200 over fixed G. Candidate H2: A is noninferior within proposed 0.01 absolute recall while reducing measured online GPU/CPU work by a proposed 20%. These margins are planning suggestions requiring review before freeze. Select **one primary effectiveness or efficiency claim** prospectively; do not choose whichever looks favorable afterward. Superiority and noninferiority need different inferential declarations.

## 2. Prior art and novelty boundary

Yang et al. already implement ontology-guided LLM meta-path generation and LLM-scored pruning for patent recommendation. MemGraph uses LLM entity/ontology memory traversal for PatentMatch. HippoRAG2 uses graph propagation and online LLM processing for memory retrieval. The full closest-work comparison and source limits are in [RELATED-WORK-AUDIT](RELATED-WORK-AUDIT.md).

Potential new evidence is a controlled, cost-accounted comparison of fixed and adaptive acquisition on a source-linked patent corpus, with failures and stopping behavior. “LLM agent+KG+patent” and generic path planning are not novel claims. These sources use different tasks/metrics; their numbers are not baselines reproduced in this repository.

## 3. Evaluation independence is a prerequisite

Do not treat ST1's once-opened DAPFAM protected split as a fresh untouched test for a new controller. Its outcomes can inform exploratory follow-up only. Before development specify one of:

1. A controller and final comparisons prospectively frozen before any applicable protected results are seen, with owner-approved panel/multiplicity changes; this may be part of ST1 rather than a separate article.
2. A genuinely new authorized evaluation cohort or benchmark with family/exposure separation and available rights, obtained without a score-driven sample. No such new holdout is established here.
3. A clearly labelled development-only exploratory study, with no new confirmatory generalization claim.

Existing data does not become new evidence because the method receives a new name. If no feasible independent evaluation route exists, do not spend a large controller budget to manufacture a third paper. Preserve original split assignments and existing test restrictions.

## 4. Common information and state contract

Use the fixed ST1 graph/index, extracted records, alias registry and source/version hashes. No new extraction, corpus re-encode or model training is part of the primary contrast. Query input, entry seeds, allowable edge types, terminal family scorer, output depth and failure rules match fixed G.

Controller state contains only permitted query text, the current visited/available frontier records, their source-linked attributes, prior actions and measured remaining resources. It contains no qrels, target IDs, dev-evaluator summaries, target-derived statistics, future test outcomes or hidden relevance oracle. Do not insert reward feedback from gold during evaluation.

Actions use a finite typed menu: choose an existing frontier/edge type; expand within cap; request a structured-index search with allowed query fields; score already acquired families; or stop. Every action names existing IDs and bounds. The controller may not execute arbitrary shell, Cypher or network commands, invent graph nodes/edges or query external sources. Validate outputs mechanically before action; unresolved/invented actions are failures, not silently repaired instructions.

Keep concise source-linked action reasons and observable decisions, not claims of access to private model reasoning. Explanation plausibility is not evidence that an action caused improved retrieval.

## 5. Proposed bounded controller

This is a concrete draft for future review, not implemented or adopted behavior:

- One local model/configuration selected for demonstrated compatibility, with exact weights/tokenizer/prompt/decoder/runtime identities. No change of account/provider/model label to hide failed runs.
- Maximum 4 decision calls/query, each <=512 new tokens; total generated tokens<=2,048/query. Maximum 4 expansion/search actions, graph hops<=2 per path, <=512 visited relation records and <=600 acquired families; output 200 families. Match fixed G's total visit/candidate envelope, or reduce both prospectively.
- Candidate action list and observed source-text cap are deterministic and identical for comparable policies. No access to global graph text via an unmetered prompt. Charge query analysis, shared profile/extraction and every failed call.
- Greedy/no-retry initial policy. Stop on explicit STOP, exhausted resources, frontier exhaustion, deadline or invalid response. Predetermine whether a verified invalid controller decision falls back to the fixed continuation or terminates with available candidates; use that same rule for all queries. Unknown infrastructure outcomes require status checking, not replaying a call.
- One distinct engineering smoke on authored data only if newly authorized. It is not a retry allowance from SACR's consumed smoke. Then a small declared dev pilot; no automatic prompt/model search.

The proposed token/action values must be checked against measured hardware throughput. No service, API spend or GPU reservation is authorized by this plan.

## 6. Four primary control policies

| Policy | Shared resources | What it controls |
|---|---|---|
| HT-ST3-G | Frozen deterministic ST1 traversal | Fixed search baseline |
| HT-ST3-H | Simple label-free heuristic choosing frontier by frozen semantic score, novelty/diversity and remaining budget | Benefit of adaptation without an LLM |
| HT-ST3-L | Same LLM decision budget over S's structured search, with no cross-record traversal; same corpus records/aliases/query information | Extra reasoning/query planning without graph navigation |
| HT-ST3-A | LLM selects graph actions/stop over the same G | Proposed adaptive graph policy |

Static B0/SACR results may provide context but are not additional unregistered confirmatory arms. If fresh comparison is needed, revise the panel explicitly. A random valid-action policy is an optional dev diagnostic under matched action caps, not an unmetered fifth final system.

Maintain fixed generator/scorer and graph for all policies. If A sees longer source text than G/H/L, add matched-coverage diagnostics and limit the interpretation. If L lacks an information field that A sees, the contrast confounds information with graph topology. Identical final top 200 does not equal identical effort; report allowed and realized visited/scored records, calls, tokens, time and memory.

## 7. Outcomes, stopping and statistical analysis

Primary setting should be native DAPFAM OUT if an independent evaluation route exists; otherwise identify the new setting prospectively. Use the exact native evaluator semantics, full candidate corpus, failed-output denominators and unjudged treatment from ST1.

Effectiveness endpoints: query-macro known-family Recall@200; secondaries NDCG@100, hit@k, MRR@100 and rescue/loss versus G. Control diagnostics: chosen actions, valid-action fraction, early stops, repeated/cyclic visits, frontier exhaustion, candidate displacement, failure/fallback fraction and source-grounded path errors. None is a clinical/design-innovation outcome.

Efficiency endpoints: actual construction carried forward, per-query p50/p95 latency, CPU/GPU wall time, model load amortization, observed memory, calls/tokens, record/passage scoring and actual/unknown monetary billing. Record all failures/timeouts. Report quality-cost frontiers at predeclared action budgets using complete fixed populations; do not select the best budget on test.

For adaptive stopping, define success as a predeclared noninferiority quality criterion **and** a measured cost reduction with compatible uncertainty. Shortening latency by returning fewer candidates is not enough. Never stop based on whether a hidden target was found.

Use paired group/component analysis and report effective independent groups. Repeated stochastic seeds are sensitivity analyses nested within queries, not independent samples. If multiple confirmatory comparisons A−G/A−H/A−L are kept, define a primary hierarchy or multiplicity correction before access. Small or broad null intervals remain inconclusive. A versus G alone cannot prove the LLM or graph caused the gain.

## 8. Work packages and acceptance

| Package | Deliverable | Acceptance / stop |
|---|---|---|
| HT-ST3-W0 | Distinct-contribution and untouched-evaluation decision | If no credible new evidence route, defer/merge; no controller run |
| HT-ST3-W1 | Typed state/actions, replay log and hand-computable fixtures | Illegal IDs/oracles/arbitrary actions rejected; shared policy budgets verified |
| HT-ST3-W2 | Fixed G, heuristic H and non-graph L contracts | Same information/scoring; label-free actions; measured work accounting |
| HT-ST3-W3 | Newly authorized bounded A engineering smoke/pilot | One declared configuration, all failure artifacts; source/format/resource gates |
| HT-ST3-W4 | Limited dev comparison and stop/carry decision | A adds useful effectiveness or quality-preserving savings over relevant controls; no indefinite tuning |
| HT-ST3-W5 | Protocol freeze and independent protected evidence | Exact owner authority/panel/evaluation independence; no reuse of opened holdout as untouched |
| HT-ST3-W6 | Manuscript or honest ablation/negative report | Report extra cost, failure burden and controls that eliminate apparent benefit |

## 9. Solo feasibility, rights and limits

Agent control is a last increment on an already built graph. No new budget is inherited from prior papers. Read existing cost/attempt/reservation journals; count shared costs once at the declared accounting boundary and allocate them transparently. Do not reset the 60-card fidelity cap or use the same query with a new configuration as a free new card.

A pilot forecast must include every decision call and invalid/fallback case, not just successful query latency. If the local model is too slow/unreliable within the one-job V100 window, stop or use a simpler controller; a paid model replacement requires new exact authorization and the existing ledger/adapter. No installations/account configuration or concurrent jobs are implied.

Graph-derived artifacts retain data/model/source-license restrictions. Publish authored schemas/code, permitted aggregate decisions and hashes; do not publish source text, protected target relations or private model journals. No participants or external messaging are planned.

## 10. Result routing and next action

- A beats G but not H: evidence favors adaptive search, not an LLM-specific need.
- A beats G but not L: extra language-model planning may explain the gain; graph control remains unresolved.
- A improves recall but costs much more: report the quality-cost trade-off, not automatic superiority.
- A matches quality while meeting declared savings with valid uncertainty: bounded evidence for adaptive stopping.
- A is unreliable or gains vanish under fair controls: retain negative results; integrate a modest ablation into ST1 or defer the separate paper.

**Next action:** none until ST1's graph/fidelity/resource decision and an independent evaluation plan are recorded. Maintain this conditional plan and relevant component rows while completing ST1.
