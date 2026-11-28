# IS2F | Bilingual abstract, introduction and references

**Status: PASS for the assigned editorial changes.** The drafts retain the main planner's abstract text verbatim. Both abstracts exceed the 250-word limit and are with the main planner for trimming.

Branch `loe/IS2F` was cut from the fetched `research/loe-bench` revision `48ff8307d332c4b26a6f0daa822accdb7b0f3b28`. The deliverables are the [English working edition](../../writing/is2/mwd/IS2-DRAFT-EN.md) and the [Thai working edition](../../writing/is2/mwd/IS2-DRAFT-TH.md).

## Changes

1. In both editions, replaced each abstract body with one paragraph using the supplied text. Checked the development figures against [FREEZE](FREEZE.md#development-results), [C3b](C3b.md#c3-development-queue-result) and [C2](C2.md#development-results).
2. Kept the opening question and inserted the supplied competition, prior work and contributions paragraphs after the dossier description. Reordered the bibliography and all numerical citations by first appearance.
3. Removed repository-file text links from the drafts and preserved both figure embeds. Added the OSF preregistration and GitHub repository references, cited the protocol in §§3.2–3.4 and added the availability statement before the references. The OSF DOI placeholder now appears in reference [30].
4. Replaced internal task codes with descriptions for the applicant count, Medicaid reimbursement, evidence-matched language-model comparison, preregistration simulation and earlier baselines. The remaining C5 and C9 prose mentions now describe the price scenario and optional prospective comparison. Defined C′ and Track A at their first use in §3 and updated the Table 1 cutoff header. Kept the model identifiers.
5. Deleted the development-results paragraph from §2.4. The development results are reported in §4.
6. Kept the rest of the draft within the card's scope, including the existing Paper 53 program sentence, findings, keywords and figure targets.

## Reference numbering in both editions

| Previous | Current | Reference |
| ---: | ---: | --- |
| 15 | 1 | Conrad and Lutter |
| 1 | 2 | Srihangpiboon and Ploysuwan, Paper 53 |
| 2 | 3 | Beall et al., approximating generic entry |
| 3 | 4 | Beall et al., biosimilar versus generic competition |
| 4 | 5 | Kerr and Glos |
| 5 | 6 | Hu et al., ANDA submission |
| 6 | 7 | Hopefl et al. |
| 7 | 8 | Chahal, Patel and Shimer |
| 8 | 9 | Hemphill and Sampat |
| 9 | 10 | Kannappan et al. |
| 10 | 11 | Durvasula et al. |
| 11 | 12 | Rai et al. |
| 12 | 13 | Scott Morton |
| 13 | 14 | Reiffen and Ward |
| 14 | 15 | Hollis |
| 16 | 16 | Nikolopoulos et al. |
| 17 | 17 | Trippe |
| 18 | 18 | WIPO public-domain guide |
| 19 | 19 | Hu et al., PatentAgentBench |
| 20 | 20 | Leela and Kessomboon |
| 21 | 21 | Vachanavuttivong et al. |
| 22 | 22 | Paleka et al. |
| 23 | 23 | He et al. |
| 24 | 24 | Karger et al. |
| 25 | 25 | van den Akker et al. |
| 26 | 26 | Traub et al. |
| 27 | 27 | Field and Welsh |
| 28 | 28 | FDA multiple-endpoints guidance |
| 29 | 29 | Turtel et al. |
| New | 30 | Srihangpiboon and Ploysuwan, OSF preregistration |
| New | 31 | Srihangpiboon, GitHub code and data repository |

## Word counts

English uses whitespace-delimited tokens. Thai uses PyThaiNLP 5.4.0 `word_tokenize(engine="newmm", keep_whitespace=False)` and counts tokens containing at least one Unicode letter or number. Body counts cover the prose and captions in §§1–5 and the availability statement. They exclude section headings, table cells, figure alt text, numerical citation markers, editorial placeholders, front matter, abstracts, keywords and references.

| Edition | English abstract | Thai abstract | §§1–5 | Availability | Total body | References |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| English | 252 | 305 | 3,579 | 32 | 3,611 | 31 |
| Thai | 252 | 305 | 4,606 | 49 | 4,655 | 31 |

The English abstract exceeds 250 words by 2 and the Thai abstract by 55. Both retain the supplied wording in both editions.

The default Python interpreter did not have PyThaiNLP. The following PyPI wheels were installed to a temporary target outside Git for word counting. The `newmm` count completed successfully.

| Wheel | License from wheel metadata | SHA-256 |
| --- | --- | --- |
| `pythainlp-5.4.0-py3-none-any.whl` | Apache-2.0 | `9239753df877202da1a50dd2842d9569eff764034f31f20222b3df4def5df193` |
| `tzdata-2026.6-py2.py3-none-any.whl` | Apache-2.0 | `0a10eec6e13ef16b627fabed9a5f2ba61a62b1c67f327305f4e7e412a70b4aec` |

## Verification and handoff

- **PASS** Verbatim one-paragraph abstracts, supplied introduction and availability text, identical 31-entry bibliography, first-appearance numbering and all 29 original source entries preserved.
- **PASS** OSF citations in §§3.2–3.4, original figure targets resolve, and the development paragraph, task codes and repository-file text links are absent from the requested locations.
- **NOT_RUN** Research analyses and the repository test suite. This was a Markdown-only card.

The main planner owns abstract trimming, final audit and lane integration. The OSF registration remains pending in the drafts. Confirm the DOI before final publication of the availability statement.

| Remaining placeholder | Location |
| --- | --- |
| OSF registration DOI | Reference [30] |
| Blinded C′ admission verdict and disposition | §4.1 |
| C′ H1–H3 contrasts, intervals, usefulness checks and ordered decisions, subject to admission | §4.1 |
| Track A timestamped prediction freeze and outcome readouts | §4.1 |
| Dossier claim-level traceability audit | §4.3 |
