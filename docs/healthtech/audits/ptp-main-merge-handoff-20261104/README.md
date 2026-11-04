# Patent-to-Pilot main merge and Claude handoff

- Run ID: `ptp-main-merge-handoff-20261104`
- Observed: `2026-11-04T12:15:46.2028916Z`
- Repository: `C:/Users/User/Desktop/myProject/patent-to-pilot`
- Branch: `main`
- Tested source merge HEAD: `26be1c1f037c35352a5c0c4bbc8f0fbc0c135f09`
- Handoff-document commit: `7e8fd1a`

## Outcome

The continuation candidate was integrated into `main` after preserving the
pre-existing owner handoff in a separate commit:

- Candidate integration commit: `a71d808`
- Preserved main-owner commit: `f77c502`
- Merge commit: `26be1c1`

Current status is **merged, locally verified, and ready to push**. The current
`main` HEAD includes the docs-only handoff commit above. This is not
an overall goal-complete claim.

| Area | Status | Boundary |
|---|---|---|
| Engineering O1-O4 | COMPLETE for the current offline engineering scope | Current-head local HTTP/UI, source inspection, edit/history/reopen/export, local generation and guarded accounting are covered by committed receipts and regressions. |
| Scientific evidence | PARTIAL | No admissible final semantic device-patent holdout and no paid local/API matched comparison. Historical Stryker material remains diagnostic only. |
| Business value | PARTIAL | Solo developer operational proxy and scenario analysis only; no independent user validation, revenue, willingness-to-pay, ROI, or customer evidence. |
| Manuscript/WPI | PARTIAL | Draft, references, appendix, checklist and cover letter are present; owner review remains required, WPI-specific Aims/Scope and Guide details were not fully verified, and nothing was submitted. |
| Paid API | BLOCKED before reservation | Supplied credit snapshot was stale for the 300-second live gate. No provider call, reservation, retry, unknown billing, ledger mutation, budget reset, or time-window reset occurred. |

## Verification

- Python regression on merged `main`: exit `0`, reaching 100%; the exact prior
  candidate-bound receipt is `655 passed, 2 skipped`.
- Frontend unit tests: `73 passed, 1 optional skip`.
- HealthTech JSON receipts under `docs/healthtech`: `964` parsed successfully.
- Source merge-marker scan: clean.
- Non-audit `git diff --check`: clean. Historical audit XML/patch receipts
  retain their original recorded whitespace.
- Before push, `main` was ahead of `origin/main` by `78` commits and behind by
  `0`.

## Paid branch handoff

Use the existing canonical E2 ledger and preserve its history. The known
state remains: SQLite integrity `ok`; four legacy settled receipts totaling
`USD0.0001464`; zero operational attempts; zero pending/unknown attempts;
prospective E2 allowance `USD1`; unknown history preserved. Do not create a
zero ledger, reset the epoch, retry an unknown request, or edit the stale
credit timestamp.

The only paid-branch input still required is one fresh, non-secret credit
snapshot for the existing dispatch key with matching E2 scope and an
observation time no older than 300 seconds at dispatch. Refresh exact-route
pricing in that same admission window, recheck rights and writer quiescence,
then reserve only the bounded canary through the canonical ledger.

## Claude handoff

Claude can resume from `main` at the final HEAD above. Start by reading this
folder, `AGENTS.md`, `GOAL.md`, `PLAN.md`,
`docs/healthtech/long-runs/CURRENT_ACCEPTANCE_MATRIX.json`, and the latest E2
admission audit. Keep local/offline work independent of the paid gate. Do not
rerun completed GPU work or old scientific benchmarks merely to refresh a
receipt, and do not treat engineering or schema validity as scientific or
business completion.

Cleanup is intentionally conservative: Claude/Luna/owner worktrees and dirty
research work must remain preserved. Only verified-clean, unused temporary
worktrees may be removed after the push is confirmed.
