# เตรียม Patent-to-Pilot ก่อนเติมเงิน

สถานะ: **READY_AWAITING_FUNDING_AND_BUDGET_APPROVAL** — live **NOT_RUN**
วันที่ตรวจข้อมูลสาธารณะ: 26 October 2026 UTC

ปิดงานเตรียมแบบ offline: มี dispatcher ที่รันได้จริงผ่าน mock, journal ก่อน dispatch, resume โดยไม่ยิงงานสำเร็จซ้ำ, bounded retry และการหยุดเมื่อยอดใช้จ่ายไม่ทราบ ยังไม่ได้พิสูจน์ live compatibility หรือผลทางวิจัย

## แผนและงบที่เสนอ

| ทางเลือก | ขอบเขตที่อนุมัติ | ประมาณค่า inference ที่ nominal 4,128 input / 1,500 output | เพดานใช้เครดิต |
|---|---|---:|---:|
| **A แนะนำให้เริ่ม** | smoke 1 ครั้งต่อโมเดล รวมไม่เกิน 2 attempts ไม่มี retry | $0.005064 | **$0.60 สะสม** |
| B หลังตรวจ A | เพิ่ม synthetic packet 2 แบบต่อโมเดล, แต่ละ job ได้ไม่เกิน 2 attempts รวม retry; ทั้งโครงการไม่เกิน 10 attempts | สูงสุดประมาณ $0.02532 สำหรับ 5 attempts ต่อโมเดล | **$1.00 สะสมรวม A** |

เงินสำรองเหนือ nominal estimate คือ $0.594936 สำหรับ A หรือ $0.97468 สำหรับทั้งแผน ไม่ใช่เงินที่ตั้งใจใช้ให้หมด B ต้องมี approval ระบุ phase pilot ต่างหาก การอนุมัติ A ไม่เปิด B

แนะนำให้เจ้าของอนุมัติข้อความ: “อนุมัติ Phase A ของแผน hash ด้านล่าง ไม่เกิน 2 attempts และใช้เครดิตรวมไม่เกิน $0.60 หลังยืนยันเติมเงินแล้ว; ยังไม่อนุมัติ Phase B”

## ราคาปัจจุบันและเงื่อนไข

| model | provider.only | input / output USD ต่อ 1M tokens | advertised context | reservation ต่อ attempt |
|---|---|---|---:|---:|
| google/gemini-2.5-flash-lite | google-ai-studio | $0.10 / $0.40 | 1,048,576 | $0.1054576 |
| openai/gpt-4.1-mini | openai | $0.40 / $1.60 | 1,047,576 | $0.4214304 |

