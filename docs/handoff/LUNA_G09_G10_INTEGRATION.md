# Luna handoff — G09/G10 development integration slice

Date: 2026-10-25
Status: **BOUNDED_G09_G10_TARGETED_ACCEPTANCE_ACCEPTED; scoped commit ready; full G09/G10 remains open**
Owner boundary: Luna integration writer. Pepo reviews this result before any commit/push.

## Acceptance decision

Pepo confirmed `BOUNDED_G09_G10_TARGETED_ACCEPTANCE_ACCEPTED` after the
targeted regressions and reports were reviewed. This records acceptance of the
bounded offline implementation slice only; it is not acceptance of full G09 or
G10, a main benchmark, a scientific utility result, or a paid pilot.

## Outcome

The offline deterministic path now connects the existing typed core, fictional
profiles, public-input case packets, source-linked evidence, route options,
revision records, and a readable handoff report for PTP-0001–0003. This is a
development slice only. It is not full G09/G10, full G05/G06, a main benchmark,
or evidence that an AI system beats a baseline.

## Files added or changed in this package

- src/patent_to_pilot/integration/pipeline.py — public-input allowlist adapter, typed agent packet, deterministic facts/options/routes, traceability checks, revision/diff persistence and report export.
- src/patent_to_pilot/integration/__init__.py — integration exports.
- scripts/run_g09_g10_integration.py — one-command offline runner.
- tests/test_g09_g10_integration.py — allowlist, profile binding, case rules, scoped revision/preservation and report tests.
- tests/fixtures/audit_regressions/ — persistent synthetic regression matrix and fixture notes; no evaluator oracle.
- configs/g09-g10-api-smoke.toml — proposal only; no provider/key/call.
- results/development/g09-g10/integration.json — generated machine-readable result.
- results/development/g09-g10/integration.md — generated compact summary.
- results/development/g09-g10/integration.html — generated static report for a non-developer reader.
- configs/g09-g10-example-input.json — synthetic caller-supplied two-state input with new project/profile/source/policy IDs.
- scripts/run_g09_g10_workflow.py — CLI for schema-valid caller-supplied workflow sequences.
- results/development/g09-g10-new-input/workflow.json — measured new-input JSON report.
- results/development/g09-g10-new-input/workflow.md — readable new-input report.
- results/development/g09-g10-new-input/workflow.html — static new-input report.
- docs/research/PILOT_READINESS.md — bounded pilot question, fair baselines, data requirements, measurements and complexity decision rule.

No file under methodology/evaluation/ was modified. No G01/G02/G03/G04/G07/G08 contract or fixture was rewritten, and no evaluator-only answer was used to generate an output.

## Targeted audit corrections

- Metrics are now calculated from an independent DevelopmentEvaluator result for every public state, including S0. The evaluator checks actual policy changes, no-op preservation, scoped unknowns, route-local status, yield non-fabrication, and integrity gating. It is separate from AgentPacket and receives no expected outputs.
- Public packets now use closed nested Pydantic models for event, policy, options, organization reference, sources/chunks, rules, and output contract. Unknown nested fields are rejected; the adapter does not rely on a blacklist alone.
- Profile version requests are checked explicitly. A requested version other than the available 1.0.0 is rejected; it is never silently replaced with 1.0.0.
- PTP-0001 material matching is role-specific: silicon must occur as substrate material, while silicon carbide/other silicon compounds cannot satisfy substrate evidence. Glass uses its explicit nonconductive-material phrase.
- Evidence integrity checks include SHA-256, reverse/length mismatch, supported offset unit, and source-specific trimmed-coordinate length. Invalid evidence cannot create supported facts or route evidence. Unrelated valid evidence remains usable.
- Route status is stored separately from pack readiness. SQLite read-back compares the full serialized RouteRecord payload, including status, evidence IDs, constraint IDs and unknowns. Change records are also read back.
- Negative tests prove that a method returning S0 for later states and a method inventing yield are rejected by the independent evaluator.
- The independent evaluator now checks every required route/option and required value field, including yield, count and cost; unsupported values and swapped route outcomes fail.
- The generic workflow path accepts caller-supplied IDs, profile versions, evidence, options, policies and events without case-ID lookup. Its first synthetic run used NEW-PROJECT-ALPHA, NEW-ORG-Z, NEW-SOURCE-1 and NEW-POLICY-1/2.
- Field-specific evidence validation now checks the declared field, role and value before a required fact or route is treated as supported. A five-stage witness cannot support a fabricated numeric batch cost; unsupported deterministic interpretation stays unknown.
- Elemental silicon matching rejects full-sentence substrate mentions of silicon carbide, silicon nitride and silicon oxide, while an explicit elemental-silicon sentence remains a positive control.
- Evidence coordinates have one canonical locator representation. Locator spans are checked against text length and against optional top-level offsets; a 46-character text with locator `0:1` is invalid even when top-level offsets are absent.
- Generic policy checks are route/component-scoped and report unsupported count forms or mismatches as route-local unknown with explicit reasons. Event `policy_rule_id` conflicts are rejected rather than silently changing policy meaning.
- Revision persistence uses the stored SQLite route history rather than `event_order + 1`; a synthetic sequence `0 → 3` read back versions `1 → 2`. Generic profiles reject nested evaluator fields such as `public_source_context.gold_answer` while retaining allowed source context.

