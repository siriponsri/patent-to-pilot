# Manuscript draft v1: one paper, three linked contributions

**Status:** DRAFT v1, 22 Nov 2026 (owner task P5-T01, program owner-note-22112026). Background, method and evaluation design
only. **No new result exists.** Every cell for the proposed method is `NOT_RUN`. Historical results appear only in §8.2 with
their recorded status (PARKED, FORMAT_SMOKE_ONLY or MEASURED_EXPLORATORY) and a link to the receipt.

**Governing documents:** owner blueprint `docs/owner/owner-note-22112026/research/PAPER_AND_IS2_BLUEPRINT.md` (owner-local),
`research/METHOD_AND_BASELINES.md`, `research/SCORE_AND_STATISTICAL_CONTRACT.md`, `04_ARCHITECTURE.md`, and the verified
bibliography `references/verified_identifiers.bib`. Claim-to-evidence map:
[P5-T01_claim_evidence_map.csv](../../tracking/owner-note-22112026/receipts/P5-T01_claim_evidence_map.csv).

**Writing rules for this file.** Cite only the verified bibliography (§11) and the authors' own prior work (Paper 53, program
listing; DOI not verified). Mark any other needed source as `[CITATION NEEDED: …]`. Never write a result sentence before its
run exists, never fill a cell with a target value, and never use a runtime model judgment as ground truth. The product name is
Patent-to-Pilot; method components have plain descriptive names and no new acronym.

---

## 0. Title options (none implies a result)

1. **Patent-to-Pilot: Source-Grounded Structural Expansion for Document Retrieval** (owner blueprint working title)
2. Searching for What Is Missing: Source-Grounded Requirements, One Bounded Corpus Search, and Inspectable Evidence
3. Patent-to-Pilot: Bounded Acquisition of Missing Evidence for Patent and Thai Official-Document Retrieval

Rule: if the acquisition contribution is not supported (§8), the title must not contain "improves", "outperforms" or an
equivalent; option 1 or 2 is then kept as a design description.

## Abstract (skeleton; result sentences are placeholders)

Prior-art and official-document search often fails before ranking begins: a relevant source never enters the candidate pool,
so no reranker or instruction can recover it. Our earlier study of cross-domain patent reranking found near-zero instruction
effects under a fixed candidate pool [P53], and a follow-up first-stage substitution on DAPFAM found the same near-zero effect
under five first stages (§8.2). This paper asks whether **source-grounded structural requirements can select a small number of
additional corpus searches that retrieve useful evidence missed by strong baselines, while keeping explanations faithful to
recorded actions and cost manageable.** We describe Patent-to-Pilot, one engine used by both a research harness and a local
Workbench. It (1) represents documents as source-grounded structure that keeps requirement spans, parent scope, conditions,
versions and page locations; (2) marks each requirement as supported, contradicted or unresolved against cited source spans
and turns one unresolved relation into one bounded, global-corpus search whose candidates are reranked against the original
query; and (3) records every action, citation and dependency so that a result can be inspected and a source revision refreshes
only the affected evidence. We evaluate on three separate scoreboards that are never averaged: a patent development lineage
(Challenge-1M, ALL Recall@200), the exposed DAPFAM benchmark (native nDCG@100), and Thai official and legal documents
(document nDCG@10). `[RESULT 1: primary contrast on the P1 scoreboard — NOT_RUN]`. `[RESULT 2: newly recovered judged-positive
families and displaced positives — NOT_RUN]`. `[RESULT 3: DAPFAM matched comparison — NOT_RUN]`. `[RESULT 4: Thai transfer —
NOT_RUN]`. `[RESULT 5: selective revision versus full recomputation, correctness and work — NOT_RUN]`. Code, configurations and
receipts are released where licences allow `[RELEASE STATE — NOT_RUN]`.

## 1. Introduction

**The missing-evidence problem.** Multi-stage retrieval first forms a candidate pool and then reorders it. When the relevant
source never enters the pool, later stages cannot help. In patent prior-art search this failure is common for cross-domain
(OUT) relevance, where a relevant family uses another field's vocabulary. In official and legal documents a similar failure
arises when the decisive text sits in a different scope: an exception that qualifies a section for a date, an annex that a
clause incorporates, or a footnote that restricts one row of a table.

