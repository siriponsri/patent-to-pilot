# Repair generation-evidence replay at cohort finalization

During inspection for profile-generation integration, actual controller code
showed that embedding replay supported v3 generated-view evidence but
`finalize_mixed` still reconstructed only the legacy v2 result. It consequently
rejected valid v3 output as changed evidence. Profile work was deferred to repair
this concrete integration gap first. Previous turn was verified progress.

Reproduction: five newly authored integration cases failed before the fix. Ready
plus missing query, generic review, selective review and retrieval failure all
stopped with `view terminal evidence changed`. The fifth cost-mutation case also
stopped at that wrong earlier check rather than reaching sealed-event verification.
These were fixture failures, not new model or research attempts.

Repair: one `_replay_view` helper now serves embedding and finalization. It retains
the existing v2 path and validates v3 original artifact, generation identity,
sealed costs and exact screening result. Review remains a stop; the refactor does
not relax evidence, authorize family rejection or convert failed generation into
successful views. No old artifacts were rewritten.

Validation after repair: all five reproductions pass; 36 focused controller,
embedding and mixed-finalization cases pass. Full related suite: 396 tests pass.
Ruff passes both changed Python files. The authored ready/missing cohort retains
both queries and totals two generated-view calls, six input and four output tokens.
The failed embedding case retains unknown aggregate costs with the observed two
model calls as a lower bound. Both review arms stop scoring. Event-byte mutation
blocks completion. The ready fixture uses a fake encoder and a tiny authored CPU
index, not real generation, R1 parity, or retrieval effectiveness evidence.

A requested inspection path `tests/test_sacr_selection_finalization.py` did not
exist; the relevant existing mixed-finalization and retrieval fixtures were read.
No actual data/model/GPU/remote job was accessed. No automatic retries.

Next: profile-generation evidence binding and a prospective execution version that
requires it, then declared family-rejection/accounting integration. Actual R1
isolation/A03/baseline/native parity NOT_RUN; curator/environment unanswered.
Generation/fidelity/resources remain open, R3/R4 absent, R5 not authorized, R6
incomplete. This repair does not complete the research Goal.
