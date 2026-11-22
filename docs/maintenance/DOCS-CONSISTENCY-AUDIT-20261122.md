# Documentation consistency audit, 22 Nov 2026

**Scope.** Top-level documents (`README.md`, `CLAUDE.md`, `AGENTS.md`, `HANDOFF.md`, `INDEX-PLAN.md`, `pyproject.toml`) and
`docs/` (maintenance, tracking, writing, assets), checked against the owner's outcome-based direction of 22 Nov 2026
(phases P0–P5 without calendar gates; the product name Patent-to-Pilot; source-grounded structural expansion as the
proposed method; three separate status fields `method_evidence`, `product_readiness`, `publication_readiness`).

**Method.** Manual reading, plus a relative-link check (every Markdown link and `href`/`src` attribute outside code blocks
resolved against the file system and `git ls-files`) over `README.md`, `docs/README.md`, `INDEX-PLAN.md`, `HANDOFF.md`,
`CLAUDE.md`, `AGENTS.md`, `docs/writing/README.md`, `docs/maintenance/*.md`, the G01/G02 STATUS files,
`docs/healthtech/audits/README.md` and `literature-review/README.md`. Line numbers refer to the working tree at the time of
the audit (HEAD `ad7982d2` plus uncommitted work).

**Not changed by this audit.** Only `README.md`, `docs/README.md` and this file were written. Fixes to `HANDOFF.md`,
`CLAUDE.md`, `INDEX-PLAN.md` and `AGENTS.md` are for the coordinator. Items in protected paths (`scripts/ptp_run.py`,
`artifacts/owner-program/`) need a goal that requires the change (CLAUDE.md §4).

## 1. Broken or unpublished links

| # | Location | Finding | Proposed fix |
|---|---|---|---|
| L1 | `README.md:125`, `docs/README.md:21-24` | Links to `docs/tracking/owner-note-22112026/` (PHASE_BOARD.md, goal_registry.json, phase_tasks.csv, receipts/, affine/) resolve locally but the folder is **untracked**, so the links break on the remote. | Commit `docs/tracking/owner-note-22112026/` (and `scripts/tracking/ptp_tracker.py`, which renders the board) together with the READMEs. |
| L2 | `README.md:155` | Link to `docs/README.md` (new file, untracked). | Commit with this package. |
| L3 | `docs/healthtech/audits/README.md:21` | Dead links: `pepo-followup-20261028-1ce0443/README.md` and `../LUNA_PATENT_LINKED_DOSSIERS_GOAL.md` do not exist. | Point to the recovery commit named in `docs/healthtech/HISTORY.md`, or mark the sentence as historical without links. |

No other broken relative links were found in the checked files. `HANDOFF.md`, `INDEX-PLAN.md`, `CLAUDE.md` and `AGENTS.md`
have no dead links.

## 2. Old G-numbering presented as the current plan

The owner's 22 Nov direction replaces the G01–G08 registry with outcome-based phases P0–P5 (live board in
`docs/tracking/owner-note-22112026/`). G01/G02 remain valid completed foundation receipts and G03 history is preserved, but
G04–G08 are no longer the plan.

| # | Location | Finding | Proposed fix |
|---|---|---|---|
| G1 | `CLAUDE.md:3` | "Target: IS2 presentation, March 2027" reads as a date-based goal. | Keep the date only as presentation context; state that phases advance by verified outcomes (owner N11). |
| G2 | `CLAUDE.md:24`, `AGENTS.md:10`, `HANDOFF.md:9`, `INDEX-PLAN.md:9` | Program source named as `docs/owner/owner-note-21112026/` only; "Goals are G01–G08" (AGENTS.md:10, HANDOFF.md:9). | Name `docs/owner/owner-note-22112026/` as the current owner input (P0–P5) and keep 21112026 as the earlier package; say G-identifiers are historical. |
| G3 | `INDEX-PLAN.md:13-19`, `INDEX-PLAN.md:22-33` | §1 lists only the 21 Nov package files; §2 goal table G01–G08 with G04–G08 "Not started" as if planned. | Add a §1 row set for `owner-note-22112026` (00_START_HERE, 01, 02, 03, 04); replace §2 with a P0–P5 table pointing to the live board, keeping G01/G02 (COMPLETE) and G03 (history) as foundation rows. |
| G4 | `HANDOFF.md:22-33`, `HANDOFF.md:105` | Goal-status table G01–G08; next step "Then G04 planning". | Rewrite the takeover section around P0–P5 task IDs (e.g. P0-T04 A3r1 protocol, P0-T05 budget accounting, P0-T06 synthetic trace); move G04 notes into P2/P3 tasks. |
| G5 | `CLAUDE.md:29-37` | Current-state bullets are G01/G02/G03-centred; no mention of the P0–P5 board or the three status fields. | Add a bullet: "Plan: P0–P5 (live board link); status fields method_evidence / product_readiness / publication_readiness". |
| G6 | `docs/tracking/PTP-PHASE-TRACKER.md:9`, `:13-19` | Earlier tracker with calendar windows per phase ("ช่วงเวลาที่วางไว้") and an invented working title "An Adaptive Evidence Engine for Structured Retrieval and Revision". Contradicts N01 (descriptive naming) and N11 (no calendar gates). | Add a superseded banner pointing to `docs/tracking/owner-note-22112026/PHASE_BOARD.md`, or archive it. (`docs/README.md` already lists it as superseded.) |
| G7 | `docs/writing/README.md:11`, `docs/writing/journal/README.md:1-13` | Journal track still described as Paper 1 → Paper 3 (BridgeRet, CEDS, EG-SHE) with "Status 19 Nov 2026"; the 21 Nov banner says one paper. | Rewrite `journal/README.md` for the one paper (structural expansion, three linked contributions, P5) and keep the Paper 1–3 table under "History". |

