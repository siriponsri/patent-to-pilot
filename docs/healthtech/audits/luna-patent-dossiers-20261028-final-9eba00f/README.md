# Luna patent-linked dossier goal: current-head closeout

Run ID: `luna-patent-dossiers-20261028-final-9eba00f`

Checked: 2026-10-28 (Asia/Bangkok)

Candidate commit: `9eba00f89c7c8430c19465de5b49aadffa0a2887`

Remote: `origin/main` resolves to the same commit.

Tree state: `DIRTY_PRESERVED_UNRELATED_OWNER_ARTIFACTS`; only scoped files were
staged for the two implementation commits. The pre-existing `AGENTS.md` edit and
untracked owner artifacts remain untouched.

## Acceptance matrix

| Package | Result | Current evidence |
|---|---|---|
| A. Atomic committed-version publication | `PASS` | Fresh reader-pause reproduction plus interruption, stale-parent, same-base concurrency, staging-recovery, and export regressions. No version-2 bytes were visible during staging; final chain was `[1, 2]`. |
| B. Real patent-linked dossier backend | `PASS_LOCAL_DEVELOPMENT_BACKEND` | Fresh local Abbott rebuild with three named devices, 41 real patent inputs per case, source-backed disclosure links, typed source views, user edit, versioned history, and selected-version JSON/English/Thai exports. |
| C. Development cohort/frontier | `PASS_DEVELOPMENT_ONLY_WITH_FRONTIER` | Frozen three-device/41-patent/61-disclosed-pair universe, 62 unjudged distractors, explicit groups and split, five offline methods, per-prefix quality/resource diagnostics, and `NOT_ESTIMABLE` uncertainty. |
| Scientific generalization, final holdout, UI, release | `NOT_RUN` | Bridge rights/cohort/split remain blocked; no independent relevance judgments or final holdout; Claude UI remains paused; restricted patent/disclosure text remains local-only. |

## Package A

The current history implementation uses same-directory staging, payload fsync,
atomic no-overwrite hard-link publication, expected-parent validation, directory
fsync where supported, and recoverable staging cleanup. The current reproduction
record is `history-current.json` in this run folder:

- status: `READER_SAW_COMMITTED_CHAIN`
- reader during the writer pause: versions `[1]`
- published version-2 bytes during the pause: `null`
- final chain after release: versions `[1, 2]`
- provider/model calls: `0`

The focused regression suite covers same-base one-winner concurrency, stale
parents, interruption before publication, interruption after payload fsync,
interruption after publication, staging recovery, partial-reader behavior, and
selected-version export with user edits.

## Package B

Fresh artifacts are under the ignored local root
`results/healthtech/ht-abbott-dossiers-20261028-final-9eba00f/`:

- `HT-DEV-MITRACLIP`: 35 candidates, 14 retrieved candidates, 21 disclosed links, 41 patent inputs.
- `HT-DEV-TENDYNE`: 20 candidates, 3 retrieved candidates, 17 disclosed links, 41 patent inputs.
- `HT-DEV-TRICLIP`: 28 candidates, 5 retrieved candidates, 23 disclosed links, 41 patent inputs.

Each case has PMA/product facts, real patent inputs, source-backed disclosure
evidence, source-view output, history versions 1 and 2, a preserved
`review-note`, and selected-version JSON/English/Thai exports. The case outputs
separate `retrieved_candidate` from `disclosed_link` and preserve typed rights
IDs for the openFDA, Abbott disclosure, and Google-derived patent sources.

The adapter reads runtime cohort data and the source registry but does not use
`evaluator/references.json` to construct product queries or citations. Product
disclosure evidence is independent source evidence and remains product-level,
not claim-level semantic proof.

The older Abbott cohort registry still has a legacy free-text rights note, so its
provenance receipt remains `PASS_WITH_LEGACY_RIGHTS`. The new acquisition builder
now emits typed `rights_policy_id` values for future cohorts; this run did not
redownload or rewrite the old third-party artifact.

## Package C

The development freeze records three eligible Abbott devices, 41 canonical
patents, 61 product-level disclosed pairs, 62 unjudged distractor pairs, two
exact-patent overlap components, unknown family mapping, and no final holdout.
The current frontier contains HT-B0a, HT-B0b, HT-B1, HT-B2, and HT-B3 with zero
provider calls, zero paid cost, zero errors, and actual prefix-level resource
rows. Uncertainty is `NOT_ESTIMABLE` because the slice has three queries, two
exact-patent groups, one company, unknown family mapping, and no final holdout.

The separate Boston development cohort remains independently provenance-checked
at 13/13 disclosed pairs under `TYPED_POLICY_ID`; it is not substituted for
Bridge gold.

## Rights and release boundary

The canonical rights matrix records source URLs, clauses/locators, checked date,
source revisions, basis hashes, intended-use decisions, and limits for openFDA,
Abbott, Google-derived patent text, and Boston Scientific. Abbott disclosure and
Google-derived patent text remain `BLOCKED_LOCAL` for product display and
redistribution. Typed policy IDs are provenance bindings, not license grants.

No paid or free remote provider inference, cloud/GPU execution, deployment,
outreach, credential/session read, Bridge payload acquisition, clinical/FTO/
validity/investment analysis, customer validation, or public redistribution was
performed.

Machine-readable evidence is in `verification.json`; concise continuation work is
in `NEXT_ACTIONS.md`.
