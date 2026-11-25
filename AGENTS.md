# Agent instructions — Patent-to-Pilot

These rules apply to every coding agent (Claude, Codex or others) on every account. [CLAUDE.md](CLAUDE.md) carries the full
standing rules; this file is the shared summary and must stay consistent with it.

## Start of session

1. Read [CLAUDE.md](CLAUDE.md), [HANDOFF.md](HANDOFF.md) and [INDEX-PLAN.md](INDEX-PLAN.md).
2. Verify the checkout: `git status --short --branch`, `git log -3`, and that no other agent is writing the same files.
3. Follow the [RA Pharma plan and ownership board](docs/ra-pharma/MASTER-PLAN.md), [evidence contract](docs/ra-pharma/EVIDENCE-CONTRACT.md) and your assigned brief. GPT 6.2 high owns Research. Claude Sonnet 5.5 medium owns Product. Use the published lane branch in its own checkout. The Planner owns main.
4. Read the applicable project memory before work and use the [documentation skill](.agents/skills/ra-pharma-writing/SKILL.md). At every task close update all affected English documentation, the responsible HANDOFF and project memory, including failed attempts and blockers. Commit these with explicit paths and push your branch. A chat summary alone cannot close a task.
5. Maintain one writer per path. Each executor owns its lane HANDOFF.md and MEMORY.md under `docs/ra-pharma/`; update the handoff at major events and before long jobs. The Planner maintains the root HANDOFF, INDEX-PLAN, [shared memory](docs/ra-pharma/MEMORY.md) and master board. Update the inherited P registry only through `python scripts/tracking/ptp_tracker.py`.
6. Record failed publication locally. Verify the remote revision before reporting a push.

## Hard limits

- Never open protected TEST data. Never let an exposed test set select a method.
- Use paid APIs or GPU rental only within a recorded, applicable envelope. State the pod price and obtain owner approval before creation. Delete it after use. D27 authorizes necessary in-scope installs and dataset downloads for the new direction. D29 also authorizes necessary project-local skills, harnesses, tools and MCP. Record each item, version, use rights and hash; gated terms and scope changes require their own decision.
- dr-train: `ssh chaw@100.77.149.83`, approved V100 only (`CUDA_VISIBLE_DEVICES=1`), one GPU job at a time. After every
  phase, pull this project's artifacts to local, then delete remote copies that are no longer needed.
- Pre-declare protocols, endpoints and selection rules before computing. Report failures, retries and unknown costs.
- Paper 86 is banned in journal papers; arXiv:2605.24297 is not used as a source.
- Never read or print `.env` or credentials; never force-push, reset, clean, rewrite history or change ACLs/global config.
- Never edit `docs/owner/`. Commit only your own files with explicit paths.
- Report to the owner in Thai. All authored project documentation, including receipts and memory, is in English. Preserve original evidence and Thai product content.

## Evidence and software invariants

- Keep source ID, version, content hash and exact locator on every piece of evidence. A literal quote match proves source
  integrity, not semantic support.
- Runtime inputs never contain evaluator labels, gold-derived queries or hidden oracles; evaluators live outside the engine.
- Unjudged is not negative. Known-link recall is not exhaustive recall. Schema validity is not correctness.
- Test changed behaviour with small hand-checkable fixtures. Run `python -m pytest` before committing code; the only
  accepted pre-existing failures are the 8 SACR r2/r3 supervisor budget tests.
- Keep RA Pharma research receipts under the research lane in the dispatch board. Earlier programs keep audit receipts in `docs/healthtech/audits/<run-id>/` or the goal folder in
  `artifacts/owner-program/PTP-2026-11-21/<goal>/`. Large or restricted data stay in `../_private_artifacts/` with hashes
  recorded in Git.