**Continuity with our prior work.** Paper 53 ("Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking",
Srihangpiboon and Ploysuwan, iSAI-NLP 2026 program [P53]; DOI not verified) studied instruction changes **after** a candidate
pool had been formed and found near-zero effects. Its query-level exposure statistic is not restated here: its original
denominator is still being recovered, and it is not reused until then. Our re-implemented first-stage substitution (B53)
measured exposure directly and found that no tested first-stage substitution raised exposure at K = 100 and no instruction
contrast was significant under any of five first stages (§8.2; exploratory, previously exposed benchmark, not a replication).
The present work changes the question from *how the pool is reordered* to *what can enter the pool*.

**Why not another expansion method.** Generating hypothetical documents [R1], appending pseudo-documents [R2], iterating
generation and retrieval [R3], missing-facet feedback [R4], evidence selection before expansion [R6] and lexical expansion from
semantic evidence [R5] are all established. Our own development lineage also shows that re-weighting, re-slicing or learning to
select among the same four candidate routes did not move ALL Recall@200 beyond about ±0.005 on validation (§8.2). The open
question is narrower: **can an unresolved relation in the user's source-grounded requirements select a useful next corpus
search, under a small fixed budget, better than generic expansion, deeper original-query retrieval and complete-content
retrieval?** This is a hypothesis, not an established novelty claim.

**Intended user benefit.** An examiner, analyst or official reading the result should see which requirement was unresolved,
which search the engine issued, which previously unseen source it found, the exact passage and governing scope, and what the
action cost. When a source is revised, only the evidence that depends on it should be re-checked.

**Prospective contributions** (each is narrowed to what its evidence supports; §8 and §9):

1. **Source-grounded structural evidence.** A document representation that keeps requirement spans, parent scope, conditions,
   document versions and page locations, evaluated against equal-content flat passages and parent/page-context controls.
2. **Bounded acquisition of missing evidence.** One unresolved relation selects one new eligible global-corpus search; new
   candidates are merged and reranked against the original query under a declared action budget, evaluated against the
   strongest matched comparators with harm and cost checks.
3. **Inspectable execution and selective revision.** The same engine drives evaluation and a local Workbench; it records
   evidence/action dependencies and refreshes only affected evidence after a revision, evaluated by source-pointer
   correctness, action-removal replays, changed-binding tests and selective-versus-full recomputation.

The contributions form one causal chain: structure supplies the search signal, acquisition uses it, and the trace makes the
behaviour inspectable and maintainable. We do not claim three independently novel algorithms. If acquisition never beats the
required baselines, the paper reports that the retrieval objective is unmet; the other two contributions are not presented as a
retrieval win.

## 2. Related work

All works below are from the verified bibliography (§11). Reading depth differs and is stated in the owner's source register;
no published score was reproduced or transferred to our data.

**Hypothetical and pseudo-document expansion.** HyDE generates a hypothetical document and retrieves its corpus neighbours
[R1]. Query2doc appends a generated pseudo-document to the query for sparse or dense retrieval, repeating original terms in the
sparse form [R2]. Our historical A3 amendment belongs to this family; generated text is a search hypothesis and never a cited
source. Both appear as model-matched controls (§6.4).

**Iterative and feedback-driven retrieval.** Iterative retrieval-generation alternates generation and retrieval for QA [R3].
ADORE assesses newly retrieved documents against the original query, targets under-covered facets, suppresses drift and stops on
saturation or budget [R4]. Generic missing-facet iteration is therefore a direct collision; our hypothesis rests on a specific
action-selection signal (a source-anchored unresolved relation) and must beat a budget-matched feedback control.

**Evidence-grounded expansion.** EviQE selects evidence before LLM-based expansion [R6] (full method not yet accessed; a
faithful reproduction remains conditional). CE-QE uses semantic seed passages and token attribution to build a fresh lexical
query [R5]. Extractive corpus feedback is an inexpensive control, not a contribution.

**Structured patent retrieval and feature grounding.** Sparse Coverage represents local patent spans through semantic centres
for first-stage search [R7], so "keep local structure instead of one document vector" has patent-specific precedent and must be
separated from more indexed text. FiNE-Patents decomposes claims into features and links them to passages of a supplied
closest prior-art document [R8]. Our task differs in requiring global discovery of missing families; FiNE-Patents is an optional
grounding benchmark, not a substitute for the patent score.

**Thai language models and legal agents.** Typhoon-S includes a legal search/read agent over a Thai legal corpus [R9]; it is
direct Thai legal-agent prior art, and its reported results are answer accuracy in its own environment, not document retrieval
recall. Thai-adapted generators [R10, R11], a Thai encoder [R12], general and embedding models [R13, R14] and a multilingual
embedding model [R15] define the model landscape. NitiBench [R16] and NitiBench+ [R17] are Thai legal QA benchmarks; we use
NitiBench+ only within its public, authorized settings and make no claim about its private retrieval leaderboard.