The supplied external audit repro was attempted first, but this runtime could
not read it: audit_repro.py returned an access-denied error and
audit-evidence.json was unavailable at the supplied path. The corrections
above were therefore verified with local TEMP regression cases and the actual
runner output, without modifying frozen fixtures or expected answers.

## Runtime boundary and flow

public-input/S*.json
        ↓ allowlist + forbidden-key check
AgentPacket(case/state/profile/policy/allowed evidence)
        ↓ deterministic rules
source facts + options/routes + scoped unknowns
        ↓ typed RouteRecord / ChangeRecord in temporary SQLite
JSON + Markdown + static HTML handoff report

PublicCaseAdapter reads only methodology/evaluation/cases/<case>/public-input/S*.json and the versioned fictional profile JSON. It rejects evaluator-only keys such as expected_doc_ids, gold_answer, answer_facts, oracle, checked_facts, and future_events. The agent packet contains no expected output or answer key. source_id, evidence IDs, source versions and locators remain separate fields.

Profiles are bound as follows:

| Case | Fictional profile | Version | Evidence input |
|---|---|---|---|
| PTP-0001 | PTP-FIC-ORG-A | 1.0.0 | current public active_chunks |
| PTP-0002 | PTP-FIC-ORG-B | 1.0.0 | current public sources |
| PTP-0003 | PTP-FIC-ORG-C | 1.0.0 | current public sources |

The output labels source facts, fictional stipulations, deterministic
interpretations, unknowns, route status, and proposed next tests separately.
ready_for_review is set by artifact/traceability checks only; reviewer approval
remains not_reviewed.

## New-input CLI prototype

Run a caller-supplied JSON sequence:

    python scripts\\run_g09_g10_workflow.py configs\\g09-g10-example-input.json

The current example produced two states and one policy-change diff. It is a
synthetic development demonstration, not a held-out benchmark. State 0 keeps
both new coating routes as candidates; state 1 changes only the declared
policy, making NEW-A a route-local failure while NEW-B remains a candidate.
The report includes brief, evidence/locators, source facts, unknowns,
proposed test, handoff status, and before/after fields.

The integration persists each allowlisted span as a typed EvidenceRecord and
routes/revisions as typed RouteRecord/ChangeRecord entries. The existing G08
ingestion and FTS retrieval implementations are not invoked for these case
packets: the fixed-source contract exposes spans rather than raw CSV and
forbids corpus expansion. This is reported explicitly in the JSON
interface_status; the deterministic packet rule adapter is the only extraction
path used and model_called=false.

## Case behavior demonstrated

- **PTP-0001:** silicon and glass are initially separate candidate substrate routes. A silicon prohibition affects only the silicon route. Withdrawal of current glass support makes the glass route unknown; it does not turn unrelated evidence into a failure. Production yield remains unknown and no fabrication or clinical claim is emitted.
- **PTP-0002:** PEG carrier evidence is kept distinct from PVP/HPMC crystallization-inhibitor evidence. Forbidding PVP affects option A only. Withdrawal of HPMC support makes option B unknown while option A remains separately represented.
- **PTP-0003:** five reported intermediate stages and two BTC stages are kept as different fields. A count-definition change does not substitute one count for another. Total manufacturing operations and numeric batch cost remain unknown when absent; “inexpensive” is not converted to a number.

