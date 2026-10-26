# ตั้งค่า OpenRouter ด้วย .env แบบ explicit

สถานะ: template/loader ทดสอบ offline แล้ว ไม่มี key จริงถูกอ่านหรือสร้าง และยังไม่อนุมัติ budget/funding

## ทำตอนกลับถึงเครื่องบ้าน

1. ใน project folder ทำสำเนา .env.example แล้วตั้งชื่อเป็น .env ถ้ามี .env อยู่แล้ว **อย่า copy ทับ** เปิดแก้ไฟล์เดิมเฉพาะเมื่อคุณตั้งใจเปลี่ยน key ชื่อไฟล์ต้องเป็น .env ไม่ใช่ .env.txt
2. เปิด .env ด้วย Notepad ในเครื่อง แทน REPLACE_WITH_YOUR_OPENROUTER_KEY ด้วย key ของคุณ แล้ว Save แบบ UTF-8 ไม่ส่งค่า key ในแชท/คำสั่ง/ภาพหน้าจอ และห้ามใส่ key จริงใน .env.example
3. ทดสอบ preflight ได้ด้วยคำสั่งด้านล่าง คำสั่งนี้ไม่อ่านไฟล์ key แม้ระบุ --env-file:

```powershell
python -B scripts/dispatch_provider_pilot.py --env-file .env
```

ยังไม่ให้รัน live ตอนนี้ หลังมีคำอนุมัติ Phase A 2 attempts/$0.60 พร้อมยืนยัน funding และมี approval-smoke.json ที่ถูกต้องแล้ว จึงใช้:

```powershell
python -B scripts/dispatch_provider_pilot.py --live --env-file .env --phase smoke --approval results/development/provider-pilot/approval-smoke.json --state results/development/provider-pilot/live.sqlite3
```

## พฤติกรรมที่ยืนยันแล้ว

- ไม่มี auto-load หรือค้นหา .env เอง ต้องระบุ --env-file เสมอ
- Default dry-run และ --mock ไม่อ่านไฟล์ ไม่โหลด key; live ที่ approval/funding ยังไม่ผ่านก็ไม่อ่าน
- OPENROUTER_API_KEY ที่มีใน process environment อยู่แล้วมีลำดับก่อน และจะไม่เปิดไฟล์ในกรณีนี้
- รองรับเฉพาะ OPENROUTER_API_KEY=value หนึ่งบรรทัด มี blank/comment lines และ quotes รอบ literal ได้ รองรับ UTF-8/BOM/CRLF ไม่รองรับ export, multiline, inline comments, variable expansion หรือ shell evaluation
- ไฟล์ผิด/placeholder/ค่าซ้ำ/อ่านไม่ได้ รายงาน fixed error code โดยไม่พิมพ์บรรทัดหรือค่า key
- เมื่อโหลดไฟล์ key จะอยู่ชั่วคราวใน environment ของ Python CLI เพื่อให้ adapter เดิมอ่านได้ แล้ว restore/remove ใน finally ไม่ตั้ง environment ถาวร ไม่มี setx และไม่รับประกันการล้างสำเนาใน process memory ทั้งหมด

**.env เป็น plaintext ไม่ใช่ encrypted credential store.** Git ignore ช่วยกันการ commit โดยไม่ตั้งใจ แต่ไม่ใช่ access control หรือการเข้ารหัส ผู้ที่มีสิทธิ์อ่านไฟล์อาจอ่าน key ได้ ไม่ใช้เพื่อแก้/ลดสิทธิ์ Windows ถ้า executor อ่านไม่ได้ให้หยุดและใช้ owner-run flow ที่ได้รับอนุญาต ไม่ copy ไปที่อื่นหรือเปลี่ยน ACL เพื่อเลี่ยง denial

.gitignore กัน .env และ .env.* แต่เปิดให้ .env.example ที่ไม่มี secret อยู่ใน Git ได้ ตรวจแล้วไม่มี actual .env/.env.* ที่ tracked อยู่ก่อนการเปลี่ยนแปลง ห้าม force-add ไฟล์ key หาก key เคยถูก commit ต้อง revoke/rotate ผ่านเจ้าของก่อน ไม่ถือว่าการเพิ่ม ignore ลบประวัติเดิม

## ผลทดสอบ

71/71 tests ผ่าน: env-file ใหม่ 23 + dispatcher/provider/G11 เดิม 48 ทดสอบด้วย fake values เท่านั้น ปิด socket/DNS ระหว่างชุดทดสอบ รวม parser, precedence, restoration, error redaction, dry-run/mock/unapproved-live gates และ ignore rules ใน repo ชั่วคราวที่เป็นเจ้าของ ไม่มี global safe.directory/ACL/policy changes

DPAPI helper เดิมยังเป็น staging/fake-only ไม่ใช่กลไกที่ติดตั้งแล้ว งานนี้ไม่ได้อ่านหรือสร้างไฟล์ DPAPI ที่ถูกปฏิเสธซ้ำ
