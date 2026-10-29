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
