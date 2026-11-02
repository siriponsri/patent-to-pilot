# G09/G10 development integration report

This is deterministic offline development evidence, not a model benchmark.

- Cases: 3
- States: 15
- Elapsed seconds: 0.035507
- Source integrity: PASS
- Required changes: PASS
- Preservation: PASS
- Unknown handling: PASS
- Route-local status: PASS
- SQLite route payload/status read-back: PASS
- Independent evaluator: PASS
- Failures: 0

## State summary

### PTP-0001
- S0: A=passes_this_explicit_check, B=passes_this_explicit_check; handoff=ready_for_review; evidence=7
- S1: A=fails_this_explicit_check, B=passes_this_explicit_check; handoff=ready_for_review; evidence=7
- S2: A=fails_this_explicit_check, B=passes_this_explicit_check; handoff=ready_for_review; evidence=7
- S3: A=fails_this_explicit_check, B=unknown; handoff=ready_for_review; evidence=6
- S4: A=fails_this_explicit_check, B=unknown; handoff=ready_for_review; evidence=6
- S1 revision forbid_silicon_substrate: affected=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- S2 revision project_name_only: affected=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
- S3 revision support_withdrawal: affected=allowed_evidence, options, proposed_next_tests, routes, source_facts, source_integrity; preserved=agent_input_fields, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, unknowns
- S4 revision request_yield_without_new_evidence: affected=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
### PTP-0002
- S0: A=passes_this_explicit_check, B=passes_this_explicit_check; handoff=ready_for_review; evidence=4
- S1: A=fails_this_explicit_check, B=passes_this_explicit_check; handoff=ready_for_review; evidence=4
- S2: A=fails_this_explicit_check, B=passes_this_explicit_check; handoff=ready_for_review; evidence=4
- S3: A=fails_this_explicit_check, B=unknown; handoff=ready_for_review; evidence=3
- S4: A=fails_this_explicit_check, B=unknown; handoff=ready_for_review; evidence=3
- S1 revision forbid_material_at_role: affected=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- S2 revision project_name_only: affected=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
- S3 revision sole_support_withdrawal: affected=allowed_evidence, options, proposed_next_tests, routes, source_facts, source_integrity; preserved=agent_input_fields, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, unknowns
- S4 revision request_yield_without_new_evidence: affected=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
### PTP-0003
- S0: R=passes_this_explicit_check; handoff=ready_for_review; evidence=2
- S1: R=fails_this_explicit_check; handoff=ready_for_review; evidence=2
- S2: R=fails_this_explicit_check; handoff=ready_for_review; evidence=2
- S3: R=unknown; handoff=ready_for_review; evidence=2
- S4: R=unknown; handoff=ready_for_review; evidence=0
- S1 revision tighten_bound: affected=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- S2 revision project_name_only: affected=none; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, proposed_next_tests, routes, source_facts, source_integrity, unknowns
- S3 revision count_definition_change: affected=fictional_stipulations, options, routes; preserved=agent_input_fields, allowed_evidence, brief, case_id, contradictions, handoff, interface_status, interpretations, mock_provider_called, profile_id, profile_version, proposed_next_tests, source_facts, source_integrity, unknowns
- S4 revision support_withdrawal: affected=allowed_evidence, proposed_next_tests, source_facts, source_integrity; preserved=agent_input_fields, brief, case_id, contradictions, fictional_stipulations, handoff, interface_status, interpretations, mock_provider_called, options, profile_id, profile_version, routes, unknowns
