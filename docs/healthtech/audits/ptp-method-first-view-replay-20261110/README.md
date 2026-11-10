# Replayable view results and embedding-input gate

2026-11-10 09:41:13 Bangkok; base 95efd9d2ce550d633038efd818600fac6bb66542. No real model, query or embedding run.

View-stage v2 retains private UTF-8 response, canonical profile-output digest, screening
records, and retained-generated-view count/degeneracy flag. view_result replays the same
strict parsing/protected-condition screening and compact proposal under declared caps.
Existing v1 artifacts are not rewritten; embedding preparation requires replayable v2.

Controller embedding_inputs reads sealed profile and both view outputs, recomputes them
against its bound source/caps, and refuses mismatched, unsealed, failed or review-required
records. It returns detached component plans, immutable ordered view tuples and output
hashes. Rejected/duplicate proposals remain in private evidence; excluded views do not
enter embedding inputs. No-generated-view-retained is explicit even when compact remains.
The declared rejected-view policy permits retained anchor; that is not a successful
abstraction claim or permission to substitute anchor-only as the research method.

Seven new tests;21 SACR files plus MTM bound runner:270 PASS; changed Python Ruff PASS.
Tests cover honest degeneracy, detached outputs, absent/failed/review/mutated views,
forged screening decision even in a sealed output, and rejected-proposal evidence.

This prepares inputs only; no embedding adapter is dispatched or attested. Typed view
reconciliation at finalization, failed-generation family policy, actual vector/index/anchor
bindings, live resource control, R1 isolation/A03/parity, generation compatibility and
fidelity still remain. No semantic certificate, experiment success or R5 authorization.
Raw responses/source are PRIVATE and must not be committed; only authored fixtures here.
Next bind prepared text rows to actual embedding outputs within the reserved stage, then
connect acquisition/selection and finalization without bypassing these gates.
