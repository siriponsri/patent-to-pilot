# LOE-Bench lane handoff

Owner of this file: the main planner (Claude Opus). Branch: `research/loe-bench`, with its local worktree at `../_worktrees/ptp-loe-bench`; `main` is kept equal to it at each integration. Plan and board: [PLAN.md](PLAN.md). Memory: [MEMORY.md](MEMORY.md). Techniques: [TECHNIQUE-LEDGER.md](TECHNIQUE-LEDGER.md). Documentation index: [README.md](README.md).

## Orchestrator resume point (read first when switching accounts)

The owner runs the orchestrator on two Claude accounts. Per-account chat memory is not shared, so this section and [MEMORY.md](MEMORY.md) are the main memory. Update both, then commit and push, after every step (owner rule, 28 Nov 2026, night).

Last update: 28 Nov 2026, 23:50 Bangkok time (system clock). The orchestrator plans and reviews only; executors do hands-on work (owner, 28 Nov). **Focus (owner, 28 Nov): close every research result beyond reviewer doubt (main planner and co-planner review); product and writing paused. Then IS2 revision, then journals.**

| Line | State | Next action |
|---|---|---|
| IS2 short paper | IS2LAYOUT merged (a2cc45c1): figures and Table 1 next to first mention, 9 pages TH/EN, 0 orphans. Gap on pages 1–2 is the KMITL template (abstract pages with pinned footnotes). IS2REF merged (87a9ef4d). Reviewed files delivered to `IS_2_new/01_short-paper/final` (hashes match the IS2LAYOUT receipt); the earlier copies are in `archive/2026-11-28_pre-layout` | Owner reads it; slides wait for that |
| Slides | Folder structure only | Wait for the owner's reading |
| Journals (STA conditional, JAMIA) | JAMIA v2.1 outside Git with Figures 1–2 (JAMIAFIG merged; figures reviewed; 3,771 words incl. tables and captions; 12 pages in LibreOffice). PSA and MDM dropped | **PAUSED (owner, 28 Nov).** Resume after the research close-out: IS2 revision first, then journals. Owner items kept: degree, ORCIDs, corresponding author, OSF contributor, STA enquiry |
| Product | Merged: PO-CURRENT (1ff2db22), PO-LANDING (1ae7f500), BE-GATEWAY B1 (4922cc83), BE-MCP B5 (aa6865b9), PO-PDF (02e432e5; one print layout, 64/64 parity, Semaglutide TH 59→30 pages; 39 tests rerun). B5 follow-ups: ROW_TOO_LARGE on 10 oversized records, first-call CPU vs Workers Free 10 ms, remote clients NOT_RUN until the owner deploys | **PAUSED by the owner (28 Nov).** PO-WOW, B2 and B3 were cancelled before any push; resume from the PRD card list after the research line is complete. Known blocker to fix on resume: historical References-tab reveal leak |
| Research close-out | **OPEN: final closure waits for the external review** (owner decision 21:46: the co-planner acts as external reviewer until NO REMAINING DOUBT). The joint sign-off at `0a5ff7f5` is a completed **milestone** for historical results, archive and records ([JOINT-SIGNOFF](JOINT-SIGNOFF.md), [checklist](RESEARCH-COMPLETION.md)). Zenodo 10.5281/zenodo.24629100 restored independently. Power expansion: POWER-SIM merged (7e068c99, PASS WITH LIMITATIONS; filing gate unmet, any filing returns to the owner). JURIS-COUNT merged (a088e612). **Jurisdiction: US-only** on the sufficient ground that no jurisdiction passes M3; materiality is undecided (fixed-calendar gain is a ceiling effect, the earlier-readout route was not simulated) and no further simulation is needed ([decision](JURISDICTION-DECISION-RULE.md)). External review: R1 DOUBTS REMAIN (answered, [responses](reviews/EXTREV-RESPONSES.md)); R2 (22:54) DOUBTS REMAIN: R4–R6 resolved, R1–R3 partial, new N1 blocking (H3 estimate depends on how the readout is invoked), N2 and N3 major. | Planner fixed the R1/R2 wording; TRACKA-READOUT3 merged (23:12) fixing N1–N3; EXTREV-R3 (23:19): DOUBTS REMAIN (R3-A blocking: caller-chosen FDA snapshot can flip formal H1; R3-B major); TRACKA-READOUT4 merged 23:38, EXTREV-R4 (23:50): DOUBTS REMAIN (R4-A blocking: first-publication input can still change on retry or late run; R4-B provenance; R4-C legacy policy computable; R4-D Zenodo README). TRACKA-READOUT5 dispatched 23:50 (blind capture, Sigstore attestations, legacy policy, Zenodo clarification text for the owner); EXTREV-R4 was dispatched 23:38; IS2-DELTA merged (28 planned IS2 changes, docs/writing/is2/IS2-REVISION-DELTA.md); READOUT4 was dispatched 23:19; EXTREV-R3 was dispatched 23:12. Close only at NO REMAINING DOUBT, then revise IS2 (drafter, Astra critique, planner audit; KMITL template; no orphan words). **Overnight mandate (owner, 22:53):** work autonomously until 06:00; owner-only items go into the 05:45 brief (scheduled), heartbeat 02:00. **Owner pre-approval (22:56):** GPU if needed, USD 20 ceiling (quote rate and scope before each pod, delete after), and any edits or actions needed for the close and IS2. Still outside: OSF filing, paid LLM APIs, journals, the frozen package. Owner: deploy the readout automation before 27 Nov 2027 |
| Integration | `main` equals `research/loe-bench` at 23af56eb | Fast-forward main after each merge |

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

