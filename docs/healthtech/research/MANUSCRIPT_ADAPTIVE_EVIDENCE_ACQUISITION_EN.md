# Evaluating Adaptive Evidence Acquisition for Medical-Device Patent Screening under Incomplete Judgments

Status: `DRAFT_FOR_OWNER_REVIEW / SOLO_COMPUTATIONAL_STUDY / NOT_SUBMITTED`

Target venue: *World Patent Information* (official scope checked on 2026-11-01; journal-specific author requirements still require owner recheck immediately before submission).

## Abstract

Patent-information workflows for medical devices must connect regulatory or product evidence to patent records without silently treating a retrieved candidate as a disclosed relationship. This study evaluates whether adaptive evidence acquisition improves the auditability and resource efficiency of device-patent screening when documented links are incomplete. We compare metadata, lexical, strong fixed hybrid, fixed multi-query, and simple adaptive policies under shared evidence access, candidate universes, cutoffs, group splits, and declared per-call budget units while reporting realized total resources. The primary endpoint is macro known-link Recall@K over source-backed documented relationships; unlisted pairs remain unjudged rather than negative. A separate dossier application uses at least three permitted real device cases and tests source inspection, editing, history, and export. The current repository contains descriptive offline results and a verified local engineering path, but not a rights-cleared semantic relevance gold set, a powered confirmatory comparison, a live provider comparison, or independent user validation. In the frozen descriptive audit, HT-B2 has the highest final-holdout macro Recall@20 (0.8857), while HT-B1 and HT-B4-MOCK each record 0.8381; a four-company sensitivity audit shows that observed rankings vary by held-out company. These results are not equal-total-budget superiority claims because the cohort is small, repeated across local relations, and the realized query/rerank budgets differ by policy. The practical contribution is a reproducible patent-information protocol and evidence-dossier workflow that makes provenance, unknowns, costs, and failure modes inspectable.

Keywords: patent information; medical devices; evidence acquisition; adaptive retrieval; incomplete judgments; provenance; cost-quality trade-off; reproducible research

## 1. Introduction

Medical-device screening sits between regulatory evidence, product descriptions, patent records, and an eventual business or research decision. The evidence is heterogeneous and often incomplete: an official disclosure can support a device-patent association, while a retrieval system can produce only a candidate that still requires review. Collapsing these states creates a practical and scientific error. It can make a candidate look like a confirmed relationship, hide missing evidence, and overstate recall.

This paper studies a narrower question: when the evidence acquisition budget is fixed, does an adaptive policy produce a more auditable dossier or a better quality-cost trade-off than strong fixed baselines and a simple heuristic? The study is deliberately patent-information centered. It does not claim clinical suitability, freedom to operate, patent validity, regulatory approval probability, investment merit, or market demand.

The contributions are:

1. A provenance-bound evaluation contract that preserves raw and canonical identifiers, source revisions, rights policies, exact locators, and the distinction between disclosed links, retrieved candidates, and unjudged pairs.
2. A frozen-input comparison of fixed and adaptive evidence-acquisition policies with predeclared grouping, leakage controls, explicit per-call budget controls, realized-resource accounting, and failure retention.
3. A reproducible dossier workflow that connects retrieval to source inspection, editing, history, and bilingual export for real permitted medical-device cases.
4. A bounded quality-cost and business-value analysis that reports operational potential without inventing user validation, willingness-to-pay, revenue, or ROI.

## 2. Related work and problem framing

Prior work has studied cross-domain medical-device and patent linking, patent analysis, biomedical claim verification, retrieval-augmented generation, adaptive retrieval, and cost-aware evidence selection. The present study differs in its explicit state model and evaluation boundary: a documented association is not the same object as a retrieval candidate, and missing judgment is not a negative label. The computational workflow is therefore evaluated as an evidence-acquisition and provenance system, not as an autonomous legal or clinical decision-maker.

