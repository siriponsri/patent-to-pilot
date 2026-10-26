# User journeys: brief → options → handoff → change

**สถานะ:** G01 acceptance journeys · 24 ตุลาคม 2026
**คู่กับ:** [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md)
**สถานะ implementation:** เป็น journey contract สำหรับการออกแบบ/ตรวจภายหลัง ยังไม่มี UI หรือ model run

เอกสารนี้ตอบคำถามว่า ผู้ใช้กรอกอะไร ระบบต้องแสดงอะไร และจุดใดต้องหยุดรอการยืนยัน เพื่อให้ workflow ไม่กลายเป็น chatbot ที่ให้ข้อความยาวแต่ไม่มี artifact ที่ตรวจต่อได้

## Journey A — จากโจทย์องค์กรถึง route comparison และ handoff

### ผู้เกี่ยวข้องและเงื่อนไขก่อนเริ่ม

- **ผู้ขอ:** ระบุเป้าหมาย R&D และขอบเขตงาน
- **ผู้ทบทวน:** ตรวจ source, interpretation, route และคำถามที่ต้องทำต่อ
- **ระบบ:** จัดหลักฐาน สร้าง draft และคำนวณ impact; ไม่มี authority อนุมัติ
- **ก่อนเริ่ม:** มี approved/public documents ที่อนุญาตให้ใช้, source snapshot/locator, brief version และ output target

### เส้นทางหลัก

| ขั้น | ผู้ใช้ทำ/ให้ข้อมูล | ระบบต้องทำ | ผลลัพธ์ที่ผู้ใช้ตรวจ | หยุด/ส่งต่อเมื่อ |
|---|---|---|---|---|
| A0 รับงาน | ระบุ goal, scope, target และ source boundary | สร้าง brief version และแสดง missing prerequisites | brief ไม่เกินขอบเขตและ source ใช้ได้ | ข้อมูล critical หาย → confirmation queue |
| A1 ตรวจ organization card | ตรวจ capability/policy ที่ระบบดึงจาก source | แยก owned/external/unknown, locator, effective date และ ambiguity | แต่ละ field รู้ที่มาและยังไม่รู้ตรงไหน | interpretation กระทบ route → ผู้ใช้ยืนยัน |
| A2 กำหนด decision frame | ระบุ constraints และคำถามที่ต้องเปรียบเทียบ | ผูก constraints กับ options และ policy scope | เห็นว่า constraint ใดเป็น fact/stipulation/unknown | hard constraint ยังไม่ชัด → ไม่สร้าง final-looking route |
| A3 ทบทวน options | เปรียบเทียบ options และถาม source conflict | แสดง evidence, hypothesis, trade-offs, conflicts, unknowns | ตรวจได้ว่า option ใดผ่าน explicit check ใด | evidence ขัดกัน/ขาด → reviewer question |
| A4 รับ draft handoff | เลือกประเด็นที่ต้องส่งต่อและเพิ่มคำถามถ้าจำเป็น | สร้าง evidence ledger, draft test specification, risks และ reviewer questions | คนถัดไปรู้ task, evidence gap และ next measurement | claim/route ที่ขาดหลักฐาน → `blocked_by_missing_evidence`; ส่วนไม่เกี่ยวข้อง draft ต่อได้ |
| A5 สร้าง pack พร้อมตรวจ | ไม่ต้องรอ reviewer approval เพื่อสร้าง draft | ตรวจ artifact completeness, source ID/locator และ traceability แล้วล็อก pack version | `ready_for_review` หมายถึงพร้อมให้ตรวจ; unresolved list ยังแสดง | check ล้มเหลว → แก้ artifact/traceability; reviewer review เป็นสถานะถัดไป |

### ผลลัพธ์ขั้นต่ำของ Journey A

ผู้ใช้ต้องได้ artifact อย่างน้อย: versioned brief, capability/policy map, options matrix, evidence ledger, draft test specification, reviewer questions และ unresolved/confirmation queue รายการที่ไม่มี source support ต้องติด `unknown` หรือ `hypothesis` ไม่ถูกซ่อนใน narrative

## Journey B — เมื่อ constraint หรือ evidence เปลี่ยน

### เงื่อนไข

มี handoff version เดิมและมี change event ที่ระบุชนิด, scope, effective date และผู้ยืนยันแล้ว เช่น ห้ามวัสดุหนึ่งชนิดเฉพาะใน substrate หรือถอน source support หนึ่งรายการ

### ขั้นตอนและ expected behavior

| ขั้น | Event/การกระทำ | ระบบต้องเปลี่ยน | ระบบต้องรักษา | สิ่งที่ต้องถาม/ส่งต่อ |
|---|---|---|---|---|
| B0 บันทึก event | ผู้ใช้ส่ง confirmed change | สร้าง event/version และตรวจ scope | ประวัติเดิมและ source snapshot | ถ้า scope ไม่ชัด → ขอ clarification |
| B1 หา impact | ระบบ trace dependency จาก policy/evidence ไป option/route/handoff | invalidate เฉพาะ derived fields ที่พึ่ง event | unrelated fields, source IDs และ prior versions | dependency ที่พิสูจน์ไม่ได้ → ทำเครื่องหมาย unknown |
| B2 สร้าง diff | ระบบคำนวณ before/after | แสดง removed/changed/unchanged พร้อมเหตุผล | facts ที่ไม่เกี่ยวข้องและ unresolved questions | collateral change พบ → หยุดเพื่อ review |
| B3 ปรับ draft | ระบบเสนอ affected options/route และคำถามใหม่ | คง option ที่ยังผ่าน explicit check หรือเปลี่ยนเป็น unknown เมื่อ support ถอน | ไม่สร้าง yield/cost/feasibility ใหม่เอง | claim/route ที่ได้รับผลติด `blocked_by_missing_evidence`; ส่วนอื่น draft ต่อ |
| B4 ส่ง revision | ระบบตรวจ diff และ pack revision; reviewer ตรวจได้ภายหลัง | ล็อก revision และส่งต่อพร้อมสถานะ | change history และ provenance | reviewer ยังไม่รับรอง → คง `ready_for_review`/review-pending ไม่ใช่ approved |

