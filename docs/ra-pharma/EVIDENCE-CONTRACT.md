# Evidence handoff v1

One dossier has an applicant, product, intended market and as-of date. The specialist receiving a statement needs to know whose fact it is, its intended use and where to check it. Use these field names when exchanging records between lanes. An adapter can map an existing Workbench trace to this interface. Store evaluator labels and adjudication outside runtime records.

| Field | Meaning |
|---|---|
| schema_version, dossier_id, item_id | Use `ra-pharma/1` and stable dossier and item identifiers |
| agent, task, statement | Originating specialist (`patent`, `regulatory`, `correspondence`), requested action and the bounded proposition |
| subject_id, evidence_role | Entity described and use of the evidence. Roles include `patent_disclosure`, `claim_limitation`, `applicant_result`, `regulatory_requirement` and `incoming_request` |
| jurisdiction, as_of | Market and date being evaluated. Record unknown explicitly |
| status | `supported`, `missing`, `conflict` or `needs_review` for the stated subject and use |
| sources | Each reference carries source ID, owner or issuing authority, edition, SHA-256 of retained bytes, and exact locator (claim and paragraph, section and page, or page and bounding box for a scan). Preserve source language and keep translations distinguishable |
| depends_on, missing | Upstream item IDs and the specific information still needed; empty lists are allowed |
| trace_id | Resolves to the reading actions, skill and harness versions, model or deterministic implementation, budget and output snapshot |

### Acceptance fixture shared by both lanes

An English patent gives a result for its inventor's example. The fictional incoming letter requests the applicant's product result. With only the patent available, the patent statement can be supported. The separate applicant-result item must be missing or require review. The draft lists the absent report and leaves the assertion unresolved. Add a synthetic, attributable applicant report and the item can be supported from the correct page. Reopen both snapshots after adding the report. Historical values and citations must still resolve.

Repeat with the applicant result already present. Changing the patent claim branch alone must not rewrite a supported assertion about the applicant. A handler must also preserve uncertainty when a jurisdiction, edition, sender authority or attachment is ambiguous. A source locator proves provenance; judging whether the source supports the sentence is a separate check.

The outgoing letter includes only information relevant to the addressee. Its internal review view connects sentence to evidence item, source passage and attachment. FTO assessment, legal applicability and sign-off remain distinct reviewer decisions.
