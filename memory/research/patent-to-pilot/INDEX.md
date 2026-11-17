# Patent-to-Pilot shared project memory

## DIRECTION CHANGE 2026-11-17 (owner): Paper 1 -> BridgeRet. Read `docs/healthtech/research/plans/DIRECTION-20261117-BRIDGERET-HANDOFF.md` FIRST

The owner's new direction lives in `docs/owner/owner-note-17112026/` (owner-local, untracked).
- New Paper 1 = **P1-BridgeRet**: fine-tune Arctic-embed-m-v2.0 on USPTO OA 102/103 citations (TRAIN filing 2006-2009), RRF with BM25. Evaluated on P1-TEST = the reverse-hash tail of 2012 (n1 about 8-10k), on a fixed ~1M-document corpus. Primary endpoint: OUT Recall@200 (RPD).
- The old Paper 1 is now called **P1-DAPFAM** (closed, H1 INCONCLUSIVE).
- Paper 2 gains arms E0-P1 / E3-P1. Paper 3 is unchanged.
- Nothing is run yet. First step: ask the owner ONE decision package (O1-O10 + the R5 text downloads + the RunPod method + the proposals in the handoff note).
- The FINAL CHECKPOINT below stays valid for everything else.

## TAKEOVER STATE for any Claude account 2026-11-17T11:30+07:00 — FINAL CHECKPOINT (read this first)

This section supersedes every section below. The writer that produced it has stopped. Nothing is running: no S8 driver, no GPU or CPU jobs, no background tasks. A new account is the sole writer once it has checked `git log` and confirmed no other session is writing.

**1. Paper 1: test stage COMPLETE, evaluated ONCE (17 Nov 2026)**
- S8 generation finished: DRIVER_COMPLETE, FA/GR/SACR x 773 test queries. SACR had 765 used and 8 original-query fallbacks.
- Test retrieval: settled at gen 247. C1 = MOVEMENT_PRESENT for FA/GR/SACR. Reference = re-encoded anchors (frozen rule).
- Test evaluation (CPU, precharged 660 s, frozen at gen 249): `takeover-20261112/paper1-s8-eval/summary.json`. Accounting note: `paper1-s8-eval/SETTLEMENT-NOTE.json`. A mistaken settle_synthetic run failed before changing anything; the journal was verified at gen 249, IDLE.
- **Results (OUT R@200, n = 556):**
  - **H1 F-FA − B0 = −0.0135 [−0.0285, +0.0012] → INCONCLUSIVE.** H2 and H3 were not tested (the gate closed).
  - Harm check: F-FA on IN −0.0185 [−0.0235, −0.0138] and on ALL −0.0186 [−0.0233, −0.0143]. **Not non-inferior** at the 0.020 margin.
  - FA standalone −0.0527 [−0.0729, −0.0330].
  - F-GR −0.0045 and F-SACR −0.0021 versus B0, both with CIs spanning 0.
  - B0 OUT R@200 = 0.3296.
- Tables: `docs/healthtech/research/paper1-report/TEST-RESULT-TABLES.md` (renderer `render_paper1_test_report.py`).
- Manuscript: `docs/healthtech/research/PAPER1-MANUSCRIPT-DRAFT.md`. Status notes are at the top. **Keep conclusion branch C.** The placeholders are NOT filled yet; that is the next task.
- Totals after Paper 1: GPU charged 203,732.6 s, model_calls 5,269 (a lower bound), CPU remaining about 21.9 ks, journal gen 249, IDLE.
- **Never re-run any S8 job and never re-open the test qrels.** The test set is now exposed; it cannot select methods for Paper 2/3.

**2. Paper 2/3 plan v2 (PROPOSAL, not frozen):** `docs/healthtech/research/plans/PAPER-2-3-MERGED-PLAN-20261116.md`. It was revised after an owner-supplied external review.
- P2 pre-declaration draft: `docs/healthtech/research/plans/P2-OA-PREDECLARATION-DRAFT.md`.
- OA splits: `docs/healthtech/research/paper2-precheck/oa/OA-SPLITS.md`. DEV 2011 / P2-TEST 2012 / P3-TEST 2013, 378,109 eligible tasks. The open-population corpus needs 5.5-7.9M documents, about 175-250 V100-h fp32.
- Owner planning pack (untracked, owner-local): `docs/owner/`.

**3. Do-not-repeat ledger:** `docs/healthtech/research/paper2-precheck/README.md`. Every DAPFAM-dev acquisition pre-check so far is NO_GO.
- Quote the DAPFAM 13/9,480 OA figure only together with its mapping limits.

