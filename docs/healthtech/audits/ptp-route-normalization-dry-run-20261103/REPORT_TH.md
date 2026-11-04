# รายงาน checkpoint route normalization และ parallel paths

## ผลสรุป

สถานะ: `PASS_PAYLOAD_DRY_RUN_API_DISPATCH_BLOCKED_LEDGER_CREDIT`

แก้เฉพาะจุดที่พบจาก API dry-run เดิม: rights-cleared manifest ใช้ route
`deepinfra` แต่ pricing snapshot ใช้ `DeepInfra` และ payload validator เทียบ
string แบบ exact ทำให้ fail ก่อน dispatch การแก้ใหม่ normalize เฉพาะ case และ
whitespace ที่ boundary ของ payload ไม่เพิ่ม route alias, fallback หรือ
auto-routing

ผล dry-run กับ owner-private FDA-only pack:

- 3/3 cases ผ่าน payload/rights validation
- rights decision: `ALLOWED_WITH_ATTRIBUTION`
- manifest route: `deepinfra`
- snapshot/wire route: `DeepInfra`
- manifest SHA-256: `c298b1027e31a270c7db8956cf36a000c854f5c7374e8bb75241881f84729843`
- provider calls: `0`
- paid cost: `USD 0.00`
- status: `DRY_RUN_NOT_EXECUTED`

## Local path

ตรวจพบว่า `local_execution.py` และ regression test จาก worktree รุ่นก่อน
หายจาก current worktree จึงนำเข้าเฉพาะ guard/test/runner delta ที่เกี่ยวข้อง:

- exact approved GPU UUID เท่านั้น
- authorization end: 15 พฤศจิกายน 2026 เวลา 23:59 ไทย
- nonblocking OS-held slot สำหรับ embedding/LLM
- ตรวจ output path ก่อนและหลัง lock เพื่อไม่เขียนทับ receipt
- ตรวจหน้าต่างเวลาอีกครั้งก่อนแต่ละ case
- เก็บ `messages_sha256`, start time และ completion time

ยังไม่ได้เริ่ม model inference ใหม่ เพราะไม่พบ model root ปัจจุบันใน task pack
ที่อนุญาต และ remote allocation ที่เคยตรวจยังเป็น unknown ไม่ใช้ lock marker
ว่างเป็นหลักฐานอนุมัติ

## การตรวจงบและ ledger

ไม่พบ canonical registry ที่
`%LOCALAPPDATA%/PatentToPilot/healthtech/budget-ledgers` และไม่พบ current
canonical journal ในหลักฐานที่เข้าถึงได้ จึงยังไม่ reserve, allocate attempt ID
ใหม่ หรือ dispatch paid API

หลักฐาน historical ที่ตรวจได้ยังคงเป็น debit รวม `USD 0.0001464` และ
unknown-pending `0` ใน legacy receipts แต่ legacy journal ไม่สามารถ bind เป็น
R1 canonical ledger ได้ และไม่พิสูจน์ current account credit

## Tests

- Focused: `26 passed, 0 failed, 0 skipped`
- Full Python: `611 passed, 0 failed, 0 errors, 1 skipped`
- Compile: `PASS`
- Diff check: `PASS`
- Active experiment processes: `0`
- API/GPU/dataset/ledger mutations: `0`

ข้อสรุปคือ local guard และ payload boundary พร้อมตรวจต่อแล้ว ส่วน paid branch
ยัง `BLOCKED_LOCAL` เฉพาะจาก canonical journal และ current credit evidence ไม่ได้
บล็อกงาน local หรือ manuscript ทั้งหมด
