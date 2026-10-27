# HealthTech user journey

เป้าหมายคือผู้ประกอบการหรือนักวิเคราะห์เลือก device/comparator ที่มีชื่อหรือรหัสแล้ว ตรวจแหล่งของแต่ละ fact แยก candidate จาก disclosed association ระบุสิ่งที่ต้องขอเพิ่ม แล้วแก้/ส่งออกแฟ้มเพื่อนำไปหารือ

เส้นทางที่รันได้ในปัจจุบันเป็น CLI: supplied local input → FTS/fixed queries → source integrity checks → `dossier.json` และ `dossier.md` ตัวอย่างเป็น synthetic ทั้งชุด เปิด Markdown เพื่ออ่าน/แก้ได้ ยังไม่ใช่ no-code UI หรือหลักฐานว่าผู้ใช้ทำงานสำเร็จ

เส้นทางเป้าหมายมี TH/EN source viewer, evidence editing, project history และ export ดู [PLAN](../../PLAN.md) W12/W13/W16 UI ต้องรักษา language/theme choices จาก `ProjectBrief` และไม่แสดง internal test/engineering details เป็นขั้นตอนที่ผู้ใช้ต้องตัดสินใจ
