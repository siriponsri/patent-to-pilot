# รายงาน checkpoint: readiness follow-up 2026-11-03

แพ็กเกจนี้เป็นงานต่อของ goal Patent-to-Pilot เดิม ไม่เปิด goal ใหม่ ไม่สร้าง ledger ใหม่ ไม่ reset งบหรือเวลา และไม่เริ่ม batch ทดลองใหม่

## ผลที่ทำเสร็จ

โค้ด `scripts/healthtech/run_real_baselines.py` ใน candidate ปัจจุบันมีการแก้ failure accounting อยู่แล้ว จึงไม่แก้ซ้ำโดยไม่จำเป็น การแก้ที่ตรวจพบทำให้:

- รักษา attempts ที่เกิดขึ้นก่อน failure
- เก็บ wall time และ CPU time ที่วัดได้จริง
- ระบุ resource ที่วัดไม่ได้เป็น `PARTIAL_UNKNOWN`
- ไม่เติม synthetic attempt ที่มี cost เป็นศูนย์
- ส่งต่อ method-level และ attempt-level failure ให้ frontier diagnostics

ผล regression บน HEAD ปัจจุบัน:

- focused package: `49 passed, 1 skipped, 1 warning`
- full Python suite: `596 passed, 1 skipped, 2 warnings`
- skip เดิม: ไม่มี pinned local tokenizer artifact

ไม่เขียนต้นทุนย้อนหลัง และไม่แก้ historical receipt

## ผลกระทบ historical

จากการตรวจ receipt ที่อยู่ในชุด audit ที่เข้าถึงได้ ไม่พบค่า non-zero ของ failed query/device/error ที่ยืนยันว่ารอบใดเสียหายจริง จึงบันทึก `NONE_KNOWN` ไม่ใช่การรับรอง completeness ของ private journal และไม่ใช่เหตุผลให้เดาต้นทุนย้อนหลัง

## การตีความงบ B2/B3/B4

ชุด frozen frontier ใช้ corpus, query, groups, encoder/reranker, `K=20` และ depth ต่อ call `41/41` ร่วมกัน แต่จำนวน retrieval ที่เกิดขึ้นจริงไม่เท่ากัน:

| วิธี | query calls | rerank pairs |
|---|---:|---:|
| HT-B1 | 3 | 123 |
| HT-B2 | 9 | 369 |
| HT-B3 | 5 | 205 |
| HT-B4 offline | 5 | 205 |

HT-B4 มี controller steps อีก 8 ขั้น ซึ่งไม่ใช่ dollar budget หรือ rerank budget เดียวกัน ดังนั้นข้อสรุปที่รองรับคือ descriptive realized quality-resource frontier เท่านั้น ไม่ใช่ matched-total-budget superiority ของ B2/B3/B4 และไม่ถือว่า shared inputs เท่ากับ matched budgets

## สถานะ G0–G8

- G0: `COMPLETE_CONTRACT_AND_SCOPE`
- G1: `PARTIAL_RIGHTS_AND_SEMANTIC_GOLD_INCOMPLETE`
- G2: `PARTIAL_DEVELOPMENT_BASELINES_AND_EVALUATOR`
- G3: `PASS_CURRENT_HEAD_O1_HTTP_UI_ENGINEERING`
- G4: `PARTIAL_DESCRIPTIVE_FRONTIER_NOT_ESTIMABLE`
- G5: `OPERATIONAL_POTENTIAL_ONLY_EXTERNAL_VALIDATION_NOT_VALIDATED`
- G6: `PARTIAL_OWNER_REVIEW_AND_WPI_GUIDE_RECHECK`
- G7: `PASS_ISOLATED_RELEASE_REPRODUCTION_CURRENT_CANDIDATE`
- G8: `NOT_RUN_FUTURE_SCOPE`

ขั้นถัดไปที่ปลอดภัยคือคง paid/API และ new-compute branch ไว้ตาม gate เดิม แล้วรอเฉพาะหลักฐานที่ขาดจริงหรือ owner review ต่อ ไม่เปิด batch ซ้ำเพียงเพื่อเปลี่ยนสถานะเอกสาร
