# 04 — Data Registry (verified / blocked / unknown)

| แหล่ง | สถานะ | รายละเอียด | หมายเหตุ |
|---|---|---|---|
| openFDA `/drug/orangebook.json` | VERIFIED | fields: approval_date (YYYYMMDD), exclusivity[], patents[], products[] | **patent/exclusivity เป็น snapshot ปัจจุบันเท่านั้น** |
| openFDA `/drug/drugsfda.json` | VERIFIED | NDA/ANDA/BLA; ORIG AP date ใช้เป็นวัน approval; TYPE 1 = NME; orphan; review_priority | submission_status_date = สถานะล่าสุดเท่านั้น |
| ดึงข้อมูลจริง 2026-11-27 | VERIFIED | ob_nda 10,922; ob_anda_pre1982 3,196; ob_anda_to2009 13,595; ob_anda_2010s 11,576; ob_anda_2020plus 9,701; df_nda 5,921; df_anda 23,072; df_bla 488 | sha256 ใน data/MANIFEST.json |
| Purple Book รายเดือน (CSV) | VERIFIED (บางเดือน) | ดาวน์โหลดผ่านบริการ scrape ได้ (curl ถูกบล็อกด้วยหน้าบอท); เมษายน 2024 parse ได้ 1,971 แถว, 98 แถว 351(k) Original | รูปแบบ URL: `.../PurpleBook/<year>/purplebook-search-<month>-data-download.csv` เดือนอื่นต้องตรวจหน้ารายการ; dedupe ตาม BLA |
| ClinicalTrials.gov API v2 | VERIFIED | `https://clinicaltrials.gov/api/v2/studies` | ใช้ใน IS3 |
| Orange Book edition ย้อนหลัง | UNKNOWN / BLOCKED (G1) | จำเป็นสำหรับ patent feature ย้อนหลัง | ต้องค้นหน้า Orange Book data files ของ FDA (archive) หรือ Wayback; ถ้าไม่ได้ ใช้ Track A + Track C ที่ไม่มี patent |
| ข้อมูลยอดขาย/ผลการคาดการณ์ของนักวิเคราะห์ | UNKNOWN | ไม่ใช่ข้อมูลสาธารณะแบบเปิด | อาจต้องซื้อ/ใช้ผลจากวรรณกรรม; ส่งผลต่อ IS3 |
| ข้อมูลไทย (ซื้อจัดหา) | SECONDARY, UNVERIFIED | เกณฑ์ ≤500,000 บาท วิธีเฉพาะเจาะจง; สูงกว่านั้น e-bidding ใน e-GP; 500,000–5,000,000 บาท คัดเลือก/ต่อรอง; ป.ป.ช. เปิดเผย ≥500,000 บาท | ต้องตรวจกฎหมายล่าสุดจากแหล่งทางการ |
| คู่แข่ง DrugPatentWatch | VERIFIED (เว็บผู้ขาย) | ทำ generic-entry prediction, patent risk, litigation tracker; ผู้ขายอ้างว่าที่ปรึกษา boutique คิด $20k–$100k+ ต่องาน; softwarefinder ระบุ $1,000/$3,000 ต่อเดือน (แหล่งรอง ไม่ยืนยัน) | Cortellis, Citeline, Evaluate, PatSnap/Derwent, Lens **ยังไม่ได้ตรวจ** |

## ข้อควรระวังสำคัญ
- ห้ามใช้ patent snapshot ปัจจุบันเป็นฟีเจอร์ของ cutoff ในอดีต (leakage)
- Track A แก้ปัญหานี้ด้วยการ freeze วันนี้แล้วให้อนาคตเป็นตัวตัดสิน
- ingredient key เป็น proxy หยาบ ให้ตรวจสุ่ม 100 รายการด้วยมือ (task card T7)
- หลังทุกการดึง: บันทึก sha256 + fetched_at
