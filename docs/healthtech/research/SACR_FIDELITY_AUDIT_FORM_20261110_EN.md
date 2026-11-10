# SACR-v0 developer fidelity audit form

Status: BLANK FORM / NO OBSERVATIONS. Use only after an authorized dev sample and prompt/configuration manifest are fixed. This is formative developer review, not independent expert validation. Do not read retrieval scores or qrels to decide whether a rewrite is faithful.

## Record identity
For each item record benchmark, opaque query ID, sample-manifest SHA256, exact allowed-source SHA256, profile-output SHA256, prompt/config/model/code hashes, reviewer role, timestamp and attempt ID. Keep source/generated snippets and IDs in private artifacts; publish only permitted aggregate counts and hashes.

## Required observations
Use yes/no/uncertain/unassessable for judgments; never replace unknown with no. Counts must be observed or null, not default zero.

| Field | What to record |
|---|---|
| available_input | Whether allowed query text exists; preserve missing queries in denominator |
| explicit_condition_present | A stated condition, with source span; not an inferred engineering requirement |
| relation_blocks | Number extracted, number source-grounded, number with an explicit attached condition |
| numeric_conditions / qualitative_conditions | Separate counts; preserve literal quantities/units |
| invalid_source_spans | Count and exact failed offset/text references |
| unsupported_mechanism_addition | Added mechanism words, with source/output snippets |
| unsupported_parameter_addition | Invented number, range, unit, threshold or specification |
| lost_polarity / direction / comparison | Missing or reversed explicit information |
| action_operand_error | Swapped roles, unsupported action or operand |
| attachment_error | Condition attached to the wrong relation; distant occurrence alone is insufficient |
| uncertain_context_removal | Removed domain/material/environment term whose relevance is unresolved |
| complete_failure / partial_failure | Exact attempt outcome and affected views, without retries |
| unchanged_view / duplicate_view | Identity to anchor/other generated view |
| overall_rating | faithful / unsupported / ambiguous / unassessable |
| rationale | Source/output locators and short reason for every unsupported/ambiguous judgment |

## Mechanical versus semantic outcomes
The current validator returns STRUCTURE_AND_SPANS_PASS only. It validates exact Python Unicode-code-point slices, source hash, query identity, schema, source-backed raw roles/conditions/units, source-order blocks and caps. A source-backed phrase can still be assigned the wrong role. An exact source span does not establish attachment, preservation of omitted information or semantic equivalence.

Normalization/replacement flags require review. Even an unflagged profile has fidelity_review=REQUIRED and semantic_status=unknown. Do not use the absence of flags as a semantic approval signal. For example, replacing “low pressure” with “5 kPa” produces normalization flags; no code path here approves that invention. The generated-view acceptance layer remains to be implemented and must reject unresolved unsafe changes before experimental use.

Uncertain conditions do not count as conjunction-ready. Whole failed or empty profiles require anchor fallback; partial records remain visible. Structural validation errors are failures, not discarded queries. There is no automatic retry, post-outcome correction or alternative research method.

## Aggregation and revision
Record denominators separately: sampled queries, available queries, attempted profiles, mechanically valid profiles, generated views, reviewed views. Report full-cohort failure rates as well as conditional fidelity rates. Keep missing/unassessable counts separate. Report condition-present and conjunction-active rates without excluding condition-free queries from primary results.

If review exposes a systematic defect, preserve all outputs and declare a new prompt/code version before any new run. An edited output cannot replace the original attempt. Record developer role and prior exposure to benchmark outcomes as limitations. A second model's disagreement is an auxiliary signal only.

## Acceptance before a pilot
The sample manifest, complete observations and defect disposition must exist. Prompt/token/resource configuration and a precise generated-view acceptance rule must be fixed; actual R1 isolation/eligibility/parity must pass. No universal fidelity percentage threshold is invented by this form. Any adopted threshold and its rationale must be declared before reviewing method outcomes. R2 and R3 are not complete because this form exists.
