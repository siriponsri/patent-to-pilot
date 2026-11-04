# Evaluating Adaptive Evidence Acquisition for Medical-Device Patent Screening under Incomplete Judgments

Status: `DRAFT_FOR_OWNER_REVIEW / SOLO_COMPUTATIONAL_STUDY / NOT_SUBMITTED`

Target venue: *World Patent Information* (official Elsevier profile scope rechecked on 2026-11-04; journal-specific author requirements still require owner recheck immediately before submission).

## Abstract

Patent-information workflows for medical devices must connect regulatory or product evidence to patent records without silently treating a retrieved candidate as a disclosed relationship. This study evaluates whether adaptive evidence acquisition improves the auditability and resource efficiency of device-patent screening when documented links are incomplete. We compare metadata, lexical, strong fixed hybrid, fixed multi-query, and simple adaptive policies under shared evidence access, candidate universes, cutoffs, group splits, and declared per-call budget units while reporting realized total resources. The primary endpoint is macro known-link Recall@K over source-backed documented relationships; unlisted pairs remain unjudged rather than negative. A separate dossier application uses at least three permitted real device cases and tests source inspection, editing, history, and export. The current repository contains descriptive offline results and a verified local engineering path, but not a rights-cleared semantic relevance gold set, a powered confirmatory comparison, a live provider comparison, or independent user validation. A historical transfer diagnostic recorded HT-B2 at macro Recall@20 0.8857 and HT-B1 and provider-shaped HT-B4-MOCK at 0.8381; those values are retained for provenance only and are not pooled with the current-head three-device frontier. A four-company sensitivity audit shows that observed rankings vary by held-out company. These results are not equal-total-budget superiority claims because the cohort is small, repeated across local relations, and the realized query/rerank budgets differ by policy. The practical contribution is a reproducible patent-information protocol and evidence-dossier workflow that makes provenance, unknowns, costs, and failure modes inspectable.

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

Development and final evaluation groups are separated at the company or patent-family level where the local mapping supports it. Query templates, controller rules, thresholds, stopping logic, and endpoint choices are frozen before final evaluation. Runtime inputs exclude evaluator labels, gold-derived queries, and hidden oracles. Evaluator-only relations are read only after runtime artifacts are frozen.

Repeated cases from one device, patent family, company, or source snapshot are not independent samples. When the effective group count is too small for a stable uncertainty estimate, the result is labeled `NOT_ESTIMABLE` and is not converted into a significance claim.

### 5.3 Reference semantics

The reference set contains documented product-level device-patent relationships. `disclosed_link` requires independent source provenance. `retrieved_candidate` is a system output. `unjudged` means that the pair has not been adjudicated and is not automatically negative. No agent judge, similarity score, or LLM critique is used as a replacement for semantic gold.

### 5.4 Generation comparison

The generation branch compares local `Qwen/Qwen3-8B` with API `qwen/qwen3-32b` only when the existing ledger, current credit, route, rights, and reconciliation gates are satisfied. Both branches must receive the same exact messages, evidence order, schema, and configuration manifest. Because the weights, model size, and provider differ, this is a deployment/configuration comparison, not a pure causal model-size experiment. The current package records a current-head guided local inference over a rights-cleared patent-candidate pack and keeps live API execution separate while the paid gate is incomplete. The exact-head local receipts are new inference runs bound to the current candidate; earlier runtime-bound receipts remain historical and are not pooled with them. See [`ptp-local-qwen-exact-head-20261103/verification.json`](../audits/ptp-local-qwen-exact-head-20261103/verification.json), [`ptp-local-qwen-patent-run-20261104/verification.json`](../audits/ptp-local-qwen-patent-run-20261104/verification.json), and [`ptp-current-head-runtime-rebind-20261103/verification.json`](../audits/ptp-current-head-runtime-rebind-20261103/verification.json).

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

The two rows below are retained from the previously exposed transfer-diagnostic
package and its bound protocol, not from the current-head `88dc4047` run. They
are shown for provenance and sensitivity context only. The current-head
three-device frontier is reported separately in Section 7.5; results from the
two candidates are not pooled into one endpoint or PASS claim.

| Split | HT-B0a | HT-B0b | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|---:|---:|
| Development macro Recall@20 | 0.9613 | 1.0000 | 0.9688 | 0.9063 | 0.9688 |
| Previously exposed transfer-diagnostic macro Recall@20 | 0.5429 | 0.8095 | 0.8381 | 0.8857 | 0.8381 |

The transfer-diagnostic row is previously exposed, descriptive, and small. HT-B2 is highest in this artifact, but the table does not establish adaptive superiority, semantic relevance, exhaustive recall, or stable generalization.

### 7.2 Leave-one-company-out sensitivity

To reduce dependence on the single previously exposed Stryker transfer diagnostic,
a separate older-candidate sensitivity audit reran the same HT-B0a/B0b/B1/B2/B3
controls in four leave-one-company-out views. The frozen local composite
contains 11 devices, 31 patents, 38 product-level disclosed pairs, and 303
explicitly unjudged distractor pairs. Each view uses candidate and rerank depth
31 and K=20; the scoring-excluded company is untouched until scoring. These
rows remain sensitivity evidence from that bound audit and are not combined
with the current-head `88dc4047` results in Section 7.5.

| Scoring-excluded company | Scoring-excluded devices | HT-B0a | HT-B0b | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|---:|---:|---:|
| Boston Scientific Corp | 2 | 0.845238 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| Stryker Neurovascular | 3 | 0.542857 | 0.809524 | 0.838095 | 0.885714 | 0.838095 |
| Cook Medical | 3 | 1.000000 | 1.000000 | 1.000000 | 0.833333 | 1.000000 |
| Philips Image Guided Therapy | 3 | 1.000000 | 1.000000 | 0.916667 | 0.916667 | 0.916667 |

Across these four views, the observed macro Recall@20 ranges are 0.542857–1.000000 for HT-B0a, 0.809524–1.000000 for HT-B0b, 0.838095–1.000000 for HT-B1, 0.833333–1.000000 for HT-B2, and 0.838095–1.000000 for HT-B3. All eight development/transfer-diagnostic splits completed with zero failed devices, zero provider/network calls, and USD0.00 paid cost. The Stryker view is the lowest observed transfer case for HT-B0a, HT-B0b, HT-B1, and HT-B3; Cook is lowest for HT-B2. These repeated rows reuse the same local companies and source relations, so they are sensitivity diagnostics rather than independent samples or confirmatory inference. The source and machine-readable receipt are in [`luna-long-run-20261030-company-holdout-sensitivity-20261030`](../audits/luna-long-run-20261030-company-holdout-sensitivity-20261030/README.md).

### 7.2.1 Paired group uncertainty diagnostic

A separate diagnostic aligned methods by the frozen `group_id` and compared each method with the lexical baseline HT-B0b. The predeclared minimum effective group threshold was five, but both development and the previously exposed transfer diagnostic contained only three effective groups. The diagnostic therefore reports descriptive mean deltas, population standard deviations, and ranges, with status `NOT_ESTIMABLE`; it does not report confidence intervals, significance, or a superiority claim.