**4. Code merged to main on 17 Nov:**
- the acquisition harness with PatEx-style arms E0/E0-deep/E1/E2/E3 (CEDS) and a funnel evaluator, tested with doubles only (tests `test_acquisition_harness.py`, `test_patex_arms.py`, `test_ceds_arm.py`);
- product P0: gap audit `docs/healthtech/product/P0-P2-GAP-AUDIT.md`, 42 offline scenarios (41 pass, 1 recorded gap), P0 fixes not yet wired to the API/UI.
- Targeted tests pass, with 1 expected xfail.
- Known pre-existing failures: 8 SACR r2/r3 supervisor budget tests, which also fail on the old base.

**5. Leftover cleanup:**
- The local branches `claude/paper2-harness-0d504a` and `claude/prod-p0-evidence-bedc49` and the folders under `.claude/worktrees/` are locked by idle app sessions; their remote branches are already deleted. After the owner archives those sessions, run `git worktree prune` and `git branch -D` on the branches.
- The old Codex branches/worktrees (`codex/*`) are untouched on purpose.

**6. RunPod pilot (approved, hard cap USD 10):** the package and runbook are in `docs/healthtech/research/paper2-precheck/runpod/` (`RUNPOD-PILOT-RUNBOOK.md`).
- The owner's account holds USD 57; the pilot cap stays USD 10. Nothing has been rented.
- Pending owner choice: (a) the owner clicks in the console, or (b) the RunPod MCP via OAuth with per-action approval.

**7. Owner decisions still open:**
1. RunPod pod-creation method.
2. Full-encoding compute option and its USD cap (after the pilot).
3. R5 downloads: pre-grant text, PatEx-Gym 100 tasks, PatentsView continuity tables.
4. USD 100 OpenRouter sub-ledger and its first envelope.
5. Freeze of plan v2 + the P2 pre-declaration (now that S8 is reported).
6. A post-hoc DEV block 2006-2009?
7. ai-memory: the owner decided NOT to install it. Use the repo memory only.

**8. Standing rules:** report to the owner in Thai; pre-declare before computing; one settle per job; no LLM judge; no paid API or downloads without a recorded per-item approval; commit only your own files; keep `src/` clean while any frozen driver is running.

## Paper 2 pre-checks on DAPFAM dev: all NO_GO so far; read before proposing a new idea 2026-11-16T07:00+07:00

Ledger of everything already tested (do not repeat): docs/healthtech/research/paper2-precheck/README.md.
- BM25 + RRF with dense: NO_GO (OUT R@200 -0.020, IN -0.055), replicates the 5 Nov Stage 1 result.
- Fixed/per-section mixes of six actions (Stage 1, 5 Nov) and a citation-learned IPC class prior (6 Nov): NO_GO.
- Per-query oracle headroom +0.094 is real, but a label-free router (3 pre-declared variants) captures 0%: NO_GO.
- Still open: deeper pools (500-1,000) + reranker under matched budget; a new 102/103-labelled set from USPTO office actions (D1/D2 blocked by the USPTO.gov login; owner must sign in or download); harness prototype on branch claude/paper2-harness-0d504a (not merged).
- Owner approvals this round: owner-parallel-gpu-llm-approval.json (takeover dir), paper2-precheck/owner-reencode-approval.json, paper2-precheck/owner-oa-download-approval.json.
- Data already local (check before downloading): DAPFAM source parquets in methodology/datasets/research-only-nc/, family-ipc3 map and Stage 1 rankings in ../_private_artifacts/healthtech/ptp-org-adaptive-20261105/, PANORAMA PAR4PC/PI4PC, HUPD 2017 on dr-train.
- S8 continues independently (detached driver PID 13984).

## Latest terminal R6 and Graph v2 checkpoint

R6 calibration finished24 EOS calls but failed:23 contract-invalid and one valid semantic grading failure. Raw24/costs verified,1749 whole-stage GPU/fidelity seconds charged, journal generation1 reconciled. No automatic critic revision. Graph compact v2 CPU inspection completed100 admitted/14 technical risks among fixed114;14.728927 CPU seconds charged, no model or cards. Both jobs terminal. Prior running-state entries below are historical. See HANDOFF and audits ptp-r6-calibration-20261111 and ptp-sg-compact-v2-preparation-20261111. R7-SINGLE-CANDIDATE-CONTINUATION.md is proposed; owner decision pending, no new model authority or reservation. Preserve cumulative journal history; canonical CPU ledger advanced after the GPU snapshot and requires an explicit idle reconciliation before any future GPU declaration.


