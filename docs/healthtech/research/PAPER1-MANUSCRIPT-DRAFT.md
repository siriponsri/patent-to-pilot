# Source-preserving query representations and relation extraction for cross-domain patent retrieval

Working manuscript, 10 November 2026. Development evidence only; incomplete and
not ready for submission. SACR generation is in progress at this checkpoint;
its fidelity, pilot and retrieval results are not available. The restricted
tests remain unopened. This draft preserves measured results and failed arms
without presenting the intended four-system comparison as completed.

## Abstract — provisional

We investigate whether query-side functional representations and deterministic
corpus relation extraction can support cross-domain known-family recovery in
DAPFAM under a bounded solo-project workflow. We first establish a native
title-and-abstract query baseline over the full candidate corpus, reusing
existing passage vectors without retraining or corpus re-encoding. On 349
eligible cross-domain development queries, this baseline obtains Recall@200
of 0.14772. A fixed, stratified 100-family feasibility sample for one conservative
relation extractor produces six records from five families and no cross-family
exact-alias candidates; this configuration is therefore stopped before graph
construction. Source-linked query generation is subject to a prospective
automated-screening and limited human-review gate. Its retrieval effects remain
unmeasured. These intermediate findings establish an executable baseline and
a specific extraction feasibility failure, not superiority of a new method or
a general impossibility result for structured retrieval.

## 1. Motivation and research questions

Cross-domain patent retrieval seeks useful functional correspondences despite
different application terminology. Query abstraction may improve lexical or
semantic matching, but it can also remove conditions that distinguish the
technical requirement. Corpus relations may expose shared mechanisms, yet
extraction coverage and cross-record linkage must be demonstrated before
traversal can be evaluated.

The planned study asks whether a source-preserving query intervention improves
known-family recovery over a fixed dense anchor, and whether graph traversal
adds value over direct search of the same extracted information. These are
separate questions: an extraction-empty configuration cannot provide a valid
test of traversal benefit. The intended B0/SACR/S/G panel is retained in the
protocol; unavailable arms must remain explicitly unavailable in reporting.

## 2. Data and evaluation contract

We use the existing 474-query development assignment and all 45,336 candidate
families. Query input is the exact native title-and-abstract text; candidate
passages derive from title, abstract and claims. The runtime receives no qrels.
A separate evaluator reads only the prepared development projection. The
restricted DAPFAM and MTM tests remain closed.

Positive qrels are interpreted by the pinned native adapter before applying
IN/OUT partition filters. Candidate search remains over the full corpus in all
partitions. Scores are query-macro averages over queries with at least one
known positive in that partition. Missing or empty eligible rankings score
zero; queries without partition positives are counted and excluded from that
partition's denominator. Known positives are binary, and nDCG ideals use all
known partition positives up to the cutoff. Incomplete judgments prevent
interpreting every unjudged candidate as a false positive.

The primary development endpoint is OUT Recall@200. nDCG@10 is a descriptive
bridge to supplied literature, not a new confirmatory endpoint. Historical
development exposure and shared-positive dependence limit independent
generalization claims. Component-based uncertainty analyses are still pending;
no confidence intervals or significance claims are supplied here.

## 3. Methods and fidelity controls

### 3.1 Dense anchor

B0 uses the existing PatEmbed-large fp32 passage vectors with 384-word windows
and 64-word overlap, query-only encoding, the established retrieval prefix,
and family MaxP aggregation. Global lexical family-ID tie ordering precedes
top-200 selection. The run binds 188,944 passage vectors to the existing corpus
and encoder identity. It does not construct new corpus embeddings.

### 3.2 Source-linked query method

The prospective SACR pipeline uses the existing local Qwen3-8B model with
greedy, non-thinking fp16/eager generation. Per-query JSON grammar binds the
query identity and exact source hash. Validation checks literal quote alignment,
source order and structural constraints; these checks do not establish semantic
fidelity. Normally completed unusable generations are retained and charged,
without repair or replacement calls. Infrastructure failures stop dependent
work. Independently valid anchors are not evidence that abstraction succeeded.

The fixed 100-query fidelity sample is selected by a published deterministic
hash rule. Complete query bundles undergo structural, lexical and local-model
screening before human cards or new SACR retrieval scores. At most 20 flagged
queries and exactly 10 hash-selected unflagged sentinels are reviewed. Any
critical error, including a false-negative sentinel, stops the configuration;
incomplete judgments cannot pass. This is automated screening plus limited
owner review, not independent expert validation. Same-model criticism may
share generation blind spots. See the frozen fidelity specification for the
full rule and cumulative 60-card allocation across SACR and S/G.

### 3.3 Fixed relation extraction feasibility

One deterministic extractor was declared before inspecting its outputs. The
100-family sample consists of 25 hash-selected families from each of four
corpus text-length rank strata, without using qrels or retrieval outcomes.
The extractor requires explicit configured/adapted/operable-to clauses, retains
literal spans and unresolved conditions, and proposes only exact whole-clause
cross-record aliases. It does not use inferred synonyms or LLM extraction.
These conservative design choices are part of the tested configuration, not
claims about the maximum achievable coverage of relation extraction.