| Split | Comparison vs HT-B0b | Mean delta | Population SD | Min to max | Status |
|---|---|---:|---:|---:|---|
| Development | HT-B0a | -0.0516 | 0.0730 | -0.1548 to 0.0000 | NOT_ESTIMABLE |
| Development | HT-B1 | 0.0000 | 0.0000 | 0.0000 to 0.0000 | NOT_ESTIMABLE |
| Development | HT-B2 | 0.0000 | 0.0000 | 0.0000 to 0.0000 | NOT_ESTIMABLE |
| Development | HT-B3 | 0.0000 | 0.0000 | 0.0000 to 0.0000 | NOT_ESTIMABLE |
| Previously exposed transfer diagnostic | HT-B0a | -0.1333 | 0.1886 | -0.4000 to 0.0000 | NOT_ESTIMABLE |
| Previously exposed transfer diagnostic | HT-B1 | -0.0190 | 0.1406 | -0.2000 to 0.1429 | NOT_ESTIMABLE |
| Previously exposed transfer diagnostic | HT-B2 | -0.0190 | 0.1406 | -0.2000 to 0.1429 | NOT_ESTIMABLE |
| Previously exposed transfer diagnostic | HT-B3 | -0.0667 | 0.0943 | -0.2000 to 0.0000 | NOT_ESTIMABLE |

The observed wall-time/recall frontier remains HT-B0a and HT-B0b in both frozen views. This diagnostic strengthens uncertainty reporting but does not create semantic relevance gold or independent samples. Reproduction and machine-readable values are in [`luna-long-run-20261029-m12-group-uncertainty-20261029`](../audits/luna-long-run-20261029-m12-group-uncertainty-20261029/README.md).

### 7.3 Provider-shaped mock control

| Method | Previously exposed transfer-diagnostic macro Recall@20 |
|---|---:|
| HT-B0a | 0.5429 |
| HT-B0b | 0.8095 |
| HT-B1 | 0.8381 |
| HT-B2 | 0.8857 |
| HT-B3 | 0.8381 |
| HT-B4-MOCK | 0.8381 |

This table uses a previously exposed transfer diagnostic. HT-B4-MOCK exercised action schemas and accounting paths. It was not live-provider evidence and its simulated debit is not paid cost.

A prior current-head reproducibility package of the deterministic offline HT-B4
controller used frozen Abbott and Boston cohorts, K=20, candidate depth 50,
rerank depth 50, and maximum three controller steps. It is retained as a
separately bound diagnostic from candidate `94ce5b10f7b787677ebd11d8c3f193753e4b7d8c`:
Abbott achieved macro and micro Recall@20 of 0.498802 and 0.475410 over three
devices; Boston achieved 1.000000 and 1.000000 over two devices. No device
failed, provider calls were zero, and paid cost was USD0.00. Boston is
ceiling-limited because K=20 exceeds its seven-patent candidate universe. This
historical package is reproducibility evidence for the offline controller, not
a semantic adaptive-superiority result.

### 7.4 Frozen-input current-head offline frontier

To make the O4 comparison explicit on one frozen cohort, the 3 November
current-head candidate `88dc40471cb9078f929c02bb893cfa1e364da841` reran
HT-B0a/B0b/B1/B2/B3 and the deterministic offline HT-B4 controller on the same
Abbott runtime, references, groups, encoder/reranker bundle, candidate depth 41,
rerank depth 41, and K=20. All fifteen
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
raw/evaluator receipts and hashes for this exact candidate are in
[`ptp-current-head-offline-20261103`](../audits/ptp-current-head-offline-20261103/README.md).
The protocol-availability audit separately confirms that the current Abbott
cohort is development-only and that historical Stryker diagnostics are not a
substitute for a current-head final holdout
([`ptp-current-head-holdout-availability-20261103`](../audits/ptp-current-head-holdout-availability-20261103/README.md)).

#### 7.4.1 Post-hoc equalized first-action diagnostic

Because the full frontier has unequal realized budgets, we also extracted a
post-hoc descriptive slice at exactly three query calls and 123 rerank pairs.
This selects the first action for HT-B1, HT-B2, and HT-B3; it does not represent
the completed adaptive policy for HT-B3, and it was not the preregistered final
endpoint.

This diagnostic is bound to current candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. The older `891f3b3` package is
historical diagnostic evidence only and is not pooled with this current-head
receipt.

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
same-unit final comparison. The machine-readable current-head diagnostic is in
[`ptp-current-head-matched-budget-20261103/verification.json`](../audits/ptp-current-head-matched-budget-20261103/verification.json).

#### 7.4.1a Post-hoc budget-ceiling sensitivity

We also reconciled the saved frontier against each observed query/rerank
ceiling. This is a post-hoc descriptive analysis: the selected row for each
method is the maximum observed prefix within the ceiling, with no endpoint-based
selection and no rerun. Only the first ceiling has equal realized resources
across HT-B1, HT-B2, and HT-B3.

| Ceiling | HT-B1 | HT-B2 | HT-B3 | Interpretation |
|---|---:|---:|---:|---|
| 3 query calls / 123 rerank pairs | 0.498802 (3/123) | 0.498802 (3/123) | 0.498802 (3/123) | equal realized budget |
| 5 / 205 | 0.498802 (3/123) | 0.498802 (3/123) | 0.224293 (5/205) | at-most ceiling; B3 has 1 not-realized query |
| 6 / 246 | 0.498802 (3/123) | 0.498802 (6/246) | 0.224293 (5/205) | at-most ceiling; realized budgets differ |
| 9 / 369 | 0.498802 (3/123) | 0.568912 (9/369) | 0.224293 (5/205) | at-most ceiling; realized budgets differ |

The exact 3/123 row is the only matched-budget diagnostic. The larger rows
should not be read as equal-budget comparisons, because policies reached
different realized prefixes and HT-B3 did not realize one scheduled query at
its second prefix. The analysis remains development-only, has no final holdout
or semantic relevance gold, and does not support an adaptive-superiority or
significance claim. The machine-readable reconciliation is in
[`ptp-private-frontier-budget-ceilings-20261104/verification.json`](../audits/ptp-private-frontier-budget-ceilings-20261104/verification.json).

#### 7.4.2 Transformer encoder component diagnostic

The O2 path also has an actual prior remote run on `dr-train`: PatEmbed-base and
multilingual-e5-base encoded 45,336 passage rows into resumable shards and 1,247
query rows into imported bundles. On the frozen DAPFAM diagnostic with 49,869
qrel pairs, PatEmbed dense retrieval reached macro Recall@100 `0.422525`, micro
Recall@100 `0.422319`, and macro nDCG@100 `0.348830`; multilingual-e5 dense
retrieval reached macro Recall@100 `0.287414`, micro Recall@100 `0.287296`, and
macro nDCG@100 `0.244781`. Both runs recorded zero dense failures.

| Encoder | Passage rows | Query rows | Qrel pairs | Macro Recall@100 | Micro Recall@100 | Macro nDCG@100 | Dense failures |
|---|---:|---:|---:|---:|---:|---:|---:|
| PatEmbed-base | 45,336 | 1,247 | 49,869 | 0.422525 | 0.422319 | 0.348830 | 0 |
| multilingual-e5-base | 45,336 | 1,247 | 49,869 | 0.287414 | 0.287296 | 0.244781 | 0 |