All route evidence lists are scoped to the evidence that supports that route,
not the entire packet. A missing-evidence state is route-scoped; it does not
globally block the handoff.

Pack ready_for_review and route-local status are intentionally separate:
ready_for_review describes artifact/traceability completeness, while a route
may independently be candidate, draft, or blocked_by_missing_evidence.

## Revision and persistence

Each public state is processed in order. Routes are serialized as typed
RouteRecord entries in temporary SQLite with version numbers. State changes
produce ChangeRecord entries containing affected_fields,
preserved_fields, reason, source references, before/after payloads in the
report, and a repository read-back check. Project-name-only states produce no
material change. Source withdrawal changes only dependent evidence/facts/routes
and preserves unrelated fields.

The SQLite store is temporary for this bounded runner; it is not a production
database or long-term project memory implementation.

## Runner result

Command:

    python scripts\\run_g09_g10_integration.py

Latest run generated 3 cases and 15 states. Measured result in
results/development/g09-g10/integration.json:

| Check | Result |
|---|---|
| source integrity | PASS |
| required changes recorded | PASS |
| revision read-back | PASS |
| SQLite full route payload/status read-back | PASS |
| preservation checks | PASS |
| unknown handling | PASS |
| route-local status checks | PASS |
| independent evaluator | PASS |
| runner failures | none |
| elapsed time | recorded per run; latest report was 0.044782 s on this machine |
| paid API/GPU/RunPod | NOT_RUN |

The separate new-input run measured 0.003041 seconds for two states and one
change, with source integrity and SQLite read-back PASS.

The HTML report displays the brief/input, allowed evidence and locators,
derived facts, options/routes, proposed next test, handoff state, and
before/after revision summaries:

    Start-Process .\\results\\development\\g09-g10\\integration.html

The JSON is the machine-readable source of the displayed report; Markdown is
the compact text view.

## Verification evidence

Targeted regressions and integration tests:

    python -m pytest -q tests/test_core.py tests/test_g08_pipeline.py tests/test_g04_profiles.py tests/test_g09_g10_integration.py

Result: **47 passed** (including persistent synthetic regressions for field/value
evidence support, silicon compound separation and positive control, canonical
coordinates, generic policy scope/count forms, evaluator-field exclusion,
event/policy conflict, and SQLite revision gaps).

Additional check:

    python -m compileall -q src/patent_to_pilot

Result: **PASS**.

The tests use temporary paths/SQLite and synthetic boundary payloads where
needed. They do not download data, rehash the raw corpus, call a model, call
an API, use GPU/RunPod, or read evaluator-only material.

## Targeted acceptance matrix

| Acceptance | Test/evidence | Outcome |
|---|---|---|
| Cost support binds the value directly to the cost phrase; 100 passes and unrelated 999 fails | `test_cost_phrase_binds_value_not_unrelated_number` with `The total batch cost was 100 USD; 999 tablets were produced.` and `For batch 999, the total batch cost was 100 USD.` | PASS |
| Ambiguous multiple cost-linked values are unsupported rather than guessed | `test_ambiguous_cost_phrase_is_not_supported` | PASS |
| Elemental silicon is separated from carbide/nitride/oxide | `test_elemental_silicon_rule_rejects_compounds`; `test_elemental_silicon_positive_control` | PASS |
| Locator and top-level offsets have one canonical span; malformed locator is invalid | `test_locator_is_invalid_when_canonical_span_does_not_cover_text`; `_integrity` reasons | PASS |
| Generic policy is component-scoped and unsupported count forms are explicit | `test_generic_policy_scope_and_unsupported_count_are_explicit_unknown` | PASS |
| Event policy mismatch is rejected; no silent policy rewrite | `test_generic_event_policy_rule_mismatch_is_rejected`; existing case conflict test | PASS |
| Revision references actual stored version through event gap | `test_generic_revision_gap_uses_stored_sqlite_versions`; report history `[1, 2]` | PASS |
| Generic evaluator-field exclusion preserves allowed context | `test_generic_profile_excludes_evaluator_fields_but_preserves_allowed_context` | PASS |
| Invalid evidence does not crash workflow and affects only related route | `test_invalid_evidence_and_prohibited_option_complete_generic_workflow`; `regression-matrix.json` | PASS |
| Full bounded case runner metrics are computed from actual evaluator output | `results/development/g09-g10/integration.json` | PASS: 3 cases, 15 states, zero failures |
| New caller-supplied input is processed without case-ID lookup | `results/development/g09-g10-new-input/workflow.json` | PASS: 2 states, 1 change, SQLite read-back |

