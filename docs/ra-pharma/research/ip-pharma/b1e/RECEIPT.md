# B1E source feasibility under D37

**Execution complete. Planner review pending.** In the fixed 24-group development prefix, 24 exact FDA product keys and 24 original labels were verified. Twenty-two groups had a product-specific quality review from the same original approval edition and a locally usable pair. One review had a confidentiality notice and one did not establish the exact formulation. Each stayed in the denominator. Original B1 remains BLOCKED_FRAME and B2–B4 remain NOT_RUN.

## Authority and preflight

The owner approved [B1E v1.0](https://github.com/siriponsri/patent-to-pilot/blob/b0e7ba42480d5c64e3af8c54ac5e34cbffcccb87/docs/ra-pharma/ip-pharma/B1E-AMENDMENT.md) under [D37](https://github.com/siriponsri/patent-to-pilot/commit/d17e498635122b158bc3ef017353829782ed384c). Research started from clean published revision `f893f4a2a7c5fd5de4afa44950afb91e53da0be3`. Before dispatch, Research verified the raw Git blob hashes, the bytes and SHA-256 of all 14 frozen inputs, selector and fixture hashes, and the four isolated selector tests. The isolated local replay reproduced the ordered prefix byte for byte. The [verification record](verification.json) pins the immutable revisions, timestamps, files, digests and runtime.

| Artifact | Immutable revision | SHA-256 |
|---|---|---|
| Approved protocol | `b0e7ba42480d5c64e3af8c54ac5e34cbffcccb87` | `75fe128312b96321a8d5ed522a1054e88269c7c835b34a43e2a458ebcec0d96b` |
| [Executable lock](https://github.com/siriponsri/patent-to-pilot/blob/5c583343c4c0d75f098c9ed54ea9cf242271a201/docs/ra-pharma/ip-pharma/b1e/lock.json) | `5c583343c4c0d75f098c9ed54ea9cf242271a201` | `de12cefb63ab064b45585328c50fb71daa50da29a5bb3923ec6b6753589ea58e` |
| [Ordered prefix](https://github.com/siriponsri/patent-to-pilot/blob/7d5ef920c9e3058cdb563361b6125606950a1931/docs/ra-pharma/ip-pharma/b1e/prefix.json) | `7d5ef920c9e3058cdb563361b6125606950a1931` | `49b2b80b51224a78f0618529d7e9109312adab57543ed8e94f496582df7ecf88` |

The frozen join covered 936 Orange Book product keys in 496 NDAs and 38 FDA-only product keys. The 936 dispositions were 304 eligible, 15 known overlaps, 15 without a listed grant, 382 outside eligible form or route, 164 outside RX or RLD status, and 56 with unresolved moiety or class. The eligible products formed 171 groups. All 24 selected groups have EXPOSURE_UNKNOWN for historical family overlap. Zero matched a known overlap rule in this prefix. All 24 are exposed development material from selection onward. Neither the listed grants nor the known exclusions establish historical family independence.

## Observed funnel

| Measure | Observed among the fixed 24 |
|---|---:|
| Exact product key, ingredient, strength, form and route matched | 24 |
| Original label verified | 24 |
| Original quality review verified for the exact product | 22 |
| Exact product and edition pair | 22 |
| Locally usable pair for scoped inspection | 22 |
| Local rights unresolved | 1 |
| Document redistribution rights unassessed | 24 |
| Historical patent-family overlap unresolved | 24 |

The [source ledger](source-ledger.json) contains the 24 ranks in locked order, exact keys, original dates and submission numbers, FDA locators, source scope, private retention and rights dispositions. Its attempt slots resolve to the [write-ahead request ledger](requests.jsonl) for URLs, timestamps, issuer, HTTP result, bytes, SHA-256 and private filename. The product checks use the exact product entry inside each FDA application result. The original approval index anchors the edition. Each label match uses the issuer's dosage-forms-and-strengths statement. Each quality match uses the product fields on the cover, review index or scope summary. The GAVRETO original manifest lists the review package and omits a standalone label entry. Its original FDA package link and the label revision supplied edition provenance.

- **Rank 14, QINLOCK.** The FDA quality PDF returned HTTP 200. An express confidentiality and nondisclosure legend on PDF page 2 left local permission uncertain. The collector had already made a private copy and mechanically scanned it before the notice was detected. The copy and scope derivative were discarded. The request hash, byte count, processing cost and rights disposition remain. No marker or scoped finding from that review enters the funnel.
- **Rank 15, FERRIPROX.** The original label covers two distinguishable oral tablet formulations at 1,000 mg. The formulation qualifier in the selected application's quality-review scope table is redacted. This leaves variant-level quality coverage unresolved despite a matching NDA, route, strength and original package. The pair is excluded under the exact-variant reading of the protocol.
- **Rank 18, DOJOLVI.** The letter mapping on the scope table of the quality PDF is garbled in text extraction. A local visual check of the scope table confirmed dosage form, route and 100% w/w strength. No OCR was used. The literal text-layer count carries a garbled-encoding flag.

Public FDA access supported scoped local inspection of the other sources and private research retention. Redistribution is unassessed for the document bodies and cloud use is unauthorized. Sources were assessed only for identity and scope. The machine counted exact printed `(b)(4)` strings in the original selectable text layer of retained PDFs. It reported 0 across 24 labels and 36 across 23 retained quality reviews, including the unresolved rank 15 review. Other spacing, image-only markers and malformed encoding can evade the literal count. Absence of a literal match does not establish absence of redactions. The unavailable rank 14 marker value is NA. [FDA site policy](https://www.fda.gov/about-fda/about-website/website-policies#linking) · [openFDA terms](https://open.fda.gov/terms/)

All 72 optional metadata slots were NOT_CHECKED. The ledger records the reasons separately for other regulators, prosecution and litigation. These slots carry no absence finding. Results apply to this chronological prefix under the frozen caps. It is concentrated in approvals dated January through September 2020. Availability elsewhere, independent patent families, comparative performance and legal clearance were not measured. D36 remains an independent portfolio inquiry.

## Effort, audit and retained material

The journal logged 96 starts and 96 settlements, 24 in each required slot. All returned HTTP 200. Case dispatch ran from 04:02:35 to 04:05:35 UTC. No slot was replayed. The initial parser missed the issuer's JavaScript filename object and padded archive submission types. It completed the metadata and package slots and initiated zero PDF identity requests. The repaired parser used the settled FDA metadata and package files, then filled the untouched PDF slots. The initial rows and runtime were archived privately. The first pass took 33.602 seconds elapsed and 1.234 seconds Python process CPU. The second pass took 126.059 seconds elapsed and 6.203 seconds Python process CPU. PDF extraction accounted for 4.2372 seconds elapsed and 3.5782 seconds CPU within the second pass, including the discarded review's incurred cost. Transfer totaled 130,375,236 payload bytes and 147.432 seconds of request time. Retained response bodies total 129,376,297 bytes across 95 files. Offline ledger verification and generation took 0.193 seconds elapsed and 0.188 seconds CPU in the final run. Human active review time and separate visual rendering effort were not instrumented. New service charges were USD 0, with no model, protected data, OCR or GPU execution.

All listed files reside in the private sibling `ptp-b1e-research-d37-20261127/` under `C:/Users/User/Desktop/myProject/_private_artifacts/`. The published request ledger leaves the rank 14 locator marked disposed and preserves the pre-disposition journal hash. Review can use the retained files with no new requests. The executed collector is provenance for this run. A future release should check scope-page rights notices before retention or marker processing.

| Private audit file | SHA-256 |
|---|---|
| `attempts.jsonl` | `d214c71b6f2272bcf75745a60ba73b885de3ac77f3ce750c5a64884a6a8bdb59` |
| `collector-executed.py` | `578a48e03355d6918d4bd85de72a158da5cb834bb73d81c05519640cfb0a4a5a` |
| `initial-parse.zip` | `81fa345f86b71a03efbf63e82ed8b547eac2e33b22bd23f89b1513f4a2da6c21` |
| `rights-disposition.json` | `52648a005a46ce58c76c7654fb29238154917980c4d7a4843f6bf8e1f20923fd` |
| `15-quality-scope-visual.png` | `e6feb9bde0c6c4cda377e960c01197d85383f765137f6ae92d153c2d1fd4fa39` |
| `18-quality-scope-visual.png` | `10bd3329fd21f62ce116bd5bf3baaf7e4457ecac7a649a0bcd3d0af3256b613c` |
| `build-ledger.py` | `ba7c0960caf1cc459e349d73214aedfe9cef0b2c2f2ff635a9e189923b43c408` |
| `pytest.log` | `1a17b3349ab2808a7c904fba6cc31a24c5cb4158ec6f6e9133045e227a4c4ed4` |

The collector used local Python 3.12, installed requests 2.34.2 (Apache-2.0), Beautiful Soup 4.15.0 (MIT) and PyMuPDF 2.0 (AGPLv3 or commercial license). No dependency was added. Offline checks verified every retained response hash and byte count, all 96 one-start and one-settlement records, all 24 rank identities, and the single disposition. The S4 validation Python and qa-sites ran `python -m pytest -o addopts= -q --tb=short --basetemp C:/Users/User/AppData/Local/Temp/b1eqa1127`. It returned 2,807 passed, 10 skipped, one expected failure and eight standing SACR r2/r3 budget failures in 273.68 seconds, exit 1. The publication target is the commit containing this receipt on `origin/research/ra-pharma`.