This is a component diagnostic over DAPFAM citation-based labels, not semantic
device-patent relevance gold. The remote receipt is an actual prior run; the
current candidate uses a zero-diff runtime rebind and vector-bundle integrity
revalidation. A read-only reconciliation on 3 November 2026 matched all four
private local bundle manifests to the prior `dr-train` manifests. This confirms
artifact identity but does not constitute a new remote encode or GPU window, so
no new remote encode or GPU window is claimed here. The
current candidate also has a fresh acquisition checkpoint verifying the pinned
PatEmbed and multilingual-e5 model snapshots in private ignored Windows
storage. A two-row-per-model local CPU runtime smoke also passed model loading
and L2 normalization, but no new encode or quality result is pooled into this
table. A later read-only current-head reconciliation matched the same four
device bundle manifests to both current server-owned dossier providers: all
three named cases succeeded for PatEmbed and all three succeeded for
multilingual-e5, with zero vector errors and source/history/edit/export passing.
This closes the O2 engineering boundary while leaving the scientific endpoint
descriptive and `NOT_ESTIMABLE`. The
machine-readable sources are [`ht-research-product-20261031/verification.json`](../audits/ht-research-product-20261031/verification.json),
[`ptp-current-head-runtime-rebind-20261103/verification.json`](../audits/ptp-current-head-runtime-rebind-20261103/verification.json),
[`ptp-vector-artifact-revalidation-20261103/verification.json`](../audits/ptp-vector-artifact-revalidation-20261103/verification.json),
[`ptp-o2-model-snapshot-20261103/verification.json`](../audits/ptp-o2-model-snapshot-20261103/verification.json),
[`ptp-remote-artifact-manifest-reconciliation-20261103/verification.json`](../audits/ptp-remote-artifact-manifest-reconciliation-20261103/verification.json),
and [`ptp-o2-current-head-completion-r16-20261104/verification.json`](../audits/ptp-o2-current-head-completion-r16-20261104/verification.json).

#### 7.4.3 Fresh current-head three-device transformer diagnostic

On 3 November 2026, the current candidate also completed a fresh bounded
`dr-train` run over the three-device development pack. PatEmbed-base and
multilingual-e5-base each encoded 41 patent passages and 3 device queries in
one GPU process, with four encode passes and 88 output rows overall. The
resulting vectors were retained on Windows, and a separate verifier
recomputed rankings and metrics from the saved arrays with maximum absolute
delta `0.0` at tolerance `1e-12`.

| Method | Hits / 61 | Macro Recall@20 | Micro Recall@20 | Macro nDCG@20 |
|---|---:|---:|---:|---:|
| Frozen-query BM25 | 21 / 61 | 0.392685 | 0.344262 | 0.430022 |
| PatEmbed dense | 24 / 61 | 0.430073 | 0.393443 | 0.409533 |
| multilingual E5 dense | 27 / 61 | 0.481021 | 0.442623 | 0.455981 |

This is a fresh three-device retrieval diagnostic, not a final holdout or a
semantic relevance evaluation. MitraClip and Tendyne share one query text,
unlisted patents remain unjudged, and the results are not pooled with the
DAPFAM component or the current-head HT-B0b/B1/B2/B3 frontier. The current
HTTP dossier receipt using the earlier MiniLM ONNX bundle remains a separate
protocol/result. A subsequent current-head run explicitly binds the PatEmbed
bundle to the dossier provider and completes the same three application cases;
it does not bind multilingual-e5 or turn the application slice into semantic
gold. The complete binding, source/model hashes, resource receipt, and
integration boundary are in
[`ptp-fresh-gpu-device-diagnostic-20261103/verification.json`](../audits/ptp-fresh-gpu-device-diagnostic-20261103/verification.json).

The PatEmbed provider-binding receipt is
[`ptp-o2-patembed-http-rebind-20261103/verification.json`](../audits/ptp-o2-patembed-http-rebind-20261103/verification.json).
It records 3/3 succeeded cases, source inspection status `200`, history edit
version `1 -> 2`, JSON/Thai/English export success, zero vector errors, zero
provider calls, and zero paid cost. Candidate counts were 35/35/41 and dense
candidate counts were 33/33/41 for MitraClip, Tendyne, and TriClip,
respectively. These are engineering/application measures, not retrieval
quality endpoints or evidence of adaptive superiority.

#### 7.4.4 Medical-subset denominator and saved-ranking diagnostic

An independent read-only recheck of the saved medical-ranking package covered
`96` medical queries and `3,061` screened patents. The full query-positive
denominator is **`1,920 = 983` both-screen positives + `937` target-unscreened
positives**. The denominator is therefore not reducible to the `983` pairs that
passed both screening rules. The check used selected-column reads, a literal
substring screen, set-based qrels, and rank arithmetic without importing the
production evaluator; it found zero duplicate qrel pairs, zero selected
positive self-hits, and `10` selected queries without a both-screen positive.

| Method | Hits / 1,920 | Recall@100 | nDCG@100 |
|---|---:|---:|---:|
| BM25 | 326 | 0.169792 | 0.149408 |
| PatEmbed dense | 715 | 0.372396 | 0.310173 |
| PatEmbed + BM25 hybrid | 628 | 0.327083 | 0.264248 |
| multilingual E5 dense | 488 | 0.254167 | 0.213106 |
| multilingual E5 + BM25 hybrid | 457 | 0.238021 | 0.202883 |

These values are an independently recomputed diagnostic over Oct 31 saved
rankings, not a final semantic holdout or a claim of exhaustive medical-device
patent relevance. The input hashes were unchanged during the check and no new
model, GPU, metadata, or paid calls were used. The machine-readable recheck is
[`pepo-strong-followup-20261104/medical-recheck.json`](../audits/pepo-strong-followup-20261104/medical-recheck.json).

### 7.5 Engineering application slice

The recorded O1-O4 engineering receipt from the reviewed prior candidate covers
three named real-device cases through browser/HTTP job start, retrieval, local
generation, source inspection, edit/history, reopen, and export. Local
generation was schema-valid for `3/3` cases in that receipt; provider calls
were `0` and paid cost was `USD0.00`. A fresh current-candidate run at
`88dc40471cb9078f929c02bb893cfa1e364da841` now re-executes the local-vector
HTTP path for MitraClip, Tendyne, and TriClip with `3/3` succeeded cases,
source inspection, version `1 -> 2` edit/history, reopen, and JSON/Thai/English
exports. Its machine-readable receipt is
[`ptp-local-http-vector-20261103/verification.json`](../audits/ptp-local-http-vector-20261103/verification.json).
This remains engineering/application evidence, not a user study, semantic
patent gold benchmark, paid model-generation comparison, or external business
validation. The exact-head cross-outcome checkpoint binds this application
slice to the same candidate revision as the O1, O2, O3, and O4 receipts and
keeps prior remote artifacts separate from newly executed current-head work
([`ptp-continuation-exact-head-20261103/verification.json`](../audits/ptp-continuation-exact-head-20261103/verification.json)).

The current-head PatEmbed rebind independently reran the retrieval/source/
history/export lifecycle on the same three cases with the server-owned
`datalyes/patembed-base` bundle. It is reported separately from the MiniLM
receipt above and is not a new generation run; local Qwen and paid API
generation remain separate branches.

The current-head multilingual-e5 rebind independently reran the same
retrieval/source/history/export lifecycle on MitraClip, Tendyne, and TriClip
with the server-owned `intfloat/multilingual-e5-base` bundle. All three cases
succeeded, with zero vector errors and version `1 -> 2` history edits. This is
an engineering/provider-binding result recorded in
[`ptp-o2-e5-http-rebind-20261103/verification.json`](../audits/ptp-o2-e5-http-rebind-20261103/verification.json); it is not semantic patent gold,
an exhaustive recall result, an adaptive-superiority result, or a paid API
comparison.

