# ELIQUIS SPRINKLE evidence dossier

**Phase 1 PASS for replayable US evidence. Thai family member, national claim text and dated status are UNKNOWN.** This exposed portfolio dossier connects the pinned FDA product and listing to the verified grant ancestors, then maps publicly documented product facts to individual claim features. Independent reconstruction used the source bytes rather than the older pilot output or the second reader's transcription. [Planner report and graph at 2b4188e1](https://github.com/siriponsri/patent-to-pilot/tree/2b4188e1/docs/ra-pharma/ip-pharma)

## Product and grant

| Source and exact locator | Verified observation |
|---|---|
| Orange Book ZIP, `products.txt` line 9,053 including header, key `N~220073~001` | ELIQUIS SPRINKLE, APIXABAN, FOR SUSPENSION;ORAL, 0.15MG. The row records approval on 17 April 2025. |
| Orange Book ZIP, `patent.txt` line 7,130, same key | Patent 11896586, product flag Y and use code U-4180. The listing fields carry 22 November 2040 and submission 16 May 2025. Treat the date as the archive's submitted listing field. |
| Orange Book ZIP, `products.txt` line 34,469, key `N~202155~001` | ELIQUIS, 2.5MG tablet. The exact key has no 11896586 pair in the pinned patent table. Ingredient alone would conflate the two keys. |
| US11896586B2, 13 February 2024, Claims HTML section | Follow `#CLM-00045` → `#CLM-00044` → `#CLM-00039` → `#CLM-00033` → `#CLM-00030`. The four edges are explicit claim references. Claim 30 is independent. |

