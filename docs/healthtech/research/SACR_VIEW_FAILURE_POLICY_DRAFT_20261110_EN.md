# SACR generated-view failure policy proposal

Status: ADOPTED PROSPECTIVELY by the owner's explicit 10 November 2026 chat reply;
typed family-rejection continuation is NOT_IMPLEMENTED and no scientific run has
used it. This policy alone authorizes no additional model attempt. Earlier proposal
wording below describes the adopted design, not completed runtime behavior.
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

1. Typed generation records now bind reported termination, token/byte counts, raw private
   artifact hash and costs before parser acceptance through generated profile/view adapters.
   Execution v3 requires these adapters; legacy interfaces remain for older declarations.
   Actual process-terminal evidence and runtime identity still require independent capture;
   a bound normal-return record alone cannot attest real model execution.
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

Typed generation outcomes and failed-attempt costs are now bound in the controller/journal;
see the [generation-failure evidence](../audits/ptp-method-first-generation-failure-evidence-20261110/README.md)
and [execution-v3 contract](../audits/ptp-method-first-required-generation-20261110/README.md).
`GenerationEvidenceFailure` preserves verified failure evidence and still seals FAILED;
it does not implement GENERATION_REJECTED or permit dependent retrieval. The owner has adopted the policy prospectively. Next is versioned implementation
of items 2–5, with acceptance checks before any use in a scientific run. Do not reinterpret existing failed receipts as completed rejected families.
