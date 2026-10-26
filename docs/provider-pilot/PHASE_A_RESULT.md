# Phase A live closeout

Status: **PHASE_FAILED** (terminal under the approved two-attempt plan).

| Job | Result | API-reported debit |
|---|---|---:|
| smoke-1-1 / Gemini | Historical model_drift; actual mismatch unknown | USD 0.0000132 |
| smoke-1-2 / GPT | success; exact model/upstream and output schema validated | USD 0.0000600 |
| Total: 2 attempts, 0 retries | No unknown billing or outstanding reservation | **USD 0.0000732** |

The remaining GPT request used `openai/gpt-4.1-mini` through OpenRouter with the
approved `openai` route. The response reported exactly `openai/gpt-4.1-mini` and
`OpenAI`, canonical upstream `openai`. Usage: 86 input + 16 output tokens.
Its validated output was `{"ack":"ready","case_id":"smoke-1-2"}`.

The focused offline identity repair passed 88 tests; tested source hashes and
approval were checked unchanged before execution. The actual journal was
reconciled read-only immediately before resume: one settled historical Gemini
attempt, USD 0.0000132 prior debit, no unknown billing. Exactly one additional
request was made. Billing was retained before identity/schema validation.

The historical Gemini failure was preserved, not relabeled as a success. It lacks
captured response identity, so the live mismatch cause remains unknown. A mock
reproduction does not prove that historical cause. GPT success therefore does
not make the aggregate phase complete, and the CLI's nonzero terminal exit is
expected for this preserved phase failure.

Both approved attempt slots are spent. **Do not dispatch this phase again, reset
state, retry Gemini, or expand to Phase B.** Additional work requires a separately
reviewed plan/approval that preserves this journal and prior charges. USD 0.60
was a ceiling, not a spending target; the funded USD 10 was not authorization
to use the remaining balance.

These were synthetic echo transport tests. No private patent/user documents were
sent, no scientific result is claimed, and no key values were printed or included
in the report. Source details, validated identities and usage are recorded in
`phase-a-result.json`; the authoritative execution evidence is the existing
`results/development/provider-pilot/live.sqlite3` journal. No commit/push was made.