The adaptive policy is not claimed to be novel merely because it uses adaptive retrieval. Adaptive-RAG, dynamic retrieval, cost-aware selection, verification-aware stopping, and related methods establish prior art for those general mechanisms. Any contribution here must come from the medical-device patent-information setting, the matched experimental design, the disclosed-link/unjudged boundary, and the reproducible operational artifacts.

## 3. Research questions and estimands

**RQ1.** Under a frozen device-patent candidate universe and incomplete documented links, how do fixed metadata/lexical/hybrid/multi-query controls and adaptive policies differ in known-link recovery at a fixed budget?

**RQ2.** What resource and failure trade-offs accompany any quality difference, including query count, reranking, embedding, latency, tokens, GPU time, paid cost, retries, and unresolved evidence?

**RQ3.** Can the same evidence engine create a source-inspectable dossier that preserves provenance through correction, version history, reopening, and export?

The primary estimand is macro known-link Recall@K over source-backed documented device-patent relationships in an eligible frozen cohort, aggregated over independent company or patent-family groups where the source mapping supports that grouping. This is recovery of known/documented links, not exhaustive recall or semantic relevance.

## 4. Data, rights, and provenance

The current application slice uses permitted public-source cases including MitraClip, Tendyne, and TriClip. The comparative offline artifacts use the frozen HealthTech cohort recorded by the linked audit manifests. The application slice is not treated as the complete benchmark, and three cases are not treated as a sufficient sample for user or market claims.

Each input record preserves raw and canonical IDs, kind codes, source revision/hash, jurisdiction, date, exact locator, and rights policy. Product-level disclosure evidence remains separate from evaluator-only metadata. Patent families are not merged without a sourced mapping. Public repository release should contain source IDs, URLs, hashes, authored fixtures, and acquisition instructions rather than restricted raw payloads or private source text.

PatEmbed-base and multilingual-e5-base are used under the recorded model revisions and import receipts. DAPFAM is retained as a diagnostic component and is not a semantic device-patent gold set. SciFact is a separate evidence-verification component with its own labels, denominator, rights, and evaluation contract; its scores are not pooled with patent-association recall.

The 1 November 2026 benchmark-expansion continuation adds a rights-checked Helmers human-evaluation archive and four PANORAMA validation/test files. A later selected-manifest extension also inspects PatSnap, PatentsView AIR-UMASS/NBER, and AffRoDB under separate rights and task-fit boundaries. Helmers is used only as a post-freeze selected-pool relevance diagnostic, while PANORAMA is used as a closed-candidate option/paragraph-selection component benchmark. None of these resources is treated as device-patent linkage gold or as a substitute for the matched adaptive dossier study.

## 5. Experimental design

### 5.1 Methods

| ID | Method | Experimental role |
|---|---|---|
| HT-B0a | company/metadata-only control | estimates metadata shortcut value |
| HT-B0b | lexical retrieval | transparent low-cost baseline |
| HT-B1 | strong fixed hybrid | strong fixed comparator |
| HT-B2 | fixed multi-query schedule | tests query breadth without adaptation |
| HT-B3 | simple adaptive heuristic | tests whether a rule is sufficient |
| HT-B4 | bounded controller | optional adaptive condition; live status remains gated |

All methods receive the same frozen corpus, eligible inputs, source cutoff, candidate universe, K, permitted metadata, output schema, failure rules, and declared per-call budget units. Equal inputs and per-call caps do not imply equal total query or rerank budgets when policies stop at different prefixes. If a method uses an additional representation, the matched fixed condition must report and account for that representation as well.

### 5.2 Splits and leakage controls

Development and final holdout groups are separated at the company or patent-family level where the local mapping supports it. Query templates, controller rules, thresholds, stopping logic, and endpoint choices are frozen before final evaluation. Runtime inputs exclude evaluator labels, gold-derived queries, and hidden oracles. Evaluator-only relations are read only after runtime artifacts are frozen.

Repeated cases from one device, patent family, company, or source snapshot are not independent samples. When the effective group count is too small for a stable uncertainty estimate, the result is labeled `NOT_ESTIMABLE` and is not converted into a significance claim.

