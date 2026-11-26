# FDA approval-package recovery receipt

**Recovery closed at admission.** The openFDA route matched all three exact product keys. One approval package provided an original-submission product quality lead. Its metadata did not bind the review to the selected later product edition. Zero cases qualify for a two-source pre-score packet. The original overview intake remains three selected and zero admitted. [Original intake](NEXT-SOURCE-INTAKE.md)

The [recovery protocol](ACCESS-RECOVERY-PROTOCOL.md) was committed and verified on origin as `131db60a6b63ad82d5034831df14c50be4d7b64f` before any lookup. This pass used three exact openFDA requests, two FDA-domain index queries and one issuer HTML landing request. All four issuer requests returned HTTP 200. There were zero HEAD or PDF body requests. The prospective request caps and original case order were preserved. This is access and scope evidence. Comparative execution and scores are NOT_RUN. [openFDA Drugs@FDA scope](https://open.fda.gov/apis/drug/drugsfda/)

## Subject and edition audit

Independently matched the product and active ingredient, strength, dosage form and route from each openFDA product entry against the exact pinned `products.txt` row. The Orange Book ZIP and table digests matched the [dossier source pins](ELIQUIS-DOSSIER.md#source-pins-and-rights). The three API records report dataset update 25 November 2026.

| Exact product | Approval and source roles | Disposition |
|---|---|---|
| N/220963/001, row 27,922, EMCITATE 350MCG tablet for oral suspension | ORIG 1 approved 28 September 2026. API lists label ID 87326 and letter ID 87316, both dated 29 September. Exact FDA-domain index query surfaced no approval-package landing. [openFDA exact query](https://api.fda.gov/drug/drugsfda.json?search=application_number%3A%22NDA220963%22&limit=1) | Product and original submission matched. Chemistry/quality source unresolved. |
| N/221109/001, row 23,964, LAMLIQUE EQ 5MG BASE/ML oral suspension | ORIG 1 approved 25 September 2026. API lists label ID 87354 dated 6 October and letter ID 87317 dated 29 September. Exact FDA-domain index query surfaced no approval-package landing. The same application also contains product 002, EQ 25MG BASE/ML. [openFDA exact query](https://api.fda.gov/drug/drugsfda.json?search=application_number%3A%22NDA221109%22&limit=1) | Product and original submission matched. Chemistry/quality source unresolved. Keep the two strengths separate. |
| N/219379/002, row 27,942, GOMEKLI 3MG tablet for oral suspension | openFDA matched exact product 002. The selected archive row records 28 July 2026. API submission history contains ORIG 1 dated 11 February 2025, its label ID 81218 and review IDs 81691/81692 pointing to the same combined NDA 219379/219389 landing page. [openFDA exact query](https://api.fda.gov/drug/drugsfda.json?search=application_number%3A%22NDA219379%22&limit=1) · [FDA original approval package](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2025/219379Orig1s000,219389Orig1s000TOC.html) | Original-submission quality lead recovered. The applicable 2026 submission and the review coverage of the exact 3MG formulation remain unknown. |

The combined GOMEKLI HTML body identifies both application numbers and 11 February 2025 approval at lines 33–35, original submission basename at line 41, and label and chemistry availability flags at lines 47–50. Lines 113–114 enable the displayed Product Quality Review link. Static anchors alone show a loading placeholder. These indicators identify the role of an issuer-linked original package. They say nothing about exact product 002 coverage or the contents of the PDF. The later row's submission ID remains unresolved. Review availability by HEAD was immaterial after the exact-scope gate failed. The additional original multidisciplinary review flag at line 58 provides no formulation-bound quality section.

The prior GOMEKLI overview's web-fetch 400 remains part of the original intake funnel. The API and original package successes here came through a different route. Empty index results for the other two cases leave access unknown and cannot establish absence of review records. The Planner's independent contemporaneous metadata check agreed on the combined GOMEKLI TOC and the 2025/2026 scope gap.

## Metadata manifest and handling

Retained locally under `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-ip-pharma-access-recovery-131db60a/`. Manifest SHA-256 `89b4fff0b43c64d0e59376c29c87296e21d21fb8456b5bbc5b2e6d547c43f39d`. Acquisition receipts carry exact URLs, timing and HTTP metadata with headers limited to provenance fields. The index receipt fixes the exact two discovery queries and their empty result.

| Primary or receipt file | Bytes | SHA-256 |
|---|---:|---|
| `220963-openfda.json` | 2,989 | `be33a07caca4a184780df039baa292f9f143ede3b3a41a58869ccd2bcd27cc83` |
| `221109-openfda.json` | 2,409 | `884f3cea7009954b90065b4001c3f60bed8b15a89d8232e7b7e811ec5a10b113` |
| `219379-openfda.json` | 3,416 | `14b7401bce34f62bbb71444043475631bf77c2d7fdb1b7f256cdbe6d5ea64987` |
| `219379-approval-package.html` | 12,743 | `8f2d7d379c3b171b3fc5cf41419313e08d7ecdf4922b26f2b16bc1492744148d` |
| `openfda-receipts.json` | 1,907 | `a26593a33f4005ec3c032f41cbae95903bddcabc26a9d7ec807aa578adfd2926` |
| `219379-package-receipt.json` | 598 | `54a55a007c95b80da303bf85ec77468d063686ed5720e463652981b3eebef3d5` |
| `index-discovery-receipt.json` | 476 | `406f801206eccb921d6479dd373e3c7b39249bb53715c4be38be5d8889e9bedd` |

Public agency metadata was inspected and retained locally. The record contains source links and derived factual fields. Applicant material and redistribution of linked PDFs would need source-specific review. All three cases are now metadata-exposed. Source content, hidden keys and policy outcomes remain unobserved. Patent family separation and artifact-level use rights would still need independent verification before any research admission. No new candidate set or substitutions followed. If an authorized later review finds an official submission or heading expressly tying a quality review to N/219379/002, the next decision is a separate pre-score packet review under the existing one-open fixed field-aware comparator. [Fixed comparator](NEXT-SOURCE-INTAKE.md#proposed-execution-contract) · [PatentAgentBench](https://arxiv.org/abs/2610.35031) · [Priorbit](https://github.com/Lawless-Inc/priorbit)
