# K1a: why Paper 53 used `datalyes/patembed-base` as its single first stage

Status: DRAFT v2 for IS2 (agent, 19 Nov 2026), which replaces v1 of the same day.

**Correction log (v1 → v2).** v1 rested on arXiv:2605.24297 (Yousefiramandi & Cooney). That preprint was **withdrawn by arXiv Admin
on 5 Nov 2026** because it "does not meet arXiv's research content quality standards"; this was checked on the arXiv abs page on
19 Nov 2026. v1 was drafted from the owner's v1 PDF without checking the current status. v2 removes every number taken from that
preprint. Paper 53 cites the preprint as ref. [15], but only in its related-work list of patent-embedding benchmarks
("[14]-[16]"), not as the reason for choosing the encoder. If IS2 mentions it, state that it was withdrawn.

## What Paper 53 actually records (historical fact, not reconstructed)

Paper 53 §III-B (`literature-review/internal/paper53_ieee_express.pdf`) records:

> "Candidate generation indexed 45,336 frozen TAC records with the datalyes/patembed-base encoder [5], [18] and returned 100
> candidates per query. Normalized inner product served as cosine similarity, with deterministic ties ..."

- [5] = PatenTEB (Ayaou & Cavallucci, arXiv:2510.22264, 2025).
- [18] = the model card at revision `244ba452908a3093be11efb8a44396652317fb14`.

The paper records **which** encoder was used and **where it comes from**. It does **not** record a comparative selection
experiment. IS2 must not invent one after the fact.

Paper 53 §VI already lists this as a limitation: "one benchmark, candidate generator, TAC rendering, primary reranker, pool
depth of 100". It names broader retriever comparisons as future work.

## Answer for the IS2 report

The PatenTEB group at ICUBE, INSA Strasbourg, developed the model and DAPFAM. The model card describes multi-task training on 13 patent tasks for applications including prior-art search. The base encoder distils 12 of the large encoder's 24 layers and has 193 million parameters, 768-dimensional embeddings and a 512-token input limit. The license is CC BY-NC-SA 4.0. Pinning the revision made it possible to freeze a reproducible candidate pool for paired instruction comparisons. These facts explain the encoder's role. Paper 53 reported no comparative first-stage selection experiment and identified this limitation in section VI.

| Retrospective evidence | Observation | Evidence scope |
|---|---|---|
| Paper 86 (unpublished, withdrawn from IEEE), 2026 nine-cell run on 250 DAPFAM DEV queries | PatEmbed-large led Qwen3-Embedding-0.6B and Arctic-embed-m-v2.0 under every recipe, at about 0.419 Recall@100. | HISTORICAL PROJECT RECORD; large model variant |
| P1-DAPFAM DEV, B0 = PatEmbed-large | OUT R@200 was 0.1477 on 349 queries. | MEASURED / REPOSITORY RECEIPT; large model variant |
| P1-BridgeRet P1-DEV, USPTO office actions, 1M corpus | OUT R@200: Z-PatEmbed-large 0.3282, Z-Qwen3 0.2741, Z-Arctic 0.2248. | MEASURED; descriptive, different benchmark |

These results support the PatEmbed family's retrieval performance in those settings. None measures patembed-base on Paper 53's original cohort. For the empirical answer to K1a/K1b, B53 compares F0 (patembed-base) with BM25, RRF(BM25,F0), Arctic and RRF(BM25,Arctic) on the same DAPFAM cohort at depths 100 and 200. The secondary arms are F6 (PatEmbed-large) and F7 (Qwen3-Embedding).

## Sources
- Paper 53, §III-B, §VI and refs [5], [15], [18] (`literature-review/internal/paper53_ieee_express.pdf`).
- datalyes/patembed-base model card, https://huggingface.co/datalyes/patembed-base (read 19 Nov 2026).
- I. Ayaou and D. Cavallucci, PatenTEB, arXiv:2510.22264 (2025).
- arXiv:2605.24297: withdrawn by arXiv Admin, 5 Nov 2026 (https://arxiv.org/abs/2605.24297). Not used as evidence.
- Paper 86 (owner, unpublished; withdrawn from IEEE): `myDegree/IS/IS_2/` (see `PAPER86-AND-P1DAPFAM-SELECTION.md` S2).
- P1-DAPFAM dev receipt: `docs/healthtech/audits/ptp-native-dense-preparation-20261110/dev-metrics-v1.json`.
- P1-BridgeRet DEV: `docs/healthtech/research/paper1-bridgeret/dev-results/`.
