# G6 numerical claim-to-artifact checkpoint

Observed: 2026-11-04 Asia/Bangkok (recorded UTC `2026-11-03T23:37:29.6876142Z`)

## Candidate and scope

- Existing goal: Patent-to-Pilot O1–O4 / G0–G8; no new goal or epoch.
- Worktree: `patent-to-pilot-long-run-20261103`.
- Branch: `codex/patent-to-pilot-long-run-20261103`.
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`.
- Tree state: intentionally dirty; owner/Claude/Luna and prior evidence changes were preserved.
- Change type: documentation and continuation-record update only. No source, model, dataset, ledger, or GPU artifact was rerun or rewritten.

## Completed package

The first READY continuation item, `manuscript_claim_table` (G6), is complete on
the current candidate. The manuscript now contains:

1. a medical-subset diagnostic with the full denominator `1,920 = 983 both-screen + 937 target-unscreened`;
2. a numerical claim-to-artifact index for Results 7.1–7.7, including dataset/cohort, split, denominator, method/model revision, evidence state, artifact path, and SHA-256; and
3. a reproducibility appendix with the recorded current-head frontier commands, failure-accounting result, private-input boundary, local Qwen receipt hashes, and no-semantic-gold limitations.

The negative BM25/adaptive observation, unequal realized budgets, development-only
cohorts, distinction between disclosed links/retrieved candidates/unjudged pairs,
and source-binding limitations remain explicit. No source binding is described as
semantic validation.

## Verification

- Markdown links: `73` checked, `0` missing.
- JSON receipts: `CURRENT_ACCEPTANCE_MATRIX.json`, strong-follow-up verification, and medical recheck all parsed successfully.
- Focused tests: `6 passed`, `0 failed`, `0 errors`, `0 skipped`.
- `git diff --check`: pass for the changed manuscript.
- Queue item: `manuscript_claim_table = COMPLETE`.
- Progress and next-actions pointers updated to select G5 next.

## Resource and evidence boundary

- Paid provider calls: `0`.
- GPU jobs: `0`.
- Downloads: `0`.
- Ledger mutations/reservations: `0`.
- Retries or pending-call replays: `0`.
- API branch: still paused at current scoped credit/key-limit evidence.
- Final semantic holdout: still unavailable; current results remain descriptive or component diagnostics.
- External business validation: not performed in the solo project and not claimed.
- Merge/push/publish: not performed.

## Next action

Continue with `solo_operational_case_table` (G5) using the existing three-case
local Qwen and dossier receipts. Keep human time, independent user validation,
revenue, willingness-to-pay, ROI, semantic accuracy, and paid API comparison
unmeasured unless new authorized evidence exists.
