# Checkpoint readiness recheck R3: 3 พฤศจิกายน 2026

แพ็กเกจนี้ทำต่อใน goal Patent-to-Pilot เดิม ไม่เปิด goal ใหม่ และไม่เริ่ม batch
ถัดไป เพราะการตรวจที่ร้องขอเสร็จได้โดยไม่ต้องใช้ API หรือ GPU

## ผลการตรวจ failure accounting

Source ที่ HEAD `88dc40471cb9078f929c02bb893cfa1e364da841` มี repair อยู่แล้วจาก
`0d092019` และ regression hardening จาก `323bcc5` จึงไม่ทำ duplicate patch และ
ไม่แก้ runner กลางรอบใด ๆ พฤติกรรมที่ยืนยันได้คือ:

- เก็บ attempt ที่เริ่มไปแล้วและลำดับเดิมไว้
- เก็บ wall/CPU elapsed time ที่วัดได้เมื่อเกิด exception
- ระบุ resource ที่ยังวัดไม่ได้เป็น `PARTIAL_UNKNOWN`
- ไม่เติม synthetic attempt ที่มีค่าเป็นศูนย์
- ไม่เขียน historical receipt หรือเดาต้นทุนย้อนหลัง

จาก audit receipts ที่เข้าถึงได้ยังพบผลกระทบรอบเดิมเป็น `NONE_KNOWN` แต่ private
journal ที่เข้าถึงไม่ได้ยังไม่สามารถยืนยันความครบถ้วนได้

## ผลทดสอบบน candidate ปัจจุบัน

- Focused regression/budget tests: `52 passed, 1 skipped, 1 warning`
- Full Python suite: `599 passed, 1 skipped, 2 warnings`, exit `0`
- Skip เดิม: pinned local tokenizer artifact unavailable
- ไม่มี local experiment process ระหว่างตรวจ และไม่ได้เริ่ม batch ใหม่

## การตีความงบ B2/B3/B4

ทุกวิธีใช้ frozen inputs, references/groups, encoder/reranker, `K=20`,
`candidate_depth=41` และ `rerank_depth=41` ร่วมกัน แต่ realized total budget
ต่างกัน:

| วิธี | Query calls | Rerank pairs | Macro Recall@20 | สถานะการเทียบ |
|---|---:|---:|---:|---|
| HT-B1 | 3 | 123 | 0.498802 | fixed reference |
| HT-B2 | 9 | 369 | 0.568912 | ใช้ retrieval มากกว่า |
| HT-B3 | 5 | 205 | 0.498802 | heuristic prefix |
| HT-B4 offline | 5 | 205 | 0.498802 | มี controller steps เพิ่ม 8; เป็นคนละหน่วย |

ดังนั้นผลรองรับเพียง descriptive realized quality-resource frontier ไม่รองรับ
equal-total-budget หรือ adaptive-superiority claim

มี post-hoc prefix diagnostic จาก candidate เก่า `891f3b3` ที่ `3/123` และ
Recall `0.498802` เท่ากันสำหรับ B1, B2-prefix-1 และ B3-prefix-1 แต่ไม่ใช่
current-head final endpoint และไม่รวม B4 เพราะ controller steps เทียบตรงกับ
query/rerank pairs ไม่ได้

## สถานะ checkpoint

- Engineering: `COMPLETE`
- Scientific evidence: `PARTIAL_DESCRIPTIVE_FRONTIER_NOT_ESTIMABLE`
- Business validation: `PARTIAL_OPERATIONAL_POTENTIAL_ONLY`
- Manuscript readiness: `PARTIAL_OWNER_REVIEW_AND_WPI_GUIDE_RECHECK`

ไม่มี API call, GPU job, dataset download, ledger mutation, budget reset หรือ
window reset ในรอบนี้ ขั้นถัดไปคือหยุดที่ checkpoint นี้ รักษา receipts ที่ผูกกับ
candidate และรอ owner review หรือทำเฉพาะ offline work ที่ได้รับอนุญาตแล้ว

รายละเอียด machine-readable อยู่ใน
`READINESS_RECHECK_R3_20261103.json` และ raw JUnit อยู่ในไฟล์ `*-r3-20261103.xml`
ใน audit directory เดียวกัน
