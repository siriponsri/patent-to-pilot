# SACR-v0 specification and fidelity plan

Status: DRAFT_NOT_RUN; selector arithmetic implemented on synthetic fixtures only. This is preparatory R2 work while R1 actual data isolation, eligibility and baseline parity remain open. It is not a pilot declaration or experiment authorization.

## Research contract and source
This draft operationalizes the owner's supplied research handoff §§8–10, 12–13 and Appendices B/C, without changing benchmark rules. SACR remains an untested candidate. The question is whether selective abstraction preserving explicit relations improves cross-class known-citation retrieval over a frozen passage anchor and resource-matched generic multi-query controls. No claim of novelty, semantic entailment, complete solutions, clinical usefulness or transfer feasibility follows from implementation.

MTM receives only the frozen P text and opaque ID. No title/abstract enrichment, labels, construction roles or citation lookup. DAPFAM receives the selected native TA view shared with controls; native OUT filters qrels, not candidate corpus. TAC-query experiments are not silently substituted. Runtime eligibility is a separate named adapter: MTM publication-date/own-family/CPC X versus native DAPFAM full corpus. Evaluation inputs never enter extraction/selection.

## Profile and view contract
The profile records source hash, input kind, version, status, failure reasons and up to eight relation blocks in source order. Each block contains a relation phrase, optional action/operand/effect, exact source spans and explicitly attached conditions. Preserve raw and normalized wording separately. Span offsets are Python Unicode code-point indices, start inclusive/end exclusive, over the exact allowed text; no whitespace or Unicode normalization before offset checking. Numeric normalization retains the literal source form and never adds a threshold or unit conversion without an explicitly declared rule.

Each condition records kind (numeric, qualitative, polarity, direction, material, other), raw/normalized text, exact spans and explicit/uncertain attachment. An uncertain attachment is not used in local conjunction; retain it in the uncertainty record. Context substitutions record original span, replacement, reason and retain/proposed-abstraction/unresolved status. Do not automatically remove anatomical, material or environmental nouns. No calibrated-confidence field is inferred from model wording.

Allowed views are anchor unchanged, selective abstract, and deterministic relational compact serialization, at most three total. Relational serialization is source-order relation followed by its explicitly attached conditions; no new mechanism words. Duplicate views are logged and deduplicated, never replaced by extra generations. Preserve numbers, units, comparison, polarity, direction and action-operand roles. Source-span matching is a mechanical check, not proof that generated paraphrases preserve meaning.

The extractor is the existing local Qwen3-8B, pending fresh local model/tokenizer/software identity capture. One prompt version, deterministic decoding, no generation retries. Exact prompt, token caps, truncation policy, memory/time cap and decoder implementation must be frozen in the methods log before the pilot. They are intentionally unresolved here rather than claimed as historical values. No corpus-side generation or full-corpus re-encoding.

Whole-profile failure/no usable relation uses the immutable anchor output with a recorded reason. One invalid generated view is discarded; retain other valid views. Condition-free relations are allowed and tracked; do not remove those queries. Absent query text remains a failed query in the complete denominator. Runtime scoring failure stops the attempt; no silent candidate/query drops, automatic alternative method or score-driven retries.

## Acquisition and selection arithmetic
Proposed fixed first version: depth 200 per valid view, union at most 600 families, final depth 200; anchor alpha 0.5 and bottleneck beta 0.5. No hyperparameter search in this draft. These weights have no evidentiary relationship to V4's 0.5 fusion weight.

Search every view over the full eligible frozen passage index with the existing query prefix and MaxP aggregation. Apply identical eligibility to every view before global top-k selection. Stable global cutoff ties use descending score then family ID. The historical baseline wrapper intentionally preserves historical torch.topk cutoff behavior for parity; the new stable acquisition implementation must report any tie divergence, not silently rewrite historical results. Acquisition implementation is still pending.

For each candidate family and block, component cosine matrix rows are relation plus explicit conditions; columns are that family's identical indexed passages. Convert cosine to z=(1+cosine)/2, then for each column compute (1-beta)*mean(z)+beta*min(z). Take the maximum of that joint score over passages, then maximum over valid blocks. Thus evidence for separate components cannot be assembled from different passages. The maximum over blocks permits partial feature matching; no global all-requirements veto.

The implementation rejects empty/nonfinite/out-of-range matrices and inconsistent passage counts. Numerical cosine excursions within 1e-6 of [-1,1] are clipped solely for floating-point tolerance; larger excursions fail. Column identity/order remains the caller's provenance obligation: dimensions alone do not prove it.

