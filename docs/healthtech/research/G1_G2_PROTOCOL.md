# HT-G1 / HT-G2 Development Protocol

**Protocol:** `ht-g1-g2-public-disclosure-development-v1`
**Frozen:** 2026-10-28
**Status:** development-only; no final holdout claim

## Setting

The main Bridge device--patent dataset is `BLOCKED_LOCAL` for rights, cohort, and split reasons. This protocol therefore freezes an independent public development setting without changing the root research question: known recovery of documented device--patent relationships.

The cohort builder is `scripts/healthtech/fetch_public_device_cohort.py`. The observed run acquired three predeclared Abbott cardiovascular products from PMA identifiers `P100009`, `P230007`, and `P240042`. It resolved 41 unique U.S. patent documents and 61 product-level disclosed pairs. The union of those documents is the candidate universe for every method.

The immutable run artifacts are under `results/healthtech/ht-public-cohort-20261028-r1/`. The runtime file contains device metadata and patent text only. The evaluator reference file contains the disclosed relations and is opened only after raw rankings and runtime predictions are written.

## IDs and evidence types

- Preserve Abbott's raw numeric patent string and the page-resolved canonical publication/grant ID, including jurisdiction and kind code.
- Canonical IDs are deduplicated before each cutoff. A collision or missing page is a data error, not a silent merge.
- PMA number plus supplement, UDI, and patent document identifiers remain distinct keys.
- `disclosed_link` means a source-backed product disclosure relation. It is not a claim-level semantic judgment, FTO conclusion, validity conclusion, or clinical fact.
- Unlisted device--patent pairs are unjudged and do not become negatives.

## Queries, universe and split

Eligible queries are `HT-DEV-MITRACLIP`, `HT-DEV-TRICLIP`, and `HT-DEV-TENDYNE`, each with at least one disclosed link. The exact-patent graph has two components: MitraClip/TriClip share disclosed patents; Tendyne is separate. All three devices share the Abbott company group. No family mapping is assumed because an independent family source was not acquired.

All three queries remain in `development`. There is no final holdout because the cohort has only three devices, one applicant, one disclosure source, and small independent-group counts. The split is a declared limitation, not a generalization result.

## Endpoint and cutoffs

- Primary metric: macro known-link Recall@20.
- Secondary cutoffs: Recall@10 and Recall@50.
- Secondary micro recall is retained in evaluator output.
- Missing or failed eligible queries score zero and remain in the denominator.
- Unknown prediction IDs retain their rank and cannot count as hits.
- No open-world precision or F1 is computed.

## Methods

### HT-B0a

Company/metadata-only control using source-backed Abbott applicant/disclosure metadata. All ties break by canonical patent ID. This measures a metadata shortcut and is not comparable to the full technical information regime without an explicit information-regime label.

### HT-B0b

Deterministic BM25 over patent title, abstract, and claims in source order. `k1=1.2`, `b=0.75`, candidate depth 50, score ties by canonical ID.

### HT-B1

Fixed strong local hybrid: BM25 candidate retrieval plus independent `sentence-transformers/all-MiniLM-L6-v2` dense retrieval, reciprocal-rank fusion with `k=60`, then actual `cross-encoder/ms-marco-MiniLM-L-6-v2` reranking over the same frozen pool. Both model revisions are pinned by commit hash and the quantized ONNX files are retained locally with SHA-256 manifest entries. The old token-overlap approximation remains separately labeled in the legacy engine and is not reused here.

### HT-B2

Fixed multi-query schedule using the device technical description followed by the declared PMA generic-name and product-code features. Each query uses the same lexical encoder, dense encoder, fusion, and reranker as HT-B1. Duplicate candidates, query count, and rerank work remain charged.

### HT-B3

Simple observable heuristic. Start with the technical description. Continue to the next declared feature only when first-pass new-candidate yield or lexical/dense disagreement indicates unresolved state; otherwise stop. The controller can read only current retrieval outputs, disagreement, new IDs, and budget. It never reads references or hit status.

## Leakage and diagnostics

Runtime validation rejects `references`, `known_links`, `disclosed_by`, `gold`, `evaluator`, `split`, and `family_label` fields. The Abbott disclosure page and evaluator relations are absent from `runtime.json`. Explicit patent-like tokens are counted and masked for diagnostics; the observed PMA device inputs contain no patent document IDs. Company overlap is reported; company-held-out sensitivity is not estimable.

## Resources and failures

Every query attempt records the query text/hash, status, candidate counts, rerank pairs, embedding query tokens, rerank tokens, local CPU time, wall time, and stop reason. Index/model preparation is reported separately from online query work. Monetary cost is zero because no provider action is dispatched; offline resource units are not dollars.

## Reproduction boundary

Acquisition requires public network access only to the allowlisted FDA, Abbott, Google Patents, and Hugging Face URLs and writes raw pages/weights to ignored local paths. Scoring is offline-only after acquisition. No credentials, private data, paid provider, live API, deployment, clinical study, FTO analysis, or publication-readiness claim is included.

The exact commands and outcome receipts are recorded in `docs/healthtech/G1_G2_RECEIPT.md` after the run and final verification.
