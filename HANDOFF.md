# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 22 Nov 2026 (Asia/Bangkok)

**Program:** PTP-2026-11-21, goals G01–G08 (owner package `docs/owner/owner-note-21112026/`, owner-local, untracked).

**Last verified pushed base before this update:** `6742ce7b`. The G02 commit that rewrote this file follows it; check
`git log -3`. Lessons for a new agent account: [docs/maintenance/AGENT-LESSONS.md](docs/maintenance/AGENT-LESSONS.md).

### Goal status

| Goal | Status | Evidence / next action |
|---|---|---|
| G01 Shared core and local vertical slice | **COMPLETE** | [G01/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md): 16 tests, smoke 15/15, browser QA at 1280/360 px, restart persistence. Owner still to observe: Explorer double-click and default-browser auto-open. |
| G02 Provider, ingestion and dataset contracts | **COMPLETE** (22 Nov, USD 0) | [G02/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md): provider ports with Ollama / OpenAI-compatible / Anthropic adapters and policy; index generations; hybrid mode; text/MD ingestion into owner projects; dataset registry and adapters. Real route: Qwen3-Embedding-0.6B on dr-train CPU through an SSH tunnel ([receipt](artifacts/owner-program/PTP-2026-11-21/G02/REAL_EMBEDDING_ROUTE.json)). Not real-tested: paid API (no envelope), Ollama (not installed), reranker. PDF parked (needs a package approval). |
| G03 Baselines and candidate policy on allowed DEV | **NEXT** | Uses the G02 ports. DAPFAM is not a tuning set in this program. Carry over the AM-7 lessons: always report IN and OUT, keep N4 IPC-demotion as a counterexample, treat co-citation as one action. |
| G04 Matched patent benchmark (DAPFAM) | Not started | DAPFAM is previously exposed (B53 evaluated all 1,247 queries); report it as such. |
| G05 Transfer and evidence maintenance | Not started | Thai Gazette public benchmark; NitiBench+ optional. |
| G06 English-first product beta | Not started | Can run alongside G04/G05. |
| G07 Unified paper and evidence audit | Not started | Manuscript goes in `docs/writing/journal/` (Paper 86 guard applies). |
| G08 IS2 demonstration and release rehearsal | Not started | March 2027. |

### Research and IS2 (historical evidence, kept with its original scope)

- **P1 / AM-7: PARKED.** Stage 2a done 20 Nov (DEV/VAL only, descriptive, USD 0):
  [am7/stage2a/](docs/healthtech/research/paper1-bridgeret/am7/stage2a/) (`stage2a-results.json`, `stage2a-tables.md`,
  `sensitivity.json`, `STAGE2A-REPORT-TH.md`). Selected A* = RRF(U0, N5) gave +0.010 MR@200 over U0; IPC-demotion N4 dominated
  both endpoints; the AM-7 §6.4 owner gate failed. No paid step (A3 reranker) without the owner.
- **P1-BridgeRet fine-tuning:** all 5 grid configs below the zero-shot Qwen3 and PatEmbed baselines on P1-DEV
  ([sstar-grid30k.md](docs/healthtech/research/paper1-bridgeret/ft-grid30k/sstar-grid30k.md),
  [P1-RETHINK-20261120.md](docs/healthtech/research/paper1-bridgeret/P1-RETHINK-20261120.md)). RunPod spend USD 18.54 of
  the USD 30 envelope; all pods deleted. No P1 TEST was read.
- **P1-DAPFAM (old Paper 1): CLOSED**, H1 inconclusive
  ([TEST-RESULT-TABLES.md](docs/healthtech/research/paper1-report/TEST-RESULT-TABLES.md)). Its test qrels are exposed; never
  rerun S8 jobs.
- **B53 (IS2 core):** Stage 1 measured 19 Nov ([B53-STAGE1-RESULTS.md](docs/writing/is2/results/B53-STAGE1-RESULTS.md)).
  Stage 2 scoring **FINISHED**: `b53/queue_b53_stage2.log` ends `B53_STAGE2_SCORES_DONE` (seen 22 Nov ~07:25 Bangkok,
  PID gone, V100 idle). Scores are in `/data/ptp-paper2/b53/stage2/scores-*.tsv`. **Evaluation RUNNING** since
  22 Nov ~07:50 on dr-train CPU (`python3 code/b53_stage2_eval.py inputs runs stage2 stage2-results.json`, PID 2053484,
  script sha 93305f9e…). The log `b53/logs/stage2-eval.log` ends `EXIT 0` when done. Then run
  `scripts/writing/render_b53_stage2.py`, write the results doc, then pull and prune `b53/` (runbook below).
- **IS2 drafts:** [docs/writing/is2/](docs/writing/is2/) (short paper v0.1, committee response, slides outline). Advisor
  details and Stage 2 numbers are pending.

### Running jobs

- B53 Stage 2 evaluation on dr-train CPU (above); no GPU is used. The G02 embedding shim and its folder were removed from dr-train after QA, and its logs
  are in `artifacts/owner-program/PTP-2026-11-21/G02/`.
- **21 Nov dr-train cleanup done** ([summary](artifacts/maintenance/20261121-dr-train-cleanup/SUMMARY.md), runbook
  [DR-TRAIN-ARTIFACT-RUNBOOK.md](docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md), script
  `scripts/maintenance/pull_dr_train_artifacts.py`): small result files are archived and sha256-verified in
  `../_private_artifacts/dr-train-archive/20261121/`. On dr-train, about 21.8 GB was freed: dry-run, pilot and failed
  directories removed; duplicate FT run TSVs removed; unique run TSVs compressed in place as `run-*.tsv.gz` (read them with
  `gunzip -c`). `b53/` is not yet archived.

### Next steps

1. B53 Stage 2 evaluation and rendering, then pull and prune `b53/` (scores are ready).
2. G03 from `02_GOALS_AND_PHASES.md` §G03 and `research/METHOD_SPEC.md` / `POLICY_V0.md`, using the G02 ports.
3. Ask the owner to observe the G01 launcher checks (double-click, browser auto-open).
4. After each phase, pull dr-train artifacts to local and delete remote copies that are no longer needed.

### Owner decisions pending

- Any spending envelope for API provider use (default USD 0; Claude profiles stay blocked).
- Optional per-item approvals: Ollama (local chat models) and `pypdf` (PDF ingestion).
- Large derived files on dr-train: the owner chose on 21 Nov to keep them for now.
- Two git stashes from 30 Oct 2026 (`ba92cf3a`, `5e95e5c2`) were kept; drop them only on request.
