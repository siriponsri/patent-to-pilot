# Audit และ repair ต่อจาก E2 — 4 พฤศจิกายน 2026

**แนะนำ resume goal เดิม** มีการแก้โค้ดจริง 2 จุด ไม่สร้าง goal หรือ epoch ใหม่ ไม่แก้ ledger จริง และไม่เปลี่ยน acceptance ให้ปิดง่ายขึ้น หลักฐานใน [verification.json](verification.json), [regressions-final.xml](regressions-final.xml), [medical-recheck.json](medical-recheck.json)

Snapshot UTC 2026-11-03T22:26:03.605832+00:00; candidate HEAD `88dc40471cb9078f929c02bb893cfa1e364da841` ยังเป็น dirty worktree ที่มีงานของ owner/Claude/Luna เก็บส่วนอื่นไว้ทั้งหมด ขณะอ่านพบ SSH PID82752 และ process อื่นที่มีอยู่แล้ว ไม่ kill/relaunch และไม่อ่าน credentials/command lines ไม่ได้เข้าถึง control/session ของ Luna จึงไม่ยืนยันว่า idle หรือเปลี่ยน runtime goal เป็น active เอกสาร r17 ระบุ `ACTIVE_NOT_COMPLETE_NOT_BLOCKED` ส่วน owner รายงาน runtime `BLOCKED`; ทั้งสองเป็นหลักฐานคนละชั้น ไม่แก้ประวัติให้ดูตรงกัน

## สิ่งที่พบและแก้แล้ว

1. **HIGH — คำตอบ paid API ไม่ถูกเก็บไว้ตรวจซ้ำ:** CLI เดิมเรียก `write_sanitized_receipt` ซึ่งตัด parsed output/ข้อความคำตอบออก หลังจบ process เหลือ hash กับผล schema จึงไม่พอใช้ตรวจ factual support หรือเทียบ local/API เพิ่ม `PrivateCaseJournal` ที่ `%LOCALAPPDATA%/PatentToPilot/healthtech/evidence/api-generation/<run-id>.jsonl` เปิดแบบ exclusive ก่อนอ่าน key/dispatch; เก็บข้อความที่ provider ส่งกลับก่อน adapter ตรวจ schema รวมกรณี JSON ผิด, ผล validation และ billing ของแต่ละ case แล้ว flush/fsync ก่อน case ถัดไป หยุดทันทีเมื่อเขียนไม่ได้ ไม่ overwrite run ID เดิม ไม่ใส่ input messages/key/config/raw exception ใน journal; sanitized public receipt ยังไม่มี generated text
2. **MEDIUM — ต้นทุน/calls ของรันอาจรวม process อื่น:** เดิมใช้ผลต่าง ledger ทั้งก้อนก่อน–หลัง งานคนละ process ที่แทรกระหว่าง cases ถูกนับรวมได้ แก้ให้ผูกกับ attempt IDs ที่ transport ของรันนี้เรียกจริง แสดง shared ledger snapshot แยกไว้ และทดสอบกรณี ledger มี 6 attempts แต่รันนี้ส่ง 3 เท่านั้น
3. **Gate-loop/process issue:** เงื่อนไข API ไม่หยุด CPU/reproducibility/manuscript preparation; การเตรียม local release package ไม่ต้องรออนุมัติเผยแพร่ การส่งวารสาร/merge/release จริงยังเป็นอีก action ไม่ตั้งการดู Guide ที่เคยได้ HTTP403 เป็นเหตุให้รัน tests/checkpoints ซ้ำไปเรื่อย ๆ และไม่ retry denied access โดยไม่มีหลักฐานใหม่

**ทดสอบ final 211 passed, 0 failed, 0 errors, 0 skipped** ครอบคลุม provider, E2, output persistence, `.env`, API generation, interleaved accounting และ native DuckDB medical-screen check. รอบก่อนของชุดนี้มี SQL test skipped เพราะยังไม่ได้ชี้ executable; รอบ final ตั้ง path แล้วผ่าน ไม่อ้างว่าเป็น full suite ทั้งโครงการ ค่า full suite r13 `644 passed/2 skipped` เป็นหลักฐานก่อน patch นี้ ไม่ใช่การรันใหม่

การเก็บคำตอบทดสอบด้วย synthetic transport ยังไม่มี paid API output ใหม่ หากเครื่องดับระหว่าง provider ตอบและ checkpoint เขียนเสร็จ ยังต้อง reconcile ด้วย generation ID/ledger ที่มีจริง ไม่อ้างว่ามี atomic transaction ข้าม provider และ filesystem และห้าม replay unknown call

## ทวนผลวิจัยด้วยข้อมูลจริงที่เก็บไว้

