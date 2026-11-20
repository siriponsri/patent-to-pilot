# Claude instructions for Patent-to-Pilot

**Program:** PTP-2026-11-21 (set by the owner on 21 Nov 2026). **Target:** IS2 presentation, March 2027.
**Read at session start, in this order:** this file → [HANDOFF.md](HANDOFF.md) (current state) → [INDEX-PLAN.md](INDEX-PLAN.md)
(goal and evidence index) → [AGENTS.md](AGENTS.md) (shared agent rules). Then verify the actual checkout with `git status`
and `git log -3`; chat memory is never a substitute for these files.

The dated history that used to live here (Nov 2026 HealthTech, Paper 1, SACR, BridgeRet and AM-7 checkpoints) is preserved
verbatim in [archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md). It is provenance, not
instruction.

## 1. What the project is

One research paper with three connected contributions, implemented by **one shared Evidence Engine** and delivered through
two tracks:

- **Research:** frozen configurations, benchmark adapters, isolated evaluators, ablations, uncertainty and result provenance.
- **Product:** a local Workbench (one Python server, bundled UI, SQLite, local files) that calls the same engine.

Proposed contributions (novelty and performance are still to be established):
C1 support-frontier acquisition and repair policy; C2 executable versioned evidence architecture (PLAN → ACQUIRE → COMMIT);
C3 reproducible evaluation package (DAPFAM, Thai Gazette transfer, declared update episodes; NitiBench+ optional).

The owner's program package is in `docs/owner/owner-note-21112026/` (start at `00_START_HERE.md`). It is **owner-local and
untracked: never edit, move, delete or commit anything under `docs/owner/`.**

## 2. Current state (details in HANDOFF.md)

- **G01 local Workbench vertical slice: COMPLETE** (commit `40780c97`). Status and receipts:
  [artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md).
  Only owner-observed item left: Explorer double-click of `Start-PTP.cmd` and default-browser auto-open.
- **Next goal: G02** (provider, ingestion and dataset contracts).
- **Research P1 / AM-7: parked.** Stage 2a results (DEV/VAL, descriptive) are in
  [docs/healthtech/research/paper1-bridgeret/am7/stage2a/](docs/healthtech/research/paper1-bridgeret/am7/stage2a/).
  The owner gate in AM-7 §6.4 failed, so no paid step runs without the owner.
- **B53 / IS2:** Stage 1 measured ([B53-STAGE1-RESULTS.md](docs/writing/is2/results/B53-STAGE1-RESULTS.md)); Stage 2 was
  last recorded incomplete on dr-train. IS2 drafts live in [docs/writing/is2/](docs/writing/is2/).

## 3. Standing rules (all remain in force)

1. **Never open protected TEST data** (research TEST splits, sealed qrels, per-query TEST outputs). Exposed sets stay exposed;
   they never select methods.
2. **No paid API, RunPod or other GPU rental without an owner envelope** (a recorded amount and scope). Downloads need a
   per-item owner approval.
3. **dr-train:** reach it as `ssh chaw@100.77.149.83`. Use only the approved V100, always with `CUDA_VISIBLE_DEVICES=1`.
   GPU0 (RTX 2080 Ti) is not approved. One GPU job at a time, under the shared GPU lock.
4. **Pre-declare before computing.** Freeze the protocol, endpoints and selection rule before any number exists; one settle
   per job; report failures and unknown costs, never repair outputs silently.
5. **Report to the owner in Thai.** Code, paper, product and developer docs are English-first; keep source documents in their
   original language.
6. **Commit only your own files**, with explicit paths (never `git add -A`). Push to `origin main` after a verified package.
7. **Update the handoff on major events:** a finished step, an owner decision, a new blocker, before long or background jobs,
   and before ending a session. Rewrite the current-state section of HANDOFF.md in place; do not append diaries.
8. **After every phase, pull this project's dr-train artifacts to local, then delete the remote copies that are no longer
   needed** (this project's folders only, never other users' or services' data).
9. **Paper 86 is banned in journal papers** (never mentioned, cited or reused). It is allowed only in the IS2 track.
   `tests/test_org_adaptive_terminology.py` enforces this over `docs/writing/journal/`.
10. **arXiv:2605.24297 is not used as a source.**
11. Paper 53 may be cited as the authors' own prior work (iSAI-NLP 2026 program listing; no DOI verified).
12. No LLM judge as ground truth. Literal source match is source integrity, not semantic support.
13. Never read or print `.env` or credentials. No force-push, `git reset --hard`, `git clean`, or history rewriting.

## 4. Protected code (G01 just shipped)

Do not change `src/patent_to_pilot/workbench/`, `scripts/ptp_run.py`, `Start-PTP.cmd`, `tests/` or
`artifacts/owner-program/` without a goal that requires it. Run `python -m pytest` before committing code; the only accepted
pre-existing failures are the 8 SACR r2/r3 supervisor budget tests.

## 5. Where things are

| Need | Location |
|---|---|
| Run the Workbench | `Start-PTP.cmd`, or `python scripts/ptp_run.py --doctor` / `--smoke` / `--serve` |
| Engine and Workbench code | `src/patent_to_pilot/workbench/` (G01), legacy modules in `src/patent_to_pilot/` |
| Goal receipts | `artifacts/owner-program/PTP-2026-11-21/<goal>/` |
| Research evidence (frozen protocols, results, audits) | `docs/healthtech/research/`, `docs/healthtech/audits/` |
| Writing | `docs/writing/journal/` (the one paper), `docs/writing/is2/` (IS2) |
| Housekeeping record of 21 Nov 2026 | [docs/HOUSEKEEPING-20261121.md](docs/HOUSEKEEPING-20261121.md) |
| Private artifacts outside Git | `../_private_artifacts/` (never commit their contents) |
