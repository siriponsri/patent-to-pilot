# Query outcomes and actual-operation cost accounting
research/sacr_outcomes.py implements prospective outcome/reconciliation utilities.
It does not execute the pipeline, score relevance, or authorize a run.
MISSING_INPUT keeps empty rankings in the expected cohort. PROFILE_FAILED and
PROFILE_EMPTY copy the supplied verified anchor into all four profile-dependent
factorial arms, recording fallback. The separate plain generic multi-query baseline
is not one of these arms. REVIEW_REQUIRED and RETRIEVAL_FAILED retain no rankings
and make the complete cohort unscorable. They cannot silently become empty output
or an anchor fallback. READY requires exactly four bounded, duplicate-free rankings.
All query states remain visible; semantic_status unknown. 'scorable' means only
structural outcome completeness, not passed integrity/fidelity gates or permission.

Cohort reconciliation rejects missing/duplicate/foreign queries and inconsistent
fallback/flag records. It never repairs original attempts, filters queries, retries
or performs human per-view selection. Caller must bind supplied anchor/rankings to
their actual immutable run receipts; this module alone does not prove that binding.

Cost events require explicit metrics for calls/tokens, embeddings, full-index and
candidate dot products, operation wall/GPU seconds and peak memory. Unknown values
remain null with labelled observed lower bounds. Failed/interrupted events count.
Duplicate event IDs, negative/nonfinite/bool costs and omitted fields are rejected.
Peak memory uses max, not sum. Empty ledger is unknown, not zero-cost evidence.
Operation wall sum is not end-to-end elapsed time. Shared actual work is recorded
once; standalone arm costs and end-to-end elapsed time are NOT_DERIVED/unknown.
These functions cannot detect an event omitted from an external attempt journal:
receipt completeness explicitly requires external reconciliation.

36 targeted tests pass:15 outcomes,8 generation,13 components. Tests cover failed/
missing-query denominators, stop states, missing/foreign/duplicate outcomes, fallback
consistency, unknown interrupted costs, peak aggregation, invalid/incomplete events
and an empty ledger. Ruff passed for two new files. No actual query/model/data/GPU
run. This is not a complete runtime controller or a complete measured cost report.

Next reconcile reserved attempts and events under an immutable run manifest; audit
the complete R0–R6 requirements against current artifacts to expose remaining gates.
Actual R1 curator/isolation/A03/parity, viable generation, fidelity observations,
real encoder/index integration, resource evidence, R3/R4 and R5 freeze remain open.
Do not turn these utility tests into end-to-end or research-success claims.