## 3. Outdated status lines

| # | Location | Finding | Proposed fix |
|---|---|---|---|
| S1 | `INDEX-PLAN.md:44` | "Stage 2 running on dr-train (861/905 on 21 Nov)". Stage 2 was measured 22 Nov. | "Stage 1 and Stage 2 measured; no instruction contrast significant" with a link to `docs/writing/is2/results/B53-STAGE2-RESULTS.md`. |
| S2 | `INDEX-PLAN.md:52` | "`b53/` pending" for the dr-train pull. The B53 phase pull/prune is done. | Add `artifacts/maintenance/20261122-b53-pull/SUMMARY.md` and `artifacts/maintenance/20261122-g03-pull/SUMMARY.md`; drop "pending". |
| S3 | `INDEX-PLAN.md` §3 | Missing rows for evidence created 22 Nov: B53.0 (`docs/healthtech/research/b53-0/B53-0-RESULTS.md`), the PatenTEB overlap audit, G03 amendments 1–3 and the A3 spend record. | Add rows (they are already listed in `docs/README.md`). |
| S4 | `HANDOFF.md:13` vs `HANDOFF.md:110` | "D1–D9" in the header, "D1–D10" in the decisions section. | Use "D1–D10" in both. |
| S5 | `CLAUDE.md:44-45` | "Owner decisions D1–D8"; OpenRouter "approved in principle, but each still needs a recorded USD cap". D9 recorded E1 = USD 8 / 35,000 requests and D10 exists. | "D1–D10"; "E1 = USD 8 / 35,000 requests approved (D9) for its original scope; the proposed USD 50 envelope (E1R, owner N08) is pending". |
| S6 | `docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122.md:5` | Says decisions are "D1–D8". Superseded by the `…20261122b.md` handoff. | Add a one-line "superseded by NEXT-ACCOUNT-HANDOFF-20261122b.md" banner. |
| S7 | `CLAUDE.md:20-22` | C1 named "support-frontier acquisition and repair policy". The v1 support-frontier policy is parked and the owner's proposed method is now source-grounded structural expansion. | Reword C1 to the structural-expansion mechanism (one bounded relation-to-corpus search under a fixed action budget), marked as proposed. |
| S8 | `artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md:15` (protected) | Requirement 6 says "PDF parked". PDF text-layer ingestion was added under D8 (`tests/test_ptp_g02_pdf_ingest.py`). | Append a dated addendum line rather than editing the receipt; HANDOFF.md:27 already records the add-on. |

## 4. Product and code metadata

| # | Location | Finding | Proposed fix |
|---|---|---|---|
| M1 | `pyproject.toml:8` | `description = "Traceable HealthTech device evidence dossiers and bounded retrieval evaluation"` describes the earlier HealthTech track. | "Local evidence workbench and reproducible retrieval-research engine with exact, versioned source citations." |
| M2 | `scripts/ptp_run.py:231` (protected) | `--ingest` help says ".md/.txt", but `ingest.py` also accepts `.markdown` and `.pdf` (with the `pdf` extra). | "add a .md/.markdown/.txt/.pdf file …" when a goal next touches the launcher. |
| M3 | `scripts/ptp_run.py:215`, `:226` (protected) | Help text labels the tool "(PTP-2026-11-21 / G01)" and the option group "G02 providers, ingestion and retrieval". Accurate provenance but reads as the current plan. | Optional: neutral labels ("Patent-to-Pilot Workbench", "Providers, ingestion and retrieval"). |
| M4 | `docs/assets/architecture.svg:1`, `:100`, `:113` | Figure says "Model providers are planned for G02" and labels providers "(G02)"; providers, hybrid mode and index generations are implemented. The new README therefore uses a Mermaid diagram instead. | Regenerate the figure (providers implemented; hybrid/index generations shown), or keep it only as the foundation-slice figure. |
| M5 | Test environment | `.venv` has `pypdf` but no `pytest`; the system Python has `pytest` but no `pypdf`. With either interpreter the PDF tests are skipped or the suite cannot run. | Install `-e ".[test,pdf]"` into `.venv` (a download; per-item owner approval under rule 2 unless already covered by D8). |

## 5. Consistent, no action needed

- The 8 accepted SACR r2/r3 failures are stated identically in CLAUDE.md §4 and AGENTS.md.
- The Paper 86 and arXiv:2605.24297 rules are consistent across CLAUDE.md, AGENTS.md, `docs/writing/README.md` and INDEX-PLAN.md §4.
- Licence statements in `NOTICE` (DAPFAM, PatEmbed CC BY-NC-SA 4.0; no redistribution) match the dataset registry and the README.