**Faithfulness of explanations.** Faithfulness differs from plausibility [R18]; self-consistency tests on natural-language
explanations do not establish internal faithfulness [R19]; retrieval-specific explanation [R20] and sanity checks for
explanation methods [R21] motivate controlled interventions. Our explanations are operational traces of recorded actions and
exact citations, validated by removing an action in a controlled replay; they are not claims about a model's internal reasoning.

**Benchmarks and baselines to be cited** (outside the verified bibliography; to be verified before submission):
`[CITATION NEEDED: DAPFAM benchmark paper]` (dataset card verified, see §11), `[CITATION NEEDED: PatenTEB / PatEmbed]`,
`[CITATION NEEDED: Arctic-embed-m-v2.0]`, `[CITATION NEEDED: BM25]`, `[CITATION NEEDED: reciprocal rank fusion]`,
`[CITATION NEEDED: Challenge-1M / USPTO office-action citation corpus source]`, `[CITATION NEEDED: Thai Gazette evidence
retrieval paper]` (dataset card verified), `[CITATION NEEDED: Docling]` if used.

## 3. Problem formulation and contracts

**Corpus and units.** A corpus `D` contains retrievable units (passages or records). Each unit `d` has a document identifier,
a family identifier `fam(d)`, a source version, and span coordinates (code-point offsets, and page region where a layout exists).
Families are the evaluation unit for patents; source documents or source families are the evaluation unit for Thai documents.

**Eligibility.** For a query `q`, `elig(q, d)` applies every declared mask identically to every route: publication or filing
date relative to the query, the query's own unit or family, and task scope. A route that skips a mask is a defect (§10).

**Requirements.** A query or query document yields a small set `R(q) = {r_1 … r_m}`. Each requirement keeps its exact source span
and represents a relation (subject, action/object, condition), preserving negation, quantity, dependency and temporal scope.
Requirements are search signals; they are not relevance labels.

**Actions and budget.** A retrieval action `a = (route, query text, window)` returns up to `w` eligible units. A run spends at
most `B` actions. The first new-method comparison fixes `B = 4`: three declared seed actions and one selected action; the
no-expansion arm spends the fourth action on the original query. Generation tokens, assessment tokens, inspected candidates,
reranking tokens, latency and money are counted separately; equal action count is not equal cost.

**Runtime assessment.** For each requirement, the runtime records `supported`, `contradicted` or `unresolved`, each non-unknown
status with a cited source span. These are fallible runtime signals. The runtime never sees evaluator labels.

**Evaluator-only quantities.** `G(q)` is the set of judged relevant families. With seed pool `S(q)` and expanded pool `E(q)`:
new candidates `|E(q) \ S(q)|` (exploration, not relevance); newly recovered judged positives `|G(q) ∩ (E(q) \ S(q))|`;
displaced positives (judged positives in the seed top-`K` that leave the final top-`K`); and the final metric change after family
deduplication at the common cutoff `K`.

**Benchmark boundaries.** Each scoreboard keeps its own release, input scope, evaluator, cutoffs and access history (§6). A
corpus split named `train` does not authorize training on its evaluation questions; protected TEST data stay closed until a
frozen method and an opening gate exist.

## 4. Method

### 4.1 Source-grounded structural representation (contribution 1)

Ingest original files and keep the original bytes, canonical text with code-point offsets, page regions, typed nodes
(section, claim, clause, annex, table cell, footnote, header) and typed edges (parent, dependency, incorporation, exception,
version-of). Thai text is stored unchanged; normalized search text, Thai-digit conversions and date normalizations are added as
reversible derivatives. Date roles (issue, receipt, publication, effective, referenced) are distinguished and marked as stated or
inferred. A visual observation such as an emblem is stored as an observation with region and detector identity, separate from
stated issuer, source provenance and signature status; it is not an authenticity label.

Before any adaptive policy, a **coverage check** asks whether eligible relevant text is lost through truncation or omitted
sections in the current representation (for example, most DAPFAM TAC records exceed a 512-token encoder input in our pipeline;
§10). If so, all available eligible content is indexed as stable passages with family ID, section path, span coordinates and
parent links; passage multiplicity is capped or normalized at family aggregation. This is first an **engineering control**: it is
compared with equal-content flat passages under the same encoder, tokenizer, aggregation, eligibility and cutoff, so that
"structure helped" is not confused with "more text was indexed".

