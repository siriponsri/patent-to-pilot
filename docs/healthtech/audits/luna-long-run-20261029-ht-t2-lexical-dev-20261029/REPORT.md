# HT-T2 SciFact lexical development report

## Objective and scope

Create the first declared current-run SciFact prediction artifact for HT-T2 and
score it against the pinned local `dev` split without allowing evaluator labels to
enter runtime generation. The package is bounded to deterministic lexical ranking
and is separate from HT-T1 device-patent retrieval.

Excluded: hidden/test scoring, adaptive or neural inference, provider calls,
clinical or patent conclusions, and any claim about exhaustive evidence recovery.

## Inputs and protocol

| Item | Value |
|---|---|
| Protocol | `configs/healthtech/ht_t2_scifact_lexical_dev_v1.json` |
| Release manifest | `data/manifests/healthtech/scifact-release-20261027-r1.json` |
| Source release | SciFact commit `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e` |
| Corpus | 5,183 documents; SHA-256 `b8d6c89624cb2ed74dee8938effc4f5d8bd2086887880af8110d64be4ceade62` |
| Dev claims | 300 claims; SHA-256 `86f0435d08fdb65d1aa41d1472684f57e6e71930626497bdf4d7a9ec1a632217` |
| Official test labels | Absent from the pinned release |
| Rights recorded by release manifest | Claims/annotations CC BY 4.0; abstracts ODC-By 1.0; code Apache 2.0 |

The generator uses lowercase alphanumeric tokens, a fixed stopword list, BM25
document ranking, top-3 documents, and sentence overlap to select at most three
rationale sentences. Every emitted evidence item uses the frozen default label
`SUPPORT`.

## Results

| Metric | Precision | Recall | F1 |
|---|---:|---:|---:|
| Abstract label-only | 0.125556 | 0.540670 | 0.203787 |
| Abstract rationalized | 0.103333 | 0.444976 | 0.167719 |
| Sentence selection | 0.061060 | 0.434426 | 0.107071 |
| Sentence label | 0.041859 | 0.297814 | 0.073401 |

The denominator is the full 300-claim development split. There are no missing
prediction claim IDs. The abstract counts are 113 correct label-only items and 93
correct rationalized items out of 900 retrieved document rows; sentence counts are
159 correct selections and 109 correct labels out of 2,604 retrieved sentence
rows.

These values are descriptive baseline performance on the local development split.
They should not be compared with a hidden test score, used as HT-T1 patent-link
evidence, or presented as a clinical or investment result.

## Verification

| Acceptance check | Status | Evidence |
|---|---|---|
| Runtime reader ignores malformed evaluator fields | PASS | `tests/test_healthtech_prelive.py` |
| Deterministic lexical ranking and empty-evidence behavior | PASS | `tests/test_healthtech_scifact_baseline.py` |
| Targeted tests | PASS | `17 passed` |
| Python compilation | PASS | `python -B -m compileall -q src scripts tests` |
| Prediction generation | PASS | `results/healthtech/ht-t2-scifact-lexical-dev-20261029-r3/prediction_manifest.json` |
| Evaluator-only score | PASS | `results/healthtech/ht-t2-scifact-lexical-dev-20261029-r3/score.json` |
| Provider calls and paid cost | PASS | `0` and `$0` in run outputs |

The executable commands and file hashes are recorded in `verification.json`.
The generated prediction and per-claim files remain in the ignored results area;
the audit stores only sanitized counts, hashes, provenance, and limitations.

## Limitations and next test

This is a deterministic lexical control, not the proposed adaptive method. The
split is development-only, the official test labels are unavailable, and SciFact
is an evidence-verification component rather than device-patent gold. The next
discriminating HealthTech experiment remains a rights-cleared device cohort with
multiple independent company/family groups and a predeclared final holdout. Keep
live/provider HT-B4 `BLOCKED_LOCAL` until its independent pricing, identity,
credit, transfer-rights, payload, and reconciliation gates are evidenced.