The prior unguided local Qwen attempt was schema-valid for `0/3` cases because
each output emitted `unresolved` as a string rather than the required string
array. A fresh isolated run bound to current candidate
`88dc40471cb9078f929c02bb893cfa1e364da841` used guided JSON decoding with
`lm-format-enforcer` and was schema-valid for `3/3` cases. Per-case generation
latency was `38.552–39.409` seconds (mean `38.960` seconds), with `3,073`
prompt tokens and `1,054` output tokens in total; model load was `3.960`
seconds and total wall time was `120.954` seconds. This receipt establishes
schema-valid generation only. It does not establish semantic correctness,
retrieval quality, citation correctness, or a paid local/API comparison. See
[`ptp-local-qwen-exact-head-20261103/verification.json`](../audits/ptp-local-qwen-exact-head-20261103/verification.json).

The current-head local branch was then run on the frozen rights-cleared
patent-candidate pack, rather than the FDA-only smoke pack. The pack contains
three named devices with 35, 20, and 28 ordered patent candidates and five
evidence rows per case; source payloads, evaluator labels, hidden oracles, and
credentials were excluded from the model-visible input. Guided local Qwen3-8B
generation was schema-valid for `3/3` cases. Prompt/output tokens were
`7,301/1,448` in total, per-case generation latency was `53.448–55.193`
seconds (mean `54.320` seconds), model load was `4.261` seconds, peak GPU
reserved memory was approximately `17.570` GiB, and paid cost/provider calls
were `USD0.00/0`. An independent Windows verifier checked the pack hash, exact
message hashes, output IDs/locators, frozen classification rules, and the
no-paid-call boundary without printing model outputs. This is a reproducible
generation and citation-binding result for the three case studies, not a
semantic accuracy score, retrieval endpoint, independent user validation, or
local/API superiority result. Two pre-model launch failures (missing
`pydantic` in the default interpreter and a pre-created output path) are
retained as failures and did not consume GPU or paid resources. See
[`ptp-local-qwen-patent-run-20261104/README.md`](../audits/ptp-local-qwen-patent-run-20261104/README.md).

An additional deterministic operational evaluation of the same receipt and
frozen pack found exact source/locator binding for 12/12 emitted findings and
classification-contract agreement for 12/12. The model emitted 12 of 15
available evidence rows (80% operational evidence coverage), and all 3/3 cases
reported at least one unresolved item. These are source-integrity and workflow
coverage proxies, not semantic correctness, retrieval accuracy, or a model
comparison. The sanitized receipt is available in the
[operational evaluation audit](../audits/ptp-local-qwen-patent-run-20261104/operational-evaluation.json).

The same current rights-cleared three-case message pack was rechecked against
current public OpenRouter endpoint metadata. The selected exact route was
DeepInfra with observed text prices of `USD0.08/M` input and `USD0.28/M`
completion tokens and support for the required structured-output parameters.
The current-head paired preflight remained `3/3` rights-valid, with zero
provider calls and zero paid cost. A stale Desktop copy was rejected before
output creation or network access and is retained only as workspace-availability
negative evidence. Paid dispatch remains blocked before reservation because the
exact remaining limit and scope of the `.env` dispatch key are still
unresolved. The new E2 journal preserves four known legacy settled calls
totaling `USD0.0001464` and records `UNKNOWN_OWNER_ACCEPTED_CUTOVER`; it is an
execution boundary, not proof of complete historical coverage. The public
endpoint observation and ordinary-key usage metadata are not account-credit or
billing evidence. See
[`ptp-api-parallel-recheck/preflight-current-pack.json`](../audits/ptp-api-parallel-recheck-20261103/preflight-current-pack.json),
[`ptp-api-parallel-recheck/verification.json`](../audits/ptp-api-parallel-recheck-20261103/verification.json),
[`ptp-api-metadata-recheck/metadata-observation-r2.json`](../audits/ptp-api-metadata-recheck-20261103/metadata-observation-r2.json),
and the read-only gate checkpoint
[`ptp-api-gate-recheck/CHECKPOINT.json`](../audits/ptp-api-gate-recheck-20261103/CHECKPOINT.json) and
the R2 continuation checkpoint
[`ptp-api-metadata-recheck/CHECKPOINT_R2.json`](../audits/ptp-api-metadata-recheck-20261103/CHECKPOINT_R2.json).

The latest read-only live-readiness receipt confirms the same boundary on the
current candidate: the ordinary key endpoint exposed usage metadata, but its
exact remaining limit and key scope remained unresolved, so no reservation or
provider attempt was made
([`ptp-api-live-readiness-20261103/verification.json`](../audits/ptp-api-live-readiness-20261103/verification.json)).
The current E2 accounting and credit recheck is recorded in
[`ptp-api-current-credit-recheck-20261103/README.md`](../audits/ptp-api-current-credit-recheck-20261103/README.md).
The subsequent 4 November 2026 E2 recheck used the same canonical journal and
owner `.env` observation path: `/api/v1/key` returned HTTP 200, but the
ordinary non-management key still did not expose current scoped credit or a
remaining key limit. Route pricing was therefore not refreshed for admission,
and no paid attempt was made
([`ptp-resume-e2-current-r2-20261104/verification.json`](../audits/ptp-resume-e2-current-r2-20261104/verification.json)).

After the owner configured the OpenRouter MCP, its read-only `get-credits`
action returned an account-level observation of `total_credits=10` and
`total_usage=0.0001464`. A read-only reconciliation matched that usage to the
four E2 legacy settled receipts, with zero operational attempts and zero
attempt-context rows. The MCP response did not identify the `.env` dispatch
key's remaining limit, key scope, or a response timestamp, so this evidence
updates the account-credit statement but does not satisfy the live admission
gate. The owner-supplied `USD30` first-round MCP cap is retained as a separate
provider-key setting and is not treated as project spend authorization. See
[`ptp-api-openrouter-mcp-recheck-r2-20261104/verification.json`](../audits/ptp-api-openrouter-mcp-recheck-r2-20261104/verification.json)
and [`ptp-api-openrouter-mcp-recheck-r2-20261104/mcp-get-credits.json`](../audits/ptp-api-openrouter-mcp-recheck-r2-20261104/mcp-get-credits.json).

The latest additive rights-cleared rebind projects the current private pack to
an FDA factual canary containing only `pma_number`, `trade_name`, and
`applicant`. Its source-backed transfer review and API payload dry-run pass,
with deterministic message/payload hashes and zero provider calls. This is a
generation-transfer smoke test only; it does not add patent candidates to the
remote payload, establish semantic retrieval quality, or create a paid local/
API comparison. See
[`ptp-e2-rights-rebind-20261103/README.md`](../audits/ptp-e2-rights-rebind-20261103/README.md)
and [`ptp-e2-rights-rebind-20261103/verification.json`](../audits/ptp-e2-rights-rebind-20261103/verification.json).

An earlier O1 engineering receipt is retained separately for historical
comparison only: it was bound to source candidate
`ec3f72147bb8d12531720e5e6dbd8d78914ba25d`, where 28 backend contract tests
and browser HTTP integration passed. It is not combined with the current-head
Qwen or local-vector receipts. See
[`ptp-o1-current-head-20261103/verification.json`](../audits/ptp-o1-current-head-20261103/verification.json).

### 7.6 Figures and machine-readable outputs

