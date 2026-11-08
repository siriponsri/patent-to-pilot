# MTM phase-3 audit: current results, plan, and literature check (9 Nov 2026)

- **Status:** AUDIT, documentation only. Nothing was trained or scored, and no test file was read.
- **Owner request (9 Nov 2026):** before any phase-3 run, audit the plan and the current results, with a thorough literature search. The GPU window is now 31 Dec 2026.
- **Scope:** the MTM benchmark build, the dev results of phases 1b and 2, the phase-3 draft (3a–3e), and DAPFAM as a second benchmark.
- **Inputs:**
  - read-only dev diagnostics on dr-train (dev labels only; counts and aggregates only);
  - two independent web reviews (citation verification and literature on first-stage recall);
  - the owner's ChatGPT Deep Research report (not committed).

## A. Findings on the current benchmark and results

### A1. The corpus is enriched with cited documents. This affects any citation-derived method (critical for 3c/3d)

The corpus has 899,838 families: 8,518 targets (0.95%), 442,886 matched distractors and 448,434 uniform distractors. The distractors are matched to the targets on priority year and CPC section only, not on citation count.

Every target, by definition, was cited by a US device grant. Most real documents that device examiners cite are absent from the corpus unless they happen to be a benchmark target.

A method that uses "was cited by an earlier device patent" therefore gains partly from how the corpus was built, not from relevance. This is the degree/popularity bias described for link prediction by Aiyappa et al. (arXiv 2405.14985). DAPFAM has the same "cited targets plus random negatives" design.

Text-only methods (BM25, dense, the rerankers) are much less exposed. The required controls are listed in section C.

### A2. The dev/test split is temporal, which enables time-safe training

`tm03_build_mtm.sql` assigns:

- dev to grants from 2010–2016;
- test to grants from 2019–2023.

Training pairs taken from US device grants of 2001–2009 are therefore earlier than every benchmark query. Pairs from 2001–2018 are earlier than every test query.

No published patent retriever we found was evaluated with a temporal split and a per-query priority-date filter. That supports MTM's novelty as a benchmark.

### A3. The V4 gain survives a cluster bootstrap

- Queries can share targets. 64 targets are shared among dev queries, which forms 1,924 clusters; the largest has 4 queries.
- Resampling clusters (5,000 resamples, seed `20261107`), V4 − X on P/main hit@20 is +0.0171 [+0.0101, +0.0242]. The per-query bootstrap gave [+0.0101, +0.0247].

### A4. The P briefs carry little leakage risk

- The MTM brief inputs hold title and abstract only. The description field is empty for all 1,985 dev queries, so P is an LLM paraphrase of the abstract.
- No brief contains a patent-number pattern. 10 of 1,985 use prior-art wording such as "conventional" or "prior art".
- The order T 0.129 < P 0.180 < A 0.251 (hit@20, X, main) is as expected.

### A5. The exposure ceiling, which motivates phase 3

Share of dev queries (P/main, X) with at least one target in the top k:

| k | 1 | 10 | 20 | 30 | 50 | 100 | 200 |
|---|---|---|---|---|---|---|---|
| X | 3.5% | 12.7% | 18.0% | 20.8% | 25.7% | 31.3% | 38.8% |

- 61% of queries have no target in the top 200.
- The ideal reordering of the top 30 gives 20.8%. V4 reached 19.7%, which is about 61% of the reorderable headroom.
- Even the abstract query A reaches only 49.7% at k = 200.

### A6. Earlier queries rarely re-cite the same target

2.8% of dev queries have a target that an earlier dev query also cited (1.4% with a 36-month lag). 4,091 distinct dev targets; 64 are cited by two or more dev queries. This uses a pool of only about 2,000 queries, so it is a weak lower bound for citation reuse across all device grants.

### A7. Possible look-ahead in PatEmbed-large (a benchmark-wide limitation)

PatEmbed-large was trained on patent citation data for PatenTEB, which has family-level splits and no time split. Some MTM pairs, especially test pairs from 2019–2023, may already be in its training data. That would inflate the baseline and every method built on it.

To do:

- find out whether PatenTEB publishes its training-pair identifiers, and if so, check the overlap with dev pairs;
- a test-pair overlap check reads test labels, so it needs separate owner approval.

### A8. External consistency

The 22-model benchmark (Yousefiramandi & Cooney, arXiv 2605.24297) also found that BGE-reranker-v2-m3 hurt a strong first stage (WIPO corpus, 0.1970 → 0.1295 nDCG@10). That matches our V3/V3b result.

