# HealthTech research product report — O1-O4 continuation — 2026-10-31

Status: `PARTIAL_O4_ENGINEERING_PASS_O3_BLOCKED_LOCAL`.

This report is the current research/product handoff for the named Abbott
cases. It supersedes the older parent narrative where that narrative still
describes the named-device HTTP generation path as not run. Historical parent
receipts remain immutable.

## Scope and evidence

The bounded question is whether the product path can carry three named public
device dossiers through browser input, server-owned retrieval, local
generation, evidence inspection, history editing, and export while preserving
the research separation between fixed controls, adaptive heuristics, and
provider evidence.

Primary evidence:

- `browser-receipt.json`: real Chrome acceptance for MitraClip, Tendyne, and
  TriClip.
- `../ht-o1-o4-http-vector-20261031/patembed-http-receipt.json`: PatEmbed
  retrieval receipt.
- `../ht-o1-o4-http-vector-20261031/e5-http-receipt.json`:
  multilingual-e5 retrieval receipt.
- `../ht-o1-o4-http-vector-20261031/adaptive-acquisition-report.json`:
  fixed-control, adaptive-control, local-generation, and API-gate summary.
- `verification.json`: final command outcomes and privacy boundaries.

Raw dossiers, source payloads, vector bundles, model weights, generated text,
credentials, and private runtime paths are outside this report and outside the
repository.

## 1. Three-case E2E result

| Case | PatEmbed candidates | e5 candidates | HTTP job | Source/history/export | Local generation |
|---|---:|---:|---|---|---|
| `HT-DEV-MITRACLIP` | 33 | 33 | succeeded | source PASS; `1 -> 2`; JSON v2 | schema-valid; 32.888s |
| `HT-DEV-TENDYNE` | 33 | 33 | succeeded | source PASS; `1 -> 2`; JSON v2 | schema-valid; 33.059s |
| `HT-DEV-TRICLIP` | 41 | 41 | succeeded | source PASS; `1 -> 2`; JSON v2 | schema-valid; 33.121s |

All three cases completed the browser route with zero vector errors, zero
paid/provider calls, and paid cost `USD 0.00`. The acceptance also checked
that the selected evidence ID did not produce a source mismatch.

## 2. Grouped retrieval analysis

The current Abbott adapter groups the two mitral devices together and keeps
TriClip as the tricuspid case. This grouping is a product/query-family view,
not a new evaluator gold label.

| Group | Cases | Jobs | Candidate pattern | Generation latency | Interpretation |
|---|---|---:|---|---:|---|
| Mitral pair | MitraClip, Tendyne | 2/2 | 33 and 33 for both encoders | 32.888–33.059s | Stable candidate cardinality across the pair; no runtime failure observed |
| Tricuspid | TriClip | 1/1 | 41 for both encoders | 33.121s | Larger returned candidate set; no runtime failure observed |

The two encoder receipts share the same 41-patent runtime corpus and three
ordered queries. Equal candidate counts here are an execution receipt, not
evidence that the encoders rank the same patents or have equal quality.

The separate DAPFAM retrieval diagnostic reports the following citation-based
metrics over its frozen benchmark inputs:

| Diagnostic | Macro Recall@100 | Micro Recall@100 |
|---|---:|---:|
| PatEmbed | 0.422525 | 0.422319 |
| multilingual-e5 | 0.287414 | 0.287296 |
| BM25 control | 0.214225 | 0.213928 |

These values are not semantic device–patent gold and are not a claim of
exhaustive recall, clinical suitability, FTO, or investment merit.

## 3. Fixed-budget research frontier

The adaptive report keeps the method classes separate and reports the current
development frontier descriptively at macro known-link Recall@20. These rows
are not per-case browser metrics and are not pooled scientific estimates.

| Method | Macro Recall@20 | Query calls | Rerank pairs | Cost | Evidence class |
|---|---:|---:|---:|---:|---|
| HT-B0a company control | 0.8190 | 3 | 0 | USD 0.00 | offline control |
| HT-B0b BM25 lexical | 0.9524 | 3 | 0 | USD 0.00 | offline control |
| HT-B1 fixed hybrid | 0.9333 | 3 | 72 | USD 0.00 | offline control |
| HT-B2 fixed multi-query | 0.9333 | 12 | 288 | USD 0.00 | offline control |
| HT-B3 simple adaptive heuristic | 0.8857 | 5 | 120 | USD 0.00 | offline control |
| HT-B4-MOCK | 0.8857 | 8 shaped calls | n/a | USD 0.0008 simulated | mock only |

Within this bounded development slice, HT-B0b has the highest reported
Recall@20 with fewer query calls than B2 and no reranking. The result is a
negative adaptive finding for this slice, not evidence that adaptive
acquisition is generally worse. Cohort size, candidate-universe ceilings,
grouping, and the `UNJUDGED` policy prevent a pooled generalization claim.

## 4. Generation and cost-quality trade-off

The local Qwen3-8B branch is schema-valid for all three cases with measured
latencies of 32.888–33.121 seconds and zero paid cost. It is a deployment
configuration check, not a causal claim that an 8B model is better or worse
than a larger API model.

The OpenRouter `qwen/qwen3-32b` branch is `BLOCKED_LOCAL` and was not called.
The missing gates are one canonical cumulative ledger identity, current
account credit, a fresh route/parameter/pricing snapshot, and a rights-cleared
outbound dossier-prompt manifest. The original USD8 owner scope already
authorizes one local generator plus one API generator. The absence of an API
result is therefore a known blocker, not a zero-quality or zero-cost
observation.

The follow-on offline engineering package is complete: the existing owner
authorization is no longer represented as `NOT_GRANTED`; the shared ledger
registry rejects path substitution and refuses to create a replacement journal;
the paired payload and API runner are implemented with mock/dry-run coverage;
and candidate output validation preserves `retrieved_candidate` versus
source-backed `disclosed_link` semantics. These checks do not clear the paid
branch because the real journal and current account credit were not available
for reconciliation.

## 5. Failure analysis and boundaries

- Named-device HTTP jobs: `3/3` succeeded for each encoder receipt.
- Vector errors: `0` for all six retrieval jobs.
- Source inspection: HTTP `200` / browser source check PASS for all three
  cases.
- History/export: all cases reached version `2`; JSON export passed in the
  generation browser acceptance, and the vector receipts also record Thai and
  English version-2 exports.
- Generation schema: `3/3` valid; no local generation job failed.
- Existing browser integration deferred temporary-directory cleanup after a
  Windows `EPERM` retry limit. The test exited `0`; this is scratch cleanup,
  not a product-path failure.
- No semantic judgment acquisition, clinical/FTO review, patent-validity
  conclusion, deployment, public release, or commercial validation occurred.

## Decision

O1 and O2 are complete engineering packages. O4 is a verified three-case
product-path and research handoff with grouped retrieval, failure, and
cost-quality analysis. O3 remains the only material blocker to a complete
four-outcome goal. Keep paid dispatch closed and resume only after the O3
ledger, credit, fresh route/parameter, and prompt-rights gates are recorded;
the original owner authorization is already present.
