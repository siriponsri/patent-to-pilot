# WPI readiness — 4 November 2026

This is not editorial acceptance and does not authorize submission.

| Dimension | Status | Basis | Gap |
|---|---|---|---|
| Engineering | READY (current offline scope) | Earlier offline regression; focused tests for this round's new modules | Full suite not rerun on this head |
| Data and rights | READY for Track A local research | PANORAMA CC BY-NC 4.0, PatEmbed CC BY-NC-SA 4.0, e5 MIT; raw data outside Git | Non-commercial terms limit any commercial reuse; Bridge blocked |
| Scientific evaluation | PARTIAL → substantive | Preregistered PAR4PC test with paired cluster CIs, negative results reported | Single benchmark; proxy labels; possible PatEmbed contamination; no open-corpus setting |
| Reproducibility | PARTIAL | Commands, hashes, freeze commit, registry; BM25 reproduction exact | Same-author rerun only; private data must be re-acquired by readers |
| Manuscript | PARTIAL | Track A sections written from artifacts | Owner revision of framing, related work and references; figures |
| Owner/submission | PARTIAL | Guide for Authors read on 2026-11-05 (requirements below). Owner decisions W1–W4 recorded on 2026-11-05: Track A goes in the main text, short; code license Apache-2.0 (`LICENSE`, `NOTICE`); authors are Srihangpiboon (first, corresponding) and Ploysuwan (supervision), at KMITL; no funding; no competing interests | Organization-adaptive study results; anonymized manuscript and code link; final declarations |

## Journal requirement checks (2026-11-04)

| URL | Result |
|---|---|
| https://www.sciencedirect.com/journal/world-patent-information/publish/guide-for-authors | HTTP 403. Not verified. No limits are inferred from mirrors. |
| https://shop.elsevier.com/journals/world-patent-information/0172-2190 | Accessible. Scope includes prior-art searches, IR system benchmarking, real data collections for IR experiments, and AI/ML applications. Research and review articles are named. |

### WPI Guide for Authors, read 2026-11-05 in the in-app browser

| Item | Requirement |
|---|---|
| Length | Papers 3,000–6,000 words; brief communications up to 1,500 words |
| Review | Double anonymized. Submit a separate title page. The manuscript and supplements carry no names, affiliations or acknowledgments. |
| Abstract | Up to 250 words: purpose, procedures, main findings with statistical significance, conclusions |
| Keywords | 1–7, in English; avoid multi-word "and"/"of" phrases |
| Highlights | Encouraged: 3–5 bullets of at most 85 characters each, in a separate file with "highlights" in the name |
| Graphical abstract | Encouraged |
| Structure | Numbered sections (1, 1.1, 1.1.1); the abstract is not numbered |
| References | Numbered, in square brackets: [3,6] |
| Source files | .docx in single column, or LaTeX (the Elsevier template is encouraged; double column allowed only in LaTeX). A PDF is not an acceptable source file. |
| Declarations | Competing interests; funding sources and sponsor role; CRediT roles; generative-AI use statement |
| Research data | Option B: deposit and link data where possible; otherwise state why the data cannot be shared |

Consequences for this manuscript:
- During review, cite the authors' own published IEEE paper in the third person.
- During review, link the code through an anonymized mirror. The `siriponsri/patent-to-pilot` URL identifies the authors.
- Data statement: DAPFAM and PANORAMA are public and are cited, not redistributed. Aggregates and code are shared.

## Minimal owner decision packet

1. Done 2026-11-05: Guide for Authors checked (above).
2. Done 2026-11-05: Track A goes in the main text as a short section; the organization-adaptive DAPFAM study is the primary contribution (see `docs/healthtech/research/ORG_ADAPTIVE_MANUSCRIPT_PLAN_20261105_EN.md`).
3. Done 2026-11-05: code license Apache-2.0.
4. Done 2026-11-05, except the final AI-use wording:
   - authors and CRediT;
   - affiliation: School of Information Technology, KMITL, 1 Chalong Krung 1 Alley, Lat Krabang, Bangkok 10520, Thailand;
   - funding: none;
   - competing interests: none.

   The AI-use wording is written once the manuscript text exists.
