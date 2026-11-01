# Evaluating Adaptive Evidence Acquisition for Medical-Device Patent Screening under Incomplete Judgments

Status: `DRAFT_FOR_OWNER_REVIEW / SOLO_COMPUTATIONAL_STUDY / NOT_SUBMITTED`

Target venue: *World Patent Information* (fit and author requirements must be rechecked by the owner immediately before submission).

## Abstract

Patent-information workflows for medical devices must connect regulatory or product evidence to patent records without silently treating a retrieved candidate as a disclosed relationship. This study evaluates whether adaptive evidence acquisition improves the auditability and resource efficiency of device-patent screening when documented links are incomplete. We compare metadata, lexical, strong fixed hybrid, fixed multi-query, and simple adaptive policies under shared evidence access, candidate universes, cutoffs, group splits, and budget units. The primary endpoint is macro known-link Recall@K over source-backed documented relationships; unlisted pairs remain unjudged rather than negative. A separate dossier application uses at least three permitted real device cases and tests source inspection, editing, history, and export. The current repository contains descriptive offline results and a verified local engineering path, but not a rights-cleared semantic relevance gold set, a powered confirmatory comparison, a live provider comparison, or independent user validation. In the frozen descriptive audit, HT-B2 has the highest final-holdout macro Recall@20 (0.8857), while HT-B1 and HT-B4-MOCK each record 0.8381; the observed result is not a superiority claim because the cohort is small, group uncertainty is limited, and the reference relations are product-level disclosures. The practical contribution is a reproducible patent-information protocol and evidence-dossier workflow that makes provenance, unknowns, costs, and failure modes inspectable.

Keywords: patent information; medical devices; evidence acquisition; adaptive retrieval; incomplete judgments; provenance; cost-quality trade-off; reproducible research

## 1. Introduction

Medical-device screening sits between regulatory evidence, product descriptions, patent records, and an eventual business or research decision. The evidence is heterogeneous and often incomplete: an official disclosure can support a device-patent association, while a retrieval system can produce only a candidate that still requires review. Collapsing these states creates a practical and scientific error. It can make a candidate look like a confirmed relationship, hide missing evidence, and overstate recall.

This paper studies a narrower question: when the evidence acquisition budget is fixed, does an adaptive policy produce a more auditable dossier or a better quality-cost trade-off than strong fixed baselines and a simple heuristic? The study is deliberately patent-information centered. It does not claim clinical suitability, freedom to operate, patent validity, regulatory approval probability, investment merit, or market demand.

The contributions are:

1. A provenance-bound evaluation contract that preserves raw and canonical identifiers, source revisions, rights policies, exact locators, and the distinction between disclosed links, retrieved candidates, and unjudged pairs.
2. A matched comparison of fixed and adaptive evidence-acquisition policies with predeclared grouping, leakage controls, resource accounting, and failure retention.
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

All methods receive the same frozen corpus, eligible inputs, source cutoff, candidate universe, K, permitted metadata, output schema, failure rules, and declared budget units. If a method uses an additional representation, the matched fixed condition must report and account for that representation as well.

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

### 7.2 Provider-shaped mock control

| Method | Final holdout macro Recall@20 |
|---|---:|
| HT-B0a | 0.5429 |
| HT-B0b | 0.8095 |
| HT-B1 | 0.8381 |
| HT-B2 | 0.8857 |
| HT-B3 | 0.8381 |
| HT-B4-MOCK | 0.8381 |

HT-B4-MOCK exercised action schemas and accounting paths. It was not live-provider evidence and its simulated debit is not paid cost.

### 7.3 Engineering application slice

The current O1-O4 engineering receipts cover three named real-device cases through browser/HTTP job start, retrieval, local generation, source inspection, edit/history, reopen, and export. Local generation was schema-valid for `3/3` cases in the recorded receipt; provider calls were `0` and paid cost was `USD0.00`. This is engineering and application evidence, not a user study or a three-case scientific benchmark.

### 7.4 Figures and machine-readable outputs

The current frozen descriptive audit provides the following actual figure and table inputs:

- [Development quality-cost frontier](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/quality_cost_development.svg)
- [Holdout quality-cost frontier](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/quality_cost_holdout.svg)
- [Recall comparison](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/recall_comparison.svg)
- [Quality-cost table](../audits/luna-long-run-20261030-current-head-baseline-b4-20261030/analysis/quality_cost_frontier.csv)
- [Current O1-O4 browser report](../audits/ht-o4-remote-http-generation-browser-20261031/REPORT.md)

