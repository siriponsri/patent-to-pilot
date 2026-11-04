# ข้อเสนอข้อมูลเสริมตาม HealthTech GOAL/PLAN

ตรวจแหล่งต้นทาง 27 ตุลาคม 2026 · สถานะ **PROPOSAL / ไม่ได้ acquire corpus ใหม่** ข้อเสนอนี้รองรับ HT-G1–G6 และ HT-W03–W07/W12/W16–W18 ตาม pack เดิม ไม่เปลี่ยน thesis, success criterion หรือผู้ใช้เป้าหมาย

## ข้อมูลสำหรับ scientific evaluation

| ลำดับ / เป้าหมาย | แหล่งและ scale/version ที่ตรวจได้ | สิทธิ์/การเข้าถึง | Keys และการแบ่งข้อมูล | Claim ที่รองรับ / ข้อจำกัด |
|---|---|---|---|---|
| Must-have แบบมีเงื่อนไข; G1/G2/G4, W03/W07 | [Bridge-MedDevKG](https://github.com/myqqhub/Bridge-MedDevKG/tree/f3990a207949f25012d1070a08ac303e140387e6), release ที่ pack pin: 434 device docs/50K patents/672 exported links; completeness subset 585 links/74 devices | README แสดง MIT badge แต่ pack audit ไม่พบ distinct data license; ยังไม่ถือว่า rights-cleared จาก badge หรือ paper CC BY ไม่ acquire/relicense payload รอบนี้ | `fda_id`, `pat_id`; raw/canonical IDs และ sourced family map; shared-patent/family components; company-held-out sensitivity; exported training positives ทับ evaluation ไม่ใช่ independent split | Known-link recovery ใน declared cohort/universe เท่านั้น ไม่ใช่ exhaustive recall/FTO; ต้อง reconcile paper 585/88 และ release ก่อน final protocol |
| Must-have; G1/G2, W04/W15 | [SciFact source](https://github.com/allenai/scifact/tree/68b98a56d93e0f9da0d2aab4e6c3294699a0f72e); paper 1,409 claims/5,183 abstracts; 809 train/300 dev/300 test | [License](https://github.com/allenai/scifact/blob/68b98a56d93e0f9da0d2aab4e6c3294699a0f72e/LICENSE.md): claims/annotations CC BY 4.0, abstracts ODC-By 1.0, code Apache 2.0 `release/latest` mutable จึงต้องเก็บ download hash/version จริง; official test labels ไม่เปิดตาม README | Claim ID, document ID, sentence index/rationale sets; train-only fitting และ frozen dev/final design; ไม่ส่ง test/evaluator labels เข้า runtime | Independent pre-existing labels สำหรับ evidence component ไม่ใช่ patent-link gold; local test-score reproduction ยังทำไม่ได้เมื่อไม่มี test labels ใช้ official route หรือประกาศ adapted held-out design ตามจริง |
| Must-have engineering controls; G2/G3, W06/W12 | Project-authored corruption/absence cases ขนาดเล็ก: source missing, wrong hash/version/field/span, failed query, duplicate IDs, unjudged input | ไม่มี third-party corpus; เก็บใน tests/examples ได้ | แยก evaluator reference fixtures ออกจาก runtime JSON; freeze hand-computable expected values | วัด deterministic integrity/failure handling เท่านั้น **synthetic ไม่ใช่ independent scientific gold หรือ market validation** |
| Optional; G2/G6, W04/W18 | [BioASQ participants data](https://participants-area.bioasq.org/datasets/), annual Task b expert questions; paperอธิบายการเพิ่มราว 500 คำถามต่อปี เลือก edition ก่อนใช้ | Portal ระบุ CC BY 2.5; training downloads ต้อง registered user ไม่ลงทะเบียน/รับเงื่อนไขแทน owner ในรอบนี้; rights ของ abstracts/full-text แยก | Question ID, PMID, snippet offsets; pin annual edition, กันคำถาม/บทความซ้ำข้าม dev/final | Biomedical document/snippet retrieval เมื่อ dossier ต้องใช้ literature จริง ไม่รับรอง dossier ทั้งฉบับหรือแทน HT-T1; ไม่ขยายเป็น main QA study |
| Optional later; G8, W20 | ChEMU, NLI4CT, FiNE-Patents ตาม [paper notes](../../../literature-review/healthtech/READING_NOTES.md) | ChEMU data มี NC restriction; NLI4CT reuse terms ยังต้องตรวจ; FiNE data release/version/license ต้องตรวจเฉพาะก่อนใช้ | Patent/application/family หรือ trial IDs; keep related variants in same split | ใช้เมื่อ branch/task ตรงเท่านั้น ไม่เพิ่มเป็น prerequisite ของ medical-device dossier และไม่ยืม scores ข้าม task |

## Screened but not admitted to HT-T1

PatSnap PatentBench was screened at public commit `b8e059081883fe2411c308221434842950846f8c`. Its repository provides a public non-commercial license notice and human-verified patent-query tasks, but the reviewed task is prior-art/design-FTO retrieval rather than named medical-device/product-to-patent relevance. It is therefore not a semantic HT-T1 replacement, and no dataset payload was downloaded. The source decision is recorded in [`luna-long-run-20261030-source-landscape-20261030`](../audits/luna-long-run-20261030-source-landscape-20261030/README.md).

Negative cases ต้องแยกสามชนิด: verified negative ที่มี annotation ตาม task, unjudged relation ที่ห้ามเรียก negative และ authored corruption สำหรับ software controls SciFact REFUTES/NOINFO ก็ไม่ได้เป็น patent-device non-association ห้ามสร้าง clinical/patent truth ใหม่ด้วย LLM แล้วเรียก independent gold

## ข้อมูลรองรับ public dossier และบริบทธุรกิจ

| ลำดับ / เป้าหมาย | แหล่ง/version/scale | สิทธิ์และขอบเขต | Linkage และการใช้ที่เสนอ |
|---|---|---|---|
| Must-have; G1/G3, W05/W12 | [openFDA download metadata](https://api.fda.gov/download.json): export 2026-10-26 มี 510(k) 176,466 records/238.45 MB zip และ PMA 57,373 records/21.17 MB zip | [Licensing](https://open.fda.gov/license/): โดยทั่วไป CC0 เว้น fields ที่ระบุและข้อกำหนดบริการ; ไม่ bundle เอกสาร third-party ที่ linked มาโดยไม่มีสิทธิ์ | `k_number` หรือ `pma_number` + supplement number, product code, applicant, dates; PMA supplements ไม่ใช่ unique devices ทั้งหมด ใช้ selected records รองรับ product/regulatory facts ไม่ตีความ 510(k) ว่า PMA approval หรือเป็น patent relationship |
| Optional enrichment; G3/G5, W05/W12/W16 | openFDA UDI export 2026-10-27: 5,182,695 records/52 zip parts; AccessGUDID หน้า download/API fetch ไม่สำเร็จในรอบนี้ จึงไม่อ้างว่า API readiness ผ่าน | [AccessGUDID terms](https://accessgudid.nlm.nih.gov/terms) แยก D&B labeler D-U-N-S และ GMDN ที่มีข้อจำกัด; งด fields เหล่านี้และไม่ใช้เว็บ harvesting; เข้าผ่าน official permitted export/API เมื่อพร้อม | DI/primary DI, brand/version, company และ submission numbers ถ้ามี ข้อมูล company match เป็น proxy; ไม่มี guarantee ว่า DI↔PMA↔patent join ครบหรือ one-to-one ใช้ระบุ named comparator ไม่เป็น gold |
| Optional contextual failures; G3/G5, W05/W12 | [Device recall API](https://open.fda.gov/apis/device/recall/), metadata export 2026-10-27: 59,618 records/275.94 MB zip | openFDA terms และข้อจำกัดการใช้ recall/lifecycle; ใช้ dated source records ไม่แสดงเป็นระบบ alert หรือ latest lifecycle guarantee | `res_event_number`, recall identifiers, product code และ submission numbers ที่มีจริง; ตรวจ join เป็นราย record Recall ไม่ใช่ verified negative patent link หรือ comparative clinical safety rate |
| Future work; G5, W16/W17 | Owner ยืนยันเป็น solo computational study และไม่มี participant route ในรอบนี้; ใช้ developer self-evaluation ได้เฉพาะเมื่อบันทึกและติดป้ายเป็น proxy | ไม่มีการติดต่อ รับสมัคร ขอ consent หรือเก็บข้อมูลผู้เข้าร่วมในรอบนี้; participant materials เป็น future-work template เท่านั้น | Project/task/session IDs ที่ไม่ระบุตัวบุคคล; completion, correction time, rejected evidence, manual delivery effort แยกจาก machine/GPU time; scenario inputs ต้องระบุว่าเป็นสมมติฐาน; external user validation, adoption, actual purchase, revenue, willingness-to-pay และ ROI ยังคง `NOT_RUN` และไม่เป็น engineering/research gate |

จำนวน submissions/product codes/UDI เป็นบริบทว่ามีผลิตภัณฑ์และ workflow ให้ศึกษา ไม่ใช่ market size, demand, willingness to pay หรือ ROI ไม่ซื้อ market reports และไม่ scrape proprietary listings เพื่อเติมตัวเลขธุรกิจ ข้อมูลสาธารณะช่วยเตรียม case และคำถามให้ผู้ใช้ แต่ business validation ต้องมีงาน/การใช้ซ้ำ/การซื้อที่สังเกตจริง

## Acquisition และ integration ที่ทำได้เป็นชุดเล็ก

1. **W04 + W06:** pin SciFact repository commit ที่ระบุและ hash ของ release ที่ดึงจริง เก็บ attribution แยก claims/abstracts เขียน local reader และ official-format adapter ก่อน model evaluation เริ่ม train/dev schema sample; ไม่แตะ hidden final labels ขนาด 1,409 claims/5,183 abstracts ทำ local component work ได้ ไม่จำเป็นต้องโหลด medical corpus ใหญ่
2. **W05 + W12:** เลือก public named devices 3 กรณีเพื่อครบ minimum dossier ของ G3 ภายหลัง เริ่ม **หนึ่งกรณี** ด้วย official records 1–10 รายการต่อแหล่ง ตั้ง transfer cap 10 MB และ storage cap 50 MB ต่อ preparation batch เป็นข้อเสนอด้านทรัพยากร ไม่ใช่จำนวนตัวอย่าง final study บันทึก source URL, snapshot time, jurisdiction, raw hash, normalized hash, per-field rights และ missing joins
3. Normalize ผ่าน contract เดิม เพิ่ม PMA/UDI/recall adapters แยกตาม record type หลังตรวจ schema แล้ว Core `SourceRecord`/`EvidenceItem`/`DossierVersion` ใช้ร่วมกัน ตัว 510(k) adapter ที่เพิ่มแล้ว allowlist เฉพาะ core device/decision fields ตัด unknown/openFDA enrichment ออก การกัน GMDN/D&B ไม่ใช่การตรวจสิทธิ์ให้ครบทุก input ที่ผู้ใช้ส่งมา
4. **W03 + W07:** ใช้ Bridge เฉพาะเมื่อ reuse terms/cohort พร้อม จัด groups จาก reference patents/families, pin eligible-query universe/split และ preregister endpoint/margin ก่อน held-out run ห้าม tune จาก final queries ไม่มีแหล่งเสริมใดในตารางนี้แทน independent HT-T1 labels ที่ขาดได้โดยอัตโนมัติ
5. **W16:** ใช้ [task template](../business/PILOT_TASK_TEMPLATE.md) เตรียมเทียบงานจริงกับ baseline workflow เมื่อมี public dossiers ไม่เพิ่ม experts เป็น gate ของ engineering แต่จำกัด claims ตามหลักฐาน ห้ามเปลี่ยน owner formative review เป็น expert gold

ใน migration/source-landscape pass เดิม ค่าดึง public metadata/official API ที่เสนอไม่มี subscription charge ที่พบในแหล่งอ้างอิง แต่ยังมีค่าแรง/storage/network และเงื่อนไขบริการ และงบ paid inference ถูกบันทึกเป็น **$0** ในรอบนั้น ข้อความนี้เป็น historical boundary; benchmark-expansion continuation ภายหลังมีเพดานสะสม USD100 ตาม owner record โดยไม่ reset ledger และไม่ใช่การอนุมัติให้ใช้จ่ายอัตโนมัติ ขนาด zip ด้านบนเป็นตัวเลขต้นทาง ไม่ใช่ actual download หรือ expanded storage

ไม่มี owner decision ที่ต้องรอก่อนเดิน W04/local adapters ต่อ หากจะใช้ BioASQ ที่ต้องสมัคร, ติดต่อ Bridge ผู้ให้ข้อมูล, เก็บผู้ใช้จริง หรือใช้ paid service ให้เสนอ action/terms/cost ที่ชัดในรอบนั้น สิ่งที่ยังไม่พร้อมเหล่านี้ไม่บล็อก migration หรือ public synthetic engineering release

## Verification limits

ใน source-landscape pass ก่อน benchmark expansion ตรวจ primary pages/repository metadata/selected paper passages เท่านั้น และยังไม่ได้ acquire หรือ profile แถวข้อมูลใหม่ใน pass นั้น ClinicalTrials.gov เป็น candidate สำหรับ NLI4CT branch แต่ API terms page อ่านไม่ได้อย่างน่าเชื่อถือ จึงไม่รวมเป็น must-have หรือยืนยัน redistribution rights จนกว่าจะตรวจได้ หยุด retry แหล่งที่ติดแทนการอ้างว่าพร้อม; สถานะ acquisition ล่าสุดอยู่ใน addendum ด้านล่าง

## Benchmark-expansion reproducibility addendum — 2026-11-01

The historical staged benchmark-expansion component scores were run on pre-run candidate `cd7e5d364d529a001fc51f78c217c10d7d9c8945` and remain preserved. A fresh current-head revalidation was run on candidate `88dc40471cb9078f929c02bb893cfa1e364da841` under the same frozen protocol and verified payloads; the authoritative current receipt is `docs/healthtech/audits/ptp-panorama-current-head-20261103/verification.json`, including the current-head Helmers diagnostic. Results from the historical candidate and current-head run are not pooled.

### Verified acquisition

- Helmers `human_eval.zip`: 13,962,880 bytes; MD5 `83465f1a95805d963d4aabe085e2af98`.
- PANORAMA PAR4PC and PI4PC validation/test: four Parquet files, 166,093,884 bytes total, all parsed with `pyarrow`.
- All five files passed manifest/version, size/hash, archive/Parquet schema and rights checks. Raw payloads and full row-level predictions remain outside Git.
- Existing DAPFAM, PatEmbed and multilingual-e5 vectors/rankings were reused; no re-download or re-embedding was performed.

### Frozen split and runtime contract

- Official validation/test assignment was retained. Cross-split application overlap was zero for PAR4PC and PI4PC.
- Shared candidate IDs across official splits were reported as diagnostics (149 PAR4PC; 38 PI4PC) and not silently removed.
- Ranking excluded `gold_answers`, `silver_answers`, `negative_answers`, post-examination outcomes and answer-derived queries.
- Deterministic baseline used zero automatic retries and kept every failed row in the denominator.

### Observed component results

| Run | Rows / judged pairs | Macro hit@1 | Macro hit@8 | Singleton exact top-1 | Wall seconds | Failures |
|---|---:|---:|---:|---:|---:|---:|
| PAR4PC validation | 3,029 | 0.733575 | 1.000000 | 0.681583 | 19.2277 | 0 |
| PAR4PC test | 2,896 | 0.715124 | 1.000000 | 0.697702 | 18.0915 | 0 |
| PI4PC validation | 3,937 | 0.377699 | 1.000000 | 0.377699 | 7.9967 | 0 |
| PI4PC test | 3,402 | 0.401235 | 1.000000 | 0.401235 | 6.4792 | 0 |
Helmers remains a separate selected-pool diagnostic (10 targets / 450 pairs): macro AP 0.885450 and macro AUC 0.880012, freshly rerun at current head; it has no comparable PANORAMA hit@1/hit@8 endpoint or failure denominator.

These metrics are component diagnostics. They do not establish adaptive dossier superiority, exhaustive device-patent recall, independent global relevance, user validation, revenue or ROI. The authoritative receipts are in `docs/healthtech/audits/benchmark-expansion-20261101/`.

### Selected manifest extension

Three additional small manifest-listed packages were acquired after the core component runs. PatSnap `data/test.parquet` passed SHA-256 and Parquet schema checks for 30 rows but was not scored. PatentsView AIR-UMASS/NBER passed Git blob SHA-1 and CSV schema checks for 185,250 and 216,847 rows, but standalone benchmark-data rights remain unresolved and the files were not used for scoring or release claims. AffRoDB passed MD5 and JSONL parsing for 1,374 rows; the required ROR v1.40 snapshot was not acquired, so no linkage score was run. These packages expand traceable inventory only and do not change the primary endpoint, split, fair-budget freeze, adaptive claim, or business-validation status.

### Existing uncertainty diagnostic

The manuscript also cites the earlier paired group uncertainty diagnostic at [`luna-long-run-20261029-m12-group-uncertainty-20261029`](../audits/luna-long-run-20261029-m12-group-uncertainty-20261029/README.md). It aligns methods by frozen group ID, compares against HT-B0b, and reports descriptive deltas only because the effective group count is three versus the predeclared minimum of five. The diagnostic is `NOT_ESTIMABLE` and does not support confidence intervals, significance, or adaptive superiority.

## Local generation evidence addendum - 2026-11-04

The current-head local generation branch used a private, frozen, rights-cleared
pack at `ptp-local-qwen-patent-pack-20261103-r2`. The pack contains three named
device cases, 35/20/28 ordered patent candidates, and five evidence rows per
case. Its model-visible contract excludes source payloads, evaluator labels,
hidden oracles, and provider credentials; unlisted pairs remain unjudged.

The exact-head `Qwen/Qwen3-8B` guided run used model revision
`b968826d9c46dd6066d109eabc6255188de91218`, float16/eager attention, eight CPU
threads, and the approved V100 UUID. All three cases were schema-valid. Total
prompt/output tokens were 7,301/1,448; per-case generation latency was
53.448-55.193 seconds; model load was 4.261 seconds; peak GPU reserved memory
was 18,865,979,392 bytes; provider calls and paid cost were zero. The raw and
parsed receipt remains in private Windows storage. The repository stores only
the sanitized verification and failure accounting in
[`ptp-local-qwen-patent-run-20261104`](../audits/ptp-local-qwen-patent-run-20261104/README.md).

Two pre-model failures are retained: the default remote interpreter lacked
`pydantic`, and a retry used an output path that had been pre-created even
though the runner requires a fresh path. Neither failure loaded the model,
used the GPU, called a provider, or mutated the E2 ledger. These are runtime
failure observations, not retrospective cost estimates.

The result supports reproducible generation, source-ID/locator binding, and
machine-time/cost scenario inputs for the three case studies. It does not
support semantic accuracy, retrieval quality, adaptive superiority, paid
local/API comparison, user validation, revenue, ROI, or willingness-to-pay.

### Local generation operational evaluation

The sanitized operational evaluator
docs/healthtech/audits/ptp-local-qwen-patent-run-20261104/operational-evaluation.json
recomputed deterministic workflow measures from the frozen receipt and pack.
It matched 12/12 emitted source IDs and locators and 12/12 allowed
classification contracts. The outputs covered 12/15 input evidence rows
(80%), and all three cases surfaced unresolved items. The result is a
source-binding and evidence-coverage proxy only; it is not a semantic gold
score, retrieval-quality endpoint, adaptive-policy comparison, user study, or
commercial validation.

### Current-head private frontier resource reconciliation

The current-head private baseline was independently reconciled from its saved
receipt without exporting raw query, patent, or source text. The run covers
three eligible queries, 61 reference pairs, two shared exact-patent groups, and
15 completed ranking rows. Full-method resource vectors differ, so the quality
rows below are descriptive rather than an equal-total-budget comparison.

| Method | Macro Recall@20 | Query calls | Rerank pairs |
|---|---:|---:|---:|
| HT-B0a | 0.442739 | 3 | 0 |
| HT-B0b | 0.662242 | 3 | 0 |
| HT-B1 | 0.498802 | 3 | 123 |
| HT-B2 | 0.568912 | 9 | 369 |
| HT-B3 | 0.498802 | 5 | 205 |

The observed prefix-1 first-action diagnostic for HT-B1/HT-B2/HT-B3 is
matched at three query calls and 123 rerank pairs, with Macro Recall@20
`0.498802` for each, zero failed queries, and zero not-realized queries. This
is a first-action diagnostic, not a completed adaptive-policy comparison. The
slice has no final holdout and only two shared exact-patent groups; uncertainty
therefore remains `NOT_ESTIMABLE`. The sanitized machine-readable receipt and
source hashes are in
[`ptp-private-frontier-reconciliation-20261104`](../audits/ptp-private-frontier-reconciliation-20261104/README.md).

### Post-hoc budget-ceiling sensitivity addendum — 2026-11-04

The same saved current-head receipt was reconciled against each observed
query/rerank ceiling without rerunning computation or selecting by endpoint.
Only the first row below has equal realized resources for all three methods;
the other rows are at-most-budget sensitivity views.

| Ceiling | HT-B1 | HT-B2 | HT-B3 | Budget interpretation |
|---|---:|---:|---:|---|
| 3 query calls / 123 rerank pairs | 0.498802 (3/123) | 0.498802 (3/123) | 0.498802 (3/123) | equal realized budget; 0 failed / 0 not realized |
| 5 / 205 | 0.498802 (3/123) | 0.498802 (3/123) | 0.224293 (5/205) | at-most ceiling; B3 has 1 not-realized query |
| 6 / 246 | 0.498802 (3/123) | 0.498802 (6/246) | 0.224293 (5/205) | at-most ceiling; realized budgets differ |
| 9 / 369 | 0.498802 (3/123) | 0.568912 (9/369) | 0.224293 (5/205) | at-most ceiling; realized budgets differ |

These rows are descriptive development diagnostics over three eligible queries,
two shared exact-patent groups, no final holdout, and product-level
disclosed-link references. They do not establish adaptive superiority,
statistical uncertainty, semantic relevance, or generalization. The exact
matched-budget interpretation remains limited to the 3/123 slice. The
sanitized reconciliation and source hashes are in
[`ptp-private-frontier-budget-ceilings-20261104`](../audits/ptp-private-frontier-budget-ceilings-20261104/README.md).
