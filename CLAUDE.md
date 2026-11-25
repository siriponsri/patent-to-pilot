# Claude instructions for Patent-to-Pilot

## Start here

Read [HANDOFF](HANDOFF.md), [INDEX-PLAN](INDEX-PLAN.md), the [RA Pharma plan](docs/ra-pharma/MASTER-PLAN.md) and [AGENTS](AGENTS.md). Verify repository, branch, remote, last three commits and other active writers. Research uses GPT 6.2 high on `research/ra-pharma`. Product uses Claude Sonnet 5.5 medium on `product/ra-pharma`. Each session uses its own checkout.

## Current mandate

Build a Thai-first regulatory affairs dossier with patent/FTO, Thai and foreign regulatory, and official correspondence specialists. Research inherits the IS1 exposure and reading-depth question and tests adaptive skills under a matched budget. See the [evidence interface](docs/ra-pharma/EVIDENCE-CONTRACT.md) for the boundary between a patent disclosure and applicant evidence. Track method evidence, product readiness and publication readiness separately.

**Mandatory task closeout.** Use the project [documentation skill](.agents/skills/ra-pharma-writing/SKILL.md). Update all affected English documentation, the assigned HANDOFF and project memory after every task, including blocked and failed work. Research and Product each own the MEMORY.md next to their lane HANDOFF. The Planner owns [shared memory](docs/ra-pharma/MEMORY.md) and records accepted cross-lane lessons at integration. Include the decision, evidence, failure or limitation and next action. Commit and push explicit paths on the assigned branch. Chat-only memory does not complete the handoff.

The [decision register](docs/maintenance/OWNER-DECISIONS-20261122.md) and [index](INDEX-PLAN.md) preserve previous results, budgets and scope. Original gated materials and untracked owner records remain read-only. Read [dr-train memory safety section 2a](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md) before any approved remote work.

## 3. Standing rules (all remain in force)

1. **Never open protected TEST data** (research TEST splits, sealed qrels, per-query TEST outputs). Exposed sets stay exposed;
   they never select methods.
2. **No paid API, RunPod or other GPU rental without an owner envelope** (a recorded amount and scope). Quote each pod's hourly rate before creation, get owner approval, and delete the pod after use. D27 approves in-scope installs and dataset downloads for S1–S5. Record each item's revision, rights and digest. D29 authorizes necessary RA Pharma project-local skills, harnesses, tools and MCP integrations. Record version, license, digest, purpose and smoke result.
3. **dr-train:** reach it as `ssh chaw@100.77.149.83`. Use only the approved V100, always with `CUDA_VISIBLE_DEVICES=1`.
   GPU0 (RTX 2080 Ti) is not approved. One GPU job at a time, under the shared GPU lock.
4. **Pre-declare before computing.** Freeze the protocol, endpoints and selection rule before any number exists; one settle
   per job; report failures and unknown costs, never repair outputs silently.
5. **Report to the owner in Thai.** All project-authored documentation, including plans, receipts, READMEs and memory, is English only. Preserve source evidence in its original language. The product UI and sample correspondence serve Thai readers.
6. **Commit only your own files**, with explicit paths (never `git add -A`). Push to the assigned lane branch after verification. Only the Planner integrates to main.
7. **Update the handoff on major events:** a finished step, an owner decision, a new blocker, before long or background jobs,
   and before ending a session. On a lane, update its HANDOFF and task status. The Planner maintains the root HANDOFF and dispatch board. At every task close also update the affected documentation and the project memory entry for that lane. Update inherited P rows only with the tracker CLI.
8. **After every phase, pull this project's dr-train artifacts to local, then delete the remote copies that are no longer
   needed** (this project's folders only, never other users' or services' data). Procedure:
   [docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md](docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md).
9. **Paper 86 is banned in journal papers** (never mentioned, cited or reused). It is allowed only in the IS2 track.
   `tests/test_org_adaptive_terminology.py` enforces this over `docs/writing/journal/`.
10. **arXiv:2605.24297 is not used as a source.**
11. Paper 53 may be cited as the authors' own prior work (iSAI-NLP 2026 program listing; no DOI verified).
12. No LLM judge as ground truth. Literal source match is source integrity, not semantic support.
13. Never read or print `.env` or credentials. No force-push, `git reset --hard`, `git clean`, or history rewriting.

## 4. Protected code (G01 and G02 shipped)

Do not change `src/patent_to_pilot/workbench/`, `scripts/ptp_run.py`, `Start-PTP.cmd`, `tests/` or
`artifacts/owner-program/` without a goal that requires it. D29 grants the Product lane the Workbench and launcher scope documented in the current board. Other lanes follow their own path ownership.
Run the test suite before committing code; the only accepted pre-existing failures are the 8 SACR r2/r3 supervisor budget
tests.
- For the integrated Windows gate, use the dependency profile, Chromium setup and a short, fresh basetemp in the [S4 verification receipt](docs/evidence-scope/receipts/S4-integrated-verification.md). Record the exact interpreter, command, skips, failures and raw exit code.

## 5. Where things are

| Need | Location |
|---|---|
| Run the Workbench | `Start-PTP.cmd`, or `python scripts/ptp_run.py --doctor` / `--smoke` / `--serve` |
| Engine and Workbench code | `src/patent_to_pilot/workbench/` (G01), legacy modules in `src/patent_to_pilot/` |
| Historical S0–S5 plan and freeze | [Master plan](docs/evidence-scope/MASTER-PLAN.md) and [prospective freeze](docs/evidence-scope/FREEZE.md) |
| Inherited plan and receipts (P0–P5) | `docs/tracking/owner-note-22112026/` (board, registry, receipts, AFFiNE pages); tool `scripts/tracking/ptp_tracker.py` |
| Foundation receipts (G01/G02) | `artifacts/owner-program/PTP-2026-11-21/<goal>/` |
| Budget ledger | `src/patent_to_pilot/budget/` (shared reservations for research and Workbench calls) |
| Research evidence (frozen protocols, results, audits) | `docs/healthtech/research/`, `docs/healthtech/audits/` |
| Writing | `docs/writing/journal/` (the one paper), `docs/writing/is2/` (IS2) |
| Housekeeping record of 21 Nov 2026 | [docs/HOUSEKEEPING-20261121.md](docs/HOUSEKEEPING-20261121.md) |
| Private artifacts outside Git | `../_private_artifacts/` (never commit their contents) |
