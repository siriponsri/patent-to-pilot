# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 22 Nov 2026 (Asia/Bangkok)

**Program:** PTP-2026-11-21, goals G01–G08 (owner package `docs/owner/owner-note-21112026/`, owner-local, untracked).

**ACCOUNT SWITCH CHECKPOINT, 22 Nov ~16:30:** start from
[docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122.md](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122.md). It has a
paste-ready prompt, the state and the open owner items. The owner's decisions D1–D8 of 22 Nov are in
[docs/maintenance/OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md). Lessons for a new account:
[docs/maintenance/AGENT-LESSONS.md](docs/maintenance/AGENT-LESSONS.md). Verify with `git log -5`.

### Goal status

| Goal | Status | Evidence / next action |
|---|---|---|
| G01 Shared core and local vertical slice | **COMPLETE** | [G01/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md): 16 tests, smoke 15/15, browser QA at 1280/360 px, restart persistence. Owner still to observe: Explorer double-click and default-browser auto-open. |
| G02 Provider, ingestion and dataset contracts | **COMPLETE** (22 Nov, USD 0) | [G02/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md): provider ports with Ollama / OpenAI-compatible / Anthropic adapters and policy; index generations; hybrid mode; text/MD ingestion into owner projects; dataset registry and adapters. Real route: Qwen3-Embedding-0.6B on dr-train CPU through an SSH tunnel ([receipt](artifacts/owner-program/PTP-2026-11-21/G02/REAL_EMBEDDING_ROUTE.json)). Not real-tested: paid API (no envelope), Ollama (not installed), reranker. PDF parked (needs a package approval). |
| G03 Baselines and candidate policy on allowed DEV | **IN PROGRESS 22 Nov** | Protocol v1 decided: support_frontier_v0 **PARKED** (VAL SF\* − F\* ALL R@200 −0.020 [−0.025, −0.014]); F\* = Qwen3×2 + PatEmbed×2 ([memo](docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md)). Amendment 1 (field obligations): **PARKED** (P1-DEV +0.0018; VAL −0.0054 [−0.0107, 0.000]; memo §4a). Amendment 2 (learned selector on TRAIN labels) is frozen at 8e759b8e and was **RUNNING** detached at the account switch (`/data/ptp-paper2/g03-dev/a2.log` ends `G03_A2_DONE`; the decision is in `results-a2.json`). Next: memo §4b, the G03 closing summary, then pull/prune `g03-dev`. The V100 is shared with another user's service (thaivoice, 24 GB); do not touch it. | Uses the G02 ports. DAPFAM is not a tuning set in this program. Carry over the AM-7 lessons: always report IN and OUT, keep N4 IPC-demotion as a counterexample, treat co-citation as one action. |
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
  **Stage 2 MEASURED 22 Nov** ([B53-STAGE2-RESULTS.md](docs/writing/is2/results/B53-STAGE2-RESULTS.md)):
  - None of the 10 primary instruction contrasts on C (153 queries) is significant; Holm p ≥ 0.695, Δ between +0.001 and
    +0.009.
  - So the near-zero instruction effect holds under all five first stages.
  - Scrambled ≈ Generic. BGE plain pair is worse than Qwen3 everywhere.
  - Phase closed: [pull/prune summary](artifacts/maintenance/20261122-b53-pull/SUMMARY.md).
  - B53 run TSVs on dr-train are now `runs/F*.tsv.gz`.
  - `b53/inputs/` was deleted 22 Nov after owner approval (D4); `b53/` is now 203 MB.
  - IS2 drafts updated 22 Nov:
    - short paper v0.2: Markdown + docx, 9 pages;
    - slides outline v2;
    - deliverables;
    - committee response;
    - Workbench demo storyboard.
- **IS2 papers (22 Nov):** Thai and English editions, 8 pages each, 3 figures, in
  [docs/writing/is2/paper/](docs/writing/is2/paper/) (`IS2-paper-th/en.docx/.pdf`). Advisor: ผศ.ดร. ทัศนัย พลอยสุวรรณ.
  - Open: the Paper 53 DOI, the English byline title, and the acknowledgments line.
  - **Owner decisions 22 Nov (D1, D5, D6):**
    - IS2 = "research + demo" (Paper 53 → B53 bridge → G03 DEV findings → B53.0 → Workbench demo);
    - English byline "Tuchsanai Ploysuwan", with the title in footnote 2 only;
    - acknowledgments = AI-use statement only.
    - Re-scope the papers and slides next.

### Running jobs

- G03 amendment 2 on dr-train (detached; see the goal table). Nothing else of this project runs.
- B53.0 measured 22 Nov ([B53-0-RESULTS.md](docs/healthtech/research/b53-0/B53-0-RESULTS.md)): TAC→TAC consistent with
  the DAPFAM paper in 11 of 12 cells. Caution: F0 patembed-base may overlap DAPFAM through PatenTEB.
- The B53 evaluation finished, and the G02 embedding shim and its folder were removed from dr-train after QA, and its logs
  are in `artifacts/owner-program/PTP-2026-11-21/G02/`.
- **21 Nov dr-train cleanup done** ([summary](artifacts/maintenance/20261121-dr-train-cleanup/SUMMARY.md), runbook
  [DR-TRAIN-ARTIFACT-RUNBOOK.md](docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md), script
  `scripts/maintenance/pull_dr_train_artifacts.py`): small result files are archived and sha256-verified in
  `../_private_artifacts/dr-train-archive/20261121/`. On dr-train, about 21.8 GB was freed: dry-run, pilot and failed
  directories removed; duplicate FT run TSVs removed; unique run TSVs compressed in place as `run-*.tsv.gz` (read them with
  `gunzip -c`). `b53/` is not yet archived.

### Next steps

The order and prompt are in the handoff file §1:
1. G03 amendment 2. If it is parked, keep working on acquisition (D2): pre-declare a new candidate-bringing mechanism.
2. PatenTEB overlap audit (D3, download approved).
3. IS2 re-scope to research + demo (D1, D5, D6), Thai and English.
4. `pypdf` and the PDF ingestion adapter (D8).
5. OpenRouter profiles (D7).
6. Then G04 planning.

### Owner decisions

**Decided 22 Nov:** D1–D8 in [OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md):
- IS2 = research + demo;
- keep working on acquisition;
- PatenTEB download approved;
- `b53/inputs` deleted;
- byline "Tuchsanai Ploysuwan";
- acknowledgments = AI statement only;
- OpenRouter with several research-relevant models;
- `pypdf` yes; no local Ollama, so GPU work goes to dr-train and RunPod via MCP.

**Still pending:**
- per-job caps for RunPod. (OpenRouter E1 = USD 8 / 35,000 requests was **approved 22 Nov**: D9,
  [proposal](docs/maintenance/API-BUDGET-PROPOSAL-20261122.md).)
- the Paper 53 DOI;
- the G01 launcher observation.

Also, unchanged:
- large derived files on dr-train are kept (owner, 21 Nov);
- two git stashes from 30 Oct 2026 (`ba92cf3a`, `5e95e5c2`) were kept; drop them only on request.
