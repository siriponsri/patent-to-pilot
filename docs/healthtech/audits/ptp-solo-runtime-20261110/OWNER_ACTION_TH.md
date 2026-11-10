# ขั้นตอน curator สำหรับ MTM

เตรียมโค้ดและตรวจ hash แล้วจาก commit `8ff53ab8d4cfe156f79ee464eddd7e0ecff8e901`
ยังไม่ได้อ่าน mixed metadata หรือจัดข้อมูลจริงผ่าน agent

ให้คุณเปิด PowerShell แล้วรันคำสั่งนี้ด้วยตัวเอง:

```powershell
ssh chaw@100.77.149.83 "bash /home/chaw/patent-to-pilot-jobs/owner-curator-mtm-20261110-v1/owner-stage-mtm.sh --owner-curator"
```

คำสั่งใช้เครื่องและข้อมูลเดิม ไม่ต้องตั้งสิทธิ์เพิ่ม ไม่ใช้ GPU และไม่เปิดการประเมิน test
จะอ่านข้อมูลรวมในบทบาท curator เพื่อแยก runtime/dev, dev evaluator และส่วนที่ปิดไว้
พร้อมเตรียม corpus ที่ตัด construction roles ออก และเก็บ query P-dev ตาม bytes เดิม
ต้นฉบับไม่ถูกแก้ ไม่สร้าง query ใหม่ และไม่ตัด query ที่ล้มเหลวออกเพื่อเพิ่มคะแนน

เวลาสูงสุด30นาที จำกัด address space32GiB/threads8 และใช้ project lock เดียวกัน
ถ้าพบงานอื่นค้างจะไม่เริ่ม ถ้ามี staging directory อยู่แล้วจะไม่เขียนทับหรือเริ่มซ้ำ
กรณีล้มเหลวให้เก็บ output เดิมและแจ้งสถานะ ไม่ต้องส่ง rows, labels, IDs หรือเนื้อหา corpus

ถ้าสำเร็จ แจ้งเพียงว่า `Owner staging complete` ผมจะตรวจ completion marker และ
receipts ที่อนุญาต แล้วสร้าง runtime/evaluator container แยกกันตาม mounts ที่ตรวจจริง
การจัดข้อมูลเสร็จอย่างเดียวยังไม่ใช่การยืนยัน isolation หรือ baseline parity ผ่าน

ขั้นตอนนี้เป็นของ MTM เท่านั้น ไม่ใช้แทนการจัด DAPFAM ซึ่งต้องรักษา split เดิมและ
สร้าง dev query แบบ native TA ไม่ใช้ไฟล์ TAC เดิมแทนโดยเงียบ ๆ ไม่มีการประเมิน test
หรือรันโมเดลเกิดขึ้นจากคำสั่งนี้ ส่วน hidden/test outputs จะไม่ถูก mount เข้า runtime

ข้อจำกัด: owner คนเดียวทำ curator และ review ได้ แต่ไม่เรียกว่า independent curation
Codex ฝั่งควบคุมยังมีสิทธิ์ host ตามที่เปิดเผยไว้ และจะไม่อ่านไฟล์ mixed/protected