### 5.3 Reference semantics

The reference set contains documented product-level device-patent relationships. `disclosed_link` requires independent source provenance. `retrieved_candidate` is a system output. `unjudged` means that the pair has not been adjudicated and is not automatically negative. No agent judge, similarity score, or LLM critique is used as a replacement for semantic gold.

### 5.4 Generation comparison

The generation branch compares local `Qwen/Qwen3-8B` with API `qwen/qwen3-32b` only when the existing ledger, current credit, route, rights, and reconciliation gates are satisfied. Both branches must receive the same exact messages, evidence order, schema, and configuration manifest. Because the weights, model size, and provider differ, this is a deployment/configuration comparison, not a pure causal model-size experiment. The current package records local schema-valid generation and keeps live API execution separate when the paid gate is not complete.

## 6. Measures and analysis

### 6.1 Primary and secondary measures

- Primary: macro known-link Recall@20, with K fixed before final evaluation.
- Secondary: micro known-link recall, citation/locator resolution, evidence coverage, unresolved/unknown rate, failed-query rate, query and rerank counts, embedding work, wall-clock time, GPU time, tokens, paid cost, and schema validity.
- Operational dossier measures: source-view availability, history integrity, edit preservation, reopen behavior, and JSON/English/Thai export integrity.
- Human time is measured only when a person actually performs a task. Machine time, GPU time, support time, and human time are never merged.

The analysis reports denominators, group counts, failures, retries, unknowns, and all attempts. Quality-cost frontiers are descriptive. Scenario labor rates and dossier volumes may be used for sensitivity analysis but are not observed revenue or ROI.

### 6.2 Failure and ablation analysis

Report failures due to source unavailability, no new candidates, budget exhaustion, schema failure, provider failure, retry, rights blocking, or user cancellation. Where artifacts permit, ablate company/entity signals, action order, query breadth, stopping, and embedding choice. Preserve hard cases and blocked branches.

## 7. Results

The tables below reproduce the frozen descriptive audit already stored in the repository. They are not a newly executed final confirmatory evaluation on this continuation candidate; each table remains bound to its own audit manifest and revision.

### 7.1 Offline known-link recovery

| Split | HT-B0a | HT-B0b | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|---:|---:|
| Development macro Recall@20 | 0.9613 | 1.0000 | 0.9688 | 0.9063 | 0.9688 |
| Final holdout macro Recall@20 | 0.5429 | 0.8095 | 0.8381 | 0.8857 | 0.8381 |

The holdout row is descriptive and small. HT-B2 is highest in this artifact, but the table does not establish adaptive superiority, semantic relevance, exhaustive recall, or stable generalization.

### 7.2 Leave-one-company-out sensitivity

To reduce dependence on the single Stryker holdout, a separate sensitivity audit reran the same HT-B0a/B0b/B1/B2/B3 controls in four leave-one-company-out views. The frozen local composite contains 11 devices, 31 patents, 38 product-level disclosed pairs, and 303 explicitly unjudged distractor pairs. Each view uses candidate and rerank depth 31 and K=20; the held-out company is untouched until scoring.

| Held-out company | Holdout devices | HT-B0a | HT-B0b | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|---:|---:|---:|
| Boston Scientific Corp | 2 | 0.845238 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| Stryker Neurovascular | 3 | 0.542857 | 0.809524 | 0.838095 | 0.885714 | 0.838095 |
| Cook Medical | 3 | 1.000000 | 1.000000 | 1.000000 | 0.833333 | 1.000000 |
| Philips Image Guided Therapy | 3 | 1.000000 | 1.000000 | 0.916667 | 0.916667 | 0.916667 |

