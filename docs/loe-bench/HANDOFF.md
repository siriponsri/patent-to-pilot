# LOE-Bench lane handoff

Owner of this file: the main planner (Claude Opus). Branch: `research/loe-bench`, with its local worktree at `../_worktrees/ptp-loe-bench`; `main` is kept equal to it at each integration. Plan and board: [PLAN.md](PLAN.md). Memory: [MEMORY.md](MEMORY.md). Techniques: [TECHNIQUE-LEDGER.md](TECHNIQUE-LEDGER.md). Documentation index: [README.md](README.md).

## Current state (28 November 2026, afternoon, D41 accelerated plan)

**Product.** Market Window Dossier (working name): a pre-development launch-window forecast plus an FTO hand-off dossier. LOE-Bench is its benchmark.

**Roles.**
- Claude Opus: main planner and only reviewer; also figures, slides, applications and product UI.
- GPT-6.2 Astra high: co-planner.
- GPT-6.2 Sol: executors (xhigh or high).
- Writing drafter: Gemini 4 Hydrogen xhigh, with Sol high substituting until the Antigravity quota resets around 5 Dec.

**Phases (target 15 Dec 2026).**

| Phase | Item | State |
|---|---|---|
| Pre-OSF | C2 L1e, C3/C3b crowding, C4/C4b Medicaid, C9 spec | Done, merged |
| Pre-OSF | Preregistration v2 and audited OSF package | Done (audited commit 52908944) |
| Registration | OSF p2smd, doi:10.17605/OSF.IO/P2SMD | Registered 03:59 UTC. Update 1 (lock wording) 05:00 and update 2 (C9 timing) 05:10 are approved and co-planner verified |
| Release | PREREG_LOCK 3f911452… (canonical original record, `scripts/osf_lock.py`) | Done |
| Release | C′ gate (custodian) | PASS |
| Confirmatory | SCORE: H1–H3, secondary, C3, C4 | Done. See "Results" |
| Exploratory | SCORELLM: L1/L1e on C′ (RunPod, ≤ USD 3) | Running |
| Exploratory | C9 GRPO/SFT: code, approved development projection (10,603 rows), frozen roster (256 rows) | Ready. Training is scheduled for 1 Dec 2026 00:15 UTC (scheduled task 58a1b3e5) on an L4 in US-MO-2 at USD 0.69/h, all-in cap about USD 4.5 |
| Track A | Retrain on matured windows and freeze (hash, tag, OSF timestamp) | Not started. Runs after C9 trains, around 2–6 Dec, and before 2027-01-31 |
| Product | PRD1 builder (32 dossiers, C8 audit 1,789/1,789), EVP (C6 3/5 documented restrictions; C7 17/17 family leads, 0/6 Thai statuses verified) | Done |
| Product | UIBUILD: F2 web app, landing page, Tauri desktop installer (unsigned) | Done. Installer at `_private_artifacts/mwd-desktop/` |
| IS2 | TH/EN drafts with the C′ results and Figures 1–2 | Drafted. Next: SCORELLM result, Astra critique, main-planner audit, KMITL docx, slides |
| Release | v1.0 (GitHub release, optional Zenodo DOI) | Not started (8–15 Dec) |

**Results.**
- **Confirmatory (C′, no deviation).**
  - H1 M3−B1 at 24 m: +20.37 pp [+14.37, +26.16], PASS; meets the +10 threshold.
  - H2 M3−M1 at 24 m: +1.36 pp [−2.20, +3.01], FAIL; the fixed sequence stops here.
  - H3 M3−B1 at 12 m: +16.69 pp [+9.98, +24.21], descriptive only.
  - The dated evidence carries the gain; the graph's added value is not confirmed.
- **Exploratory C′.**
  - C3 crowding: +30.11 pp [+20.16, +36.86].
  - C4: NOT_RUN.
  - Auto-clear safety failed.
- **Development.**
  - FREEZE: H1 +9.80, H2 +5.49, H3 +13.00 pp.
  - L1e was below L1, M3 and B1.
  - C3b: +25.60 pp at one cutoff.
  - C4b: the erosion factor worsened MAE.

**Resources.**
- RunPod GPU spend is about USD 0.97 of the USD 20 envelope. SCORELLM (≤ 3) and C9 (≤ 4.5) are pending. Volume `8n6rnzljwg` costs USD 2.10 a month.
- Installed at user level for the desktop build: Rust 1.100.1 (GNU) with MinGW, plus Tauri CLI. Licences are in receipts/UIBUILD.md.
- The fonts are self-hosted under SIL OFL.
- External services: OSF (free) and a public GitHub repository.

## Next action (owner returns 4 PM, 28 Nov)

1. Merge SCORELLM when it finishes and fill the IS2 placeholder.
2. Send IS2 to Astra for critique, then do the main-planner audit, build the KMITL docx (TH/EN) and make the slides (Claude).
3. On 1 Dec, dispatch C9 training. After it finishes, dispatch the Track A freeze card.
4. Before v1.0: polish the product, sign the installer if a certificate becomes available, and remove the 3 duplicate images (DOCS2 inventory).
