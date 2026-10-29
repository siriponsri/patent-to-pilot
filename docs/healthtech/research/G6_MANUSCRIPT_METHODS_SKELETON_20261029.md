# G6 manuscript and reproducibility skeleton

Status: `PREPARED METHODS/RESULTS SKELETON; DESCRIPTIVE DEVELOPMENT EVIDENCE ONLY`.

Working title: *Evaluating Adaptive Evidence Acquisition for Medical-Device Patent Screening under Incomplete Judgments*.

## Abstract boundary

This manuscript will report a bounded retrieval/evidence-acquisition study over named public medical-device cases. The current package supports a reproducible offline baseline comparison and a provider-shaped mock seam. It does not yet support a claim of adaptive superiority, semantic relevance gold, live-provider behavior, clinical suitability, FTO, patent validity, investment merit, or publication readiness.

## Research question and estimand

Primary question: under a frozen device-patent candidate universe and incomplete documented links, how do fixed company/lexical/hybrid/multi-query controls and a bounded adaptive policy differ in known-link recovery and resource use?

Current endpoint: descriptive macro known-link recall at `K=20` over product-level disclosed relationships. Unlisted query-patent pairs remain `UNJUDGED` and are not negatives. Family-aware rows are evaluator-side sensitivity diagnostics, not legal family adjudication or semantic relevance labels.

## Data and protocol

- Development view: 5 devices/queries, 24 patents, 3 family-aware groups.
- Final holdout view: 3 untouched Stryker queries, the same 24-patent universe, 3 family-aware groups.
- Composite context: 8 devices, 24 patents, 31 product-level disclosed pairs, 161 unjudged distractors, and 6 full-cohort family groups.
- Protocol hash: `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`.
- Cohort manifest hash: `1b42b7c4a52b697d9c5c4f7db4f9236b7d5d239d83584863a6ba844591adef75`.
- Report receipt: [`luna-long-run-20261029-m7-report-20261029`](../audits/luna-long-run-20261029-m7-report-20261029/REPORT.md).
- Descriptive analysis and figures: [`luna-long-run-20261029-m8-analysis-20261029-r2`](../audits/luna-long-run-20261029-m8-analysis-20261029-r2/ANALYSIS.md).
- HT-B4 mock holdout comparison: [`luna-long-run-20261029-m10-b4-holdout-20261029`](../audits/luna-long-run-20261029-m10-b4-holdout-20261029/COMPARISON.md).

The final holdout was not used for policy tuning. No semantic reviewer labels were available in this package. The Bridge branch remains `BLOCKED_LOCAL`.

## Actual baseline table

| Split | HT-B0a | HT-B0b | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|---:|---:|
| Development macro known-link R@20 | 0.9381 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Final holdout macro known-link R@20 | 0.8190 | 0.9524 | 0.9333 | 0.9333 | 0.8857 |

The development rows used 5 queries; the holdout rows used 3 queries. Realized query calls were method-dependent because HT-B2 and HT-B3 use multiple queries/actions. Full resource and hash detail is in `summary_tables.json` and `frontier_table.csv` in the linked report audit.

## HT-B4 provider-shaped mock holdout comparison

The fixed-policy HT-B4 provider-shaped mock was run once on the untouched final holdout after the control outputs were frozen. It completed 3 devices, 24 patents, 8 provider-shaped calls, 120 rerank pairs, macro known-link R@20 of `0.8857`, micro known-link R@20 of `0.8462`, simulated debit of USD `0.0008`, paid cost of USD `0.00`, zero unknown/pending billing items, and no ledger breach.

| Method | Final holdout macro known-link R@20 | B4 mock minus control |
|---|---:|---:|
| HT-B0a | 0.8190 | +0.0667 |
| HT-B0b | 0.9524 | -0.0667 |
| HT-B1 | 0.9333 | -0.0476 |
| HT-B2 | 0.9333 | -0.0476 |
| HT-B3 | 0.8857 | 0.0000 |
| HT-B4-MOCK | 0.8857 | — |

In this descriptive holdout comparison, HT-B4-MOCK matches HT-B3 and is below HT-B0b, HT-B1, and HT-B2. Provider-shaped calls exercise the action schema and accounting path only; they are not live-provider evidence. The result remains `DESCRIPTIVE_NOT_ESTIMABLE` because the cohort uses product-level disclosures, unjudged pairs, and a small company-level transfer check rather than rights-cleared semantic relevance gold.

## Reproducible analysis and figures