## API smoke plan — not executed

configs/g09-g10-api-smoke.toml proposes a later, separately authorized
smoke test: 3 cases × 1 call, at most one bounded retry per case, an
approximate ceiling of 16,500 tokens and USD 5.00. The provider and model
version must be checked for current availability at run time. Measure usage,
retry cost, elapsed time, source integrity, traceability, required changes,
preservation, and unknown handling against the same public packets and
deterministic baseline. Stop on missing auth/model, budget exceedance, or
input-boundary failure. No key is stored here and no call was made.

## Status and limitations

- **G09:** bounded development integration slice is implemented and runnable; not full G09. It does not provide a semantic generator, live retrieval expansion, document templates for every downstream role, or scientific/clinical/regulatory/legal validation.
- **G10:** bounded offline runner and deterministic path are implemented; not full G10. B0–B4 comparison matrix, fair multi-method execution, cost ledger for provider runs, and benchmark claims remain pending.
- **G05/G06:** consumed as development interfaces only; neither is being declared fully complete here. The three cases are development units, not a final sample or frozen held-out split.
- The deterministic path is real and runs offline. The provider/model adapter remains mock/disabled; no model extraction or paid API result exists.
- ready_for_review means artifact and traceability checks passed. It does not mean reviewer approval, feasibility, efficacy, safety, regulatory approval, patentability, FTO, or production readiness.
- Static reports are derived outputs from public development packets. They are not an independent scientific result and should not be used as a main experiment.
- Span validation is limited to the coordinate metadata exposed in each public packet. It checks the declared Unicode/end-exclusive or G08-trimmed contract and payload lengths; it does not reopen or rehash the raw corpus.
- Latest actual runner report was regenerated from the current code: 3 cases, 15 states, elapsed 0.044782 seconds, with all evaluator metrics PASS and zero reported failures.
- The external repro/evidence supplied for this audit was not readable in this runtime, so its exact original assertion IDs cannot be independently quoted here.
- docs/research/PILOT_READINESS.md is a readiness proposal, not a pilot result. It does not set a winning method, final sample, split, provider, model, or paid budget.
- The generic workflow path is intentionally limited: it accepts explicit caller-supplied evidence/options/policy and deterministic route checks, but does not claim semantic entailment or implement G11/G12 behavior.

## Full G09/G10 still remaining

- Full G09: broader development-case coverage, semantic/provider-backed
  generation, live retrieval expansion where authorized, downstream role
  handoff templates, and validation beyond this deterministic packet slice.
- Full G10: freeze the fair B0--B4/proposed comparison matrix, prepare the
  required dev/validation/test data and family/organization grouping, run the
  same-information multi-method evaluation, and record provider calls, tokens,
  retries, latency, cost, failures, and repair attempts.
- Still open for both: scientific utility, clinical/regulatory/legal validity,
  patentability/FTO, generalization, AI superiority, and main/held-out
  benchmark claims. These require separately authorized data, protocol and
  budget decisions.

## Review and publication boundary

The accepted scoped commit contains implementation, tests, synthetic fixtures,
configs/scripts, and research/handoff documentation only. Generated reports
remain local derived evidence for this handoff and are not included in the
scoped commit. No raw/processed dataset, evaluator-only payload, secret,
credential, or prohibited PDF is part of the commit. Do not push or start a
paid API/model run from this acceptance record.

## Next action for review

The targeted acceptance has been confirmed by Pepo. The next action is a
scoped commit review of the exact staged file list and commit SHA; after that,
the owner may separately decide whether to push. Do not extend to G11 or G12
or authorize an API/GPU run from this handoff.
