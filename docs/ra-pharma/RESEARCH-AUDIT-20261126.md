# Planner decision on the first RA Pharma research handback

**Accept R1 input audit, R2 protocol, R3 synthetic mechanism check and R5 feasibility handback. The eight IS1 benchmark cells and R4 natural transfer remain NOT_RUN.** No method promotion or reserved-scoring release. This review concerns [the Research branch at d956473c](https://github.com/siriponsri/patent-to-pilot/tree/d956473c2c05d111ac18ff95ed3c414e460c6ec9/docs/ra-pharma/research). Integration into main is a separate decision.

## Evidence checked

- Verified the live research ref, clean research checkout and two-commit diff from the common planning base. All 22 changed paths fall within the lane. The prospective commit `b5584589` contains the same eight input digests as the final freeze; all eight final Git blobs match. The two implementation files were published in the final commit, with their hashes already in the earlier freeze. Freeze SHA-256 `5aacb45c351c85ff292fce141da99b0dbea4ee6ff01470ea07baa490f93b867f`. Seal SHA-256 `1435a7dc3c374de697151e70ac36be0beeeb9605363eeaf1f48a2e85b62f34d2`.
- Ran the read-only sealed replay and the focused regression test (1 passed). Independently reconstructed issued, supported and unsupported case IDs from the raw traces and authored evidence key. All four template echoes account for the net gain from 2 to 6 correct issuances across 11 cases. On the seven additional cases the learned reader gained D09 and lost D07, ending at 2/7 alongside the fixed reader. Switching off only the evidence-role gate added one unsupported issuance. Switching off all scope checks added four. Seven cases had permitted support; four had known missing support. The reported counts of correct issuances should not be read as overall accuracy including correct abstention.
- Both stored full-suite log hashes match. The final raw exit was 1, with 2,793 passed, eight standing SACR failures, ten skips and one expected failure. The first attempt had three additional BM25 dependency failures. The Planner checked the saved full logs and reran only the focused test. Direct fixture API/GPU spend was zero; executor and reviewer harness costs were unmeasured.

## Finding for the next scorer

The current harmful-stop calculation marks a topic stop as harmful if any permitted source remains unread under the cap. In a separate in-memory probe with two equally valid witnesses, a correct issuance supported by the first witness was also labeled a harmful stop. None of the original correct issuances had this flag, so the published eleven-case counts stand. For the next study, require an incorrect or missed required outcome and a reachable admissible alternative; include a regression case with two valid witnesses. Keep the original unchanged.

## Next dispatch

The owner authorized directing the Research Executor. The existing research session received the next assignment: establish a rights-cleared source, candidate-family counts, independent known OUT links, family/overlap exclusions and a label-blind runnable plan for a fresh IS1-compatible reference. If a candidate lacks an essential field, document the specific evidence and alternative. R4 independently needs a keyed natural dossier packet. The next review point is a published input package and exact pre-run lock or a source-specific feasibility stop. No permission for a reserved score, paid call or GPU rental was issued.
