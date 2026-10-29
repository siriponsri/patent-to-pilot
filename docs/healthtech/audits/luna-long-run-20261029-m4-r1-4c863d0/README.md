# HealthTech M4 R1 policy/runner audit

- Run ID: `luna-long-run-20261029-m4-r1-4c863d0`
- Scope: versioned OpenRouter Round 1 budget seam and offline fault closure
- Base commit: `4c863d0a01d8fc7211682745786a35f1474963f5`
- Candidate commit: `7395b92` (`healthtech: add versioned R1 budget seam`)
- Working tree rule: unrelated owner artifacts and paused Claude worktree preserved
- Provider calls: `0`
- Paid cost: `$0`
- Verdict: `PASS_ENGINEERING_OFFLINE`; live branch remains `BLOCKED_LOCAL`

## Implemented

- Historical `ProjectBudget()` keeps the existing `ptp-owner-5usd-20261027` policy/hash behavior.
- `Round1ProjectBudget` binds a new policy version to authorization `PTP-HT-OR-R1-20261028-USD8`.
- Total authorization is `$8.00`; dispatch admission is capped at `$7.00`.
- Phase caps are canary `$0.40`, paired pilot `$5.40`, and robustness `$1.20`.
- Exact model/provider and official pricing-snapshot hashes are required inputs; no historical alias is treated as current by the helper.
- `Round1Runner` reuses `OpenRouterAdapter`, `BudgetedTransport`, and the existing transport seam with zero retries and exact routing.
- Old-policy SQLite files fail closed instead of being rebound or reset.

## Evidence

See `verification.json` for source hashes, commands, and outcomes. See `REPORT.md` for the acceptance summary and limits.
