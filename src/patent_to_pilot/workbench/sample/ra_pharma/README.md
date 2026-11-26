# RA Pharma demo pack

This pack feeds the **แฟ้มทะเบียนยา** tab of the local Workbench. It holds one fictional dossier, `RA-TH-2026-0001`, for a taste-masked orally disintegrating tablet. The applicant, product, people, letters and test results are invented. Short public excerpts supply the patent claims, an inventor example, the ASEAN quality requirement and the Thai letter-format rule. [`pack.json`](pack.json) pins every excerpt and file by SHA-256; the loader refuses a changed byte.

## Contents and rights

| Item | Origin | Use in the demo | Rights basis |
|---|---|---|---|
| `docs/*.pdf` (five files) | Authored for this demo, built by [`examples/ra_pharma/build_fixtures.py`](../../../../../examples/ra_pharma/build_fixtures.py) | Incoming authority letter, incoming company letter, applicant formulation record, dissolution report editions 1.0 and 1.1 | Fictional fixtures under the same CC0 dedication as the [sample folder](../LICENSE.md). Each page carries a fictional-document footer |
| Emblem on `incoming-authority-rfi.pdf` | Drawn by the build script | Placed where Thai government paper prints the Garuda, 30 mm high at the top centre | A neutral outline. It is not the state emblem |
| US20120276199A1 claims 1, 2, 15, 17 and 18 | Reused from the S4 reader bundle (`pharma-15`) | Claim-element chart | [S2 rights record](../../../../../docs/evidence-scope/receipts/S2-pharma-source.md) |
| US20120276199A1 paragraphs [0245]–[0250] and the Table 2 row at 30 | Google Patents transcript, transcript SHA-256 `191334ca…6309`; checked against the USPTO page image, printed page 10 (PDF page 16) | Inventor example result that must not replace the applicant result | USPTO patent text; extends the S2 decision to this short description excerpt and one table row |
| ACTR & ACTD on Quality, P 5.4, Thai (PDF pp. 46–47) and English (PDF pp. 78–79) | Thai FDA Medicines Regulation Division page and scanned PDF, SHA-256 `4b27779a…f8e8`, retrieved 26 November 2026 | Registration requirement in two languages | Short attributed quotation. Manually transcribed from page images; the 130 MB scan is not redistributed |
| Office of the Prime Minister Saraban Regulation 2526, clauses 11, 71 and 75 | Royal Gazette edition of 23 September 2548, SHA-256 `d63a601b…8765` | Template rule: the Garuda paper belongs to government senders | Thai regulation text, short attributed quotation. Later amendments were not checked |
| `dev/inhaler-dev.json` | US20120145150A1 paragraph [0109] and Table 1 row; fictional applicant reports | Separate development family for skill tests | USPTO patent text (S2 record for this publication) plus fictional fixtures |
| `dev/expected.json` | Product lane evaluator labels | Read only by `skill_eval.py` | Project-authored |

The Workbench serves the Sarabun font from [`../../fonts/`](../../fonts/OFL.txt) under the SIL Open Font License 1.1 and embeds it in exported DOCX files.

## Rebuilding the fixture PDFs

Run `python examples/ra_pharma/build_fixtures.py` with Pillow, Playwright and a local Chromium. Chromium writes a creation date, so every rebuild changes the bytes. Copy the printed digests into `pack.json` and rerun `tests/ra_pharma_product`. Thai mark composition is switched off in the fixture stylesheet so the PDF text layer keeps each tone mark; see the [product memory](../../../../../docs/ra-pharma/product/MEMORY.md).
