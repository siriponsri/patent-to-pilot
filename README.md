# Patent-to-Pilot

**วิสัยทัศน์ล่าสุด:** Organization-Adaptive R&D Agent — organization sources/capabilities → opportunities/routes → draft pilot/handoff → confirmed-feedback learning และ project adaptation

**Agent หลักที่เจ้าของเลือก:** `gpt 5.6 luna max` สำหรับ coding/research (runtime mapping/availability ยังไม่ยืนยัน) แยกจาก product inference API ดู [วิธีเริ่ม/ทำต่อ](docs/CODEX_CLI_HANDOFF.md) ไม่ต้องเปิด memory server หรือ audit ทั้งโครงการเพื่อเริ่มงาน

แผนผลิตภัณฑ์และการศึกษาระบบสารสนเทศสิทธิบัตร ภายใต้ข้อจำกัดองค์กรที่เปลี่ยนได้

เริ่มที่ [GOAL.md: G01–G22](GOAL.md) และ [AGENTS.md](AGENTS.md) แล้วใช้ [docs/PLAN.md](docs/PLAN.md) เป็นรายละเอียดฐาน แล้วดู [literature/reading order](literature-review/README.md), [dataset inventory](methodology/datasets/INVENTORY.md) และ [evaluation protocol](methodology/evaluation/PROTOCOL.md)

เจ้าของโครงการเป็นเภสัชกรและยังไม่มีผู้เชี่ยวชาญอิสระทำ gold standard เริ่ม technical study ที่มี source-backed facts/explicit validators ได้ ส่วน natural cases ใช้ owner review แบบ formative ไม่ใช่ independent clinical/legal validation

รอบจัดเตรียม 24 ตุลาคม 2026 มี PDFs ภายนอก 35 ฉบับและ internal Paper 53 แยกอีก 1 ฉบับพร้อม manifest และ dataset metadata/qrels/samples ขนาดเล็ก มี PTP-0001 หนึ่ง development case พร้อม authored fixtures แต่ยังไม่มี product implementation, model run หรือ scientific results ไม่ได้ใช้ paid compute และไม่ได้ publish/Git-push

ตรวจไฟล์แบบ offline จาก project root:

```powershell
python methodology/codes/verify_assets.py
```

ดูผลตรวจและสิ่งที่ยังไม่ได้ที่ [docs/COMPLETION_REPORT.md](docs/COMPLETION_REPORT.md) PDFs เป็น reading copies ในเครื่อง การดาวน์โหลดได้ไม่เท่ากับมีสิทธิ์เผยแพร่ทุกฉบับต่อสาธารณะ แยก DAPFAM NC data จาก commercial product corpus และตรวจสิทธิ์ก่อนเผยแพร่ artifacts


อัปเดตรอบรับ PDF: เริ่มอ่าน [ตัวอย่างแรกที่ผู้ใช้กรอก/ได้รับ](docs/FIRST_CASE_WALKTHROUGH.md) และ [gap matrix](docs/RESEARCH_GAP_MATRIX.md) ดูผลรอบนี้ที่ [research progress](docs/RESEARCH_PROGRESS_2026-10-24.md)
