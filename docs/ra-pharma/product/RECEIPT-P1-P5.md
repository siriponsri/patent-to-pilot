# Product receipt · P1–P5 local RA Pharma dossier

Product lane, `product/ra-pharma`, based on `2085e4be` (no later origin commits at start). Session runtime: the owner requested Claude Sonnet 5.5 medium; this session ran as Claude Opus 5.5 in the same client, which is recorded here as a deviation for the Planner. Windows 11, CPython 3.12. Completed 26 November 2026.

**Disposition: local engineering demonstration READY_FOR_REVIEW.** One fictional dossier runs end to end on the normal Windows launcher. `product_readiness` is a local alpha for one operator. `method_evidence` is none: the skill correction is an engineering loop on authored fixtures, not a measured transfer result. `publication_readiness` is outside this task. External usability, legal suitability, regulatory acceptance and time savings are NOT_RUN.

The [owner walkthrough](../../../examples/ra_pharma/README.md) gives the exact clicks. The [pack record](../../../src/patent_to_pilot/workbench/sample/ra_pharma/README.md) lists every source, digest and rights basis.

## Tasks

| Task | Result | Evidence |
|---|---|---|
| P1 Open the dossier | PASS | Dossier `RA-TH-2026-0001` (applicant, product, TH market, as-of 2026-11-26) in [`pack.json`](../../../src/patent_to_pilot/workbench/sample/ra_pharma/pack.json). New tab **แฟ้มทะเบียนยา** on the existing launcher and SQLite store. Applicant facts come from applicant documents; patent examples stay separate items. One build produces the claim chart, checklist and reply together |
| P2 Read the patent | PASS, FTO open | US20120276199A1 claims reused from the S4 bundle (same digest). Ten curated elements across branches 15 → 2 → 1 and 18 → 17 → 1, each with a claim offset and an applicant-record citation. Branch 15 is `needs_review` (two construction questions, including a deterministic molar calculation that flips by counting molecules or protons); branch 18 is `does_not_meet` pending review. Publication kind A1, US jurisdiction, legal status and family unchecked. Thai FTO is `needs_review` with three listed checks |
| P3 Registration checklist | PASS, applicability open | ACTD P 5.4 in Thai (PDF pp. 46–47) and English (pp. 78–79) from the Thai FDA ACTR/ACTD page, transcribed from the scan. Recorded as technical guidance, not a binding provision. The generic-product cross-reference to P 3.4 and the 2550 compilation versus the July 2006 Thai footer are kept as review notes. Coverage table: TH demo, ASEAN reference only, US patent publication only, other countries not covered. Applicant result and the CoA attachment are separate items |
| P4 Correspondence | PASS | The layout reader (pypdf text layer and drawing operations) finds number, sender block, Buddhist-era date, subject, salutation, reference, enclosures, numbered requests, closing, signer and position with page coordinates. It reports a 30 mm top-centre image as matching OPM Saraban Regulation clauses 71.1 and 75, and keeps emblem identity, missing signature image and absent enclosure as uncertain. The emblem in the fixture is a placeholder. The licensor letter is classified as a company letter. Template choice follows the actual sender: the applicant company never receives the Garuda template. Output is editable in the UI, stored as revisions, and exported as DOCX (Sarabun embedded) and print HTML |
| P5 Learning and handoff | PASS | Skill `evidence-role-reader` 1.0.0 takes the patent's 96% as the applicant result. The operator rejection produces 1.1.0 (parent 1.0.0, spec SHA-256 recorded). On the separate inhaler development family plus two dossier regressions, 1.1.0 has 0 errors against 5 for 1.0.0 and no regressions. Promotion requires a passing evaluation. Snapshots built with 1.0.0 replay identically after promotion |

## Acceptance fixture from the evidence contract

| Contract behaviour | Observed |
|---|---|
| Patent only: patent statement supported, applicant item missing, draft lists the absent report | `patent.example-6` supported as `patent_disclosure`; `reg.R-P54.applicant-result` missing with the patent candidate rejected and its reason; reply paragraph 1 says the report will follow |
| Add an attributable applicant report: supported from the correct page | 91% from `applicant-dissolution-report-1.0`, PDF page 2, quote `30 นาที: ร้อยละการละลายเฉลี่ย 91` |
| Reopen both snapshots | Both reverify: all citations resolve to stored bytes, and a rebuild from stored inputs reproduces the content hash |
| Changing the claim branch alone does not rewrite the applicant assertion | Branch 15 → 18 changes only `patent.*` items; the applicant item hash and the letter are unchanged |
| Ambiguous edition and missing attachment preserve uncertainty | Reports 1.0 and 1.1 together give `conflict` and a blocking letter sentence until the operator chooses; the CoA stays missing after any report |
| The outgoing letter carries only addressee-relevant content; the internal view connects sentence, item, passage and attachment | The reply never contains the patent number or the 96%. Each letter block lists its item IDs; each item opens its page text with the quote highlighted and a PDF page link |

