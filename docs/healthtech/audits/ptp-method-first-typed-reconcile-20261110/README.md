# Typed profile output reconciliation

Checkpoint 2026-11-10 09:35:41 Bangkok; base 30adb67bdbea1a6e281fdf9bc4f94bf2b822aab0. No experiment or model attempt.

A versioned private profile-stage output now retains its allowed source, canonical
profile, compiled components, compact view and derived decision. The controller and
reconciler share profile_result, so reconciliation recomputes structural/source checks
and compares the entire record instead of trusting a decision string.

DevStageJournal reads output only after checking its sealed byte hash, checks source
against the execution declaration when bound, and passes typed profile outputs into
reconciliation. Completed transport can support PROFILE_FAILED only when its typed
output recomputes to failed extraction. Empty, failed, review and prepared decisions
cannot be silently interchanged. Typed stopped profiles cannot reconcile executed
embedding/acquisition/selection stages. Legacy exception-based failures remain supported.

Six new cases: completed transport plus failed/empty/review profile; false empty relabel;
retrieval despite review; modified sealed output. Full19 SACR files + MTM bound runner:
253 PASS. Ruff on five changed Python files PASS. Synthetic anchor family IDs are authored;
no real baseline ranking was read or verified.

This is record consistency, not enforcement of scheduling before execution. The generic
journal can still execute arbitrary callbacks; typed controller integration must prevent
those calls prospectively. Anchor fallback attestation, actual preflight and resource
controls remain incomplete. Legacy untyped records retain their old weaker contract;
they are not a production approval path. Raw source/profile outputs remain PRIVATE and
must never enter public Git. Only authored fixtures and aggregate audit are committed.

Next implement prospective typed scheduling/view acceptance, ensuring no work follows a
stopped profile, then bind retrieval/anchor evidence and live budgets. R1 curator/isolation,
A03/parity, generation compatibility and fidelity gates remain open. R5 not authorized.
