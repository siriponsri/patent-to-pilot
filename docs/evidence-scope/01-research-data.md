# S1 · Research data and controls

**Status:** NOT_STARTED. **Track:** research. **Entry:** S0 documentation checkpoint and a later execution goal. **Can start alongside:** S2. **Consumer:** S3. [Master plan](MASTER-PLAN.md) · [Research freeze](FREEZE.md) · [Matched evaluation](03-research-evaluation.md).

## Mission for the next executor

Produce the smallest auditable corpus and evaluation contract that can distinguish a missing witness from a witness already retrieved in an incompatible scope. Document-level or family-level relevance alone cannot make this distinction. The archived 2,000-request patent screen and 1,330 Thai DEV packets supply continuity and text-retrieval controls. They do not constitute the new controlled cohort. S2 can build the product with its own demonstration fixtures while this work runs.

### S1-T01 · Inventory eligible assets and rights

1. Resolve the predecessor receipts and file pins in [the freeze](FREEZE.md). Verify DEV/private files by allowlisted path and streaming hash. Never enumerate contents of protected shards or load sealed judgments to check a hash.
2. Build one source ledger with provider ID, release/revision or effective date, retrieval URL, file name, byte size, SHA-256, role, licence, access basis, extraction and redistribution permission, and device/storage location. For a statute include issuing body and amendment chain. For patents include publication identifier, family and claim dependency. Record translations as separate derived assets.
3. Record installations and eligible downloads under the new owner approval. Use existing inputs first. Product packages require an explicit distribution basis even when a file is publicly accessible. Third-party terms or paywalls need their own resolution. Never ship a citation benchmark's research licence as the product's licence.
4. Return a disposition for each asset: eligible for controlled DEV, auxiliary text retrieval, public demo, research-only historical comparator, pending rights or unavailable. Keep unknowns actionable by naming the missing evidence.

**Acceptance:** a second reader can locate every included byte by ID and hash, distinguish the publication, effective and collection dates, and determine where the file may be used. Missing optional assets do not block controlled fixtures.

### S1-T02 · Normalize source units and assemble initial pools

- Reuse current source IDs, versions, content hashes and Workbench locator conventions. A unit identifies a clause, paragraph, claim, embodiment, or table cell with its row label, column header and footnote context. Retain original wording, language, date, page or official section/claim locator and normalized form. Make accuracy of page geometry explicit when inputs only have OCR text.
- Expose typed relationships recoverable from the source, including inheritance, amendment, exception and table scope. Store the exact paragraph, claim reference, effective-date clause or heading that licenses each relationship. An inferred edge carries its evidence and uncertainty. The research runner and product renderer must agree on IDs and locator semantics.
- Build a small corpus with meaningful distractors. For each request, declare a plausible common seed pool and a shared searchable corpus outside it. Arrange the three states in the freeze without scenario codes in filenames, queries or runtime features. Use equivalent lengths and topical vocabulary for false matches when possible.
- Keep public demos disjoint. An invented statute or patent example must be visibly fictional. For a real example use the allowed text or a link and a versioned locator. For an English patent that needs two embodiments, obtain permitted description text; the prior claims-only index cannot establish embodiment membership.

**Acceptance:** a hand-checkable Thai exception/amendment and an English patent relation each resolve to original units, and each of the three pool states can be realized. One writer owns the source contract during its change. Give S2 a minimal fixture or schema description, independently of the benchmark labels.

### S1-T03 · Prepare controlled pairs and independent judgments

