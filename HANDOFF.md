# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 24 Nov 2026 (Asia/Bangkok)

**Account takeover active.** Codex owns D19 verification and P2-T04 integration in this
session. At takeover `main` matched `origin/main` at `5891d7ea`; the existing Claude branches and owner-local files
are preserved. Ordered instructions: [next-account handoff](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md).

**Plan.** Outcome-based **P0–P5** (owner note 22 Nov). Live board:
[docs/tracking/owner-note-22112026/PHASE_BOARD.md](docs/tracking/owner-note-22112026/PHASE_BOARD.md).
- Tool: `python scripts/tracking/ptp_tracker.py show|set|render`.
- Status fields stay separate:
  - `method_evidence` = NOT_YET_DEMONSTRATED (A3r1 is exploratory; a matched structural gain has not been measured);
  - `product_readiness` = core verified, with modes, Thai search, structural acquisition and selective revision checked;
  - `publication_readiness` = draft with results NOT_RUN.

### Phase status (35 tasks: 20 COMPLETE, 5 PARTIAL, 10 NOT_STARTED)

| Phase | Done | Open |
|---|---|---|
| P0 control | 5/7 | T02/T03 AFFiNE web sync blocked (the repo board is the tracker of record) |
| P1 A3 model panel | **6/6 COMPLETE** | A3r1 CONTINUE (exploratory) — carried into P2 |
| P2 structural acquisition | 3/7 (+T04 PARTIAL) | D19 follow-up → T04 screen vs close controls → T05 freeze → T06 matched comparison → T07 attribution |
| P3 Thai transfer | 1/5 (+T02 PARTIAL) | T03 text-transfer comparisons, T04 structure/OCR, T05 freeze scope |
| P4 product | 3/5 (+T04 PARTIAL) | T04 policy v2.1 merged; source removal (D3) and T05 clean-install user test open |
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
- **P4-T02 COMPLETE** (execution modes). **P4-T04 PARTIAL:** policy 2.1.0 merged at `98d6c37a`. D25's full gate
  had exactly the eight permitted SACR failures, Workbench smoke passed 15/15 and selective/full comparisons
  matched in all 11 supported fixtures. D3 (source removal) is open.

### Running or pending at handoff

- **A3r1 is finished** (Stage B + full evaluation, pod deleted). Nothing is running. No pod exists.
- **D19 verification:** verified source `d30d9d51` merged at `563b10a8`. The combined full gate had 2,707 passed,
  eight skips, one known xfail and exactly the eight permitted SACR failures. Local P1-DEV staging and independent
  manifest verification passed for 85 files, including 54 filtered claims archives.
  [Readiness receipt](docs/tracking/owner-note-22112026/receipts/P2-T02_D19_readiness.md).
- **D26:** the owner approved opening eligible US RunPod pods, machine selection, parallel sub-agent work and a long-run
  goal. D19 can spend up to USD 20 within the existing R2 envelope.
- **Parallel checkpoint:** both workers finished. P2-T04 now has a hash-bound runtime and separate evaluator.
  The combined full gate had 2,741 passed, nine skips, one known xfail and exactly the eight permitted SACR cases.
  P2-T04 benchmark execution remains NOT_RUN. See the
  [preparation record](docs/healthtech/research/p2-coverage/P2-T04-SCREEN-PREPARATION.md).
- **PatEmbed complete:** all A2 gates passed. C1 replaces C0 under the frozen rule, ALL R@200
  +0.00718 [0.00505, 0.00936], from 0.41806 to 0.42523. Verified output is in
  `../_private_artifacts/p2t02-d19-runpod/p2t02-d19-patembed-results.tgz`. The collector pulled the archive at
  16:27:35 UTC. Scoped termination failed, so the RunPod management API deleted `arm09wy8rok4qk`. GET returned 404
  and the pod list shows only Qwen3. The billing API still lagged through parts of the 15:00–16:00 buckets.
  Carry a USD 6.00 provisional charge until final billing is visible. The full lexical corpus is also verified locally.
- **Qwen3 pod active:** `10813cm5sej2s2`, Secure RTX PRO 4500 Blackwell Server Edition in US-KS-2, quoted at
  USD 0.72/hour compute plus up to USD 0.03/hour ephemeral disk. Created 24 Nov 14:58:21 UTC after capacity returned.
  Setup started. Operational deadline 25 Nov 01:46:21 UTC and best-effort in-pod timer 01:54:21 UTC.
  USD 8.50 reserved. Pre-encode gates passed with window 511 and Qwen3 started C1 encoding at 15:20:29 UTC.
  The job launched with the optional fast-transfer setting off. Earlier L40S/RTX attempts and expired queue
  created no pod.
- **D19 settlement:** both workers have Bash progress watchers. The success-only collector
  `../_private_artifacts/settle-ptp-d19-on-success-20261124.sh` verifies a result archive before requesting termination
  of its assigned pod. Verify termination and provider billing independently after each collector.
- **P2-T04 artifact staging:** ten non-TEST runtime and historical inputs passed transfer and SHA-256 checks on
  `/data/ptp-paper2/p2t04-run-prep-20261124`. The 30 GiB MemAvailable guard did not trigger. The lexical stream
  has been materialized and hash-checked, the two evaluator inputs are in a separate directory, and both entry
  points from `ff9c2048` load on dr-train. Complete the comparator manifest after D19 before retrieval or scoring.

### Money and access (24 Nov)

- **E1R** (OpenRouter + Typhoon; USD 50, notify 40): committed USD 3.853 (33,685 attempts) after Stage B. OpenRouter
  credits: total 20, usage about 5.5.
- **RunPod:** prepaid balance was about USD 40.6 before D19. Only Qwen3 is active, USD 8.50 reserved.
  No network volume was created.
  - R1 (D20, USD 20): about USD 5.1 used (P2-T02 pods).
  - R2 (D22/D24, USD 60, notify 45): about USD 11.3 used (A3r1 pilot pods 9.6 + full-evaluation pod 1.7).
  - D21 allows a network volume for reusable data; none has been created.
- **Upload route:** US data centres only. EU-SE-1 measured 47 KB/s from the owner PC; US measured 3–8 MB/s over 4 streams.
- `OPENROUTER_API_KEY` and `TYPHOON_API_KEY` are user environment variables. The RunPod SSH key is
  `~/.ssh/runpod_paper86_20261017`.
- **dr-train is back** (rebooted 24 Nov about 06:48). The partial build was deleted, Thai data copied and hashes verified,
  and the deferred P2-T02 CPU checks completed. Deeper retrieval adds zero at R@200 and the coverage-control fusion is
  unchanged at 0.4230 ([receipt](docs/tracking/owner-note-22112026/receipts/P2-T02_coverage_control_results.md)).
  Memory-safety rules: next-account handoff §2a.

### Owner decisions

- D1–D26 are in [OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md); N01–N12 are in the owner
  note.
- Still open: the Paper 53 DOI and the 37.1% denominator; whether to report LLM-judge-graded NitiBench (rule 12); the G01
  launcher check; Thai annex/table packet sources.

Unchanged:
- large derived files on dr-train are kept;
- the two git stashes from 30 Oct 2026 are kept.
