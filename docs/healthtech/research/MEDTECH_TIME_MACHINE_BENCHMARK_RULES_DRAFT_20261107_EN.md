# Medtech time-machine benchmark (MTM): rules (DRAFT for owner approval, 7 Nov 2026)

- **Status:** DRAFT. Nothing in this file is frozen yet.
  - Items marked ⚙ are fixed after a free dry run or a small pilot.
  - The whole file is then frozen by a commit that says FROZEN, before any query brief, ranking or score exists.
- **Background:**
  - The dev probe on DAPFAM passed `GO_SHOCK` on n = 25 ([audit](../audits/ptp-time-machine-dev-probe-20261107/README.md)).
  - The BigQuery population count (tm02, [audit](../audits/ptp-medtech-tm-bigquery-20261107/README.md)) found 59,020 US device grants from 2010 to 2023 that qualify.
- **Related documents:**
  - data plan: [MEDTECH_TIME_MACHINE_DATA_PLAN_DRAFT_20261107_EN.md](MEDTECH_TIME_MACHINE_DATA_PLAN_DRAFT_20261107_EN.md);
  - the independent confirmation on DAPFAM test: [Amendment 1 draft (E6)](SOLUTION_SCOUT_PROTOCOL_AMENDMENT_1_DRAFT_20261107_EN.md).

## 1. Question

A medtech problem is described without its solution, and only documents that existed at the invention date are searchable. How often does a search show, in the first k results, an **older patent from another field** that the **examiner** later cited against the invention? How does a plain search compare with a cross-field lane?

## 2. Units and source

- **Source:** Google Patents Public Data (`patents-public-data.patents.publications`), read through `scripts/healthtech/bq_probe.py`. Every query is dry-run first and stays under the owner's byte cap.
  - Every label and ID can be rebuilt from USPTO public-domain data.
  - ⚙ The SEA semantics are cross-checked against one USPTO grant XML file before the freeze; that download needs owner approval.
- **Family level:** at most one query per `family_id`, the earliest-granted member. Targets and corpus documents are also deduplicated by `family_id`. This stops continuations and divisionals, which share text and citations, from counting twice or crossing splits.
- **Invention date T(q):** the query's earliest priority date. **Document date:** the earliest priority date of the target or corpus document.

## 3. Queries

- US utility grants (B1/B2) with at least one CPC subclass in A61B, A61F, A61G, A61H, A61J, A61L, A61M or A61N (devices; A61K/A61P/A61Q, i.e. drugs and cosmetics, are excluded).
- An English title and abstract must be present.
- The query needs at least one target, per §4.

## 4. Targets G(q) (the gold)

G(q) is every family that meets all of these:
1. It is cited in q's citation list with a category containing **SEA** (examiner-cited).
2. It is a US publication with an English abstract.
3. It shares **no** 3-character CPC code with q, comparing every CPC code of both (the IPC3-equivalent rule used by DAPFAM).
4. Its priority date is at least **5 years** before T(q).

Unjudged documents are not negatives. Results are known-link hits, not exhaustive recall.

## 5. Split, sampling and leakage control

| Split | Query grant years | Sample |
|---|---|---|
| dev | 2010–2016 | 2,000 queries |
| — (buffer, unused) | 2017–2018 | — |
| test | 2019–2023 | 2,000 queries |

- **Order:** queries are sampled by sha256(`20261107:` + publication_number) order within each split, after family deduplication.
- **Family-disjoint:** a test query whose family also has a member among the dev candidates is dropped.
- **Test is sealed:** test briefs, rankings and scores are produced only after the method is frozen on dev, and the analysis runs once.
- ⚙ **Sample size:** 2,000 per split gives a 95% CI half-width of about ±0.02 on a hit rate. It may be lowered if the brief-generation time (§7) does not fit the V100 window.

## 6. Search corpus