**Abbott:** คำนวณจาก raw rankings ใหม่ครบ 18 method-device rows /6 methods /3 devices /41 patents /61 disclosed pairs คะแนนตรงรายงานทุกวิธี ผลต่างมากสุด 0

| วิธี | Macro Recall@20 | Query calls / rerank pairs |
|---|---:|---:|
| B0a | 0.442739 | 3 / 0 |
| B0b | 0.662242 | 3 / 0 |
| B1 | 0.498802 | 3 / 123 |
| B2 | 0.568912 | 9 / 369 |
| B3 | 0.498802 | 5 / 205 |
| B4 offline | 0.498802 | 5 / 205 (+8 controller steps) |

B4 micro =29/61=0.475410; macro เป็นค่าเฉลี่ย recall ของ 3 devices ไม่ใช่ 29/61. ข้อมูลและเพดานต่อ call ร่วมกันไม่ได้ทำให้ realized total budget เท่ากัน B0b สูงกว่า adaptive ในชุดนี้เป็นผลจริงที่ต้องเก็บไว้ ไม่ใช่เหตุให้แก้ gold/controller จนชนะ ไม่อ้าง superiority/generalization หรือใช้ unlisted links เป็น negatives

**Medical subset:** รัน PyArrow + literal substring screen + independent rank arithmetic ใหม่จริง 6.19 วินาที ไม่ import evaluator production: ยืนยัน 96 queries, 3,061 patents, query-screen/full-corpus positive denominator **1,920 =983 both-screen +937 target-unscreened**. แต่ละ query มี20 positives; 10 queries ไม่มี positive target ผ่าน lexicon; positive self-hits0. คะแนน BM25 Recall@100 .169792, PatEmbed dense .372396/hybrid .327083, E5 dense .254167/hybrid .238021 ตรงเดิม ไม่มีการลด denominator เหลือ983ใน corpusเต็ม เป็น posthoc diagnostic จาก saved Oct31 rankings ไม่ใช่ final semantic holdout การเรียกครั้งแรกใช้ historical worktree ผิดและหยุดก่อนคำนวณ; รอบสำเร็จใช้ `patent-to-pilot-research-product-20261031` ตาม provenance เดิม

**PANORAMA/Helmers:** อ่านและเทียบ current stored receipts รอบนี้ ไม่ได้คำนวณใหม่ทุกแถว: PANORAMA gold hit@1 PAR4PC val .733575/test .715124 และ PI4PC val .377699/test .401235; hit@8=1.0 เป็น ceiling ของ task options ไม่ใช่โมเดล perfect retrieval. Helmers 10 targets/450 judged pairs/258 positives, macro AP .885450 และ AUC .880012 เป็น selected-pool diagnostic ไม่ใช่ device-patent semantic gold ไม่รวม .8381/.8095 จาก protocol เก่าเข้าก้อนเดียว

