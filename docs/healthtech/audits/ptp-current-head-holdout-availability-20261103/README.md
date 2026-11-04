# Current-head holdout availability audit

Date: 2026-11-03 (Asia/Bangkok)

This audit records whether the current candidate has an authorized final
holdout for the frozen G1/G2 protocol. It is a protocol-availability check;
it does not rerun retrieval, download a dataset, or create evaluation labels.

## Candidate and protocol

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Protocol: `configs/healthtech/g1_g2_public_cohort_protocol.json`
- Protocol SHA-256: `582e7d9a551f2e4afefa6cec7be26f6c98f2af9fe32ffb4b16bab726b1f32508`

## Finding

The current public protocol is `FROZEN_DEVELOPMENT_ONLY`. It defines three
predeclared Abbott cardiovascular products, one applicant/source, and explicitly
states that all three queries are development-only with no final holdout or
generalization claim. Therefore a current-head final-holdout endpoint is not
available or authorized in this worktree.

The historical Stryker packages remain separate diagnostics. They are not
substituted for a current-head final holdout, and their results are not pooled
with the Abbott development results. No new holdout claims are made here.

## Consequence

- G1/G2 scientific status remains `PARTIAL_DEVELOPMENT_ONLY`.
- Current-head metrics remain descriptive development evidence.
- No final generalization, powered adaptive-superiority, or independent-group
  uncertainty claim is supported by this package.
- Local engineering, API preflight, rights checks, manuscript work, and other
  independent branches may continue.

## Resource and privacy boundary

No provider call, GPU job, dataset download, ledger mutation, budget reset,
time-window reset, label acquisition, or private-payload copy occurred. The
audit contains no credential, raw restricted source, or evaluator-only label.

See `verification.json`, `CHECKPOINT.json`, and `NEXT_ACTIONS.md` for the
machine-readable receipt and resumable next step.
