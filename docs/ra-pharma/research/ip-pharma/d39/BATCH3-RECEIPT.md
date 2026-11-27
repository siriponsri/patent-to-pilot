# D39 Batch 3 · Public biosimilar document readiness

**BLOCKED_FRAME, 27 November 2026 Asia/Bangkok.** No ordered prefix was established. Candidate enrollment, detail retrieval and assessments are NOT_RUN. There are zero promoted leads and no screened denominator.

## Question and authority

A Thai CMC lead would use the public record to decide whether to request an attributable comparison or route an existing comparison to qualified review. The incumbent is the D38 manual guidance checklist, beginning with the exact product, reference, edition and source locator. Lee et al., Figure 5, is the protocol's contextual primary example of product-specific applicability. No candidate-specific publication was assessed. [D38 checklist and comparison](../d38/COMPARISON.md) · [Lee et al.](https://pubmed.ncbi.nlm.nih.gov/29469653/)

The [Planner release](https://github.com/siriponsri/patent-to-pilot/blob/7f53bea8a46aa3ce518870382761a78e00fe35ce/docs/ra-pharma/ip-pharma/D39-DECISION-REQUEST.md#batch-2-independent-disposition-and-batch-3-release) authorizes Batch 3 against research revision `ddd3c5c7a03d016c3cde9e2639c88c844b3c58b7` and [LOCK.json](LOCK.json). The checked-out protocol SHA-256 matched the lock and both files matched that revision. Live origin main and research were verified before access. The [protocol](PROTOCOL.md#source-frame-snapshot-and-order) allows two frame slots and requires a uniquely identified edition and an explicitly linked reference that can be grouped by proper name and reference BLA before any detail lookup.

## Frame preflight

| Source ID and scope | Exact locator | Observation and effect |
|---|---|---|
| PB-LIST, US FDA Purple Book public listing, viewed 27 November | [Download Purple Book Data](https://purplebooksearch.fda.gov/downloads), introductory description and Current Year | The listing describes a full product section in each monthly report and displays CSVs through October 2026. October is the latest visible edition. The listing does not designate one canonical full-search export, and the lock does not define a choice among several full monthly sections. The October file was inspected as a frame diagnostic. Listing bytes unretained, integrity UNVERIFIED. |
| PB-OCT-2026, US FDA October 2026 Monthly Historical Data Changes Report, viewed 27 November | [October 2026 CSV](https://www.accessdata.fda.gov/drugsatfda_docs/PurpleBook/2026/purplebook-search-October-data-download.csv), CSV record 1 and headers at logical records 4 and 20, one-based | Both 28-column headers contain BLA Number, Proper Name, License Type, Approval Date, Submission Type, Ref. Product Proper Name and Ref. Product Proprietary Name. Neither header includes a reference BLA field. BLA Number identifies the row's application. The two reference fields identify names. No FDA-defined in-file rule binding those names to a reference BLA was established under the lock. A name-based cross-row join and its treatment of conflicting or repeated identities were never frozen or tested. |

The public CSV returned HTTP 200 with Last-Modified `Wed, 28 Oct 2026 13:02:35 GMT`. SHA-256 computed from the received 487,133 bytes was `f688373c4f1fd274fbfad55d2f7228d00dcea54672f2f17348c5c107ab9fadf1`. Standard-library Python decoded UTF-8 with BOM handling and parsed 2,276 logical CSV records of 28 fields each, including headings and both report sections. These are file dimensions. Only schema metadata is retained in Git. The raw response was inspected in memory and discarded. Independent byte verification requires the issuer to return the same snapshot. [Frame record](BATCH3-PREFIX.json)

The frame stopped before approval-date eligibility, grouping, exclusions or ordering. No substitution, name-based enrollment, or product-level query followed. Thai NDI ingredient and biosimilar checks, exact US pair verification, label and original review-package checks, and literature checks are all NOT_RUN. Thai registration, local applicability, US pairs for any eligible prefix, and applicant dossier availability remain unknown.

## Manual comparator and future design

The manual checklist has no attributable pair to review. The frame stop leaves the source packet, missing witness for a specific applicant, and next scientific reviewer undefined. The D38 historical tie remains separate. A matched manual comparison, operator evaluation, ChatGPT, NotebookLM, local AI integration and differentiation are NOT_RUN.

For any separately released design, retain distinct fields for source-frame status, reference-link witness, jurisdiction and original review edition. A matched task can measure whether a workflow requests an authoritative binding when the input contains named reference fields and an unbound BLA. Lock the same bytes, allowed joins, expected action, evidence locator and reviewer roles before evaluation. Keep frame failures separate from dossier-readiness errors and from the scored case denominator.

## Access and cost

Two logical frame accesses. The browser's text extractor rejected the CSV's binary media type. The one recovery attempt used a byte-capable client on the same link. This was a client-format recovery, recorded as a retry and a deviation from the protocol's transient-failure retry wording. Three deliberate source attempts including the recovery, with additional listing find and context operations on the same web result. The web backend's HTTP traffic, response bytes and redirect count are unknown. One direct HTTP request was observed, with no final URL change. The directly observed CSV transfer took 1.109 seconds. No detail access. Incremental service charges USD 0. Labor and tool overhead were unmeasured. [Access ledger](BATCH3-ACCESSES.jsonl)

Documentation and schema metadata only. Code suite NOT_RUN. Planner owns independent disposition of the blocked frame and any future release.