### 4.2 One bounded, relation-targeted corpus search (contribution 2)

1. **Extract requirements** from the original query or query document with exact spans (§3).
2. **Seed retrieval** with the strongest reproducible eligible baseline, using three declared seed actions.
3. **Assess coverage** on a capped evidence set: mark each requirement supported, contradicted or unresolved with cited spans;
   uncertainty stays unresolved.
4. **Select one unresolved relation** by a rule frozen before evaluation, and issue **one** fresh global-corpus search (lexical
   or dense, as declared) built from original anchors plus traceable corpus vocabulary. Generated synonyms are kept as labelled
   hypotheses with separate provenance. The search runs over the whole eligible corpus, not only the seed pool.
5. **Merge and rerank against the original query.** Deduplicate families, keep all seed candidates, and rank with the common
   final scorer. All-requirements coverage is never a hard filter, because a relevant citation may match only part of a query.
6. **Return an evidence packet**: original requirement span → issued query → newly found candidate → source passage and scope →
   final rank → cost. If no adequate evidence is found, the packet says so and invents no source.

One expansion round is the default. A second round needs its own prospectively declared arm. Runtime model assessments are
search signals; no model judgment replaces gold relevance.

*Illustration (design only, not an observed case):* a document mentions a sensor, a valve and a temperature separately but does
not support "the sensor closes the valve when temperature exceeds the threshold". The targeted search preserves that relation.

### 4.3 Evidence trace and dependency-based refresh (contribution 3)

Every run records actions, inputs, outputs, citations and costs as immutable events. A citation is valid only if the stored
quote equals `text[start:end]` of the cited source version and its hash matches. Dependencies link source versions → passages →
index generations → search receipts → assessments → results. A revision creates a new source version, keeps the old one
resolvable as historical, and marks dependent assessments `needs_review`; only those are re-executed. An embedding change creates
a new index generation and never mixes vector spaces. The trace is operational provenance: it shows what the engine did, not
that a statement is semantically true.

## 5. System architecture

Patent-to-Pilot is one local Python server with a bundled UI, SQLite persistence and local files. Four components share one
engine:

| Component | Responsibility |
|---|---|
| Document store | Immutable originals, canonical text, page regions, typed nodes/edges (SQLite adjacency tables), versions and rights |
| Retrieval engine | Lexical and dense search, family deduplication, eligibility filters, structural context closure, interchangeable acquisition policies |
| Evidence recorder | Exact citations, runtime assessments, action provenance, costs, invalidation dependencies |
| Workbench and harness | Search / Compare / Inspect / Update views for users; reproducible evaluation for research, adding evaluator-only labels after inference |

Model choice is configuration behind typed provider ports (chat, embedding, rerank), with local and API adapters, explicit
capability states and a lexical fallback. Paid routes require a recorded spending envelope. The research configuration may use
research-only assets (for example PatEmbed and DAPFAM, both non-commercial licences); the product default stack excludes them.

Existing functional evidence (engineering, on a synthetic fixture; not effectiveness evidence): the Workbench and CLI reach the
same core; every non-unknown decision carries a literal citation; a revision creates v2, keeps v1 resolvable and reopens
affected work; state survives restart; a new uncited source can overturn an earlier "nothing found"
([G01 status](../../../artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md),
[G02 status](../../../artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md)).

`[FIGURE 1: architecture flow, from owner package asset traceable_evidence_architecture — to be redrawn in the journal style]`

## 6. Evaluation design

Three scoreboards, never averaged into a single score. Each freezes its protocol, endpoints, comparator set, cluster unit,
missing-query policy and seed before its first number.

### 6.1 Scoreboard A — P1 / Challenge-1M (development lineage)

- **Data:** the 1M-unit Challenge-1M corpus; TRAIN for fitting, P1-DEV for selection, VAL for decisions. Populations are counted
  separately and never merged: 26,575 raw DEV tasks (25,626 with runs); 2,000 raw VAL tasks; the latest A3 input manifest lists
  1,919 VAL IDs; the A2 ALL contrast scored 1,999 VAL queries.
- **Principal endpoint:** ALL Recall@200 on VAL against F\* = `alloc-L0-Q2-P2-A0` (two 200-rank windows each of
  Qwen3-Embedding-0.6B and PatEmbed, RRF), under the historical B = 4 action model.
- **Guards:** IN and OUT paired 95% lower bounds above −0.005 (non-inferiority); failure to establish non-inferiority is
  uncertainty, not proof of harm.
