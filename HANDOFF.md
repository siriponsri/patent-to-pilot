# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 25 Nov 2026 (Asia/Bangkok)

**Option A resumed through 04:00 Thai time on 26 Nov 2026.** The Executor integrated the fresh packet from `ea150deb` and Windows S4 changes from `2989cdb9` with their recorded authorship. Packet structure and disjointness checks pass. S4 closes as local Windows alpha and local public-data demo READY_FOR_REVIEW. [Integrated QA](docs/evidence-scope/receipts/S4-integrated-verification.md) confirms launcher, restore, retained-source rebuild and 19 original hashes. Final full pytest on the integrated candidate had 2,795 passed and only the eight standing SACR failures. The earlier path-length failure is retained. No QA job is still running.

**Prospective checkpoint.** The Planner rejected v1 because the ablation changed the option set and the primary comparison used unequal ties. The retained [v2 protocol](docs/evidence-scope/alternative-evidence/PROTOCOL.md) corrects both. [Fixture v3](docs/evidence-scope/alternative-evidence/fixture-checks.json) validates 30 arm traces and independent worktree audit verified parity. The [v2 lock](docs/evidence-scope/alternative-evidence/freeze.json) SHA-256 is `518b22b70bf9edf9bd0070b0ff6ee171764e45efaacbe2e756473ed1796e3dd4`. Next, obtain explicit release for the exact published revision and then create the one canonical original. Held execution is still NOT_RUN. The local original uses zero model tokens. Separate ancillary OpenRouter and dr-train authority is in the [resource ledger](docs/evidence-scope/alternative-evidence/RESOURCE-LEDGER.md). No paid booking, remote job, public deployment, credential access or protected TEST access entered this checkpoint.

**S0, S1 and S2 complete.** Under D28 the owner extended this goal from planning to implementation. [S1 receipt](docs/evidence-scope/receipts/S1-20261125.md) pins 100 authored requests in ten families, runtime/evaluator separation, a three-state primary and matched controls. There are only three reserved DEV families per language. No method score was computed. [S2 receipt](docs/evidence-scope/receipts/S2-workbench.md) records a Thai-first local reader with 23 public-source presets from ten display-only families, including pharmaceutical formulations, devices and five Thai legal families. Browser and HTTP workflows reopen exact cited spans. Product demonstrations and research families are disjoint.

**S3 complete, NEGATIVE on Thai controlled DEV.** The frozen scope controller had 3/27 correct against 6/27 for the budget-matched coverage control. Equal-state paired change −11.11 pp, unstable family-cluster 95% interval [−33.33, 0.00]. All three losses were displaced cases in one family, with no improvements. English transfer was uninformative with 0/27 correct and 30/30 abstentions in both primary arms. Both arms correctly abstained on all three finite probes in each language. Park the tested method and retain the evidence. The [execution receipt](docs/healthtech/audits/S3-20261125/RESULTS.md) and [machine result](docs/healthtech/audits/S3-20261125/results.json) include costs, exact counts and hashes. The Planner/Auditor verified the preregistration and independently validated and rescored all 300 original traces. The canonical private captures and seal are at `../_private_artifacts/ptp-s3-20261125/`.

The [prospective v2 commit](docs/healthtech/audits/S3-20261125/PREREGISTRATION.md) was published at `e42b6254` before DEV. The v1 metering correction happened before any reserved DEV access. Final targeted verification passed 21 checks. Repository-wide pytest started before the correction and ended with only the eight standing SACR budget errors. The [bridge](docs/healthtech/audits/S3-20261125/BRIDGE.md) preserves historical P2-T04 NO_GAIN and documents all eight IS1 depth slots NOT_RUN. No project jobs or paid bookings remain. S4 awaits a separate dispatch. S5 can use this bounded research result.

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

[D1–D28](docs/maintenance/OWNER-DECISIONS-20261122.md) record owner authority. Historical resource balances describe completed work and require matching scope for any later use. The generic new download approval does not extend a paid envelope. Read [dr-train memory safety §2a](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md) before remote work.

The [original PDF source record](docs/evidence-scope/00-organization.md#original-source-corrections) resolves Paper 53's exposure denominator. Its DOI, independent semantic judgments for natural cases, reuse rights for future additions beyond the S2 manifest, real-user adoption and submission status remain open. Existing local-only owner material and private artifacts retain their access boundaries.