The main figures below are bound to the current candidate `88dc40471cb9078f929c02bb893cfa1e364da841`
and the current-head offline verification manifest. They are explicitly
development-only: they do not create a final holdout, semantic relevance gold,
or an equal-total-budget comparison.

The latest current-head engineering/documentation checkpoint, including the
test and link receipts used for this draft, is recorded in [`ptp-current-checkpoint-r3-20261103`](../audits/ptp-current-checkpoint-r3-20261103/README.md). The explicit availability declarations and local bibliography reconciliation are recorded in [`ptp-manuscript-availability-20261103`](../audits/ptp-manuscript-availability-20261103/README.md) and [`ptp-manuscript-reference-reconcile-20261103`](../audits/ptp-manuscript-reference-reconcile-20261103/README.md).

- [Current-head development-only Recall@20 figure](../audits/ptp-current-head-offline-20261103/analysis-current-head-20261103/current_head_recall.svg)
- [Current-head realized retrieval-units figure](../audits/ptp-current-head-offline-20261103/analysis-current-head-20261103/current_head_budget.svg)
- [Current-head frontier table](../audits/ptp-current-head-offline-20261103/analysis-current-head-20261103/current_head_frontier.csv)
- [Current-head figure manifest](../audits/ptp-current-head-offline-20261103/analysis-current-head-20261103/manifest.json)
- [Historical four-company sensitivity audit](../audits/luna-long-run-20261030-company-holdout-sensitivity-20261030/README.md)
- [Historical quality-cost figure](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/quality_cost_development.svg) is retained as a separately bound diagnostic and is not pooled with the current-head rows.
- [Current O1-O4 browser report](../audits/ht-o4-remote-http-generation-browser-20261031/REPORT.md)
- [Current exact-head local-vector three-case receipt](../audits/ptp-local-http-vector-20261103/verification.json)

### 7.7 Benchmark-expansion component diagnostics

The post-freeze continuation acquired and verified five files from the staged manifest, then ran a fresh deterministic CPU lexical baseline on the four official PANORAMA validation/test splits at candidate `88dc40471cb9078f929c02bb893cfa1e364da841`. The runtime did not read `gold_answers`, `silver_answers`, or `negative_answers` when ranking; all rows remained in the denominator and failed-output rate was zero. The same current-head receipt also reran the post-freeze Helmers diagnostic from the verified archive. Source, summary, prediction hashes, timing and command bindings are in [`ptp-panorama-current-head-20261103/verification.json`](../audits/ptp-panorama-current-head-20261103/verification.json); raw predictions remain outside Git.

| Component | Split / pool | Units | Macro hit@1 | Macro hit@8 | Singleton exact top-1 | Wall seconds | Failed-output rate |
|---|---|---:|---:|---:|---:|---:|---:|
| PANORAMA PAR4PC | validation | 3,029 rows | 0.733575 | 1.000000 | 0.681583 | 19.2277 | 0.0 |
| PANORAMA PAR4PC | test | 2,896 rows | 0.715124 | 1.000000 | 0.697702 | 18.0915 | 0.0 |
| PANORAMA PI4PC | validation | 3,937 rows | 0.377699 | 1.000000 | 0.377699 | 7.9967 | 0.0 |
| PANORAMA PI4PC | test | 3,402 rows | 0.401235 | 1.000000 | 0.401235 | 6.4792 | 0.0 |
Helmers is a separate selected-pool diagnostic (10 targets / 450 judged pairs; 258 positive pairs): macro AP = 0.885450 and macro AUC = 0.880012, freshly rerun at the same current head. It has no comparable PANORAMA hit@1/hit@8 endpoint or failed-output rate.

The PANORAMA test rows are final component holdouts under the official application split, but shared candidate IDs across official splits are reported as a diagnostic (149 for PAR4PC and 38 for PI4PC) rather than silently removed. The wall values are machine-side CPU time, not human review time. The Helmers judged pool was selected by the source authors and has no modern official dev/test split. These results therefore provide robustness and component evidence only; they do not estimate adaptive dossier superiority, exhaustive device-patent recall, or independent global relevance.

### 7.8 Numerical claim-to-artifact index

