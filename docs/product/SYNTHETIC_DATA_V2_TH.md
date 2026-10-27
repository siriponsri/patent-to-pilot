# Synthetic development corpus รุ่น 2

วันที่ 27 ตุลาคม 2026 · `methodology/development/synthetic-20261027-v2/`

มี 48 cases จาก 24 fictional families และ 4 template components แบ่ง development24/demo24 ไม่แยก variant ของ family/template เดียวข้าม split
เลข 48 เป็นจำนวนแถวสำหรับพัฒนา ส่วน independent real validation cases เท่ากับ **0** Development/demo สองชุดไม่ได้หมายถึง train/test ของการทดลองวิจัย

## Coverage และ provenance

- domains: barrier film, powder mixing, sensor housing, water filtration เป็นสถานการณ์แต่ง ไม่ใช่ผลิตภัณฑ์ที่ยืนยันความเป็นไปได้
- changes: evidence withdrawal, policy revision, contradictory capacity, partner delay
- unknowns: demand, valuation, FTO, partner access; ไม่มี revenue/ROI/clinical/legal gold
- Seed20261027, generator version `ptp-synthetic-20261027-v2`, SHA256 ทุกไฟล์อยู่ manifest
- รูปแบบที่สร้างจริง: JSON current input, Markdown/text source documents และ CSV inventory ไม่มี image/PDF/OCR claims
- pseudo-source IDs ขึ้นต้น SYN- ไม่ปลอมเป็นเลข patent จริง ข้อความและสิทธิ์ระบุ project-authored synthetic fixture ภายใต้ repository license ไม่คัดลอก third-party patent

## Runtime boundary

Mount **เฉพาะ current/{case_id}.json ที่เลือกแล้ว** ให้ runtime รูปแบบนี้เป็น product demo contract ไม่ใช่ scientific AgentPacket และไม่มี adapter ไปสู่ benchmark โดยอัตโนมัติ
`corpus.json` มี curator future events ส่วน `inventory.csv`/manifest มี split/template information จึงไม่ให้ evaluated method อ่านทั้งโฟลเดอร์
การคัดไฟล์นี้เป็นการเตรียม boundary ไม่ใช่ OS isolation ซึ่งยังต้องทำแยก

## Quality controls และ limits

Validator ตรวจ duplicate identity, explicit synthetic label, source content/hash, capacity cross-field consistency, event source/version, route partition, split grouping และ closed source/profile shape
Tests มี tampered hash, hidden nested field, false independent-validation claim, heldout contamination, duplicate, route overlap และ family/template split leakage
ค่าที่ validator ผ่านหมายถึง consistency ของ fixture ไม่ใช่ความจริงของตลาด/เทคนิค Coverage ยังเล็กและ authored template มาก จึงห้ามเอาเป็นหลักฐาน business effectiveness หรือ uncertainty ของ real-world population

ขยายได้ด้วย seed/families 8–120 หาร4ลงตัว ค่าเริ่มต้น24families ไม่รันใหญ่เพื่อเพิ่มจำนวนเฉย ๆ ถ้าต้องเปลี่ยน template/grouping ให้ version และตรวจ split ก่อนใช้
