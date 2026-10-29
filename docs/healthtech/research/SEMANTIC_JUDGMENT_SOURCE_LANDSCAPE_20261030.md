# Semantic device-patent source landscape

This is a bounded public-source screen for a future HT-T1 semantic
device-product-to-patent judgment source. It does not claim an exhaustive
literature or dataset review, and no candidate was downloaded or promoted to
runtime input.

## Admission criteria

A candidate must support named device/product queries paired with patent
records and explicit semantic judgments. It must also expose source revision
and locator fields, rights for local research, independent company/family
groups, and a predeclared untouched holdout. A license or public repository
badge cannot cure a task mismatch or missing provenance.

## Screened candidates

| Candidate | Observed resource | Decision | Reason |
|---|---|---|---|
| PatentMatch | Patent claims matched to cited prior-art passages, with examiner-derived semantic correspondence labels; arXiv `2012.13919` and GitHub `julian-risch/PatentMatch` | `REJECTED_FOR_HT_T1_TASK_MISMATCH` | The query unit is a patent claim and the target is prior art passage correspondence, not a named medical device/product linked to a patent. The required company/family holdout contract is not supplied by the public description. |
| PatentBench | Patent prosecution benchmark with prior-art, claim-mapping, and related prosecution tasks; GitHub `rhahn28/patentbench` | `REJECTED_FOR_HT_T1_TASK_MISMATCH` | The benchmark evaluates prosecution workflows across patent tasks, not device-product relevance judgments. The repository license does not establish a compatible HT-T1 label schema or source provenance. |
| Sharps disposal device landscape | Zenodo `10.5281/zenodo.21101400`; health-care sharps disposal device landscape with screening outputs, raw search exports, and technical feature extraction | `PROMISING_DOMAIN_BUT_BLOCKED_LOCAL` | This is the closest domain match found. The public record says files are restricted and does not expose a source-specific reuse clause. The metadata also does not establish exact `relevant`/`not_relevant` pair labels, adjudicator roles, independent company/family groups, or a final holdout. |
| Bridge-MedDevKG | Existing pinned branch at `f3990a207949f25012d1070a08ac303e140387e6` | `BLOCKED_LOCAL` | Preserve the existing rights/cohort/split blocker; do not reopen or acquire the payload in this screen. |

## Decision

No candidate currently passes the M23 authorization contract. The sharps
disposal landscape is a concrete lead for owner outreach or a source-specific
access decision, but it is not an admissible judgment source today. The next
discriminating action is to obtain an authorized copy plus terms and inspect
its actual screening schema without changing the frozen HT-T1 denominator or
holdout.

## Boundaries

- Public metadata and landing pages only; no restricted files downloaded.
- No new runtime inputs, semantic labels, provider calls, or paid cost.
- No candidate is treated as independent gold or as a negative source.
- A future access decision must still pass M23, M25, and M24 in sequence.
