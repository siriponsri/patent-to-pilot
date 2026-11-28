# Agent instructions — Patent-to-Pilot

These rules apply to every coding agent (Claude, Codex or others) on every account. [CLAUDE.md](CLAUDE.md) carries the full
standing rules; this file is the shared summary and must stay consistent with it.

## Start of session

1. Read [CLAUDE.md](CLAUDE.md), [HANDOFF.md](HANDOFF.md) and [INDEX-PLAN.md](INDEX-PLAN.md).
2. Verify the checkout: `git status --short --branch`, `git log -3`, and that no other agent is writing the same files.
3. D41 (28 Nov 2026) makes [Market Window Dossier](docs/loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026) the active product, from a pre-development launch-window forecast to an evidence pack and checklist for freedom-to-operate (FTO) review. LOE-Bench remains the research benchmark. Follow the program's task cards and protocol. For the Thai demo layer and RA Pharma history follow the [RA Pharma plan and ownership board](docs/ra-pharma/MASTER-PLAN.md), [evidence contract](docs/ra-pharma/EVIDENCE-CONTRACT.md) and your assigned brief. LOE-Bench roles (owner-approved 27 Nov 2026): Claude Opus 5.5 is the main planner and the only reviewer. GPT-6.2 Astra high is co-planner. GPT executors use GPT-6.2 Sol xhigh for result-critical code and statistics, GPT-6.2 Sol high for other code, and GPT-6 Luna high for mechanical cards. Model by card type is listed in the plan. Use the published lane branch in its own checkout. The Planner owns main.
4. Read the applicable project memory before work and use the [documentation skill](.agents/skills/ra-pharma-writing/SKILL.md). At every task close update all affected English documentation, the responsible HANDOFF and project memory, including failed attempts and blockers. Commit these with explicit paths and push your branch. A chat summary alone cannot close a task.
5. Maintain one writer per path. In LOE-Bench (D40), executors write only their card paths and a receipt in `docs/loe-bench/receipts/`. The main planner owns `docs/loe-bench/HANDOFF.md`, `MEMORY.md`, `PLAN.md` and `TECHNIQUE-LEDGER.md`. In the historical RA Pharma lanes, each executor owned its lane HANDOFF.md and MEMORY.md under `docs/ra-pharma/`; update the handoff at major events and before long jobs. The Planner maintains the root HANDOFF, INDEX-PLAN, [shared memory](docs/ra-pharma/MEMORY.md) and master board. Update the inherited P registry only through `python scripts/tracking/ptp_tracker.py`.
6. Record failed publication locally. Verify the remote revision before reporting a push.

## Planner evidence

For every Planner assignment, proposal or substantive claim, cite a relevant primary research paper and identify a benchmark or named competitor. Link both sources and explain which task, metric or product workflow they support. Distinguish a measured head-to-head result from an external reference or an untested hypothesis. [Owner decision D32](docs/maintenance/OWNER-DECISIONS-20261122.md#d32--require-a-paper-and-a-comparator-for-planner-work-26-november-2026).

## Hard limits

- Never open protected TEST data. Never let an exposed test set select a method.
- Use paid APIs or GPU rental only within a recorded, applicable envelope. State the pod price and obtain owner approval before creation. Delete it after use. D27 authorizes necessary in-scope installs and dataset downloads for the new direction. D29 also authorizes necessary project-local skills, harnesses, tools and MCP. Record each item, version, use rights and hash; gated terms and scope changes require their own decision.
- dr-train: `ssh chaw@100.77.149.83`, approved V100 only (`CUDA_VISIBLE_DEVICES=1`), one GPU job at a time. After every
  phase, pull this project's artifacts to local, then delete remote copies that are no longer needed.
- Pre-declare protocols, endpoints and selection rules before computing. Report failures, retries and unknown costs.
- Paper 86 is banned in journal papers; arXiv:2605.24297 is not used as a source.
- Never read or print `.env` or credentials; never force-push, reset, clean, rewrite history or change ACLs/global config.
- Never edit `docs/owner/` (D40: only the Orchestrator may copy or manage files there). Commit only your own files with explicit paths.
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
