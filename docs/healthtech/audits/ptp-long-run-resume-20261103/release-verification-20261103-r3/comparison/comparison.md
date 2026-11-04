# G10 bounded offline comparison

Mechanics-only development evidence from the public PTP-0001 packet; not a scientific benchmark.

- Status: **PASS**
- Case: `PTP-0001`
- States: `S0, S1, S2`
- Network calls declared: `0`
- Network observation: `NOT_MEASURED`
- Mock provider cost: USD 0.0000000

## Method status

| Method | Status | Provider calls | Failed attempts | Failed states | Validation failures | Cost |
|---|---|---:|---:|---:|---:|---:|
| B0_rules_only | PASS | 0 | 0 | 0 | 0 | USD 0.0000000 |
| B1_full_regeneration | PASS | 3 | 0 | 0 | 0 | USD 0.0000000 |
| B2_direct_revision | PASS | 3 | 0 | 0 | 0 | USD 0.0000000 |
| B3_invalidation_same_generator | PASS | 3 | 0 | 0 | 0 | USD 0.0000000 |
| P_existing_workflow | PASS | 0 | 0 | 0 | 0 | USD 0.0000000 |

## Before/after checks

### B0_rules_only
- `S0` `PASS` (execution=PASS, validation=PASS); changed=initial state; preserved=n/a
- `S1` `PASS` (execution=PASS, validation=PASS); changed=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- `S2` `PASS` (execution=PASS, validation=PASS); changed=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
### B1_full_regeneration
- `S0` `PASS` (execution=PASS, validation=PASS); changed=initial state; preserved=n/a
- `S1` `PASS` (execution=PASS, validation=PASS); changed=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- `S2` `PASS` (execution=PASS, validation=PASS); changed=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
### B2_direct_revision
- `S0` `PASS` (execution=PASS, validation=PASS); changed=initial state; preserved=n/a
- `S1` `PASS` (execution=PASS, validation=PASS); changed=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- `S2` `PASS` (execution=PASS, validation=PASS); changed=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
### B3_invalidation_same_generator
- `S0` `PASS` (execution=PASS, validation=PASS); changed=initial state; preserved=n/a
- `S1` `PASS` (execution=PASS, validation=PASS); changed=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- `S2` `PASS` (execution=PASS, validation=PASS); changed=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
### P_existing_workflow
- `S0` `PASS` (execution=PASS, validation=PASS); changed=initial state; preserved=n/a
- `S1` `PASS` (execution=PASS, validation=PASS); changed=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- `S2` `PASS` (execution=PASS, validation=PASS); changed=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns

## B4-RG boundary

B4-RG and B4-DR are `NOT_IMPLEMENTED`/`NOT_RUN`; the current public case does not contain a verified adaptive-search distractor/recovery pool.

## Limits

- No provider network, paid compute, model-quality, scientific-utility, clinical, legal, patentability, or FTO claim.
- The existing workflow wrapper is bounded public-input integration, not full G10 dependency-guided repair.