The M8 analysis package computes the observed Pareto frontier from macro known-link recall and realized wall time, adds K=20 group-level min/max/range, and reports holdout-minus-development deltas. HT-B0a and HT-B0b are on the observed frontier in both frozen views; HT-B1, HT-B2, and HT-B3 are dominated on these descriptive coordinates. This is not a superiority claim because the labels are product-level disclosures, the pair universe is incomplete, and effective group uncertainty remains `NOT_ESTIMABLE`.

- Analysis table: [`quality_cost_frontier.csv`](../audits/luna-long-run-20261029-m8-analysis-20261029-r2/quality_cost_frontier.csv)
- Development quality-resource plot: [`quality_cost_development.svg`](../audits/luna-long-run-20261029-m8-analysis-20261029-r2/quality_cost_development.svg)
- Holdout quality-resource plot: [`quality_cost_holdout.svg`](../audits/luna-long-run-20261029-m8-analysis-20261029-r2/quality_cost_holdout.svg)
- Development/holdout recall comparison: [`recall_comparison.svg`](../audits/luna-long-run-20261029-m8-analysis-20261029-r2/recall_comparison.svg)

## Paired group uncertainty diagnostic

The M12 diagnostic aligns methods by frozen `group_id` against `HT-B0b` at `K=20` and reports descriptive mean deltas, population standard deviation, and min/max deltas. The predeclared minimum effective group threshold is `5`; both the development and final-holdout views contain `3` effective family-aware groups, so every paired comparison remains `NOT_ESTIMABLE`.

| Split | HT-B0a minus HT-B0b | HT-B1 minus HT-B0b | HT-B2 minus HT-B0b | HT-B3 minus HT-B0b |
|---|---:|---:|---:|---:|
| Development mean delta | -0.0516 | 0.0000 | 0.0000 | 0.0000 |
| Final holdout mean delta | -0.1333 | -0.0190 | -0.0190 | -0.0667 |

These values are descriptive diagnostics only. They do not estimate statistical significance, confidence intervals, or generalization beyond the frozen groups. The canonical M12 audit contains the machine-readable analysis, exact hashes, reproduction command, and continuation note: [`luna-long-run-20261029-m12-group-uncertainty-20261029`](../audits/luna-long-run-20261029-m12-group-uncertainty-20261029/README.md).

## Separate HT-T2 SciFact component

HT-T2 is a separate evidence-verification component, not device-patent gold. The current deterministic lexical development run covers the full 300-claim development denominator over 5,183 corpus documents, writes 300 prediction rows, includes lexical evidence for all 300 rows, and has no missing prediction claim IDs. The pinned release records claims/annotations under CC BY 4.0, abstracts under ODC-By 1.0, and code under Apache 2.0. Official hidden/test labels are absent from the pinned release.

| Metric | Precision | Recall | F1 |
|---|---:|---:|---:|
| Abstract label-only | 0.125556 | 0.540670 | 0.203787 |
| Abstract rationalized | 0.103333 | 0.444976 | 0.167719 |
| Sentence selection | 0.061060 | 0.434426 | 0.107071 |
| Sentence label | 0.041859 | 0.297814 | 0.073401 |

Source and evaluator details are in the [HT-T2 audit](../audits/luna-long-run-20261029-ht-t2-lexical-dev-20261029/REPORT.md) and its [verification record](../audits/luna-long-run-20261029-ht-t2-lexical-dev-20261029/verification.json). These scores are development-only component evidence. They must not be pooled with HT-T1 patent-association recall, used as clinical truth, or presented as an adaptive-method or hidden-test result.

### HT-T2 evaluator-only error profile

The same frozen 300-claim development run was analyzed after scoring using only the evaluator-derived per-claim metrics. The analysis is non-exclusive: one claim can contribute to a partial-retrieval bucket and a rationale or label-mismatch bucket in the same split.

| Failure mode | Claims | Rate |
|---|---:|---:|
| Abstract retrieval miss | 78 | 0.2600 |
| Abstract partial retrieval | 5 | 0.0167 |
| Abstract rationale mismatch | 20 | 0.0667 |
| Sentence retrieval miss | 59 | 0.1967 |
| Sentence partial selection | 46 | 0.1533 |
| Sentence label mismatch | 38 | 0.1267 |
| Claims with no abstract/sentence gold evidence | 112 | 0.3733 |

This profile separates retrieval failure from rationale/label mismatch and keeps no-gold-evidence claims out of the retrieval-miss bucket. It is a descriptive development diagnostic, not a new metric, a patent-device label source, or evidence of clinical truth. The reproducible analysis artifact is [`luna-long-run-20261029-ht-t2-error-analysis-20261029`](../audits/luna-long-run-20261029-ht-t2-error-analysis-20261029/README.md).

## Provider-shaped mock table

