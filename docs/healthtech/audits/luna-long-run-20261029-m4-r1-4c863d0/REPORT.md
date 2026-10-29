# M4 R1 report

## Objective

Create a versioned, durable R1 OpenRouter budget/runner seam without mutating the historical USD5 policy or dispatching paid inference.

## Acceptance

| Criterion | Status | Evidence |
|---|---|---|
| Versioned `$8` policy and `$7` admission threshold | PASS | `src/patent_to_pilot/providers/round1.py`; `tests/test_healthtech_round1_budget.py` |
| Exact model/provider and price-snapshot binding | PASS | `build_round1_policy`, config-version mismatch regression |
| Historical policy/journal preservation | PASS | legacy provider suite and old-policy DB regression |
| Durable reservation before send | PASS | SQLite `pending` observation during transport send |
| Crash/timeout/unknown billing fail closed | PASS | synthetic `BaseException` and timeout tests |
| Replay/concurrency/cap accounting | PASS | duplicate attempt and two-writer tests |
| Billing/identity/schema failure ordering | PASS | malformed cost, overrun, model/provider drift, schema tests |
| Live canary / paid pilot | NOT_RUN | no current readiness/credential/credit/rights gate was opened |

## Exact R1 policy

- Authorization: `PTP-HT-OR-R1-20261028-USD8`
- Total cap: `8000000000` nano-USD
- Admission threshold: `7000000000` nano-USD
- Phase caps: `canary=400000000`, `paired_pilot=5400000000`, `robustness=1200000000` nano-USD
- Concurrency: `1`
- Retries: `0`
- Unknown billing: blocks future dispatch
- Data classes: only `public` or `synthetic` at the shared budget boundary

## Limits

The model/provider map and pricing snapshot are caller-supplied verified inputs; this package does not assert current OpenRouter availability or pricing. No current metadata refresh, balance check, credential check, transfer-rights approval, live request, generation reconciliation, canary, pilot, SciFact differential, or final scientific claim was performed here. Abbott/Boston remain development-only and the Bridge blocker is unchanged.