### A9. Statistics and process

- **Already in place:**
  - the analysis scripts refuse `--split test`;
  - CV out of fold handles selection within each method;
  - the test carry-forward uses Holm;
  - all dev results are exploratory.
- **The phase-1 defect** (the query prefix in BM25 and the reranker) is fixed and covered by a unit test. Any new query channel needs the same kind of test.

## B. Literature check of the phase-3 candidates (verified sources)

### Citation chasing (3c)

- **Gobeill et al., TREC-CHEM 2010.**
  - Promoting patents cited by the top results raised MAP from 0.043 to 0.261, and Recall@500 from 0.31 to 0.62, on USPTO chemistry.
  - On CLEF-IP it gave only about +3%. The authors explain the difference by "inter-connection": 70% of a topic's cited patents link to each other on USPTO chemistry, against 8% on CLEF-IP.
  - Restricting the method to earlier-filed patents cost about 15%.
- **Mahdabi & Crestani, ACM TOIS 2014.**
  - Citation-graph expansion did not significantly beat the text baseline on Recall@1000 on CLEF-IP 2010/2011. For example, the baseline scored 0.6105 against 0.567–0.585 for the citation runs.
- **Gap:** we found no study of examiner or art-unit citation reuse across similar applications measured as recall.
- **Conclusion:** citation chasing is promising only if inter-connection is high, and it must be measured on MTM dev under the time filter before any build.

### Dense PRF (3a)

- Vector (Rocchio) PRF is cheap and training-free (Li et al., TOIS 2023).
- Its gain depends strongly on the quality of the feedback documents (Li et al., SIGIR 2022). ANCE-PRF gave about +5% R@1K on TREC DL.
- **No patent study was found.** On MTM the top 3 contain a target for only about 4–10% of queries, so query drift is likely. Keep α ≤ 0.3: the original query should keep most of the weight.

### Citation fine-tuning (3d)

- **PaECTER** (PLOS ONE 21(10): e0358188, 2026; weights Apache-2.0) trains on EPO search-report citations with second-order hard negatives.
- **Yousefiramandi & Cooney:** domain fine-tuning *hurt* DAPFAM cross-domain retrieval in 5 of 8 model × recipe cases.
- **RocketQA:** mined hard negatives are often unlabeled positives (about 70% on MS MARCO). EPO practice also cites only one of several equivalent documents.
- **Conclusion:** possible, but it needs:
  - time-split training;
  - exclusion of all benchmark families;
  - false-negative filtering;
  - the controls in section C.

### Other candidates

- **AutoIndex** (arXiv 2607.18603): its dense +18.3% R@100 comes from one StackExchange (CRUMB) task, not patents. Transforming 900k documents with an 8B LLM would take about 34 days on one V100. Dropped.
- **PHAGE** (arXiv 2605.10073): no public weights or code, and its DAPFAM OUT nDCG@100 (0.062) is below patembed-large's (0.069). Dropped.
- **ColBERTv2/PLAID, SPLADE, doc2query:** general-IR evidence only. Kept in reserve.

## C. Required changes to the phase-3 plan

1. **3b becomes a gating probe with four measures** (BigQuery, citation columns only; estimated ~35 GiB, inside the free tier). All four use dev labels only.
   - (i) **Reach:** the share of dev queries with a target that the examiner of an earlier-granted US device patent cited, where the grant was published before T(q).
   - (ii) **Inter-connection,** in Gobeill et al.'s sense.
   - (iii) **A popularity-null baseline:** rank lane-X corpus families by the number of earlier device-patent SEA citations before T(q), with no query text.
   - (iv) **Outside-corpus share:** the fraction of chased references that are not in the corpus, which indicates inflation.
2. **Go/no-go rule for 3c, fixed before the probe:**
   - **Go** only if reach exceeds the current hit@200 (38.8%) by at least 10 points, **and** the popularity null reaches less than half of the reach at k = 200.
   - Otherwise 3c is reported as a negative feasibility result.
3. **An open-candidate protocol for 3c.**
   - Chased references outside the corpus keep their rank positions as unjudged non-relevant documents. They are never silently dropped.
   - The popularity null is reported next to every citation-derived result.