| Metric | Actual value |
|---|---:|
| Development devices | 5 |
| Patents | 24 |
| Provider-shaped calls | 12 |
| Schema-valid calls | 12 |
| Macro known-link R@20 | 1.0000 |
| Simulated mock debit | USD 0.0012 |
| Paid cost | USD 0.00 |
| Unknown/pending billing items | 0 |

The mock transport exercised the action schema and R1 reservation/settlement path. It did not create provider evidence. Live/provider HT-B4 remains `BLOCKED_LOCAL` pending explicit transfer rights, credentials/credit, and reconciliation gates.

## Sources, model, and system-card references

- Frozen report and machine-readable outputs: [`docs/healthtech/audits/luna-long-run-20261029-m7-report-20261029/`](../audits/luna-long-run-20261029-m7-report-20261029/).
- Holdout comparison and machine-readable outputs: [`docs/healthtech/audits/luna-long-run-20261029-m10-b4-holdout-20261029/`](../audits/luna-long-run-20261029-m10-b4-holdout-20261029/).
- Paired group diagnostic and verification: [`docs/healthtech/audits/luna-long-run-20261029-m12-group-uncertainty-20261029/`](../audits/luna-long-run-20261029-m12-group-uncertainty-20261029/).
- Frozen B4 verification: [`docs/healthtech/audits/luna-long-run-20261029-m4-b4-r1-mock-20261029/verification.json`](../audits/luna-long-run-20261029-m4-b4-r1-mock-20261029/verification.json).
- HT-T2 SciFact development audit: [`luna-long-run-20261029-ht-t2-lexical-dev-20261029`](../audits/luna-long-run-20261029-ht-t2-lexical-dev-20261029/README.md).
- Model snapshot: `results/healthtech/ht-b4-r1-inputs-20261029-gpt41mini/model_snapshot.json`.
- Endpoint metadata: `results/healthtech/ht-b4-r1-inputs-20261029-gpt41mini/endpoint_metadata.json`.
- Long-run report code tested: `237fc669a4b7829be420c48547f36a69e28f64f0`.
- Holdout comparison code tested: `b12ef954a22f30c33e87c6ed78d8d40cc97d4fe3`.
- R1 policy and accounting limits: `docs/healthtech/goals/luna-long-run-20261028-889958e/OPENROUTER_ROUND1_TH.md` and the filled budget request.

The system-card section must preserve model/provider identity, pricing snapshot, structured-output/action restrictions, no-fallback/no-retry policy, transfer-rights gates, and the distinction between mocked transport and live execution.

## Claims kept separate

### Patent-association branch

The current outputs measure recovery of documented product-level device-patent associations under a frozen local candidate universe. They do not establish claim-level semantic relevance, exhaustive recall, patent validity, FTO, clinical suitability, investment merit, or generalization beyond the frozen groups.

### SciFact component branch

SciFact is a separate evidence-verification component with its own source release, labels, split, evaluator, and denominator. Component parity or lexical development scores must not be presented as proof of patent association quality or clinical truth. A current pooled claim remains `NOT_RUN` unless its prediction manifest, denominator, and permitted labels are present.

## Explicitly not run or not validated

- Live OpenRouter request, paid canary, paired pilot, and robustness round: `NOT_RUN / BLOCKED_LOCAL`.
- Rights-cleared semantic relevance gold and expert adjudication: `NOT_RUN`.
- Statistical significance, power, confidence intervals, or confirmatory superiority test: `NOT_RUN` / `NOT_ESTIMABLE`.
- Independent user study, correction burden, repeat use, willingness to pay, purchase, and ROI: `NOT_VALIDATED`.
- Journal submission, peer review, acceptance, and publication readiness: `NOT_RUN`.
- Clinical, legal, regulatory, FTO, patent-validity, and investment conclusions: out of scope.

## Reproducibility and next test

Reproduce the report and figures with the commands recorded in the M7/M8 audit verification files, reproduce the holdout comparison with the M10 audit command and frozen input hashes in `comparison.json`, and reproduce the paired group diagnostic with the M12 command and hashes in `verification.json`. The next discriminating test is a rights-cleared semantic judgment source with explicit labels, source revision/hash, rights policy, adjudicator role, exact locators, multiple independent company/family groups, and a predeclared untouched final holdout. Do not tune on the current holdout or recode unjudged pairs as negatives.

## M13 Philips-expanded offline sensitivity

