# Claude instructions for Patent-to-Pilot

## Start here

Read [HANDOFF](HANDOFF.md), [INDEX-PLAN](INDEX-PLAN.md), the [LOE-Bench plan](docs/loe-bench/PLAN.md), the [LOE-Bench lane handoff](docs/loe-bench/HANDOFF.md) and [AGENTS](AGENTS.md). Verify repository, branch, remote, last three commits and other active writers. Under D40 (roles approved by the owner on 27 Nov 2026), Claude Opus 5.5 is the main planner and the only reviewer. GPT-6.2 Astra (high) is co-planner for methodology decisions only. GPT models execute through Codex, with each executor taking one task card on a `loe/<task-id>` branch cut from `research/loe-bench` in its own checkout. Executor model by card type: GPT-6.2 Sol xhigh for code and statistics that decide results (FIX1, T4, T3), GPT-6.2 Sol high for other code and drafts (T2, T1, T5, GPU runs), and GPT-6 Luna high for mechanical cards (T7, T9, T12, Thai demo curation). Writing deliverables (registrations, IS short papers, reports) are drafted by Antigravity Gemini 4 Hydrogen (xhigh), critiqued by GPT-6.2 Astra high as co-planner, then audited and finalized by Claude (owner decision, 28 Nov 2026). Figures and slide presentations are designed and created by Claude (owner decision, 28 Nov 2026). Applications and product (UI, demo apps, report design) are owned, designed and built by the Product Owner, Claude Sonnet 5.5 (medium), working from the [product PRD](docs/product/prd/PRD-MWD-v1.md) that the main planner and co-planner draft; the main planner reviews product branches; GPT executors may build data pipelines behind the product (D42, owner decision, 28 Nov 2026). GPU work moves from dr-train (offline) to RunPod, or to Vast.ai once its MCP is installed, within a recorded owner envelope.

## Current mandate (D41, 28 November 2026)

Build [Market Window Dossier](docs/loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026), the working name for a pharma market-research workflow. Forecast the launch window before bioequivalence or comparative trials so teams can assess whether demand will still be there at launch. For scarce freedom-to-operate (FTO) evaluators, provide a review queue, dated evidence pack and verification checklist for decision support. Qualified counsel determines freedom to operate. LOE-Bench remains the research benchmark for abstention-aware, evidence-traced entry forecasting, with a prospective Track A freeze. All data must be open. RA Pharma is folded in as the Thai-context layer, and the program must ship a Thai-context demo. The previous RA Pharma plan, [evidence interface](docs/ra-pharma/EVIDENCE-CONTRACT.md) and memory stay as history and as inputs to the Thai demo. Track method evidence, product readiness and publication readiness separately.

**Planner evidence.** For every Planner assignment, proposal or substantive claim, cite a relevant primary research paper and identify a benchmark or named competitor. Link both sources and explain which task, metric or product workflow they support. Distinguish a measured head-to-head result from an external reference or an untested hypothesis.

**Mandatory task closeout.** Use the project [documentation skill](.agents/skills/ra-pharma-writing/SKILL.md). Update all affected English documentation, the assigned HANDOFF and project memory after every task, including blocked and failed work. LOE-Bench executors write a task receipt in `docs/loe-bench/receipts/`; the Orchestrator owns the [lane HANDOFF](docs/loe-bench/HANDOFF.md) and [lane memory](docs/loe-bench/MEMORY.md) and updates them at integration. Include the decision, evidence, failure or limitation and next action. Commit and push explicit paths on the assigned branch. Chat-only memory does not complete the handoff.

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
