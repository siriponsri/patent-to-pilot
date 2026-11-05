# Novelty check: cross-industry solution scout (5 Nov 2026)

**Candidate direction.** Input: a short technical problem brief, not a full patent. A local Qwen3-8B abstracts the brief into a required function and retrieves through two lanes:
- an in-domain lane;
- a cross-domain lane, restricted to families that share no IPC3 code with the query.

The output is an evidence dossier with a transfer rationale.

**Evaluation.** Strict-OUT recall at a 200-family budget on DAPFAM.

**Business use.** Technology scouting and open-innovation search.

Sources: the five owner-supplied papers (files 36–40), eight new open-access papers (files 51–58), the earlier scan ([ORG_ADAPTIVE_RELATED_WORK_SCAN_20261105_EN.md](ORG_ADAPTIVE_RELATED_WORK_SCAN_20261105_EN.md)) and a web search. This is not a systematic review.

## Verdict

The combination is novel; no single component is.

### What is new

No work found combines:
- a short brief as input;
- LLM function abstraction on an open 8B model;
- a hard IPC-disjoint retrieval lane;
- quantitative, citation-grounded evaluation at a fixed budget on an open benchmark.

Every earlier abstraction-to-far-domain system was evaluated only by case studies or user studies:
- functional-vector design-by-analogy (Murphy, Fu, Wood et al. 2014);
- InnoGPS knowledge distance (Luo, Sarica, Wood 2021);
- problem-similarity solution reuse (Ni, Samet, Cavallucci, *J. Intell. Manuf.* 2022);
- SAO cross-domain technology mining (Yu et al., *IJPR* 2023);
- MUSE (Sweed et al., EMNLP 2025).

Every quantitative cross-domain benchmark (DAPFAM, PatenTEB, the Clarivate 22-model study) tests raw patent fields with encoders, without LLM rewriting.

### What we must not claim

- First cross-domain patent retrieval: that is DAPFAM.
- First LLM abstraction for far analogies: that is MUSE.
- First problem-to-solution patent retrieval: that is Ni et al. and PatenTEB problem2solution.

### Positioning

The first citation-grounded, budget-controlled test of whether LLM function abstraction recovers cross-domain prior solutions from a short problem brief.

## Closest works and how we differ

| Work | Overlap | Difference |
|---|---|---|
| MUSE, EMNLP 2025 (file 51) | LLM functional graph over 500K patents; free-text problem → far-domain inspirations | User study only; no retrieval metric, dense baseline or citation ground truth |
| Ni, Samet, Cavallucci 2019–2022 | Same premise: similar problems across domains share solutions | Word2vec/XLNet similarity; case study; no IPC-controlled benchmark |
| Elmi et al. 2026, CPC-aware LLM query expansion (file 39) | Problem-statement queries + LLM rewrites + CPC | CPC is a **same-domain drift guard**: rewrites that change the predicted section are rejected (pp.154, 159). It has no cross-domain evaluation, uses private Turkish aviation data, and its gain nearly vanishes after reranking (R@50 0.47 → 0.48) |
| Luo, Sarica, Wood 2021 (file 55) | Class distance selects near- or far-field patents | Ideation guidance; case studies |
| DAPFAM (file 01; *Array* 2026) | Our benchmark. Title, T+A, T+A+C and keyword query views | No LLM and no rewriting. Title-only OUT NDCG@100 is 0.050 vs 0.059 for T+A+C (p.22): weak queries lose only modestly |
| Sophia-Bench / QaECTER 2026 (file 52) | LLM summaries as queries match or beat original fields (NDCG@10 0.539 vs 0.517) | In-domain only |
| Jiang et al. 2026, LLMs in the patent lifecycle, WPI 87:102506 (file 36) | Lists Kim, Park & Lee 2026 (function-oriented solutions from unrelated fields; topic models), Nomaguchi et al. 2025 (LLM problem-solution pairs) and TRIZ-GPT | The review names no retrieval benchmark or ranking metric. About 80% of reviewed studies use closed data (pp.9, 11). Scouting and open innovation are absent |

## Risks that change the design

1. **The weak-query headroom may be small.**
   - In DAPFAM, title-only and keyword queries lose only about 8–15% OUT performance against full fields (pp.22, 32, 34).
   - LLM help is therefore not assured. A dev-only feasibility check with a pre-declared stop rule must come before any protocol freeze.
2. **The LLM may recall the target patent (knowledge leakage).**
   - Yoon et al. 2025 (file 53) show LLM query-expansion gains can come from what the model has memorized.
   - Needed controls: a probe for target-identifier or title recall, and results split by family date relative to the Qwen3 training cutoff.
3. **Brief construction may leak solution terms.**
   - A brief cut from the patent's own description can carry solution vocabulary.
   - Use title-only and a constrained problem-only extraction as two brief types. Report vocabulary overlap with the target.
4. **Citation pairs are a proxy.** A cross-domain citation is evidence of relatedness, not of transferability. State this in the paper.
5. **Embedding training leakage.** patembed's retrieval_OUT training data may overlap DAPFAM. Access to the gated HF dataset is granted to the owner's account; the overlap check is still pending.
6. **No business validation.** The PoC is a technical demonstration only, under the project's no-external-validation rule. DAPFAM has no assignee field, so partner suggestions would need another public source.

## Baselines this direction must beat (dev first, test once)

1. Dense retrieval on the brief.
2. BM25 on the brief.
3. DAPFAM's keyword-query view.
4. A cross-domain lane on the raw brief, without an LLM.
5. Untuned RRF with K = 60. Searchformer shows the result hardly depends on k (file 37, p.11).

## Still to obtain

| Item | Priority |
|---|---|
| DAPFAM, published *Array* version. The owner's download is the arXiv v2 preprint (identical bytes to file 01). https://www.sciencedirect.com/science/article/pii/S2590005626000433 | Medium |
| Ayaou, Chibane, Koch, Cavallucci, "Leveraging information retrieval pipelines for inventive design", TFC 2024 (IFIP AICT) | Highest: same authors as DAPFAM |
| Ni, Samet, Cavallucci, *J. Intell. Manuf.* 33(6) 2022, doi 10.1007/s10845-021-01749-4, and the 2019/2020 TFC chapters | High |
| Yu et al., *IJPR* 61(21) 2023, doi 10.1080/00207543.2022.2151659 | High |
| Kim, Park & Lee, *Adv. Eng. Inform.* 70 (2026) 104116 | High |
| Guarino & Cavallucci, PatRIS, DEXA 2021 | Low |
| Russo, *IJPD* 2014 | Low |
| Technology-partner recommendation, *IPM* 63 (2026), doi 10.1016/j.ipm.2025.104458 | Low |
| Cavallucci / ICube publications 2025–2026, including TFC 2025 | Manual check: the DBLP page was blocked |