1. Start with a small, balanced pilot of family-disjoint packets, preserving enough sources per scenario for an informative readout. Identify an answerable case whose individually plausible spans refer to different versions, branches, embodiments or table scopes. Also prepare a case with a legitimate cross-source relationship, so the engine cannot succeed by rejecting every multi-source answer.
2. Create both edit directions. Changes with semantic effect include moving an operative date, changing a table heading's scope and substituting an alternative embodiment. Invariance checks include spelling normalization, layout or a paraphrase that preserves the applicable clause. Label the original and variant, permitted witness alternatives and why the outcome should change or stay constant.
3. Keep a separate set of unanswerable cases with finite, documented scope. Record all ambiguous real interpretations for later independent review. Store annotator provenance, disagreement, resolution and revision. Never use the system's preferred answer or an LLM verdict as ground truth.
4. Group by legal lineage, family, near-duplicates, translation and synthetic descendants. Reserve whole families for evaluation. The optimizer's training and edit-selection families must also be separate. Pin counts by domain, state and edit direction, and report differences between controlled and natural material. If natural examples lack independent review, report engineering feasibility there and close the controlled pilot separately.

**Acceptance:** split, rights, evidence and label manifests are versioned independently. A fixture test detects leakage from a translated sibling. A hand-checked invariant pair and a changing pair in both domains produce their authored expected outcomes through the evaluator.

### S1-T04 · Build control contracts and freeze the measurement packet

Pin the strongest primary reference in [FREEZE.md](FREEZE.md). Use the same retriever, available document text, seed pool, candidate budget and reranker across the controller comparison. Match the budget for optimizer edits as well as the budget per request. Where a published implementation cannot run on these units, specify its adapted algorithm, cite the version and label the adaptation explicitly.

| Reference | Capability to reproduce or adapt | Why it matters |
|---|---|---|
| FinDeCrowd-RAG | Fixed-pool compatibility scoring with a rerank-or-keep decision | Isolates ranking relief from discovery of a missing witness. [Paper](https://arxiv.org/abs/2609.35782) |
| MAP-Law | Requirement coverage and marginal gain control continued search, redirection or stopping | Tests whether compatibility at action selection adds value to an existing adaptive policy. Combine this controller with the preceding ranker for the principal comparison. [Paper](https://arxiv.org/abs/2605.01486) |
| n-Clue | Complete-first ranking against partly satisfied alternatives | Measures coverage when every condition must be found. Our controlled incompatible-scope cases include texts that appear to cover every condition. [Paper](https://arxiv.org/abs/2607.24165) |
| SkillOpt and HarnessOpt | Frozen target model with optimized skill text or execution policy | Separate a better instruction from a better choice of action. Include the unoptimized starting point. [SkillOpt](https://arxiv.org/abs/2605.23904) · [HarnessOpt](https://github.com/EvolvingLMMs-Lab/SkillOpt-Lite) |
| FiNE-Patents and NitiBench | Patent feature grounding within supplied references and Thai legal section retrieval | Provide task-specific external context. Report their scoreboards independently from open-corpus discovery and the new controlled endpoint. [FiNE-Patents](https://arxiv.org/abs/2605.02392) · [NitiBench](https://aclanthology.org/2025.emnlp-main.1739/) |

Record exact budgets, initial-pool construction, eligibility, deduplication, ties, annotation inclusion, action accounting, scorer hash, baseline configuration and ordered case IDs. Freeze before sampling outcome-dependent examples, optimizer selection or computing a metric. A hash-only reference to a private approved manifest is sufficient for the Git receipt.

### Handoff and light gate

Write a timestamped S1 receipt listing the checks that passed and the exact unverified gaps, manifests and versions needed by S3. Link it from the active task status and handoff. Keep raw private data outside Git. A runnable controlled pilot, frozen primary reference and documented coverage suffice to advance S3. A rights-cleared subset or controlled synthetic pilot may close feasibility without authorizing claims about natural Thai law, patent validity or generalization. Phase closure and score improvement have independent meanings.

**Suggested first instruction for GPT 6.2 high:** read the freeze, verify the inherited DEV receipts, then create the S1-T01 rights ledger and S1-T02 hand-checkable examples. Stop before the first scored run until the packet, scorer and resource ceilings are pinned. Coordinate only shared schema changes with S2.

## Dispatch status

| Task | State | Receipt |
|---|---|---|
| S1-T01 | NOT_STARTED | Pending |
| S1-T02 | NOT_STARTED | Pending |
| S1-T03 | NOT_STARTED | Pending |
| S1-T04 | NOT_STARTED | Pending |
