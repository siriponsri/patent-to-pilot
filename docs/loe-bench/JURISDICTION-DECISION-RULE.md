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

## Interim decision (planner, 28 November 2026, after the feasibility comparison)

Applied against the rule above using [JURISDICTION-FEASIBILITY](JURISDICTION-FEASIBILITY.md). Final inclusion still needs the measured counts (JURIS-COUNT) and the power simulation.

| Jurisdiction | M1 open terms | M2 dated events | M3 as-of | M4 new-substance cohort | Mechanism coverage (H2) | Interim status |
|---|---|---|---|---|---|---|
| **Canada** | Likely (federal open data); exact licence text to verify | NOC decisions dated | Register of Innovative Drugs includes expired entries; Patent Register CSV; legacy NOC files | Innovative drug register identifies new medicinal ingredients | **Strong:** dated patent register and data-protection (six-year no-file) dates, the closest analogue to the Orange Book | **Primary candidate** |
| **Japan** | MHLW/PMDA terms to verify | NHI price-list amendments carry effective dates | Dated amendments; PMDA fiscal-year lists | PMDA flags 新有効成分含有医薬品 (new active ingredient) | **Weak:** no open, dated product-to-patent crosswalk; re-examination terms only case by case | **Secondary candidate:** adds events for H1, little graph information for H2 |
| China | **Fails:** open item-level licence unverified | Proposals, not verified decisions | Unverified | Unclear | Patent-linkage platform since 2021, no open archive found | **Excluded** (M1) |
| Thailand | **Fails:** DIP licence "other"; automated access blocked (EVP 403/timeouts) | Partial | Unverified | Partial | Unverified | **Excluded from confirmatory**; descriptive Thai-context work only |
| Singapore | Open register under the Singapore Open Data Licence, but HSA site terms require permission for decision lists | Approval dates | Unverified | **Fails** in the open register (no application class) | Unverified | **Excluded for now** |
| Malaysia | CC BY 4.0 (NPRA) | Registration dates; renewals must be separated | Preview contains future-dated rows; unverified | Data-exclusivity register exists | Partial | **Excluded from confirmatory** (about 1.3 first generics per year in a sampled study, immaterial power); descriptive ASEAN context possible |

**Reason a reviewer can check.** The expansion exists to give H2 (the graph increment) power. H2 is only testable where dated patent and exclusivity or data-protection evidence exists, because the graph states are built from it. Canada publishes both registers with dates, so Canadian origins add information to H2 as well as H1. Japan adds first-generic events for H1 but, without an open patent crosswalk, its graph features would be largely empty, so it cannot raise H2 power much. China and the ASEAN registries fail the open-terms or as-of criteria, which the benchmark needs for reproducibility and leakage control.

**Next.** JURIS-COUNT measures, for Canada and Japan, the licence text, archived editions and unique eligible first-generic events per year over three complete years after removing US-duplicated moiety sets. The final decision follows the rule's materiality test with POWER-SIM rerun on the measured rates.