## 4. Results available at this checkpoint

### 4.1 Native dense development baseline

| Partition | Eligible queries | nDCG@10 | nDCG@100 | Recall@100 | Recall@200 |
|---|---:|---:|---:|---:|---:|
| ALL | 474 | 0.17239 | 0.20893 | 0.25222 | 0.34262 |
| IN | 450 | 0.20691 | 0.27972 | 0.39413 | 0.51370 |
| OUT | 349 | 0.02328 | 0.04490 | 0.09732 | 0.14772 |

There were no missing or empty rankings. The 24 IN-ineligible and 125
OUT-ineligible queries are excluded only from their respective metric
denominators. IN and OUT are overlapping eligible populations, not disjoint
subsets whose sizes should sum to 474.

### 4.2 Negative extraction feasibility result

Five of 100 sampled families yielded six records; 95 yielded none. Among 43
cue-bearing segments, 24 exceeded the configured length bound. No cross-family
exact-alias candidate pair was produced. The configuration failed its graph
feasibility gate and could not supply ten record-bearing sentinel cases.
Consequently no full-corpus extraction, structured index, accepted graph edge
or S/G retrieval comparison was run. Semantic fidelity was not assessed.
Zero sample alias candidates do not establish zero possible corpus links.

### 4.3 Unavailable comparisons

SACR fidelity and retrieval results are pending. S/G retrieval effects are
unavailable because the fixed extraction configuration failed feasibility.
Neither absence is reported as a zero treatment effect. MTM transfer is not
run and has no human-review allocation. No protected-test result exists.

## 5. Cost, failures and reproducibility

The B0 supervisor interval was 40.455 seconds, including 5.829 seconds of query
encoding and 9.985 seconds of ranking. Peak sampled host cgroup usage was
1,960,681,472 bytes; this is not GPU memory. The first evaluator attempt failed
on an import before reading data (0.701 seconds). A separately preserved
dependency-mount repair completed evaluation in 7.978 seconds, with no GPU use.

The relation feasibility task used 1.797 seconds of wall time and wrote 54,639
private bytes, with no GPU/model calls or human cards. Its approximately0.047
seconds of in-memory extraction is too short and too narrow to support a
reliable full-corpus resource forecast. Do not extrapolate it into approval.

SACR engineering history includes a failed source-order smoke and one subsequent
authorized successful smoke. Their costs remain in the cumulative resource
ledger. Native profile generation costs must be added from the actual terminal
receipt; the current reservation is not an observed completed cost.

Private source records, per-query outputs and qrels are not published. Public
reproducibility artifacts include code, source/configuration hashes, aggregate
receipts, failure states and the sampling protocol. All relevant model and
dataset rights require assessment before any wider artifact release.

## 6. Relation to the supplied papers

The supplied Paper53 motivates exposure-aware analysis and paired wins/losses
rather than a single average-effect headline. Its fixed-pool decomposition
cannot be applied unchanged to SACR acquisitions that alter candidate unions.
For changed pools, report exposure/rescue/loss strata and distinguish acquisition
from within-pool selection; do not label these diagnostic strata causal effects.

The DAPFAM papers use different cohorts, encoders, precision and passage/view
configurations. Our 474-query dev results are not apples-to-apples replications
of published all-query scores. The paired local comparison must hold the query
cohort, candidate universe, qrels, fields, encoder/index and metrics fixed.
Published values belong in a separately labeled context table, without direct
percentage-gain claims. The protocol comparison and source-page references are
maintained in DAPFAM-PAPER-COMPARABILITY.md; files01 and38 are byte-identical and
must not be counted as independent studies.

## 7. Limitations and required completion

The current evidence supports a measured native baseline and failure of one
specific deterministic extraction configuration. It does not support a new
retrieval-quality claim, independent semantic validation, test generalization,
inventive-design success or clinical/product usefulness. Complete the bounded
SACR stages and fidelity decisions before permitted pilot/full-dev comparisons.
Report stopped arms, all spent resources and remaining uncertainty even if the
intended panel cannot be completed. Final discussion and conclusions remain
pending these outcomes; submission and test access require separate authority.

## Evidence links

- [Native baseline and evaluator receipt](../audits/ptp-native-dense-preparation-20261110/README.md)
- [Native aggregate metrics](../audits/ptp-native-dense-preparation-20261110/dev-metrics-v1.json)
- [S/G feasibility receipt](../audits/ptp-sg-feasibility-20261110/README.md)
- [S/G extraction result](../audits/ptp-sg-feasibility-20261110/extraction-result.json)
- [Solo fidelity freeze](plans/SACR-SOLO-FIDELITY-FREEZE.md)
- [Paper comparison protocol](plans/DAPFAM-PAPER-COMPARABILITY.md)
- [Cumulative resource ledger](../audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json)
