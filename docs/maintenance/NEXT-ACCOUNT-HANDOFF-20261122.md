> **SUPERSEDED (22 Nov 2026):** use [NEXT-ACCOUNT-HANDOFF-20261122b.md](NEXT-ACCOUNT-HANDOFF-20261122b.md). Kept as history.

> Historical dispatch. Start new work from the [LOE-Bench plan](../loe-bench/PLAN.md) and [lane handoff](../loe-bench/HANDOFF.md). The [S0–S5 master plan](../evidence-scope/MASTER-PLAN.md) and the procedures below retain their original scope.

# Next-account handoff, 22 Nov 2026 (v2, after the owner decisions)

The owner switched accounts because of the weekly limit. Paste the prompt in §1 into a new Claude Code session opened in
`C:\Users\User\Desktop\myProject\patent-to-pilot`. The owner's decisions are in
[OWNER-DECISIONS-20261122.md](OWNER-DECISIONS-20261122.md) (D1–D8).

## 1. Prompt to paste

```text
You are continuing program PTP-2026-11-21 (patent-to-pilot) from another Claude account. Read, in order:
CLAUDE.md, HANDOFF.md, INDEX-PLAN.md, AGENTS.md, docs/maintenance/AGENT-LESSONS.md,
docs/maintenance/OWNER-DECISIONS-20261122.md, docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122.md.
Then run `git status` and `git log -5`. Report to the owner in plain Thai.
All standing rules in CLAUDE.md §3 apply: no TEST data; no paid API, RunPod or GPU rental without a recorded USD cap;
V100 only with CUDA_VISIBLE_DEVICES=1 under the GPU lock (another user's service holds 24 GB on it; never touch it);
freeze a protocol before any number; commit only your own files with explicit paths; update HANDOFF on every major
event; pull and prune dr-train after each phase.

Do these in order, without asking about routine choices:
1. G03 amendment 2: collect /data/ptp-paper2/g03-dev/results-a2.json (a2.log ends G03_A2_DONE; if it shows a
   Traceback, fix the bug only and rerun code/g03_queue_a2.sh, which is resumable). Copy it to
   docs/healthtech/research/g03-dev/g03-dev-results-a2.json and add memo section 4b to G03-DEV-DECISION-MEMO.md.
   Owner decision D2: if amendment 2 is parked, keep working on acquisition. Pre-declare a new mechanism that brings in
   NEW candidates (e.g. LLM query rewriting or obligation decomposition via OpenRouter, or new candidate sources).
   Freeze it before any number; allowed DEV only. Then pull and prune g03-dev per
   docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md.
2. D3: download the PatenTEB train split (approved; if Hugging Face asks for a login or terms, ask the owner to do it)
   and run a family-level overlap audit of PatEmbed training data against DAPFAM (queries + corpus). Commit
   aggregates only.
3. D1/D5/D6: re-scope IS2 to "research + demo": Paper 53 → B53 bridge → G03 DEV findings (honest, including parked
   arms) → B53.0 (our pipeline matches the DAPFAM paper) → Workbench demo of selective update. English byline
   "Tuchsanai Ploysuwan", with the title only in footnote 2; acknowledgments = AI-use statement only. First show the
   owner a short Thai outline, then rebuild the Thai and English editions with the kmitl-is-paper and academic-figures
   skills (sources in docs/writing/is2/paper/), and update SLIDES-OUTLINE.md and DEMO-STORYBOARD.md.
4. D8: install pypdf into .venv, enable the G02 PDF ingestion adapter with tests (python -m pytest; only the 8 known
   SACR failures are accepted).
5. D7 / API: read docs/maintenance/API-BUDGET-PROPOSAL-20261122.md. Envelope E1 = USD 8 / 35,000 requests for
   G03 amendment 3 (LLM query expansion as new acquisition routes). Check OWNER-DECISIONS-20261122.md for the owner's
   approval; if not recorded, ask once in Thai. If approved: freeze G03-DEV-AMENDMENT-3 (pilot on 2,000 P1-DEV
   queries x 4 models, then one full run with the P1-DEV-selected model, same harness, same B = 4, same final scorer,
   same decision rule), add OpenRouter profiles in the Workbench (openai_compatible adapter, endpoint
   https://openrouter.ai/api/v1, key from env var OPENROUTER_API_KEY set by the owner), reasoning off, max_tokens
   <= 400, temperature 0, save every response, log usage, and obey the stop rules in the proposal. Check get-credits
   before and after. RunPod (via MCP) needs its own per-job USD cap.
Finish each step with a commit, a push and a HANDOFF update. At the end, write a new next-account handoff file.
```

