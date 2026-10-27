# Patent-to-Pilot — ข้อกำหนดที่เจ้าของยืนยัน รุ่น 2

วันที่ 27 ตุลาคม 2026 · อ้างอิง owner decision `Sentinel_724546b367448191abc0389ac1968fa8` และคำขอ publication `Sentinel_c92ab7eb9a30819189a87dfed4d6cea4`

เอกสารนี้แทนสถานะ PENDING ที่ได้รับคำตอบแล้วใน [รุ่น 1](REQUIREMENTS_DECISIONS_20261027_V1_TH.md) รุ่นเก่าเก็บไว้เป็นประวัติ ไม่แก้ GOAL G01–G22 หรือ protocol ย้อนหลัง

## สิ่งที่ตกลงแล้ว

| ID | ข้อกำหนด | Acceptance ที่ตรวจได้ |
|---|---|---|
| R01 | ไปถึง complete deployable repository และบทความสำหรับวารสารระดับนานาชาติ | แยก engineering release-ready, scientific pilot-ready และ journal submission-ready; ไม่รับรองการตอบรับ ไม่ส่งบทความหรือจ่าย APC เอง |
| R02 | ให้ความสำคัญกับผู้ประกอบการและนักลงทุน ใช้ R&D เป็นเครื่องยนต์เบื้องหลัง | ทำ discovery/due-diligence brief ที่ย้อนกลับหลักฐานได้ กลุ่มผู้ใช้ยังไม่ผ่าน user research; ไม่มี automated investment/FTO verdict/valuation |
| R03 | no-code และลดภาระผู้ใช้ | เริ่มจาก brief สั้นและแหล่งข้อมูล ดึงข้อมูล/default ให้อัตโนมัติ เปิดรายละเอียดเมื่อจำเป็น ยืนยันเฉพาะ critical interpretation, outbound disclosure และ release export |
| R04 | เตรียมข้อมูลสังเคราะห์ให้สมจริงและครอบคลุม เพราะยังไม่มีข้อมูลจริงขององค์กร | generator ทำซ้ำได้ มี seed/coverage/validator; SYNTHETIC ทุกเคส ไม่ปะปน held-out real cases ไม่แต่ง scientific gold |
| R05 | minimal/formal ปรับหลาย theme รวม KMITL และ ICT | มี theme identifiers; สีสถาบัน/โลโก้/endorsement ยังไม่ verified ใช้ inspired placeholder จน Claude ตรวจ official identity |
| R06 | OpenRouter ใหม่รวม USD 5 | ทุก agent/retry/calibration/pilot/UI test ใช้ยอดร่วมเดียวกัน ภายในแบ่ง calibration $1 และ subsequent $4; ไม่ใช้เครดิต $10 เป็น cap ไม่รวมยอดเก่า ไม่เติมอัตโนมัติ |
| R07 | ส่งได้เฉพาะ public patent text หรือ synthetic ที่อยู่ใน manifest | OpenRouter → google-ai-studio / Gemini 2.5 Flash Lite และ OpenAI / GPT-4.1 Mini เท่านั้น ไม่มี fallback/provider expansion/private source |
| R08 | Pepo push งาน scoped เข้า main ของ origin เดิมได้; Claude แยก branch | ก่อน push ต้องผ่าน tests, explicit staging, secret/rights/diff review และตรวจ deployment implications ไม่ force/merge/deploy เอง |

สิทธิ์เรื่องงบ/data/models ไม่ได้ยืนยันว่า token bounds, worker isolation หรือ scientific adapter พร้อมแล้ว งานนี้เตรียม offline เท่านั้น ให้ Luna รับ live execution เมื่อผ่าน gates

## ยังไม่ตัดสิน และไม่จำเป็นต้องหยุดงานอื่น

- ภาษา UI/content: เสนอ EN เริ่มต้นและ TH toggle แต่เจ้าของยังไม่ได้เลือก พารามิเตอร์ปรับได้
- Authentication, roles, collaboration และ retention: ยังไม่เลือก Single-user local prototype เป็นข้อเสนอที่ย้อนกลับได้ ไม่ใช่ production policy
- Deploy destination/domain/public access/hosting cost: ยังไม่ทราบ ห้าม deploy หรือเปิด network service จริง
- Deadline ของ complete repo/paper ยังไม่กำหนด เวลา 18:00 เป็น handoff ไม่ใช่คำรับรองเสร็จ
- Journal target: World Patent Information เป็น candidate ที่มี domain fit; Q1/Q2 เป็น aspiration ไม่ใช่ ranking ที่ยืนยันแล้ว

## สถานะตามหลักฐาน

G10 bounded comparison ผ่าน independent offline audit 57 tests ตาม [handoff ที่ปิดแล้ว](../handoff/PEPO_TO_LUNA_20261027_TH.md) ไม่ใช่ scientific comparison result ทั้งโครงการ
Readiness cohort 36 tests มี overlap กับ G10 จึงไม่บวกเป็นจำนวน independent experiments รอบ input-boundary v1 ผ่าน 32 tests และตรวจ 15 staged bundles

รุ่น 2 เพิ่ม product data contracts, synthetic generator และ shared atomic budget component แต่ยังไม่มี HTTP product API/UI หรือ live scientific dispatcher ที่ผ่านครบทุก gate
ผลทดสอบปัจจุบันและ source hashes อยู่ใน closeout receipt รุ่น 2 ไม่ใช้ตัวเลขในเอกสารเป็น PASS โดยตัวเอง

## ขอบเขตที่ต้องรักษา

ไม่แก้ accepted G11 adaptation, historical G09/G10 evidence, frozen evaluation, `docs/research/pilot-next/`, original Phase A journal, denied preflight หรือ ZIP ที่ส่งแล้ว
ไม่อ่าน `.env`/key ในงาน offline ไม่อ้างว่าสิทธิบัตรพิสูจน์ demand, safety, efficacy, commercial viability หรือ FTO

อ่านต่อ: [Claude handoff](CLAUDE_ENTREPRENEUR_INVESTOR_V2_TH.md), [Luna long-run GOAL](../handoff/LUNA_LONG_RUN_V2_20261027_TH.md), [publication evidence plan](../research/JOURNAL_EVIDENCE_PLAN_20261027_V2_TH.md)
