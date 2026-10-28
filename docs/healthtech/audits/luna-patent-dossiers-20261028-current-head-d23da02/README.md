# Current-head revalidation: atomic history and real patent-linked dossiers

Run id: `luna-patent-dossiers-20261028-current-head-d23da02`

Checked on October 28, 2026 against local and `origin/main` commit
`d23da02ece90b6e776e7fa0e23e64b7b974dd8d8`. This run supersedes the older
atomic receipt for current-head evidence only; historical receipts remain
immutable.

## Acceptance matrix

| Package | Result | Evidence |
|---|---|---|
| A: atomic committed-version publication | PASS | Fresh portable reproduction saw only committed version `[1]` while version 2 was staged, then `[1, 2]` after publication; current focused tests cover concurrency, stale parents, interruption, recovery, and export. |
| B: real patent-linked dossier backend | PASS for local development backend | Fresh rebuild from the frozen Abbott cohort produced three real cases with 41 patent inputs each, source-backed disclosure annotations, source-view output, versioned edits, history, and selected-version CLI exports. |
| C: development cohort/frontier | PASS for development-only use | Existing frozen cohort/frontier artifacts match the current unchanged runner/config hashes: 3 devices, 41 patents, 61 disclosed pairs, 62 unjudged distractors, five methods, zero provider calls, zero paid cost, and `NOT_ESTIMABLE` uncertainty. |
| Scientific generalization, final holdout, UI, release | NOT_RUN | Bridge rights/cohort/split remain blocked; no independent relevance judgments or final holdout; Claude UI remains paused; restricted patent/disclosure text remains local-only. |

## Package A

The current implementation uses same-directory staging, payload fsync, atomic
hard-link creation, and directory fsync where supported. The fresh reproduction
is recorded in `history-current.json`. During the writer pause, the committed
reader saw version 1 only and no published version-2 bytes. After release, the
chain loaded as versions 1 and 2. The focused regression suite also exercises
same-base concurrency, stale expected parents, interruptions before and after
publication, staging cleanup/recovery, and selected-version export.

## Package B

The fresh case root is the ignored local path
`results/healthtech/ht-abbott-dossiers-20261028-current-d23da02/`:

- `HT-DEV-MITRACLIP`: 35 candidates, 14 retrieved candidates, 21 disclosed links.
- `HT-DEV-TENDYNE`: 20 candidates, 3 retrieved candidates, 17 disclosed links.
- `HT-DEV-TRICLIP`: 28 candidates, 5 retrieved candidates, 23 disclosed links.

Each case contains 41 real patent inputs, a typed source manifest, JSON/Markdown
dossier outputs, source-view output, history versions 1 and 2, and a version-2
export preserving the authored `review-note`. The CLI source viewer returned the
PMA `trade_name` field with the `openfda-pma-records` rights policy for all three
cases. Restricted Abbott disclosure and Google-derived patent sources remain
`BLOCKED_LOCAL` for product display and redistribution.

The adapter reads the frozen runtime cohort and source registry. Evaluator
references remain outside product construction; product-level disclosed links
retain their disclosure evidence and are not promoted to claim-level relevance.

## Package C

The revalidated development protocol keeps the three Abbott devices in
development, preserves 62 unjudged distractor pairs, uses two exact-patent
components, keeps family mapping `UNKNOWN_NOT_ASSUMED`, and has no final holdout.
The current frontier is descriptive development evidence only: HT-B0a, HT-B0b,
HT-B1, HT-B2, and HT-B3 ran with zero provider calls and zero paid cost. No
generalization or adaptive-superiority claim is made.

## Verification

See [`verification.json`](verification.json) for exact commands, counts,
hashes, source boundaries, and remaining not-run items. The canonical source
rights and per-link provenance evidence remain in the prior rights-aware audit:
`docs/healthtech/audits/luna-patent-dossiers-20261028-rights-cohort/`.
