# Pharmaceutical patent examples

These six Thai reading presets use three US patent application publications. The reader follows two explicit claim references per question, opens the cited English, and compares the conditions on the two branches. The three complete publications contain 98 numbered claims in total. The offline packet indexes the 15 selected claims across the three documents. It belongs exclusively to the product demonstration pool.

| Publication | Original claims | Offline claims | Two reading paths | Printed page and PDF locator |
|---|---:|---|---|---|
| [Taste masked pharmaceutical formulations, US20120276199A1](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/20120276199#page=17), 1 November 2012 | 36 | 1, 2, 15, 17, 18 | `pharma-15` follows 15 → 2 → 1 to identify the antiadherent. `pharma-18` follows 18 → 17 → 1 to distinguish the permitted diluents. | Printed p. 11, PDF p. 17. The last claim is on PDF p. 18. |
| [Dry powder inhaler, US20120145150A1](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/20120145150#page=27), 14 June 2012 | 30 | 1, 9, 10, 11 | `inhaler-10` and `inhaler-11` both inherit the second chamber from claim 9. Claim 10 directs flow from both chambers to the outlet channel. Claim 11 adds a second outlet and assigns an outlet to each chamber. | Printed p. 10, PDF p. 27. The last claim is on PDF p. 28. |
| [Child-resistant medicament package, US20070289893A1](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/20070289893#page=6), 20 December 2007 | 32 | 1, 2, 3, 7, 8, 9 | `blister-3` follows 3 → 2 → 1 and `blister-9` follows 9 → 8 → 7. Both specify a cut ending short of an edge. The parent claims identify different layers through which it extends. | Printed p. 3, PDF p. 6. The last claim is on PDF p. 7. |

## Source verification and replay

The original edition for each case is the A1 publication shown above. We compared the numbered claims, selected wording, physical page and direct parent references against the official page images. Every transcript had all integers from 1 to its printed last claim in order. Separate identifiers distinguish the three publications and the six questions. All Thai glosses are editorial descriptions of the selected passage. Reading the three claim numbers gives the user the dependency path within the displayed scope.

The packaged canonical text joins the selected complete numbered claims in numeric order with a single LF between them. Text comes from the corresponding numbered claim elements in the public HTML transcript with whitespace runs collapsed. Line-layout hyphenation from the printed page is removed. Each excerpt is a contiguous substring of the canonical text, identified by Unicode offsets and a separate SHA-256. The gloss of an independent claim describes only the elements asked about. The other conditions remain visible in the linked original.

| Family | Canonical text SHA-256 | Public transcript |
|---|---|---|
| `demo-en-pharma` | `6626d72834cbe26024855c4e018c8a2b1a90b0914313cf465ae9d1502019440c` | [US20120276199A1 claims](https://patents.google.com/patent/US20120276199A1/en#claims) |
| `demo-en-inhaler` | `6ca02af1ebf946e76e2f96f58d020aa56374a477be4c2d548fc6f624d2578a55` | [US20120145150A1 claims](https://patents.google.com/patent/US20120145150A1/en#claims) |
| `demo-en-blister` | `f3e34dd622bdaae88bcab4aa984ccabbe689563b6cdf28bedfb09cc5f87a4a29` | [US20070289893A1 claims](https://patents.google.com/patent/US20070289893A1/en#claims) |

## Use and attribution

The USPTO describes patent text and drawings as typically free of copyright restrictions subject to specified exceptions. We checked the three complete publication transcripts for a copyright notice, reserved-rights phrase, copyright symbol or mask-work notice and reviewed the selected claim pages. These checks found no such notice or third-party material in the selected claims. On this basis the packet permits local download and inspection, redistributes the selected publication text and allows quotation, JSON export and the project's own Thai explanations. Its redistribution decision covers this text only. The source HTML, site branding, drawings, tables and original PDFs stay outside the shipped packet. Patent exclusivity and claim validity are separate legal questions. [USPTO website terms of use](https://www.uspto.gov/terms-use-uspto-websites)

The [source ledger](S2-sources.json) records URLs, byte lengths, UTC fetch times and SHA-256 for each original. Its `pharma_uspto_terms` record preserves the terms reviewed for all three. The official PDFs were downloaded on 25 November 2026 under `pharma_pdf`, `inhaler_pdf` and `blister_pdf`. The matching `*_claims` records identify the HTML transcriptions. Original URLs and hashes travel with each saved run. The source audit used public HTTP and existing local libraries.