- **Inference:** paired per-query differences, cluster bootstrap by art unit, 10,000 replicates, seed 20261119.
- **Exposure:** VAL has already been looked at three times (v1, A1, A2); A3 would be the fourth. No VAL result here is
  confirmatory. A confirmatory claim needs the protected P1 TEST gate and a frozen method.

### 6.2 Scoreboard B — native DAPFAM (exposed external comparison)

- **Endpoints:** nDCG@100 (native primary) and Recall@100 (secondary), family-level, ALL/IN/OUT, with the native scorer. Query
  views TA and TAC; corpus views TA, TAC and full text (18 cells with ALL/IN/OUT). Recall@200 stays in a separate historical
  table.
- **Reference rows:** the published Arctic configuration (int8) as reported; our fp16 Arctic as a separate modernized row; BM25;
  Qwen3-Embedding. **PatEmbed is a separately reported row** with its caveat: public PatenTEB test files share a family pool with
  DAPFAM, and training overlap is unmeasured.
- **Status:** DAPFAM is already exposed in this project (B53, B53.0); this scoreboard is an external matched comparison, never a
  pristine holdout.

### 6.3 Scoreboard C — Thai official and legal documents (transfer)

- **Thai Gazette evidence retrieval:** document nDCG@10 (main), Recall@20 and complete required-source coverage@20
  (secondary), exact evidence-span checks (diagnostic). These cutoffs are this study's proposed contract, not a published
  leaderboard. Single-source and multi-source questions reported separately.
- **Structural packets:** required-evidence correctness and scope-binding accuracy on declared question types, with original
  pages and provenance; OCR error, layout overlap and emblem-region accuracy as supporting diagnostics only.
- **NitiBench / NitiBench+:** answer scores and citation measures in separate tables, within authorized public settings.
- **Exposure:** public dataset cards may display examples; such exposure is recorded. A fresh-data generalization claim needs a
  separately frozen packet with held-out document families.

### 6.4 Comparators and ablations (matched resources)

1. Strong lexical and dense/hybrid baselines and the exact historical F\* where applicable; N4 (or a task-compatible
   counterpart) to keep IN/OUT trade-offs visible.
2. Equal-content flat versus structural passages (contribution 1).
3. Deeper original-query retrieval using the same extra action.
4. Model-matched HyDE-style and lexical Query2doc-style expansion.
5. Corpus-term pseudo-relevance feedback; a reproducibly specified CE-QE-style control; a budget-matched ADORE-style feedback
   control where feasible.
6. Policy controls: static structural queries without feedback; a randomly selected requirement; shuffled binding–evidence
   associations within a query (matched queries and tokens).
7. For contribution 3: action-removal replay, changed-binding tests, and selective refresh versus full recomputation.

Adapted baselines are labelled as adaptations; an unreproducible method is reported as such, not as a loser.

### 6.5 Decision rule for the acquisition claim (frozen before the final evaluation)

One primary task, endpoint and strongest eligible comparator are frozen on permitted development data. Planning target: at least
+0.010 absolute on the primary 0–1 metric with the paired 95% lower bound above zero, plus the IN/OUT guards on the patent task.
This is a planning target, not a power calculation or a promise. A positive point gain below target is preserved as evidence for
the next bounded experiment. A final-score gain without newly recovered judged-positive families supports a ranking improvement,
not the acquisition mechanism. Secondary significance claims use Holm correction.

### 6.6 User-task evaluation (Workbench)

Predefined tasks: locate the governing source, resolve an annex or exception, check an update. Measures: task success, elapsed
time, correction rate. `[PROTOCOL AND PARTICIPANTS — NOT_RUN]`.

## 7. Implementation and reproducibility

Frozen configurations with prompt and configuration hashes; versioned run artifacts generate every manuscript number; per-query
rows from licensed benchmarks stay outside the public repository; paid calls run under one shared reservation ledger with
unknown costs paused, never recorded as zero. `[ARTIFACT MANIFEST AND LICENCE RECEIPT — NOT_RUN (P5-T03)]`.

## 8. Results

### 8.1 New results (all NOT_RUN)

**Table 1. Scoreboard A (P1 / Challenge-1M), VAL, B = 4.**

