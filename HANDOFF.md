# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 21 Nov 2026 (Asia/Bangkok)

**Program:** PTP-2026-11-21, goals G01–G08 (owner package `docs/owner/owner-note-21112026/`, owner-local, untracked).

**Last verified pushed base before this update:** `40780c97` (G01 Workbench). The housekeeping commit that rewrote this file
follows it; check `git log -3` for the containing commit.

### Goal status

| Goal | Status | Evidence / next action |
|---|---|---|
| G01 Shared core and local vertical slice | **COMPLETE** | [G01/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md): 16 tests, smoke 15/15, browser QA at 1280/360 px, restart persistence. Owner still to observe: Explorer double-click and default-browser auto-open. |
| G02 Provider, ingestion and dataset contracts | **NEXT** | Chat/embedding/reranking ports (Ollama, OpenAI-compatible, native Anthropic), text/Markdown ingestion, dataset registries. Lexical-only mode must stay usable. USD 0 unless the owner sets an envelope. |
| G03 Baselines and candidate policy on allowed DEV | Not started | Needs G02. DAPFAM is not a tuning set in this program. |
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
  Stage 2 (reranker scoring, resumable per query) was last recorded at 69/905 queries on dr-train and is **unverified this
  session**; check `b53/queue_b53_stage2.log` before relying on it.
- **IS2 drafts:** [docs/writing/is2/](docs/writing/is2/) (short paper v0.1, committee response, slides outline). Advisor
  details and Stage 2 numbers are pending.

### Running jobs

- None started by this session. A parallel session (`drtrain-cleanup`) is pulling and pruning this project's dr-train
  artifacts and `../_private_artifacts`; it commits only under `artifacts/maintenance/` and `scripts/maintenance/`. Read its
  report before starting dr-train work.

### Next steps

1. Start G02 from `docs/owner/owner-note-21112026/02_GOALS_AND_PHASES.md` §G02 and `product/` specs; reuse the G01 core.
2. Ask the owner to observe the two remaining G01 launcher checks (double-click, browser auto-open).
3. Confirm B53 Stage 2 state on dr-train (read-only) and record it here.
4. After each phase, pull dr-train artifacts to local and delete remote copies that are no longer needed.

### Owner decisions pending

- Whether and when to resume B53 Stage 2 on the V100.
- Any spending envelope for G02 API provider tests (default: USD 0, local/lexical only).
- Two git stashes from 30 Oct 2026 (`ba92cf3a`, `5e95e5c2`) were kept; drop them only on request.