4. **A new robustness corpus view, "cited distractors"** (BigQuery pull plus a small encode).
   - It adds US families that device grants examiner-cited before 2019 but that are not benchmark targets, matched to the target strata.
   - Every phase-3 method, including V4 and the baseline, is reported on it.
5. **Safeguards for 3d:**
   - training pairs come only from 2001–2009 grants;
   - all benchmark query and target families are excluded;
   - mined hard negatives are filtered for likely false positives;
   - DAPFAM OUT is reported zero-shot after a decontamination check;
   - the encoder licence choice stays with the owner: PatEmbed is CC BY-NC-SA 4.0; Qwen3-Embedding and PaECTER are Apache-2.0.
6. **BigQuery timing:** the 3b probe can run in November. The large text pulls (cited distractors, 3c neighbour index, 3d training pairs) can wait for the December free-tier reset, since the GPU window now runs to 31 Dec.

## D. DAPFAM as a secondary benchmark (verified facts)

- **Data:** 1,247 query families and 45,336 target families; about 5,193 positive OUT relations.
- **IN/OUT:** OUT means the target shares no IPC3 with the query.
- **Metrics:** only nDCG@100 and Recall@100, for ALL/IN/OUT (arXiv 2506.22141 v2; *Array* 29:100720, 2026).
- **Published OUT baselines:**
  - R@100: BM25 passage 0.152, dense passage (Arctic) 0.154, hybrid RRF 0.165.
  - nDCG@100: 0.059–0.063.
  - patembed-large OUT nDCG@100 is 0.069 (PatenTEB Table 16). Its 0.377 is the ALL figure.
- **Construction:** cited targets plus about 20 random non-cited families per query. Queries need at least 100 citations. Citation-derived methods are therefore not applicable on DAPFAM.
- **Not stated in the paper:** whether ranking runs over the full 45,336 pool. Check the released code before calibrating.
- **Licence:** the HF dataset (`datalyes/DAPFAM_patent`) is CC BY-NC-SA 4.0; the *Array* article is CC BY 4.0.
- **Use:** report the transferable methods (3a, 3d, V4) on the project's sealed DAPFAM test split (773 queries), after reproducing the published baselines on all 1,247 queries.

## E. Owner items

- **DOI for the published IEEE paper:** a web and Crossref search did not find it, so take the DOI from the IEEE publication email or Xplore before citing.
- **Google Patents Public Data terms:** a 2017 Google Cloud blog attributes the data to IFI CLAIMS and Google under CC BY 4.0. No current terms page was found, so check before releasing derived data.
- **Approval** of the revised phase-3 order:
  1. 3a PRF;
  2. the 3b gating probe;
  3. the cited-distractor view;
  4. 3c, if it passes the gate;
  5. 3d with safeguards;
  6. DAPFAM;
  7. freeze at most 4 methods for the single test read.

## Sources (verified by the reviewers; links checked)

- **DAPFAM:**
  - https://arxiv.org/abs/2506.22141
  - DOI 10.1016/j.array.2026.100720
  - https://huggingface.co/datasets/datalyes/DAPFAM_patent
- **PatenTEB:**
  - https://arxiv.org/abs/2510.22264
  - https://huggingface.co/datalyes/patembed-large
- **PaECTER:**
  - https://arxiv.org/abs/2402.19411
  - https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0358188
- **The 22-model benchmark:** https://arxiv.org/abs/2605.24297
- **AutoIndex:** https://arxiv.org/abs/2607.18603
- **PHAGE:** https://arxiv.org/abs/2605.10073
- **Gobeill et al. 2010:** https://trec.nist.gov/pubs/trec19/papers/univ.geneva.chem.rev.pdf
- **Mahdabi & Crestani:**
  - TOIS 2014, DOI 10.1145/2651363
  - CIKM 2014, DOI 10.1145/2661829.2661899
- **CLEF-IP 2009:** https://ceur-ws.org/Vol-1175/CLEF2009wn-CLEFIP-RodaEt2009.pdf
- **Aiyappa et al.:** https://arxiv.org/abs/2405.14985
- **Dense PRF:**
  - ANCE-PRF: https://arxiv.org/abs/2108.13454
  - Li et al.: https://arxiv.org/abs/2108.11044 and https://arxiv.org/abs/2205.05888
- **RocketQA:** https://arxiv.org/abs/2010.08191
- **IPRally graph transformer:** https://arxiv.org/abs/2508.10496
- **Kuhn, Younge & Marco 2020:** RAND J. Econ. 51(1):109–132
