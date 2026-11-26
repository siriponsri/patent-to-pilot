# Natural registry metadata feasibility

**Product–artifact metadata pairing observed. Natural adaptive evaluation NOT_RUN.** The publicly indexed national registry exposes stable product-level identifiers, audience categories and dated artifact listings. The inspected pairing would make a useful source-binding check. It supplies neither an applicant-facing question and response pair nor an independently validated choice under uncertainty.

## Bounded public checks on 26 November 2026

| Source and exact locator | Observation | Disposition |
|---|---|---|
| [Data.go.th dataset](https://data.go.th/th/dataset/web-service-drug-reg), [CKAN package](https://data.go.th/api/3/action/package_show?id=web-service-drug-reg), package `40d470c5-d2c0-49c0-8b80-f7e742f4b270`, resource `edaf236b-8311-43ea-b4d6-cc2d46b8e3d7` | Direct HTTP 200 for catalogue and package. Metadata modification 2 August 2024. Public dataset, licence explicitly unspecified, no active datastore. Resource points to Thai FDA SOAP help, with no flat public export indicated. | Catalogue access establishes discovery, with no dataset licence or proof of query execution. |
| [Thai FDA operation help](https://porta.fda.moph.go.th/FDA_SEARCH_ALL/WS_LICENSE_SEARCH.asmx?op=GET_DATA_DRUG) and [WSDL](https://porta.fda.moph.go.th/FDA_SEARCH_ALL/WS_LICENSE_SEARCH.asmx?WSDL) | Direct HTTP 200 for both documentation surfaces. GET_DATA_DRUG accepts opaque `DATAS` string and returns a generic XML data set. No field-level bounded query syntax, audience, version or product-artifact join in the schema. | No service data request. Do not submit an unknown `DATAS` payload. Product row access or permitted export via this API remains unestablished. |
| [NDI public enumeration](https://ndi.fda.moph.go.th/drug_info_corporation/char/N/460), row NORMAPRO | The publicly indexed registry's alphabetical lookup enumerates one specific registration, `1C 15114/65(B)`, with separate public and healthcare professional audience entries. | An independently enumerable metadata lookup. No applicant question is attached to the row. |
| [Product-specific NORMAPRO record](https://ndi.fda.moph.go.th/drug_detail/index/?rcno=6515114&rctype=1C&register=MUMgMTUxMTQvNjUoQik%3D), `rcno=6515114` | Same registration. The official product page lists the label, PIL and SPC as separate artifacts all displaying 1 August 2022 as approval date, with public and physician roles on PIL and SPC respectively. Registration snapshot line says 30 June 2025. | Exact registration + audience + displayed date identifies one listed artifact for either leaflet role. This is the product-specific metadata binding. The approval dates are as displayed on the artifacts, with no inference about the original registration or a filing amendment. |
| [Second product-specific record](https://ndi.fda.moph.go.th/drug_detail/index/?rcno=6515082&rctype=1C&register=MUMgMTUwODIvNjUoTkJDKQ%3D%3D), `rcno=6515082` | Separate registration `1C 15082/65(NBC)`. Carton and vial label entries have displayed approval dates. Public and professional leaflet rows explicitly have no approval date. | Observe the missing dates and keep them unknown. An exact current-version lookup cannot derive a date for these two artifacts. |
| [NDI unkeyed detail route](https://ndi.fda.moph.go.th/drug_detail/index/) | Indexed response includes blank product fields and many unrelated document names. Direct trial timed out. | Excluded as a key. Aggregated links do not bind a product. |

NDI item evidence is from open, publicly indexed official page views. Direct standalone HTTPS tests to the product pair, the public enumeration and additional ordinary detail routes timed out in the same bounded attempt. This is evidence of discoverability and displayed pairing, with direct reacquisition unresolved. Public item pages carry a reserved-rights footer. The [Thai FDA website policy](https://www.fda.moph.go.th/website-policy/) and portal's unspecified licence establish no open reuse licence for PDFs or data export. No artifact body, credentialed THAIRIMS record, hidden evaluation report or dataset export was accessed. The product identifiers listed here name the observed public records. They do not become method-selection or held inputs.

| Retained public documentation response | Bytes | SHA-256 |
|---|---:|---|
| CKAN package metadata | 7,585 | `c26df04fa4bf2a217abf50d80ff0aabfaa145a5ca3827a22390fc8c36ca4100b` |
| National portal dataset page | 99,383 | `f7fb47cee161e8fc6c4571765006cda62a2fa1ba22093579e677520458d6ed0b` |
| SOAP operation help, same bytes via HTTP and HTTPS | 6,192 | `4f89f4b93b74129ab452dab143fe2587a4f058bb79f9131042709bf29819de2f` |
| WSDL | 40,177 | `4cd7ec8a699f8bf70590601fd228e1b4757e89257ce251c7e3b175f99985242d` |

Successful direct responses are retained locally under `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-thai-registry-preflight-20261126/`. Read requests timed out on the NDI direct route and were checked against separately indexed official item and enumeration routes. No repeated original, candidate trial, bulk download, model or scoring was performed.

## Decision boundary

On the fully populated example, opening the product-specific page discloses audience, date and artifact names at the same time. An exact composite lookup can therefore resolve the visible metadata query in one source read. The same source supplies both fields and key. This is source binding. It does not test which action to take under incomplete information, and it does not reproduce an applicant dossier or question. On the missing-date example, the real first observation is informative about what is absent. It offers no independent witness that could resolve the missing version. Neither example provides an admissible natural sample of competing branches with a separately checkable answer.

The smallest missing input for an architecture measurement is a rights-cleared independently enumerated case with a genuine competing next action and an independent artifact or filing-version key. To test applicant correspondence specifically, the question or request, confirmed applicant, round/sequence, outgoing audience and supporting attachment must be paired independently of the worker. No such packet, reuse permission or exact release was demonstrated. Stop at metadata feasibility. R4 remains NOT_RUN.

## Historical OCS correspondence source binding

**PASS for one exposed source-binding check.** The Office of the Council of State (OCS) publishes Opinion No. `344/2532`, an August 1989 memorandum on medical-device labelling under the statute identified in its heading. The memorandum records a Ministry of Public Health inquiry, letter `0701/2205` dated 24 May 1989, and contains the Council's historical response. The verified artifact is the Council's memorandum. The standalone inbound letter was not independently retrieved. [Official OCS PDF](https://comment.ocs.go.th/main/download/dlf/pdf/%E0%B9%80%E0%B8%A3%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B8%87%E0%B9%80%E0%B8%AA%E0%B8%A3%E0%B9%87%E0%B8%88%E0%B8%97%E0%B8%B5%E0%B9%88%20%E0%B9%93%E0%B9%94%E0%B9%94-%E0%B9%92%E0%B9%95%E0%B9%93%E0%B9%92)

A direct HTTPS fetch on 26 November 2026 returned HTTP 200 and `application/pdf`. The 229,581-byte, four-page file matched the independent review's SHA-256 `16bb3ed114f6a93d5596183ef421a51c6c9f5d5052315f93e3abde822b834c7a`. The Executor visually checked the first page rendered from those bytes against its embedded text. Both show the opinion number and letter reference above. The local source and page-1 heading render are under `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-ocs-344-2532-20261126/`. The heading render SHA-256 is `ad78dc56996002ecbd14512942bf2aafe8ce51522c2a53d257d5a86193980e68`. Use the canonical PDF for page locators and source identity.

| Evidence item | PDF locator, counting from the first page |
|---|---|
| Opinion identity and historical subject | Page 1, upper-right case-number heading and centered memorandum title |
| Requesting agency, recipient, letter ID and date | Page 1, opening paragraph immediately below the memorandum title |
| Ministry inquiry and cited positions | Page 1, the two issue paragraphs, continuing to page 2 in the paragraph immediately before the Council panel introduces its opinion |
| Response issuer and disposition location | Page 2, main-body paragraph introducing Law Drafting Committee No. 4, continuing through the main body on pages 3–4. Page 4 closing signature block identifies OCS and dates the memorandum August 1989. |

An earlier independent review recorded `345/2532` and `0310/2205` in a web-rendered transcription for the same URL. The current web rendering agrees with the directly verified PDF, so that discrepancy was not reproduced in this check. Its cause is unknown. The example supports a narrow engineering check that cites the original page before trusting a derived transcription of routing identifiers.

This is an interagency legal inquiry and historical response. It adds an exposed source-binding example separately from the missing applicant filing and supporting attachment. It supplies no measure of domain accuracy, no evidence of current legal applicability or applicant-specific support, and no legal, medical or FTO recommendation. An official-correspondence endpoint would require a separate owner decision and prospective design. No experiment or scoring was started. R4 remains `NOT_RUN`.