Across these four views, the observed macro Recall@20 ranges are 0.542857–1.000000 for HT-B0a, 0.809524–1.000000 for HT-B0b, 0.838095–1.000000 for HT-B1, 0.833333–1.000000 for HT-B2, and 0.838095–1.000000 for HT-B3. All eight development/holdout splits completed with zero failed devices, zero provider/network calls, and USD0.00 paid cost. The Stryker view is the lowest observed transfer case for HT-B0a, HT-B0b, HT-B1, and HT-B3; Cook is lowest for HT-B2. These repeated rows reuse the same local companies and source relations, so they are sensitivity diagnostics rather than independent samples or confirmatory inference. The source and machine-readable receipt are in [`luna-long-run-20261030-company-holdout-sensitivity-20261030`](../audits/luna-long-run-20261030-company-holdout-sensitivity-20261030/README.md).

### 7.2.1 Paired group uncertainty diagnostic

A separate diagnostic aligned methods by the frozen `group_id` and compared each method with the lexical baseline HT-B0b. The predeclared minimum effective group threshold was five, but both development and final holdout contained only three effective groups. The diagnostic therefore reports descriptive mean deltas, population standard deviations, and ranges, with status `NOT_ESTIMABLE`; it does not report confidence intervals, significance, or a superiority claim.

| Split | Comparison vs HT-B0b | Mean delta | Population SD | Min to max | Status |
|---|---|---:|---:|---:|---|
| Development | HT-B0a | -0.0516 | 0.0730 | -0.1548 to 0.0000 | NOT_ESTIMABLE |
| Development | HT-B1 | 0.0000 | 0.0000 | 0.0000 to 0.0000 | NOT_ESTIMABLE |
| Development | HT-B2 | 0.0000 | 0.0000 | 0.0000 to 0.0000 | NOT_ESTIMABLE |
| Development | HT-B3 | 0.0000 | 0.0000 | 0.0000 to 0.0000 | NOT_ESTIMABLE |
| Final holdout | HT-B0a | -0.1333 | 0.1886 | -0.4000 to 0.0000 | NOT_ESTIMABLE |
| Final holdout | HT-B1 | -0.0190 | 0.1406 | -0.2000 to 0.1429 | NOT_ESTIMABLE |
| Final holdout | HT-B2 | -0.0190 | 0.1406 | -0.2000 to 0.1429 | NOT_ESTIMABLE |
| Final holdout | HT-B3 | -0.0667 | 0.0943 | -0.2000 to 0.0000 | NOT_ESTIMABLE |

The observed wall-time/recall frontier remains HT-B0a and HT-B0b in both frozen views. This diagnostic strengthens uncertainty reporting but does not create semantic relevance gold or independent samples. Reproduction and machine-readable values are in [`luna-long-run-20261029-m12-group-uncertainty-20261029`](../audits/luna-long-run-20261029-m12-group-uncertainty-20261029/README.md).

### 7.3 Provider-shaped mock control

| Method | Final holdout macro Recall@20 |
|---|---:|
| HT-B0a | 0.5429 |
| HT-B0b | 0.8095 |
| HT-B1 | 0.8381 |
| HT-B2 | 0.8857 |
| HT-B3 | 0.8381 |
| HT-B4-MOCK | 0.8381 |

HT-B4-MOCK exercised action schemas and accounting paths. It was not live-provider evidence and its simulated debit is not paid cost.

A current-head reproducibility rerun of the deterministic offline HT-B4 controller
used the same frozen Abbott and Boston cohorts, K=20, candidate depth 50,
rerank depth 50, and maximum three controller steps. Abbott achieved macro and
micro Recall@20 of 0.498802 and 0.475410 over three devices; Boston achieved
1.000000 and 1.000000 over two devices. No device failed, provider calls were
zero, and paid cost was USD0.00. Boston is ceiling-limited because K=20 exceeds
its seven-patent candidate universe. The rerun is reproducibility evidence for
the offline controller, not a semantic adaptive-superiority result; its exact
input/output hashes are recorded in [`ht-o4-offline-current-head-20261101`](../audits/ht-o4-offline-current-head-20261101/README.md).

### 7.4 Frozen-input current-head offline frontier

