# Next-account handoff, 22 Nov 2026 (Bangkok afternoon)

The owner switched accounts because of the weekly limit. Paste the prompt in §1 into a new Claude Code session opened in
`C:\Users\User\Desktop\myProject\patent-to-pilot`. Everything else here is reference for that session.

## 1. Prompt to paste

```text
You are continuing program PTP-2026-11-21 (patent-to-pilot) from another Claude account. Read, in order:
CLAUDE.md, HANDOFF.md, INDEX-PLAN.md, AGENTS.md, docs/maintenance/AGENT-LESSONS.md,
docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122.md. Then run `git status` and `git log -5`. Report to the owner in Thai.
All standing rules in CLAUDE.md §3 apply: no TEST data, no paid API/GPU rental, V100 only with CUDA_VISIBLE_DEVICES=1,
freeze a protocol before any number, commit only your own files with explicit paths, update HANDOFF on every major
event, pull and prune dr-train after each phase.

Tasks, in this order:
1. Collect G03 amendment 2 from dr-train (/data/ptp-paper2/g03-dev; a2.log ends G03_A2_DONE; results-a2.json holds the
   decision computed by the frozen rule). Copy results-a2.json to docs/healthtech/research/g03-dev/g03-dev-results-a2.json.
   Add section 4b to G03-DEV-DECISION-MEMO.md. Write the G03 closing summary (what is parked, the static default F*,
   the next mechanism hypothesis). Then pull and prune g03-dev per docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md.
2. Owner decision of 22 Nov 2026: the IS2 report's CORE becomes the research we are doing now (program PTP-2026-11-21:
   G03 acquisition experiments, B53.0 native check, the Evidence Engine / Workbench), with B53 as the bridge from
   Paper 53. Propose a re-scoped IS2 outline (Thai + English short papers, slides) to the owner in Thai first, with
   claims calibrated to DEV-only evidence. Then rebuild both editions with the owner's skills kmitl-is-paper and
   academic-figures (sources: docs/writing/is2/paper/content_th.py, content_en.py, make_figs.py, paper_numbers.py).
3. Then G03 → G04 planning per docs/owner/owner-note-21112026/02_GOALS_AND_PHASES.md. Ask the owner only what needs
   their authority (see the open owner items in the handoff file).
```

## 2. State at handoff (all pushed to origin/main)

| Item | State | Where |
|---|---|---|
| G01 Workbench | COMPLETE | `artifacts/owner-program/PTP-2026-11-21/G01/` |
| G02 provider / ingestion / dataset contracts | COMPLETE (USD 0) | `artifacts/owner-program/PTP-2026-11-21/G02/` |
| B53 Stage 2 | MEASURED: 0/10 instruction contrasts significant | `docs/writing/is2/results/B53-STAGE2-RESULTS.md` |
| B53.0 vs DAPFAM paper | MEASURED: 11/12 cells within ±0.010; patembed overlap caution | `docs/healthtech/research/b53-0/` |
| G03 protocol v1 | support_frontier_v0 **PARKED** (VAL ALL R@200 −0.020 vs F\*). F\* = Qwen3×2 + PatEmbed×2 | `docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md` |
| G03 amendment 1 (field obligations) | **PARKED** (P1-DEV +0.0018; VAL −0.0054 [−0.0107, 0.000]) | memo §4a, `g03-dev-results-a1.json` |
| G03 amendment 2 (learned selector, TRAIN labels) | **RUNNING** on dr-train, detached. Frozen at 8e759b8e. At 16:30: TRAIN sample of 30,000 chosen and encoded; the TRAIN arms, their evaluation and the selector follow (about 1 h). | `/data/ptp-paper2/g03-dev/a2.log`, `results-a2.json` |
| IS2 short papers | Thai and English editions, 8 pages each, 3 figures, audited | `docs/writing/is2/paper/IS2-paper-{th,en}.{docx,pdf}` |
| IS2 scope | **Owner decision 22 Nov:** the core becomes the current research program (see §1 task 2) | this file |

**If amendment 2 failed** (`Traceback` in `a2.log`):
- Fix the bug and rerun `code/g03_queue_a2.sh`; it is resumable.
- Do not change the frozen design, features, models or decision rule.
- Record the failure in the memo.

**How to read amendment 2:**
- `results-a2.json` → `decision`, `principal_VAL_LSstar_minus_Fstar`, and `blocks.*.selectors.*.headroom_captured`.
- The frozen rule:
  - CONTINUE if the ALL lower CI > 0 and the IN/OUT lower CIs > −0.005;
  - PARK if the ALL upper CI < 0 or IN/OUT is inferior;
  - otherwise REVISE.
- This is the third look at VAL. Say so.

## 3. What we learned today (also in AGENT-LESSONS.md)

- **Static fixed allocations are hard to beat on P1-DEV.**
  - Extra depth on the same routes adds little: 0.418 at B = 2 against 0.423 at B = 4.
  - Per-query oracle headroom is large (+0.079), but rule-based observable signals, and field obligations, did not
    capture it.
  - Amendment 2 tests whether a learned selector can.
- **If acquisition stays null, the paper's strongest defensible contribution may be maintenance (C2/M3)**
  (STATISTICAL_PLAN §8). Do not rewrite history.
- **B53.0** shows our DAPFAM pipeline matches the published paper, so G04 numbers will be credible.
- **PatEmbed on DAPFAM may be contaminated.** Treat it as historical only until an overlap audit is done.
- **dr-train V100** is shared with another user's service (thaivoice, 24 GB). Our jobs fit in ~8 GB with memory fraction
  0.12 and the GPU lock. Never touch that process.

## 4. Open owner items (ask in one message, in Thai)

1. **IS2:**
   - the English byline title for the advisor (e.g. "Asst. Prof. Dr. Tuchsanai Ploysuwan");
   - the acknowledgments line;
   - the Paper 53 DOI;
   - confirm the re-scoped outline.
2. Approval to download the gated PatenTEB train split for the PatEmbed–DAPFAM overlap audit.
3. Whether to delete the read-only `/data/ptp-paper2/b53/inputs/` (341 MB; an identical local copy exists).
4. Optional per-item approvals: Ollama, `pypdf`. A spending envelope for API profiles (default USD 0).
5. Observe the G01 launcher by Explorer double-click.

## 5. Local-only (not in Git)

- `docs/owner/` (owner package).
- `../_private_artifacts/`, which holds:
  - the dr-train archives `20261121/` and `20261122-b53/`;
  - the B53 inputs;
  - the IS2 template copy.
- Agent memory: `C:\Users\User\.claude\projects\C--Users-User-Desktop-myProject-patent-to-pilot\memory\`. It is
  machine-local; the repo copy of the lessons is `docs/maintenance/AGENT-LESSONS.md`.