ตรวจจาก public endpoint metadata แบบไม่ใช้ credentials: [Gemini](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints), [GPT-4.1 mini](https://openrouter.ai/api/v1/models/openai/gpt-4.1-mini/endpoints). ทั้งสอง route แสดง max_tokens, structured_outputs, response_format และ status=0 ในเวลาตรวจ การมีใน catalog ไม่รับประกันว่า account/privacy settings หรือ service ณ เวลารันจะยอมรับ request

ทุก request ส่ง exact model, provider.only, allow_fallbacks=false, require_parameters=true, max_price ที่ตรงตาราง และ max_tokens=1500 ไม่มี tools/web/search/plugins/tier/reasoning override หรือข้อมูลลับ มีเพียง synthetic engineering echo ที่อยู่ในแผน ไม่มี corpus, hidden evaluator answers, frozen research cases หรือการประเมินประโยชน์เชิงวิทยาศาสตร์

สูตร nominal คือ (4128×input_rate + 1500×output_rate)/1,000,000 จึงได้ $0.0010128 / $0.0040512 ต่อ attempt ตัวเลข 4000+128 เป็น illustration ไม่ใช่ tokenizer bound และไม่ใช่ actual cost

**Reservation ใช้ advertised context ทั้งหมดเป็น input bound** (รวม schema/framing) บวก output 1500 ไม่ได้ใช้ 128 เป็นหลักประกัน รายงาน actual ใช้ usage.cost และ normalized usage จาก response เท่านั้น

เพดานเป็นการควบคุม dispatch/reservation ของแอป ภายใต้สมมติฐานว่า provider เคารพ context length, max_tokens, max_price และไม่มีค่า auxiliary ที่ไม่ได้ร้องขอ ไม่ใช่คำรับประกัน invoice โดยไม่มีเงื่อนไข หาก debit เกิน reservation จะเก็บยอดจริงและหยุด dispatch ถัดไป หากยอดไม่ทราบจะหยุดและไม่ถือว่าเป็นศูนย์ Worst-case เต็ม reservation ทุกครั้งอาจทำให้จบไม่ครบ 10 attempts เพราะแอปจะหยุดก่อนส่งครั้งที่เหลืองบไม่พอ

## ยอดเติมเงิน แยกจากงบโครงการ

[เงื่อนไข OpenRouter](https://openrouter.ai/terms) ระบุขั้นต่ำซื้อเครดิต $5 ต่อ transaction; [pricing ปัจจุบัน](https://openrouter.ai/pricing) ระบุ Standard fee 5.5% และ Business 8% บนการซื้อเครดิต ไม่บวก inference ทุกครั้ง [ประกาศ fee ทางการ](https://openrouter.ai/blog/announcements/simplifying-our-platform-fee/) ระบุ non-crypto fee ขั้นต่ำ $0.80

ถ้ายังไม่มีเครดิต เสนอซื้อ **$5 credits** สำหรับ Standard; กันเงินสดประมาณ **$5.80 ก่อนภาษี/FX/ค่าธนาคาร** หาก checkout บวก minimum fee ตามประกาศ ต้องดูยอด checkout จริงก่อนจ่าย เพราะยังไม่ตรวจ account tier/ภาษี/checkout ของเจ้าของ และไม่ถือ $5.80 เป็นยอดยืนยัน เครดิตส่วนที่เหลือไม่ใช่สิทธิ์ให้โครงการใช้เกินวงเงินที่อนุมัติ ไม่ต้องเติม $200 และไม่เปิด auto top-up เพื่อแผนนี้

## กลไกที่ตรวจแล้ว

- Journal SQLite commit reservation ก่อนทุก transport.send; lock SQLite อีกไฟล์กัน dispatcher รันซ้อน และ OS ปลด lock เมื่อ process ตาย
- ใช้ ledger เดียวข้ามโมเดลและ retries; คืน accounting ผ่าน reserve/settle เดิมเมื่อ resume โดยไม่ reset charges
- นับ dispatched attempts รวม phase/job/retry; adapter retries=0, dispatcher คุม retry ต่อ job เอง
- known charged schema failure retry ได้ภายใน job/phase/project limits; timeout/HTTP failure ที่ billing ไม่ทราบ, response ขาด billing หรือ crash หยุดทั้ง batch เป็น unknown_pending
- unknown_pending ไม่ยิงซ้ำอัตโนมัติ ต้องมี provider billing evidence ที่ได้รับอนุมัติผูก plan hash/attempt ก่อน append reconciliation; ไม่ลบ raw journal ไม่เปลี่ยน unknown เป็น free และไม่อ้างว่างานสำเร็จเพราะ reconcile
- approval ผูก canonical state path; durable activation marker กันการเริ่มนับใหม่ถ้า DB เดิมหาย ห้ามเปลี่ยน state path/ลบ activation เพื่อเลี่ยงเพดาน; ถ้ากู้ข้อมูลไม่ได้ให้หยุด
- live state/approval/activation อยู่ใต้ folder ที่ .gitignore ปกป้อง
- jobs ที่สำเร็จแล้วถูกข้ามเมื่อ resume; mock/live และ plan hashes ใช้ state ร่วมกันไม่ได้
- approval ต้องตรง phase, วงเงิน, attempt limit, plan hash, owner reference และ funding_confirmed=true ก่อนสร้าง transport หรืออ่าน key
- ทดสอบ 48 tests ผ่าน: dispatcher ใหม่ 18 + provider/G11 เดิม 30; sockets/DNS ถูกปิดระหว่างชุดทดสอบ ไม่มี inference API calls

## คำสั่งที่เตรียมไว้

จาก project root ตรวจแผนโดยไม่อ่าน key/ไม่สร้าง run state:

```powershell
rtk proxy python -B scripts/dispatch_provider_pilot.py
```

ทดสอบ mock ใน TEMP (state แยกจาก live):

```powershell
rtk proxy python -B scripts/dispatch_provider_pilot.py --mock --phase smoke --state "$env:TEMP/ptp-mock-smoke.sqlite3"
rtk proxy python -B scripts/dispatch_provider_pilot.py --mock --phase pilot --state "$env:TEMP/ptp-mock-smoke.sqlite3"
```

**ยังห้ามรัน live ตอนนี้** หลังเจ้าของอนุมัติ A + ยืนยันเติมเงินแล้ว agent จึงบันทึก approval จาก template โดยใช้ owner message reference จริง และตรวจ key availability ผ่าน environment แบบไม่พิมพ์ค่า key ห้ามส่ง key ใน chat/commit/config

```powershell
rtk proxy python -B scripts/dispatch_provider_pilot.py --live --phase smoke --approval results/development/provider-pilot/approval-smoke.json --state results/development/provider-pilot/live.sqlite3
```

คำสั่งเดิมใช้ resume ได้ จะไม่ทำงานสำเร็จซ้ำ ถ้าจะรัน B ต้องมี approval-pilot.json ที่อนุมัติ phase pilot/8 additional attempts และเพดานสะสม $1.00:

```powershell
rtk proxy python -B scripts/dispatch_provider_pilot.py --live --phase pilot --approval results/development/provider-pilot/approval-pilot.json --state results/development/provider-pilot/live.sqlite3
```

ถ้าต้อง reconcile ให้ agent ตรวจ billing evidence ก่อนแล้วใช้ --reconcile receipt.json ไม่เดาค่า 0 จาก timeout หากพิสูจน์ยอดไม่ได้ให้คง blocked ไว้ ถ้าหมด job attempts แล้วไม่สร้าง plan/state ใหม่เพื่อเลี่ยงเพดาน

## สถานะรอเจ้าของ

- [x] implementation, mock safeguards, persisted resume และ focused G11/provider regressions
- [x] exact staged matrix, current public endpoint observations, cost formula และข้อจำกัด
- [x] default dry-run/approval gate; template approved=false/funding_confirmed=false
- [ ] owner เลือก A (แนะนำ) หรืออนุมัติ A+B ด้วยวงเงินและ attempts ชัดเจน
- [ ] owner ยืนยันเครดิตพร้อมใช้หลังเติมเงิน และ key อยู่ใน environment ที่อนุญาตให้ใช้ภายหลัง; ตอนเตรียมงานนี้ยังไม่อ่าน key จริง
- [ ] live smoke compatibility, measured tokens/debit/latency และผลทดสอบจริง — NOT_RUN

แผนเป็น editable proposal นอก frozen methodology การแก้ matrix/prompt/rates/limits เปลี่ยน hash และทำให้ approval/state เดิมใช้ไม่ได้ Funding confirmation อย่างเดียวไม่สร้าง approval หรือเริ่มงานใด

Plan SHA256: `6cf9bd14059f1df9f11ff6f913d31bcc5e5c60f3f993ac4766621bf1c7c148b2`