| System | ALL R@200 | Δ vs strongest [95% CI] | IN lower bound | OUT lower bound | new candidates | new judged positives | displaced positives | cost |
|---|---|---|---|---|---|---|---|---|
| F\* (historical static default) | NOT_RUN | — | — | — | — | — | — | NOT_RUN |
| Deeper original-query retrieval | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Equal-content flat passages | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Structural passages | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| HyDE-style (model-matched) / A3r1 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Query2doc-style lexical | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Corpus-term feedback | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Generic feedback (ADORE-style) | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Static structural queries | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Random requirement | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| Shuffled binding–evidence | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| **Relation-targeted search (proposed)** | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |

The historical F\* values (DEV 0.4230, VAL 0.4523) are not copied into this table: the new protocol's cohort, guards and
comparator set must be frozen first, and the cell is regenerated from that run.

**Table 2. Scoreboard B (native DAPFAM, exposed), nDCG@100 / R@100, ALL / IN / OUT, per query/corpus view.**

| System | nDCG@100 ALL / IN / OUT | R@100 ALL / IN / OUT | note |
|---|---|---|---|
| BM25 | NOT_RUN | NOT_RUN | |
| Arctic-embed-m-v2.0, published int8 | reported values only, not rerun | reported values only | published reference row |
| Arctic-embed-m-v2.0, our fp16 | NOT_RUN | NOT_RUN | modernized row |
| Qwen3-Embedding-0.6B | NOT_RUN | NOT_RUN | |
| PatEmbed (separate, caveat) | NOT_RUN | NOT_RUN | shared family pool; training overlap unmeasured |
| Strongest matched comparator | NOT_RUN | NOT_RUN | |
| **Relation-targeted search (proposed)** | NOT_RUN | NOT_RUN | |

**Table 3. Scoreboard C (Thai).** Gazette nDCG@10 / Recall@20 / coverage@20; structural-packet evidence correctness and
scope-binding accuracy; NitiBench answer measures in their own table: **all NOT_RUN.**

**Table 4. Contribution 1, equal-content control.** Flat versus structural passages, extraction and binding accuracy: **NOT_RUN.**

**Table 5. Contribution 3, trace and revision.** Citation-pointer correctness on evaluation data, action-removal replay effect,
changed-binding tests, selective versus full recomputation (output equality and work units): **NOT_RUN.** (The G01/G02 fixture
checks in §5 are engineering verification, not these measurements.)

**Table 6. User tasks.** Success, time, corrections: **NOT_RUN.**

### 8.2 Historical results (measured earlier; status as recorded)

These results motivate the design. None is a result of the proposed method, and none is confirmatory.

**Table 7. P1 development lineage on VAL, contrast against F\*, ALL R@200 (art-unit cluster bootstrap, 10,000 replicates).**

| Mechanism | ALL Δ [95% CI] | IN Δ [95% CI] | OUT Δ [95% CI] | Status | Source |
|---|---|---|---|---|---|
| Support-frontier allocation v0 | −0.0199 [−0.0254, −0.0141] | −0.0208 [−0.0301, −0.0111] | −0.0157 [−0.0241, −0.0076] | PARKED | [memo §2](../../healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md) |
| Field-obligation routes (A1) | −0.0054 [−0.0107, +0.0000] | −0.0078 [−0.0169, +0.0016] | −0.0051 [−0.0123, +0.0016] | PARKED; mask defect disclosed, direction of its effect unknown | memo §4a and correction note |
| Learned route selector (A2) | +0.0017 [−0.0019, +0.0054] | +0.0002 [−0.0060, +0.0062] | +0.0032 [−0.0023, +0.0085] | PARKED (IN non-inferiority not shown) | memo §4b |
| LLM query expansion, A3r0 | — | — | — | FORMAT_SMOKE_ONLY (4 TRAIN calls; no effectiveness pilot) | [amendment 3](../../healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md), memo §4b correction note |
| LLM query expansion, A3r1 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN (prospective amendment) | owner A3 checkpoint |

F\*: P1-DEV 0.4230, VAL 0.4523. The per-query oracle over 35 fixed allocations reaches +0.079 on P1-DEV (post hoc, label-using,
descriptive); the learned selector captured about 1.5% of it on P1-DEV. These are DEV quantities, not a proven learnable gain.
The A3r0 panel is one Claude, two Qwen and one DeepSeek model and supports no generator-diversity claim.

**Table 8. B53, first-stage substitution on DAPFAM (re-implementation; exploratory; previously exposed benchmark).**

