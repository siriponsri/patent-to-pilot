# -*- coding: utf-8 -*-
"""IS2 short paper, English edition (paperkit content contract).

Faithful counterpart of content_th.py: same sections, numbers (paper_numbers.py), figures (English labels) and
references. The bilingual front matter (titles, authors, both abstracts, keywords, footnotes) is shared with the Thai
edition so the two files cannot drift apart.
"""
from content_th import (ABS_EN, ABS_TH, ADVISOR_FOOT_TH, AUTH_EN, AUTH_TH, AUTHOR_META, EMAIL, EQUATIONS, KW_EN,  # noqa: F401
                        KW_TH, REFS, TITLE_EN, TITLE_TH)
from fx import typeset
from paper_numbers import C, N_OUT, NUM as N, T1, T3, MINUS, localise

LANG = "en"
B = lambda t: (t, {"b": True})        # noqa: E731
SUB = lambda t: (t, {"sub": True})    # noqa: E731

H1 = ["First stage", "π@100", "Δπ@100 [95% CI]", "Gained/lost", "Holm p", "OUT R@100", "nDCG@100", "First OUT rank"]
H3 = ["First stage", "π@100", "Generic", "Patent-aware", "Claim-focused", "Scrambled", "BGE", "No rerank"]
t1 = localise(T1, "reference", "not tested")

