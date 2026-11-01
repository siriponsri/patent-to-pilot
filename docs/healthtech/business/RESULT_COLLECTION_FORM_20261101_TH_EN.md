# Result collection form / แบบเก็บผล

Status: `TEMPLATE / CURRENT_ROUND_NOT_RUN`

Use this form for future authorized task sessions or for a clearly labeled owner self-evaluation. Do not fill missing fields with estimates.

## Session record

| Field | Value |
|---|---|
| session_id | `<PRIVATE_RECORD>` |
| participant_mode | `NOT_RUN` / `DEVELOPER_SELF_EVALUATION` / `EXTERNAL_PARTICIPANT` |
| participant_code | `<PRIVATE_RECORD>` |
| case_id/device | `<CASE_ID>` |
| workflow/method | `<METHOD_ID>` |
| evidence_manifest_hash | `<SHA256>` |
| software/candidate revision | `<GIT_REVISION>` |
| start_utc | `<NOT_RUN>` |
| end_utc | `<NOT_RUN>` |
| human_time_seconds | `<NOT_RUN>` |
| machine_time_seconds | `<NOT_RUN>` |
| gpu_time_seconds | `<NOT_RUN>` |
| support_time_seconds | `<NOT_RUN>` |
| provider_calls | `<NOT_RUN>` |
| token_count | `<NOT_RUN>` |
| paid_cost_usd | `<NOT_RUN>` |
| correction_count | `<NOT_RUN>` |
| export_reopened | `<NOT_RUN>` |

## Evidence and citation checks

| Measure | Result | Evidence path |
|---|---|---|
| exact source locator resolved | `NOT_RUN` | `<PATH>` |
| disclosed/candidate/unresolved separation | `NOT_RUN` | `<PATH>` |
| required-field coverage | `NOT_RUN` | `<PATH>` |
| unsupported or rejected items | `NOT_RUN` | `<PATH>` |
| history version and reopen check | `NOT_RUN` | `<PATH>` |
| JSON/EN/TH export check | `NOT_RUN` | `<PATH>` |

## Rubric scores

Record each score from the task/rubric file and keep dimension-level failures visible.

| Dimension | Score 0-2 or `not_run` | Notes |
|---|---|---|
| source locator | `not_run` | |
| link classification | `not_run` | |
| evidence coverage | `not_run` | |
| citation quality | `not_run` | |
| correction safety | `not_run` | |
| decision handoff | `not_run` | |

## Interpretation guardrails

- A developer self-evaluation is not independent user validation.
- A deterministic citation check is not semantic patent relevance gold.
- Machine time and human time must not be merged.
- Scenario labor rates and dossier volumes are hypothetical sensitivity inputs, not observed revenue or ROI.
- No willingness-to-pay, purchase, repeat-use, customer, or market claim is allowed unless the corresponding evidence is present and authorized for reporting.