Within the deduplicated union, ascending average ranks normalize anchor and coverage scores using (rank-minimum average rank)/(maximum average rank-minimum average rank). All-equal scores receive 0.5 when size >=2; singleton receives 1. Final score is alpha*anchor ranknorm+(1-alpha)*coverage ranknorm. Sort by descending final score, descending original anchor score, then family ID. Empty eligible union returns empty output and remains in the evaluator denominator. Partial/nonfinite scores fail. Every evidence record defaults semantic_status to unknown.

Implemented module: src/patent_to_pilot/research/sacr_selector.py. It accepts already eligible union IDs and numeric scores; it performs neither search nor extraction. A union selector cannot rescue any family absent from all acquisition lists.

## Fidelity inspection before retrieval outcomes
Proposed sample: 100 dev queries per benchmark, or all if fewer, selected by ascending SHA256 of UTF-8 "sacr-v0-fidelity-20261110|benchmark|query_id", ID as final tie break. Record sampling manifest before generation or outcome inspection. Use the full authorized dev cohort, not baseline failures or only constraint-present queries. No test IDs or labels are required. Samples are not independent new test sets. Execution waits for R1 isolation and an adopted prompt/budget declaration.

For each source/profile/view, a developer annotates:
- explicit condition present; relation count; numeric/qualitative condition count;
- exact span failures; unsupported mechanism or numeric/unit additions;
- lost/reversed negation, direction, comparison or action/operand role;
- uncertain context removal and incorrectly attached conditions;
- complete/partial generation failure; unchanged/duplicate views;
- whether a conjunction component is active (at least one valid relation with explicit condition).

Ratings: faithful, unsupported, ambiguous, or unassessable. Every unsupported/ambiguous rating cites exact source and generated spans plus rationale. Invalid source spans or changed explicit protected information invalidate the affected view. Ambiguous replacements are retained as unresolved, not endorsed. Human discovery after a declared run is logged as a defect; do not edit only losing outputs or retry. Amendments require a new version and preserved failed attempt.

Report numerator and denominator for every rate, separated by dataset and complete/partial failures. Do not average away missing profiles. This is a formative developer fidelity audit, not independent expert validation. Retrieval relevance labels do not adjudicate semantic fidelity. A second model, if separately declared, can supply disagreement only; it is not ground truth. No semantic-support score is inferred from successful literal checks.

## Required matched comparisons and accounting
Keep B0 frozen MaxP and B1 existing V4 on its original head separate. The factorial development panel is G/G, G/L, I/G, I/L: generic versus invariant-preserving views crossed with mean-only beta=0 versus local bottleneck beta=0.5. Both selectors use the same alpha, rank normalization, cached relation profile and candidate union for each view family. I/L is full SACR. An ordinary RRF multi-query comparator may be added only with fixed formula/budgets declared before results; no post-hoc selector switching.

Use the same allowed raw input, view/depth/output caps and index. Generic generation prompt and exact output budget are pending declaration, not assumed matched. Count shared extraction cost explicitly for every arm that uses it; also show amortized reuse separately. Report model calls/tokens/failures, view and component embeddings, full-index dot products, candidate passage operations, union size/duplicates, selection/rerank cost, wall/GPU time and peak memory. Natural-cost B0 is not artificially padded.

Evaluate acquisition rescue into raw union and selection rescue into fixed top-200 separately; include losses, selection loss and cases where baseline wins. A 600-family union gain is not a fixed-depth result. Never use oracle selection as method output. V4 on a new candidate head needs a separately declared comparison and cannot inherit historical eligibility by name.

## Evidence and remaining freeze items
Synthetic verification covers average-rank degeneracies, complementary passages, same-passage joint scores, partial-block matching, condition-free reductions, nonfinite inputs, duplicate IDs and stable final cutoff ties. It does not validate extraction, semantics, real vector alignment, acquisition or retrieval improvement.

Before R3: finish strict profile/prompt validation and audit form; capture actual local model/software hashes; freeze prompt/token/time/memory limits; implement stable full-index acquisition and matched generic controls; declare benchmark adapters and failure/resource logs; complete actual R1 integrity/parity and source-fidelity review. Methods-log entry and bounded pilot declaration must precede execution. R5 protected evaluation still requires owner-approved freeze of at most four systems. No automatic ROSER/CPQA or other fallback research method.
