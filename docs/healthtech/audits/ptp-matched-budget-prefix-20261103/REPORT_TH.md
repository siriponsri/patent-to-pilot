# รายงาน matched-budget prefix diagnostic — 2026-11-03

แพ็กเกจนี้วิเคราะห์ receipt O4 เดิมจาก private artifact โดยไม่ rerun retrieval ไม่โหลด dataset ไม่ใช้ GPU ไม่เรียก API และไม่เปลี่ยน ledger

## ผล

เลือก budget เดียวกันที่ `3 query calls` และ `123 rerank pairs` แล้วอ่าน first action ของ B1/B2/B3:

| วิธี | prefix | query calls | rerank pairs | Macro Recall@20 |
|---|---:|---:|---:|---:|
| HT-B1 | 1 | 3 | 123 | 0.498802 |
| HT-B2 | 1 | 3 | 123 | 0.498802 |
| HT-B3 | 1 | 3 | 123 | 0.498802 |

ทุกแถวมี failed และ not-realized query เป็นศูนย์ ช่วงค่าของ endpoint ใน slice นี้จึงเป็น `0.0`

## ขอบเขตการอ้างผล

นี่เป็น post-hoc descriptive first-action control ไม่ใช่ preregistered final endpoint และยังไม่ใช่การทดสอบ adaptive behavior ที่เสร็จสมบูรณ์ของ B3 จึงไม่สนับสนุนข้อสรุปว่า adaptive acquisition เหนือกว่า baseline

ไม่รวม B4 เพราะ controller steps ไม่ใช่หน่วยเดียวกับ query/rerank budget และ receipt เดิมไม่มี same-unit final slice ที่ประกาศไว้ล่วงหน้า cohort นี้ไม่มี final holdout และใช้ product-level disclosed links ไม่ใช่ semantic relevance gold

เพิ่มผลนี้ใน manuscript ภาษาอังกฤษแล้ว โดยคงสถานะ scientific evidence เป็น PARTIAL
