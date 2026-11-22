# P0-T01 — State reconciliation (22 Nov 2026)

**Result:** COMPLETE · ENGINEERING_VERIFIED (a reconciliation; this is not a research result).

## Checkout

- Owner package audit pin: `3e5e2595d43df129d091c01dd4cd268f3b7b6c8d`.
- Actual HEAD at reconciliation: `ad7982d2a4d0702e3c13e29adf79423f4cf6dcf3`.
- **Divergence:** one commit, `ad7982d2`. It added the previous Thai phase tracker `docs/tracking/PTP-PHASE-TRACKER.md` (G01–G08
  numbering) and recorded the AFFiNE 0.27.4 desktop installation. That tracker is superseded by this live P0–P5 tracker
  and is kept only as history.
- Untracked and never committed: `docs/owner/` (owner input), `.claude/`, `uv.lock`, and one handoff file from 9 Nov.
- Two git stashes from 30 Oct 2026 are kept untouched.

## Instructions in force

- The order of authority is CLAUDE.md §3 standing rules, then AGENTS.md, then the owner decisions D1–D10
  (`docs/maintenance/OWNER-DECISIONS-20261122.md`), then owner-note-22112026 (N01–N12).
- The new package replaces the date-based G01–G08 roadmap with outcome-based phases P0–P5.
- Historical G-identifiers keep their meanings.
- **Name:** N01 keeps "Patent-to-Pilot". The owner's chat permission to rename the repository is therefore **not** used.

## Historical evidence (preserved, not rerun)

| Item | State | Evidence |
|---|---|---|
| G01 local vertical slice | COMPLETE (21 Nov) | `artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md` |
| G02 provider, ingestion and dataset contracts | COMPLETE (22 Nov). Add-ons on 22 Nov: PDF text-layer ingestion and OpenRouter templates | `artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md`, commit `1e190c4f` |
| G03 v1 support_frontier_v0 | PARKED | `docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md` §2–3 |
| G03 A1 field obligations | PARKED. Mask inconsistency disclosed; its direction is **not** established | memo §4a |
| G03 A2 learned selector | PARKED (VAL ALL +0.0017 [−0.0019, +0.0054]; IN lower bound −0.0060) | memo §4b, `g03-dev-results-a2.json` |
| A3r0 (LLM expansion) | FROZEN protocol and code. **Format smoke only:** 4 calls on 1 TRAIN query. **No effectiveness pilot has run; no DEV or VAL A3 score exists.** | `G03-DEV-AMENDMENT-3-20261122.md`, `g03-dev-a3-spend.json` |
| VAL exposure in G03 | Looked at 3 times (v1, A1, A2) | memo §4b |
| B53 Stage 1–2, B53.0 | Measured | `docs/writing/is2/results/`, `docs/healthtech/research/b53-0/` |
| PatenTEB overlap (D3) | Train split unreleased. The public-test overlap shows a shared family pool; it is not a training-data audit | `docs/healthtech/research/b53-0/PATENTEB-OVERLAP-AUDIT-20261122.md` |

## Spending and resource scope

- **Active envelope:** E1 = USD 8.00 nominal, stop-and-report at USD 6.00, 35,000 attempted requests (D9). Scope: G03 A3 and
  Workbench checks (≤ USD 0.20).
- **Spent under E1:** USD 0.00064223 across 4 requests (format smoke through the MCP tool). Workbench OpenRouter spend is
  USD 0.
- **OpenRouter account (read 22 Nov):** total credits 10, usage 1.63501153.
- **E1R** (USD 50 cumulative, notify at 40, 100,000 requests) is **PENDING owner approval**. It is not in force.
- **Not authorised:** RunPod/GPU rental; research model or dataset downloads without per-item approval.
- **Authorised for this package:** ordinary local AFFiNE installation/update and the runtime downloads it requires.
- **Credentials:** `OPENROUTER_API_KEY` is **not set** in the owner's Windows environment, so paid research is not ready.
- **dr-train:** V100 device 1 only, under the shared GPU lock. Nothing of this project is running there. The `g03-dev`
  phase was pulled and compressed (`artifacts/maintenance/20261122-g03-pull/SUMMARY.md`).

## Next

P0-T02/T03 (AFFiNE and the live tracker), P0-T04 (A3r1), P0-T05 (ledger) and P0-T06 (trace slice) run in parallel.
