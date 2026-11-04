# Manuscript E2 provenance rebind — 2026-11-03

Status: `PASS_CURRENT_HEAD_MANUSCRIPT_E2_REBOUND_OWNER_REVIEW_PENDING`.

This checkpoint repairs stale acceptance metadata for the manuscript currently
present in the dirty candidate worktree. It is a provenance-only change. It
does not rerun experiments, alter scientific claims, or reopen any paid or GPU
gate.

## Bound artifact

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Manuscript: `docs/healthtech/research/MANUSCRIPT_ADAPTIVE_EVIDENCE_ACQUISITION_EN.md`
- SHA-256: `0c3ed5f1ff80c44f704cb4cc6f93e03c9675fec2cfb1063ab5c34be81faf2cc0`
- Bytes: `50708`
- Relative links checked: `46`
- Missing relative links: `0`

The prior `50,363`-byte / `45`-link record remains historical in its original
audit. It is not silently overwritten.

## Claim and resource boundaries

- Current-head and historical metrics remain separated; no metric was changed.
- The manuscript does not claim adaptive superiority, semantic device-patent
  gold, exhaustive recall, confirmatory significance, or journal acceptance.
- The local Qwen result remains schema-valid local evidence only. No paid API
  request, reservation, retry, or pending call was issued.
- The E2 journal remains the canonical local journal. Four legacy settled calls
  totaling `USD0.0001464` and `UNKNOWN_OWNER_ACCEPTED_CUTOVER` are preserved;
  the prospective allowance remains `USD1`.
- Current scoped credit/limit evidence is still unavailable, so paid dispatch
  remains blocked before reservation.
- No GPU job, dataset download, ledger mutation, budget reset, or window reset
  occurred in this rebind.

## Verification basis

- Current handoff: `docs/healthtech/audits/pepo-blocked-goal-repair-20261103/README.md`
- Paid-gate checkpoint: `docs/healthtech/audits/ptp-api-current-credit-recheck-20261103/verification.json`
- Existing manuscript integrity receipt: `docs/healthtech/audits/ptp-manuscript-integrity-current-head-r3-20261103/verification.json`
- Relative-link check: `checked=46 missing=0`
- Focused regression receipt: `focused-tests.xml` (`45 passed, 0 failed, 0 errors, 0 skipped`)
- Scoped whitespace check: `PASS`; repository diff check still reports pre-existing
  CRLF conversion noise in the dirty `memory/next-actions.md` file.

The manuscript remains `DRAFT_FOR_OWNER_REVIEW`. Owner review, release
metadata confirmation, and the official WPI Guide check remain required before
merge or submission.
