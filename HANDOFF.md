# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 23 Nov 2026 (Asia/Bangkok)

**Plan.** Outcome-based **P0–P5** (owner note 22 Nov). Live board:
[docs/tracking/owner-note-22112026/PHASE_BOARD.md](docs/tracking/owner-note-22112026/PHASE_BOARD.md).
- Tool: `python scripts/tracking/ptp_tracker.py show|set|render`.
- Status fields kept separate: `method_evidence` = NOT_YET_DEMONSTRATED; `product_readiness` = core verified plus synthetic
  trace slice; `publication_readiness` = draft with results NOT_RUN.

### Where things stand

**P0 complete except AFFiNE.**
- OFFLINE_READY.
- PAID_RESEARCH_READY since 23 Nov.
- AFFINE_READY is **blocked**:
  - the 0.27.4 web client never opens its sync socket (server verified fine);
  - the built-in MCP is read-only;
  - the owner imported a snapshot into AFFiNE Desktop (local workspace);
  - the repo board is the tracker of record ([P0-T02 receipt](docs/tracking/owner-note-22112026/receipts/P0-T02_affine_setup.md)).

**P1 (A3r1).**
- **P1-T01:** done. Keys present by presence check; E1R approved in the ledger (D11).
- **P1-T02:** TRAIN calibration done. 128/128 complete, no truncation, no reasoning tokens, USD 0.0152.
- **P1-T03:** **FROZEN** ([freeze receipt](docs/tracking/owner-note-22112026/receipts/P1-T03_freeze_receipt.json),
  commit 8c4c23f1).
  - Stage-B-eligible: Qwen3-32B, DeepSeek V4 Flash, Gemini 2.5 Flash-Lite. Bound totals USD 17.8–21.0, within the USD 50
    limit.
  - Typhoon2.5 is pilot-descriptive only (quota unconfirmed).
- **P1-T04 is RUNNING:** pilot generation, 2,000 P1-DEV queries × 4 models.
  - Runs on the owner PC under the E1R ledger (`../_private_artifacts/g03-a3r1/ledger/A3r1/<model>/P1-DEV.jsonl`).
  - Then upload the ledgers to dr-train `g03-dev/a3r1/ledger/`, copy `g03_a3_routes.py`, `g03_a3_decide.py` and
    `g03_queue_a3r1_pilot.sh` to `g03-dev/code/`, and run the queue detached (ends `G03_A3R1_PILOT_DONE`). It needs the
    V100 lock; check that the P2-T02 GPU job is not holding it.
  - Apply the frozen GO rule. Stage B only on GO.

**P2.**
- T01 content audit: done. The index holds title + abstract + first claim only, about 12% of claim tokens.
- T02 coverage control: protocol frozen (bd30d3f7). An agent is implementing it and launching a detached Arctic C1/C2
  build on the dr-train V100 under `/data/ptp-paper2/p2-coverage/`.
- T03 relation-search operator: done (32bb87d2). Its policy is to be frozen in the P2-T04 protocol.

**P3.** T01 Thai data contract done (fd3cae1a). Downloads and the NitiBench+ gate need per-item owner approval.

**P4.** T01 Search/Compare/Inspect: an agent is working on it (uncommitted changes in `workbench/core.py`, `server.py`,
`static/*` and `workflow.py` are its work).

**P5.** T01 manuscript draft done.

### Money and access

- **E1R active:** USD 50 cumulative, notify at USD 40, 100,000 requests (D11).
- Committed before the pilot: USD 0.0159.
- OpenRouter credits: total 20.
- `OPENROUTER_API_KEY` and `TYPHOON_API_KEY` are set as user environment variables.
- Typhoon is settled at USD 0 (D12).
- **RunPod envelope R1 (D20): USD 20 for P2-T02**, stop and report at USD 15; prepaid balance USD 37.21; **no network
  volume** (owner): pod disk only, deleted with the pod. No pod exists yet. PatentsView sources are local in `data/raw/uspto/` (17 GB; no re-download needed). The C0 runs,
  `ser-arctic-v1`, `texts-v1/corpus.jsonl` and `tasks.tsv` exist only on dr-train, so the RunPod run starts after the reset.

### Running jobs and incident (23 Nov, evening)

- **P2-T02 runs on RunPod, second attempt** ([amendment A1 §7](docs/healthtech/research/p2-coverage/P2-T02-AMENDMENT-A1-RUNPOD.md)).
  The first pod (EU-SE-1) was deleted because the upload route to Sweden was about 47 KB/s.
  - Pod `jd41r4cvv171q6` (`ptp-p2t02-a1b`): RTX PRO 4500 Blackwell, US-KS-2, 94 GB RAM, 13.6 CPUs, no volume, USD 0.72/h,
    started 12:42 UTC. SSH: `ssh -i ~/.ssh/runpod_paper86_20261017 -p 14876 root@216.81.151.69`.
    Log: `/data/ptp-paper2/runpod.log`.
  - C0 is rebuilt on the pod and must pass the rebuild gate before C1/C2 count. Gate A already holds locally
    (corpus text byte-identical after CRLF→LF).
  - Stop at USD 15 (watcher deadline 2026-11-24 08:30 UTC). On finish: pull results to
    `../_private_artifacts/p2t02-runpod/`, write the receipt, delete the pod, read billing.
- **dr-train:** rebooted by the admin in the evening of 23 Nov, but it stays unreachable (Tailscale online through relay
  "sin", no ping, SSH times out). The chain script `scripts/research/drtrain_chain_20261123.sh` (A3r1 evaluation)
  and the upload bundle `../_private_artifacts/drtrain-upload-20261123.tgz` are ready. Do **not** run P2-T02 there
  while the RunPod run is live.
- **A3r1 pilot generation is complete** (7,999/8,000 usable; E1R committed USD 0.785). Route building, evaluation and
  GO/STOP wait for dr-train ([receipt](docs/tracking/owner-note-22112026/receipts/P1-T04_pilot_generation.md)).
  Stage B is automatic on GO (D16).
- **Thai data** is downloaded and verified locally (`../_private_artifacts/thai-data/`); the dr-train copy is pending.
- AFFiNE Docker stack: tracker only.

### Owner decisions

- D1–D14: [OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md).
- N01–N12: in the owner note. N01 keeps the name.
- Pending:
  - Thai dataset download approvals (P3-T02);
  - whether to report LLM-judge-graded NitiBench scores (rule 12);
  - the Paper 53 DOI and the 37.1% denominator;
  - the G01 launcher check;

Unchanged:
- large derived files on dr-train are kept (compressed);
- the two git stashes from 30 Oct 2026 are kept.
