# Patent-to-Pilot shared project memory

## TAKEOVER STATE for any Claude account 2026-11-16T17:30+07:00 (read this first)

This section supersedes the sections below for the current state. Parent writer = the session that started the jobs below. A new account becomes sole writer only after checking that no other session is writing (Claude desktop sidebar / `git log`). Never start a second S8 driver.

**1. Paper 1 S8 (frozen test stage), running unattended**
- A detached driver (Windows process PID 13984, started with Start-Process) runs `takeover-20261112/drive_paper1_s8.py`. FA b1-b5 and GR b1-b5 are settled. SACR b1 is settled (gen 217: 76 used, 3 fallback). SACR b2 was launched at gen 219; SACR b3-b10 remain. About 2.1 h per SACR batch; generation ends around 10:00-11:00 on 17 Nov.
- Progress log: `takeover-20261112/paper1-s8-progress.jsonl`. The driver commits and pushes after every freeze and settle.
- **Check the driver is alive:** `tasklist /FI "PID eq 13984"`.
- **If the driver is dead:** read the last event. If it is LAUNCHED without SETTLED, do NOT start the job again. Observe it with `python takeover-20261112/native_control.py observe paper1-s8-<arm>-b<n>`. Settle ONCE with `python takeover-20261112/settle_synthetic.py <job> paper1-s8-<arm>-b<n>`. Append TERMINAL and SETTLED lines to the progress log, commit, then restart the driver DETACHED (PowerShell Start-Process) with the remaining items only.
- **After SACR b10 settles:**
  1. Run `takeover-20261112/freeze_paper1_s8_retrieval.py`, start the job with `native_control.py start`, observe, then settle once.
  2. Check C1: MOVEMENT_PRESENT for FA, GR and SACR.
  3. Run `takeover-20261112/freeze_paper1_s8_eval.py`. It opens the sealed test qrels ONCE. Start the CPU evaluation and settle once.
  4. Render the report with `python docs/healthtech/research/paper1-report/render_paper1_test_report.py <summary.json>`. Fill the matching conclusion branch in `docs/healthtech/research/PAPER1-MANUSCRIPT-DRAFT.md`.
  5. Write the Thai owner report.
- `package()` refuses uncommitted changes under main's `src/` and `scripts/healthtech`. Keep them clean. **Do not merge branches that touch `src/` or `scripts/healthtech` into main until the last S8 freeze (the evaluation job) is done.**

**2. Paper 2/3 plan v2 (proposal, NOT frozen):** `docs/healthtech/research/plans/PAPER-2-3-MERGED-PLAN-20261116.md`. It is revised after an owner-supplied external review.
- Paper 2: an OA-derived cross-domain benchmark plus a new search method E3 (claim-element deficit-aware search).
- Paper 3: stage-specific harness evolution, gated on integrity only.
- The plan is frozen only after the owner sees the S8 result. Owner planning pack (untracked): `docs/owner/`.

**3. Do-not-repeat ledger:** `docs/healthtech/research/paper2-precheck/README.md`. Every DAPFAM-dev acquisition pre-check so far is NO_GO.
- OA data (USPTO OA Research Dataset 2017 + PatentsView) is downloaded and hash-verified at remote `/data/ptp-paper2/` and local `data/raw/uspto/`.
- Census: `paper2-precheck/OA-DATA-FEASIBILITY.md` section 9. When quoting the DAPFAM 13/9,480 figure, give it only together with its mapping limits.

**4. Parallel sessions and branches (merge when done; delete after merge, as the owner allows):**

| Session | Branch | State | Merge rule |
|---|---|---|---|
| p2-oa-splits | `claude/p2-oa-splits-6f1f87` | R1 split run in progress on the remote; R2 v2 pre-declaration draft written | docs only: merge when done |
| p2-harness | `claude/paper2-harness-0d504a` | Harness + E0/E0-deep/E1/E2/E3 + funnel evaluator, 78 tests PASS, doubles only | touches `src/`: merge only after S8 evaluation |
| prod-p0 | `claude/prod-p0-evidence-bedc49` | Product P0 audit, scenarios and fixes in progress | touches `src/`: merge only after S8 evaluation |
| p1-report-scaffold | merged (cd38e17), branch deleted | done | n/a |

The folder `.claude/worktrees/p1-report-scaffold-f29529` is a leftover locked directory; delete it later.

**5. Owner approvals on record:**
- `owner-parallel-gpu-llm-approval.json` (takeover dir);
- `paper2-precheck/owner-reencode-approval.json`;
- `paper2-precheck/owner-oa-download-approval.json`.

Still needs the owner:
- R5: download pre-grant text and the PatEx-Gym 100 tasks;
- R6: GPU choice for a corpus-encoding speed test (the shared RTX 2080 Ti, or RunPod);
- the USD 100 OpenRouter sub-ledger and its first envelope;
- the plan v2 freeze.

**6. Standing rules:** no paid API without the per-dispatch approval above; never read DAPFAM test data except through the single frozen S8 evaluation; no LLM judge; pre-declare before computing; one settle per job; report to the owner in Thai.

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
