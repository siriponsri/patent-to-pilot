# Independent integrity and R1 budget review

Snapshot: `db0798276e3158b04131b4e910abc0a11511e94c` (start and end). Read-only review of the changes since `889958e`; exact Git archive used for isolated checks. No repository implementation/status changes, credential reads, SSH, network, remote provider, neural model or paid execution. This subtask does not audit datasets, vector implementation or scientific completeness.

## Verified repairs

- Old F1 evidence-statement leak is repaired on the tested path: `healthtech/rights.py:220` projects external evidence, rebuilds allowed structured values from source payloads, and omits unreviewed/quote-only items. `engine.py:224` uses this in Markdown; `engine.py:295` uses it in JSON serialization. History-reload and nested/encoded evidence regressions pass.
- Old F2 is repaired on the Abbott adapter path: `healthtech/abbott.py:113` validates manifest/runtime/registry/raw-file identities and safe runtime paths; `build_abbott_case_inputs` invokes it. Independent isolated tests reject runtime/text/raw/registry/missing-file/metadata mutations and duplicate IDs after resealing. No new real-corpus/model run was performed by this subtask.
- Old F3 is repaired at the assurance boundary: `evaluation/healthtech/provenance.py:70` resolves against the reviewed policy matrix; unknown/mismatched/blank IDs become `PASS_WITH_UNRESOLVED_RIGHTS` / `UNRESOLVED_TYPED_POLICY` (`:315`), rather than verified typed binding. Adapter rejects unknown/mismatched declared IDs.
- R1 policy is versioned separately from historical USD5 policy. Same-database reservation transactions, duplicate attempts, old-policy DB mismatch, timeout/unknown billing, billed schema/model/provider failure and observed-debit-over-reservation tests pass. USD8 is authorization ceiling and USD7 admission ceiling in the implementation.

## Findings and limits

### IB-1 — P2, proven external query-metadata projection gap

`src/patent_to_pilot/healthtech/engine.py:297` serializes the whole dossier, then filters `sources[*].payload` and `evidence`; it leaves `query.company_metadata` intact. The adapter explicitly binds copied applicant metadata to `company_source_id` at `healthtech/abbott.py:445` / `:446`.

Reproduction uses the existing authored Abbott fixture, source intended-use ALLOWED, and a reviewed-field allowlist containing only `trade_name`. Both product-display and redistribution JSON correctly expose only `{trade_name: MitraClip}` in source payload and omit applicant evidence, but still emit `query.company_metadata.applicant == ABBOTT MEDICAL` under the same source ID. This is source-derived metadata, not a manually added user note. Thus the all-channel field-boundary claim has a blind spot beyond the repaired evidence path.

Evidence: `query-projection-probe.json`, `summary.json`; script `probe_and_tests.py`. No real restricted source material was released. Current production FDA policies may permit applicant; this fixture proves generalized policy enforcement inconsistency, not an observed public data leak. Minimal repair is a provenance-aware projection of copied query metadata (or explicit public/user-authored origin), preserving local research values.

### IB-2 — P1 operational guard gap before future live use: same authorization can use separate ledgers

`scripts/healthtech/run_b4_controller.py:313` accepts arbitrary `--budget-path`; `:156` opens it. `providers/round1.py:138` / `ProjectBudget.__init__` bind policy hash within one DB but do not enforce a canonical per-authorization ledger path or authorization registry across DBs.

Offline simulation creates ledger-A and ledger-B with the same `PTP-HT-OR-R1-20261028-USD8` authorization. Each independently admits and settles synthetic phase exposures 5.40 + 1.20 + 0.40 = USD7; neither marks breach. Aggregate simulated exposure is USD14 under one USD8 authorization. This demonstrates application scope depends on the operator always choosing the same path. Same-path concurrency tests do not cover this case.

Evidence: `budget-scope-probe.json`, `budget_scope_probe.py`. **Actual cost is USD0; no transport/provider call was made.** This is not a finding of historical overspend and not a malicious-code containment claim. A release runner should bind the round authorization to one canonical ledger through immutable run/activation config and reject resume/workers pointing elsewhere. It should not reset or rebind historical journals. This condition must not be used to block offline/remote embedding compute, which need not use OpenRouter.

### IB-3 — P2 API assurance limitation, not demonstrated CLI exploit

`healthtech/b4_live.py:146` checks only that `pricing.model` is a policy model. Constructor accepts a different pricing snapshot hash/time/upstream provider than the policy; rates and max_price guards can also disagree. Probe supplies policy snapshot `a...`, pricing snapshot `c...`, pricing time 1900 and different upstream, and the constructor succeeds. No select/complete/transport call is executed.

Current `run_b4_controller.py` builds both policy and pricing from the same file, so this mismatch is not observed through that CLI. Before reusable live API use, validate pricing hash/time/provider and rate-guard consistency at the selector boundary. Also source review notes `b4_live.py:189` cost calculation uses `input_bound` while request/AttemptLedger include `schema_framing_tokens` (`:198`); this is an unverified full-request-bound consistency concern, not a demonstrated real token overrun or charge.

## Independent checks

Command in audit-owned directory: `rtk python -B probe_and_tests.py` after extracting exact HEAD to `snapshot/`. Selected modules: `test_healthtech_repairs`, `test_healthtech_boundary_matrix`, `test_healthtech_round1_budget`, `test_healthtech_b4_live`.

Result: **62 passed, 1 skipped, 0 failures**, exit 0. Skip is absent pinned tokenizer artifact; snapshot has no local model cache. Network sockets/DNS were blocked in-process, pytest plugin autoload disabled. Network attempts 0, remote provider calls 0, neural calls 0. Existing unit tests use mock transports/synthetic billing, which are not paid inference.

Additional command: `rtk python -B budget_scope_probe.py`; exit 0; two-ledger and pricing-constructor counterexamples as above. The probe scripts expect an audit-owned `snapshot/` beside the script and fresh probe/ledger output paths. Do not run them against production journals. Raw tests/fixture histories/SQLite simulation DBs stay in scratch; only small authored JSON/scripts/this report need continuation persistence.

No denied actions or unresolved execution blockers occurred. Broader source coverage, complete project tests and main audit acceptance remain the parent audit's responsibility.
