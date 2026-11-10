# Final outcome binding to sealed selection

2026-11-10 09:53:59 Bangkok; base a501b96cbc9169a3381a12bfbd95ffa02493156d. Authored six-stage fixtures only.

selection_outcome derives four arm rankings from typed selection, with canonical outcome
validation. Journal finalization passes byte-verified typed selection to reconciliation;
caller-supplied outcomes must match exactly, including order and state. Generic untyped
legacy records retain their old compatibility path and are not production approval.

Controller finalize_ready requires exactly the declared cohort's masks, replays profile/
views/embedding inputs, checks index/mask/embedding/depth bindings and acquisition hash,
checks selection's acquisition/order references and candidate exposure, derives outcomes,
and finalizes the journal. It never accepts arbitrary rankings, reruns retrieval, or silently
drops an incomplete query. READY is an engineering state, not semantic/scientific readiness.

Eight new cases.25 SACR files + MTM bound runner:305 PASS (local session27000 terminal exit0).
Ruff on five changed Python files PASS. Tests cover canonical finalization without rerun,
reversed/dropped/added rankings, changed state, missing/foreign masks, incomplete attempts
and changed sealed selection. No actual model, corpus or protected evaluation.

This is currently all-ready cohort finalization only. Mixed missing/failure/review/fallback
cohorts need bound terminal evidence and original-anchor attestations; they are refused
here, not omitted. Finalization trusts verified program-generated score records and does
not independently recompute retrieval arithmetic. It does not provide adversarial storage
security, fidelity approval or external data provenance. Full-scale resource acceptance,
actual R1 curator/isolation/A03/parity, generation compatibility remain open.
Next integrate mixed outcomes/anchor receipts and address full-index memory/live budgets
before any real execution. R3/R4 absent; R5 not authorized; R6 incomplete.
