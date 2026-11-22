# P5-T01 — Draft the single manuscript and three linked contribution tests (22 Nov 2026)

**Result:** DRAFT_COMPLETE for the P5-T01 exit (background, method, design written; result cells `NOT_RUN`).
**Research evidence for the proposed method:** none yet (`method_evidence = NOT_YET_DEMONSTRATED`). This receipt does not
claim any retrieval result.

## Deliverables

| File | Content |
|---|---|
| `docs/writing/journal/MANUSCRIPT-DRAFT-v1.md` | One English manuscript, three linked contributions (source-grounded structural evidence; bounded acquisition of missing evidence; inspectable execution and selective revision). Title options, abstract skeleton with `NOT_RUN` slots, introduction, related work, problem formulation, method, architecture, evaluation design (P1, DAPFAM, Thai scoreboards kept separate), implementation, results, threats, references, gap list |
| `docs/tracking/owner-note-22112026/receipts/P5-T01_claim_evidence_map.csv` | 21 claims: claim, contribution, required evidence, current evidence, status |
| `docs/writing/journal/README.md` | Dated pointer to the one-manuscript draft; earlier three-paper table kept as history |

## How the draft meets the task boundaries

- **Product and method names:** product "Patent-to-Pilot"; method components named descriptively (structural evidence,
  relation-targeted search, evidence trace, dependency-based refresh). No new acronym.
- **Results:** every new-method cell is `NOT_RUN`. Historical results appear only in §8.2 with their recorded status and
  receipt links: G03 v1, A1 and A2 **PARKED**; A3r0 **FORMAT_SMOKE_ONLY**; A3r1 **NOT_RUN**; B53 Stage 1–2 and B53.0
  **MEASURED_EXPLORATORY** (previously exposed benchmark; re-implementation, not replication). No target gain is written as a
  result; the +0.010 rule is labelled a planning target.
- **Citations:** related work cites only the 21 verified bibliography entries (`references/verified_identifiers.bib`) and
  Paper 53 as the authors' own prior work (program listing; DOI not verified). Sources outside the verified list (DAPFAM paper,
  PatenTEB/PatEmbed, Arctic-embed, BM25, RRF, Challenge-1M, Thai Gazette paper, Docling) are marked `[CITATION NEEDED]`;
  dataset cards are listed separately as records, not scholarly citations.
- **Excluded:** the unpublished, withdrawn conference paper (IS2-only; standing rule 9) is not mentioned anywhere in
  `docs/writing/journal/`; arXiv:2605.24297 is not used; Paper 53's 37.1% statistic is not printed (denominator to be recovered).
- **Ground truth:** runtime model assessments are search signals only; no LLM judge is used as ground truth (rule 12).
- **Owner corrections carried into the draft:** A1 mask defect direction unknown; PatenTEB shared family pool with training
  overlap unmeasured; A3r0 = one Claude, two Qwen, one DeepSeek, format smoke only; no automatic maintenance headline.
- **Contribution mapping note:** CLAUDE.md §1 still lists C1 support-frontier acquisition / C2 versioned evidence architecture /
  C3 evaluation package. The draft follows the newer owner blueprint (structure / acquisition / trace and revision); the
  evaluation package becomes reproducibility material inside the one paper. The coordinator owns CLAUDE.md.

## Related corrections pass (same session)

Recorded in `docs/maintenance/WRITING-CORRECTIONS-20261122.md` (W1–W6). Frozen protocol files were not edited.

## Checks

| Command | Result |
|---|---|
| `python -m pytest -q -p no:cacheprovider tests/test_org_adaptive_terminology.py` | 2 passed (after the manuscript, README and CSV were written) |
| CSV parse (`csv.reader`) | 22 rows (header + 21), 6 columns each |

No paid call, download, remote job, code change or commit was made. Full `python -m pytest` was not run (documents only).

## Open gaps (block P5-T02 positive-method writing, not this task)

1. All §8.1 results: P1 scoreboard, DAPFAM matched comparison, Thai transfer, contribution 1 equal-content control,
   contribution 3 replay/revision measurements, user tasks.
2. Missing citations and author lists (manuscript Appendix A item 2).
3. Paper 53 DOI and the original exposure denominator.
4. The frozen rule that selects which unresolved relation to search, and the frozen A3r1 configuration.
5. Figure 1 in journal style; venue and length choice.

**Next:** P5-T02 when actual scoreboards exist.
