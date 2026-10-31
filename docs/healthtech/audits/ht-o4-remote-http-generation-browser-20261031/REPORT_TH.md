# รายงานวิจัยและผลิตภัณฑ์ HealthTech — O1-O4 — 31 ตุลาคม 2026

สถานะ: `PARTIAL_O4_ENGINEERING_PASS_O3_BLOCKED_LOCAL`

รายงานนี้เป็น handoff ปัจจุบันของ 3 named Abbott cases และแก้ขอบเขตที่
เอกสาร parent เดิมยังระบุว่า HTTP generation ยังไม่ถูกทดสอบ

## ผล E2E

| Case | PatEmbed candidates | e5 candidates | HTTP | Generation | History/export |
|---|---:|---:|---|---|---|
| MitraClip | 33 | 33 | succeeded | schema-valid, 32.888s | `1 -> 2`, JSON v2 |
| Tendyne | 33 | 33 | succeeded | schema-valid, 33.059s | `1 -> 2`, JSON v2 |
| TriClip | 41 | 41 | succeeded | schema-valid, 33.121s | `1 -> 2`, JSON v2 |

ทั้ง 3 cases ผ่าน browser → HTTP → vector retrieval → local Qwen3-8B →
source inspection → history → export ครบถ้วน ไม่มี vector errors, paid calls
หรือ paid cost (`USD 0.00`)

## Grouped retrieval

- **Mitral pair:** MitraClip และ Tendyne มี candidate count 33 ต่อ caseสำหรับ
  encoder ทั้งสองตัว และไม่พบ runtime failure
- **Tricuspid:** TriClip มี candidate count 41 และไม่พบ runtime failure

Candidate count ที่เท่ากันเป็นเพียง execution receipt ไม่ใช่หลักฐานว่า
ranking หรือ quality ของ encoder ทั้งสองเท่ากัน

## Reference fixed-budget frontier

ตารางนี้เป็น **Stryker final holdout ที่นำมาอ้างซ้ำ** ไม่ใช่ผลของ Abbott
browser cohort ปัจจุบัน โดยอ้างจาก comparison ที่มี 3 queries, 24 patents,
3 family-aware groups, protocol hash
`1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`, cohort
manifest hash `1b42b7c4a52b697d9c5c4f7db4f9236b7d5d239d83584863a6ba844591adef75`
และ comparison code commit
`b12ef954a22f30c33e87c6ed78d8d40cc97d4fe3`:

- HT-B0a: `0.8190`, 3 query calls
- HT-B0b: `0.9524`, 3 query calls
- HT-B1: `0.9333`, 3 calls, 72 rerank pairs
- HT-B2: `0.9333`, 12 calls, 288 rerank pairs
- HT-B3: `0.8857`, 5 calls, 120 rerank pairs
- HT-B4-MOCK: `0.8857`, simulated cost `USD 0.0008`, mock-only

ใน Stryker reference comparison นี้ B0b ให้ Recall สูงสุดด้วยจำนวน query ต่ำกว่า
B2 แต่เป็นผล descriptive เฉพาะ holdout นั้น ไม่ใช่ผลของ Abbott และไม่ใช่
หลักฐานว่า adaptive แย่กว่า fixed controls โดยทั่วไป

สำหรับ Abbott development cohort ปัจจุบัน deterministic controller report ให้
macro known-link Recall@20 เท่ากับ `0.498802` จาก 3 devices, 41 runtime patents,
5 query calls และ 8 controller steps โดยยังไม่มีการ rerun fixed controls แบบ
matched บน Abbott ใน browser package นี้ จึงห้ามจัดอันดับค่านี้เทียบกับตาราง
Stryker ด้านบน

## O3 และข้อจำกัด

Qwen3-8B local ให้ schema-valid `3/3` ที่ latency ประมาณ 32.888–33.121 วินาที
และไม่มีค่าใช้จ่ายแบบ paid provider ส่วน OpenRouter qwen3-32b ยัง
`BLOCKED_LOCAL` เพราะ canonical ledger, current credit, fresh route/parameter
checks และ rights-cleared prompt manifest ยังไม่ครบ จึงไม่มีการเรียก API โดย
สิทธิ์เดิม USD8 อนุมัติ local generator 1 ตัวและ API generator 1 ตัวอยู่แล้ว

ส่วน engineering ที่ทำต่อแบบ offline เสร็จแล้ว: แก้ gate ไม่ให้ตีความสิทธิ์เดิม
เป็น `NOT_GRANTED`, เพิ่ม canonical ledger registry ที่ปฏิเสธการสลับ path และไม่
สร้าง journal ใหม่, ต่อ paired payload/API runner พร้อม mock/dry-run tests และ
เพิ่ม validation ไม่ให้ `retrieved_candidate` ถูกยกระดับเป็น `disclosed_link`
โดยไม่มี disclosure provenance. ส่วนนี้ยังไม่ปลด paid branch เพราะยังไม่มี
journal จริงและหลักฐานเครดิตปัจจุบันสำหรับ reconcile.

ผลนี้เป็น engineering/research handoff ไม่ใช่ semantic patent gold, exhaustive
recall, clinical/FTO, patent validity, investment, deployment หรือ commercial
validation
