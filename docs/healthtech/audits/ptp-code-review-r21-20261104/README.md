# Current-head source and test review r21

Recorded on 4 November 2026 (Asia/Bangkok). This continues the existing
Patent-to-Pilot goal and does not create a new goal, paid attempt, GPU job,
dataset download, merge, push, or branch deletion.

## Review boundary

Candidate worktree:

`C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`

Branch: `codex/patent-to-pilot-long-run-20261103`

HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`

The worktree is intentionally dirty. Owner, Claude, Luna, documentation,
source, test, and audit changes were preserved. The review inspected the
goal-specific changes around API generation, rights-cleared payloads,
canonical ledger binding, local execution guards, private case journaling,
local E2 accounting, and real-baseline failure accounting.

This is a serial same-agent pre-owner review. It is not an independent review,
merge approval, publication approval, or evidence of scientific superiority.

## Specification axis

No new specification finding was found in this pass. The current candidate
continues to:

- require a canonical ledger for live dispatch and reject mock-ledger
  promotion;
- preserve pending and unknown billing instead of converting it to zero;
- reject duplicate attempt IDs, route substitution, stale source revisions,
  missing source provenance, and non-rights-cleared model-visible fields;
- retain returned model text in the private per-case journal while omitting
  messages, credentials, headers, raw HTTP bodies, and exception text from the
  journal allow-list and public receipt;
- record wall/CPU time on failed baseline attempts and mark unmeasured
  candidate/resource fields as unknown; and
- preserve the owner-set USD30 OpenRouter MCP/provider cap as metadata separate
  from the existing USD100 project envelope and E2 accounting history.

No code change was required from this review.

## Standards axis

No new standards finding was found. The candidate remains intentionally dirty;
no unrelated refactor, reset, cleanup, credential read, external message,
paid request, GPU launch, dataset download, merge, push, or branch deletion was
performed.

The direct `pytest` entrypoint on this Windows environment does not place the
repository root on `sys.path` for tests importing the namespace package
`scripts`. The supported invocation used for this receipt is
`python -m pytest`, which honors the repository `pythonpath = ["src"]` setting
and passed the same test files.

## Verification

Focused tests on the exact current dirty candidate:

- API generation, private case journal, history migration, and release budget:
  `26 passed`.
- Rights-cleared generation payload, O3 repair/adversarial coverage, and HTTP:
  `64 passed`.
- Local execution, local epoch, current-head frontier, and private frontier:
  `27 passed`.
- Real baseline failure/accounting coverage: `4 passed`.
- Existing full offline regression r19 remains the candidate-bound record:
  `657 collected; 655 passed; 2 skipped; 0 failed; exit 0`.
- `git diff --check`: pass; only pre-existing LF/CRLF conversion warnings were
  emitted for dirty documentation files.

The focused test commands and the r19 receipt are recorded in
`verification.json` and
`../ptp-offline-regression-r19-20261104/verification.json`.

## Paid and resource boundary

This review performed no paid provider call, reservation, retry, ledger write,
budget reset, runtime-window reset, GPU job, or dataset download. The paid
branch remains `BLOCKED_BEFORE_RESERVATION`: the existing MCP receipt is
account-level and does not bind a current exact dispatch-key scope or remaining
key limit, and route pricing still needs a fresh in-window observation before
admission. The E2 journal and unknown history were not changed.

## Disposition

`READY_FOR_OWNER_REVIEW_NOT_MERGE`

The engineering candidate remains usable for owner review. The overall goal is
still `ACTIVE_NOT_COMPLETE_NOT_BLOCKED` because paid comparison, final semantic
holdout evidence, owner-controlled WPI checks, and clean release/publish
decisions remain incomplete or blocked. No claim of user validation, revenue,
ROI, adaptive superiority, or journal acceptance is made.
