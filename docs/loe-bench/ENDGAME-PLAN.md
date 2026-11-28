## Superseded decisions (29 November 2026)

The owner is now the Track A custodian after January 2027. Journal route: STA conditional on confirmation that AI drafting with disclosure is allowed, then JAMIA; PSA and MDM are dropped. Product and writing paused on 29 November for research close-out. Public web hosting is Cloudflare Pages. These decisions supersede conflicting schedule and owner-availability assumptions below. Current close-out status: [research completion checklist](RESEARCH-COMPLETION.md) and [lane handoff](HANDOFF.md); OSF update 4 verified approved 28 November 2026 at 11:30:06 UTC.

---

# Endgame plan: finish research and product by 31 January 2027

Proposed by the main planner and the co-planner (GPT-6.2 Astra high with SciSpace) on 28 November 2026. **The owner approved it on 28 November 2026**: Apache-2.0 for the whole repository, a public web app, and a different GPU type if no L4 is available by 10 Dec (see the decision register). The owner will not follow the project into 2027, so nothing in this plan requires the owner's account, machine or labour after 31 January 2027.

## Goal

Finish with **one usable product, one journal manuscript beyond IS2, and one frozen prediction set that others can score**. The product must be usable by the IS2 committee by about 15 December 2026, and every owner task must close by 31 January 2027. Track A outcomes (November 2027 and 2028) add value later. Graduation, the product release and the first paper do not depend on them.

## What the evidence supports (what we say)

| Status | Claim | Source |
|---|---|---|
| Measured, H1 PASS | At a 20% review budget and 24 months, M3 found 66.85% of event rows versus 46.48% for the age baseline (+20.37 pp [14.37, 26.16]). Queue precision was 26.62%; always show it next to recall. | SCORE |
| Measured, H2 FAIL | The tabular model M1 found 65.49%. The graph's added value for ranking is unconfirmed; the graph is kept for traceability and checklists. H3 is descriptive. | SCORE |
| Measured, exploratory | Qwen2.5-7B with the same evidence (L1e) found 12.36% (−54.48 pp vs M3). This applies to the tested setting only. | SCORELLM |
| Measured in part | C3 crowding +30.11 pp. C4 on C′ was not run. Auto-clear safety failed. | SCORE |
| Prepared, pending | Track A: 651 drugs per horizon at t0 = 27 Nov 2026, plus the P1/P2 open-feature adaptations of prior methods. | TRACKA-CORE, PRIORARMS |

Never call 66.85% "accuracy". Never claim that the graph works, that LLMs are useless in general, or that the product gives an FTO opinion.

## Publication

