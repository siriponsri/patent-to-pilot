# SACR generated-view failure policy proposal

Status: PROPOSED, NOT ADOPTED FOR A SCIENTIFIC RUN. No new model attempt authorized.
This resolves implementation cases prospectively; it does not rewrite previous receipts.

## Authority and interpretation

Owner handoff section 8.4 (failure rule near line732) and protocol configuration
invalid_generated_view: discard_view_and_log establish two existing rules: unusable whole
profile uses the frozen anchor; an invalid individual view is discarded while anchor and
other valid views remain. SACR_V0_SPECIFICATION_DRAFT_20261110_EN.md section on failure
behavior and SACR_GENERATION_CONTRACT_DRAFT_20261110_EN.md output gate repeat them.
The fidelity proposal is a separate batch-level gate, not permission for human per-query
repair. The following family-level distinction is an implementation proposal, not a
claim that the owner already specified every transport/parser case.

## Prospective deterministic decision table

| Observed evidence | Proposed handling | Required accounting / prohibition |
|---|---|---|
| Valid response envelope; one proposal mechanically rejected | Exclude that proposal only; preserve other proposals and unchanged anchor | Existing implemented rule; log reasons and original response; no replacement generation |
| Duplicate of anchor or an accepted view | Do not add duplicate | Log duplicate separately from malformed/rejected output; no refill |
| Structurally valid proposal with unresolved vocabulary/meaning | REVIEW_REQUIRED; retrieval stays stopped | Do not call it safe or silently discard ambiguity to manufacture a passing arm |
| Normally terminated generation with malformed JSON/wrong envelope/oversize response/non-EOS termination | Reject the generated family as unusable; preserve unchanged anchor and independently valid deterministic compact proposal, if applicable | New proposed typed GENERATION_REJECTED record; do not salvage substrings, strip fences, repair JSON or accept a sibling from an invalid envelope |
| Missing/invalid generated list item makes the strict envelope invalid | Same family rejection | Strict envelope validation remains intact; no selective repair of malformed structures |
| Explicit empty generic list or null selective abstraction in a valid envelope | Record abstention; keep anchor/independently valid compact proposal | Not semantic success and not a newly generated view |
| Adapter exception, unknown process state, infrastructure failure or unverified timeout | Preserve FAILED/INTERRUPTED only with actual terminal evidence; otherwise unsealed | No automatic conversion to an empty successful family; resolve bounded recovery policy before continuation |
| Whole profile failed or empty | Existing pinned original-anchor fallback for all factorial arms | Do not run dependent view/embedding/search; preserve failure/empty distinction and external baseline costs |
| Runtime scoring failure | Stop scoring cohort with recorded retrieval failure | No partial candidate/query deletion or arbitrary anchor substitution |

Family rejection is proposed as a deterministic per-query failure behavior inside the
intended method. It must not be advertised as a successful test of selective abstraction
when generated selective views systematically fail. Report retained generated-view counts,
anchor-only/compact-only cases, all attempted calls and the unchanged query denominator.
A successful fallback path is an engineering property; configuration-level generation and
fidelity gates still prevent the present failed configuration from proceeding to R3.

## Required integration before adoption

1. Preserve the generation adapter's actual termination status, token/byte counts, raw
   private artifact hash and terminal receipt before parser acceptance. Controller currently
   receives raw bytes and metrics only; that is insufficient to classify infrastructure
   failure versus normally terminated unusable generation.
2. Introduce a new typed result version carrying generated-family outcome/reason and
   independent compact status. Bind replay to the original generation record; never change
   previously sealed v1/v2 outputs or failed attempts. Charge rejection attempts normally.
3. Pass generated-family failure flags through embedding plans, acquisition, selection,
   finalization and aggregate reporting. READY rankings must not erase generation failure.
4. Test generic and selective cases symmetrically, no repaired JSON, no repeat call, known
   and unknown costs, terminal and unsealed failures, and unchanged full cohort.
5. Record a dated methods-log adoption before new generation. R1, compatible generation,
   actual resource caps and fidelity gate remain separate prerequisites. No outcome-based
   policy choice or threshold relaxation is permitted.

## Current evidence and next action

Individual lexical rejection/duplicates and review stops are implemented and fixture-tested.
Whole malformed family currently produces a failed journal stage and blocks downstream work;
this proposal has not changed that behavior. Existing SYN-SACR-001/002 and grammar failures
remain unchanged. No retrieval effectiveness, human validation or semantic guarantee follows.

The next implementation should first bind a typed generation outcome into the controller
rather than broadly catching all exceptions as rejection. Independent safe work can also
address full-index hashing memory while generation and curator gates remain unresolved.