**งานที่ Luna เพิ่มหลัง handoff ก่อน:** O2 engineering ปิดด้วย remote-shard/Windows/shared-engine receipts แล้ว; Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218` รัน patent pack จริง 3/3 cases เมื่อ 4 พ.ย. 00:55:54–00:58:42 ไทย ใช้ prompt7301/output1448 tokens, mean generation latency54.32s, findings12/source-locator bindings12/12. ตรวจ hash ของ private local receipt ตรงอีกครั้งในรอบนี้ ไม่ rerun GPU และไม่แปล schema/source binding เป็น semantic correctness

## Goal inventory และ blocker ที่ยังเป็นจริง

G0–G8 คือ9กลุ่ม canonical; O1–O4 เป็น outcomes ที่ทับซ้อนกัน ไม่ใช่อีก4 goals:

| Goal | สถานะจากหลักฐานปัจจุบัน |
|---|---|
| G0 contract/scope | ปิดในขอบเขต contract |
| G1 data/rights/gold | ยัง partial; สิทธิ์/semantic gold และ final cohort ยังไม่ครบ |
| G2 baseline/evaluator | ผล development และ evaluator มีจริง; final comparison ยังไม่ครบ |
| G3 dossier workflow | engineering ผ่าน; ไม่มี deployment/user-validation claim |
| G4 adaptive research | ยัง descriptive; ไม่ได้ final holdout หรือ superiority |
| G5 business value | operational/scenario evidence เท่านั้น; ไม่รอ external participants ตาม solo amendment |
| G6 manuscript | draft พร้อม owner review; authors/declarations/venue-specific verification ยังต้องจัดการ |
| G7 release/reproducibility | engineering receipts มี; patch รอบนี้ผ่าน targeted211 แต่ยังต้อง bind release package รวม patch ไม่ได้เผยแพร่ |
| G8 expansion | future scope ไม่เพิ่มเป็น mandatory goal |

O1/O2 engineering complete, O3 local generationผ่านแต่ paid comparisonยังไม่รัน, O4 engineeringผ่านแต่ scientific endpointยังpartial. Protocol ปัจจุบันเป็น `FROZEN_DEVELOPMENT_ONLY`:3 Abbott devices/1 applicant-source ไม่ทำให้เป็น untouched holdout ด้วยการเปลี่ยนชื่อไฟล์หรือ seed ห้ามสร้าง labels จาก LLM มาแทน independent gold. การได้ final study ต้องมีสิทธิ์/eligible unseen units/group split/evaluation freeze จริง หรือให้ owner ตัดสินใจเปลี่ยน research claim เป็น descriptive paper อย่างชัดเจน; รอบนี้ไม่ได้เปลี่ยน goal เอง

## สิ่งที่ owner ต้องให้จริง และลำดับงานต่อ

**API pending ก่อน reservation:** journal E2 อ่านได้ `integrity=ok`; legacy4/$0.0001464, operational0, pending/unknownภายในepoch0, prospective$1. ประวัติก่อนepochยังunknownและ `lifetime_cap_guaranteed=false`. ไม่สร้าง ledger/credentialใหม่ ไม่ reset และไม่ถาม$100/GPU grantซ้ำ สิ่งที่ขาดคือ non-secret current credit ของ account/workspace เดียวกับ key ใน local `.env` กับ key remaining limit หรือ unlimited ที่ตรวจแล้ว พร้อมเวลา

ขั้นตอนเล็กที่สุด: owner เปิด Credits และหน้ารายการ key ของบัญชีเดียวกัน แจ้ง **ยอดUSD +เวลาที่ดู +key limit เหลือเท่าไร/Unlimited** โดยไม่ส่ง secret; ผู้รัน bind scope และตรวจราคาrouteใหม่ภายใน300วินาทีก่อนส่ง หากใช้ MCP ต้องมี OAuth ที่อนุมัติเป็น action แยก ไม่มีการสร้าง/ทดสอบ MCP connection ในรอบนี้ ไม่วนเรียก ordinary `/key` ซ้ำโดยหวังว่าจะกลายเป็น account credit

เมื่อเครดิตพร้อม ใช้ frozen patent pack เดียวกับ local Qwen run ที่อ้างข้างบนและ E2 เดิม เตรียม canary/paired run แบบ sequential ภายใน phase caps พร้อม private case journal/output directory ที่ยังไม่เคยใช้ เก็บ source/payload/model hashes และ failures. ระหว่างรอทำ package/claim/evidence inspection ต่อได้; ไม่ต้องรัน GPU ซ้ำเพียงเพราะ goal ถูกพัก และไม่รัน full tests ทุก checkpoint หากไม่มี source change

Author names/affiliations, declarations และการตัดสินใจ submit/merge เผยแพร่ต้องมีข้อมูล/คำอนุญาตเฉพาะจริง แต่การเตรียมเอกสารและ package ภายในทำต่อได้ ไม่ปลอม author/declaration หรือ promise journal acceptance. ใช้ evidence paths เดิม ไม่เพิ่ม goal/AI4AI/participants เป็นงานบังคับ

## Handoff สำหรับ Luna

ไม่พบเครื่องมือที่ใช้ส่งไปยัง exact Luna session ได้ และไม่มีปลายทาง session ที่ตรวจสอบได้ จึง **ยังไม่ได้ส่งข้อความภายนอกหรือสร้าง goal ซ้ำ** ให้ owner inject ลง goal เดิม:

```text
Resume goal Patent-to-Pilot เดิม อ่าน docs/healthtech/audits/pepo-strong-followup-20261104/README.md ก่อน ใช้ E2 journal เดิมและ local per-case output sink ที่แก้แล้ว อย่าวน R1/GPU/venue gate checks โดยไม่มีข้อมูลใหม่ รอเฉพาะ paid branch จนมี current scoped credit+key limit แล้ว refresh route และทำ paired run ด้วย frozen pack เดิม เก็บคำตอบและ receipts บน Windows ไม่ส่งซ้ำเมื่อ billing ไม่ชัด ทำ release package ของ patch ปัจจุบันต่อโดยไม่รอสิทธิ์เผยแพร่; ขอ owner เฉพาะข้อมูล author/declarations และการตัดสินใจที่ต้องใช้จริง คงผลเป็น descriptive จนมี final holdout/gold ไม่สร้าง goal หรืองบใหม่ และรายงานผลจริงกับต้นทุน
```

ค่าใช้จ่าย/ทรัพยากรรอบ audit นี้: paid calls0, provider metadata0, GPUjobs0, ledger mutations0, downloads0, external messages0; มี CPU recomputation และ tests จริง ไม่มี commit/push/merge ไม่มีลบ raw evidence/docs. Patchเฉพาะงานนี้มี baseline snapshots ใน task workspace และ source hashes ใน verification.json
