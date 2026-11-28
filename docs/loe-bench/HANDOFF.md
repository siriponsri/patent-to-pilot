# LOE-Bench lane handoff

Owner of this file: the main planner (Claude Opus). Branch: `research/loe-bench`, with its local worktree at `../_worktrees/ptp-loe-bench`; `main` is kept equal to it at each integration. Plan and board: [PLAN.md](PLAN.md). Memory: [MEMORY.md](MEMORY.md). Techniques: [TECHNIQUE-LEDGER.md](TECHNIQUE-LEDGER.md). Documentation index: [README.md](README.md).

## Current state (28 November 2026, D41)

Market Window Dossier covers the launch-window decision before bioequivalence or comparative trials and the later freedom-to-operate (FTO) hand-off. The queue, dated evidence pack and checklist help scarce evaluators prioritize and verify cases. Qualified counsel determines freedom to operate. The Workbench and RA Pharma inputs support the Thai layer. LOE-Bench remains the research benchmark. [D41 scope and component gates](PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026).

- **Roles (owner-approved).** Claude Opus is main planner and only reviewer. GPT-6.2 Astra high is co-planner. GPT executors use GPT-6.2 Sol xhigh or high, and GPT-6 Luna high only for scripted cards.
- **Primary criteria.** Criteria v3 measure entry recall at a 20% review budget, with queues ranked by native scores. The fixed sequence is H1 (M3 − B1 at 24 months), H2 (M3 − M1 at 24 months), then H3 (M3 − B1 at 12 months), each one-sided at α = 0.025. The practical-usefulness threshold is +10 percentage points. Auto-clear remains a secondary safety analysis. [Criteria v3](PLAN.md#confirmatory-criteria-v3-owner-approved-27-november-2026-supersedes-v2-endpoints).
- **Test.** The test is sealed in code (`loe_bench/seal.py`). No confirmatory result exists. Track A inputs are frozen at tag `loe-S0-input-20261127`. Track A predictions still require an external timestamp and freeze before 2027-01-31 23:59 UTC.
- **Pipeline.** As-of Orange Book (FDA ZIPs plus NBER 1985–2016), active-moiety keys (FIX2c), challenge evidence (E7 plus E7b patent-number relinking) and K07. Rejected techniques: K06, K08, K09, K10 and K19. See the [NBER reuse limits](receipts/E8.md).
- **Disclosed incidents (T4).** A preflight decoded test-period ANDA records for an index and produced no outcome output. An executor also stopped a process it had not verified as its own. [Memory](MEMORY.md).

## Overnight results (27→28 Nov)

- **T4c.** α = 0.025 by rule. H1 power at 75 event clusters is 50% at +10 pp and 85% at +15 pp, with MDE80 about +14 pp.
- **FREEZE.** FROZEN_FOR_PREREG (config sha256 `3a6a66f9…c68`). Frozen development recall differences in percentage points (95% CIs) are H1 +9.80 [+0.14, +19.65], H2 +5.49 [−2.00, +11.25] and H3 +13.00 [+3.27, +23.17]. The REG fix for undated Paragraph IV records explains the H2 change. [FREEZE receipt](receipts/FREEZE.md).
- **Preregistration v1.** Merged after CP5 and T5b. D41 schedules v2 and a main-planner audit before owner submission.
- **LLM arm (L1, Qwen2.5-7B on L4).** The exploratory development arm received only ingredient identity, cutoff and horizon. Its recall was below B1 and M3 at both horizons. The planned L1e comparison gives the LLM the same as-of evidence as M3. [L1DEV receipt](receipts/L1DEV.md) · [K24](TECHNIQUE-LEDGER.md).
- **GPU spend.** About USD 0.53 of the USD 20 envelope. Volume `8n6rnzljwg` is kept at USD 2.10 a month, and every pod is deleted.

## Next action

Develop C2 (L1e), C3 (competition at launch) and C4 (demand baseline and volume forecast) on allowed development data, select demo cases by source availability and prepare preregistration v2 for main-planner audit by 6 December. Where a source vintage cannot be established, label the analysis retrospective. The owner submits to OSF on 7–13 December through a GPT-6.2 Sol high browser agent using the audited copy sheet. The main planner writes `PREREG_LOCK` from the registered PDF hash and runs the blinded C′ gate before scoring. The full schedule includes the first dossier, traceability and metric audits, the December IS2 draft, the January Track A freeze and the January final IS2. [D41 schedule](PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026) · [IS2](../writing/is2/README.md).

The DOCS2 handback records the documentation changes and the remaining planner follow-up. Review its inventory before authorizing any deletion. [DOCS2 receipt](receipts/DOCS2.md) · [Deletion inventory](receipts/DOCS2-DELETION-INVENTORY.md).
