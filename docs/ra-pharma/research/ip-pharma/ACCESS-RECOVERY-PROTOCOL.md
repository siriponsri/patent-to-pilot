# FDA approval-package metadata recovery

**Independent recovery iteration, prospectively frozen in Git before network access.** The [original intake result](NEXT-SOURCE-INTAKE.md) remains three selected and zero admitted. Recovery revisits only these keys, in the original order, using the exact Orange Book snapshot and row locators in that receipt.

| Key | Selected product and approval in the pinned snapshot |
|---|---|
| N/220963/001 | EMCITATE, tiratricol, 350MCG, tablet for oral suspension, 28 September 2026 |
| N/221109/001 | LAMLIQUE, lamotrigine hemifumarate, EQ 5MG BASE/ML, oral suspension, 25 September 2026 |
| N/219379/002 | GOMEKLI, mirdametinib, 3MG, oral suspension presentation, 28 July 2026. Read the exact dosage-form string from the pinned row during local audit. |

## Same recovery route for each key

1. Issue one official openFDA Drugs@FDA JSON request using `application_number:"NDA<application number>"` and `limit=1`. Cap response bytes at 1 MiB and the request at 20 seconds. Match application number, exact `product_number`, name, strength, dosage form, route and application/submission history. Use only product and approval-document metadata. Preserve failures or index lag.
2. Use one supplementary metadata view. If the openFDA response explicitly links an FDA approval-package landing page matching the application, choose that link. Otherwise use one FDA-domain index discovery query for the exact product name and NDA plus “Drug Approval Package” on `accessdata.fda.gov/drugsatfda_docs/nda/`. Use only the index's URL and heading to locate a matching issuer HTML landing page. Never open a PDF from search. If multiple matching landing URLs are surfaced, prefer the exact selected approval submission/date if explicitly identifiable, then ascending URL; otherwise inspect the first exact-NDA landing URL in ascending URL order. Get at most one such landing page, with the same 1 MiB/20 second cap. Keep index evidence and acquisition errors even if no landing page resolves.
3. From exact issuer-linked records, retain a label and an explicitly named chemistry, product quality, or integrated review with an identifiable quality section. Prefer metadata tied to the exact selected approval submission, then exact subject coverage expressly shown by issuer metadata and latest eligible release date, then ascending URL. For the selected review only, allow one HEAD request, 20 seconds, with no PDF body read. Record status, headers and final URL. A denied HEAD or unresolved scope remains unknown.

Allow no guessed document links, no further queries, no PDF bodies, no recovery of redactions, no material submission data entry and no replacement cases. Confirm the review's submission identity and subject from issuer metadata. An earlier review for a different form or strength, application-level review title alone, or an unverified quality section does not bind to the exact product. An integrated review can be offered after explicit evidence of its quality scope and exact formulation binding. Keep product, submission, document type and scope ambiguity separate from link existence. Future receipts can propose subject review by an independent evaluator only within a separate released scope.

Preserve metadata captures outside Git with SHA-256, response details, exact source URLs and dates. Record role, subject, edition, rights and exposure per case. FDA data are public metadata for local audit. Linked applicant materials and downstream use require separate rights checks. If none qualify, close recovery at admission. For any qualified case send the manifest and scope review before releasing a packet. No candidate execution, scoring or exposure of evaluation keys in this iteration.

The comparator remains exact product-key join, cached claim walk and field-aware checklist with one extra source open. PatentAgentBench compares known-patent retrieval, and Priorbit is a US patent/FTO workflow comparator. [Original comparator contract](NEXT-SOURCE-INTAKE.md#proposed-execution-contract) · [PatentAgentBench](https://arxiv.org/abs/2610.35031) · [Priorbit](https://github.com/Lawless-Inc/priorbit)
