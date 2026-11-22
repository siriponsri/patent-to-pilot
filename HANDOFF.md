# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 22 Nov 2026 (Asia/Bangkok)

**Program:** PTP-2026-11-21, goals G01–G08 (owner package `docs/owner/owner-note-21112026/`, owner-local, untracked).

**Session of 22 Nov afternoon (new account), checkpoint ~14:30 Bangkok:** the next-account task list was worked through.
Start a new account from [docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md).
The owner's decisions D1–D9 are in [docs/maintenance/OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md).
Lessons: [docs/maintenance/AGENT-LESSONS.md](docs/maintenance/AGENT-LESSONS.md). Verify with `git log -8`.

**Blocked on the owner (asked 22 Nov):**
1. Set `OPENROUTER_API_KEY` as a Windows user environment variable. G03 amendment 3's pilot cannot start without it.
2. IS2: the arc is decided (D10, Paper 86 exposure ceiling included; [outline v3](docs/writing/is2/IS2-OUTLINE-v3-20261122.md)).
   Open: rebuild now with an A3 placeholder, or wait for the A3 pilot.
3. Choose a PatenTEB option (audit §5).

### Goal status

| Goal | Status | Evidence / next action |
|---|---|---|
| G01 Shared core and local vertical slice | **COMPLETE** | [G01/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md): 16 tests, smoke 15/15, browser QA at 1280/360 px, restart persistence. Owner still to observe: Explorer double-click and default-browser auto-open. |
| G02 Provider, ingestion and dataset contracts | **COMPLETE** (22 Nov, USD 0) + 22 Nov add-ons | [G02/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md): provider ports, index generations, hybrid mode, text/MD ingestion, dataset registry. **Add-on D8 (22 Nov):** `pypdf` 6.21.4 in `.venv` (extra `pdf` in pyproject); PDF text-layer ingestion (`pdf_text_layer_v1`, page markers, PDF sha256 in `origin_path`, scans/encrypted refused); tests `tests/test_ptp_g02_pdf_ingest.py`. **Add-on D7/D9:** four OpenRouter chat templates (`openrouter-*`, reasoning off, temperature 0, USD 0.05 / 20 requests each), `request_options` profile field, `cost_usd` recorded from usage; tests `tests/test_ptp_g02_openrouter_profiles.py`. A real OpenRouter Workbench check waits for `OPENROUTER_API_KEY`. |
| G03 Baselines and candidate policy on allowed DEV | **IN PROGRESS 22 Nov** | [memo](docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md). v1 support_frontier_v0 **PARKED**; F\* = Qwen3×2 + PatEmbed×2. A1 field obligations **PARKED** (§4a; a mask defect in its T/C routes is now disclosed there). **A2 learned selector PARKED** (§4b): VAL LS\* − F\* ALL +0.0017 [−0.0019, +0.0054], IN lower −0.0060 < −δ. **A3 LLM query expansion: FROZEN** ([protocol](docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md), commit 82ab143a; code e5a3f616). Pilot inputs ready on dr-train `g03-dev/a3/` and locally `../_private_artifacts/g03-a3/inputs/`; format smoke on 4 models done (USD 0.00064, [spend](docs/healthtech/research/g03-dev/g03-dev-a3-spend.json)). **Pilot not started: `OPENROUTER_API_KEY` not set.** | Run order in §"Next steps". The V100 is shared with another user's service (thaivoice, 24 GB); do not touch it. Always report IN and OUT; keep N4 as a counterexample. |
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

- **Nothing of this project runs** (22 Nov ~14:30). A2 finished (`G03_A2_DONE`); the g03-dev compression finished
  (`COMPRESS_DONE`).
- **G03 phase close (v1, A1, A2) done:** [pull/prune summary](artifacts/maintenance/20261122-g03-pull/SUMMARY.md).
  - 826 small files were pulled and sha256-verified.
  - 327 arm run TSVs were compressed in place (24.44 GB freed; `g03-dev` 36 → 13 GB).
