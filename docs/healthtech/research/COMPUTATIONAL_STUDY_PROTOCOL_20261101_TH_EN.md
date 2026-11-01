# Reproducible computational study protocol / ระเบียบวิธีการทดลองเชิงคำนวณ

Status: `PROTOCOL_FROZEN_FOR_CURRENT_ROUND / EXECUTION_PARTIAL`

Version date: 2026-11-01 (Asia/Bangkok)

This protocol replaces the assumption that a human pilot is required for the current round. It defines a solo, reproducible computational study with real permitted case studies. It does not authorize paid API use, new data acquisition, external outreach, or human-subject research.

## 1. Research question

Does adaptive evidence acquisition produce a more auditable dossier at the same evidence access and budget than a strong fixed-budget retrieval schedule, a fixed multi-query schedule, and a simple adaptive heuristic for medical-device patent screening under incomplete judgments?

The comparison is about quality and resource trade-offs in a patent-information workflow. It is not a clinical, legal, FTO, patent-validity, regulatory, investment, or revenue study.

## 2. Estimand and hypotheses

Primary estimand: macro known-link Recall@K over source-backed documented device-patent associations in an eligible, frozen evaluation cohort, with group-level aggregation over non-overlapping patent-family or company groups.

Primary null: the adaptive policy does not improve the predeclared quality-at-budget endpoint over the strongest fixed baseline.

Secondary estimands:

- citation support and locator resolution rate;
- evidence coverage of required dossier fields;
- unresolved/unknown rate and failure rate;
- realized query, rerank, embedding, token, wall-clock, GPU, and paid costs;
- quality-cost frontier and cost per dossier meeting the declared evidence threshold;
- generation schema validity and citation completeness on identical frozen evidence.

No endpoint is selected after viewing the final results. A negative or inconclusive result is valid.

## 3. Data and case boundaries

- Real application slice: at least three permitted named medical-device cases, currently MitraClip, Tendyne, and TriClip for the O1-O4 workflow.
- Comparative retrieval study: use the frozen cohort and group definitions recorded in the current HealthTech audits. The three application cases are not treated as the full benchmark.
- Preserve raw IDs, canonical IDs, source revision/hash, jurisdiction, date, exact locator, rights policy, and provenance for every source and relation.
- `disclosed_link` means an independently source-backed product/device-to-patent relationship. `retrieved_candidate` is a system output. `unjudged` is neither positive nor negative.
- Legacy Stryker, DAPFAM, product-marking, and other diagnostic artifacts must not be silently substituted for the current cohort or treated as semantic patent gold.

## 4. Methods and matched conditions

The minimum policy set is:

| ID | Method | Role |
|---|---|---|
| HT-B0a | company/metadata control | measures metadata shortcut value |
| HT-B0b | lexical retrieval | transparent low-cost baseline |
| HT-B1 | strong fixed hybrid | strongest fixed comparator |
| HT-B2 | fixed multi-query schedule | separates query breadth from adaptation |
| HT-B3 | simple adaptive heuristic | tests whether complex control adds value over a rule |
| HT-B4 | bounded controller | optional proposed adaptive condition; live status remains gated |

All policy comparisons use the same frozen corpus, eligible queries, source cutoffs, permitted metadata, candidate universe, reranker configuration, K, output schema, retry rules, and budget units unless the protocol explicitly labels a factor as an ablation.

PatEmbed and multilingual-e5 are used according to the recorded model revisions and embedding protocol. DAPFAM is a diagnostic only; it is not a device-patent semantic gold set.

Generation comparison is a separate analysis: local `Qwen/Qwen3-8B` and API `qwen/qwen3-32b` must receive the same exact messages, evidence order, schema, and rights-cleared payload. The model-size/provider difference is a deployment/configuration confound and must not be presented as a pure causal model-size effect.

## 5. Splits and leakage controls

- Freeze the eligible query set, candidate universe, source cutoff, group mapping, action set, evaluator, primary endpoint, K, budget, and failure/retry rules before final evaluation.
- Keep development and final holdout groups disjoint at the patent-family/company level where the source mapping supports it.
- Do not tune query templates, controller rules, thresholds, stopping rules, or reporting choices on the final holdout.
- Runtime inputs exclude evaluator labels, gold-derived queries, hidden oracles, and post-hoc labels.
- Evaluator-only data may be used only after runtime artifacts are frozen and only by the evaluator layer.
- Repeated cases from the same device, patent family, company, or source snapshot are not independent samples.

If a complete expert semantic gold set is unavailable, report the result as recovery of documented known links and source integrity, not semantic relevance. Do not use an agent judge, similarity score, or LLM critique as a replacement for gold without an explicit validation study and limitation statement.

## 6. Analysis rules

Report macro and micro values, denominators, group counts, missing/failed queries, unjudged counts, retries, and all realized resources. Use group-level uncertainty or mark `NOT_ESTIMABLE` when the effective group count is too small.

Include ablations for company/entity signals, action order, query breadth, stopping behavior, and embedding choice only when the corresponding artifact and budget are available. Preserve failed attempts and blocked branches in the report.

Do not pool O1/O2/O4 engineering receipts with scientific comparison results. Bind each result table to one candidate revision and one audit manifest.

## 7. Business-value interpretation

Business value is assessed as practical potential, not validated demand. The current round may report:

- citation support and locator quality;
- evidence coverage and unresolved-item visibility;
- machine/GPU time, latency, token use, and paid cost;
- cost per dossier meeting the declared evidence threshold;
- developer self-evaluation only when explicitly labeled and kept separate from external-user evidence;
- scenario/sensitivity analysis using stated labor and dossier-volume assumptions, clearly marked as hypothetical.

The current round must not claim independent user validation, customer adoption, willingness-to-pay, revenue, or ROI.

## 8. Reproducibility and artifact contract

For every attempt, retain a private or rights-cleared manifest containing exact prompts/messages, configurations, model revisions, input/output hashes, source hashes, output or error, retries, latency, token counts, cost, and ledger/authorization state. Do not commit keys, restricted payloads, raw private journals, or unlicensed source text.

The published package should contain code, schemas, authored fixtures, source IDs/URLs/hashes, aggregate tables, figure inputs, and reproduction commands. Private artifacts remain outside Git with a sanitized provenance receipt.

## 9. Current status and stopping rule

The protocol is ready for offline execution and manuscript preparation. Engineering evidence may be complete for a branch while scientific comparison remains `PARTIAL` or `NOT_ESTIMABLE`. Paid API execution remains subject to the existing canonical ledger, current credit, route, rights, and reconciliation gates; this protocol does not reset any authorization or time window.

Stop a branch when its declared budget, rights, data, or runtime gate is exhausted. Continue independent offline work and report the blocked branch separately.