Source definitions. [FDA Orange Book files](https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files) · [Grant HTML mirror](https://patents.google.com/patent/US11896586B2/en#claims)

## Claim 45 and inherited product evidence

Page numbers below are one-based PDF pages. A supported row is an observation about this specific US product or source. The claim remains unassessed as a whole.

| Grant element | Product witness | Finding |
|---|---|---|
| 45, sprinkle capsule; 44, capsule containing the treated core | FDA label §3 p. 7 and §16 p. 40 identify the powder within a capsule, which is marked 898 and supplied in a 28-count bottle. FDA quality review p. 6 calls the product a sprinkle-only formulation. | Sprinkle capsule presentation supported. Whether the contents are the particular treated core remains open. |
| 39, formulation with approximately 0.1–0.4 mg apixaban | FDA label §11 p. 25 gives 0.15 mg apixaban per capsule for SPRINKLE. | Nominal amount falls inside the stated range on the capsule basis. This quantity is distinct from the percentage of a treated core. |
| 33, at least one treated core defined by 30 | FDA quality review p. 4, Executive Summary §4(a)(2), describes the capsule fill as beads and identifies apixaban, hypromellose and sugar spheres. Label §11 corroborates the ingredient identities. | Beads and named ingredients documented. The presence of a core meeting claim 30 remains unknown. |
| 30, substrate with apixaban and carrier arranged in a surface layer | Same review paragraph and label list do not establish physical distribution, the identity of the functional carrier, or how the ingredients are associated with the core surface. | Unknown. Ingredient co-presence gives a lead to request a layer or distribution record. |
| 30, treated-core apixaban weight fraction | Review p. 4 masks the numerical bead percentage with `(b) (4)`. Label gives mass per capsule but no corresponding treated-core denominator. | Unknown. Preserve the redaction and avoid substituting dose or assuming mass per bead. |
| 30, spray-layered dispersion with the solvent concentration below its solubility limit | Review p. 5, Executive Summary §4(a)(3), masks the description of the manufacturing process with `(b) (4)`. | Process and solvent condition remain unknown. |

The FDA quality review adds the bead form and explicitly redacted quantitative and process fields. The label is the direct witness for marketed strength and pack. This distinction informs a deterministic source checklist. It supplies no comparative score. [FDA approved label](https://www.accessdata.fda.gov/drugsatfda_docs/label/2026/220073s001lbl.pdf) · [FDA product quality review](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2025/220073Orig1s000ChemR.pdf)

## Thai family verification

The pinned grant mirror reports the PCT lead `PCT/US2019/027456` / `WO2019204193A1` and the EP lead `EP19722333.2` / `EP3781132B1` in the application/family metadata. This is a positive discovery lead for the bounded official pass. The national verification attempts on 26 November 2026 returned no usable Thai row.

| Authority, exact input | Observed result |
|---|---|
| WIPO PATENTSCOPE public lookup `WO2019204193`, with `PCT/US2019/027456` and TH/Thailand in the authority-scoped index query | No matching official record surfaced in the bounded index query. The direct record URL failed with 403 via web fetch. [PATENTSCOPE lookup](https://patentscope.wipo.int/search/en/WO2019204193) |
| EPO European Patent Register, application `EP19722333` with family tab; authority-scoped index cross-check with `EP3781132 WO2019204193 TH` | Direct HTTPS returned 403. Index results provided help on formatting and family scope. No case-level national family record was verified. [EPO Register family lookup](https://register.epo.org/application?number=EP19722333&lng=en&tab=family) |
| Thai DIP patent search. Authority-scoped `WO2019204193 PCT US2019 027456 apixaban`, followed the official public search link | Index results exposed no matching official matter. The national search form returned 403 via web fetch, so no form query was submitted. [DIP service directory](https://www.ipthailand.go.th/th/dip-law-2/item/42-281.html) · [DIP search form](https://patentsearch.ipthailand.go.th/DIP2013/simplesearch.php) |

The replay retains the US and international leads. Thai national application/publication, effective claim set, examination history and dated legal status need a case-level DIP record or evidence from a qualified local reviewer. Access failures and bounded search visibility give no reliable negative. US listing, foreign family metadata and literal claim features do not determine Thai scope or present enforceability. [Internal Thai evidence request](ELIQUIS-INTERNAL-REQUEST.md)

## Source pins and rights

| ID and retained location | Version and SHA-256 |
|---|---|
| OB. `ptp-ip-pharma-landscape-20261126/orange-book.zip` | FDA HTTP Last-Modified 13 November 2026 16:03:15 UTC, `d4dbc9d85df4fbd78c5e448f130a55b05054f529d2054a46df10735437792241`. ZIP members `products.txt` `02274827ecc0e63ae63cc0cfec9e755bcd947c144b2b7b4e66fe585db139cfa0` and `patent.txt` `ae5e64d61b4ae1ea9ea1c3a86e4ec49141bba81b1f9e3078f763a46b9c8e0352`. |
| GR. `ptp-ip-pharma-landscape-20261126/US11896586B2.html` | Pinned B2 HTML, `dab046852767298848a2b864f40d49fe518aaee55aa5592c760b18c9f3e7ded8`. Mirror metadata is a lead and grant claim text is page-scoped. |
| LB. `ptp-ip-pharma-research-phase1-20261126/220073s001lbl.pdf` | FDA S001 PDF, HTTP Last-Modified 26 June 2026 17:31:49 UTC, 54 pp., 2,604,197 bytes, `950676dec7af1dd261054223d3eee140614ec7535e878a86426b0cd0c2da7454`. |
| QR. `ptp-ip-pharma-research-phase1-20261126/220073Orig1s000ChemR.pdf` | FDA original submission quality review, HTTP Last-Modified 10 October 2025 18:52:45 UTC, 56 pp., 11,562,712 bytes, `4869f708d48435d65328e7cd040dda1eaf1b49467b9bfd7d4edbb9453452089e`. The web fetch exceeded its content limit. The direct bounded HTTPS acquisition succeeded, and the federal redactions remain intact. |

Both directories are under `C:/Users/User/Desktop/myProject/_private_artifacts/`, the main project checkout's private sibling. FDA public access supports the local evidence inspection. Use attributed factual extracts and links in the dossier. FDA's general site copying policy has exceptions. Applicant material, trademarks, mirror HTML and national-office content have separate conditions. Retain source bytes privately and do a component-specific rights review before redistribution or service transfer. Neither a research record nor the internal draft authorizes a filing. [FDA website policy](https://www.fda.gov/about-fda/about-website/website-policies#linking)

## Offline replay

Run the following block in Python 3.12 with PyMuPDF 2.0. It reads only the two private source directories. The checks preserve the exact archive keys and confirm the relevant parent elements and FDA page mapping.

```python
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import re
import pymupdf

base = Path("C:/Users/User/Desktop/myProject/_private_artifacts")
original = base / "ptp-ip-pharma-landscape-20261126"
phase1 = base / "ptp-ip-pharma-research-phase1-20261126"

def checked(data, digest):
    assert sha256(data).hexdigest() == digest
    return data

archive = original / "orange-book.zip"
checked(archive.read_bytes(), "d4dbc9d85df4fbd78c5e448f130a55b05054f529d2054a46df10735437792241")
with ZipFile(archive) as source:
    def table(name, digest):
        member, = [n for n in source.namelist() if Path(n).name.lower() == name]
        return checked(source.read(member), digest).decode("latin1").splitlines()

    products = table("products.txt", "02274827ecc0e63ae63cc0cfec9e755bcd947c144b2b7b4e66fe585db139cfa0")
    patents = table("patent.txt", "ae5e64d61b4ae1ea9ea1c3a86e4ec49141bba81b1f9e3078f763a46b9c8e0352")
    assert products[9052].split("~")[2:8] == ["ELIQUIS SPRINKLE", "BRISTOL", "0.15MG", "N", "220073", "001"]
    assert products[34468].split("~")[2:8] == ["ELIQUIS", "BRISTOL MYERS SQUIBB", "2.5MG", "N", "202155", "001"]
    assert patents[7129].split("~")[:4] == ["N", "220073", "001", "11896586"]
    assert not any(row.startswith("N~202155~001~11896586~") for row in patents)

grant = checked((original / "US11896586B2.html").read_bytes(), "dab046852767298848a2b864f40d49fe518aaee55aa5592c760b18c9f3e7ded8").decode()
assert '<dd itemprop="publicationNumber">US11896586B2</dd>' in grant
claims = grant.split('<section itemprop="claims" itemscope>', 1)[1].split("</section>", 1)[0]
blocks = re.split(r'<div id="CLM-(\d+)" num="\d+" class="claim">', claims)
by_number = {int(i): body for i, body in zip(blocks[1::2], blocks[2::2])}
assert sorted(by_number) == list(range(1, 46))
path = [45]
while refs := re.findall(r'<claim-ref idref="CLM-(\d+)">', by_number[path[-1]]):
    parent, = map(int, refs)
    assert parent in by_number and parent < path[-1]
    path.append(parent)
assert path == [45, 44, 39, 33, 30]

def pdf_pages(file, digest, count, locators):
    data = checked((phase1 / file).read_bytes(), digest)
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        assert len(pdf) == count
        for page, phrases in locators.items():
            text = " ".join(pdf[page - 1].get_text(sort=True).split())
            assert all(phrase in text for phrase in phrases), (file, page)

pdf_pages("220073s001lbl.pdf", "950676dec7af1dd261054223d3eee140614ec7535e878a86426b0cd0c2da7454",
          54, {25: ["0.15 mg apixaban", "sugar spheres"], 40: ["0003-0898-28"]})
pdf_pages("220073Orig1s000ChemR.pdf", "4869f708d48435d65328e7cd040dda1eaf1b49467b9bfd7d4edbb9453452089e",
          56, {4: ["beads of (b) (4) % w/w apixaban"], 5: ["manufacturing process includes (b) (4)"]})
print("PASS: pinned sources, exact FDA rows, claim ancestry and product witness locators")
```
