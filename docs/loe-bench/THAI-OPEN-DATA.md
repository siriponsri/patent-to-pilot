# Thai open-data feasibility for the LOE-Bench Thai-context demo (task E5)

Executor E5, branch `loe/E5`, retrieval date 27 November 2026. All probes ran from the owner's Windows PC, anonymously, with default HTTP and no login. Scope: can open Thai data support a per-ingredient demo that sits beside the US triage output? Test ingredients: apixaban and rituximab. Sample files are outside Git; hashes are in the [receipt](receipts/E5.md).

## 1. What the RA Pharma lane already verified

| Fact | Source file |
|---|---|
| Two Thai FDA NDI detail pages for rituximab biosimilars (TRUXIMA 1C 1/61(NBS), REDDITUX 1C 2/62(NBS)) were read earlier, registry as of 30 June 2568 BE. Fields seen: registration number, product, form, strength, TMT. | [d36/EVIDENCE.md](../ra-pharma/research/ip-pharma/d36/EVIDENCE.md) rows M3a, M3b |
| The Thai DIP patent search form returned 403 to web fetch for apixaban (WO2019204193), so no Thai patent status was established. | [ELIQUIS-DOSSIER.md](../ra-pharma/research/ip-pharma/ELIQUIS-DOSSIER.md) |
| NDI timed out twice during setup and eight plan codes stayed BLOCKED for exact regulator classification. Hospital plan PDFs (item code, price per vial) and the NHSO annual report (people per drug) are readable. | [d39/BATCH4-RECEIPT.md](../ra-pharma/research/ip-pharma/d39/BATCH4-RECEIPT.md), [d39/PROTOCOL.md](../ra-pharma/research/ip-pharma/d39/PROTOCOL.md) |

This task reproduces the NDI and DIP failures from a fresh request and adds the data.go.th catalogue findings below.

## 2. Source table

Ratings: GREEN = bulk or API, usable now. AMBER = usable with manual steps, or stale or unverified. RED = not machine-accessible.

| Source | URL | Access mode (observed) | Terms on automated use | Relevant fields | Generics / biosimilars | Rating |
|---|---|---|---|---|---|---|
| Thai FDA NDI drug search | `ndi.fda.moph.go.th/drug_info`, `/drug_detail/index/?rcno=…` | Web form and detail pages only. Connection timed out after about 21 s (HTTP code 000), repeated on the detail URL, as in D39. | No terms page retrieved. Treated as unknown. | Registration no., product, form, strength, TMT (earlier lane) | Yes, all registered products. The two biologics seen carry an `NBS` suffix. | **RED** from this PC |
| data.go.th FDA drug datasets | `data.go.th/api/3/action/package_search` (CKAN API, HTTP 200) | API and CSV/XLSX | Per-dataset licence field. The FDA licensee lists are "Open Data Common". | Only licensee name lists (`drug-manufacturing-licensee`, `drug-import-licensee`, `drug-sale-licensee`) and FDA aggregate import and production value (`report-import-drug`, `report-manufacture-drug`). Searches for ทะเบียนตำรับยา and "drug registration" found no product-level registration dataset. | No product-level data | **RED** for registration status, AMBER for importer or holder names |
| DIP patent search | `patentsearch.ipthailand.go.th` | Web form. HTTP 403 to a scripted request (also in D39). | Not retrieved. Not bypassed. | Application no., filing, publication, status | Not drug-specific | **RED** |
| DIP open dataset "ข้อมูลสิทธิบัตรการประดิษฐ์" (`dip_01070101`, data.go.th, modified 2026-08-25) | Records are hosted at `exchange.ipthailand.go.th`, a JavaScript app behind a Cloudflare challenge. data.go.th lists only the data dictionary XLSX. | No bulk file reachable | Licence field "อื่นๆ" (other), unspecified | The dictionary lists ApplicationNumber, ApplicationDate, PatentNumber, ExpiryDate, Title, Claim, Abstract, CurrentStatusCode and date, Applicant, IPCClasses, PCTApplicationNumber, PriorityApplicationNumber | Not drug-specific. An IPC A61K filter could narrow it if the data were obtainable. | **AMBER**: best route to Thai patent status and expiry, but not downloadable anonymously today. Needs owner action (account or request). |
| DIP statistics datasets (`dip_010302` and similar) | CKAN, CSV/JSON/XML per month | API | Open Data Common | Aggregate counts | No | Not useful per ingredient |
| NLEM on data.go.th (`item_64a59021-…`, FDA publisher) | XLS download, HTTP 200, 483,328 bytes | Bulk XLS | Creative Commons Attributions | English drug names. The workbook was last saved 16 Oct 2013 (BIFF format, filename `…edit16-10-56`). | Names only. Searching the file found `Paracetamol`, `Warfarin`, `Enoxaparin`, and not `apixaban`, `rituximab`, `trastuzumab`. | **AMBER**: open and parseable, but a 2013 edition cannot give 2026 status for newer drugs. The current NLEM edition was not located. |
| Reference prices on data.go.th (`item_ff313a7a-…`, "ราคากลางยา แผนปัจจุบัน") | XLSX, HTTP 200, 12,253 bytes | Bulk XLSX | Creative Commons Attributions | The retrieved workbook holds herbal items (ยาประคบสมุนไพร, ยาขมิ้นชัน and similar), so it does not match its modern-drugs title. | Not for the target ingredients | **RED** for apixaban and rituximab |
| DMSIC (`dmsic.moph.go.th`, HTTP 200) | The menu lists "ราคากลาง ยา", "ราคาอ้างอิงจัดซื้อปกติ ยา" and "ราคาอ้างอิงต่างประเทศ ยา" | Search pages. Their URLs and terms were not retrieved. | Unknown | Reference price per drug (menu text only) | Unknown | **AMBER, unverified**: the right source for price, not tested |
| e-GP via Thailand Government Spending (`egp-contact-2568`, modified 2026-11-06) | CSV parts of roughly 0.5 to 0.6 GB each, and a REST API that needs a free API key | Bulk CSV. Anonymous download works (first 4 MB retrieved). | Creative Commons Attributions | Project ID, project title, agency, method, announce date, budget, reference price, agreed price, winner, contract dates | Project level only, no item or generic name. Drug rows need free-text title search. The 4 MB head (about 2,800 rows, mostly construction) had zero hits for apixaban or rituximab. That is not evidence of absence. | **AMBER** |
| GPO (`gpo.or.th`, HTTP 200) | Marketing site. data.go.th holds only pharmacy-shop datasets. | None for product data | n/a | None found | n/a | **RED** |
| Hospital procurement plan PDFs and NHSO annual report | See the D39 files above | PDF, manual reading | Public documents, reuse rights unknown | Item code, quantity, unit price, people served | Yes, by brand | **AMBER** (manual, per ingredient) |