To make the O4 comparison explicit on one frozen cohort, the 1 November
current-head candidate `891f3b3` reran HT-B0a/B0b/B1/B2/B3 and the deterministic offline HT-B4
controller on the same Abbott runtime, references, groups, encoder/reranker
bundle, candidate depth 41, rerank depth 41, and K=20. All fifteen
method-device rows and all controller devices completed without failure. These
conditions match evidence access and per-call depth; they do not equalize total
query or rerank budgets across policies.

| Method | Macro Recall@20 | Query calls | Rerank pairs | Evidence class |
|---|---:|---:|---:|---|
| HT-B0a | 0.442739 | 3 | 0 | offline metadata control |
| HT-B0b | 0.662242 | 3 | 0 | offline lexical control |
| HT-B1 | 0.498802 | 3 | 123 | offline fixed hybrid |
| HT-B2 | 0.568912 | 9 | 369 | offline fixed multi-query |
| HT-B3 | 0.498802 | 5 | 205 | offline heuristic |
| HT-B4 offline | 0.498802 | 5 | 205 | deterministic controller |

The controller also recorded micro Recall@20 `0.475410` and eight controller
steps. The realized total retrieval budgets were 3 query calls/123 rerank pairs
for HT-B1, 9/369 for HT-B2, and 5/205 for both HT-B3 and offline HT-B4. The
eight HT-B4 controller steps are a separate action count, not a dollar or
rerank budget. B0b is the strongest observed condition in this development
slice; B4 ties B1 and B3 at the macro endpoint. This is a frozen-input,
realized quality-resource frontier, not an equal-total-budget comparison and
not evidence that adaptive acquisition is generally better or worse. The
cohort has two exact-patent groups, one company group, no final holdout, and
product-level disclosed-link labels rather than semantic relevance gold. The
raw/evaluator receipts and hashes are in
[`ht-o4-matched-offline-current-head-20261101`](../audits/ht-o4-matched-offline-current-head-20261101/README.md).

#### 7.4.1 Post-hoc equalized first-action diagnostic

Because the full frontier has unequal realized budgets, we also extracted a
post-hoc descriptive slice at exactly three query calls and 123 rerank pairs.
This selects the first action for HT-B1, HT-B2, and HT-B3; it does not represent
the completed adaptive policy for HT-B3, and it was not the preregistered final
endpoint.

| Condition | Prefix | Query calls | Rerank pairs | Macro Recall@20 |
|---|---:|---:|---:|---:|
| HT-B1 | 1 | 3 | 123 | 0.498802 |
| HT-B2 | 1 | 3 | 123 | 0.498802 |
| HT-B3 | 1 | 3 | 123 | 0.498802 |

All three selected rows had zero failed and zero not-realized queries. The
equality is therefore an observed first-action budget control, not evidence
that adaptive acquisition improves the endpoint. HT-B4 is excluded from this
slice because its controller-step count is not directly interchangeable with
the query/rerank budget, and its receipt does not provide a predeclared
same-unit final comparison. The machine-readable diagnostic is in
[`ptp-matched-budget-prefix-20261103/verification.json`](../audits/ptp-matched-budget-prefix-20261103/verification.json).

### 7.5 Engineering application slice

The recorded O1-O4 engineering receipt from the reviewed prior candidate covers
three named real-device cases through browser/HTTP job start, retrieval, local
generation, source inspection, edit/history, reopen, and export. Local
generation was schema-valid for `3/3` cases in that receipt; provider calls
were `0` and paid cost was `USD0.00`. The current continuation candidate has
passed the loopback HTTP contract, but its exact-head real-case rerun is
asset-gated because the permitted cohort, rights matrix, and vector/runtime
bundles are not present. This is engineering and application evidence, not a
user study or a three-case scientific benchmark.

### 7.6 Figures and machine-readable outputs

The current frozen descriptive audits provide the following actual figure and table inputs:

- [Development quality-cost frontier](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/quality_cost_development.svg)
- [Holdout quality-cost frontier](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/quality_cost_holdout.svg)
- [Recall comparison](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/recall_comparison.svg)
- [Quality-cost table](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/quality_cost_frontier.csv)
- [Four-company holdout sensitivity audit](../audits/luna-long-run-20261030-company-holdout-sensitivity-20261030/README.md)
- [Current O1-O4 browser report](../audits/ht-o4-remote-http-generation-browser-20261031/REPORT.md)

