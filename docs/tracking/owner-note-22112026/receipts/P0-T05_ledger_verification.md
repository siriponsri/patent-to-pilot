# P0-T05 receipt: shared budget reservation ledger

**Date:** 22 November 2026. **Outcome:** implemented and verified offline with fake provider responses. **Spend:** USD 0
(no inference call, no paid call, no download; OpenRouter prices were read with the free catalogue tool only).
**Forecast:** [P0-T05_budget_forecast.json](P0-T05_budget_forecast.json).

## What exists now

| File | Role |
|---|---|
| `src/patent_to_pilot/budget/ledger.py` (+ `__init__.py`) | Stdlib-only SQLite ledger; envelopes, owner approval records, one row per attempted paid request, events; CLI `python -m patent_to_pilot.budget.ledger status / approve / reconcile / recover-stale / import-workbench / events` |
| `scripts/research/g03_a3_llm_expand.py` | A3 caller: reserves before every HTTP attempt, settles from `usage.cost`, pauses on unknown cost; config-driven for A3r1 (`--config`, `--max-tokens`, `--calibration`, `--plan`, `--envelope`, `--budget-ledger`) |
| `docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json` | Tracked A3r1 caller config (4 primary models, 800 tokens, envelope E1R, both enable flags **false**) |
| `src/patent_to_pilot/workbench/providers.py`, `profiles.py` | Workbench paid remote calls go through the same ledger (scope `workbench`); usage list shows a settled cost when known |
| `tests/test_budget_ledger.py`, `tests/test_g03_a3_caller_budget.py` | 17 + 10 tests, fake HTTP only |

SHA-256 at verification: `ledger.py` a938e0e1…c424a, caller 1cd4bbd2…19ccd, A3r1 config 4ce3d3bc…c0e2.

## Accounting rules implemented

- **Location:** `%PTP_BUDGET_LEDGER%`, else `%LOCALAPPDATA%\PatentToPilot\budget\ledger.sqlite3`. A path inside a git work
  tree is refused. Research caller and Workbench share this file on one machine.
- **Dispatch rule**, inside one `BEGIN IMMEDIATE` transaction: settled + outstanding reserved + unknown-cost reserved +
  this attempt's maximum ≤ the envelope's operational limit; attempted requests + 1 ≤ request cap; scope and per-profile caps
  checked in the same transaction.
- **Per-attempt maximum:** (UTF-8 bytes of the request body + 256 template tokens) × input price + `max_tokens` × output
  price, at the **highest endpoint price** OpenRouter listed on 22 Nov 2026 (routing is not pinned). Unknown price means no
  dispatch.
- **Outcomes:** reported cost → `settled`; HTTP error answer or connection refused before sending → `released` (cost 0, still
  one attempt); timeout after sending, unreadable answer, or a 200 answer without `usage.cost` → `unknown`. Any `unknown` entry
  **pauses** the envelope until `reconcile` records a cost and its evidence. Retries are attempts with their own reservation.
- **Restart:** reservations persist; `recover_stale` (the caller runs it at start, lease 900 s) turns orphaned reservations
  into `unknown`.
- **Envelopes:**
  - **E1 (ACTIVE):** approval seeded from OWNER-DECISIONS D9. Limits: hard USD 8.00, stop-and-report USD 6.00 (this is the
    operational limit until a `continue_past_stop` approval is recorded), 35,000 requests, Workbench scope ≤ USD 0.20.
  - **E1R (configured, disabled):** hard USD 50, notify USD 40 (reported once), 100,000 requests. It is cumulative: E1 spend
    counts inside it. It **refuses dispatch (`not_approved`) until** `approve --envelope E1R --evidence "<owner's words and
    where>"` is recorded. Once approved, it supersedes E1.
- **History:** the four A3r0 smoke calls (USD 0.00064223, 4 requests, generation IDs) are seeded as one idempotent
  historical E1 entry. No Workbench store existed at the default path, so Workbench spend to date is USD 0 / 0 requests.
  HANDOFF also records that the real check still waits for the key. `import-workbench` would import later rows made
  before the ledger existed, as unknown when their cost is missing; it skips rows that already carry a ledger entry.

## Tests run (exact results)

Command: `python -c "import sys; sys.path.append(r'.venv/Lib/site-packages'); import pytest; sys.exit(pytest.main([...]))"`
with system Python 3.12.

