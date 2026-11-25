# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 25 Nov 2026 (Asia/Bangkok)

**S0 complete.** The [S0–S5 master plan](docs/evidence-scope/MASTER-PLAN.md) implements the owner-approved direction. The owner authorized the prospective [questions and data design freeze](docs/evidence-scope/FREEZE.md), parallel research/product work and in-scope installs and dataset downloads. Only organization was activated. No S1–S5 run, download, install, remote job or spend was made for S0.

**Next activation:** dispatch [S1 research data](docs/evidence-scope/01-research-data.md) and [S2 product](docs/evidence-scope/02-product-workbench.md) together. The master contains the copy-ready goal for GPT 6.2 high. All S0 writing assignments (research documents, product documents, README/assets and integration) are closed on handoff. Establish one writer per lane on the next activation.

**Evidence at handoff:** new method NOT_RUN; existing Workbench core verified with synthetic material; local open-data alpha NOT_RUN; publication is a design draft. S1 pins new bytes and judgments, S2 demonstrates both languages. A positive DEV point estimate may open one bounded follow-up. Null research can close with its receipt and product can progress independently. Never promote these labels to a benchmark win or real-world usage claim.

**Inherited P0–P5 state:** the [evidence board](docs/tracking/owner-note-22112026/PHASE_BOARD.md) keeps the original IDs and measured outcomes. Update that registry only with the tracker CLI.

### Phase status (35 tasks: 20 COMPLETE, 4 PARTIAL, 11 NOT_STARTED)

| Phase | Done | Open |
|---|---|---|
| P0 control | 5/7 | T02/T03 AFFiNE web sync blocked (the repo board is the tracker of record) |
| P1 A3 model panel | **6/6 COMPLETE** | A3r1 CONTINUE (exploratory) — carried into P2 |
| P2 structural acquisition | 4/7 | T04 NO_GAIN; screened arm parked. A viable hypothesis is required before T05. |
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
  - D19 selected complete-content PatEmbed and Qwen3 (C1).
- **P2-T04 COMPLETE, NO_GAIN.** The unresolved-relation arm yielded ALL R@200 0.44372 against 0.44998 for the
  strongest eligible reference, complete-content fusion. Paired change was −0.00626 [−0.00902, −0.00369]. The frozen
  progression rule failed. Park this arm. P2-T05 confirmation remains NOT_RUN.
  [Matched screen result](docs/tracking/owner-note-22112026/receipts/P2-T04_results.md).
- **P1-T04 A3r1 pilot: frozen rule GO**, m\* = DeepSeek V4 Flash, Δ = **+0.0245 [0.0179, 0.0310]** against F\* 0.4334 on
  2,000 apps ([receipt](docs/tracking/owner-note-22112026/receipts/P1-T04_pilot_generation.md)). This is optimistic and
  only gates spending.
- **P3-T02 PARTIAL:** Thai packets-v1 (DEV 1,330 / held-out 3,779). 75.2% of NitiBench-CCL questions have a gold section that was a WangchanX train positive. DEV has no annex/table items.
- **P4-T02 COMPLETE** (execution modes). **P4-T04 PARTIAL:** policy 2.1.0 merged at `98d6c37a`. D25's full gate
  had exactly the eight permitted SACR failures, Workbench smoke passed 15/15 and selective/full comparisons
  matched in all 11 supported fixtures. D3 (source removal) is open.

### Inherited execution receipts through P2-T04

- **A3r1 finished** (Stage B + full evaluation; its pod was deleted).
- **D19 verification:** verified source `d30d9d51` merged at `563b10a8`. The combined full gate had 2,707 passed,
  eight skips, one known xfail and exactly the eight permitted SACR failures. Local P1-DEV staging and independent
  manifest verification passed for 85 files, including 54 filtered claims archives.
  [Readiness receipt](docs/tracking/owner-note-22112026/receipts/P2-T02_D19_readiness.md).
- **D26:** the owner approved opening eligible US RunPod pods, machine selection, parallel sub-agent work and a long-run
  goal. D19 operated under a sub-cap of USD 20 within the existing R2 envelope.
