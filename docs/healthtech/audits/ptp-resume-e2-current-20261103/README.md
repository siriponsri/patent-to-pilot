# Patent-to-Pilot E2 resume checkpoint

Recorded: 2026-11-03T15:34:58.8264436Z

This checkpoint resumes the existing Patent-to-Pilot goal. It does not create a
goal, reset a budget or time window, recreate the E2 journal, replay a pending
request, launch a new GPU job, or close the research goal.

## Candidate

- Worktree: C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103
- Branch: codex/patent-to-pilot-long-run-20261103
- HEAD: 88dc40471cb9078f929c02bb893cfa1e364da841
- Working tree: intentionally dirty; owner, Claude, Luna, and research changes
  were preserved.
- The latest committed patch is the documentation-only commit
  88dc40471cb9078f929c02bb893cfa1e364da841. Source and test repairs remain
  uncommitted in this candidate, so this is not a clean release.

## Offline verification

The current working tree was checked with the E2/API/payload/O3 regression
batch:

- 84 tests passed.
- 0 failures, 0 errors, 0 skips.
- JUnit receipt: focused-tests.xml.
- Receipt SHA-256:
  8931cfa61155ce8cda6f55bde5dc88ccd540de779a62ecd695a4a2767a8b9e22.
- python -m compileall -q src scripts/healthtech: passed.
- Scoped git diff --check passed after excluding the known pre-existing
  CRLF/trailing-whitespace noise in memory/next-actions.md.

This is engineering evidence for the dirty candidate only. It is not a paid
model result, a scientific superiority claim, or a clean-release verification.

## E2 journal readback

The canonical Windows journal was inspected read-only:

%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3

- SQLite integrity: ok.
- Authorization: PTP-HT-OR-E2-20261103-USD100.
- Ledger: ptp-healthtech-openrouter-local-e2-20261103.
- Operational attempts: 0.
- Pending or unknown attempts: 0.
- Attempt contexts: 0.
- Scope binding: empty because no reservation has occurred.
- Preserved legacy settled receipts: 4.
- Preserved legacy actual: USD0.0001464.
- History: UNKNOWN_OWNER_ACCEPTED_CUTOVER.
- Prospective allowance: USD1.00.
- No zero ledger, budget reset, window reset, retry, or journal mutation was
  observed.

The legacy spend and unresolved history boundary remain preserved. The USD1
allowance is prospective exposure, not evidence of provider credit and not a
new USD100 budget.

## Provider gate

The latest available sanitized owner-environment observation remains the
read-only receipt in
../ptp-api-current-credit-recheck-20261103/metadata-observation.json.
The key value was not printed, copied, or persisted.

- /api/v1/key: HTTP 200.
- Key class: ordinary non-management.
- Lifetime usage: USD0.0001464.
- Current scoped account credit: unavailable.
- Remaining key limit or explicit unlimited observation: unavailable.
- Account scope: not reconciled.

The latest available public route observation is
../ptp-api-current-credit-recheck-20261103/public-route-pricing-observation.json
at 2026-11-03T13:18:15.745843Z: DeepInfra for qwen/qwen3-32b, prompt
USD0.08/M, completion USD0.28/M. It must be refreshed inside the
runner's 300-second admission window after current credit evidence exists.

Paid dispatch therefore remains BLOCKED_BEFORE_RESERVATION. No provider
request, reservation, attempt, retry, or cost was created in this checkpoint.

## Completed GPU evidence

The completed dr-train evidence remains a separate local diagnostic:

%LOCALAPPDATA%/PatentToPilot/healthtech/evidence/20261103-pepo-patent-current/

- Run: 20261103-pepo-patent-current.
- Candidate binding: 88dc40471cb9078f929c02bb893cfa1e364da841.
- Protocol: fresh patent encoder/retrieval diagnostic, separate from paid
  generation.
- Saved-vector verification: passed.
- BM25: 21/61 known links, macro Recall@20 0.392685, micro Recall@20
  0.344262, macro nDCG@20 0.430022.
- PatEmbed: 24/61, macro Recall@20 0.430073, micro Recall@20 0.393443,
  macro nDCG@20 0.409533.
- multilingual E5: 27/61, macro Recall@20 0.481021, micro Recall@20
  0.442623, macro nDCG@20 0.455981.

These values are a small frozen-query diagnostic. They are not pooled with
older B0b/B4 protocols, do not establish general superiority, and do not
replace semantic gold or a final holdout.

## Process and ownership boundary

- Existing SSH inspection PID 18096 was inspected and left untouched.
- Claude processes were observed and left untouched.
- No provider, GPU, pytest, or remote experiment process remained active after
  this checkpoint's verification.
- No ACL, safe.directory, credential, unrelated project, or other worktree was
  changed.

## Status and next action

- Engineering: PASS_CURRENT_DIRTY_CANDIDATE_OFFLINE_VERIFIED_NOT_RELEASED.
- Scientific evidence: PARTIAL_DESCRIPTIVE_NOT_ESTIMABLE.
- Business validation: PARTIAL_SCENARIO_ONLY_EXTERNAL_NOT_RUN.
- Manuscript: PARTIAL_OWNER_REVIEW_WPI_GUIDE_UNVERIFIED.
- Paid API: BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE.
- Goal: active; not complete and not blocked globally.

The one remaining paid input, if the comparison is still required, is a
non-secret current scoped v2 credit/limit snapshot for the same account/key,
or a sanctioned pointer to one. It must not contain the API key. Once supplied,
reconcile it against E2, refresh route pricing, revalidate the frozen
rights-cleared payload, and reserve only the existing USD0.25 canary. Until
then, continue offline/manuscript work without replaying calls or rerunning the
frozen GPU diagnostic.
