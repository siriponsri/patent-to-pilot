# HT-NEXT-056 — DAPFAM BM25 full baseline

Status: `PASS_OFFLINE_DAPFAM_RETRIEVAL_DIAGNOSTIC`

Run ID: `luna-long-run-20261030-dapfam-bm25-20261030`

## Objective

Run the bounded DAPFAM citation-based patent-family retrieval diagnostic after the DuckDB CLI became available locally. This package is separate from HT-T1 semantic device-product relevance evaluation.

## Scope and inputs

- Dataset: `datalyes/DAPFAM_patent`, pinned revision `a59a74ce31384165065af1823a83c6f94ccafd48`.
- License boundary: CC BY-NC-SA 4.0, research-only; raw corpus, queries, and qrels remain under the ignored research-only input boundary.
- Corpus: `45,336` rows; `1,149,928,014` bytes; SHA-256 `469fe8e04d8bd8775a1116eccf0983e570a03444bef9c6e14c97aabafb7526d6`.
- Queries: `1,247` rows; `62,667,355` bytes; SHA-256 `b5ad91a650349a0096911fadcb7bc35a0399eb12d1470fb2601d73af5fc2bcbe`.
- Qrels: `49,869` rows; `828,375` bytes; SHA-256 `e51ae4e13abee0fc7523560ecddd272bc85dc98befc8ab4466155a0c2d2d4f74`.
- All qrel query IDs join to queries and all qrel target IDs join to corpus.

## Method

- Runner: `scripts/healthtech/run_dapfam_bm25.py`.
- View: title plus abstract for both queries and targets.
- Tokenizer: lowercase Unicode word tokens using `re\\w+`.
- Scorer: deterministic sparse BM25 implementation checked against `rank_bm25.BM25Okapi` on an authored fixture.
- Parameters: `k=100`, `k1=1.5`, `b=0.75`, `epsilon=0.25`.
- Tie-break: descending score, then stable corpus order.
- Evaluation: qrels-only; unlisted query-target pairs remain unjudged and are not treated as negatives.

## Results

Full output: `results/healthtech/ht-dapfam-bm25-20261030-r2/`.

- Status: `PASS`.
- Ranking rows: `1,247`; every query has `100` ranked candidates.
- All-qrels Recall@100: macro `0.21398467432950194`; micro `0.2136868707128244`.
- All-qrels nDCG@100: macro `0.19229519072532472`.
- Positive qrels: `24,929`; hits at 100: `5,327`.
- IN positive recall: macro `0.26443618868429536`; micro `0.2522800972841508`.
- OUT positive recall: macro `0.08343384071280348`; micro `0.06701328711727325`.

Synthetic smoke output: `results/healthtech/ht-dapfam-bm25-smoke-20261030-r2/`. It passed with `4` candidates, `2` queries, and `3` qrel pairs. The smoke is an engineering fixture only.

## Verification

- Targeted tests: `5 passed` in `tests/test_healthtech_dapfam_bm25.py`.
- Compile check: `python -B -m py_compile` passed for runner and test.
- Integrity checks: counts, unique query IDs, 100-result width, input bytes/SHA-256, output presence, and zero provider calls all passed.
- Canonical machine-readable receipt: `verification.json`.
- Continuation note: `NEXT_ACTIONS.md`.

## Boundaries

- This diagnostic does not create semantic device-product labels and does not update the HT-T1 denominator, holdout membership, company/family grouping, or `UNJUDGED` policy.
- Citation-based DAPFAM qrels are not clinical suitability, approval, FTO, patent-validity, investment-merit, or exhaustive-recall evidence.
- The result is an offline lexical component diagnostic, not HT-B4 and not an adaptive or provider result.
- No provider calls, network acquisition, credential reads, restricted payload transfer, or paid cost occurred.
- Raw DAPFAM inputs are not copied into this audit directory.

## Revision and working-tree note

- Source HEAD used by the runner: `b20844f1dcf1eb98ef2639ef88dac8a3900f47b2`.
- The runner and test were untracked working-tree files during the run; their hashes are recorded in `verification.json`.
- Existing unrelated dirty and untracked project files were preserved.
