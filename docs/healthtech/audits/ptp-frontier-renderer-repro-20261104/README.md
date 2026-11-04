# Current-head frontier renderer reproducibility repair

Recorded: 4 November 2026 (Asia/Bangkok)

This focused repair makes the current-head frontier renderer independent of
the caller's absolute verification-file path. The renderer now stores a
stable repository-relative path for repository inputs and a sanitized
`<external>/filename` label for inputs outside the repository.

## Verification

- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Regression: `2 passed, 0 failed`
- Python compile check: PASS
- Renderer replay: CSV, both SVG figures, and manifest matched the existing
  repository artifacts byte-for-byte (`4/4` SHA-256 matches).
- Existing evaluation values, protocol, cohort, and candidate revision were
  not changed.

The earlier mismatch was limited to `manifest.json`: absolute input paths
made an otherwise identical render depend on the machine and invocation
form. No provider call, GPU job, dataset download, reservation, ledger
mutation, budget reset, or time-window reset occurred.

## Boundary

The figures remain development-only descriptive artifacts. This repair does
not create a final holdout, semantic relevance gold, paid API result, or
adaptive-superiority claim.
