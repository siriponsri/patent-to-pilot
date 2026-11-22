# IS2 committee deck — outline v2 (12 slides, about 12 minutes; 10-minute variant at the end)

> **Correction note (22 Nov 2026, owner note 22112026, "Corrections to carry into writing").** Paper 53's "37.1%" exposure statement is marked **denominator to be recovered; do not reuse** wherever it appears below. The repository account (257/692 queries) has not been re-checked against the original Paper 53 table, and other drafts turned it into an item-level claim. B53's own measured π@100 = 0.371 (905 queries) is a separate number and is not Paper 53's figure. Text is kept as written; the markers govern.

v2 (22 Nov 2026): B53 Stage 1 and Stage 2 numbers are filled in. Slides 5–8 now follow program PTP-2026-11-21 (owner
package `10_PAPER53_BRIDGE.md` §6 and G08 narrative). The legacy trilogy is no longer presented as three papers.

Built from the owner strategy §6. Numbers are filled **only** from receipts. A slot marked [PENDING] stays visibly pending if no
result exists on the day. Every number carries an evidence label.

| # | Time | Title | Content (Thai speech) | Evidence / source | Label |
|---|---:|---|---|---|---|
| 1 | 0:40 | From Paper 53 to Patent-to-Pilot | near-zero instruction effect → program (Diagnose → Intervene → Discover → Acquire → Repair → Translate) | program PTP-2026-11-21 charter (`RESEARCH-ROADMAP.md` retired 21 Nov) | HISTORY + PLAN |
| 2 | 1:00 | What the IS1 Committee Asked Me to Fix | K1a–K2b; 37.1% (257/692) exposure at top-100 [**correction 22 Nov 2026:** Paper 53's 37.1% — denominator to be recovered from the original Paper 53 source; do not reuse] | Paper 53; IS1 evaluation | ACCEPTED (Paper 53) |
| 3 | 1:20 | IS2 Core Experiment: B53 | **Stage 1:** π@100 F0 0.371; BM25 −0.105, RRF(BM25, F0) +0.004 (ns), Arctic −0.054, RRF(BM25, Arctic) −0.035. **Stage 2:** 0 of 10 instruction contrasts significant on C = 153 (Δ +0.001 to +0.009, Holm p ≥ 0.695); Scrambled ≈ Generic; BGE plain < Qwen3 everywhere | `results/B53-STAGE1-RESULTS.md`, `results/B53-STAGE2-RESULTS.md` | MEASURED (exposed benchmark; re-implementation) |
| 4 | 0:55 | What We Can and Cannot Conclude | The near-zero instruction effect holds under every first stage, so it is not an artifact of patembed-base. Δ_all = π·Δ_exp is accounting, not cause. CIs of about ±0.01 do not exclude small effects. Labels are incomplete. Re-implementation ≠ replication. | COMMITTEE-RESPONSE §1 K1c, K2a | METHOD |
| 5 | 1:10 | What Did Not Work (honest record) | P1-BridgeRet fine-tuning: all 5 configs below zero-shot Qwen3/PatEmbed on P1-DEV. AM-7: OUT-only recall is gamed by IPC demotion (N4: OUT +0.054, IN −0.176). TEST not opened. | `paper1-bridgeret/P1-RETHINK-20261120.md`, `am7/stage2a/` | MEASURED (DEV) |
| 6 | 1:10 | From Ranking to Evidence: the Unified Program | One paper, three contributions: C1 support-frontier acquisition and repair policy; C2 versioned evidence architecture (PLAN → ACQUIRE → COMMIT); C3 evaluation package (DAPFAM, Thai Gazette transfer, update episodes) | owner package `01_PROGRAM_CHARTER.md`, `10_PAPER53_BRIDGE.md` | DESIGNED / G03 NEXT |
| 7 | 1:00 | Engine and Workbench Built | G01: shared core, FTS5 retrieval, exact versioned citations, selective source revision. G02: chat/embedding/rerank ports, index generations, hybrid mode, text/MD ingestion, dataset registry; real Qwen3-Embedding route | `artifacts/owner-program/PTP-2026-11-21/G01`, `G02` | ENGINEERING VALIDATED |
| 8 | 1:20 | Live Demo: Changed Source → Affected Decision | 60–90 s: project → run → open Thai citation → add a source revision or new document → only the affected cells change; old citation still opens | Workbench (`Start-PTP.cmd`) | ENGINEERING VALIDATED (SYNTHETIC / OWNER FILES) |
| 9 | 0:55 | Research Assets Built During IS | manifest, Challenge-1M, pipelines, tests, receipts, licence boundaries | `PORTFOLIO-KMITL.md` | MEASURED / RECORD |
| 10 | 0:50 | Potential Value to KMITL and Industry | venues on the faculty list; teaching; tech-transfer prospects (conditional) | `journal/VENUES.md`, PORTFOLIO | HYPOTHESIS |
| 11 | 0:45 | What IS2 Will Deliver | D1–D6 (`IS2-DELIVERABLES.md`) | IS2 contract | PLAN |
| 12 | 0:55 | Conclusion & Committee Feedback | request guidance on scope, metrics, university use | — | — |

**10-minute variant:** merge slide 4 into 3 and slide 10 into 9; cut the demo to 60 s.

Speech texts: strategy §6.1–6.3 (opening, transition, closing). Q&A bank: strategy §7. In Q4, use the S* outcome (fine-tuning
lost to zero-shot) and the B53 Stage 1 and Stage 2 numbers above. Speech for slides 6–8 must not present the legacy
BridgeRet / CEDS / EG-SHE drafts as completed or published papers (`10_PAPER53_BRIDGE.md` §6).