### 7.7 Benchmark-expansion component diagnostics

The post-freeze continuation acquired and verified five files from the staged manifest, then ran a deterministic CPU lexical baseline on the four official PANORAMA validation/test splits. The runtime did not read `gold_answers`, `silver_answers`, or `negative_answers` when ranking; all rows remained in the denominator and failed-output rate was zero.

| Component | Split / pool | Units | Primary descriptive result | Failed-output rate |
|---|---|---:|---:|---:|
| PANORAMA PAR4PC | validation | 3,029 rows | macro gold option hit@1 = 0.733575 | 0.0 |
| PANORAMA PAR4PC | test | 2,896 rows | macro gold option hit@1 = 0.715124 | 0.0 |
| PANORAMA PI4PC | validation | 3,937 rows | macro gold paragraph hit@1 = 0.377699 | 0.0 |
| PANORAMA PI4PC | test | 3,402 rows | macro gold paragraph hit@1 = 0.401235 | 0.0 |
| Helmers | 10 targets / 450 judged pairs | 258 positive pairs | macro AP = 0.885450; macro AUC = 0.880012 | not applicable |

The PANORAMA test rows are final component holdouts under the official application split, but shared candidate IDs across official splits are reported as a diagnostic (149 for PAR4PC and 38 for PI4PC) rather than silently removed. The Helmers judged pool was selected by the source authors and has no modern official dev/test split. These results therefore provide robustness and component evidence only; they do not estimate adaptive dossier superiority, exhaustive device-patent recall, or independent global relevance.

## 8. Practical business value as potential

The system provides a plausible operational path for entrepreneurs and investor analysts because it exposes source locators, evidence states, unresolved items, editable history, and exportable dossiers. The evidence currently supports potential value in four measurable dimensions: citation/locator quality, evidence coverage, machine/GPU time, and cost-quality trade-off.

The three-case browser receipt provides a machine-side operational proxy, not a user-productivity result:

| Operational measure | Observed value |
|---|---:|
| Named real-device cases | 3 |
| Local generation schema-valid cases | 3/3 |
| Local generation latency | 32.888–33.121 seconds per case; mean 33.023 seconds |
| Source inspection, history 1→2, and JSON export | 3/3 cases |
| Paid provider calls / paid cost | 0 / USD0.00 |

These measurements exclude human time, support time, and external-user behavior. They should be used for capacity and cost scenarios only, not as a service-level promise or ROI evidence.

The repository does not contain independent user validation, measured willingness-to-pay, a purchase, revenue, or ROI. If the owner runs the workflow personally, the result must be labeled `developer_self_evaluation` and interpreted as formative evidence with builder familiarity bias. Any labor-rate or dossier-volume scenario must remain a sensitivity analysis, not a commercial outcome.

## 9. Ethics, data rights, and responsible use

This current round is a solo computational study. No external participants were enrolled, no consent was collected, and no participant data are included. The repository therefore does not claim human-subject approval, exemption, usability validation, or customer validation. A future human-study consent template is stored separately and is inactive.

Data rights are handled per source and purpose. Restricted source text, private journals, credentials, and private payloads remain outside Git. The workflow must not be used as a clinical, regulatory, legal, FTO, patent-validity, or investment decision without qualified review.

## 10. Reproducibility and availability

The code, schemas, authored fixtures, audit manifests, protocol, model/configuration identifiers, and reproduction commands are stored in the repository. Private artifacts contain the exact prompts/messages, input/output hashes, errors, retries, latency, token/cost receipts, source hashes, and ledger state; they are not published when rights or privacy do not permit it. The public release should provide IDs, URLs, hashes, and acquisition instructions instead of restricted payloads.