1. **IS2 short paper** (fixed): TH and EN, 10 pages each, audited. The storytelling revision is being designed separately with the co-planner.
2. **One journal manuscript**, working title *Prioritizing Review of Upcoming US Generic Approvals Using Public Regulatory Evidence: A Preregistered Temporal Benchmark*.
   - First choice: **Clinical Pharmacology & Therapeutics**, where Hu et al. 2019 published the closest work ([doi:10.1002/cpt.1479](https://doi.org/10.1002/cpt.1479)).
   - If cost is the constraint: **Pharmaceutical Sciences Asia** (Mahidol), which charges no submission or publication fees.
   - **Scientific Data** only if the dataset is downloadable by outsiders with rights cleared. Its model is the US COVID-19 Forecast Hub paper ([s41597-022-01517-w](https://www.nature.com/articles/s41597-022-01517-w)).
   - The owner and advisor choose one journal by **8 January**, with submission by **15 January** if the conditions are met. Acceptance and reviewer replies are outside the owner's control; record the submission status truthfully.
3. **CPU work that raises acceptance odds** (no tuning on C′):
   - a benchmark card and a clean-machine reproduction test
   - the existing calibration (Brier and ECE) with counts per risk bin
   - a manual check of DEV ties and missing-patent cases
   - B1 → M1 → M3 tables by cutoff
   - at most one feature-group ablation on DEV, under a plan written before the run

## Product v1.0 (Claude builds the product; GPT executors build the data pipelines)

- **Current queue as of 27 Nov 2026**, enabled after the freeze is verified. It covers 651 histories per horizon (12 and 24 months) with 130 review slots, shows the reference date, explains boundary ties, and has a dossier for each drug as far as the evidence allows.
- **Snapshot refresh**, run on demand by a maintainer, writes a new dated snapshot. It records the fetch date, versions, SHA-256, rows added and removed, and failed sources. The t0 snapshot always stays available, and the release makes no promise of monthly updates.
- **PDF dossier (TH/EN) from the real queue**, in the same drug, date, language and version as the screen. The Thai checklist lists search terms, WO and priority numbers, the agency, the owner of each task and the missing status. Re-run the traceability audit on the new set.
- **Web and Windows.** Ship a public URL and a Windows installer, both tested on a clean machine (install, offline use, PDF export, uninstall), with checksums. The installer stays unsigned unless a certificate is bought (a separate decision).
- **Keep the historical "time machine"** (development dossiers with outcomes revealed after the forecast).
- **Not in v1.0:** auto-clear, investment recommendations, Thai price prediction, a general chatbot, biologics, or any workaround for Thai registry restrictions.
- **Disclaimer, the same text on screen and in the PDF:** "เอกสารนี้ใช้จัดลำดับงานตรวจจากข้อมูลที่ระบุ ณ วันที่แสดง แบบจำลองประเมินโอกาสการอนุมัติยาสามัญครั้งแรกในสหรัฐฯ สถานะสิทธิในไทยและการประเมินเสรีภาพในการดำเนินการด้านสิทธิบัตร (FTO) ต้องให้ผู้เชี่ยวชาญตรวจข้อถือสิทธิ ผลิตภัณฑ์ ประเทศ และสถานะกฎหมายปัจจุบัน เอกสารนี้ไม่ใช่ความเห็นทางกฎหมายหรือความเห็น FTO"
- **Business position.** The first users are BD/R&D pharmacists at Thai and ASEAN generic makers. CROs and consultants are per-project users. This is a market hypothesis with no willingness-to-pay data. Competitors: Clarivate Cortellis (it already has a US Generic Forecast, so forecasting alone is a weak pitch), IQVIA Ark Patent Intelligence, DrugPatentWatch, Evaluate and GlobalData. The differentiators we can demonstrate are as-of evidence replay, registered accuracy, open data in the declared scope, a Thai hand-off and a free reference release. The commercial path is open reference code and scorer, with revenue from internal installs, portfolio import, contracted updates and support.
- **Licence.** NOTICE now covers Apache-2.0 for `src/`, `scripts/`, `tests/` and `frontend/` only. The owner must decide on `product/` and `loe-bench/`. NBER data restricts redistribution and commercial use, so ship download recipes instead of copies.

## Wow demonstrations (true claims only)

1. **Time machine before the reveal:** open the historical solifenacin dossier, decide what to send to a specialist, then reveal the outcome and the later FDA letter.
2. **Equal budget, who finds more:** a 1-in-5 slot animation revealing B1 46.48%, M1 65.49%, M3 66.85% and L1e 12.36%, then M3 precision 26.62%.
3. **Current queue to a Thai hand-off in one click:** pick a t0 drug, switch the language, open one source and export the PDF that says who must check what with DIP and Thai FDA. Family leads are 17/17, but Thai status is 0/6, so the next question is shown instead of an invented answer.
4. **A forecast anyone can verify:** show the OSF registration, match the digest of the downloaded file, and run the scorer on a known-answer fixture next to the real Track A table marked PENDING. Run this demo only after update 4 is verified externally. No public leaderboard for new models.

## Ending Track A without the owner

- **Others need the prediction files and the method, not just digests.**
  - The **OSF registration update 4** holds the timestamp and manifest.
  - A **Zenodo version DOI** holds the release: prediction bytes that may be shared, scorer, roster, arm dictionary, environment lock, example output and guide.
  - OSF Projects change between Nov 2026 and Feb 2027, but Registrations continue, so future scoring must not depend on uploads to the old project.
- **One-command scorer** (`python -m loe_bench.score_release --release <DOI> --horizon 12 --out results/`, proposed interface):
  - verifies hashes, FDA edition coverage, identifiers, windows, ties and counts
  - writes PENDING or BLOCKED_SOURCE when coverage is missing
  - is tested on known-answer, wrong-hash and not-yet-mature fixtures
- **GitHub Action** with manual and scheduled triggers. Scheduled runs stop after 60 days of repository inactivity, so treat it as a convenience only. Hand the DOI and guide to the advisor or a consenting maintainer. If nobody takes it, publish the method and promise nothing about publication dates.
- **Statistics across years.** On 27 Nov 2027 the 12-month estimates are descriptive. On 27 Nov 2028 H1 and then H2 are tested at 24 months, and formal H3 follows from them. Track A is a replication because C′ was confirmatory.
- **Paper wording before update 4:** "Core forecasts were generated. External timestamping of the complete prediction package was pending."

## Phases

| Window | Goal | Owner | Executors and Claude | Cost and exit |
|---|---|---|---|---|
| 28 Nov–2 Dec | Close the prediction set | File OSF update 4 from the audited sheet; name a post-January custodian if possible | Sol xhigh TRACKA-FREEZE (running), Luna high manifest check, Claude audit of tag, digests and sheet | GPU ≤ USD 1.50 (approved). Exit: freeze verified. If L4 stays unavailable, apply the fallback rule (decision D-F below) |
| 1–7 Dec | A queue usable in a meeting | Read the paper and report (done); pick the demo cases | Sol high current-queue adapter and snapshot refresh; Sol xhigh count and tie check; Luna high rights and links; Claude connects F2, the PDF and the checklist | CPU, USD 0. Exit: both horizons match the release, PDFs open in both languages, and refresh keeps t0 |
| 5–12 Dec | Reproducibility kit and IS2 | Confirm reading; one rehearsal | Sol xhigh scorer and fixtures; Sol high release builder; IS2 storytelling revision (drafter, Astra, Claude); Claude builds the Thai animated slides | CPU, USD 0. Exit: a clean machine passes the fixtures; the talk is 15 + 10 minutes with an offline demo |
| 13–15 Dec | Release v1.0 and the committee pack | Try the product end to end on another machine | Sol high pipeline test, Luna high URL, checksum and PDF check, Claude clean-Windows install and fixes | Exit: public URL, working installer, PDFs, slides and report. If the freeze has not passed, ship the historical release and state that the current queue is not in v1.0 |
| 16 Dec–15 Jan | Manuscript and hand-over | IS2 draft at end of Dec; choose the journal by 8 Jan; submit by 15 Jan if conditions are met | Sol xhigh number check, Sol high archive guide and metadata, drafter manuscript, Astra critique, Claude audit and figures | APC is separate. Exit: version DOI downloadable, clean-machine test, submission receipt or truthful status |
| 16–31 Jan | Close the owner's obligations | Final IS2; confirm the custodian or record that there is none | Sol high public-instruction restore drill, Luna high storage and cost check, Claude final handoff | Exit: no step needs the owner after 31 Jan. Delete RunPod volume 8n6rnzljwg (USD 2.10/month) after verified transfer |

C10 (user study) stays NOT_RUN unless EC-KMITL approves it in time. A scripted clean-machine walkthrough gives engineering evidence only.

## Decisions the owner needs to make

- **D-P:** approve this plan.
- **D-L:** licence for `product/` and `loe-bench/` (recommended: Apache-2.0, with data shipped as download recipes).
- **D-W:** public web deployment (recommended: a static host such as GitHub Pages or Vercel; it is outward-facing, so it needs approval).
- **D-F:** fallback if no L4 by a set date. Recommended: freeze the core plus P1/P2 by 10 Dec, record L1/L1e/C9 as NOT_RUN, and add them through a later update before 31 Jan if an L4 appears. The current card forbids partial freezes, so this needs the owner's decision.
- **D-J:** journal (CPT or Pharmaceutical Sciences Asia), by 8 January.
