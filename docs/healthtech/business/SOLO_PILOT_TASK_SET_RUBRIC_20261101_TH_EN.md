# Solo computational pilot task set and rubric / ชุดงานและเกณฑ์ประเมิน

Status: `PREPARED / NOT_ACTIVATED / NO_EXTERNAL_PARTICIPANTS`

Purpose: preserve a usable task packet for future authorized target-user work while allowing the current project to proceed without participant recruitment. Any owner-run exercise must be labeled `developer_self_evaluation`.

## Current boundary

No participant is enrolled, no invitation is being sent, and no human validation claim is made. The current O1-O4 work is a reproducible computational study plus real permitted case studies.

## Target-user task set for future authorized use

Use one named device/comparator and one concrete diligence or information-request decision. Give every compared workflow the same case, evidence cutoff, source list, and output schema.

1. Locate the source and exact locator for one important device or regulatory fact.
2. Inspect one feature-evidence row and classify each patent entry as `disclosed_link`, `retrieved_candidate`, or `unresolved`.
3. Compare two candidates and record why one has stronger source support without inferring clinical, FTO, validity, or approval conclusions.
4. Identify missing evidence and write the next information request.
5. Correct one seeded dossier issue while preserving the audit trail.
6. Reopen the saved version, inspect the source view, export JSON/English/Thai, and state whether the dossier is ready for the next discussion.

Target duration is a planning value only. Record observed time; never convert the target into a result.

## Rubric

Score each dimension 0, 1, or 2. Record `not_run` when the task was not attempted.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Source locator | No source or wrong source | Source identified but locator incomplete | Exact source and locator resolve |
| Link classification | Candidate/disclosure/unknown conflated | Mostly correct with one ambiguity | All visible entries correctly separated |
| Evidence coverage | Key required fields unsupported | Partial coverage with explicit gaps | Required fields covered or explicitly unresolved |
| Citation quality | Citation cannot be checked | Citation opens but support is partial | Citation and locator support the stated field |
| Correction safety | Edit loses history or overwrites source | Edit saved with a minor traceability issue | Edit, history, reopen, and export remain consistent |
| Decision handoff | No next decision or unsupported claim | Next step is vague but bounded | Next request is concrete and evidence-linked |

Do not average away a critical failure. Report the per-dimension scores, missing fields, rejected evidence, and any support required.

## Measurement rules

- `machine_time_seconds`: measured backend/local/GPU execution time.
- `human_time_seconds`: observed person time, `NOT_RUN` unless actually measured.
- `support_time_seconds`: any manual help, kept separate from machine time.
- `correction_count`: edits or rejected evidence items, not a satisfaction score.
- `citation_accuracy`: source/locator checks using deterministic review, not an agent judge.
- `evidence_coverage`: required-field coverage under the declared dossier schema.
- `participant_mode`: `NOT_RUN`, `DEVELOPER_SELF_EVALUATION`, or `EXTERNAL_PARTICIPANT`.

Owner-run results are formative and biased toward the builder's familiarity. They cannot be reported as independent user validation.

## Future outreach boundary

Recipient list: empty. No message has been sent. A future invitation needs owner review and authorization before sending; contact details and consent records must remain outside public Git.
