# MTM dev baseline — query views P, T and A (7–8 Nov 2026)

## Update 8 Nov: primary view P (`dev-PTA.json`, `receipt-P-dev.json`)

- **What ran:**
  - Briefs P-dev: Qwen3-8B on V100, frozen prompt, 1,985 briefs, **0 failed**. Ran 20:09–22:36Z.
  - Dense P-dev: ended 22:40Z, exit 0.
  - `analyze_mtm.py --split dev --query-views P,T,A`: exit 0, written to a new file.
  - The T and A means in `dev-PTA.json` are identical to `dev-TA.json`.
- **Corpus view main, query view P:**

  | Arm | hit@20 | recall@20 | hit@100 | MRR@100 | median gap (years) |
  |---|---|---|---|---|---|
  | U | 0.084 | 0.053 | 0.205 | 0.028 | 10 |
  | X | 0.180 | 0.119 | 0.313 | 0.065 | 10 |
  | M | 0.145 | 0.093 | (=hit@20) | 0.029 | 10 |

- **Contrasts:** X − U = **+0.096 [0.084, 0.109]**; M − U = +0.062 [0.051, 0.072].
- **Sensitivity views, hit@20 for U / X / M:**
  - small: 0.216 / 0.313 / 0.276
  - matched: 0.104 / 0.204 / 0.168
  - uniform: 0.154 / 0.256 / 0.211
  - X − U is +0.097 to +0.102 in every view.
- **Reading (dev):**
  - **The brief beats the title.** U rises from 0.074 to 0.084, and X rises from 0.129 to 0.180.
    - The lane gain grows with the brief: X − U is +0.096 with P against +0.055 with T.
  - **Gate 1 is still the bottleneck.** A plain search finds an older cross-field target in the top 20 for only about 8% of problems.
  - **There is reranker headroom (gate 3).** X hit@100 is 0.313 against hit@20 of 0.180, so 13 points of queries have a target sitting in positions 21–100.
  - **The P brief may carry mechanism words** (rules §7). The descriptive leakage check is not computed yet.
  - **X − U holds partly by construction.**
- **Status:**
  - The test split is still sealed.
  - The job continues with label-free P-test briefs and test rankings (rules §14).

Status: **PASS (dev only).** The test split is still sealed. These numbers come from the dev split, so they can guide method choices on dev. They are not a headline result.

## What ran

- **Rules:** `docs/healthtech/research/MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md`, frozen at `7d317e7`.
- **Retriever:** PatEmbed-large dense, MaxP over 384/64-term TAC passages, depth 200, on a Tesla V100-SXM2-32GB on dr-train.
  - Model sha256: `234ea36a…`.
  - Corpus: 899,838 families, 1,553,678 passages.
  - Passage encoding took 31,218 s and was reused for view A. The passage-vector sha256 is in `receipt-A-dev.json`.
  - No labels were used: `labels_used: false` in both receipts.
- **Analysis:** `scripts/healthtech/analyze_mtm.py --split dev --query-views T,A`, run on dr-train with exit 0 in 67 s.
  - Paired query bootstrap, 5,000 resamples, seed `20261107`.
- **Size:** 1,985 dev queries and 4,159 query–target pairs. No ranking was missing in any view.
- **Files:**
  - `dev-TA.json` holds the aggregate means, contrasts and input sha256s.
  - `receipt-T-dev.json` and `receipt-A-dev.json` are the retrieval receipts.
  - Rankings and query text stay on dr-train and in the private artifacts. They are not in Git.

## Arms and views (from the rules)

- **Arms:**
  - **U** searches the time-filtered full corpus.
  - **X** is the other-fields lane: U minus every family that shares a 3-character CPC code with the query.
  - **M** is U[:10], then X, deduplicated, cut to 20. Because M stops at 20, its hit@100 equals its hit@20 by construction.
- **Query views:**
  - **T** is the title only (secondary).
  - **A** is the full abstract. It is a leakage reference only, because it contains the solution.
  - **P**, the primary view (a Qwen3-8B problem brief), is still being generated. Its results will follow in `dev-PTA.json`.

## Results — corpus view `main` (primary)

| Query view | Arm | hit@20 | recall@20 | hit@100 | MRR@100 | median hit gap (years) |
|---|---|---|---|---|---|---|
| T | U | 0.074 | 0.045 | 0.166 | 0.024 | 10 |
| T | X | 0.129 | 0.086 | 0.251 | 0.051 | 10 |
| T | M | 0.110 | 0.070 | (=hit@20) | 0.024 | 10 |
| A | U | 0.146 | 0.091 | 0.288 | 0.050 | 11 |
| A | X | 0.251 | 0.169 | 0.429 | 0.106 | 12 |
| A | M | 0.215 | 0.143 | (=hit@20) | 0.052 | 11 |

Contrasts on hit@20 (95% paired bootstrap CI, 1,985 queries):

| Query view | X − U | M − U |
|---|---|---|
| T | +0.055 [0.045, 0.065] | +0.036 [0.028, 0.044] |
| A | +0.105 [0.092, 0.119] | +0.069 [0.058, 0.081] |

## Sensitivity views (hit@20 for U / X / M)

| Query view | small | matched | uniform |
|---|---|---|---|
| T | 0.179 / 0.250 / 0.224 | 0.088 / 0.154 / 0.130 | 0.124 / 0.200 / 0.171 |
| A | 0.309 / 0.425 / 0.391 | 0.173 / 0.281 / 0.241 | 0.236 / 0.350 / 0.308 |

- The direction is the same in every view: X > M > U.
- Absolute rates rise as the corpus shrinks, as the rules expect. Corpus size has to be reported beside any rate.

## Reading (dev, not a claim)

1. **Gate 1 is the bottleneck.** In Paper 53's terms, this is the gate that decides whether the target enters the list at all.
   - With titles (T), a plain search puts an older cross-field target in the first 20 for about 7% of queries.
   - Even within the first 100, it does so for only about 17%.
2. **The lane helps, but part of that holds by construction.**
   - X roughly doubles hit@20 on T, from 0.074 to 0.129.
   - X removes same-CPC3 families, and the targets are defined as no-shared-CPC3. So part of X − U is built in, and any paper must say so (rules §9).
3. **Mixing costs a little.**
   - On dev, M sits between U and X.
   - Keeping U's top 10 trades some cross-field hits for same-field results.
4. **There is headroom for gate 3.** Gate 3 is the reranker's job: pulling a target that is in the list up into the top 20.
   - For X on T, hit@100 is 0.251, nearly twice hit@20 (0.129).
   - So about 12 points of queries have a target in positions 21–100 that a reranker could move up.
   - This is the gate where Paper 53's prompt-sensitivity question applies.
5. **The hits are old.** The median hit is 10–12 years older than its query.
6. **View A is a leakage reference only.** It shows what a perfect description of the solution would give, so it bounds what a better brief could reach. It is not a user-facing result.

## Limits

- These are dev results only. The primary view P is not in yet. The test split is still sealed: no `--split test` run until the methods are frozen with owner approval (rules §14).
- Examiner citations are incomplete, so a "miss" can be a relevant document the examiner did not cite. Unjudged is not negative.
- X − U holds partly by construction (see reading 2).
- There is one retriever (dense). BM25 is secondary and has not run.
