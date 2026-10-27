# Patent-to-Pilot — requirements และ decision register รุ่นร่าง 1

วันที่ 27 ตุลาคม 2026  
สถานะ **REQUIREMENTS_DRAFT / OWNER_ANSWERS_PENDING**  
เอกสารนี้เพิ่มจากกรอบเดิม ไม่แก้ GOAL, frozen protocol, handoff หรือ final manifest ที่ปิดไว้แล้ว

## ข้อเท็จจริงที่เจ้าของยืนยันในรอบนี้

| ID | ข้อที่ยืนยัน | ผลต่อแผน |
|---|---|---|
| C01 | ต้องการ long run ครอบคลุม research, backend, UI และ user journey | แยก deliverables และ acceptance ของแต่ละสาย ไม่จบเพียง provider echo |
| C02 | ให้ถาม requirements และแก้เอกสารก่อน | รายละเอียดที่ยังไม่ตอบคง PENDING ไม่ใช้ข้อเสนอเป็นข้ออนุมัติ |
| C03 | UI ต้องดู minimal + formal | Claude ใช้เป็น design direction แต่สี/ภาษา/หน้าจอสุดท้ายยังไม่ freeze |
| C04 | Pepo ทำ offline work ที่พร้อมต่อได้ก่อน | ทำเอกสาร/input checks/calibration โดยไม่รอส่วนที่ไม่เกี่ยวข้อง |
| C05 | Claude รับ UI; Luna Max รับ long-running integration/experiments เมื่อพร้อม | ไม่สร้าง UI หรือสลับ executor/model API ในงานเตรียมนี้ |
| C06 | เจ้าของต้องการให้ long run มีงบและ commit/push | ยืนยันเจตนาโดยรวม แต่จำนวนเงิน, payload scope และ Git target ยังรอคำตอบ ไม่ใช่อำนาจ dispatch/push ในรอบนี้ |

เวลา 18:00 น. ไทยจากงานก่อนหน้าเป็นเวลารับช่วงที่แจ้งไว้ ไม่ใช่ deadline ส่งมอบทั้งผลิตภัณฑ์หรืองานวิจัย

## คำถาม 8 กลุ่มที่ส่งไว้แล้ว

คำถามอยู่ในบทสนทนาหลัก เอกสารนี้จัดกลุ่มเพื่อติดตาม ไม่ส่งคำถามชุดเดิมซ้ำ และยังไม่มีคำตอบใหม่ที่บันทึกเป็น requirement

| ID | สิ่งที่ต้องตัดสิน | สถานะ | ทางเลือก/ค่าเริ่มต้นที่เสนอเท่านั้น | งานที่ขึ้นกับคำตอบ |
|---|---|---|---|---|
| R01 | Delivery endpoint และ deadline: demo, usable prototype, scientific pilot หรือ manuscript-ready ระดับใด | PENDING | แบ่ง acceptance เป็นช่วงที่ทบทวนได้ ไม่รับรองวันเสร็จก่อน scope ชัด | ขนาด long run, priority, definition of done |
| R02 | ใครใช้/ใครตัดสิน และงานใดสำคัญที่สุด | PENDING | owner pharmacist/R&D reviewer เป็น starting persona ตาม product contract เดิม ไม่ใช่กลุ่มผู้ใช้ที่ validate แล้ว | journey priorities, review responsibilities |
| R03 | Core journey, collaboration, approval/history และ export ที่ต้องใช้จริง | PENDING | brief → sources/org map → options/plan → change/diff → export; ยังไม่สร้าง team auth/collaboration ก่อนตัดสิน | interaction/API scope, roles, retention/recovery |
| R04 | Input types, public/private data, privacy และการเก็บข้อมูล | PENDING | public/approved sources + fictional profiles สำหรับ mock; ไม่ส่ง private/health dataโดยปริยาย | ingestion, storage, redaction, outbound policy |
| R05 | ภาษา UI/content, theme/color และรายละเอียด minimal/formal | PENDING บางส่วน | minimal + formal ยืนยันแล้ว; EN/TH และสีที่เสนอ **ยังไม่อนุมัติ** | localization, typography, layout/design tokens |
| R06 | Exact incremental OpenRouter cap และการนับยอดเก่า/สำรอง | PENDING | $5 overall = $1 calibration + $4 ถัดไป เป็น **ข้อเสนอ**; ไม่รวมกับ $1 เก่าแล้วกลายเป็น $6 เอง | approved matrix, ledger cap, stop/resume |
| R07 | ยอมให้ส่ง public test content อะไร ไปโมเดล/providerใด | PENDING | shortlist เดิมผ่าน OpenRouter เป็น candidate ไม่ใช่การอนุมัติ scientific payload/model ใหม่ | exact payload hashes, routing/capabilities/prices |
| R08 | Branch/remote/publication target สำหรับ commit/push | PENDING | ใช้ intended established remote เท่านั้นหลังตรวจจริง ไม่เดา branch/destination | staging, push, CI/remote-ref verification |

