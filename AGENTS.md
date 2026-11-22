# Agent instructions — Patent-to-Pilot

These rules apply to every coding agent (Claude, Codex or others) on every account. [CLAUDE.md](CLAUDE.md) carries the full
standing rules; this file is the shared summary and must stay consistent with it.

## Start of session

1. Read [CLAUDE.md](CLAUDE.md), [HANDOFF.md](HANDOFF.md) and [INDEX-PLAN.md](INDEX-PLAN.md).
2. Verify the checkout: `git status --short --branch`, `git log -3`, and that no other agent is writing the same files.
3. The current plan is the outcome-based P0–P5 plan of `docs/owner/owner-note-22112026/` (owner-local). Its live state is
   `docs/tracking/owner-note-22112026/`. Update that state only through `python scripts/tracking/ptp_tracker.py`.
   G01–G08 (PTP-2026-11-21), G01–G22 and HT-* identifiers in historical records keep their original meanings.

## One writer, one handoff

- One active writer per set of files. Record ownership and running jobs in HANDOFF.md.
- Update HANDOFF.md (current state, rewritten in place) and, when goal or evidence locations change, INDEX-PLAN.md: after a
  finished step, an owner decision, a new blocker or a failed attempt; before background or long jobs; before ending a
  session. Commit and push them with the work they describe.
- If publication fails, keep local changes and record the failure; never claim a sync that did not happen.

## Hard limits

- Never open protected TEST data. Never let an exposed test set select a method.
- No paid API, GPU rental or download without a recorded owner approval and envelope.
- dr-train: `ssh chaw@100.77.149.83`, approved V100 only (`CUDA_VISIBLE_DEVICES=1`), one GPU job at a time. After every
  phase, pull this project's artifacts to local, then delete remote copies that are no longer needed.
- Pre-declare protocols, endpoints and selection rules before computing. Report failures, retries and unknown costs.
- Paper 86 is banned in journal papers; arXiv:2605.24297 is not used as a source.
- Never read or print `.env` or credentials; never force-push, reset, clean, rewrite history or change ACLs/global config.
- Never edit `docs/owner/`. Commit only your own files with explicit paths.
- Report to the owner in Thai; write code, docs and the paper in English.

## Evidence and software invariants

- Keep source ID, version, content hash and exact locator on every piece of evidence. A literal quote match proves source
  integrity, not semantic support.
- Runtime inputs never contain evaluator labels, gold-derived queries or hidden oracles; evaluators live outside the engine.
- Unjudged is not negative. Known-link recall is not exhaustive recall. Schema validity is not correctness.
- Test changed behaviour with small hand-checkable fixtures. Run `python -m pytest` before committing code; the only
  accepted pre-existing failures are the 8 SACR r2/r3 supervisor budget tests.
- Keep audit receipts for research runs in `docs/healthtech/audits/<run-id>/` (historical convention) or the goal folder in
  `artifacts/owner-program/PTP-2026-11-21/<goal>/`. Large or restricted data stay in `../_private_artifacts/` with hashes
  recorded in Git.