## 3. Samples retrieved

For both test ingredients, no registry or patent sample could be retrieved anonymously. The saved files are infrastructure evidence: search JSON, the NLEM 2013 XLS, the price XLSX, the DIP data dictionary and the e-GP 4 MB head. No apixaban or rituximab row was found in any of them. The only Thai records for the test ingredients are the two NDI rituximab pages recorded earlier by the RA Pharma lane, which E5 could not re-fetch. Hashes are in the receipt.

## 4. Recommended minimal Thai-context demo

For each ingredient triaged by the US model, show four columns. State each cell's evidence state in the Kleene vocabulary (known, unknown, not applicable) and use an explicit "evidence needed" label where data is missing.

1. **Thai registration**: a deep link to the NDI detail page plus a one-line manual extract (registration number, holder, strength), prepared by hand for 5 to 10 demo ingredients. Do not scrape.
2. **Thai patent**: a link to the DIP search plus the US family identifier (for apixaban, WO2019204193 from the earlier dossier). Status stays "evidence needed" unless the DIP dataset becomes obtainable.
3. **NLEM**: use the 2013 open XLS only as a historical flag labelled with its edition date, or link the current list manually.
4. **Reference price and procurement**: a DMSIC link and, optionally, an e-GP title search over the CC-BY CSVs.

This design keeps abstention visible, which fits the abstention-aware method in the [program plan](PLAN.md). Owner actions that would upgrade it: (a) a network path that reaches NDI, (b) a DIP exchange account or written data request, (c) the current NLEM and DMSIC price files.

## 5. Main gaps

- No anonymous machine route to Thai registration status or Thai patent status, the two items the demo most needs.
- The open NLEM and reference-price files on data.go.th are stale or mislabelled.
- e-GP has no item-level generic name, so linking spend to an ingredient is text matching.
- Terms of automated access for NDI, DIP and DMSIC were not retrieved. Unknown is treated as not permitted.

## 6. External references (D32)

E5 did not open either source below. Both come from the [program plan](PLAN.md) and remain external references, not head-to-head results.

- Paper: [first-ANDA prediction, CPT 2019](https://doi.org/10.1002/cpt.1479). It supports the US triage the demo builds on and gives no Thai evidence.
- Competitor: DrugPatentWatch generic-entry prediction (vendor, named in the plan). It is the product workflow the demo would be compared against. Its coverage of Thailand was not checked.
