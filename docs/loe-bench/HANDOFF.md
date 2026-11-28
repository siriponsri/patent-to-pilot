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
| Exploratory | SCORELLM: L1/L1e on C′ | Done. L1e 12.36% and L1 26.14% versus M3 66.85% at 24 m. USD 2.543; pod deleted |
| Exploratory | C9 GRPO/SFT: code, approved development projection (10,603 rows), frozen roster (256 rows) | **Blocked (C9TRAIN, 28 Nov).** No US Secure Cloud L4 was available, so no pod was created (USD 0). OSF update 3 lets training start now. Scheduled task 58a1b3e5 is disabled. Awaiting owner approval of a placement: L4 in an EU data center at the same rate, or a different GPU type with a deviation |
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
- RunPod GPU spend is about USD 3.51 of the USD 23 envelope (SCORELLM USD 2.543 done). C9 (≤ 4.5) is pending. Volume `8n6rnzljwg` costs USD 2.10 a month.
- Installed at user level for the desktop build: Rust 1.100.1 (GNU) with MinGW, plus Tauri CLI. Licences are in receipts/UIBUILD.md.
- The fonts are self-hosted under SIL OFL.
- External services: OSF (free) and a public GitHub repository.

## Next action (28 Nov, evening)

SCORELLM is merged and OSF update 3 is verified. TRACKA-CORE (CPU) and the Astra IS2 critique are running.

1. **C9 placement (resolved: owner approved EU L4; C9TRAIN2 dispatched on Sol high, `loe/C9TRAIN2`).** A live read at about 09:30 UTC showed Secure Cloud L4 available only at EU-RO-1 and EUR-IS-2, both USD 0.69/h. US Secure options were the RTX 4090 at USD 0.89/h (US-IL-1, US-NC-1) and the A100 SXM at USD 2.19/h. The planner recommends EU L4: the GPU type is unchanged, so the registration needs no new hardware deviation. Only the region changes; the earlier slow upload was from EU-SE-1, and the C9 upload is small. Owner approval is required before any pod is created.
2. **Track A.** TRACKA-CORE is merged (4ca5ce4d): 651 t0 forecasts per horizon, 130 expected slots per arm, private package with 12 hashed files, and no freeze yet. On the owner's decision, exploratory prior-method arms are added before the freeze. The co-planner is extracting the methods and metrics of Hu 2019, Hopefl 2025 and others, then the planner locks at most 3 arms. Then: an executor builds the arms (Sol xhigh), and the freeze card runs GPU predictions for L1, L1e and C9, the freeze manifest, the tag and the OSF update 4 sheet. The PIV archive has no fresh t0 edition, so 628 of 651 histories keep an UNKNOWN challenge state.
3. IS2: the Astra critique is applied (IS2AUDIT, 44feb00e), and the docx build tooling is in `docs/writing/is2/mwd/build/` (0b2df2a8). The first renders ran to 14 pages (EN) and 13 (TH) against the 10-page limit. IS2FIT (Sol high, `loe/IS2FIT`) is cutting the length. Then: the planner's final audit, the docx and PDF deliverables, and the IS2 slides (Claude).
4. Before v1.0: polish the product, sign the installer if a certificate becomes available, and remove the 3 duplicate images (DOCS2 inventory).