## Current calibration and Graph repair checkpoint

R6 critic calibration is live under the unchanged frozen job
`ptp-r6-calibration-20261111-v1`; outcome and whole-stage costs remain pending.
Phase0 final256 tests and authored pipeline evidence are complete. Graph R6's
33/114 technical input-risk closure remains historical evidence. A separate
lossless compact transport and CPU-only worker/controller passed29 authored
tests and are frozen locally, not staged. See
`docs/healthtech/audits/ptp-sg-compact-preparation-20261111/README.md` for exact
resource/terminal gates and pending200 conservative local CPU seconds. Do not
start the CPU job alongside calibration or reset the active dispatch journal.
Reports now distinguish current R6 status from earlier closed rounds; no new
semantic or retrieval improvement is claimed. Read HANDOFF for latest status.


## Latest R6 actual CPU pipeline qualification

Read HANDOFF for current writer and publication state. Native100 full profile/generic inputs passed (200 requests, zero risks). Actual Docker CPU-only authored pipeline passed through R6 worker, tokenizer, grammar/EOS, adapter, durable attempts, cohort and calibration scoring: 31 simulated backend invocations, 3649 checked tokens, 93.157 seconds. Entire output tree is SIMULATED; no real model/GPU calls. Seven CPU jobs terminal. Factorial composition reviewed; controller/global-ledger faults tested. Final Phase0 evidence binding and frozen calibration dispatch remain before GPU. Graph R6 remains closed at33 technical risks of114. Audit: docs/healthtech/audits/ptp-r6-phase0-execution-20261111.

## Current R6 preparation

Read HANDOFF and INDEX-PLAN first. R6 owner approved all three decisions and goal is ACTIVE; Phase0 engineering is in progress and model dispatch is not ready. See docs/healthtech/audits/ptp-r6-preparation-20261111/owner-approval.json. Latest:174 local tests and52 real CPU tokenizer/grammar cases PASS; native source282 join completed once. Graph R6 closed at33 technical input risks out of114, before model/retrieval/cards. SACR continues Phase0. See docs/healthtech/audits/ptp-r6-phase0-execution-20261111/. Canonical audit: docs/healthtech/audits/ptp-r6-preparation-20261111/. Exact proposed scope: docs/healthtech/research/plans/R6-BOUNDED-LONG-RUN.md. Prior entries below are historical; do not reuse their old approval or running-state text.

## R5 engineering qualification, 11 November 2026

R5 CPU engineering complete:86 local tests PASS; pinned character33+7numeric cases PASS; real tokenizer/callback/EOS35/35 PASS276.912s, exact original synthetic source1/1 PASS50.434s,input1557. Confirmed integer-bound omission and fused string-boundary token10465 omission; original R4 cause remainsUNKNOWN. Broad boundary adaptersv1/v2 stopped for cost and retained. Private bounded diagnostics preserve first failure and avoid normal-path GPU scalar copies; independent read-only review found no remaining blocker. All6ownedCPUcontainers terminal/PID0, no new model/GPU/fidelitygeneration/cards/retrieval. Graph integrity PASS100source families(86empty,29records),100alias units,215unique records; fullsource attachment code6fixturesPASS, corpus execution NOT_RUN. Cumulative GPU/fidelity charges unchanged; CPU costs in canonical audit ptp-r5-diagnosis-20261111/summary.json. Frozen smoke-proposal.json and R5-BOUNDED-LONG-RUN.md await combined goal/model/source/evaluator and bounded repair-policy approval; GPU192/fidelity64/fulldev128,60cards unchanged. Existing screened-publication permission retained, no duplicate approval requested; current changes local/uncommitted/unpushed, main/baseac48e02. Parent sole writer. Next: obtain2combined decisions; reserve/rebind ledger without method changes; dispatch one qualified smoke; proceed only through declared integrity/fidelity/human/resource gates. No native retry or test opening.


## R3 active objective takeover 2026-11-11T13:17:50.350124+07:00

New owner objective read and active: continue SACR + Graph research after the bounded R1/R2 closeout, preserving failures. Parent sole writer; base ac48e02. Current canonical audit: docs/healthtech/audits/ptp-r3-diagnosis-20261111/README.md. Confirmed retained R2 wrong span positions; implemented separate literal-evidence R3 compiler, no semantic acceptance. New/legacy token suites28PASS after correcting two authored fixture offset mistakes. No generation/census/database write/publication; tests closed; budgets unchanged. Current localhost7474 refuses connection and no Neo4j MCP tools exposed; prior connection result is historical. Next finish diagnosis, schema/semantic/full-pipeline fixtures and prospective census + matched posting-list control; inspect existing Neo4j, then present concrete combined approvals before costly runs. Goal ACTIVE; previous closeout below remains historical. Local changes are uncommitted; owner unrelated untracked handoff preserved.


