# P2-T03 — One bounded source-relation search action: mechanism specification

**Status:** implemented (22 Nov 2026). **Evidence class:** engineering mechanism only. **Spend:** USD 0 (no network, no
model call, no download, no research data read).
**Code:** `src/patent_to_pilot/workbench/relation_search.py`. **Tests:** `tests/test_p2_t03_relation_search.py`
(synthetic only). **Companion receipt:** [P2-T03_mechanism_verification.md](P2-T03_mechanism_verification.md).

## 1. What the operator does

One call performs exactly one bounded action after a seed retrieval:

1. **Keep the exact query requirements.** `QueryRequirements(query_id, text, requirements)` is frozen; every requirement
   is a zero-based, half-open code-point span with `text[start:end] == requirement.text` (checked at construction;
   `bind()` refuses a requirement text that is absent or occurs more than once). Its SHA-256 fingerprint is taken before
   the action and re-checked after it.
2. **Select one unresolved relation** with the named, versioned policy `POLICY_V1` (section 2).
3. **Issue exactly one eligible global search** for it: one call of the caller's search backend over the whole corpus
   (not only the pool), only if the `ActionBudget` has an action left; the `EligibilityMask` is then applied, and the
   first `result_limit` eligible candidates are kept.
4. **Merge** the eligible returned candidates into the pool and record real membership:
   `after = before + [x for x in returned if x not in before]`, `new = [x for x in returned if x not in before]`.
   The merged pool is re-checked against the mask.
5. **Re-check coverage**: one call of the caller's assessor on the merged pool; relation and requirement status before
   and after are recorded.
6. **Rerank against the original need only**: the reranker receives a `RerankRequest(query_id, original query text,
   exact requirement texts)` and the merged ids. It never receives the expansion query, its terms or any hypothesis.
7. **Emit one evidence-trace event** (`action.kind = structural_expansion`) that must pass the owner schema
   (`evidence_trace.schema.json`, Draft 2020-12) and the semantic checks of `trace_slice.semantic_errors`; the operator
   also refuses an event whose pool sets, submitted query or original query differ from what was executed.
8. **Never cite a generated hypothesis**: hypotheses are a separate type (`SearchHypothesis`), registered separately,
   and every citation path (relation evidence, references, coverage re-check, trace assessments) resolves ids through a
   registry that raises `HypothesisNotEvidence` for a hypothesis id.

## 2. Named policy: `ptp-relsel-first-unresolved/1.0.0`

Fingerprint (SHA-256 of the canonical JSON of `POLICY_V1.describe()`):
`e4ea084cd572e4fdda37838451c9d2838f7af61bc5c68b7cec4468411265629c` (`POLICY_V1_SHA256`).
The operator refuses any policy whose name is unknown or whose fingerprint differs from the pinned value, so a changed
rule needs a new version and a new pin, never a silent edit. **This rule is not yet frozen for research use:** P2-T04
(or its protocol) must freeze it by name, version and fingerprint before any research number is computed with it.

**Selection rule**

* **S1 eligible relations:** `status == "unresolved"` AND `actionable` AND `relation_key` not already attempted AND the
  relation has search material (a `reference_text` or at least one anchor term). Skipped relations are recorded with the
  reason (`status_supported`, `status_contradicted`, `not_search_actionable`, `already_attempted`, `no_search_material`).
* **S2 order** by the tuple: (a) the position of the relation's requirement in the query, ordered by (span start, span
  end, requirement id); (b) the 0-based rank of `from_id` (the candidate holding the reference) in the pool before the
  action, `len(pool)` if absent; (c) the start offset of the reference evidence span, `2**63` if none; (d) `relation_key`
  lexicographically.
* **S3** select the first. Input order, scores, evaluator labels, randomness and model calls are not used, so the result
  is invariant to the order in which relations are supplied.

**Query rule**

* **Q1** terms in order: the relation's `reference_text` (origin `source_copy`, pointer = its source-evidence id; it must
  equal that evidence quote); each anchor term (origin `original_requirement`; it must be a term of the relation's own
  requirement); each generated hypothesis for the selected relation (origin `generated_hypothesis`, pointer = hypothesis
  id). Hypotheses are requested only for the selected relation and only when the budget allows the search.
* **Q2** case-insensitive duplicates keep the first occurrence; a term without a word token is refused.
* **Q3** submitted text = OR of quoted phrases (`trace_slice._or_match`, the FTS5 expression used by P0-T06). Exactly one
  backend call with depth `fetch_limit`, then the mask, then the first `result_limit` eligible candidates.

**Rerank rule**

* **R1** the reranker sees only the `RerankRequest` (original query and exact requirement texts) and the merged ids.
* **R2** order by score descending; unscored candidates follow; ties by merged-pool position (before-pool first, then new
  candidates in returned order). Optional `final_k` cuts the final list.

## 3. Eligibility and budget

* `EligibilityMask(profile_id, exclude_ids, exclude_groups, grouping, group_of, dates, date_cutoff, missing_date)`.
  Reasons: `excluded_id` (e.g. the query document), `excluded_group:<g>` (e.g. own family / own source), and, when a
  cutoff is declared, `date_not_before_cutoff` (eligible iff date < cutoff, strictly before) or `missing_date` (default
  rule `exclude`; `include` must be declared explicitly). A candidate's date is `dates[id]`, else `dates[group]`.
  The trace carries `eligibility_profile_id = <profile_id>#<first 16 hex of the mask fingerprint>`; the record carries the
  full mask description and fingerprint. The pool before the action must already satisfy the mask (else
  `IneligibleCandidate`): the same mask has to be applied to the seed route.