## 8. Practical business value as potential

The system provides a plausible operational path for entrepreneurs and investor analysts because it exposes source locators, evidence states, unresolved items, editable history, and exportable dossiers. The evidence currently supports potential value in four measurable dimensions: citation/locator quality, evidence coverage, machine/GPU time, and cost-quality trade-off.

The repository does not contain independent user validation, measured willingness-to-pay, a purchase, revenue, or ROI. If the owner runs the workflow personally, the result must be labeled `developer_self_evaluation` and interpreted as formative evidence with builder familiarity bias. Any labor-rate or dossier-volume scenario must remain a sensitivity analysis, not a commercial outcome.

## 9. Ethics, data rights, and responsible use

This current round is a solo computational study. No external participants were enrolled, no consent was collected, and no participant data are included. The repository therefore does not claim human-subject approval, exemption, usability validation, or customer validation. A future human-study consent template is stored separately and is inactive.

Data rights are handled per source and purpose. Restricted source text, private journals, credentials, and private payloads remain outside Git. The workflow must not be used as a clinical, regulatory, legal, FTO, patent-validity, or investment decision without qualified review.

## 10. Reproducibility and availability

The code, schemas, authored fixtures, audit manifests, protocol, model/configuration identifiers, and reproduction commands are stored in the repository. Private artifacts contain the exact prompts/messages, input/output hashes, errors, retries, latency, token/cost receipts, source hashes, and ledger state; they are not published when rights or privacy do not permit it. The public release should provide IDs, URLs, hashes, and acquisition instructions instead of restricted payloads.

The exact current continuation candidate, test commands, and limitations must be recorded in the final audit checkpoint. Results from different candidates or different protocol manifests must not be combined into one PASS claim.

## 11. Limitations

1. Documented product-level links are not semantic patent relevance gold; unjudged pairs are not negatives.
2. The current effective group counts and holdout size are too small for stable generalization or confirmatory significance claims.
3. The three real-device cases demonstrate the workflow but do not replace a benchmark, user study, or market validation.
4. Local `Qwen/Qwen3-8B` and API `qwen/qwen3-32b` differ in size and provider, so any comparison is configuration-level.
5. Live paid API evidence remains conditional on the canonical ledger, current credit, route, rights, and reconciliation gates.
6. DAPFAM is diagnostic and is not a device-patent gold set.
7. No independent user validation, willingness-to-pay, revenue, ROI, clinical, legal, FTO, patent-validity, or investment conclusion is supported.

## 12. Conclusion

The current evidence supports a reproducible patent-information workflow and a disciplined computational study design for adaptive evidence acquisition under incomplete judgments. The frozen descriptive comparison shows that a fixed multi-query schedule can outperform the simple adaptive conditions in the available holdout artifact, which is a useful negative or boundary finding rather than a failure of the project. The strongest defensible contribution is the combination of provenance-aware state separation, matched resource accounting, explicit unknowns, reproducible dossier operations, and honest quality-cost reporting. A stronger scientific conclusion requires a rights-cleared semantic judgment source or suitable benchmark, more independent groups, and a fully rerun final protocol. A stronger business conclusion requires future authorized user or customer evidence.

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
6. Jeong, S., Baek, J., Cho, S., Hwang, S. J., and Park, J. (2024). Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity. NAACL-HLT 2024.
7. Su, W., Tang, Y., Ai, Q., Liu, Y., and others. (2024). DRAGIN: Dynamic Retrieval Augmented Generation based on the Information Needs of Large Language Models. ACL 2024.
8. Wu, M., Yang, H., Ben-Porat, O., and Ziser, Y. (2026). When Knowledge Is Not Free: Cost-Aware Evidence Selection in Retrieval-Augmented Generation. Findings of EMNLP 2026.
9. Poce, S., and Cerro, G. (2026). A survey on automated and AI-based tools for patent retrieval with a special focus on the life sciences domain. World Patent Information. doi:10.1016/j.wpi.2026.102439.

## Author-review checklist

- Confirm author names, affiliations, funding, conflicts, and contribution statement.
- Recheck the official World Patent Information aims and scope and Guide for Authors immediately before submission.
- Rebind every table and figure to the final candidate revision and one protocol manifest.
- Confirm whether the final paper includes only published/permitted aggregate outputs and source identifiers.
- Keep human pilot, customer validation, revenue, willingness-to-pay, and ROI as future work unless new evidence is added.
