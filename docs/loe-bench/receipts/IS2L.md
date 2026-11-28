# IS2L: Condensed bilingual literature review

- **Status** DRAFT_READY_FOR_MAIN_PLANNER_AUDIT
- **Branch** `loe/IS2L`
- **Base** `4410cb1e621904a8f588d374bf42f7a47e415a66` from `origin/research/loe-bench`

## Changes and evidence

Section 2 now covers regulatory endpoints and dated evidence, approved applicants and price scenarios, the Thai evidence hand-off, and the fixed-capacity evaluation question. Both manuscripts cite one IEEE list in the same first-appearance order. The iSAI-NLP program supports the identity of the authors’ Paper 53.

RQ1 uses native scores before deferral. Its ordered development contrasts are M3–B1 at 24 months (+9.80 pp), M3–M1 at 24 months (+5.49 pp), and M3–B1 at 12 months (+13.00 pp). The H2 interval includes zero. C3b reports +25.60 pp at the single 2013 development cutoff using 24-month scores for the 36-month approved applicant endpoint. C4b reports increased reimbursement error on the retrospectively mapped rows after the price adjustment. C2 changed the evidence and prompt together between L1 and L1e. [FREEZE](FREEZE.md#development-results) · [C3b](C3b.md#c3-development-queue-result) · [C4b](C4b.md) · [C2](C2.md#development-results)

The Thai prose uses the requested terms for active-moiety set, endpoint timing, approved applicant counts and the cutoff date. Removing the RL catalogue also removes the Wikipedia example. The existing English and Thai Figure 2 PNGs are embedded in §4.1 at the former marker.

| Evidence file and locator | Revision | SHA-256 |
| --- | --- | --- |
| [SciSpace source](../../writing/is2/mwd/source/LITERATURE-REVIEW-IS2.scispace.md), parts A, B and D | `4410cb1e` | `6fac3f32b0105fd5c987633fd44f3365b2b6368bd68477645624abcccfc6a140` |
| [Figure 2 EN](../../writing/is2/mwd/figures/fig2_effects_en.png), §4.1 marker | `3bee8355` | `833cc21763f9684ba1aca4ad8ff5e9899a6b7a223f81575e51f39c8f8b2c6039` |
| [Figure 2 TH](../../writing/is2/mwd/figures/fig2_effects_th.png), §4.1 marker | `3bee8355` | `ebb63dc847263218a8f80d6877a4fe0ebaabecb32669272d110b0252b667da76` |

## Reference map

Each row shows the final manuscript number and the corresponding numbers in the prior draft and the SciSpace source. A dash indicates a work added to the paper. A shared row indicates deduplication.

| Final | Prior draft | SciSpace | Work |
| ---: | ---: | ---: | --- |
| 1 | 1 | 42 | Srihangpiboon and Ploysuwan, iSAI-NLP Paper 53 |
| 2 | — | 1 | Beall et al., patent-based entry approximation |
| 3 | 4 | 3 | Beall et al., biosimilar versus generic onset |
| 4 | — | 4 | Kerr and Glos, effective market exclusivity |
| 5 | 2 | 6 | Hu et al., first ANDA submission |
| 6 | 3 | 7 | Hopefl et al., first orphan-drug ANDA submission |
| 7 | 5 | 8 | Chahal et al., FDA marketing follow-up |
| 8 | 6 | 9 | Hemphill and Sampat, patent challenges |
| 9 | 7 | 10 | Kannappan et al., 30-month stay and entry |
| 10 | — | 11 | Durvasula et al., historical Orange Book reconstruction |
| 11 | 8 | 12 | Rai et al., court and agency data resource |
| 12 | — | 13 | Scott Morton, empirical firm entry decisions |
| 13 | 9 | 14 | Reiffen and Ward, generic industry dynamics |
| 14 | — | 15 | Hollis, Canadian relative unit share |
| 15 | 10 | 16 | Conrad and Lutter, FDA AMP ratios |
| 16 | 11 | 17 | Nikolopoulos et al., dispensing forecasts |
| 17 | 12 | 19 | Trippe, WIPO patent landscape guidelines |
| 18 | 13 | 20 | WIPO, public-domain search guide |
| 19 | — | 21 | Hu et al., PatentAgentBench |
| 20 | 14 | 39 | Leela and Kessomboon, Thai examination interviews |
| 21 | — | 40 | Vachanavuttivong et al., historical Thai timelines |
| 22 | 16 | 24 | Paleka et al., ICLR 2026 |
| 23 | — | 25 | He et al., chronologically consistent LLMs, JFE |
| 24 | 17 | 26 | Karger et al., ForecastBench, ICLR 2025 |
| 25 | — | 32 | van den Akker et al., secondary-data preregistration |
| 26 | 18 | 35 | Traub et al., selective classification, NeurIPS |
| 27 | 19 | 37 | Field and Welsh, cluster bootstrap |
| 28 | 20 | 38 | FDA, October 2022 multiple-endpoints guidance |
| 29 | 21 | 28 | Turtel et al., November 2025 TMLR |

### Additions and cuts

- Added SciSpace [1], [4] and [11] to ground patent-based approximations, approval timing and historical Orange Book reconstruction, respectively.
- Added SciSpace [13] and [15] for firms’ empirical entry decisions and Canadian relative generic units as measures distinct from approved applicants.
- Added SciSpace [21] and [40] for patent-task benchmark design and dated Thai examination context. The two Thai time figures identify their different start dates.
- Added SciSpace [25] and [32] for chronological training-data controls and documenting analyses of secondary data in advance.
- Cut prior-draft [15] (ASEAN IP Register) as a standalone literature citation. The Thai source inventory remains the provenance for the dossier’s regional discovery workflow.
- Cut SciSpace [2], [5] and [18]. The bibliographic-only companion study, South Korean cohort and general commentary were outside the condensed endpoint and price discussion.
- Cut SciSpace [22] and [23]. PatentAgentBench supplies the patent-task comparison. The optional IPBench entry and narrow BERT application were omitted.
- Cut SciSpace [27], [33], [34] and [36] to focus on dated forecasts, secondary-data preregistration, coverage and clustered uncertainty.
- Cut SciSpace [29]–[31]. C9 has one literature sentence, tied to the published Turtel et al. article.
- Cut SciSpace [41]. The cited statistic counts utility-model applications by applicant origin and cannot establish Thai office-level pendency.
- Kept published versions of Paleka, He, Karger, Traub and Turtel. OpenReview’s browser challenge on the Paleka and Turtel forum links was resolved with the official ICLR proceedings record and the published TMLR PDF. The Meta-Psychology publisher PDF supplied the full first-author initials where the DOI open failed. Scott Morton’s DOI redirect could not be opened during the check. The bibliography retains the confirmed DOI and pagination from the brief.

## Word counts and verification

Body counts cover prose and captions in §§1–5. Section and abstract counts exclude headings. All counts omit table cells, keywords, citation and link markup, figure alt text and editorial placeholders. English uses whitespace-delimited tokens containing a letter or number. Thai uses the Thai word segmentation in Node’s `Intl.Segmenter`. Each edition carries both abstracts.

| Draft | Section 2 | Total body | Thai abstract | English abstract | References |
| --- | ---: | ---: | ---: | ---: | ---: |
| [EN](../../writing/is2/mwd/IS2-DRAFT-EN.md) | 753 | 3,428 | 243 | 178 | 29 |
| [TH](../../writing/is2/mwd/IS2-DRAFT-TH.md) | 1,196 | 5,106 | 244 | 178 | 29 |

- **PASS** Whole-paper first-appearance numbering, shared bibliography, unique reference titles and cross-language citation parity.
- **PASS** Relative link targets, embedded PNG signatures, Thai terminology scan, pending-marker inventory and `git diff --check`.
- **NOT_RUN** Research analyses and the Python test suite. This card changes Markdown only.

## Remaining placeholders and hand-off

- §3.4 OSF registration DOI.
- §4.1 blinded C′ admission verdict and disposition.
- §4.1 C′ H1–H3 estimates, intervals, practical-usefulness checks and ordered decisions, subject to admission.
- §4.1 Track A timestamped prediction freeze and prospective outcome readouts.
- §4.3 claim-level traceability audit of the dossier.

The main planner owns final editorial and evidence review, paper layout, and integration of this receipt into the lane handoff and memory. Registration, release and audits follow their respective protocols.
