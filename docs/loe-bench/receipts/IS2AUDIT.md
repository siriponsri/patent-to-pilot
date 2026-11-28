# IS2AUDIT main-planner audit receipt

**DONE on 28 November 2026.** The main planner audited both IS2 editions against the co-planner critique and the receipts, and applied every blocker and major fix. The drafts are ready for the KMITL template build. Pagination is unverified until the template renders.

## Inputs

- Drafts at `6f803c57`: [English](../../writing/is2/mwd/IS2-DRAFT-EN.md) and [Thai](../../writing/is2/mwd/IS2-DRAFT-TH.md).
- Co-planner critique (GPT-6.2 Astra high, 28 November 2026). Verdict: revise before final audit. The confirmatory numbers and decisions were correct in both editions. It found two blockers, three major issues and one minor group.
- Sources of every number: [SCORE](SCORE.md), [SCORELLM](SCORELLM.md), [FREEZE](FREEZE.md), [C2](C2.md), [C3b](C3b.md), [C4b](C4b.md), [EVP](EVP.md) and [UIBUILD](UIBUILD.md). The planner rechecked each new figure against its receipt table.

## Changes

| Critique item | Disposition |
| --- | --- |
| B1. SCORELLM still reported as pending | New Table 1 gives C′ recall for B1, M1, M3, L1 and L1e at both horizons. §4.3 reports the paired L1e − M3 and L1e − L1 contrasts with intervals, 9,898 schema-valid forecasts, and the single-checkpoint and pretraining-exposure limits. |
| B2. Figure 1 says the test is pending | Both Figure 1 artworks now say "Sealed test (C′): H1 passed". The unbuilt "swappable models (OpenAPI · MCP)" footer was replaced with the decision-support notice. The figures were re-rendered at 3000×1620 and embedded. Figure 2 is embedded, and its caption now gives the event-drug counts (development 67 and 90, C′ 202 at each horizon). |
| M3. Lead with the measured decision | The abstracts and the opening paragraph lead with the assumed capacity, the US approval endpoint, the H1 result and M1 at 65.49%. §4.1 reports C′ before development. H3 is described as descriptive because H2 stopped testing. M1 − B1 is reported with intervals and without a causal reading. The cutoff table moved into §3.2 prose. |
| M4. Scoring lock and amendments | §3.4 describes updates 1–3, their times relative to the 05:12 UTC gate, and that C′ was scored under updates 1–2. §3.2 names the specific prior exposures. |
| M5. Evidence roles and placeholders | C3 Methods cover both the 2013 development cutoff and the 2017–2023 C′ cutoffs. The Track A placeholder is now a dated disposition. The dossier placeholder now reports the C8 audit (1,789/1,789 traceable, 1,757 hash-backed, source integrity only) and the EVP yields (C6 3/5, C7 17/17, Thai status 0/6). |
| m6. References and front matter | [2] cites the program listing without an empirical claim. [30] lists the DOI's deposited creator. [31] is pinned to `3e06537b`. The price ratio is 46.5%. The duplicate Paper 53 sentence was removed. Per D5, the English byline reads "Tuchsanai Ploysuwan", with the title only in footnote 2. Per D6, an AI-use acknowledgment was added. |

Abstract lengths are 190 English words and 246 Thai tokens (PyThaiNLP newmm). The Thai abstract now carries the US-prioritization conclusion. README and `docs/assets/market-window-flow.svg` were brought up to date with the C′ result, the OSF DOI and the product status.

## Limitations and next action

- The English text from §1 to the references is about 4,900 words including tables, so a ten-page overrun is a real risk. The KMITL template build decides it. If it overruns, move Table 4 (development LLM) and the development paragraphs into a short appendix or the IS2 report.
- Track A and C9 results remain pending in the text by design.
- **Next:** build the KMITL docx (TH and EN) with the kmitl-is-paper skill, check pagination and caption placement, then make the IS2 slides.