1. **C9 trained (C9TRAIN2, merged).** SFT and GRPO each ran 64/64 updates on one L4 in EU-RO-1. Estimated spend was USD 0.218, pod `kwo2osyic0u3ts` was deleted at 09:45:15 UTC, and 33 files were hash-verified. SFT loss fell to 0.007 and GRPO logged 103 malformed rollouts out of 1,024 under the frozen reward rule. The adapters are private in `results/trained/`, and predictions belong to the freeze card. RunPod spend is now about USD 3.73 of 23. *Earlier placement note:* A live read at about 09:30 UTC showed Secure Cloud L4 available only at EU-RO-1 and EUR-IS-2, both USD 0.69/h. US Secure options were the RTX 4090 at USD 0.89/h (US-IL-1, US-NC-1) and the A100 SXM at USD 2.19/h. The planner recommends EU L4: the GPU type is unchanged, so the registration needs no new hardware deviation. Only the region changes; the earlier slow upload was from EU-SE-1, and the C9 upload is small. Owner approval is required before any pod is created.
2. **Track A.** TRACKA-CORE is merged (4ca5ce4d): 651 t0 forecasts per horizon, 130 expected slots per arm, private package with 12 hashed files, and no freeze yet. On the owner's decision, exploratory prior-method arms are added before the freeze. The co-planner is extracting the methods and metrics of Hu 2019, Hopefl 2025 and others, then the planner locks at most 3 arms. Then: an executor builds the arms (Sol xhigh), and the freeze card runs GPU predictions for L1, L1e and C9, the freeze manifest, the tag and the OSF update 4 sheet. The PIV archive has no fresh t0 edition, so 628 of 651 histories keep an UNKNOWN challenge state. **TRACKA-GPU blocked (27ebbcfe):** the owner approved an L4 (US or EU, ≤ USD 0.69/h, cap USD 1.50), but RunPod refused creation at 09:59 UTC because of no stock. No pod was created and USD 0 was spent. The C9 code requires the same GPU name (L4) for training and prediction, so do not substitute another type. Retry the L4 GPU step as the first step of the freeze card after PRIORARMS lands. The approval stands. **PRIORARMS merged (76a903a7):** P1-RSF-OPEN and P2-COX-OPEN were admitted, with private t0 predictions of 651 per horizon. Development recall at 24 months: P1 48.35%, P2 36.26%, M3 49.45%. P2 dropped oral and injectable because they have zero variance in TRAIN. The C′ supplement was NOT_RUN, because there is no export-only runner. **TRACKA-FREEZE dispatched** (Sol xhigh): it retries the L4 every 15 minutes for up to 3 hours, runs the L1, L1e and C9 predictions, then builds the full freeze manifest, tag and OSF update 4 sheet (AUDITED: NO). It never freezes a partial package.
3. **IS2 paper done (pending Track A and C9 text).** The Astra critique was applied (IS2AUDIT). IS2FIT cut both editions to 10 pages and was merged, and the final planner audit passed (8781f4bd). The docx and PDF files are in `C:/Users/User/Desktop/IS2-MWD/`, with hashes in IS2AUDIT. Next: the IS2 slides (Claude), then text updates after the freeze. Prior-method arms are building (PRIORARMS, Sol xhigh); the spec is in `PRIOR-ARMS-SPEC.md`.
4. Before v1.0: polish the product, sign the installer if a certificate becomes available, and remove the 3 duplicate images (DOCS2 inventory).

## Endgame (approved 28 Nov 2026, night)

See [ENDGAME-PLAN.md](ENDGAME-PLAN.md). Owner decisions: Apache-2.0 for the whole repository, a public web app, and another GPU type for L1, L1e and C9 if no L4 is available by 10 Dec (with a dated deviation and a pod quote first). The journal choice is due by 8 Jan.

Running cards:
- TRACKA-FREEZE (Sol xhigh): L4 retry, then the full freeze and the OSF update 4 sheet.
- IS2STORY (Sol high): IS2 retold with the question-form title, opening A from IS1, reader-friendly names, and the new Figure 1 (`fig1_decision_*`) committed by Claude.
- PRODV1-DATA (Sol high): current-queue adapter, snapshot refresh and PDF hook. Generated data is not committed until the freeze lands.
- SCORER (Sol xhigh): one-command release scorer, fixtures, release builder, GitHub Action and how-to.

Planner fixes: the Thai abstract in the EN edition was pre-audit and is now synced (1445b000). The comprehensive report PDF (40 pages) was delivered and approved by the owner.

## Track A frozen (28 Nov 2026, 11:18:44 UTC)

- **Freeze.** TRACKA-FREEZE was merged with all 10 arms (B1, M1, M3, B3, P1-RSF-OPEN, P2-COX-OPEN, L1, L1e, C9-SFT, C9-GRPO). The tag is `loe-track-a-freeze-20261127` (commit 6712f32c) and the manifest SHA-256 is 8a78b318…c38d.
- **GPU run.** The L4 came from EU-RO-1 on the third retry. Estimated spend was USD 0.3465 and the pod was deleted; RunPod spend is now about USD 4.08 of 23.
- **C9-GRPO** abstained on all 651 rows, which the sheet now discloses.
- **OSF update 4.** The sheet was audited (b9a2c88a) and copied with the prediction ZIP to `Desktop/OSF-UPLOAD-LOE-Bench/update-4/`. The owner files it before 31 Jan 2027, then the planner verifies the timestamp.
- **Unblocked by the freeze.**
  - Commit the current-queue product data.
  - Build the real release ZIP and deposit it on Zenodo (owner login).
  - Update the IS2 and report status sentences.
  - Release v1.0.