## 2. State at handoff (all pushed to origin/main)

| Item | State | Where |
|---|---|---|
| G01 / G02 | COMPLETE | `artifacts/owner-program/PTP-2026-11-21/G01/`, `G02/` |
| B53 Stage 2 | MEASURED: 0/10 instruction contrasts significant | `docs/writing/is2/results/B53-STAGE2-RESULTS.md` |
| B53.0 | MEASURED: 11/12 cells within ±0.010 of the DAPFAM paper; PatEmbed overlap caution | `docs/healthtech/research/b53-0/` |
| G03 protocol v1 | support_frontier_v0 **PARKED**. Static default F\* = Qwen3×2 + PatEmbed×2 | `docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md` |
| G03 amendment 1 | **PARKED** (field obligations) | memo §4a |
| G03 amendment 2 | **RUNNING** on dr-train (frozen at 8e759b8e). At ~17:00 it was building the TRAIN allocation arms (30,000-query sample); TRAIN evaluation and the selector follow. | `/data/ptp-paper2/g03-dev/a2.log`, `results-a2.json` |
| IS2 papers | Thai and English, 8 pages each, B53-centred; to be re-scoped (D1) | `docs/writing/is2/paper/` |
| dr-train `b53/` | Pulled, verified, pruned. `inputs/` deleted after owner approval (D4) | `artifacts/maintenance/20261122-b53-pull/SUMMARY.md` |

**How to read amendment 2:**
- `results-a2.json` → `decision`, `principal_VAL_LSstar_minus_Fstar`, and `blocks.*.selectors.*.headroom_captured`.
- Rule:
  - CONTINUE if the ALL lower CI > 0 and the IN/OUT lower CIs > −0.005;
  - PARK if the ALL upper CI < 0 or IN/OUT is inferior;
  - otherwise REVISE.
- This is the third look at VAL. Say so.

## 3. What we learned (details in AGENT-LESSONS.md)

- Fixed dense allocations are hard to beat on P1-DEV. Extra depth on the same routes adds little. The per-query oracle
  headroom (+0.079 ALL R@200) is not captured by rule-based overlap signals or field obligations. Gains have to come from
  candidates the current routes never surface.
- Our DAPFAM pipeline matches the published paper (B53.0), so G04 numbers will be credible. PatEmbed may be
  contaminated on DAPFAM; D3 resolves that.
- The dr-train V100 is shared (thaivoice service, 24 GB). Our jobs use memory fraction 0.12 under the GPU lock.

## 4. Still open with the owner

- OpenRouter E1 (USD 8 / 35,000 requests) is **APPROVED** (D9, 22 Nov); start G03 amendment 3 when step 5 comes.
  Per-job caps for RunPod (D8) are still open.
- The Paper 53 DOI.
- The G01 launcher check by Explorer double-click.

## 5. Local-only (not in Git)

- `docs/owner/` (owner package).
- `../_private_artifacts/` (dr-train archives `20261121/` and `20261122-b53/`, the B53 inputs, the IS2 template copy).
- Agent memory: `C:\Users\User\.claude\projects\C--Users-User-Desktop-myProject-patent-to-pilot\memory\`, which is
  machine-local. The repo copy of the lessons is `docs/maintenance/AGENT-LESSONS.md`.