- **Contents:** every target family of the sampled dev and test queries, plus **distractor** families.
- **Distractors:** US families with an English abstract, sampled to match the targets' joint distribution of (priority year, CPC section).
  - Matching stops the targets standing out by age or field alone.
  - ⚙ The total is about **500,000 families** (primary) and about 100,000 (sensitivity). Absolute hit rates fall as the corpus grows, so the size is always reported beside them.
- **Per-query time filter:** documents with a priority date after T(q) are removed before ranking. The query's own family is removed.
- **Document text:** ⚙ title + abstract (primary), plus the first claim if a dry run shows the claims column fits the owner's cap. One unit per family, using the representative member with the longest abstract.

## 7. Query text (what the user would type)

| View | Text | Role |
|---|---|---|
| **P** (primary) | A problem brief from Qwen3-8B (rev `b968826d…`), greedy decoding, the frozen prompt `ptp-solution-scout-v1`, `PROBLEM` field only. Input: the query's title, abstract and first claim. A failed generation (outside 25–120 words) is not retried and scores 0 | Primary |
| T | Title only, no LLM | Secondary |
| A | The full abstract, which contains the solution | Leakage reference only |

- **Stated limitation:** P is written from the patent itself, so it may carry mechanism words.
- **Leakage check:** the share of P briefs whose words overlap each target's CPC-specific terms above a fixed threshold. It is reported, but no decision rides on it.
- ⚙ **Budget:** about 4,000 short generations, roughly 3–4 V100 hours, within or after the GPU window. The current window ends 15 Nov 2026 16:59 UTC.

## 8. Retrievers and arms

- **Retrievers:** PatEmbed-large dense (rev `2d5c0f92…`), one vector per unit; BM25 (secondary).

| Arm | Pool |
|---|---|
| **U** | The time-filtered full corpus |
| **X** | The other-fields lane: U minus every family sharing a 3-character CPC code with q |
| **M** | U[:10], then X, deduplicated, to k |

- **Dev only:** new lane or reranking methods may be developed on dev and compared with this frozen baseline. Every variant tried is logged, and at most **4** are carried into the test freeze.

## 9. Measures and statistics

- **Primary:** hit@20 (at least one member of G(q) in the first 20).
- **Secondary:** recall@20, hit@100, MRR@100, the median priority gap of hits, the CPC sections of hits, and results by grant year.
- **Statistics:** paired query bootstrap, 5,000 resamples, seed `20261107`. Contrasts: X − U, M − U, and each dev-selected method − U on test.

**Pre-declared reporting on test:**

| Statement | Allowed only if |
|---|---|
| "a plain search shows an older cross-field document in the first 20 for a% of medtech problems; a cross-field lane raises it to b%; the documents are a median of c years older" | X − U on hit@20 has a 95% lower bound > 0 |
| A method claim (better than the lane) | method − X on hit@20 has a lower bound > 0 after Holm correction across the carried-forward methods |

- In every case the paper states that the lane uses the same rule as the target definition, so part of X − U holds by construction.
- Corpus size, citation incompleteness and the brief-leakage risk are stated with every headline.

## 10. Outputs and release

- **Private:** texts, briefs and rankings in `../_private_artifacts/healthtech/medtech-time-machine/`.
- **Git:** aggregates, hashes, SQL, code and receipts only.
- **Release (after a terms check):** query and target publication numbers, labels, the split, seeds, SQL and code. These can be rebuilt from USPTO public-domain data; no Google-derived text is released.

## 11. Steps and approvals

| # | Step | Needs |
|---|---|---|
| 1 | tm03 dry runs: text-column costs; sampling SQL for queries, targets and distractors | Free; any run over the cap needs the owner |
| 2 | USPTO pilot XML: check SEA = "cited by examiner" | Owner approval for one download (about 100–300 MB) |
| 3 | Fix the ⚙ items, then the **FREEZE commit** | Owner approval |
| 4 | Extract texts (tm03 runs) | Owner approval of the byte totals |
| 5 | V100: briefs, then encoding | GPU window |
| 6 | Dev: baselines and up to 4 method variants | — |
| 7 | Test freeze of the methods, then one test run | — |
| 8 | Audit, and the paper section | — |