The benchmark-expansion reproducibility addendum and machine-readable receipts are in [`SUPPLEMENTAL_DATA.md`](SUPPLEMENTAL_DATA.md) and [`benchmark-expansion-20261101`](../audits/benchmark-expansion-20261101/README.md). They bind the five acquired files, freeze rules, component metrics, and cleanup limitation to the continuation candidate.

An additional manifest extension was inspected without changing the primary experiment: a 30-row PatSnap claim-charting file, two PatentsView assignee benchmark CSVs, and a 1,374-row AffRoDB JSONL file passed the recorded byte/hash/schema checks. PatSnap and AffRoDB remain unscored diagnostics; PatentsView remains excluded because standalone data rights were not established, and AffRoDB lacks the pinned ROR v1.40 registry needed for a valid linkage evaluation. These assets therefore do not add evidence for adaptive dossier superiority and are retained only as rights-aware reproducibility inventory.

The historical component scores remain bound to pre-run candidate `cd7e5d364d529a001fc51f78c217c10d7d9c8945` and are retained for provenance only. A current-head revalidation was run against `ab7ad348ff2fb3ec8e02a52a49ccddd1657504fd` using the same frozen protocol and verified payloads; its summary/prediction hashes and failure denominator are recorded in [`CURRENT_HEAD_COMPONENT_RESULTS.json`](../audits/benchmark-expansion-20261101/CURRENT_HEAD_COMPONENT_RESULTS.json) and [`CHECKPOINT_V10_CURRENT_HEAD.json`](../audits/benchmark-expansion-20261101/CHECKPOINT_V10_CURRENT_HEAD.json). Results from different candidates or different protocol manifests are not combined into one PASS claim.

## 11. Limitations

1. Documented product-level links are not semantic patent relevance gold; unjudged pairs are not negatives.
2. The current effective group counts and holdout size are too small for stable generalization or confirmatory significance claims.
3. The three real-device cases demonstrate the workflow but do not replace a benchmark, user study, or market validation.
4. Local `Qwen/Qwen3-8B` and API `qwen/qwen3-32b` differ in size and provider, so any comparison is configuration-level.
5. Live paid API evidence remains conditional on the canonical ledger, current credit, route, rights, and reconciliation gates.
6. DAPFAM is diagnostic and is not a device-patent gold set.
7. PANORAMA measures closed-candidate examination choices, not the full evidence-acquisition loop; Helmers is a selected judged-pool diagnostic, not independent global gold.
8. No independent user validation, willingness-to-pay, revenue, ROI, clinical, legal, FTO, patent-validity, or investment conclusion is supported.
9. The selected optional/conditional manifest extension is not a new final benchmark: PatentsView rights remain unresolved, AffRoDB lacks its required registry snapshot, and the PatSnap file is too small and task-misaligned for the primary claim.

## 12. Conclusion

The current evidence supports a reproducible patent-information workflow and a disciplined computational study design for adaptive evidence acquisition under incomplete judgments. The four-company sensitivity audit and the new PANORAMA/Helmers component results show that the pipeline can be evaluated against multiple task-shaped signals, while also exposing the limits of transferring option-selection or selected-pool relevance metrics into device-patent dossier claims. The strongest defensible contribution is the combination of provenance-aware state separation, explicit per-call and realized-resource accounting, explicit unknowns, reproducible dossier operations, and honest quality-cost reporting. A stronger scientific conclusion requires a final adaptive dossier study with equalized total budgets, independent groups, and an appropriate semantic judgment source or benchmark. A stronger business conclusion requires future authorized user or customer evidence.

## Declarations

**Funding:** No external funding is recorded for this computational study. Confirm before submission.

**Conflicts of interest:** No conflict is declared in the current draft. The owner must confirm before submission.

**Author contributions:** The owner must confirm names and contribution statements before submission. Suggested structure: conceptualization and supervision by the owner; software, data curation, methodology implementation, investigation, and draft preparation by the project team; review and approval by the owner.

**AI-use disclosure:** AI-assisted coding and drafting were used under owner direction. All claims, source links, experiment boundaries, and final submission materials require owner review. No AI system is treated as an independent scientific evaluator or source of gold labels.

