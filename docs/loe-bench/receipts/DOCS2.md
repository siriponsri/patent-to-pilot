# DOCS2 | D41 documentation alignment

28 November 2026. Executor branch `loe/DOCS2`, cut from verified `origin/research/loe-bench` at `496ca359`. This is the main planner's integration and lane-memory handback. The owner-approved plan is the source of product scope and deadlines. The FREEZE and L1DEV receipts are the sources of development claims. [D41 plan](../PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026) · [FREEZE](FREEZE.md) · [L1DEV](L1DEV.md).

| File | Change |
|---|---|
| [AGENTS.md](../../../AGENTS.md) | Named Market Window Dossier as the D41 product and LOE-Bench as the benchmark. Kept executor roles and standing rules. |
| [CLAUDE.md](../../../CLAUDE.md) | Updated the mandate with the pre-development forecast, evaluator hand-off and Thai layer. Kept standing rules. |
| [Root handoff](../../../HANDOFF.md) | Added D41 scope, evidence status, author names and next milestone. Labelled previous dispatches as historical. |
| [Evidence index](../../../INDEX-PLAN.md) | Linked the current D41 plan and writing entry point. Marked the earlier IS2 files as historical. |
| [Docs map](../../README.md) | Routed current program and writing links to D41. |
| [Dossier docs index](../README.md) | Added the D41 user flow, scope, benchmark checkpoint, Thai inputs and receipt links. |
| [Lane handoff](../HANDOFF.md) | Replaced the v2 checkpoint with criteria v3, the frozen development contrasts and the exact L1 prompt scope. Updated the sequence through preregistration v2, OSF and the blinded C′ gate. |
| [Agent lessons](../../maintenance/AGENT-LESSONS.md) | Updated the name of the active plan in the takeover instructions. |
| [Writing overview](../../writing/README.md) | Updated IS2 scope, authors and dates. Preserved the two tracks' writing rules and source constraints. |
| [IS2 entry point](../../writing/is2/README.md) | Recorded P1 and P2, the workflow, C1–C10, the seven-part dossier, evidence status and the weekly schedule. Retained links to the B53 drafts and faculty exporter input. |
| [IS2 deliverables](../../writing/is2/IS2-DELIVERABLES.md) | Marked the earlier requirements as historical and linked the current entry point. |
| [IS2 outline v3](../../writing/is2/IS2-OUTLINE-v3-20261122.md) | Pointed readers of the old outline to the D41 scope. |
| [Journal index](../../writing/journal/README.md) | Removed the stale active RA Pharma claim and kept prior manuscript provenance and the existing writing guard. |
| [Evidence-scope board](../../evidence-scope/MASTER-PLAN.md) | Directed current dispatch to D41 and preserved the S0–S5 record. |
| [RA Pharma board](../../ra-pharma/MASTER-PLAN.md) | Identified Workbench and RA Pharma inputs as the basis of the Thai demo layer. |
| [RA Pharma research-first record](../../ra-pharma/RESEARCH-FIRST.md) | Updated the banner's active plan pointer. |
| [RA Pharma session prompts](../../ra-pharma/SESSION-PROMPTS.md) | Updated the banner's active plan pointer. |
| [RA Pharma product handoff](../../ra-pharma/product/HANDOFF.md) | Updated the historical banner to point to D41. |
| [RA Pharma research handoff](../../ra-pharma/research/HANDOFF.md) | Updated the historical banner to point to D41. |
| [Deletion inventory](DOCS2-DELETION-INVENTORY.md) | Tracked-path audit with dependency examples and risks. The sole delete recommendation covers three verified duplicate screenshots, subject to review and a link update. |

## Evidence and remaining follow-up

- **Development only.** FREEZE reports H1 +9.80 [+0.14, +19.65], H2 +5.49 [−2.00, +11.25] and H3 +13.00 [+3.27, +23.17] percentage points. Retrieval and note edits did not run scoring. The confirmatory test remains sealed.
- **L1 prompt scope.** L1 received only ingredient identity, cutoff and horizon. C2 specifies a future evidence-matched L1e arm. The observed L1 comparison cannot estimate the effect of matching evidence.
- **Planner-owned plan and memory.** The plan's D40 paragraph still says LOE-Bench is the active program, and the T1v3 and T4c dispatch rows still show pre-REG values without a nearby FREEZE caveat. Mark the rows as pre-freeze and use the FREEZE receipt for the current estimate. The 28 November overnight entry in lane memory still describes L1 as evidence-fed and overstates the inference, though the following entry corrects it. Add a cross-reference on that overnight entry to its correction and record D41 approval and this receipt in the next lane-memory update. [Plan](../PLAN.md) · [Lane memory](../MEMORY.md).
- **Parallel publication work.** `origin/research/loe-bench` advanced to `9efd6bc3` during the card. The three new commits cover the main planner's README and artwork and the draft OSF copy sheet and settings. Their paths do not overlap DOCS2. The preregistration v2 and copy-sheet task should resolve the old L1 allowed-evidence wording and OSF instructions. The decision register and D40 review retain their dated scope. [Preregistration v1](../PREREGISTRATION.md) · [OSF procedure](../OSF-SUBMISSION.md) · [Root README](../../../README.md) · [D40 documentation review](../DOCS-REVIEW.md).
- **Inventory boundary.** No tracked paths were removed. Confirm the inventory against the integration head before a separate deletion commit. Keep the canonical screenshots, update the inbound link and preserve the evidence listed as keep.

## Checks

- `rtk proxy python -m pytest tests/test_org_adaptive_terminology.py -q` — PASS, 2 tests, exit 0.
- `rtk proxy git diff --check` — PASS, exit 0.
- Inline Python Markdown check — PASS, 21 changed or added files, zero new broken relative links or heading anchors.
- Assigned-path `git status --short` across the 47 registered worktrees — no concurrent changes to those paths found outside the DOCS2 checkout.
- Repository-wide tests and benchmark runs — NOT_RUN for this documentation-only card.

Next action for the main planner is to review and integrate `loe/DOCS2`, record the outcome in lane memory and review the inventory before any deletion. Preregistration v2 and the audited OSF copy sheet remain the publication dependency.