- **PatEmbed complete:** all A2 gates passed. C1 replaces C0 under the frozen rule, ALL R@200
  +0.00718 [0.00505, 0.00936], from 0.41806 to 0.42523. Verified output is in
  `../_private_artifacts/p2t02-d19-runpod/p2t02-d19-patembed-results.tgz`. The collector pulled the archive at
  16:27:35 UTC. Scoped termination failed, so the RunPod management API deleted `arm09wy8rok4qk`. GET returned 404
  and the pod list confirmed removal. Posted PatEmbed billing after catch-up is USD 5.98139. The full lexical
  corpus is also verified locally.
- **Qwen3 complete:** all A2 gates passed. C1 replaces C0 under the frozen rule, ALL R@200
  +0.01205 [0.01007, 0.01409], from 0.34736 to 0.35941. Verified archive
  `../_private_artifacts/p2t02-d19-runpod/p2t02-d19-qwen3-results.tgz`. The scoped termination failed, so management
  API deleted `10813cm5sej2s2` at about 25 Nov 00:34:53 UTC. GET returned 404 and the account pod list is empty.
  RunPod posted USD 7.07229 across both UTC billing days, including the closing period through deletion.
- **D19 complete:** both model baselines are C1. The gains are complete-content representation controls.
- **P2-T04 closed:** the owner-approved gate at `b4e0f903` passed all 2,000 BM25 lists (1,996 exact and four
  verified cutoff ties). Runtime and independent evaluator completed at 11:19:38 UTC on 25 Nov. All 22 returned
  file digests verified in `../_private_artifacts/p2t04-preflight-20261124/screen-v1-cutoff-tie/`. The raw trace was
  replaced by its verified gzip copy and duplicate staging files were pruned. There is no active project job.
  [Frozen protocol](docs/tracking/owner-note-22112026/receipts/P2-T04_frozen_protocol.md) and
  [execution receipt](docs/tracking/owner-note-22112026/receipts/P2-T04_execution.md).

### Historical resource checkpoint (25 Nov, before S0)

- **E1R** (OpenRouter + Typhoon; USD 50, notify 40): committed USD 3.853 (33,685 attempts) after Stage B. OpenRouter
  credits: total 20, usage about 5.5.
- **RunPod:** prepaid balance was USD 27.58 after both pods were deleted. Neither pod remains active.
  No network volume was created. D19 posted USD 13.05367 of the USD 20 sub-cap. USD 6.94633 remained.
  - R1 (D20, USD 20): about USD 5.1 used (P2-T02 pods).
  - R2 (D22/D24/D26, USD 60, notify 45): about USD 24.35 used (A3r1 about 11.30 and D19 13.05367).
  - D21 allows a network volume for reusable data; none has been created.
- **Upload route:** US data centres only. EU-SE-1 measured 47 KB/s from the owner PC; US measured 3–8 MB/s over 4 streams.
- `OPENROUTER_API_KEY` and `TYPHOON_API_KEY` are user environment variables. The RunPod SSH key is
  `~/.ssh/runpod_paper86_20261017`.
- **dr-train is back** (rebooted 24 Nov about 06:48). The partial build was deleted, Thai data copied and hashes verified,
  and the deferred P2-T02 CPU checks completed. Deeper retrieval adds zero at R@200 and the coverage-control fusion is
  unchanged at 0.4230 ([receipt](docs/tracking/owner-note-22112026/receipts/P2-T02_coverage_control_results.md)).
  Memory-safety rules: next-account handoff §2a.

### Decisions and unresolved items

[D1–D27](docs/maintenance/OWNER-DECISIONS-20261122.md) record owner authority. Historical resource balances describe completed work and require matching scope for any later use. The generic new download approval does not extend a paid envelope. Read [dr-train memory safety §2a](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md) before remote work.

The [original PDF source record](docs/evidence-scope/00-organization.md#original-source-corrections) resolves Paper 53's exposure denominator. Its DOI, independent semantic judgments for natural cases, source-by-source redistribution terms for new demos, real-user adoption and submission status remain open. Existing local-only owner material and private artifacts retain their access boundaries.