**Ethics statement:** No human participants or participant data were used in the current round. Future human-study materials are inactive templates.

## References

The following references are drawn from the checked local bibliography at `literature-review/healthtech/references.bib`; identifiers and links should be rechecked at submission.

1. Yang, Q., Liu, H., and Li, M. (2026). From Regulatory Approvals to Patents: Cross-Domain Linking for Cardiovascular Device Traceability. ACL 2026. doi:10.18653/v1/2026.acl-long.1611.
2. Wadden, D., Lin, S., Lo, K., Wang, L. L., van Zuylen, M., Cohan, A., and Hajishirzi, H. (2020). Fact or Fiction: Verifying Scientific Claims. EMNLP 2020. doi:10.18653/v1/2020.emnlp-main.609.
3. Xiong, G., Jin, Q., Lu, Z., and Zhang, A. (2024). Benchmarking Retrieval-Augmented Generation for Medicine. Findings of ACL 2024. doi:10.18653/v1/2024.findings-acl.372.
4. Pai, D. B. (2021). Mapping the genealogy of medical device predicates in the United States. PLOS ONE, 16(10), e0258153. doi:10.1371/journal.pone.0258153.
5. Shomee, H. H., Wang, Z., Ravi, S. N., and Medya, S. (2025). A Survey on Patent Analysis: From NLP to Multimodal AI. ACL 2025. doi:10.18653/v1/2025.acl-long.419.
6. Jeong, S., Baek, J., Cho, S., Hwang, S. J., and Park, J. (2024). Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity. Proceedings of NAACL-HLT 2024, 7036–7050. doi:10.18653/v1/2024.naacl-long.389.
7. Su, W., Tang, Y., Ai, Q., Wu, Z., and Liu, Y. (2024). DRAGIN: Dynamic Retrieval Augmented Generation based on the Information Needs of Large Language Models. Proceedings of ACL 2024, 12991–13013. doi:10.18653/v1/2024.acl-long.702.
8. Wu, M., Yang, H., Ben-Porat, O., and Ziser, Y. (2026). When Knowledge Is Not Free: Cost-Aware Evidence Selection in Retrieval-Augmented Generation. Findings of EMNLP 2026, 8713–8739. https://aclanthology.org/2026.findings-emnlp.413/.
9. Poce, S., and Cerro, G. (2026). A survey on automated and AI-based tools for patent retrieval with a special focus on the life sciences domain. World Patent Information. doi:10.1016/j.wpi.2026.102439.
10. Helmers, L., Horn, F., Biegler, F., Oppermann, T., and Müller, K.-R. (2019). Automating the search for a patent's prior art with a full text similarity search. PLOS ONE, 14(3), e0212103. doi:10.1371/journal.pone.0212103.
11. Ayaou, I., Cavallucci, D., and Chibane, H. (2025). DAPFAM: A Domain-Aware Family-level Dataset to benchmark cross domain patent retrieval. arXiv:2506.22141.
12. Lim, H., Nam, S., Na, S., Cho, J. Y., Yang, J. Y., Shin, H., Lee, Y., Kim, J., Lee, M., and Hong, H. (2025). PANORAMA: A Dataset and Benchmarks Capturing Decision Trails and Rationales in Patent Examination. NeurIPS 2025 Datasets and Benchmarks; arXiv:2510.24774.

## Author-review checklist

- Confirm author names, affiliations, funding, conflicts, and contribution statement.
- Recheck the official World Patent Information Guide for Authors and journal-specific submission fields immediately before submission; the scope check is recorded in [`WPI_SUBMISSION_CHECKLIST_20261101_EN.md`](WPI_SUBMISSION_CHECKLIST_20261101_EN.md).
- Rebind every table and figure to the final candidate revision and one protocol manifest.
- Confirm whether the final paper includes only published/permitted aggregate outputs and source identifiers.
- Keep human pilot, customer validation, revenue, willingness-to-pay, and ROI as future work unless new evidence is added.
