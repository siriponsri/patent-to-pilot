# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 24 Nov 2026, about 08:00 (Asia/Bangkok)

**Account handoff in progress.** The owner stopped this account because its weekly limit is near. Start with
[docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md).

**Plan.** Outcome-based **P0–P5** (owner note 22 Nov). Live board:
[docs/tracking/owner-note-22112026/PHASE_BOARD.md](docs/tracking/owner-note-22112026/PHASE_BOARD.md).
- Tool: `python scripts/tracking/ptp_tracker.py show|set|render`.
- Status fields stay separate:
  - `method_evidence` = NOT_YET_DEMONSTRATED (the A3r1 pilot GO is a spending gate, not a result);
  - `product_readiness` = core verified, with modes, Thai search, structural acquisition and selective revision checked;
  - `publication_readiness` = draft with results NOT_RUN.

### Phase status (35 tasks: 20 COMPLETE, 5 PARTIAL, 10 NOT_STARTED)

| Phase | Done | Open |
|---|---|---|
| P0 control | 5/7 | T02/T03 AFFiNE web sync blocked (the repo board is the tracker of record) |
| P1 A3 model panel | **6/6 COMPLETE** | A3r1 CONTINUE (exploratory) — carried into P2 |
| P2 structural acquisition | 3/7 | T04 screen vs close controls → T05 freeze → T06 matched comparison → T07 attribution |
| P3 Thai transfer | 1/5 (+T02 PARTIAL) | T03 text-transfer comparisons, T04 structure/OCR, T05 freeze scope |
| P4 product | 3/5 (+T04 PARTIAL) | T04 merge policy v2.1 + source removal (D3); T05 clean-install user test |
| P5 manuscript/release/IS2 | 1/5 | T02 scoreboards, T03 artifact, T04 IS2, T05 close |

### Results so far (P1-DEV unless stated; ALL R@200, cluster bootstrap by art unit)

- **A3r1 CHECKPOINT (P1 closed, 24 Nov):** frozen rule **CONTINUE**. VAL F3\* − F\* = **+0.0213 [0.0146, 0.0280]**,
  IN +0.0189, OUT +0.0225 (all lower CI > 0); F3\* = `alloc-L0-Q1-P1-H1-K1` (DeepSeek V4 Flash H+K routes)
  ([receipt](docs/tracking/owner-note-22112026/receipts/P1-T05_stage_b_and_full_eval.md)). Exploratory: 4th VAL look;
  F\* uses C0 routes, so the stronger complete-content controls still have to be beaten in P2.

- **P2-T02 COMPLETE** ([receipt](docs/tracking/owner-note-22112026/receipts/P2-T02_coverage_control_results.md)):
  - Arctic C1 (complete content) − C0 = **+0.0165 [0.0144, 0.0186]**;
  - BM25-full − C0 = **+0.0223 [0.0200, 0.0247]**;
  - both become the new representation baselines;
  - structure C2 − C1 = −0.0087, so it gets no credit.
  - D19 is triggered: complete-content PatEmbed/Qwen3 (C1).
- **P1-T04 A3r1 pilot: frozen rule GO**, m\* = DeepSeek V4 Flash, Δ = **+0.0245 [0.0179, 0.0310]** against F\* 0.4334 on
  2,000 apps ([receipt](docs/tracking/owner-note-22112026/receipts/P1-T04_pilot_generation.md)). This is optimistic and
  only gates spending.
- **P3-T02 PARTIAL:** Thai packets-v1 (DEV 1,330 / held-out 3,779). WangchanX train covers 75.2% of NitiBench-CCL gold
  sections. DEV has no annex/table items.
- **P4-T02 COMPLETE** (execution modes). **P4-T04 PARTIAL:** selective = full in 10/11 scenarios; D2 is fixed on an
  unmerged branch; D3 (no source removal) is open.

### Running or pending at handoff

- **A3r1 is finished** (Stage B + full evaluation, pod deleted). Nothing is running. No pod exists.
- **Next:** merge D25, finish D19, then P2-T04 (see the handoff doc). Ask the owner before opening pods.
- **Unmerged branches:**
  - `worktree-agent-a6d18c2dded3f86f2` (56267477): D25 policy v2.1. Run the full gate, then merge.
  - `worktree-agent-aa1038afae41aaf77` (ffae7a99): WIP D19 package, not verified. Finish its tests, review, merge.

### Money and access (24 Nov)

- **E1R** (OpenRouter + Typhoon; USD 50, notify 40): committed USD 3.853 (33,685 attempts) after Stage B. OpenRouter
  credits: total 20, usage about 5.5.
- **RunPod:** prepaid balance about USD 40.6. **No pod and no volume exist.**
  - R1 (D20, USD 20): about USD 5.1 used (P2-T02 pods).
  - R2 (D22/D24, USD 60, notify 45): about USD 11.3 used (A3r1 pilot pods 9.6 + full-evaluation pod 1.7).
  - D21 allows a network volume for reusable data; none has been created.
- **Upload route:** US data centres only. EU-SE-1 measured 47 KB/s from the owner PC; US measured 3–8 MB/s over 4 streams.
- `OPENROUTER_API_KEY` and `TYPHOON_API_KEY` are user environment variables. The RunPod SSH key is
  `~/.ssh/runpod_paper86_20261017`.
- **dr-train is back** (rebooted 24 Nov about 06:48). Partial build deleted, Thai data copied, and the deferred P2-T02
  checks were launched on 24 Nov (CPU, watchdog). Plan and memory-safety rules: handoff doc §2a.

### Owner decisions

- D1–D25 are in [OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md); N01–N12 are in the owner
  note.
- Still open: the Paper 53 DOI and the 37.1% denominator; whether to report LLM-judge-graded NitiBench (rule 12); the G01
  launcher check; Thai annex/table packet sources.

Unchanged:
- large derived files on dr-train are kept;
- the two git stashes from 30 Oct 2026 are kept.
