# Patent-to-Pilot handoff

This file holds the **current state only**. Rewrite the "Agent takeover state" section in place at every major event (see
rule 7 in [CLAUDE.md](CLAUDE.md)). Older checkpoints are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## Agent takeover state — 22 Nov 2026 evening (Asia/Bangkok)

**Plan.** Outcome-based phases **P0–P5** (owner note 22 Nov, `docs/owner/owner-note-22112026/`, owner-local).
- Live board: [docs/tracking/owner-note-22112026/PHASE_BOARD.md](docs/tracking/owner-note-22112026/PHASE_BOARD.md).
- Registry: `goal_registry.json`.
- Tool: `python scripts/tracking/ptp_tracker.py show|set|render`.
- No calendar gates.
- Status fields kept separate: `method_evidence` = not yet demonstrated; `product_readiness` = core verified, structural slice
  in progress; `publication_readiness` = planned, unmeasured.

**New account?** [docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md)
(to be refreshed for P0–P5), then [AGENT-LESSONS.md](docs/maintenance/AGENT-LESSONS.md).

### P0 status (details and receipts in the board)

| Task | Status | Note |
|---|---|---|
| P0-T01 reconcile state and authority | COMPLETE | [receipt](docs/tracking/owner-note-22112026/receipts/P0-T01_state_reconciliation.md). HEAD was pin `3e5e2595` + 1 commit; no A3 effectiveness exposure |
| P0-T02 AFFiNE install | PARTIAL | Upstream v0.27.4 self-host pinned by digest at `C:\Users\User\ptp-tools\affine-tracker` (http://127.0.0.1:3010); the owner created the admin account; backup/restore drill pending. [receipt](docs/tracking/owner-note-22112026/receipts/P0-T02_affine_setup.md) |
| P0-T03 live tracker + AFFiNE mirror | PARTIAL | The local tracker is live (35 tasks). Workspace `Patent-to-Pilot — Research and Product` (id `15d6fa22-…`) exists on the server, but the web client never pushes docs (server `snapshots`/`updates` = 0). The socket join and HTTP work; load-doc returns DOC_NOT_FOUND. Claude in Chrome was not connected. The owner reported doing an import, but nothing reached the server DB. **SYNC_PENDING** |
| P0-T04 A3r1 protocol + provider plan | COMPLETE | [amendment (PROPOSED)](docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3R1-PROPOSED.md). A3r1 does **not** fit E1 and fits E1R. Typhoon is not on OpenRouter (own key) |
| P0-T05 shared budget ledger | IN_PROGRESS | Background agent (ledger module, the A3 caller, the Workbench providers) |
| P0-T06 source-bound trace slice | IN_PROGRESS | Background agent (`src/patent_to_pilot/workbench/`) |
| P0-T07 readiness milestones | NOT_STARTED | After T05/T06 |
| P5-T01 manuscript draft | COMPLETE | [MANUSCRIPT-DRAFT-v1.md](docs/writing/journal/MANUSCRIPT-DRAFT-v1.md), all results NOT_RUN |

### Research record (preserved)

- G03 v1, A1 and A2 are PARKED ([memo](docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md); corrections added 22 Nov).
- A3r0: format smoke only (USD 0.00064).
- B53 Stage 1–2 and B53.0 are measured.
- PatEmbed on DAPFAM: shared family pool; training overlap unmeasured.
- Writing corrections W1–W6: [register](docs/maintenance/WRITING-CORRECTIONS-20261122.md).

### Money and access

- **E1 is active:** USD 8 / 35,000 requests, stop at USD 6.
- **E1R** (USD 50) is **pending the owner**.
- `OPENROUTER_API_KEY` is not set.
- The OpenRouter balance is about USD 8.365, so a top-up is needed before any A3r1 Stage B.
- Typhoon needs `TYPHOON_API_KEY` and a quota answer.
- RunPod: no envelope.

### Running jobs

- Two background agents (P0-T05 ledger, P0-T06 trace slice), resumed after the usage-limit reset.
- AFFiNE Docker stack (`docker compose -p ptp-affine-tracker`) running.
- Nothing of this project runs on dr-train.

### Next

1. Integrate and verify T05/T06, then run the full test gate and P0-T07 readiness.
2. AFFiNE: find why the client does not push docs (or use the owner's browser or desktop path), then mirror, read back,
   back up and run a restore drill.
3. Free P2/P4 tasks (P2-T01 content audit, P2-T03 relation search, P4-T01 Search/Compare/Inspect) by dependency.
4. Ask the owner once: E1R, Typhoon key, OpenRouter key and top-up.

### Owner decisions

- D1–D10: [OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md).
- N01–N12: in the owner note. N01 keeps the name, so the repo rename permission is not used.
- Pending:
  - E1R;
  - Typhoon access;
  - the API key;
  - the PatenTEB option;
  - RunPod caps;
  - the Paper 53 DOI and the 37.1% denominator;
  - the G01 launcher check.

Unchanged:
- large derived files on dr-train are kept (compressed);
- the two git stashes from 30 Oct 2026 are kept.
