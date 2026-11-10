# Separate selection from repeated acquisition

2026-11-10 09:47:28 Bangkok; base a09f640897b074089ff2eb39795b2710b43547d8. Authored arrays only.

Integration inspection found compare_factorial always performed full acquisition before
selection, which would repeat search if invoked after a separately journaled acquisition.
It now accepts optional acquired records. The original path is unchanged; the reuse path
checks both arms, view identities, sorted unique eligible union, per-view depth/exposure,
anchor-score shape/range, union agreement, index/view vector geometry and passage order.
It performs component coverage/selection without calling acquire_union. Selection reports
zero actual acquisition dot products plus acquisition_reused=true; original acquisition
records retain their own work counts. No costs are erased from a run-level ledger.

Eleven new tests.23 SACR files + MTM bound runner:290 PASS; Ruff PASS. A forbidden search
callback proves no repeat acquisition; rankings and passage evidence equal the original
combined path, with six component dot products in the fixture. Invalid exposure, mask,
union, depths and vectors are rejected. This is CPU synthetic equivalence, not GPU parity.

Supplied acquisition scores are not independently authenticated by these structure checks.
Caller must verify the original sealed acquisition and bind source/index/mask/vector identity.
Full corpus/index binding into the controller is still pending, as are mapped-vector
acquisition/selection dispatch, typed finalization, real anchor provenance and resource
controls. No real index was scanned. Next wire those stage boundaries with existing
source-bound embedding output; do not claim this preparatory split is end-to-end SACR.
R1 actual isolation/A03/parity, generation/fidelity gates and R5 authority remain unchanged.