คำตอบแต่ละข้อควรบันทึก decision ID, เวลา, ข้อความที่ตกลง, scope/exclusions และ source ที่อนุมัติ ไม่ลบ proposal เก่าเพื่อให้ดูเหมือนเคย approved

## งบและสิทธิ์ที่ไม่ควรสับสน

- เครดิต OpenRouter $10 เป็นยอดที่เจ้าของเคยรายงาน ไม่ใช่วงเงินที่ agent ใช้ได้
- Approval echo เดิม $0.60 ใช้กับ bounded synthetic transport scope ในอดีต ไม่โอนมาครอบคลุม scientific prompts
- $1 G13-A ใน readiness เดิมเป็น proposal; $5 overall ที่เสนอใหม่ก็ยังไม่ใช่ approved cap
- ยอดเก่า $0.0001464 เป็น SOURCE_REPORTED จาก closeout เดิม ไม่ได้อ่าน account/key/billing ใหม่
- ไม่มี scientific dispatch command ที่อนุมัติแล้วในเอกสารนี้
- General intent ให้ commit/push ไม่ใช่การเลือก remote/branch/publication sensitivity ให้ agent เดาเอง
- ไม่สร้าง deployment requirement, public exposure หรือ clinical/legal authority จากการขอ long run

## Acceptance ที่ยึดจากสัญญาผลิตภัณฑ์เดิม

1. แต่ละ source claim แสดง source/version/locator และแยก assertion, stipulation, interpretation, unknown
2. Missing evidence block เฉพาะ dependent claim/route ไม่ทำให้ unrelated draft หยุดหมด
3. ready_for_review หมายถึง completeness/traceability พร้อมตรวจ ไม่ใช่ reviewer/scientific/regulatory approval
4. Change มี affected/preserved fields, before/after versions และเหตุผล ไม่ overwrite history
5. Proposed tests ไม่มีผลทดลองที่แต่งขึ้น
6. Same-information comparison, failed-attempt costs และ oracle isolation ต้องรักษา
7. Export/source history ไม่เปิดเผย key, evaluator answers หรือ restricted dataโดยปริยาย
8. UI และ backend อธิบายข้อจำกัดด้วยสถานะจริง ไม่ใช้ success banner กลบ unknown/blocked

## วิธีอัปเดตหลังได้คำตอบ

จัด requirement version 2 และเชื่อม C/R IDs ไป acceptance/work packages อัปเดตเฉพาะเอกสาร draft/config proposal ที่เกี่ยวข้อง ไม่เขียนทับผลการทดลองหรือ manifest เก่า
หากคำตอบเปลี่ยน research claim ให้ปรับ protocol/run plan รุ่นใหม่ก่อนใช้ held-out data ไม่ทำย้อนหลังให้ดูเป็น preplanned
เมื่อ amount/model/transfer/target ยืนยันแล้วจึงสร้าง concrete approval/run receipt ของแผนที่จะรัน ไม่ใช้ไฟล์ requirements เป็น cryptographic authorization

## แหล่งหลัก

- [Product contract](PRODUCT_CONTRACT.md)
- [User journeys](USER_JOURNEYS.md)
- [Claude handoff เดิม](CLAUDE_UI_HANDOFF_TH.md)
- [Minimal/formal UI draft](CLAUDE_MINIMAL_FORMAL_DRAFT_20261027_V1_TH.md)
- [Long-run work breakdown](../handoff/LONG_RUN_REQUIREMENTS_DRAFT_20261027_V1_TH.md)
- [G10 audit และ offline readiness ที่ปิดแล้ว](../handoff/PEPO_TO_LUNA_20261027_TH.md)
- Final receipt: `results/development/pepo-readiness-20261027-r1/final-manifest.json` (immutable; ไม่แก้ในงานนี้)
