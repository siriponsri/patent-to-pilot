# Decision Twin review and B1 dispatch • 27 November 2026

## Release

APPROVED_B1 under D35. The owner package is local to the Product checkout. All 40 listed files matched manifest SHA-256 508955eb8027d506ecbe449e55e25627131d7d1c1bbf21d2aa4fc7c620d6c606. The live starting heads were main 0a709f06, research 58855f6e and product b690f9f9. Product remains held on Claude Opus 5.5 medium.

Research Executor (GPT 6.2 Sol medium) owns the B1 receipt under docs/ra-pharma/research/ip-pharma/b1/ on research/ra-pharma. This commit freezes the preflight instructions. Verify both ZIPs under the shared private artifact root, without case lookup:

| Dataset and permitted use | Private path and SHA-256 |
|---|---|
| FDA original submission metadata, local join of ORIG approval date; ZIP tables dated November 24, publisher update November 25 | ptp-b1-frame-20261127/drugsatfda.zip / b5f97ad97d5ac78437dcb305808f9f8e1a6caee7983904d96f85adadbd13269f |
| Orange Book November 13 snapshot, exact N/application/product, RX and listed patent | ptp-ip-pharma-landscape-20261126/orange-book.zip / d4dbc9d85df4fbd78c5e448f130a55b05054f529d2054a46df10735437792241 |

[Drugs@FDA table definitions](https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files) and [Orange Book fields](https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files) describe issuer metadata. Local metadata processing only. Register source-specific terms, provenance, digest and locator. External transfer and redistribution permissions remain UNKNOWN.

Before selecting, verify a dated local family crosswalk and exposed-family exclusions. The two verified ZIPs provide no general patent-family identifier. Check permissible project artifacts and public bulk metadata provenance for recoverable mappings without querying candidate matters. Return BLOCKED_FRAME under DT-06 if the exclusion boundary cannot be pinned. A grant number or a drug name alone cannot establish family independence. If recoverable, publish the complete executable selector and hashed lock for Planner verification before the first lookup. Initial lock covers original prescription oral small-molecule NDAs in 2020–2024. Join on the exact product. Group transitively by shared active moiety, NDA or family. Exclude the six registered ingredients including combinations, ELIQUIS and known project/demo families, and NDA 220963, 221109 and 219379 and aliases. Sort group representatives by earliest original date, numeric NDA then product ascending. Retain first 24 distinct groups, never backfill. Pin oral-form vocabulary, small-molecule evidence, aliases and all input and code hashes prospectively.

Per selected group allow one metadata request, one package page, one identity check per required source. Limit human inspection to cover, index or scope. Require exact strength/form and edition for original label and product quality review. Limit optional checks to one metadata-only query each for other regulator, prosecution and public litigation. Preserve all failures and ambiguous matches. Log bytes processed, machine and human time, access and rights separately. New service charge limit USD 0. Use DT-06 receipt, prefix, source-rights, marker, optional-source and funnel specifications. Marker scan is machine-only, no reconstruction; absent text layer is NA. Claim shape is descriptive only, cap at 12 with truncation flagged. No question creation, keys, protected TEST or evaluation. Fewer than four admitted ends the batch; 4–11 permits descriptive engineering; 12 or more permits a separate B2 proposal. Before selection these branches have no denominator.

## Re-audit and contract

Local rerun with python -B -m unittest test_engine passed 22 authored tests in 1.370 s. The exact mixed-tree implementation caps unknown leaves at 11. Twelve unknowns in an AND at q=.5 yield probability 1/4096 even with every field missing. Low verdict entropy measures uncertainty under the model's assumptions. A supervised dossier still needs source-supported product facts. One planner-choice assertion accepts its own first-ranked action on unequal costs. Real decision quality and calibration remain UNKNOWN.

DESIGN_ONLY. Map claim nodes to claim_limitation and observations to subject-specific evidence roles in ra-pharma/1. Link a missing element to depends_on, missing and trace_id. Preserve source owner, edition, hash, locator and jurisdiction. Leave disputed interpretation for qualified review. Proposed action and certificate schemas extend the review workflow only after versioned interface acceptance. Thai rendering follows approved assertions. Product integration, an experiment proposal and execution are separate decisions.

Keep the field-aware checklist as A, heading selector as B and entropy per cost as C. A later equal-access experiment needs identical question and heading bytes, one-open caps and symmetric charging of all full-text sidecar preprocessing, or a separate marker diagnostic. Report mixed-tree overflow explicitly with checklist fallback under a future freeze. Decision-region acquisition already has a primary algorithm, and MolPatent-240 already benchmarks molecular patent assessment. Evaluating decision-relevant gaps with qualified reviewers and matched total cost is a hypothesis. No head-to-head or priority finding follows from the 331-title discovery inventory; the full inventory is absent from this package. [Javdani et al., decision regions](https://proceedings.mlr.press/v33/javdani14.html) · [Shi et al., PatentFinder and MolPatent-240](https://arxiv.org/abs/2412.07819v2)

Historical evidence stays scoped to its original receipt. ELIQUIS is exposed. The last fresh batch selected three, admitted zero and scored zero at 58855f6e. The fictional local Product demo and the cached 45/45 single-grant ancestry check supply engineering evidence. Paper 53 known-family exposure, the eight IS1 NOT_RUN cells and the Thai correspondence nulls retain their original denominators. B2–B4 and all new model comparisons are NOT_RUN.

## Independent source checks after dispatch

The original SciSpace ZIP was located in the owner's Downloads folder. SHA-256 a4a345f2ae86f00ad42db8ff01ce989803e3b33be306ba381ff475cf443ee867, 65 members. All 13 references/scispace files matched the corresponding ZIP bytes. Six historical Markdown records also matched the applicable main or Research checkout after newline normalization. The original combined_search_results_r3.csv (38af24b59e6ab9c179abd85daffa7893ed0d75e6a7c603a0547a2d9827f027ce) has 331 rows and 331 distinct nonempty trimmed lowercase titles, with 97 missing DOI, 85 missing PDF link and 26 missing publication year. First aggregation failed on an assumed Title header; rerun used Paper Title and Publication Year. This verifies inventory counts only.

| External primary source and comparator | Scope relevant to Decision Twin |
|---|---|
| [Hu et al., PatentAgentBench v2](https://arxiv.org/abs/2610.35031v2) | 510 tasks across eight suites include claim charting and open-ended FTO search. The proposed one-open dossier endpoint isolates a narrower decision. |
| [Wang et al., PatEx-Gym v1](https://arxiv.org/abs/2610.33503v1) | Iterative prior-art discovery and office-action assessment motivate measuring retrieval trajectory separately from final output. |
| [Koomullil, hybrid AI and Lean v1](https://arxiv.org/abs/2604.18882v1) | The coverage proof conditions on supplied match scores. Evidence certificates in PTP likewise require independent checks on source interpretation. |
| [Craig et al., Andromeda 2 v1](https://arxiv.org/abs/2609.19099v1) | The paper compares formulation outcomes under a matched experimental budget. A PTP evidence request would require its own operator and proposal-quality evaluation. |

Comparisons above are based on the authors' published abstracts. No external benchmark instances or protected labels were inspected. New service charges for Planner acquisition were USD 0. The archived FDA download was 6,122,502 bytes. Full PTP pytest was NOT_RUN for this documentation change.