| Quantity | Value | Status | Source |
|---|---|---|---|
| π@100 (share of 905 OUT queries with ≥ 1 known OUT family in the top 100), patembed-base F0 | 0.371 | MEASURED_EXPLORATORY | [B53 Stage 1](../is2/results/B53-STAGE1-RESULTS.md) |
| Δπ@100 vs F0: BM25 / RRF(BM25, F0) / Arctic / RRF(BM25, Arctic) | −0.105 [−0.136, −0.075] / +0.004 [−0.015, +0.024] / −0.054 [−0.077, −0.032] / −0.035 [−0.061, −0.010] | MEASURED_EXPLORATORY | B53 Stage 1 |
| Instruction contrasts on the common-exposed set (C = 153), strict OUT nDCG@100 | 0 of 10 significant after Holm; Δ +0.001 to +0.009; smallest Holm p 0.695 | MEASURED_EXPLORATORY | [B53 Stage 2](../is2/results/B53-STAGE2-RESULTS.md) |

B53's π@100 = 0.371 is B53's own measurement on 905 queries; it is not Paper 53's statistic and is not presented as a
replication of it.

**Table 9. B53.0, native DAPFAM TAC → TAC check against the published DAPFAM paper (arXiv v2 tables).**

| System | nDCG@100 ALL, ours vs paper | Verdict | Status | Source |
|---|---|---|---|---|
| Arctic-embed-m-v2.0 (fp16 vs int8) | 0.3110 vs 0.3055 | 11 of 12 cells within the frozen ±0.010 rule; Arctic R@100 IN +0.0106 outside | MEASURED_EXPLORATORY (matched re-implementation, not exact reproduction) | [B53.0](../../healthtech/research/b53-0/B53-0-RESULTS.md) |
| BM25 (k1 1.5 vs bm25s k1 1.2) | 0.2430 vs 0.2451 | as above | as above | B53.0 |

The PatEmbed context row from B53.0 is not shown here: it is a possibly overlapping model (shared family pool, training overlap
unmeasured) and is reported only with that caveat.

## 9. Discussion `[TO BE WRITTEN AFTER §8.1 EXISTS]`

Planned structure: what the acquisition evidence does and does not support; whether gains come from new judged-positive
families or from reranking; cost and harm trade-offs; where structure helped versus where more text helped; what the trace
showed in failure cases. If the acquisition ladder ends without a supported win, this section states that the retrieval
objective is unmet and lists the evidence gathered.

## 10. Threats to validity and limitations

- **Repeated validation looks.** P1 VAL has been used for three decisions (four if A3 runs). It is development evidence only.
- **Benchmark exposure.** DAPFAM was used in B53 and B53.0; public Thai cards may show examples. Neither is a pristine holdout.
- **Model–benchmark overlap.** PatEmbed's public PatenTEB test files share a family pool with DAPFAM; its training data are
  unreleased, so training overlap, its size and the direction of any effect are unknown. LLM generators were trained on public
  patent text and may recall later documents or citations; this cannot be removed on P1 data.
- **Mask consistency.** A historical route (A1) skipped the date and own-unit masks; the direction of that defect's effect is
  not established. Every new route must apply the masks of its route family.
- **Incomplete judgments.** Exposure and recall concern known relevant families only; new candidates may be unjudged.
- **Truncation and parsing.** In B53, 92% of DAPFAM TAC records and 95% of TAC queries exceed 512 tokens. Thai PDFs depend on
  a text layer; scans and encrypted files are refused; OCR is future work.
- **Multiple comparisons and selection.** The A3 pilot GO rule is optimistic (best of many allocations on the same queries) and
  is a spending gate, not a result.
- **Cost and provider drift.** Endpoint prices and models change; raw responses are saved for replay; actual cost is reconciled.
- **Licences.** PatEmbed and DAPFAM are non-commercial research assets; the product default excludes them.
- **Explanations.** Traces show recorded actions and literal citations; they do not show semantic truth or internal model
  reasoning.

## 11. References (verified bibliography only, plus own prior work)

Identifiers checked by the owner's citation audit (21 title/identifier pairs). Author lists are given where the owner package
records them; the others are completed from the verified record before submission.

- **[P53]** S. Srihangpiboon and T. Ploysuwan, "Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking,"
  iSAI-NLP 2026, Paper 53, official program https://isai-nlp2026.aiat.or.th/program. DOI and proceedings record not verified.