## Publication verified and bounded goal closed

Report/code/evidence checkpoint 5fdd1cfa9e4a8c08897dabb56c2c9e28bf243a29 was pushed and verified against live origin/main on11 November2026. Final report review passed; exposure fixtures4PASS; staged diff/secret-pattern checks passed. Authorized bounded work is complete with negative method gates. No remaining experiment is dispatched. Only the unrelated owner document remains untracked. Preserve all failed configurations; future revisions require a separately defined next task.


## Bounded long-run closeout, 11 November2026

Current report: docs/healthtech/research/PAPER1-LONG-RUN-REPORT.md. Parent remains
sole writer. Prior verified pushed checkpoint5d406d7; this closeout awaits its
screened commit and final reviewer check. No running GPU job or pending cards.

B0 is the only measured retrieval arm: OUT Recall@200=0.14772 over349 queries.
SACR R1 stopped at21 flags above20; R2 single synthetic smoke failed source-backed
condition acceptance. S/G R1 and R2 each produced0 cross-family candidate pairs;
both closed. Pilot/full dev/MTM NOT_RUN because prerequisite gates failed.
Neo4j connection was verified, but no graph import was justified. No retry or
new configuration from remaining budget alone. Both tests remain CLOSED.

New CPU-only exposure aggregation of sealed prior dev metrics completed once:
ALL/IN/OUT unexposed at200=32/20/213; all9 recall aggregates match B0 receipt.
Whole wall0.575023457s,0GPU/model calls,1MiB disk reservation. GPU/fidelity charges
remain9006.484789591283/8727.597964742686s; remaining250193.51521040872/
20072.402035257313s. Known model calls at least59; two interrupted attempts
retain unknown counts. Human cards0/60; no semantic/independent-review pass.

Manuscript and literature supplement now report both negative rounds and the
Paper53-style coarse exposure. Direct published-score replication remains
NOT_ESTABLISHED. Bounded negative-outcome closeout is not proof of improvement,
a completed four-system comparison, test validation or submission readiness.
Paper2/3 and adaptive work remain plans only. Final read-only report review passed after correcting one broken evidence link.
No additional required experiment remains; screened publication verification is the
last closeout step. The reviewer did not independently inspect private data or GPU.
Any subsequent method revision requires a new explicit configuration/decision.
Preserve owner-untracked PATENT_TO_PILOT_RESEARCH_AND_CLAUDE_HANDOFF_2026-11-09.md.


Scope:`research/patent-to-pilot`. Updated:10 November 2026. These are project files readable by Codex and Claude, not shared private assistant memory, a memory server or experiment authority.

## Start here

1. [AGENTS](../../../AGENTS.md), [CLAUDE](../../../CLAUDE.md) and latest [HANDOFF](../../../HANDOFF.md): current writer, permissions, jobs and checkout verification.
2. [MASTER-PLAN](../../../MASTER-PLAN.md): DAPFAM first; optional MTM; conditional adaptive navigation; Scout separate.
3. [INDEX-PLAN](../../../INDEX-PLAN.md): exact reusable components, result classes, failure/NOT_RUN state and evidence links.
4. [DECISIONS](DECISIONS.md), [OPEN-QUESTIONS](OPEN-QUESTIONS.md), [SESSION-LOG](SESSION-LOG.md): durable choices, unresolved items and audit pointers.
5. Only the selected study's detailed plan and original receipts. Do not load protected labels or private session history for convenience.

## Keep memory useful

Update INDEX-PLAN on every substantive work event; update paired HANDOFF/CLAUDE checkpoints before long/background work, every 30 minutes active and at pause/end. Record decisions/questions/logs when relevant. Preserve original evidence and failed outcomes. Update progress/next-actions once per completed package. Current exact authorization controls commit/push; no automatic publication.

Use stable links/hashes instead of copying source text or dynamic counters. Mark unverified/stale facts and NOT_RUN explicitly. One active writer. No secrets, protected test material, private model journals, cross-project profiles or account/session capture.

Design/limits: [shared-memory assessment](../../../docs/healthtech/research/plans/SHARED-MEMORY-DESIGN.md). Archive routing: [archive index](../../../archives/INDEX.md).