## Who did what

| Action | Kind |
|---|---|
| Pack verification, letter layout reading, template selection, claim comparison and arithmetic, evidence-role assignment, requirement mapping, letter drafting, snapshot diff and replay | Deterministic code (`ra-pharma-dossier/1.0.0`, `thai-letter-layout/1.0.0`, `evidence-role-reader/<version>`) |
| Claim-element decomposition, element status and the Thai glosses in the pack | Authored by the product lane for review; not computed |
| Edition choice, skill correction, promotion, letter edits, signature and issuance | Operator |
| Model-assisted steps | None. Every snapshot records `model_calls: 0` and `paid_calls: 0` |

## Verification

| Check | Command or route | Result |
|---|---|---|
| Product tests | `python -m pytest tests/ra_pharma_product -o addopts=` (QA venv, Chromium 1228) | 15 passed: 14 engine tests and the browser walkthrough through `scripts/ptp_run.py --serve`, with every non-loopback request blocked (none observed), restart, `--backup` and serving the restored copy |
| Workbench regressions | Existing UI, scope reader, G01, G02, P4 suites | 130 passed after one fix: the G01 oracle guard reads each `static/*` entry as text, so the fonts moved to `workbench/fonts/` |
| Normal launcher | `Start-PTP.cmd --data-dir <fresh> --port 18931` with `PTP_NO_BROWSER=1` | Served by the repository `.venv` (pypdf 6.21.4); catalog, build, Sarabun font (`font/ttf`, 90,220 bytes) and DOCX download (attachment) responded. Doctor exit 0; smoke 15/15 |
| Scripted walkthrough with rendering | `examples/ra_pharma/walkthrough.py <out> --render` | Exit 0. Replays 1, 2, 3 and 6 all matched. HTML print (Chromium) and DOCX (LibreOffice) each rendered one A4 page with embedded Sarabun and the operator's edited number |
| Full repository gate | `python -m pytest -o addopts= -q --tb=short --basetemp %TEMP%\rp1` with `PYTHONPATH=<S4 qa-sites>` | GATE_RESULT |

Evidence is in `../_private_artifacts/ptp-ra-product-20261126/`: `walkthrough-r1/summary.json` (`0548f4f7…7636`), `reply.docx` (`223ff3e3…f0`), `reply-html.pdf` (`d5dab29b…601d`), `docx-render/reply.pdf` (`d71310af…8326`), `launcher-r1/` doctor and smoke logs, `qa-full-r1/pytest.log`, and the source captures in `sources/`.

## Tools and installs

No package was installed. Existing tools used: pypdf 6.21.4 (runtime, already a project extra), Playwright 1.60 with Chromium 149 revision 1228 and Pillow (fixture build and QA only), LibreOffice (render check only). Added asset: Sarabun Regular and Bold from `google/fonts` `ofl/sarabun` at commit `e774067705989f0bcb5e32eb0e8f76c24d679f92`, SIL OFL 1.1, SHA-256 `226d4f36…b2f1` (Regular), `d38308ca…83b9` (Bold), `b26cae13…ad60` (OFL.txt). Purpose: Thai rendering of fixtures, the UI letter sheet and embedded DOCX fonts. No network access at runtime. Smoke: served at `/fonts/…`, loaded by Chromium (`document.fonts.check`), embedded by LibreOffice.

## Limitations

- The layout reader is tuned to text-layer PDFs with this letter structure. Scanned letters, multi-page letters and handwritten stamps are untested. Text width is not measured; positions are line anchors.
- Thai text extraction needed two repairs, NUL glyph maps and decomposed SARA AM. Fixtures disable Thai mark composition; a real PDF that uses composed glyphs may still lose tone marks.
- ACTD excerpts are manual transcriptions of a scanned PDF. The OPM regulation edition predates later amendments.
- One applicant, one product, one jurisdiction profile and one skill task. The development family is small and authored by the same lane; it shows the loop works, not that the rule generalises.
- Claim elements and their statuses are authored, not derived. No Thai patent search or US legal-status check was performed.
- The reply uses Arabic numerals and Sarabun 14 pt. Some Thai line breaks fall at word boundaries chosen by each renderer; Word was not used for rendering.
- The runtime model deviated from the requested Sonnet 5.5 medium; see the opening paragraph.

## Next actions

1. Planner: review the evidence interface use (`ra-pharma/1` items, `content_sha256`, `trace_id` as `snapshot:index`) and decide whether `content_sha256` and `occurrence` join the shared contract.
2. Planner: integrate the product branch and add a root README link to the walkthrough (root navigation is Planner-owned).
3. Product: add an operator upload path for applicant PDFs and a second jurisdiction profile with its own official sources.