- `tests/test_budget_ledger.py`: **17 passed**: `test_seed_has_e1_approved_e1r_pending_and_historical_smoke`,
  `test_ledger_refuses_a_path_inside_the_git_repository`, `test_default_path_is_env_or_user_data_dir`,
  `test_reserve_settle_release_counts`, `test_thread_reservations_never_exceed_the_cap` (16 threads × 20 attempts of
  USD 0.03 against USD 1.00 → exactly 33 accepted), `test_process_reservations_never_exceed_the_cap` (4 separate OS
  processes × 30 attempts of USD 0.05 → exactly 20 accepted), `test_retries_are_attempts_and_the_request_cap_holds`,
  `test_unknown_cost_pauses_dispatch_until_reconciled`, `test_reservations_persist_across_restart_and_stale_ones_pause`,
  `test_disabled_e1r_refuses_until_an_owner_approval_record`, `test_e1_stop_threshold_then_hard_limit`,
  `test_notify_threshold_is_reported_once`, `test_workbench_scope_cap_inside_e1`,
  `test_unknown_price_is_refused_and_estimates_are_bounds`, `test_import_workbench_usage_reconciles_without_double_counting`,
  `test_workbench_paid_remote_calls_use_the_shared_ledger`, `test_workbench_paid_route_without_an_envelope_is_blocked`.
- `tests/test_g03_a3_caller_budget.py`: **10 passed**: `test_a3r0_prompt_is_byte_identical_to_the_frozen_amendment_text`
  (code prompt equals the amendment-3 text block; system line equal; default 400 tokens; A3r0 body keys and order),
  `test_every_attempt_is_reserved_retries_counted_and_costs_settled` (the fake key never reaches the ledger or outputs),
  `test_timeout_after_send_pauses_dispatch_until_reconciled`, `test_answer_without_usage_cost_is_unknown_not_zero`,
  `test_request_cap_includes_historical_calls_and_retries`, `test_calibration_selection_is_fixed_train_only_and_model_independent`,
  `test_tracked_a3r1_config_loads_800_tokens_and_stays_disabled`,
  `test_a3r1_calibration_is_refused_by_the_ledger_while_e1r_is_pending` (0 calls while pending; 32 calls at 800 tokens after a
  test approval record), `test_typhoon_without_a_verified_price_is_never_dispatched`,
  `test_owner_shape_config_and_max_tokens_override`.
- The new tests plus the existing `tests/test_ptp_g02_providers.py` and `tests/test_ptp_g02_openrouter_profiles.py`:
  **45 passed**.
- **Full suite:** **2534 passed, 8 failed, 6 skipped, 1 xfailed** (139.9 s). The 8 failures are exactly the accepted
  `test_sacr_r2_smoke_supervisor.py` / `test_sacr_r3_smoke_supervisor.py::test_budget_cannot_use_nonfinite_inflated_or_erased_cost`
  [nan, inflated, erased, insufficient]. The suite ran on a shared working tree where other agents had uncommitted changes.
- A separate script compared the request bodies with the pre-change caller: they are byte-identical for all four A3r0 models
  (`json.dumps` equality). `USER_TEMPLATE` and `SYSTEM` are unchanged.

## Behaviour changes to know

1. **A3r0 timeouts are no longer retried.** Amendment 3 allowed up to 2 retries for timeouts. A timeout may already have
   been billed, so the owner's unknown-cost rule (A3 checkpoint §6) now takes precedence: the attempt is marked unknown and
   dispatch pauses. HTTP 408/429/5xx answers are still retried up to 2 times, and connection-refused errors before sending
   are released and retried.
2. **The A3r0 USD 6.00 / 35,000 stop is now counted across the whole envelope.** It includes the historical smoke calls and
   any Workbench usage, instead of only the caller's own JSONL files. `--max-usd` and `--max-requests` remain as extra
   ceilings.
3. **Some Workbench paid remote routes are now blocked.** This covers any route without an approved envelope covering its
   provider (for example `anthropic_native` to api.anthropic.com) and any route without a known price (remote embeddings or
   rerank). Loopback routes are unchanged.
4. **A3r1 output layout:** `<ledger-root>/A3r1/<model>/…` and `<ledger-root>/A3r1/calibration/<model>/TRAIN.jsonl`, plus
   `calibration-manifest.json`. A3r0 keeps its original layout.

## Limitations (not verified here)

- **No real provider call was made.** The OpenRouter `usage.cost` field and timeout semantics are taken from the existing
  smoke receipts and documentation.
- **This is a local guard, not a provider-side limit.** The OpenRouter account has no provider-side cap configured by this
  work.
- **One ledger per machine.** If the caller runs on dr-train, its ledger there is separate from the PC's ledger, and the
  dr-train sync must include `src/patent_to_pilot/budget/`. Recommendation: run paid callers from one machine only (the
  owner PC, which also hosts the Workbench), or copy the ledger before and after.
- **Worst-endpoint reservation prices** were read once (22 Nov 2026) and change as OpenRouter adds providers. The DeepSeek
  V4 Flash worst endpoint is about 10× its list price. Pinning `provider.max_price` in the A3r1 config before calibration is
  recommended (see the forecast).
- **Typhoon has no verified price**, so the ledger refuses it until a `reservation_price` is recorded.
- **The calibration input must be a TRAIN-only extract**, which does not exist locally yet. The caller aborts on any
  non-TRAIN row in calibration mode.
- **E1 approval is seeded from the recorded D9 decision.** E1R stays pending. This receipt does not approve or enable any
  paid run.
