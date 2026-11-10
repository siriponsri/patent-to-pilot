# HT-ST2: optional retrospective temporal transfer to MTM

Updated: 10 November 2026. Status: CONDITIONAL_DETAILED_PLAN / NOT_FROZEN / NEW_METHOD_RESULTS_NOT_RUN.

[Master](../../../../MASTER-PLAN.md) · [Index](../../../../INDEX-PLAN.md) · [Literature](RELATED-WORK-AUDIT.md)

## 1. Decision before treating this as a second paper

Working title: **Publication-Constrained Retrospective Transfer of Cross-Domain Patent Retrieval to MedTech.**

Start only after HT-ST1 has a fixed reusable method and a recorded transfer decision. If this work merely runs that method on another dataset, include it as ST1 external validation. A separate article needs a distinct temporal-transfer question, adequate source/version analysis, new authorized evaluation evidence and substantive findings beyond the same ranking comparison. The owner prefers a method contribution, so do not substitute a long audit for an untested transfer method.

Proposed RQ1: How does a method fixed on DAPFAM transfer to MedTech problem briefs under a declared publication-visibility rule?

Proposed RQ2: How do representative-member selection, query reconstruction and temporal metadata affect measured known-link recovery?

Proposed RQ3: Does query-side SACR provide a useful quality-cost trade-off at MTM scale, without corpus-wide graph extraction? Graph transfer is optional and must justify its incremental resources independently.

H1: frozen SACR improves historical P/main/X hit@20 over the pinned dense baseline, with a proposed practical margin of 0.01 absolute, to be reviewed before freeze. H2: the transfer effect is sensitive to temporal information choices. H2 is an empirical hypothesis, not an assumption that the existing benchmark is invalid. Any tuning on MTM changes the claim to adapted transfer and needs a separate budget/validation route.

## 2. Existing evidence and what it does not establish

The [frozen benchmark rules](../MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md), especially amendments 13–14, and [methods log](../MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md) preserve the historical design. Recorded inputs:899,838 corpus families; 1,985 dev queries; 1,955 protected queries. Those are receipt-derived counts, not new row inspection.

| Existing item | Recorded outcome | Use here |
|---|---|---|
| P/main/X dense | hit@20/100/200 0.180/0.313/0.388, historical dev | Baseline reference after safe-input parity |
| V4 neutral Qwen rerank of X top 30 + dense, lambda 0.5 | OOF hit@20 delta +0.017 [0.010,0.025]; only historically eligible dev challenger | Strong reranking comparator; cannot discover outside top 30 |
| Phase 1 V1–V3 | Defective query-instruction prefix in lexical/reranker inputs | INVALID_RUN; never evidence of method inferiority |
| Corrected phase 1b | Main hybrid null; BM25/CE weaker; title hybrid gain secondary | Retain negative/mixed results and selection history |
| V5/V6, PRF3a | Null/negative on primary cell | Do not repackage as positive evidence |
| Citation-reuse 3b | Reach 30.3% below 48.8% gate; 3c not built; 87.1% cited families outside corpus | Negative feasibility for that citation operator, not for technical-relation G |
| Current R1 | Boundary/eligibility/parity tooling exists; MTM vector hashes checked historically | Safe actual-data staging/parity gates remain open |
| SACR | Failed synthetic generation smokes; actual MTM retrieval NOT_RUN | No transfer result yet |

Protected baseline ranking filenames were historically recorded without scoring; this session did not inspect them. Historical prefreeze permission for label-free generation does not authorize current test scoring. The parent service's goal state does not create or revoke experimental permission.

## 3. Claim wording for “Back to the Future”

Use **retrospective retrieval with publication-constrained corpus access**. Avoid “we rediscovered the invention before it existed,” “uncontaminated historical foresight” or “all model knowledge is pre-cutoff.” Modern pretrained encoders/LLMs may have seen later patents or evaluations, even without explicit citation edges.