- **[R1]** L. Gao, X. Ma, J. Lin, J. Callan, "Precise Zero-Shot Dense Retrieval without Relevance Labels," ACL 2023. doi:10.18653/v1/2023.acl-long.99
- **[R2]** L. Wang, N. Yang, F. Wei, "Query2doc: Query Expansion with Large Language Models," EMNLP 2023. doi:10.18653/v1/2023.emnlp-main.585
- **[R3]** Z. Shao, Y. Gong, Y. Shen, M. Huang, N. Duan, W. Chen, "Enhancing Retrieval-Augmented Large Language Models with Iterative Retrieval-Generation Synergy," Findings of EMNLP 2023. doi:10.18653/v1/2023.findings-emnlp.620
- **[R4]** A. Bigdeli et al., "ADORE: Iterative Query Expansion with Retrieval-Grounded Relevance Feedback," preprint, 2026. arXiv:2606.13905
- **[R5]** A. Kahirov, U. Deshpande, S. Sundararaman, "CeQe: Grounding Lexical Retrieval in Semantic Evidence," preprint, 2026. arXiv:2608.00452
- **[R6]** H. S. Le et al., "EviQE: Evidence Selection for LLM-Based Query Expansion," CIKM 2026. doi:10.1145/3799682.3839965
- **[R7]** Y. Zuo, K. Gerdes, É. de la Clergerie, B. Sagot, "Sparse Coverage: Semantic Center Representations for Patent Prior-Art Retrieval," 2026. arXiv:2608.16918
- **[R8]** V. Knappich, A. Hätty, S. Razniewski, A. Friedrich, "Is It Novel and Why? Fine-Grained Patent Novelty Prediction Based on Passage Retrieval," SIGIR 2026, 845–856. doi:10.1145/3805712.3809576
- **[R9]** K. Pipatanakul, P. Taveekitworachai, "Typhoon-S: Minimal Open Post-Training for Sovereign Large Language Models," 2026. arXiv:2601.18129
- **[R10]** "Typhoon 2: A Family of Open Text and Multimodal Thai Large Language Models," 2024. arXiv:2412.13702 `[authors to complete]`
- **[R11]** "OpenThaiGPT 1.5: A Thai-Centric Open Source Large Language Model." arXiv:2411.07238 `[authors and year to complete]`
- **[R12]** "WangchanBERTa: Pretraining transformer-based Thai Language Models," 2021. arXiv:2101.09635 `[authors to complete]`
- **[R13]** "Qwen3 Technical Report," 2025. arXiv:2505.09388
- **[R14]** "Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models," 2025. arXiv:2506.05176
- **[R15]** "M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation," 2024. arXiv:2402.03216 `[authors to complete]`
- **[R16]** "NitiBench: Benchmarking LLM Frameworks on Thai Legal Question Answering Capabilities," EMNLP 2025. doi:10.18653/v1/2025.emnlp-main.1739 `[authors to complete]`
- **[R17]** "NitiBench+: A Temporal Thai Legal Question Answering Benchmark Across 17 Domains," 2026. arXiv:2611.03576 `[authors to complete]`
- **[R18]** "Towards Faithfully Interpretable NLP Systems: How Should We Define and Evaluate Faithfulness?," ACL 2020. doi:10.18653/v1/2020.acl-main.386 `[authors to complete]`
- **[R19]** "On Measuring Faithfulness or Self-consistency of Natural Language Explanations," ACL 2024. doi:10.18653/v1/2024.acl-long.329 `[authors to complete]`
- **[R20]** "EXS: Explainable Search Using Local Model Agnostic Interpretability," 2018. arXiv:1809.03857 `[authors to complete]`
- **[R21]** "Sanity Checks for Saliency Maps," NeurIPS 2018. arXiv:1810.03292 `[authors to complete]`

**Dataset records (cards verified by the owner package; not scholarly citations):** DAPFAM
(https://huggingface.co/datasets/datalyes/DAPFAM_patent), Thai Gazette evidence retrieval
(https://huggingface.co/datasets/VISAI-AI/thai-gazette-evidence-retrieval), NitiBench
(https://huggingface.co/datasets/VISAI-AI/nitibench).

## Appendix A. Writing gaps to close before P5-T02

1. Every §8.1 cell (P1, DAPFAM, Thai, contribution 1, contribution 3, user tasks).
2. `[CITATION NEEDED]` items in §2 (DAPFAM paper, PatenTEB/PatEmbed, Arctic, BM25, RRF, Challenge-1M source, Thai Gazette
   paper) and missing author lists in §11.
3. Paper 53 DOI and proceedings record; recovery of its original exposure denominator before any reuse.
4. Frozen selection rule for "which unresolved relation" (§4.2 step 4) and the frozen A3r1 configuration.
5. Figure 1 redrawn; results figures only from versioned run artifacts.
6. Venue choice and target length (see `VENUES.md`); author/affiliation block.
