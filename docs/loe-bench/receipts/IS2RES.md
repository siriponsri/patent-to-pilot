# IS2RES | C′ results in the bilingual IS2 drafts

Draft complete for co-planner critique and main-planner audit. Branch `loe/IS2RES` was cut from fetched `origin/research/loe-bench` at `35e123a3404fbfadae1e7eaf6f47bb32fb0bb3d9`. The dedicated checkout was clean at intake and no concurrent edit of the card paths was observed.

## Changes

- Updated the identical bilingual abstracts in the [English edition](../../writing/is2/mwd/IS2-DRAFT-EN.md) and [Thai edition](../../writing/is2/mwd/IS2-DRAFT-TH.md). Updated methods and captions to reflect the completed C′ run, with Track A on its separate prospective schedule.
- Kept development results in their own block in §4.1. Added C′ panel counts, arm recall, the ordered H1–H3 decision table, secondary M1 − B1 comparisons and the failed secondary M3 auto-clear check. The table marks the H3 estimate, interval and lower quantile as descriptive because H2 stopped the sequence.
- Placed the exploratory C′ C3 result next to the single-cutoff development result in §4.2. Recorded C4 on reserved origins as NOT_RUN and retained the Medicaid development results.
- Rewrote §5 around the confirmed H1 gain and the unconfirmed graph increment in H2. The secondary M1 comparison suggests that dated evidence accounts for most of the observed gain. The conclusion retains the approval endpoint, source and linkage limits, the commercial-data gap and the pending prospective replication.
- Updated the [figure and table plan](../../writing/is2/mwd/FIGURE-TABLE-PLAN.md) with all six estimates and intervals for the two-series Figure 2, and with zero and +10-point reference lines. Assigned the new C′ table number 2 and renumbered the existing reimbursement and language-model tables to 3 and 4. Left placement markers for the planner to embed the refreshed Figure 1 and rendered Figure 2. The existing Figure 1 artwork still displays the old C′ status, and the existing Figure 2 assets depict only development data.

## Numbers and sources

The confirmed historical scoring summary is the [SCORE aggregate JSON](../../../loe-bench/data/SCORE_CPRIME_RESULTS.json) with verified LF-normalized SHA-256 `38f65240b57a4662349d3bdc89fd026908d888bdb2cfcb1ed63f430ed845d932`. Percentages and percentage-point differences use the precision in the receipts.

| Text or plot | Values used | Receipt and aggregate locator |
| --- | --- | --- |
| Release and protocol | Scored 28 November 2026. OSF 10.17605/OSF.IO/P2SMD with approved updates 1 and 2. Blinded gate PASS. No registered inference deviation. Review budget 20%. | [GATE](GATE.md), [SCORE execution protocol](SCORE.md#execution-protocol) and [handoff](SCORE.md#deviations-and-handoff). JSON `release`, `deviations`. |
| C′ cohorts | 24 months, 2017–2024, 4,639 rows, 368 event rows, 202 distinct event drugs. 12 months, 2017–2025, 5,259 rows, 202 event rows, 202 distinct event drugs. | [SCORE primary family](SCORE.md#primary-family). JSON `horizons.24`, `horizons.12`. |
| C′ H1 | 24 months, M3 − B1 +20.37 pp [+14.37, +26.16], one-sided lower +14.37. PASS. Point meets +10 pp. | [SCORE primary family](SCORE.md#primary-family). JSON `primary.H1`. |
| C′ H2 | 24 months, M3 − M1 +1.36 pp [−2.20, +3.01], one-sided lower −2.20. FAIL. Point falls below +10 pp. | [SCORE primary family](SCORE.md#primary-family). JSON `primary.H2`. |
| C′ H3 | 12 months, M3 − B1 +16.69 pp [+9.98, +24.21], lower quantile +9.98. NOT_REACHED_DESCRIPTIVE. Point meets +10 pp. | [SCORE primary family](SCORE.md#primary-family). JSON `primary.H3`. |
| C′ arm recall | B1, M1 and M3 at 24 months 46.48%, 65.49%, 66.85%. At 12 months 50.64%, 67.82%, 67.33%. M1 − B1 +19.01 and +17.18 pp, respectively. M3 auto-clear FAIL at both horizons. | [SCORE secondary analyses](SCORE.md#secondary-analyses). JSON `horizons` level, contrast and policy results. |
| C′ C3 | At least three approved applicants within 36 months, 2017–2023 cutoffs. 173 known-positive rows from 92 event drugs and four unknown rows. M3 79.8%, B1 49.7%, +30.11 pp [+20.16, +36.86]. Snapshot-sponsor sensitivity +30.16 pp. | [SCORE C3](SCORE.md#c3--competition-at-launch). JSON `C3.primary`, `C3.sensitivity`. |
| Reserved C4 | Origins from 2017 onward NOT_RUN. The first reserved origin requires the missing pinned 2018 outcome payload. | [SCORE C4](SCORE.md#c4--medicaid-demand-and-reimbursement). JSON `C4`. |
| Development Figure 2 series | H1 +9.80 pp [+0.14, +19.65] and H2 +5.49 pp [−2.00, +11.25], both 67 event drugs. H3 +13.00 pp [+3.27, +23.17], 90 event drugs. | [FREEZE development results](FREEZE.md#development-results). |
| Retained development comparisons | C3 single-cutoff result, mapped Medicaid MAE, and evidence-matched language-model scores. | [C3b](C3b.md#c3-development-queue-result), [C4b](C4b.md), [C2](C2.md#development-results). |

## Verification

| Check | Disposition | Evidence |
| --- | --- | --- |
| Abstract length and layout | PASS | In each edition the English abstract is one paragraph with 179 whitespace-delimited words (`len(text.split())`). The Thai abstract is one paragraph with 235 tokens under PyThaiNLP 5.4.0 (`word_tokenize(text, engine="newmm", keep_whitespace=False)`). Counted the final body text, excluding headings and keywords, with the existing project virtual environment. Each count is at most 250. Abstract text matches across editions. |
| Numbers and local links | PASS | Checked cohort counts, C′ recall, contrast signs, exact interval endpoints, one-sided bounds, sequence decisions, C3 estimates, C4 status and six Figure 2 entries against the receipts and aggregate JSON. Repository links and their Markdown anchors resolved. |
| OSF lookup | PASS with fallback | The web lookup could not open the DOI or update endpoints. Direct requests to the public OSF API returned the registration and both expected response IDs. Approval and inference procedure are sourced to the verified SCORE receipt. |
| Scope | PASS | Documentation-only edits in the four assigned paths. Existing bibliography retained. No protected test data or private per-row outputs accessed. No scoring rerun, runtime code changes or paid execution. |
| Root pytest | NOT_RUN | Documentation-only card. The repository requires pytest before code commits. |

## Remaining work

- §4.1 retains the placeholder for the timestamped Track A freeze and matured outcome readouts.
- §4.3 retains the dossier claim-level audit and exploratory C′ L1/L1e (SCORELLM) placeholders. The optional GRPO/SFT training and outcomes retain NOT_RUN in the drafts.
- The main planner owns the Figure 1 artwork refresh, Figure 2 rendering, final layout and integration. The co-planner critique and main-planner audit are pending. This receipt is the executor handoff and memory record for IS2RES.
