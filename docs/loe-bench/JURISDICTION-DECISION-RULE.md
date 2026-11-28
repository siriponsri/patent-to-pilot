# Second-jurisdiction decision rule

Main planner (Claude Opus 5.5), 28 November 2026, committed **before** the co-planner's [feasibility comparison](JURISDICTION-FEASIBILITY.md) and the [power simulation](receipts/POWER-SIM.md) report back. The owner delegated the choice among Canada, Japan, China and Thailand/ASEAN to the planner on the condition that the reason survives peer review (decision register, 28 November 2026). Fixing the rule first means the choice cannot be fitted to the results. The rule governs only the prospective power expansion in [POWER-PLAN](POWER-PLAN.md); it never touches C′ or the frozen Track A package.

## Must-have criteria (a jurisdiction failing any one is excluded)

| ID | Criterion | Why a reviewer needs it |
|---|---|---|
| M1 | **Open terms.** Official terms permit automated download, reuse and redistribution of derived records for research, or the data are public domain or under an open licence | Standing rule: all data must be open; the benchmark must be reproducible by others |
| M2 | **Dated events.** Each first generic (or first equivalent market listing) per active ingredient carries an official date | The endpoint must be observable and dated, as in the US first final ANDA approval |
| M3 | **As-of admission.** Archived editions, change logs or record-level dates let the evidence available at a cutoff be reconstructed and proven | Leakage control; the same admission rule as the US Orange Book editions |
| M4 | **Comparable target population.** New active substances can be identified with a dated original approval | Same estimand as the US NCE cohort |

## Ranking criteria (applied to jurisdictions passing M1–M4)

1. **Power gain per unit burden:** simulated H1 and H2 power gain (POWER-SIM) divided by owner and CPU burden per year.
2. **Mechanism coverage:** dated patent and exclusivity or data-protection records, so the graph features (and therefore H2) are testable rather than structurally empty.
3. **Identity effort:** reliable mapping of ingredients to the existing UNII/GSRS keys.
4. **Independence:** events that are not near-copies of US timing (a jurisdiction whose entries mechanically follow a fixed regulatory clock adds less information about the forecasting method).
5. **Thai-context value:** relevance to the Thai and ASEAN users of the product (tie-breaker only).

## Decision

- Include **every** jurisdiction that passes M1–M4 and whose simulated power gain is material (at least +10 percentage points of H2 power at the +5 pp design effect, or a final readout at least two years earlier for the same power) at an owner burden of no more than about one hour per quarter.
- If none qualifies, keep the US-only design and report the H2 power limitation transparently.
- A jurisdiction failing M1 (for example, terms that forbid automated access) is excluded even if it would add many events. Thai and ASEAN records that fail M1–M3 may still support a separate descriptive Thai-context analysis, never a confirmatory test.
- The planner records the decision, the evidence row for each criterion and the rejected alternatives in this file, then asks the co-planner to review it before any OSF update is drafted.