### ตัวอย่าง PTP-0001

| เหตุการณ์ | ผลที่ต้องเห็น | ห้ามทำ |
|---|---|---|
| P0 อนุญาต silicon และ glass substrate | A และ B ผ่าน explicit substrate check; yield เป็น `unknown` | ห้ามสรุปว่าผลิตได้ |
| P1 ห้าม silicon เฉพาะ substrate | A และ dependent route ถูก block/invalidated; B ยังผ่านและ draft ต่อ; เก็บ source/เหตุผล | ห้าม block B หรือเปลี่ยน substrate เป็น final needle |
| เปลี่ยนชื่อ project อย่างเดียว | A/B, evidence และ policy state เดิม | ห้ามเกิด collateral rewrite |
| ถอน C02 ซึ่งเป็น allowed support เดียวของ B | B กลายเป็น `unknown`; history ยังอยู่ | ห้ามสรุปว่า B ใช้ไม่ได้ในโลก |
| ขอ measured yield โดยไม่มีหลักฐาน | yield ยังคง `unknown` พร้อมคำขอหลักฐาน | ห้ามแต่งตัวเลขจาก patent/คำโฆษณา |

## Journey C — แหล่งข้อมูลไม่พอหรือขัดกัน

เมื่อ source locator เปิดไม่ได้, source versions ขัดกัน, หรือข้ออ้างสำคัญไม่มีหลักฐาน ระบบต้องแสดงปัญหาเป็นรายการที่แก้ได้ ไม่ซ่อนด้วย prose สรุปกว้าง ๆ:

1. ระบุ field/option ที่ได้รับผลกระทบและ source ที่เกี่ยวข้อง
2. แยก `conflict`, `missing`, `withdrawn` และ `ambiguous`
3. เสนอคำถามยืนยันหรือหลักฐานที่ต้องหาเพิ่ม
4. คง option/field เป็น `unknown` หากยังตัดสินไม่ได้
5. สร้าง handoff ส่วนที่ตรวจได้ต่อได้; แสดง `blocked_by_missing_evidence` เฉพาะ claim/route และ dependent fields ที่ขาดหลักฐาน
6. `ready_for_review` มาจาก artifact/traceability checks; reviewer approval ไม่ใช่ prerequisite
7. authored E2E example เชื่อม source evidence → proposed test → handoff และมี claim ที่ไม่ใช่ unknown ทั้งหมด

การไม่พบข้อความใน allowed packet ไม่ใช่หลักฐานเชิงลบว่าความสามารถนั้นไม่มีอยู่จริง และไม่ควรทำให้ claim/route ที่ไม่เกี่ยวข้องถูก block ไปด้วย

## Journey D — การส่งต่อไปยังบทบาทต่างกัน

| ผู้รับ | ระบบเตรียมให้ | ผู้รับต้องตัดสินเอง |
|---|---|---|
| R&D | options matrix, source/evidence ledger, draft test specification, dependencies และ change diff | การทดลองเชิงวิศวกรรม/กระบวนการและ acceptance criteria |
| RA | requirements–evidence checklist, jurisdiction/source/date และ open questions | การตีความข้อกำกับและการยื่น/รับรองอย่างเป็นทางการ |
| Clinical Research | research question, evidence gaps, feasibility questions และ unresolved risks | clinical/scientific design, ethics, safety และ human-study authorization |

ทุก pack เป็น draft portfolio material; ไม่มีบทบาทใดเปลี่ยน draft ให้เป็น approval โดยอัตโนมัติ

## Journey acceptance checklist

- [ ] ผู้ใช้รู้ว่าต้องให้ brief, allowed sources, constraints และ output target อะไร
- [ ] แต่ละขั้นมี artifact ที่ตรวจได้ ไม่ใช่เพียงคำตอบแบบสนทนา
- [ ] critical interpretation ไป confirmation queue และไม่ถูกเติมเอง
- [ ] option ที่ไม่มีหลักฐานคงเป็น `unknown`/`hypothesis` และบอกหลักฐานที่ขาด
- [ ] change แสดง affected และ preserved fields พร้อม before/after version
- [ ] PTP-0001 ให้ผลตามตารางตัวอย่างโดยไม่ใช้ evaluator-only files
- [ ] handoff แยก draft/ready-for-review ออกจาก clinical, regulatory, legal หรือ patent approval

## สิ่งที่ยังไม่ตัดสินใน journey นี้

การออกแบบ UI/API, retrieval algorithm, model/provider, budget, longitudinal memory policy และการวัดประโยชน์เชิงเวลา/ต้นทุนต้องทำใน G07–G18 ตาม prerequisite ของ GOAL ไม่ควรถือว่า journey นี้เป็นหลักฐานว่า agent ทำงานได้จริง
