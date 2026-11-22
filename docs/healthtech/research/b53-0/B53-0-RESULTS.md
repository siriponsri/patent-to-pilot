# B53.0: native DAPFAM metrics compared with the published DAPFAM paper (MEASURED, 22 Nov 2026)

**Protocol:** `plans/B53-0-AMENDMENT-20261122.md`, frozen at 58467ace before any B53.0 number.

**Code:** `scripts/research/b53_0_native.py`, run on dr-train CPU over the frozen B53 runs. **Aggregates:**
[b53-0-native.json](b53-0-native.json). **Cost:** USD 0.

## Setup

- **Task:** TAC → TAC, over the full 45,336-family corpus.
- **Queries:** 1,247; with positives: ALL 1,247, IN 1,217, OUT 905.
- **Relevance:** every relevance score is 1, so binary and graded nDCG coincide.
- The own family is not excluded (native).

## Comparison with the paper (arXiv v2, Tables 17 and 19)

| System (ours vs paper) | Metric | ALL | IN | OUT |
|---|---|---|---|---|
| **Arctic-embed-m-v2.0** (ours fp16 vs paper int8) | nDCG@100 | 0.3110 vs 0.3055 (+0.0055) | 0.3533 vs 0.3477 (+0.0056) | 0.0483 vs 0.0482 (+0.0001) |
| | R@100 | 0.3697 vs 0.3627 (+0.0070) | 0.4543 vs 0.4437 (**+0.0106**) | 0.1245 vs 0.1311 (−0.0066) |
| **BM25** (ours k1 1.5 vs paper bm25s k1 1.2) | nDCG@100 | 0.2430 vs 0.2451 (−0.0021) | 0.2737 vs 0.2759 (−0.0022) | 0.0413 vs 0.0418 (−0.0005) |
| | R@100 | 0.2798 vs 0.2820 (−0.0022) | 0.3447 vs 0.3463 (−0.0016) | 0.1069 vs 0.1117 (−0.0048) |

**Verdict under the frozen ±0.010 rule:** 11 of 12 cells are consistent with the published values. Arctic R@100 IN differs by
+0.0106, just outside the tolerance.

The pipeline, the evaluator and the cohort definitions therefore match the DAPFAM paper's TAC → TAC setting closely. The
remaining differences are what the stated configuration gaps would produce (int8 vs fp16, BM25 tokenizer and k1). These
numbers are a matched re-implementation; none is called an exact reproduction.

## Context rows (no published counterpart; descriptive)

| System | nDCG@100 ALL / IN / OUT | R@100 ALL / IN / OUT |
|---|---|---|
| F0 patembed-base (Paper 53's first stage) | 0.366 / 0.415 / 0.061 | 0.444 / 0.541 / 0.160 |
| F2 RRF(BM25, F0) | 0.349 / 0.392 / 0.063 | — |
| F4 RRF(BM25, Arctic) | 0.315 / 0.356 / 0.052 | — |

**Caution on F0.** patembed-base exceeds every document-level system in the paper. It even exceeds the paper's best passage
hybrid (nDCG ALL 0.3475). The model was trained on PatenTEB, which uses the same source (Lens) and comes from the same
authors as DAPFAM, and the AM-7 audit found it was trained on PatenTEB retrieval_OUT with a non-temporal split. Overlap
between its training data and DAPFAM evaluation families is therefore possible. Until a family-level overlap audit is done,
F0 must not be presented as a fair zero-shot baseline on DAPFAM. It stays a historical (Paper 53) comparator only.

## Not done (deferred, per amendment §1)

- TA → TAC: the title+abstract query view is not staged in the B53 inputs.
- Arctic int8: the quantisation method is not stated in the paper.
- bm25s with its defaults.
- The published Array version was not readable; the comparison uses arXiv v2 only.