- B53.0 measured 22 Nov ([B53-0-RESULTS.md](docs/healthtech/research/b53-0/B53-0-RESULTS.md)): TAC→TAC consistent with
  the DAPFAM paper in 11 of 12 cells.
- **PatEmbed–DAPFAM (D3), 22 Nov:**
  - The train-split audit is **blocked**: PatenTEB's train/validation sets are not released (authors' README).
  - The partial audit found DAPFAM families inside PatenTEB data: 50 of 1,247 queries and 466 of 45,336 corpus
    families.
  - So PatEmbed stays "possibly contaminated" on DAPFAM.
  - Report: [PATENTEB-OVERLAP-AUDIT-20261122.md](docs/healthtech/research/b53-0/PATENTEB-OVERLAP-AUDIT-20261122.md).
- 21 Nov dr-train cleanup: [summary](artifacts/maintenance/20261121-dr-train-cleanup/SUMMARY.md), runbook
  [DR-TRAIN-ARTIFACT-RUNBOOK.md](docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md).

### Next steps

1. **G03 A3 pilot**, as soon as the owner sets `OPENROUTER_API_KEY`. In a new PowerShell, for each of the 4 models:
   `python scripts/research/g03_a3_llm_expand.py --queries ../_private_artifacts/g03-a3/inputs/queries-dev-val.jsonl --apps-file ../_private_artifacts/g03-a3/inputs/apps-pilot.json --model <id> --ledger-root ../_private_artifacts/g03-a3/ledger`.
   - Read `get-credits` before and after.
   - Write `a3/pilot-costs.json` (model → USD from `--summary`).
   - Upload each `ledger/<model_dir>/P1-DEV.jsonl` to dr-train `g03-dev/a3/ledger/`.
   - Copy `g03_a3_routes.py`, `g03_a3_decide.py` and `g03_queue_a3_pilot.sh` to `g03-dev/code/`.
   - Run `setsid nohup bash code/g03_queue_a3_pilot.sh > a3-pilot.log 2>&1 < /dev/null & disown`.
   - It ends `G03_A3_PILOT_DONE`. Apply the GO/STOP rule (protocol §3); Stage B only on GO.
   - Expected pilot spend ≈ USD 1–2.
2. **IS2 re-scope (D1/D5/D6/D10):** arc fixed in [outline v3](docs/writing/is2/IS2-OUTLINE-v3-20261122.md). Rebuild
   TH/EN with the `kmitl-is-paper` and `academic-figures` skills, and update `SLIDES-OUTLINE.md` and `DEMO-STORYBOARD.md`.
   §6 (A3) stays a placeholder until the pilot decision.
3. A real Workbench OpenRouter profile check (≤ USD 0.20; E1) once the key is set.
4. Then G04 planning: DAPFAM headline routes are BM25, Qwen3 and Arctic; PatEmbed is reported separately with the
   caveat.

### Owner decisions

**Decided 22 Nov:** D1–D10 in [OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md):
- IS2 = research + demo;
- keep working on acquisition;
- PatenTEB download approved (but the train split is not public);
- `b53/inputs` deleted;
- byline "Tuchsanai Ploysuwan";
- acknowledgments = AI statement only;
- OpenRouter multi-model, with E1 = USD 8 / 35,000 requests approved (D9);
- `pypdf` yes (installed 22 Nov); no local Ollama;
- D10: Paper 86's exposure ceiling enters the IS2 arc (IS2-only; unpublished; arXiv:2605.24297 not cited).

**Still pending:**
- `OPENROUTER_API_KEY` in the environment;
- whether to rebuild IS2 now (A3 as a placeholder) or after the A3 pilot;
- the PatenTEB option (accept the partial audit, fetch the other 12 test splits, or write to the authors);
- RunPod per-job caps;
- the Paper 53 DOI;
- the G01 launcher observation.

Also, unchanged:
- large derived files on dr-train are kept (owner, 21 Nov), so they are compressed, not deleted;
- two git stashes from 30 Oct 2026 (`ba92cf3a`, `5e95e5c2`) were kept; drop them only on request.
