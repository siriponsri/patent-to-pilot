# Next actions

- Keep the clean-checkout fixture-backed backend suite as the reproducibility gate for HealthTech A/B/C.
- After the implementation commit is recorded, update `verification.json` with that commit hash and rerun only the fresh clean-worktree verification required by the handoff.
- Treat real `results/healthtech` integration as `NOT_RUN` until the local cohort and model-cache inputs are explicitly available and in scope.
- Keep Bridge, final holdout, provider inference, deployment, outreach, clinical/FTO analysis, and UI paused.
