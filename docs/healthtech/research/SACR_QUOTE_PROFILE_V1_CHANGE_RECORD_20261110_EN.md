# Prospective SACR quote-profile v1

Status: IMPLEMENTED; SYN-SACR-002 MODEL_OUTPUT_INVALID_JSON. This is a versioned engineering response to SYN-SACR-001, not a repair of its generated output or a benchmark protocol amendment.

## Evidence motivating the change
SYN-SACR-001 completed model inference but the profile failed exact span validation. Seven slice mismatches were observed; six quotations occurred once in the authored source and one did not occur. These facts suggest that numeric offset generation is a fragile interface, but do not show that the remaining extraction or semantic relationships are correct. Its two outputs and invalid-profile result remain unchanged. No output is retrospectively reprocessed as a successful v1 profile.

## New model output contract
The new prompt is prompts/sacr_profile_quotes_v1.txt, addressed by prompt kind profile_quotes. Identity version is sacr-profile-quotes-v1. Existing profile fields/caps/allowed inputs remain; source_spans entries now contain exactly field=allowed_query and literal text. The model must not provide start/end. It may quote a longer contiguous source context to distinguish repeated short phrases, but cannot join disjoint fragments or invent context.

The prompt explicitly says eight blocks is a maximum, not a target, and asks for coherent relations instead of redundant fragments. This additional instruction is part of the version change and must be reported; any observed improvement cannot be attributed solely to offset handling. All old prompts and SYN-SACR-001 code/declaration remain available and unchanged.

## Deterministic alignment
resolve_quote finds the exact Unicode-code-point substring in the immutable source. It accepts only one occurrence, including overlapping-match detection. Absent, ambiguous, empty, differently cased, whitespace-normalized or non-source quotations fail. There is no fuzzy search, normalization, synonym substitution, nearest match, ordinal guessing or offset repair.

The adapter operates only on explicitly versioned v1 proposals. It copies the proposal, computes start/end, maps to the existing sacr-profile-v0 canonical structure and runs every existing validator. The proposal object and raw generated response remain untouched. Alignment receipt records proposal/canonical hashes, resolved-reference count and exact policy. Raw-response hash remains in the generation receipt; canonical JSON hashes are separately named and not confused with original byte hashes.

Numeric offsets supplied in v1 are rejected as extra fields. V0 output, including the failed smoke output, cannot be passed to this adapter. Unknown label fields, source-identity mismatch, role/condition/unit errors and duplicate/schema failures still fail. An ambiguous quotation produces a failed profile, not a request to rerun the model.

## Interpretation and next experiment gate
Canonical structural PASS remains semantic_status unknown and fidelity_review REQUIRED. Exact quotations do not prove role assignment, attached-condition relevance, completeness, preserved meaning or retrieval utility. The conservative view screening and its role-reversal limitation are unchanged.

Before another model run, declare a distinct synthetic engineering attempt with fixed fixtures, prompt/configuration hashes, resource limits and no retries. Preserve SYN-SACR-001 as failed; do not relabel the new attempt as its continuation or replacement. No v1 model inference has been performed. A successful synthetic check would still not satisfy actual R1 isolation/A03/parity or authorize R3/protected evaluation.

## Actual model checkpoint
SYN-SACR-002 returned EOS-complete but syntactically invalid JSON. Alignment was not reached; no claim that quote-profile v1 works on actual model outputs is supported. The original raw output and prior failed smoke remain preserved; no repair/retry. See ../audits/ptp-method-first-r2-quote-smoke-20261110/README.md. Earlier future-tense statements above describe the prelaunch state.