The following ledger binds the numerical claims in Sections 7.1–7.7 to the
dataset or cohort, split, denominator, method/model revision, and evidence
state that produced them. The SHA-256 values are for the cited machine-readable
receipt (or, where the historical package has no JSON receipt in the manuscript
path, the cited audit report). A `historical` row is retained for provenance;
`fresh_current_head` means that the computation was executed against candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`; `rebound` means that an earlier
artifact was revalidated or rebound without a new encode. None of these rows
turns a disclosed link into semantic relevance gold.

| Results block | Dataset / split / denominator | Method or model revision | Evidence state | Bound artifact and SHA-256 |
|---|---|---|---|---|
| 7.1 Offline known-link recovery | Philips-family composite: development `8` devices / `31` patents / `25` disclosed links; Stryker holdout `3` devices / `31` patents / `13` disclosed links; `K=20`; denominator is product-level disclosed links within each split | Offline HT-B0a/B0b/B1/B2/B3 controls; tested code `d45faab3bf0fa08bf2818243249b77920401f6f5` | `historical`; descriptive only | [`luna-long-run-20261030-current-head-b4-r2c-20261030/verification.json`](../audits/luna-long-run-20261030-current-head-b4-r2c-20261030/verification.json), SHA-256 `b40e244be7a1a6609ec9d02530cdadf2805c41f54fca4a171b4e4a72ce66ef45` |
| 7.2 Leave-one-company-out sensitivity | `11` devices / `31` patents / `38` disclosed links; four company-held-out views; `303` explicitly unjudged distractors; candidate and rerank depth `31`, `K=20` | HT-B0a/B0b/B1/B2/B3 offline controls; source head `47aeefcd190ee109f9fb9b9f1ac5c8f37e9bdafe` | `historical`; repeated groups, not independent samples | [`luna-long-run-20261030-company-holdout-sensitivity-20261030/verification.json`](../audits/luna-long-run-20261030-company-holdout-sensitivity-20261030/verification.json), SHA-256 `247dd171b4375da98a2227a0e76d384d1a9f839e7e243d3a81d281c87b47a857` |
| 7.2.1 Paired group uncertainty | Same frozen company/family corpus; development and final-holdout effective groups `3` each against a predeclared threshold of `5`; endpoint is macro Recall@20 delta | Comparisons against HT-B0b; implementation revision `d4f4881c6192a0107fac6702909d6970920e3067` | `historical`; `NOT_ESTIMABLE`, no significance or confidence interval | [`luna-long-run-20261029-m12-group-uncertainty-20261029/verification.json`](../audits/luna-long-run-20261029-m12-group-uncertainty-20261029/verification.json), SHA-256 `30e03c95a0da92ebf5a4bd5a5ec465dafc50b7d943cc0c61995613d718306995` |
| 7.3 Provider-shaped mock control | Same prior transfer diagnostic; denominator is disclosed-link hits in the bound split; simulated debit is not paid cost | HT-B0a/B0b/B1/B2/B3 plus HT-B4-MOCK; no live provider model | `historical`; mock engineering evidence only | [`luna-long-run-20261030-current-head-b4-r2c-20261030/verification.json`](../audits/luna-long-run-20261030-current-head-b4-r2c-20261030/verification.json), SHA-256 `b40e244be7a1a6609ec9d02530cdadf2805c41f54fca4a171b4e4a72ce66ef45` |
| 7.4 Frozen-input current-head frontier | `ht-public-cohort-20261029-frozen-r1`: `3` devices / `41` patents / `61` disclosed links; per-device disclosed-link denominators `21`, `23`, `17`; `K=20`, candidate/rerank depth `41` | HT-B0a/B0b/B1/B2/B3 with `sentence-transformers/all-MiniLM-L6-v2@1110a243fdf4706b3f48f1d95db1a4f5529b4d41` and `cross-encoder/ms-marco-MiniLM-L-6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a` | `fresh_current_head`; realized budgets unequal | [`ptp-current-head-offline-20261103/verification.json`](../audits/ptp-current-head-offline-20261103/verification.json), SHA-256 `ff1c8184f526732fb14c6f6ed386aa43da9e4bbd0ba68a599123e43fe424dab0` |
| 7.4.1 Equalized first-action diagnostic | Same `3`-device / `61`-link development cohort; exactly `3` query calls and `123` rerank pairs; denominator `61` disclosed links | HT-B1, HT-B2-prefix-1, HT-B3-prefix-1; current candidate `88dc4047` | `fresh_current_head`; post-hoc descriptive slice, not final endpoint | [`ptp-current-head-matched-budget-20261103/verification.json`](../audits/ptp-current-head-matched-budget-20261103/verification.json), SHA-256 `e7afc8826a5866e5720ab6d864d55258d61c4db225c14ebf50da15827e3651aa` |
| 7.4.1a Budget-ceiling sensitivity | Same `3`-device / `61`-link cohort; ceilings `3/123`, `5/205`, `6/246`, and `9/369` query/rerank units; larger rows are at-most ceilings | Saved HT-B1/B2/B3 prefixes; current candidate `88dc4047` | `fresh_current_head`; only `3/123` is matched-budget | [`ptp-private-frontier-budget-ceilings-20261104/verification.json`](../audits/ptp-private-frontier-budget-ceilings-20261104/verification.json), SHA-256 `1abfd214588d34e236f5522d4f383bdc0bec202364030bbdad59de4efa703330` |
| 7.4.2 Transformer component diagnostic | DAPFAM citation diagnostic: `45,336` passages / `1,247` queries / `49,869` qrel pairs; denominator is citation-based qrels, not device-patent semantic gold | PatEmbed-base `datalyes/patembed-base@244ba452908a3093be11efb8a44396652317fb14`; multilingual-e5 `intfloat/multilingual-e5-base@d128750597153bb5987e10b1c3493a34e5a4502a` | `rebound`; prior remote encode revalidated, no new encode claimed | [`ht-research-product-20261031/verification.json`](../audits/ht-research-product-20261031/verification.json), SHA-256 `52bbe3602cc8e9d6370eb7fcc546492b9a924e231a9dde51539b07777bb3a7db`; current completion receipt [`ptp-o2-current-head-completion-r16-20261104/verification.json`](../audits/ptp-o2-current-head-completion-r16-20261104/verification.json), SHA-256 `f6644b2d68ea71169ed155ea8298497db96f0b8a95aa65473a5f9fdfcb5d1381` |
| 7.4.3 Fresh transformer diagnostic | Same current-head three-device pack: `41` patent passages / `3` queries / `61` disclosed links; denominator `61`; vectors independently rechecked with max absolute delta `0.0` at tolerance `1e-12` | PatEmbed `datalyes/patembed-base@244ba452908a3093be11efb8a44396652317fb14`; E5 `intfloat/multilingual-e5-base@d128750597153bb5987e10b1c3493a34e5a4502a` | `fresh_current_head`; development retrieval diagnostic only | [`ptp-fresh-gpu-device-diagnostic-20261103/verification.json`](../audits/ptp-fresh-gpu-device-diagnostic-20261103/verification.json), SHA-256 `f4a6c05d6b596efa12b655f1c978e55d8721d7cda449b190cd207a2ef838c3f5` |
| 7.4.4 Medical-subset diagnostic | `96` medical queries / `3,061` screened patents; full denominator `1,920 = 983 + 937`; `10` queries without both-screen positives; saved Oct 31 rankings | BM25, PatEmbed dense/hybrid, and multilingual E5 dense/hybrid; independent arithmetic recheck, no new model call | `historical_recheck`; not a final semantic holdout | [`pepo-strong-followup-20261104/medical-recheck.json`](../audits/pepo-strong-followup-20261104/medical-recheck.json), SHA-256 `48587a9319506716a11af6e872b635a6b9075fe757f17b6121bc1487aee3af05` |
| 7.5 Engineering application slice | Three named real-device cases; local patent pack has `35`, `20`, and `28` ordered candidates plus `5` evidence rows per case; operational denominator is `15` input evidence rows, not semantic labels | `Qwen/Qwen3-8B@b968826d9c46dd6066d109eabc6255188de91218`; guided JSON; no paid provider | `fresh_current_head`; schema/source-binding and workflow proxy only | [`ptp-local-qwen-patent-run-20261104/verification.json`](../audits/ptp-local-qwen-patent-run-20261104/verification.json), SHA-256 `6bf2a84bb66c7c0723b1508379883a45188248eafdd5f03fe2f8ccc9e331efcd`; operational receipt SHA-256 `8e329c714fb38a2aa12662bd76c672e756fac60ed5b5185a560de4b31bfc341b` |
| 7.7 Benchmark-expansion component diagnostics | PANORAMA PAR4PC validation/test `3,029`/`2,896` rows and PI4PC validation/test `3,937`/`3,402` rows; Helmers selected pool `10` targets / `450` judged pairs / `258` positives; denominators are task-specific | Deterministic current-head lexical baseline; Helmers diagnostic script SHA-256 `f9321de7b8806adca8de6ff2b9496dd49d78a05cd11e968f2f048f26ac668838` | `fresh_current_head`; component evidence, not adaptive dossier evaluation | [`ptp-panorama-current-head-20261103/verification.json`](../audits/ptp-panorama-current-head-20261103/verification.json), SHA-256 `6c0f14bbf0aa5b170a431e8dd95080f0e70ba482eacea25230345679d9116e8d` |

The table intentionally keeps disclosed links, retrieved candidates, source
facts, and unjudged pairs as different quantities. The `3/3`, `12/12`, and
`80%` values in Section 7.5 are operational source-binding proxies, not
semantic accuracy. The PANORAMA and Helmers denominators are component-task
denominators and must not be pooled with the device-patent frontier.

## 8. Practical business value as potential

The system provides a plausible operational path for entrepreneurs and investor analysts because it exposes source locators, evidence states, unresolved items, editable history, and exportable dossiers. The evidence currently supports potential value in four measurable dimensions: citation/locator quality, evidence coverage, machine/GPU time, and cost-quality trade-off.

The three-case browser receipt provides a machine-side operational proxy, not a user-productivity result:

| Operational measure | Observed value |
|---|---:|
| Named real-device cases | 3 |
| Local-vector HTTP path latency | 32.888–33.121 seconds per case; mean 33.023 seconds |
| Guided local Qwen generation | schema-valid 3/3; 38.552–39.409 seconds per case; mean 38.960 seconds |
| Guided local Qwen prompt/output tokens | 3,073 / 1,054 |
| Guided local Qwen patent-candidate pack | schema-valid 3/3; 53.448–55.193 seconds per case; mean 54.320 seconds |
| Guided local Qwen patent-candidate prompt/output tokens | 7,301 / 1,448 |
| Source inspection, history 1→2, and JSON export | 3/3 cases |
| Paid provider calls / paid cost | 0 / USD0.00 |
| Local output exact source/locator binding | 12/12 findings |
| Local output classification-contract match | 12/12 findings |
| Local output evidence coverage | 12/15 input evidence rows; 80% |
| Local output unresolved-item visibility | 3/3 cases |

This operational table is bound to the current-candidate local Qwen receipt
[`ptp-local-qwen-patent-run-20261104/verification.json`](../audits/ptp-local-qwen-patent-run-20261104/verification.json), SHA-256
`6bf2a84bb66c7c0723b1508379883a45188248eafdd5f03fe2f8ccc9e331efcd`, and its
deterministic operational evaluation, SHA-256
`8e329c714fb38a2aa12662bd76c672e756fac60ed5b5185a560de4b31bfc341b`. The
receipt records model revision `b968826d9c46dd6066d109eabc6255188de91218`,
prompt/output tokens `7,301/1,448`, mean latency `54.320437` seconds, zero
provider calls, and zero paid cost. These are machine-side and source-binding
measurements; the table contains no observed human-time, customer, revenue,
ROI, or willingness-to-pay result.

These measurements exclude human time, support time, and external-user behavior. They should be used for capacity and cost scenarios only, not as a service-level promise or ROI evidence.

The illustrative cost rows below use the earlier guided local-Qwen runtime
(`38.960` seconds per case) that is bound to the business-value scenario
package. The separate current patent-candidate run reports `54.320437`
seconds mean generation latency, `7,301` prompt tokens, and `1,448` output
tokens over the same three named cases. Because the runs use different
runtime/configuration envelopes, the current latency is reported as a separate
operational result and is not substituted into or pooled with the older unit-
cost scenario.

For a transparent sensitivity analysis, the observed mean machine time is
`71.983` seconds per case (`0.0199952778` machine-hours), combining the local
vector path and guided local generation. Human review time and an infrastructure
rate were not measured, so the following unit-cost rows are illustrative
scenarios calculated as `human_hours * labor_rate + machine_hours * GPU_rate`:

| Scenario | Human hours | Labor rate (USD/h) | GPU rate (USD/h) | Illustrative unit cost (USD) |
|---|---:|---:|---:|---:|
| Lower | 0.25 | 50 | 1 | 12.52 |
| Central | 0.50 | 100 | 3 | 50.06 |
| Upper | 1.00 | 200 | 3 | 200.06 |

These rows are assumptions for sensitivity analysis, not observed human time,
production cost, customer value, revenue, or ROI. They exclude support,
storage, rework, and paid API charges, which were not observed in this round.
The complete inputs, formula, and source hashes are in the [business-value
scenario package](../audits/ptp-business-value-scenario-20261103/README.md).

The repository does not contain independent user validation, measured willingness-to-pay, a purchase, revenue, or ROI. If the owner runs the workflow personally, the result must be labeled `developer_self_evaluation` and interpreted as formative evidence with builder familiarity bias. Any labor-rate or dossier-volume scenario must remain a sensitivity analysis, not a commercial outcome.

## 9. Ethics, data rights, and responsible use

This current round is a solo computational study. No external participants were enrolled, no consent was collected, and no participant data are included. The repository therefore does not claim human-subject approval, exemption, usability validation, or customer validation. A future human-study consent template is stored separately and is inactive.

Data rights are handled per source and purpose. Restricted source text, private journals, credentials, and private payloads remain outside Git. The workflow must not be used as a clinical, regulatory, legal, FTO, patent-validity, or investment decision without qualified review.

## 10. Reproducibility and availability

The code, schemas, authored fixtures, audit manifests, protocol, model/configuration identifiers, and reproduction commands are stored in the repository. Private artifacts contain the exact prompts/messages, input/output hashes, errors, retries, latency, token/cost receipts, source hashes, and ledger state; they are not published when rights or privacy do not permit it. The public release should provide IDs, URLs, hashes, and acquisition instructions instead of restricted payloads.

The existing private PatEmbed and multilingual-e5 corpus/query bundles were
revalidated against the frozen three-case runtime manifest on the current
candidate. All four bundles passed shard, shape, finite-float, input-binding,
and cross-encoder ordering checks; this is artifact-integrity evidence only,
not a new encode or retrieval evaluation. The current private model root also
contains the allowlist-acquired pinned PatEmbed and multilingual-e5 snapshots,
which pass layout and file-hash binding. No new remote transfer or encode is
claimed. See [`ptp-vector-artifact-revalidation-20261103/verification.json`](../audits/ptp-vector-artifact-revalidation-20261103/verification.json)
and [`ptp-o2-model-snapshot-20261103/verification.json`](../audits/ptp-o2-model-snapshot-20261103/verification.json).

The current-head PatEmbed HTTP provider-binding receipt is recorded separately
in [`ptp-o2-patembed-http-rebind-20261103/verification.json`](../audits/ptp-o2-patembed-http-rebind-20261103/verification.json).
It proves use of the verified PatEmbed vectors in the dossier path for the
three named engineering cases; multilingual-e5 remains an integrity-verified
alternative and was not silently pooled into that run.

The benchmark-expansion reproducibility addendum and machine-readable receipts are in [`SUPPLEMENTAL_DATA.md`](SUPPLEMENTAL_DATA.md) and [`benchmark-expansion-20261101`](../audits/benchmark-expansion-20261101/README.md). They bind the five acquired files, freeze rules, component metrics, and cleanup limitation to the continuation candidate.

An additional manifest extension was inspected without changing the primary experiment: a 30-row PatSnap claim-charting file, two PatentsView assignee benchmark CSVs, and a 1,374-row AffRoDB JSONL file passed the recorded byte/hash/schema checks. PatSnap and AffRoDB remain unscored diagnostics; PatentsView remains excluded because standalone data rights were not established, and AffRoDB lacks the pinned ROR v1.40 registry needed for a valid linkage evaluation. These assets therefore do not add evidence for adaptive dossier superiority and are retained only as rights-aware reproducibility inventory.

The historical component scores remain bound to pre-run candidate `cd7e5d364d529a001fc51f78c217c10d7d9c8945` and are retained for provenance only. A fresh current-head revalidation was run against `88dc40471cb9078f929c02bb893cfa1e364da841` using the same frozen protocol and verified payloads; its summary/prediction hashes and failure denominator are recorded in [`ptp-panorama-current-head-20261103/verification.json`](../audits/ptp-panorama-current-head-20261103/verification.json) and [`ptp-panorama-current-head-20261103/CHECKPOINT.json`](../audits/ptp-panorama-current-head-20261103/CHECKPOINT.json). Results from different candidates or different protocol manifests are not combined into one PASS claim. The older benchmark-expansion receipts remain available as historical records.

### 10.1 Reproduction appendix for the numerical ledger

All current-head claims in this manuscript are bound to the intentionally dirty
worktree `codex/patent-to-pilot-long-run-20261103` at candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. The working-tree state is part of
the receipt; a clean commit or release tag is not being implied. Private corpus,
vector, model, provider-journal, and raw-output paths are represented by
sanitized placeholders in the commands below and remain outside Git.

For the current offline frontier, the recorded commands are:

```text
rtk proxy python -B -m pytest -q tests/test_healthtech_real_baselines.py
rtk proxy python -B scripts/healthtech/run_real_baselines.py --runtime <frozen runtime> --references <frozen references> --groups <frozen groups> --model-root <existing MiniLM bundle> --output <private>/baselines/run-001 --code-commit 88dc40471cb9078f929c02bb893cfa1e364da841 --protocol-hash a87acaa448f97eabccae0f1fecc5378720ecf1178869336f68b42174eb828b0f --cohort-manifest-hash b92b50716599ad6ea3cdeb5b6a692990a52ae8dd113bfc0bb5cad2cdd2148715 --candidate-depth 41 --rerank-depth 41 --k 20
rtk proxy python -B scripts/healthtech/run_bounded_controller.py --runtime <frozen runtime> --references <frozen references> --groups <frozen groups> --model-root <existing MiniLM bundle> --output <private>/b4-offline/run-001 --code-commit 88dc40471cb9078f929c02bb893cfa1e364da841 --protocol-hash a87acaa448f97eabccae0f1fecc5378720ecf1178869336f68b42174eb828b0f --cohort-manifest-hash b92b50716599ad6ea3cdeb5b6a692990a52ae8dd113bfc0bb5cad2cdd2148715 --candidate-depth 41 --rerank-depth 41 --max-steps 3
```

The first command is a regression check for failure accounting and returned
`4 passed`; the second returned five methods over three devices and `61`
reference pairs with zero provider calls; the third returned three devices with
zero failed devices and zero provider calls. The corresponding receipt is
[`ptp-current-head-offline-20261103/verification.json`](../audits/ptp-current-head-offline-20261103/verification.json).

For the transformer and component diagnostics, reproduction requires the
rights-cleared input manifests and the permitted local or `dr-train` model
bundles. The exact source, model, vector, prediction, summary, and evaluator
hashes are recorded in the bound receipts rather than inferred from the
manuscript. The fresh transformer receipt records the approved GPU UUID,
concurrency `1`, `8` CPU threads, zero evaluator-label transfer, and zero paid
calls. The PANORAMA receipt records source, summary, prediction, failed-row,
and focused/full-test hashes for all four official splits. These receipts are
reproducibility evidence; they do not grant permission to download restricted
data or rerun a GPU job.

For the local generation application slice, the frozen pack hash is
`918f615210546b65111cbc683181dc43886ace2267f16c19d62c31175ea6607b`, the
private generation receipt hash is
`7072197565f26a0b88ae80aeddd08eff3c933f69f6632714fcc296a6713dc6fd`, and the
independent verifier returned `PASS_3_OF_3` for exact messages, source
ID/locator/classification validation, schema validation, and the zero-paid-call
boundary. The two pre-model-launch failures remain in the receipt; neither
started GPU computation, provider calls, or ledger mutation. This is a
source-binding and workflow reproducibility result, not semantic validation.

The final numerical reproduction rule is: preserve the stated cohort, split,
grouping, denominator, model revision, failure/retry policy, and evidence state
before recomputing. Do not pool historical, rebound, and fresh rows; do not
replace unjudged pairs with negatives; do not infer human time, ROI, revenue,
or willingness-to-pay from machine receipts; and do not use a schema pass or a
source binding as a substitute for an independent semantic gold judgment.

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

## 12. Discussion

The current development evidence does not support a claim that the adaptive
policy is better than the fixed controls. On the frozen current-head cohort,
HT-B0b has the highest observed macro known-link Recall@20 (`0.662242`), while
HT-B2 reaches `0.568912` with a larger realized query/rerank budget and offline
HT-B4 reaches `0.498802`. The post-hoc equalized first-action slice ties HT-B1,
HT-B2-prefix-1, and HT-B3-prefix-1 at `0.498802`; it is a comparability
diagnostic, not a confirmatory test. These values and resource totals are bound
to the current-head offline receipt and matched-budget receipt, and are not
pooled with older candidates
([offline receipt](../audits/ptp-current-head-offline-20261103/verification.json),
[matched-budget receipt](../audits/ptp-current-head-matched-budget-20261103/verification.json)).

The defensible contribution is therefore methodological and operational. The
workflow keeps `disclosed_link`, `retrieved_candidate`, and `unjudged` separate;
records source locators and unresolved evidence; preserves edit/history/export
state; and reports realized query, rerank, machine-time, failure, and unknown
resources. Those controls make a future adaptive comparison auditable, but
they do not turn documented links into semantic gold or make a three-case
application slice a powered research sample.

For practice, the current dossier path shows operational potential rather than
measured commercial value. The observed machine-side latency and token/cost
records can support capacity and sensitivity scenarios, but human review time,
independent user performance, adoption, purchase, revenue, willingness-to-pay,
and ROI were not measured
([business-value scenario](../audits/ptp-business-value-scenario-20261103/verification.json)).
The local/API generation comparison also remains a configuration comparison:
the API branch has not been dispatched because the canonical R1 journal and
current scoped credit evidence are unresolved.

The next scientifically discriminating study should freeze a rights-cleared
semantic judgment source, independent family/company groups, a main-task final
holdout, and equal realized total budgets before selection. It should then
compare fixed, multi-query, simple heuristic, and adaptive policies with the
same evidence access and retain all failed and unjudged cases. Until that
study is run, the appropriate conclusion is that the system and protocol are
reproducible and reviewable, while the adaptive quality advantage remains an
open research question.

## 13. Conclusion

The current evidence supports a reproducible patent-information workflow and a disciplined computational study design for adaptive evidence acquisition under incomplete judgments. The four-company sensitivity audit and the new PANORAMA/Helmers component results show that the pipeline can be evaluated against multiple task-shaped signals, while also exposing the limits of transferring option-selection or selected-pool relevance metrics into device-patent dossier claims. The strongest defensible contribution is the combination of provenance-aware state separation, explicit per-call and realized-resource accounting, explicit unknowns, reproducible dossier operations, and honest quality-cost reporting. A stronger scientific conclusion requires a final adaptive dossier study with equalized total budgets, independent groups, and an appropriate semantic judgment source or benchmark. A stronger business conclusion requires future authorized user or customer evidence.

## Declarations

**Funding:** No external funding is recorded for this computational study. Confirm before submission.

**Conflicts of interest:** No conflict is declared in the current draft. The owner must confirm before submission.

**Author contributions:** The owner must confirm names and contribution statements before submission. Suggested structure: conceptualization and supervision by the owner; software, data curation, methodology implementation, investigation, and draft preparation by the project team; review and approval by the owner.

**AI-use disclosure:** AI-assisted coding and drafting were used under owner direction. All claims, source links, experiment boundaries, and final submission materials require owner review. No AI system is treated as an independent scientific evaluator or source of gold labels.

**Ethics statement:** No human participants or participant data were used in the current round. Future human-study materials are inactive templates.

**Data availability:** The reproducible study package provides the frozen protocol, source identifiers, version and hash manifests, authored fixtures, sanitized aggregate tables, and audit receipts needed to inspect the reported computations where redistribution is permitted. Restricted raw source pages, evaluator-only judgments, private provider journals, credentials, and other non-redistributable payloads are intentionally excluded from the repository. Any released data bundle must retain the source-specific terms and provenance recorded in the corresponding audit manifest; the owner must confirm the final public or archival deposit before submission.

**Code availability:** The implementation, tests, protocol scripts, and report-generation utilities are maintained in the Patent-to-Pilot repository and are bound to the candidate revision and dirty-worktree state recorded in the current audit checkpoint. The final submission package is not yet archived under a DOI or public release tag. Before submission, the owner must pin the final reviewed revision and provide the journal-appropriate repository or archival link; private artifacts and credentials must remain outside that release.

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