* `ActionBudget(limit)` counts retrieval actions (seed and expansion). The operator issues a search only when
  `remaining >= 1`; otherwise it returns `outcome = "budget_exhausted"` without searching or generating hypotheses.
  Spending past the limit raises `BudgetExhausted`. A failed backend call still spends its action.

## 4. Two forms, one implementation

**Pure form (research harness; no Workbench store):**

```text
relation_search_step(*, requirements: QueryRequirements, relations: [RelationState], pool_before: [id],
                     search(query: ExpansionQuery, fetch_limit, eligibility) -> [(id, score)],   # called at most once
                     assess(after_ids: tuple) -> [RelationState],                               # called once
                     rerank(request: RerankRequest, after_ids: tuple) -> {id: score},
                     budget: ActionBudget, eligibility: EligibilityMask, evidence: EvidenceRegistry,
                     hypotheses_for(relation) -> [SearchHypothesis] = None, policy = POLICY_V1,
                     result_limit = 5, fetch_limit = None, final_k = None, attempted = (),
                     emit(record, query, hypotheses) -> event = None, action_id = None) -> record
```

`RelationState(relation_key, requirement_id, kind, status, from_id, reference_text, reference_evidence_id,
anchor_terms, evidence_ids, actionable, note)` is a runtime signal (`supported` / `contradicted` / `unresolved`), never
gold. Reference helpers for synthetic tests and precomputed candidate texts: `InMemoryBM25` (bag-of-terms BM25,
k1 = 1.2, b = 0.75, Lucene idf; not FTS5 phrase matching), `bm25_reranker(docs)`, `EvidenceRegistry`,
`trace_emitter(TraceContext, registry)` and `make_index_identity(...)`. The assessor is deliberately **not** provided:
which coverage signal a research arm uses is a protocol decision for P2-T04.

**Workbench form:** `RelationSearchSlice(TraceSlice)` on a project store (default project id
`synthetic-p2-t03-relation-search`): real SQLite FTS5 BM25 seed search over the bound requirement's terms (same mask,
fetch 50, first 5 eligible), the P0-T06 reference-coverage assessor, mapping to relation states (an annex reference is
`cross_document_reference`, search-actionable; a footnote marker is `in_version_footnote`, closure only, not
search-actionable), the operator with the FTS5 backend, an FTS5-BM25 reranker over the original requirement terms only,
and `TraceSlice._event` for schema-checked events stored in `trace_events`. Run and actions go to the existing `runs` /
`actions` tables (`trace_search` for seed and expansion with policy, mask, raw hits and exclusions; `trace_rerank` for the
ranking). The default budget is 2 (seed + one relation search).

**Record** (`ptp-relation-search-record/1`): `outcome` (`searched` / `no_unresolved_relation` / `budget_exhausted`),
policy (name, rules, fingerprint), requirements and fingerprint, eligibility description/fingerprint/trace id, budget
before/after, selection (selected key, considered with sort keys, skipped with reasons), query (typed terms, submitted
text, artifact ids), search (backend ranking, excluded with reasons, eligible returned), `candidate_delta`, coverage
(before/after states, selected relation and requirement status before/after), rerank (basis, request, ranking with
score / position / `is_new`, final ids) and the trace event.

## 5. Changes outside the new module

* `trace_slice.TraceSlice._event` gained two keyword arguments, `eligibility_profile_id` and `result_limit`, whose
  defaults are the previous constants. P0-T06 events are unchanged (covered by its 22 tests and one new test).
* No store schema change, no fixture change, no change to `providers.py`, `profiles.py`, `budget/` or `scripts/`.

## 6. What is claimed and what is not

Claimed (and tested on synthetic packets): exact requirement preservation; a deterministic, order-invariant, pinned
selection rule; at most one expansion search per call within an explicit budget; eligibility masks on both routes with
recorded exclusions; real before/after membership and new-candidate accounting; one coverage re-check; a rerank that can
see only the original need; schema- and semantics-valid traces; hypothesis-as-evidence refused on every path.

Not claimed: any retrieval-effectiveness gain, any relevance of a new candidate (new membership ≠ relevance), that the
runtime assessor is correct, that the rule is the right one for patents or Thai legal text, or novelty. On the P0-T06
packet the original-query rerank places every new candidate (including the Annex B rule) after the seed clauses, because
none shares a term with the requirement: whether the action improves a final ranking is exactly the open question for
P2-T04 on permitted DEV data against matched controls (static structural queries, generic feedback, random requirement,
shuffled bindings). Nothing here was run on research data.

## 7. Known limits

* An empty eligible seed produces no seed trace event: the owner schema requires at least one source and one node. The
  seed action is still recorded in the `actions` table with its exclusions.
* The FTS5 seed/expansion backend post-filters the mask over a fetch depth of 50; a corpus where more than 50 ineligible
  candidates outrank eligible ones would return fewer than 5 eligible candidates. The pure form exposes `fetch_limit`.
* The pure trace emitter records requirement-level assessments only (relation states stay in the record); its
  requirement status precedence is contradicted > unresolved > supported.