The input P is generated today from a later patent's title/abstract. Its problem framing may reveal post-invention concepts, requirements or solution clues. It is not evidence that a person at T(q) had that exact brief. Gold examiner citations occur later and may be used only by the evaluator as retrospective outcome labels.

The contribution can survive as a carefully delimited information-access and transfer study. Stronger historical claims require dated contemporaneous query sources and independently constrained models; neither exists as established evidence here. Title-only T is a useful sensitivity input, not proof of a pre-invention query. A is an explicitly solution-rich leakage reference, not a fair primary problem brief.

## 4. Temporal availability ledger

Before a new experiment, freeze the following ledger for each allowed artifact. Unknown availability is unresolved and excluded under a conservative declared rule; it is not silently assigned the family's earliest priority date.

| Artifact | Availability test / provenance | Failure mode to disclose |
|---|---|---|
| Document text | Exact indexed publication/member, field version, publication date<=T(q), hash/locator | Early family priority does not make a later grant/continuation's text available |
| Family mapping/members | Sourced mapping and version; distinguish retrospective canonical evaluation IDs from features visible at T | Later family member can leak new terminology/content |
| Query P/T/A | Original later source and exact generation prompt/model/date | Modern reconstruction may contain solution knowledge |
| Corpus passages/vectors | Text and preprocessing identity; visibility filter follows the indexed text member | Reusing vectors does not repair future text |
| Graph nodes/records | Supporting text publication and extractor/version | A node derived from later text is future information even if its family is older |
| Edges | Earliest source publication/assertion date for explicit relation; provenance for inference | Later citations or linking evidence cannot be backdated to older endpoints |
| Aliases/normalization | Dated external vocabulary/source or explicitly modern sensitivity condition | Later names, assignees or technical synonyms may reveal future knowledge |
| IPC/CPC fields | Snapshot/assignment date if used as historical information | Retrospective reclassification can change the X mask |
| Corpus statistics | Fit IDF, normalization/priors, cluster centroids and any learned scorer on the declared available corpus | Future documents change scores even when not returned |
| Models | Exact release/training statements, known patent/citation exposure and unknowns | A modern pretrained model cannot be certified pre-T from a document filter |
| Labels | Later examiner source used solely for evaluation; never runtime queries/features/edges | qrels-derived connectivity is evaluator leakage |

Existing implementation uses `visible_from` of the selected representative publication; this is conservative because an earlier public member may exist but is not indexed. Amendment 13 fixed a priority-date-only visibility defect before historical scoring. Re-selecting the earliest public member changes text/index/universe and requires a **new prospective version**, not a silent repair of frozen results. Do not automatically repeat the deferred 250–365 GiB text scan.

## 5. Design variants and controls

Primary transfer panel proposal, <=4 final systems: pinned dense X; frozen SACR; historical V4 reranker; one predeclared generic/source-anchor alternative selected on dev. Preserve U versus X/M as historical lane diagnostics. If Graph is affordable and scientifically essential, replace an arm through an explicit final-panel decision; do not add a fifth arm or require graph transfer for the SACR study.

Distinguish two independent axes:

1. **Method transfer:** keep source fields, query P and eligibility fixed across methods. Run frozen DAPFAM parameters without MTM outcome-driven tuning. If retuned, label it adapted and use disjoint tuning/validation groups.
2. **Temporal sensitivity:** compare the exact historical representative-visible setting with only those newly specified variants that are lawful, available and affordable. A modern/unfiltered reference is an explicit diagnostic and never the primary historical claim. Changing aliases/statistics is a separate factor rather than being bundled into a new model.

No requirement to build every temporal variant. A minimal solo study can audit fixed representative visibility, report uncertain model/query exposure and perform a small preregistered sensitivity supported by existing permitted artifacts. If those add no distinct scientific answer, integrate MTM into ST1 validation and stop the separate-paper branch.