BODY = [
    ("h1", "1. Introduction"),
    ("p", "Prior-art search in patent systems often has to find documents from another technology field that use the same "
          "mechanism under different vocabulary. A multi-stage retrieval system first collects candidates with a "
          "first-stage retriever and then reranks them with a model that accepts an instruction. The reranker can only "
          "reorder documents that are already in the candidate pool. If a relevant cross-domain document is not in the "
          "pool, no instruction can bring it up."),
    ("p", "Our first independent study (IS1) [1] asked whether patent-specific instructions help cross-domain reranking on the DAPFAM "
          "dataset [2] with a fixed candidate pool. Differences in mean strict OUT nDCG@100 (normalised discounted "
          "cumulative gain at 100, counting only cross-domain, or OUT, families as relevant) relative to the generic "
          f"instruction were close to zero (Patent-aware +0.0008, Claim-focused {MINUS}0.0007), and only 257 of 692 "
          "queries (37.1%) had a known cross-domain relevant family in the top 100. The IS1 committee made two "
          "comments. The first (K1) asked us to explain where the patembed-base first stage came from, to try BM25 or a "
          "hybrid, and to avoid causal conclusions from the decomposition equation. The second (K2) asked IS2 to change "
          "the first stage to test whether the limit really lies there, and to explain the benefit to users."),
    ("p", "IS1 used a single first-stage retriever, so it could not separate a property of the reranker from a "
          "property of the pool that patembed-base produced. This paper fills that gap with experiment B53, which "
          "changes only the first-stage retriever and holds everything else fixed, under a plan declared before any "
          "number was seen. We ask three research questions."),
    ("rq", "RQ1 How much does changing the first-stage retriever at equal depth (100) change the exposure of known "
           "cross-domain relevant families?"),
    ("rq", "RQ2 Do the differences between instructions change when the first-stage retriever changes?"),
    ("rq", "RQ3 How does pool depth (100, 200 and 1,000) relate to exposure?"),

    ("h1", "2. Background and Related Work"),
    ("h2", "2.1 DAPFAM and cross-domain retrieval"),
    ("p", "DAPFAM [2] is a family-level patent retrieval dataset with 1,247 query families and a target corpus of 45,336 "
          "families. Relevance is split into in-domain (IN) and cross-domain (OUT) by whether the query and the target "
          "share a three-character International Patent Classification (IPC) code. The original article reports that cross-domain results are much lower "
          "than in-domain ones, and that BM25 and RRF do not close this gap. Relevance labels come from citations and "
          "are incomplete, so an unlabelled OUT document may still be relevant."),
    ("h2", "2.2 First-stage retrievers"),
    ("p", "BM25 [3] is the standard lexical baseline. patembed is a family of patent-specific embedding models from the "
          "PatenTEB project [4], trained multi-task on 13 tasks. Arctic-embed-m-v2.0 [5] and Qwen3-Embedding [6] are "
          "general embeddings that perform well in retrieval. Reciprocal Rank Fusion (RRF) [7] is a widely used hybrid "
          "that needs no training. A reproducibility study of cross-domain retrieval in the legal and patent domains "
          "found that neural methods do not always beat BM25 and that results should be reported reproducibly [8]."),
    ("h2", "2.3 Rerankers and instructions"),
    ("p", "Qwen3-Reranker-0.6B [6], [9] scores a query and document pair under a configurable instruction, whereas "
          "BGE-reranker-v2-m3 [10] scores a plain text pair without one. Both can only reorder documents already in the "
          "candidate pool."),
    ("h2", "2.4 The accounting identity"),
    ("p", "Let π be the share of queries whose candidate pool contains a known relevant OUT family (exposed queries). "
          "When two instructions are compared on the same pool, unexposed queries score zero under both, so the mean "
          "difference over all queries follows equation (1)."),
    ("eq", 1),
    ("pi", ["Here Δ", SUB("all"), " is the mean difference over all queries and Δ", SUB("exp"),
            " the mean difference over exposed queries. Equation (1) is an accounting identity that holds by "
            "definition. It splits the size of an effect, but it says nothing about cause and effect between exposure "
            "and the instruction effect [1]."]),

    ("h1", "3. Methodology"),
    ("h2", "3.1 Data"),
    ("p", "We use DAPFAM revision a59a74ce (its data equal revision 780f4011). Queries and documents are rendered as TAC "
          "text (title, abstract and claims), as in IS1. Pairs with relevance_score above zero count as relevant. The "
          f"main cohort is the set of queries with at least one relevant OUT family: {N_OUT} queries (the IN cohort has "
          f"{N['n_in']} and the full set {N['n_all']}). The filter behind the 692-query IS1 cohort cannot be recovered, "
          "so this work is a re-implementation, not a replication."),
    ("h2", "3.2 Design"),
    ("p", "Fig. 1 summarises the design. Stage 1 changes only the first-stage retriever and measures the exposure of the "
          "top-100 candidate pool. Stage 2 applies the same reranker, instructions, text lengths and evaluation to the "
          "pool of every first stage, so any difference between experimental arms comes from the first stage alone. We froze the "
          "plan, endpoints and decision rules before any number existed (pre-declaration)."),
    ("h2", "3.3 First-stage retrievers"),
    ("p", ["The five core arms are F0 patembed-base @244ba452 with MIXED prompts, F1 BM25 (k", SUB("1"),
           " = 1.5, b = 0.75), F2 RRF(F1, F0), F3 Arctic-embed-m-v2.0 and F4 RRF(F1, F3). Three secondary arms were "
           "declared in advance for descriptive use: F0-OUT (patembed-base with OUT prompts), F6 patembed-large and "
           "F7 Qwen3-Embedding-0.6B. Every arm keeps the top 1,000; dense arms use exact inner product with text truncated "
           "at 512 tokens, F1 uses BM25 scores, and F2 and F4 fuse ranks with RRF."]),
    ("fig", "fig1_design.png", 6.5,
     "Fig. 1. B53 design. Only the first-stage retriever changes (solid box); the reranker, instructions and evaluation "
     f"are held fixed (dashed boxes). Stage 1 is measured on {N_OUT} OUT queries and Stage 2 compares instructions on "
     f"the common-exposed set C = {C}.", True),
    ("h2", "3.4 Reranker (Stage 2)"),
    ("p", "Stage 2 uses Qwen3-Reranker-0.6B @e61197ed with the four instructions of IS1 Table I: Generic, Patent-aware, "
          "Claim-focused and Scrambled (the Claim-focused words in shuffled order). Instruction texts are copied "
          "verbatim from the IS1 source. The score is the probability of the answer “yes”. Queries are "
          "truncated at 2,048 tokens and documents at 4,096 tokens. The controls are no reranking and BGE-reranker-v2-m3 "
          "without an instruction. The same reranker and instructions are applied to every first stage."),
    ("h2", "3.5 Endpoints and statistics"),
    ("p", "The primary Stage 1 endpoint is exposure, defined in equation (2)."),
    ("eq", 2),
    ("pi", ["Here n is the number of OUT queries (", str(N_OUT), ") and n", SUB("exp"),
            "(k) the number of queries with at least one known relevant OUT family in the top k. Secondary endpoints are "
            "π@200, π@1000, OUT Recall@100, the rank of the first OUT family and strict OUT nDCG@100 [11], which "
            "counts only OUT families as relevant. Contrasts against F0 use a paired bootstrap with 10,000 resamples "
            "(seed 20261119) [12] for the 95% confidence interval (CI), an exact McNemar test [13] for p, and the Holm correction [14] over "
            "the four core contrasts."]),
    ("p", "Stage 2 compares Patent-aware and Claim-focused against Generic under each of the five core first stages, "
          "10 contrasts in total, on the common-exposed set C: the queries exposed in the top 100 under every core arm "
          f"({C} queries), so that all arms are compared on the same queries. The CIs and p-values come from a paired "
          "bootstrap with 10,000 resamples, with Holm correction over the 10 contrasts. Results on all "
          f"{N_OUT} OUT queries are reported as descriptive."),

    ("h1", "4. Results"),
    ("h2", "4.1 Exposure at depth 100 (RQ1)"),
    ("tbl", f"Table 1. Exposure at depth 100, change against F0 and secondary endpoints (n = {N_OUT})", [H1] + t1,
     [1800, 760, 1950, 1050, 960, 900, 1050, 890], True,
     "Gained/lost: queries that moved from unexposed to exposed and back. CIs from a paired bootstrap; Holm over the "
     "four core arms. nDCG@100 is strict OUT nDCG@100; first OUT rank is the median rank of the first OUT family "
     "among exposed queries. The last three rows are descriptive secondary arms.", ["left"] + ["center"] * 7),
    ("p", f"Table 1 summarises Stage 1. F0 exposed an OUT family in the top 100 for {N['n_F0']} of {N_OUT} queries "
          f"(π@100 = {N['pi_F0']}). BM25 was {N['d_F1'][1:]} points lower than F0 (95% CI {N['ci_F1'][0]} to "
          f"{N['ci_F1'][1]}; {N['gl_F1'][0]} queries gained, {N['gl_F1'][1]} lost; Holm p < 0.001), Arctic-embed "
          f"{N['d_F3'][1:]} points lower and RRF(F1, F3) {N['d_F4'][1:]} points lower. RRF(F1, F0) was "
          f"{N['d_F2'][1:]} points higher than F0, but its CI ({N['ci_F2'][0]} to {N['ci_F2'][1]}) includes zero. The "
          "secondary endpoints OUT Recall@100 and strict OUT nDCG@100 order the core arms the same way as π@100."),
    ("p", f"The secondary arms point the same way: patembed-large showed no evidence of a difference from F0 ({N['d_F6']}) and "
          f"Qwen3-Embedding was lower ({N['d_F7']}). Switching only the patembed-base prompts to OUT raised π@100 by "
          f"{N['d_F0OUT'][1:]} points (95% CI {N['ci_F0OUT'][0]} to {N['ci_F0OUT'][1]}), a descriptive result outside "
          f"the confirmatory tests. F0's π@100 ({N['pi_F0']}) equals the 37.1% of IS1 only numerically: the cohorts "
          f"({N_OUT} vs. 692) and pipelines differ, and it is not a replication."),
    ("p", "The answer to RQ1 is that changing the first-stage retriever does change exposure, with clear drops for BM25 "
          "and Arctic-embed, but no core arm exceeded patembed-base significantly. This experiment therefore gives no "
          "evidence that BM25 or the RRF hybrids tested raise cross-domain exposure on DAPFAM."),

    ("h2", "4.2 Instruction effects under each first stage (RQ2)"),
    ("p", f"Fig. 2 shows the strict OUT nDCG@100 differences between instructions on the set C (n = {C}). All 10 "
          f"estimates are small and positive ({N['dmin']} to {N['dmax']}), every 95% CI includes zero, and no contrast "
          f"is significant after Holm correction. The smallest unadjusted p is {N['raw_p']} (F3, Claim-focused) and "
          f"the smallest adjusted p is {N['holm_min']}. Queries that improved and worsened are close in number, for "
          f"example {N['pa_F0']['wins']} against {N['pa_F0']['losses']} for Patent-aware under F0."),
    ("fig", "fig2_forest.png", 6.5,
     "Fig. 2. Instruction differences stay near zero under every first stage. Points are strict OUT nDCG@100 "
     f"differences of Patent-aware (circles) and Claim-focused (squares) against Generic on the set C (n = {C}); "
     "lines are 95% paired bootstrap CIs; W/L counts queries that improved or worsened, and Holm p is adjusted over all "
     "10 contrasts.", True),
    ("tbl", f"Table 2. Mean strict OUT nDCG@100 over all OUT queries (n = {N_OUT}; unexposed queries score 0), "
            "descriptive", [H3] + T3, [1800, 800, 1000, 1250, 1350, 1100, 900, 1160], True,
     "BGE is BGE-reranker-v2-m3 without an instruction; no rerank is the first-stage ranking itself.",
     ["left"] + ["center"] * 7),

    ("p", f"Table 2 reports means over all {N_OUT} OUT queries as descriptive results, with unexposed queries scored "
          f"zero. There is no evidence that the Scrambled instruction differs from Generic ({N['scr'][0]} to {N['scr'][1]}, "
          "given to four decimals because the values are so small, every CI including zero), although changing the instruction changes the nDCG@100 of "
          f"{N['resp'][0]}% to {N['resp'][1]}% of exposed queries. BGE-reranker without an instruction is below "
          f"Generic under every first stage ({N['bge'][0]} to {N['bge'][1]}, CIs excluding zero). Generic is "
          f"{N['norr'][0][1:]} to {N['norr'][1][1:]} above no reranking, with CIs excluding zero only for F3 and F4."),
    ("p", f"Absolute nDCG@100 under Qwen3-Reranker lies between {N['qwen'][0]} and {N['qwen'][1]} and follows the π@100 order of the arms. Equation (1) holds "
          "for every arm to four decimals, and the no-rerank column equals the Stage 1 strict OUT nDCG@100 (Table 1) "
          "for every arm, which confirms that both stages used the same data."),
    ("p", "The answer to RQ2 is that under every first-stage retriever, neither instruction differed significantly from "
          "Generic (no interaction test was run; each contrast was tested against zero). The near-zero instruction effect of IS1 is therefore not tied to the choice of "
          f"patembed-base in this setting. The upper CI bounds reach {N['ub'][0]} to {N['ub'][1]}, however, so this is "
          "not evidence that instructions have no effect, and effects of about 0.02 cannot be excluded."),
    ("h2", "4.3 Pool depth (RQ3)"),
    ("fig", "fig3_exposure.png", 3.0,
     "Fig. 3. Deeper pools raise exposure, but about a quarter of queries still have no known OUT family at depth "
     f"1,000. Points are π@k of the core first stages (n = {N_OUT}) at k = 100, 200 and 1,000.", False),
    ("p", f"In Fig. 3, going from depth 100 to 200 raises F0's π from "
          f"{N['pi_F0']} to {N['pi200_F0']} ({N['gain200_F0']} points), and depth 1,000 reaches {N['pi1000_F0']}. F0 "
          f"stays highest among the core arms at depth 1,000, while RRF(F1, F0), close to F0 at depth 100, falls behind ({N['pi1000_F2']}). "
          f"Even at depth 1,000, {N['none1000_F0']} of {N_OUT} queries ({N['none1000_pct']}%) have no known relevant "
          "OUT family under F0."),
    ("p", "The answer to RQ3 is that, descriptively, a deeper pool raises exposure more than changing the retriever at "
          f"the same depth (F0 from 100 to 200: {N['gain200_F0']} points, against {N['d_F2']} points for the best "
          "other core arm). The reader then has to review twice as many documents, and about a quarter of queries "
          "still have no known relevant cross-domain family at depth 1,000."),

    ("h1", "5. Conclusion"),
    ("p", "This paper changed only the first-stage retriever on DAPFAM and held the rest of the system fixed. RQ1: "
          f"changing the first stage changes exposure, but BM25 lowered it by {N['d_F1'][1:]} points and the hybrids "
          "did not exceed patembed-base. RQ2: instruction differences stay near zero under every first stage (0 of 10 "
          f"contrasts significant; Holm p ≥ {N['holm_min']}). RQ3: going to depth 200 raises exposure by about 10 "
          f"points, but even at depth 1,000, {N['none1000_pct']}% of queries have no known relevant OUT family."),
    ("p", ["The committee comments are answered as follows. ", B("K1a"),
           " patembed-base comes from the PatenTEB project [4] and, in this experiment, is among the highest-exposure "
           "first stages (patembed-large does not differ; Qwen3-Embedding and Arctic-embed are lower). This measures "
           "the original choice; it does not justify it after the fact. ", B("K1b"),
           " We found no evidence that BM25 or hybrids raise cross-domain exposure in this setting. ", B("K1c"),
           " Equation (1) is used as accounting only. The conclusion that changing the first stage changes exposure "
           "comes from actually changing the retriever in the experiment. ", B("K2a"),
           " With the reranker held fixed, the instruction effect stays near zero under every first stage. Absolute "
           "nDCG follows π@100, which is consistent with the view that the ceiling of the endpoint depends on exposure "
           "more than on instruction wording. The set C is a matched population, not an intervention on exposure, so "
           "this is not a causal conclusion. ", B("K2b"),
           f" Measures that speak to users are the share of queries with no cross-domain family at all (1 {MINUS} π), "
           f"the rank of the first cross-domain family (median {N['med_F0']} under F0) and the review depth. The benefit "
           "to real users has not been measured."]),
    ("p", "The limitations are as follows. The results come from a single benchmark (DAPFAM) that IS1 already used, so "
          "they cannot select new methods. Relevance labels come from citations and are incomplete, so exposure means "
          "exposure of known relevant families only. In Stage 1, 92% of documents (41,793 of 45,336) exceed 512 "
          "tokens under the patembed tokenizer, so their tails never reach the first-stage retriever. Only one reranker family was tested "
          "(Qwen3-Reranker-0.6B). The cohort, pipeline and instruction token counts (13/28/113/113 against "
          "13/29/119/113 in IS1 Table I) differ from the original study."),
    ("p", "In practice, developers of cross-domain patent search should measure the exposure of the candidate pool "
          "before tuning instruction wording, because the reranker works only inside that pool. Follow-up work belongs "
          "to the Patent-to-Pilot program, which extends the question from ranking within a fixed pool to evidence "
          "acquisition and maintenance, with one Evidence Engine shared by the research and a local Workbench "
          "prototype, compared against lexical, dense and hybrid retrievers under matched conditions. This follow-up "
          "work has no published results yet."),

    ("h1", "Acknowledgments"),
    ("p", "The authors thank the IS1 examination committee for the comments that motivated this work. While preparing the paper, "
          "the author used Claude (Anthropic) to help draft text, write experiment code and format tables. The author "
          "reviewed and takes responsibility for all content and results."),

    ("h1", "References"),
]
BODY += [("ref", f"[{i}] {r}") for i, r in enumerate(REFS, 1)]
BODY = typeset(BODY)
