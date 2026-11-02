# Bounded offline workflow prototype

This is a caller-supplied development workflow, not a held-out benchmark.

- States: 2
- Changes: 1
- Source integrity: PASS
- SQLite read-back: PASS
- Elapsed seconds: 0.001576
- Paid API/model/GPU: NOT_RUN

## NEW-PROJECT-ALPHA state 0
Brief: Compare two fictional coating routes and identify what must be measured before a formulation handoff.
Routes:
- NEW-PROJECT-ALPHA:NEW-A: candidate / passes_this_explicit_check; evidence=NEW-E1; unknowns=coating uniformity,pilot yield
- NEW-PROJECT-ALPHA:NEW-B: candidate / passes_this_explicit_check; evidence=NEW-E2; unknowns=coating uniformity,pilot yield
Handoff: ready_for_review (review=not_reviewed)
## NEW-PROJECT-ALPHA state 1
Brief: Compare two fictional coating routes and identify what must be measured before a formulation handoff.
Routes:
- NEW-PROJECT-ALPHA:NEW-A: draft / fails_this_explicit_check; evidence=NEW-E1; unknowns=coating uniformity,pilot yield
- NEW-PROJECT-ALPHA:NEW-B: candidate / passes_this_explicit_check; evidence=NEW-E2; unknowns=coating uniformity,pilot yield
Handoff: ready_for_review (review=not_reviewed)

## Before/after changes
- 1: policy_change; affected=fictional_stipulations,options,routes; preserved=agent_input_fields,allowed_evidence,brief,case_id,contradictions,handoff,interface_status,interpretations,mock_provider_called,profile_id,profile_version,proposed_next_tests,source_facts,source_integrity,unknowns; read_back=True