M13 adds a bounded Philips cardiovascular development cohort to the Boston Scientific, Stryker Neurovascular, and Cook Medical composite. The resulting family-aware composite contains `11` devices, `31` patents, `38` product-level disclosed pairs, and `303` unjudged distractor pairs. Eight queries remain in development and the untouched Stryker company group remains the three-query final holdout. The family mapping is evaluator-side metadata only; it covers all `31` runtime patents, yields `24` observed families, and produces zero exact-group merges or split overlaps.

Fresh HT-B0a/B0b/B1/B2/B3 runs use the frozen protocol hash, local model snapshots, and candidate/rerank depth `31`. All `40/40` development and `15/15` holdout method-query rows complete with zero provider calls, zero paid cost, and no failed queries. At `K=20`, exact and family-aware macro recall are identical because the sourced family mapping does not merge an exact reference group in either split:

| Method | Development macro R@20 | Holdout macro R@20 |
|---|---:|---:|
| HT-B0a | 0.9613 | 0.5429 |
| HT-B0b | 1.0000 | 0.8095 |
| HT-B1 | 0.9688 | 0.8381 |
| HT-B2 | 0.9063 | 0.8857 |
| HT-B3 | 0.9688 | 0.8381 |

The M13 results are descriptive offline sensitivity evidence only. Product-level marking rows are not semantic relevance gold, unlisted pairs remain unjudged, K=50 is ceiling-limited by the 31-patent universe, and the three-query single-company holdout does not support stable generalization, statistical significance, clinical/FTO, validity, investment, or publication claims. The canonical M13 audit, summary, receipts, and continuation note are in [`luna-long-run-20261029-m13-philips-expansion-20261029`](../audits/luna-long-run-20261029-m13-philips-expansion-20261029/README.md).

## M14 Philips local dossier generation

M14 adds the committed Philips-specific local dossier adapter and runner at code commit `c6494370fad1c263eed169a7bd6a8c5718ed3427`. The adapter consumes only the frozen Philips runtime, source registry, pinned raw inputs, and reviewed rights matrix; it rejects runtime/source-registry/raw-file mutation and evaluator leakage, validates Philips marking rows independently, preserves raw and canonical IDs, source revisions, locators, hashes, and typed rights policies, and reconstructs product-level disclosure evidence for the dossier export.

The committed-code run over `results/healthtech/ht-philips-cardiovascular-20261029-r2/` completed three cases with `7` disclosed links, history versions `1` and `2` for each case, `3` actual search calls, `0` returned lexical candidates, `0` provider calls, and USD `0.00` paid cost. Each case has local JSON, English and Thai exports, source views, case manifests, receipts, and history. The reproducible output is `results/healthtech/ht-philips-dossiers-20261029-r3/`, with run manifest SHA-256 `e0acaa3d9852ddee96bce73d9b7527c77998a613925c81feca60f1aeb0837f60` and receipt SHA-256 `1bdfd218f90e681892723544fbe38cdcde81fd2c8e09c10de9654e019c2321af`.

The earlier `r1` attempt exposed an incorrect patent content-hash assumption; corrected working-tree `r2` passed after adopting the producer contract `content_hash({"title", "abstract", "claims"})`, and `r3` repeated the run with committed code. Synthetic dossier/cohort regressions pass `10/10` and compile checks pass. This is inspectable offline engineering evidence only. Philips marking rows remain product-level disclosed associations rather than semantic relevance gold, unlisted pairs remain unjudged, and Philips marking material plus Google-derived patent text remain local-only. The canonical M14 audit is [`luna-long-run-20261029-m14-philips-dossiers-20261029`](../audits/luna-long-run-20261029-m14-philips-dossiers-20261029/README.md).

## M15 declared rights policies and semantic-review packet

M15 closes the declared-rights-policy seam at implementation commit `35ee0728a8b470029ea993d3362a5f9d8ef2bcbf`. The rights resolver requires a declared `rights_policy_id` and fails closed for unknown, blank, mismatched, or structurally incompatible declarations. Abbott, Cook, and Philips adapters bind source rows to their typed registry policy before constructing runtime inputs. Adversarial tests cover external Markdown/JSON/source-view projection after history reload, adapter-level bad policy IDs, and a stale Abbott registry without a typed policy. This is a provenance and rights-boundary repair, not a semantic-labeling step.

The committed Philips r5 run over the frozen Philips cohort produces three inspectable cases, seven product-level disclosed links, history versions `1` and `2`, three search calls, zero returned lexical candidates, zero provider calls, and USD `0.00` paid cost. The r5 manifest SHA-256 is `c5a7fce38d02f805f0a651e443c605838c2204aa44cf6ba4268915b4bc7387b5`; the resource receipt SHA-256 is `17d7703a4651e5253e3ee5f77bf948c7834a110cf0aa7e30c045e6ab802a1f4a`. Philips marking material and Google-derived patent text remain local-only.

