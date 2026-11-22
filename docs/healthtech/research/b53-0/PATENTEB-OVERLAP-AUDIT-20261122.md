# PatEmbed–DAPFAM overlap audit (owner decision D3), 22 Nov 2026: BLOCKED for train; partial audit on public test splits

## 1. The planned audit cannot run: the PatenTEB train split is not public

- Owner decision D3 approved downloading "the PatenTEB train split" for a family-level overlap audit.
- **No train split exists to download.** All 16 `datalyes/*` datasets on Hugging Face (15 PatenTEB tasks plus
  `DAPFAM_patent`) contain only `test/data.parquet` (Hugging Face API, 22 Nov 2026).
- The authors' repository README (github.com/iliass-y/patenteb, last push 1 Nov 2026) states that the 1,556,751 training and
  181,215 validation examples are "not released yet". The paper (arXiv 2510.22264, §3) describes an 80/10/10 split
  stratified by IPC3 that "prevents family leakage", with no time split.
- Nothing was downloaded for this audit. It used only files already on the owner PC (downloaded 5 Nov 2026).

## 2. Partial audit with what is available (aggregates only)

**Inputs** (`../_private_artifacts/healthtech/`, sha256 prefix):
- DAPFAM `corpus.parquet` (45,336 families, `relevant_id`; 469fe8e0…) and `queries.parquet` (1,247 families,
  `query_id`; b5ad91a6…). 135 query IDs are also corpus IDs.
- PatenTEB test splits: `para_problem` (rev 4247eb81; 537fefd5…), `problem2solution` (rev 69f7e9a9; e5e65734…),
  `retrieval_OUT` (rev d156b1ec; 28cdcff0…).
- Both datasets use the same Lens identifier format (e.g. `000-688-331-282-144`), so IDs match directly.

**Script:** [scripts/research/patenteb_dapfam_overlap.py](../../../../scripts/research/patenteb_dapfam_overlap.py).

| PatenTEB test file, column | Distinct IDs | DAPFAM queries found | DAPFAM corpus found |
|---|---:|---:|---:|
| para_problem, q | 17,377 | 1 | 63 |
| problem2solution, q | 18,729 | 3 | 71 |
| retrieval_OUT, q | 8,410 | 2 | 43 |
| retrieval_OUT, pos | 15,045 | 19 | 220 |
| retrieval_OUT, neg | 8,819 | 29 | 116 |
| **Union of test queries** | 35,177 | **5** | **134** |
| **Union of all test IDs** | 58,720 | **50 (4.0%)** | **466 (1.0%)** |

## 3. What this shows and what it cannot show

- **Shared universe, confirmed.** DAPFAM families occur inside PatenTEB data: 50 of 1,247 DAPFAM queries and 466 of
  45,336 corpus families appear in only 3 of 15 public test files. PatenTEB rebuilt families from Lens "following the
  DAPFAM approach", so the two datasets draw from the same family pool.
- **Train overlap is likely but unmeasured.** Under the paper's 80/10/10 split, a pool family is about eight times more
  likely to sit in train than in test. Family-disjoint splitting means the 5 + 134 families seen as *test queries* are not
  in train; nothing can be said family by family about the rest without the train IDs.
- **Citation links are the bigger risk.** PatenTEB's `retrieval_IN/OUT/MIXED` training pairs are citation links built
  like DAPFAM's relevance labels. If a DAPFAM query–target pair is a training pair, PatEmbed has seen the answer.
  This cannot be checked until the training pairs are released.

## 4. Consequence for the program (until the train IDs are public)

- **PatEmbed stays "possibly contaminated" on DAPFAM.** B53.0's patembed-base result (nDCG@100 ALL 0.366, above every
  baseline in the DAPFAM paper) must not be presented as a fair zero-shot number.
- **For G04:** headline DAPFAM comparisons use routes without this risk (BM25, Qwen3-Embedding, Arctic). PatEmbed is
  reported separately with this caveat.
- P1 (Challenge-1M, USPTO 2001–2018 citations) is a different source; this audit says nothing about P1 overlap.

## 5. Options (owner)

1. Accept the partial audit and the caveat above (no cost). **Recommended.**
2. Download the other 12 public PatenTEB test splits (gated with automatic approval; size not yet checked). This only raises the lower
   bound; it cannot prove absence from train. It needs a per-item download approval.
3. Ask the PatenTEB authors for the train/validation family IDs (a message on the owner's behalf; owner's call).
