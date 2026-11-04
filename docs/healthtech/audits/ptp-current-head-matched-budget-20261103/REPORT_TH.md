# รายงาน matched-budget current-head

## สถานะ

รอบนี้เป็นการสรุปผลเชิงพรรณนาแบบ post-hoc จากผลรัน offline จริงของ
candidate `88dc40471cb9078f929c02bb893cfa1e364da841` ไม่ใช่ final evaluation
ที่ประกาศไว้ล่วงหน้า และไม่ใช่หลักฐานว่า adaptive evidence acquisition ดีกว่า
baseline

ข้อมูลเป็น development cohort ของอุปกรณ์ Abbott 3 รายการ, สิทธิบัตร 41 รายการ
และ disclosed product-level pairs 61 คู่ ใช้ protocol ที่ freeze แล้วใน
`configs/healthtech/g1_g2_public_cohort_protocol.json` โดยไม่มี final holdout
และไม่มี semantic relevance gold

## ค่า evaluation

| วิธี | prefix | query calls | rerank pairs | Macro known-link Recall@20 | failed | not-realized |
|---|---:|---:|---:|---:|---:|---:|
| HT-B1 | 1 | 3 | 123 | 0.498802 | 0 | 0 |
| HT-B2 | 1 | 3 | 123 | 0.498802 | 0 | 0 |
| HT-B3 | 1 | 3 | 123 | 0.498802 | 0 | 0 |

ช่วงของ Recall@20 ระหว่างสามวิธีคือ `0.0` ภายใต้ slice นี้ จึงสรุปได้เพียงว่า
first-action rows ที่ถูกเลือกมี endpoint เท่ากัน ไม่สามารถสรุปว่าการเลือกหลักฐาน
แบบ adaptive เพิ่มคุณภาพ ลดต้นทุน หรือเพิ่มมูลค่าทางธุรกิจได้

HT-B4 ไม่ถูกรวมใน slice เพราะจำนวน controller steps ไม่ใช่หน่วยเดียวกับ
query calls/rerank pairs การนำมารวมจะทำให้คำว่า matched budget ไม่ตรงกับหลักฐาน

## ข้อจำกัดและการแยกสถานะ

- scientific evidence: `PARTIAL`; เป็น post-hoc descriptive diagnostic และ
  uncertainty ยัง `NOT_ESTIMABLE`
- business validation: `PARTIAL_OPERATIONAL_POTENTIAL_ONLY`; ยังไม่มี external
  user validation, revenue, ROI หรือ willingness-to-pay
- paid API: `BLOCKED_BEFORE_RESERVATION`; ไม่ได้เกิด provider call หรือ cost ใหม่
- ประวัติของ candidate อื่นและ Stryker เป็น diagnostic แยก ไม่ถูกนำมารวมเป็น
  PASS เดียว

หลักฐานเครื่อง: regression tests ผ่าน `6 passed, 0 failed` ใน `tests.xml`
และไฟล์ machine-readable คือ `verification.json` ในโฟลเดอร์ audit เดียวกัน