The corrected semantic-review packet is a reviewer-input artifact, not gold. It contains `11` queries, `31` patents, `341` query-patent pairs, all `341` pairs explicitly `UNJUDGED`, `0` semantic labels, `4` company groups, and the untouched three-query Stryker final holdout. Its family status is `SOURCED_LOCAL_EVALUATOR_MAPPING_ONLY`; the packet SHA-256 is `21df358e9b1f387d4b4f1a6c33c94e38abff7ccf15b39df746fba3acec05a206`. The first packet attempt using the company-group file was rejected; the corrected build used `results/healthtech/ht-google-family-mapping-20261029-r2-philips/family-mapping.json`.

M15 adds no semantic relevance gold, exhaustive-recall estimate, stable-generalization result, provider evidence, clinical/FTO conclusion, patent-validity conclusion, investment conclusion, customer validation, or publication-readiness evidence. The canonical audit is [`luna-long-run-20261029-m15-rights-packet-20261029`](../audits/luna-long-run-20261029-m15-rights-packet-20261029/README.md).

## M16 local semantic-review task export

M16 adds a deterministic local-only task exporter at implementation commit `23acfd468570ea2eac47d0f5790b7362268aa2d1`. The exporter consumes the corrected M15 review packet and writes `341` reviewer-visible metadata rows. Each row retains the named device, patent identity/title, source revision/hash/date/URL, and an empty response object. It omits evaluator split/family metadata, product-disclosure flags, evaluator relations, patent abstract/claims/text, and any semantic label.

The real export is `results/healthtech/ht-relevance-review-tasks-20261029-r1/`, with manifest SHA-256 `bf4ee05fc76f26f5be891866843e7f4a24a01d0fab8249c9db8c339ce09ce6d6` and task-row SHA-256 `7274129bd3cbe01449ae046e75c89b9d099aa4f78311e3b8db69ed9ab7382d8c`. Focused task/packet tests pass `11/11`; all `341` responses remain empty; semantic label count and forbidden field/text hits are both `0`.

This export is reviewer preparation, not semantic relevance gold. It does not authorize external distribution, provider transfer, or final scoring. The Stryker holdout remains untouched, and absent pairs remain `UNJUDGED`. The canonical M16 audit is [`luna-long-run-20261029-m16-review-tasks-20261029`](../audits/luna-long-run-20261029-m16-review-tasks-20261029/README.md).

## M20 company-holdout sensitivity

M20 reran the unchanged offline controls in four leave-one-company-out views
over the typed Boston Scientific, Stryker Neurovascular, Cook Medical, and
Philips composite. The frozen corpus contains `11` devices, `31` patents,
`38` product-level disclosed pairs, and `303` explicitly unjudged distractor
pairs. Each view used candidate and rerank depth `31`, `K=20`, the existing
family-aware evaluator projection, and the same HT-B0a/B0b/B1/B2/B3 method set.
All `8` development/holdout splits completed with zero failed devices, zero
provider or network calls, and USD `0.00` paid cost.

| Held-out company | HT-B0a | HT-B0b | HT-B1 | HT-B2 | HT-B3 |
|---|---:|---:|---:|---:|---:|
| Boston Scientific Corp | 0.845238 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| Stryker Neurovascular | 0.542857 | 0.809524 | 0.838095 | 0.885714 | 0.838095 |
| Cook Medical | 1.000000 | 1.000000 | 1.000000 | 0.833333 | 1.000000 |
| Philips Image Guided Therapy | 1.000000 | 1.000000 | 0.916667 | 0.916667 | 0.916667 |

These are macro known-link Recall@20 values against product-level disclosure
relationships. The repeated company rows reuse the same local corpus and are
not independent samples. The Stryker view is the lowest observed transfer case
for HT-B0a, HT-B0b, HT-B1, and HT-B3; Cook is lowest for HT-B2. Those patterns
are descriptive sensitivity evidence only and do not establish method
superiority, semantic claim relevance, exhaustive recall, stable
generalization, statistical significance, clinical suitability, FTO, patent
validity, investment merit, or publication readiness. Unlisted pairs remain
unjudged and are not negatives.

The canonical M20 record is [`luna-long-run-20261030-company-holdout-sensitivity-20261030`](../audits/luna-long-run-20261030-company-holdout-sensitivity-20261030/README.md). The next discriminating test remains an authorized rights-cleared semantic judgment source with explicit `relevant` / `not_relevant` labels, source revision and SHA-256, adjudicator role, exact locators, multiple independent company/family groups, and a predeclared untouched final holdout.
