# D40 documentation review

27 November 2026. The DOCS task branch `loe/DOCS` started at `3fb7300f6cdbf090983c394bb71acc7337c694e7`, verified against `origin/research/loe-bench`. LOE-Bench is the active program, with RA Pharma as its Thai-context demo layer. Wave 2 is development only. The confirmatory test is sealed and has no result. The publishing rules retain the Paper 86 restriction to IS2 and exclude arXiv:2605.24297 as a source. [Owner decision D40](../maintenance/OWNER-DECISIONS-20261122.md#d40--loe-bench-becomes-the-active-program-27-november-2026) · [Standing rules](../../CLAUDE.md#3-standing-rules-all-remain-in-force).

## Files changed

| File | Change |
|---|---|
| [INDEX-PLAN.md](../../INDEX-PLAN.md) | Added D40 entry points and status at the top. Preserved the earlier programs, outcomes and evidence in a historical section. |
| [docs/README.md](../README.md) | Pointed new readers to LOE-Bench and identified the archived RA Pharma dispatch and its relevance to the Thai demo. |
| [docs/loe-bench/README.md](README.md) | Indexed the plan, handoff, receipts, manifests, source references and technique ledger. Added the verified local test command. |
| [RA Pharma master plan](../ra-pharma/MASTER-PLAN.md), [research-first study](../ra-pharma/RESEARCH-FIRST.md), [session prompts](../ra-pharma/SESSION-PROMPTS.md), [research handoff](../ra-pharma/research/HANDOFF.md), [product handoff](../ra-pharma/product/HANDOFF.md) | Added a D40 banner above each historical body. |
| [IS2 README](../writing/is2/README.md) | Linked the current IS2 evidence design from a banner above the historical materials. |
| [Agent lessons](../maintenance/AGENT-LESSONS.md), [22 Nov handoff](../maintenance/NEXT-ACCOUNT-HANDOFF-20261122.md), [22 Nov afternoon handoff](../maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md), [24 Nov handoff](../maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md) | Updated onboarding links to the LOE-Bench plan and lane handoff. Preserved the dated instructions and operating procedures. |
| [docs/loe-bench/DOCS-REVIEW.md](DOCS-REVIEW.md) | Recorded the audit and planner handback for integration into the lane handoff and memory. |

## Findings for the main planner

Line numbers refer to base `3fb7300f`. The authorized changes in this card cover the navigation files above.

| Location | Finding | Suggested fix |
|---|---|---|
| [README.md](../../README.md) lines 7, 54 and 69–70 | The roadmap, research summary and contributor links still present RA Pharma as the current direction. | Put LOE-Bench first and point to its documentation map. Retain the verified Windows alpha and present the earlier dossier work as Thai-demo context. |
| [S0–S5 board](../evidence-scope/MASTER-PLAN.md) line 3 | The historical board directs readers to the 26 November RA Pharma dispatch as current. | Keep the transition date and add a D40 pointer to the current LOE-Bench plan. |
| [HANDOFF.md](../../HANDOFF.md) lines 5, 31, 47, 53, 62 and 81–83 | The D40 lead still points to Wave 1 and says no research result exists. Later instructions direct the next session to RA Pharma under the former role allocation. | Refresh the lead with the Wave 2 development status and sealed-test status. Place the pre-D40 dispatch and restart instructions under a dated historical heading. |
| [AGENTS.md](../../AGENTS.md) line 12 and [CLAUDE.md](../../CLAUDE.md) lines 28–29 | The generic ownership instructions can send LOE-Bench executors to the former RA Pharma handoff or imply executor ownership of the lane handoff and memory. | Qualify the older rule as RA Pharma history and point to the D40 protocol in the LOE-Bench plan. The main planner owns the LOE-Bench lane handoff and memory. |
| [LOE-Bench handoff](HANDOFF.md) lines 13, 18 and 21–23 | The CP1 endpoint is quoted without its replacement. The Wave 2 status still has CP2 and T7 dispatched, and the next-action block calls for dispatching FIX1. | Keep the Wave 1 record and label its endpoint as historical. Refresh the Wave 2 checkpoint from the plan's dispatch board and use the owner-approved criteria v2. |
| [LOE-Bench plan](PLAN.md) lines 177 and 180–181 | The dispatch board still assigns future or superseded groups of cards to Sonnet or Claude, contrary to the Wave 2 onward executor rules at lines 130–136. | Mark the old combined Wave 2 row superseded. Split the Wave 3 cards and assign each an approved executor. Preserve the dated Wave 1 execution history. |
| [LOE-Bench memory](MEMORY.md) lines 5 and 16 and [decision register](../maintenance/OWNER-DECISIONS-20261122.md) lines 184–187 | The initial role split still reads as current in the register. The memory records the later change but leaves the original split unqualified. | Preserve the original Wave 1 decision and append or link the dated role change. Name Claude Opus 5.5 as main planner and sole reviewer, GPT-6.2 Astra high as co-planner and the GPT card allocation from Wave 2 onward. |
| [LOE-Bench plan](PLAN.md) lines 9 and 172 and [E8 receipt](receipts/E8.md) line 22 | The open-data requirement and E8 public access can be read as granting open reuse. E8 records restrictions on redistribution and commercial use. | Keep E8's local research evidence and clarify which data can be admitted to a redistributable benchmark or demo before any further use. |

## Link and language checks

The scratch Python standard-library checker examines relative Markdown destinations, local images, reference definitions, simple HTML links and Markdown heading fragments. The check covers the editable paths, the root README, CLAUDE, AGENTS, the root handoff and all Markdown files under `docs/loe-bench/`. Remote targets, code examples and owner-local paths given as code are outside the link check. `CONTRIBUTING.md` is absent from this checkout.

The checker scanned 525 relative destinations across 62 files and found zero broken paths or fragments. The scratch checker remains outside the repository.

No editable file contained Thai project-authored prose. Thai in `docs/loe-bench/owner-source/` is the preserved source package. The Thai labels and search literals in `THAI-OPEN-DATA.md` lines 22, 24 and 27–28 document source evidence and retrieval. The November 22 consistency audit quotes an original tracker label at line 42.

A supplemental scan found historical Thai project-authored material outside the edit scope.

| Location | Suggested fix |
|---|---|
| [Earlier phase tracker](../tracking/PTP-PHASE-TRACKER.md) lines 6–28 and later | Keep the dated AFFiNE import as an archive. Use the existing English index for current navigation. |
| [IS2 short-paper draft](../writing/is2/IS2-SHORT-PAPER-DRAFT.md) lines 3–10 and 14 onward | Preserve the faculty exporter input and point readers to the English working edition for project guidance. |
| [B53 Stage 2 tables](../writing/is2/results/b53-stage2-tables.md) lines 1, 3, 11, 13 and 21 | Preserve the historical table and use the English Stage 2 results for project guidance. |

## Verification

Python 3.12.10 on Windows.

| Command | Result |
|---|---|
| `python -m pytest -q` from the repository root | Exit 1. Eight failures, all within the standing SACR r2/r3 budget exception. Both supervisor files failed `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` for the four cases `nan`, `inflated`, `erased` and `insufficient`. No additional failure appeared. |
| `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` | PASS. All 127 tests passed, exit 0. Existing Purple Book file-handle `ResourceWarning` messages appeared. |
