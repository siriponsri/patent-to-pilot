# SACR: targeted prior-art comparison

Status: READY_FOR_REVIEW as a bounded literature note; research readiness INCOMPLETE.
Access date: 10 November 2026. Implementation inspected at
`73565c728238f2d3cf0ae98bf7e263b196f9abe8`.

## Question and coverage

Which parts of the implemented proposal overlap with selected primary work, and
what experiment could distinguish the proposed contribution? This is a targeted,
non-exhaustive comparison of seven sources identified through the owner handoff
and primary-source follow-up. It is not novelty clearance, a systematic review,
a replication, or a claim that unmentioned literature lacks these mechanisms.
No paper files or dataset text are redistributed. Source statements and our
implementation-based interpretations are separated below. No cross-paper score
comparison is justified by this review.

## Source and claim ledger

| ID / primary source | Inspected scope and supported statement | Implication for SACR (our interpretation) |
|---|---|---|
| P1 Murphy et al. (2014), [functional-vector analogy search](https://edrl.engr.wisc.edu/wp-content/uploads/sites/142/2022/02/murphy_2014_function-based_design-by-analogy-jmd.pdf), DOI 10.1115/1.4028093 | PDF opening text describes functional terms, vector-space matching of design problems to patent descriptions, and near/far-domain cases. Subsequent targeted PDF reads timed out; detailed context-limiter claims were not verified here. | Functional abstraction and patent analogy retrieval predate SACR. This source does not establish whether SACR's particular requirement-preservation procedure is absent from prior work. |
| P2 Hope et al. (2017), [analogy mining](https://arxiv.org/html/1706.05585v1), DOI 10.1145/3097983.3098038 | Abstract, introduction, sections 2.1 and 2.3.1: crowd-labelled product-text spans support learned purpose/mechanism representations; analogies can seek similar purposes with different mechanisms. | Structured decomposition for analogy is established. Query-side source preservation over an existing passage index differs operationally from the inspected learned representations; this difference alone is neither novelty nor superiority. |
| P3 Liu et al. (2020), [function-based patent knowledge retrieval](https://www.sciencedirect.com/science/article/pii/S0166361519304841), DOI 10.1016/j.compind.2019.103154 | Publisher search-indexed abstract/section previews describe function, technical-term and classification information, functional-basis query abstraction and cross-domain retrieval/evaluation. Direct page access returned 403. Full experimental protocol was not audited. | Do not claim the first functional patent search or first design-requirement-aware retrieval. A fixed-index query procedure is a candidate operational distinction requiring closer full-method comparison. |
| P4 Liu et al. (2023), [SMFM analogy retrieval](https://www.sciencedirect.com/science/article/abs/pii/S0166361523001239), DOI 10.1016/j.compind.2023.103973 | Publisher search-indexed abstract/previews describe functional and causal relations, function/metafunction retrieval paths, and weighted vector similarity. Direct page access returned 403; full protocol was not reviewed. | Relation-structured design retrieval already exists. Do not infer the absence of source-preservation safeguards from a limited preview. |
| P5 Malaviya et al. (2023), [QUEST](https://aclanthology.org/2023.acl-long.784/), DOI 10.18653/v1/2023.acl-long.784 | ACL record and abstract: entity-seeking Wikipedia queries involve implicit set operations, with validated answers and evidence attribution. Full PDF was not inspected this turn. | Conjunction and exclusion are established retrieval issues. Entity-set semantics do not justify converting incomplete patent citation judgments into all-requirements labels. |
| P6 Cha et al. (2026), [conjunctive cross-page retrieval](https://arxiv.org/html/2607.24165v2), arXiv 2607.24165v2 | Preprint abstract and sections 2–3, especially section 3.3 equation 2: a distinct-page operator maximizes the minimum condition score over injective page assignments. The study distinguishes discovery from complete-first ordering. Peer-review status not established. | Min-based condition aggregation is not new. Its distinct-page assignment differs from SACR's same-passage reduction and maximum over blocks. Its all-condition task is not MTM citation recovery. No performance numbers are transferred. |
| P7 Khattab and Zaharia (2020), [ColBERT](https://arxiv.org/html/2004.12832v2), DOI 10.1145/3397271.3401075 | Sections 3.1–3.3, equation 3: contextualized query/document token embeddings interact through a sum of per-query-token maximum similarities; encoders are trained. | Late interaction and aggregation are established. SACR uses relation/condition component embeddings against passage embeddings, not this token-level trained scoring architecture. Reusing an index is an operational choice, not a novel principle. |

## What the implementation actually computes

In `sacr_selector.py`, each block contains one relation plus its attached
conditions. For component i, passage p and block b, let z=(1+cosine)/2.
The implemented score is:

`coverage = max_b max_p [(1-beta) mean_i z(b,i,p) + beta min_i z(b,i,p)]`.

The proposed beta is 0.5; the mean-only control uses zero. Candidate-union anchor
and coverage scores are separately rank-normalized and fused with proposed alpha
0.5, then trimmed to the fixed output depth. Rank normalization is union-dependent.
Comparisons must therefore keep the union fixed when isolating selector effects.

The minimum is computed before maximizing over passages: high scores from different
passages cannot be assembled into one block's score. However, the maximum over
blocks permits one block to dominate. Neither operation certifies entailment,
compatibility, fulfillment of every requirement, or complete technical disclosure.
Dense similarity remains a proxy even when the raw query spans are exact.

The quote/profile/compiler checks establish byte-level source linkage and reject
some malformed transformations. They do not establish correct attachment, preserved
roles, semantic fidelity, or retention of omitted requirements. The two actual
generation smoke failures remain failures; synthetic tests do not repair them.

## Contribution boundary and discriminating evidence

The defensible candidate is a *tested combination*, if later supported: query-only
selective abstraction retaining source-linked requirements, fixed-index acquisition,
and local relation/condition selection under explicit failure and resource accounting.
No first-ever, novel-operator, faithful-generation, or improved-retrieval claim is
currently supported. A successful engineering pipeline alone cannot establish it.

The existing planned factorial comparison is the immediate discriminator:

1. Compare generic and requirement-preserving views with matched allowed inputs,
   view counts, search/output depths and model budgets. Charge shared extraction
   costs explicitly. Improvements must exceed generic multi-query benefits.
2. Within each acquisition union, compare beta=0 with beta=0.5 using identical
   profiles, passage populations and score normalization. Compare selector effects
   only within that union; cross-union effects include candidate acquisition.
3. Evaluate fixed-depth rescue and losses, not only whether gold enters a union
   of up to 600 families. Report raw union coverage separately from final retrieval.
4. Collect source-first fidelity observations under an adopted policy independently
   of citation recovery. Exact quotes and retrieval hits cannot substitute for them.
5. Preserve all failures, fallbacks, unavailable inputs and unknown costs. Do not
   choose a favorable arm after inspecting protected outcomes.

These are interpretations of existing controls, not a new experiment declaration
or authority to run. Real isolation, eligibility counts and baseline parity remain
R1 gates; reliable generation and fidelity remain open. R3/R4 evidence is absent.
R5 requires the owner's explicit freeze. R6 remains a working draft.

## Remaining literature work

Obtain lawful full-method access for P3/P4 and complete P1 before asserting precise
algorithmic differences; inspect P5's protocol before detailed benchmark comparison.
Broader query-reformulation, relation-preservation and aggregation coverage is still
needed before any novelty wording. Independent scholarly review has not occurred.
This note supports narrowing claims now, not declaring the literature complete.
