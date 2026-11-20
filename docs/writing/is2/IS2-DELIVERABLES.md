# IS2 deliverables and report plan (v1, 19 Nov 2026)

**Core claim to test:** *A controlled first-stage substitution reveals how candidate exposure constrains the measurable effects
of reranking instructions in cross-domain patent search.* This is a research question, not a proven result.

**Format:** the faculty short-paper template `Template-short-Paper-IS1-2 (AI4BA).docx`, held owner-local; the original was
given in chat on 19 Nov:
- Thai and English titles and abstracts (about 250 words each, one paragraph);
- two-column A4, at most 10 pages, TH SarabunPSK (title 18 bold, headings 16 bold, body 14);
- numbered sections: 1 บทนำ, 2 แนวคิด ทฤษฎี และงานวิจัยที่เกี่ยวข้อง, 3 วิธีดำเนินการวิจัย, 4 ผลการวิจัย, 5 สรุปผลการวิจัย,
  then กิตติกรรมประกาศ, เอกสารอ้างอิง, ภาคผนวก (optional);
- figure captions without the word "แสดง".

The program is AI4BA (สาขาวิชาปัญญาประดิษฐ์เพื่อการวิเคราะห์เชิงธุรกิจ). The long material (Papers 1–3, product) goes into
appendices and the deck, not into the 10 pages.

## 1. Minimum deliverables (all required for IS2)

| # | Deliverable | Source in repo | Status |
|---|---|---|---|
| D1 | Paper 53 recap + IS1 comments + limitations stated plainly | `COMMITTEE-RESPONSE-DRAFT.md` v2, Paper 53 PDF | draft |
| D2 | Registered B53 protocol (first stage × pool depth; Stage 2: × instruction) | `plans/B53-PREDECLARATION.md` (Stage 1 frozen 274af5de) | Stage 1 frozen; Stage 2 after timing |
| D3 | B53 results on DAPFAM: exposure, first-hit rank, conditional/full-cohort effects, CIs, limitations | dr-train `/data/ptp-paper2/b53`, aggregates → `docs/writing/is2/results/` | Stage 1 MEASURED (3442447a); Stage 2 after timing |
| D4 | Reproducibility pack: revisions, hashes, scripts, configs, tests, model-selection rationale, licence/BOM | `scripts/healthtech/b53_first_stage.py`, `tests/test_b53_first_stage.py`, `b53-readiness-20261119.json`, K1a v2 | partial |
| D5 | Short Solution Scout demo + evidence-dossier walkthrough (labelled SYNTHETIC / PUBLIC SOURCE) | `frontend/healthtech-web` | storyboard pending |
| D6 | Research outlook: BridgeRet / CEDS / EG-SHE with true status | `docs/writing/RESEARCH-ROADMAP.md` (retired 21 Nov 2026; recover from git `40780c97`; superseded by program PTP-2026-11-21) | needs update |

Not required for IS2: P1–P3 TEST results, SOTA wins, deployment, real users, business returns.

## 2. Short-paper outline (≤ 10 pages, template sections)

Draft v0.1: `IS2-SHORT-PAPER-DRAFT.md` (Markdown master) → `IS2-short-paper-draft.docx` built from the faculty template by
`scripts/writing/build_is2_shortpaper_docx.py` (8 pages rendered; Stage 2 and the advisor's Thai name are [PENDING]).


1. **บทนำ:**
   - Paper 53 found near-zero instruction effects;
   - only 37.1% of the 692 held-out queries had a known OUT family in the top 100;
   - IS1 comments K1–K2;
   - research questions RQ-IS2.1–2.5.
2. **แนวคิด ทฤษฎี และงานวิจัยที่เกี่ยวข้อง:**
   - DAPFAM (Array 2026), PatenTEB/patembed, BM25 and dense/hybrid retrieval, multi-stage retrieval and exposure;
   - closest work from the strategy §9.1: cross-domain reproducibility, SEARCHFORMER, PaECTER, dynamic depth.
3. **วิธีดำเนินการวิจัย:**
   - DAPFAM cohorts: 905 OUT-eligible / 1,217 IN / 1,247 ALL, versus Paper 53's 692/724, which cannot be recovered;
   - arms F0–F4 (+ F0-OUT, F6, F7), K = 100/200/1000;
   - endpoints and the exposure identity (accounting only);
   - Stage 2 reranking design; statistics; isolation and licences.
4. **ผลการวิจัย:**
   - B53.1 exposure contrasts (Holm);
   - exposure curve, first-hit rank, common-exposed set;
   - Stage 2 Δ_exp; B53.0 comparison with the DAPFAM paper.
5. **สรุปผลการวิจัย:**
   - one explicit answer per comment K1a–K2b;
   - limitations; continuation into Papers 1–3 and the prototype.
- **Appendices:**
  - A: Paper 53 method and Table I;
  - B: registry, pins, hashes, cost;
  - C: research and product portfolio;
  - D: committee matrix.

## 3. Presentation
12-slide outline with speaker-note pointers: `SLIDES-OUTLINE.md`. One-page portfolio: `PORTFOLIO-KMITL.md`.

## 4. Acceptance checklist (from the strategy §12; ticked only with evidence)
- [x] K1a rationale with provenance, no invented history (K1a v2)
- [x] K1b BM25 and hybrid at K=100 measured (B53 Stage 1, `results/B53-STAGE1-RESULTS.md`)
- [x] K1c identity stated with conditions; no causal overclaim (COMMITTEE-RESPONSE v2)
- [ ] K2a only the first stage changes in the main contrast, with reranker control (Stage 2)
- [ ] K2b user journey + proxy metrics; real user benefit = NOT_MEASURED
- [x] Paper 53's 257/692 kept apart from B53-FULL (905 OUT-eligible) and DAPFAM 1,247
- [x] Paper 86 = withdrawn / unpublished, never an IEEE publication
- [x] Research trilogy presented as a parallel program, not published papers (ROADMAP)
- [ ] P1 shows measured DEV only; S* TEST = NOT_RUN unless opened with the owner's go
- [ ] product demo with source labels and static fallback
- [ ] affiliation / authorship / university wording checked with the advisor
- [x] no protected P1/P2/P3 TEST opened
- [ ] advisor agrees the IS2 scope