## 6. Integrity, eligibility and evaluation

Close A01 role/label separation, A03 exact runtime-mask gold eligibility and A14 corpus/vector identity before new comparisons. The runtime receives only projected allowlisted corpus/query records; the dev evaluator receives only dev labels. Source IDs, construction roles and gold are not interchangeable. An agent suppressing output while parsing mixed labels does not satisfy separation.

Pin the historical predicate: publication-visible member at T(q), own family exclusion and the declared no-shared-CPC cross-field X rule. Report no-date, late-publication, own-family, CPC-overlap and missing-corpus categories, including intersections. Do not silently drop hard queries or modify gold to improve the method. If a new temporal protocol changes eligibility, freeze a crosswalk from the original population to the new qualified population, report attrition and both well-defined denominators. Historical results stay attached to their original denominator.

Primary endpoint proposal remains P/main/X hit@20 for historical comparability. Report known-family recall@20/100/200 and hit@100/200, MRR@100, failures, rescue outside the baseline pool and cost. Do not compare an R@200 value with FOPNet's average-rank “Hit@100.” Native DAPFAM and MTM X have different candidate rules and cannot be pooled into one score.

Use paired uncertainty grouped by shared target/family and document query-date strata. Development choice/OOF grouping must respect overlap; historical query-level OOF estimates remain historical and do not become independent confirmatory tests. Fix primary contrasts/multiplicity and practical margins before the single protected run. Report model/query contamination as a limitation even if the corpus version ledger passes.

## 7. Sequential packages, resources and acceptance

| Package | Deliverable | Acceptance / stopping condition |
|---|---|---|
| HT-ST2-W0 | Separate-paper versus ST1-validation decision | Distinct temporal hypothesis and evidence route; otherwise merge and stop this branch |
| HT-ST2-W1 | Safe curator inputs, temporal ledger and baseline parity | Exact allowed-input identities; no protected parsing; preserve failed attempt |
| HT-ST2-W2 | Frozen method transfer declaration and resource forecast | No corpus-side rebuild by default; compare same P text, source window and universe |
| HT-ST2-W3 | One bounded authorized dev transfer + affordable temporal diagnostic | All attempts/costs/failures; no repeated prompt/model search |
| HT-ST2-W4 | Freeze, owner approval and protected evaluation | <=4 methods and untouched authorized evaluation route; historical exposure disclosed |
| HT-ST2-W5 | Transfer/temporal findings with reproducibility package | Publish only allowed source IDs/hashes/code/aggregates; retain all failure evidence |

The old 72 h continuation allocation is cumulative and must not be reset. The previous smoke is consumed; remaining compute and human-card reservations must be read from the existing journals by the authorized runner. MTM has about 19.85 times as many families as DAPFAM; document lengths prevent treating that ratio as measured runtime. At assumed 10s/corpus-family extraction it projects 2,500 h, so corpus-wide LLM Graph MTM is **not currently a viable approved plan**. No new BigQuery, training, re-encode or paid service is authorized by this document.

Stop or narrow this branch on unresolved text dates, unacceptable query reconstruction leakage, insufficient scoped evaluation independence, resource overrun, unavailable rights or no distinct contribution. A local blocker does not stop ST1 reporting or Scout maintenance.

## 8. Literature, limitations and next action

Use functional-retrieval/KG prior art from [the literature audit](RELATED-WORK-AUDIT.md), the existing MTM phase 3 audit and citation-reuse negative result. Temporal filtering itself is standard experimental hygiene, not automatically an algorithmic novelty. General IR/graph/LLM gains do not establish historical MedTech discovery. There are no new user participants or clinical outcomes.

**Next action after ST1:** select the frozen transfer candidate and write a one-page decision stating whether the available temporal ledger and sensitivity evidence warrant an independent ST2. Until then retain the historical MTM workflow and results; do not rebuild its corpus or run Graph for completeness.
