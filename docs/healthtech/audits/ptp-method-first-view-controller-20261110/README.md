# Prospective profile-to-view scheduling

2026-11-10 09:38:23 Bangkok; base 9c2b3e66ad73206344c4ab067e17a4a6a47137a5. Injected authored adapters only.

Journal read_completed_output checks plan bindings, reservation/receipt identity,
completed terminal status and output byte seal before returning a detached dependency.
Unsealed state is not inferred to be stopped. BoundProfileController.views recomputes
the canonical profile against its bound source and requires structurally prepared status
before reserving either matched factorial view stage. Failed/empty/review/missing or
changed dependencies cannot dispatch the adapter. Generic receives only ID/source;
selective additionally receives a detached profile. This concerns the matched factorial
arms; the independent generic baseline is not replaced by this dependency rule.

Responses use existing strict parsing, per-response byte cap, common protected explicit
conditions and lexical screening. Selective adds the deterministic compact proposal.
Anchor/duplicate records remain; rejected views are excluded, review stays review, and
accepted view count cannot exceed declaration. No lexical pass grants semantic fidelity.
Malformed response is a failed reserved stage, no retry. Adapter-owned raw private
attempts remain required; no generation bytes are placed in public audit.

Ten new tests;20 SACR files + MTM bound runner:263 PASS. Ruff on three changed Python
files PASS. Tests prove adapter non-dispatch before reservation on invalid dependencies,
generic interface separation, detached selective profile, duplicate anchor, review and
malformed response handling. No actual data/model/GPU work.

Still missing: typed view-output reconciliation and downstream embedding/retrieval
scheduling, failed-view family handling, original-anchor attestation and live resource
limits. The general journal remains a low-level API and does not prohibit callers bypassing
the controller. Actual artifacts, R1 curator/isolation/A03/parity, generation compatibility
and fidelity gates remain. No R3/R4 run or R5 authorization.
