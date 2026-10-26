# Product contract: Organization-Adaptive R&D Agent

**สถานะ:** G01 bounded product contract · เอกสารออกแบบที่ตรวจได้ · 24 ตุลาคม 2026
**ขอบเขต:** research/patent-to-pilot
**ผู้ใช้หลัก:** ผู้ทำ R&D และผู้ทบทวนงาน RA/Clinical Research ที่ต้องตรวจหลักฐานต่อ
**สถานะ implementation:** ยังไม่มี product app, API หรือ model run; เอกสารนี้กำหนดพฤติกรรมและขอบเขตที่ implementation ภายหลังต้องรักษา

## 1. งานที่ผู้ใช้ต้องทำให้สำเร็จ

ผู้ใช้ต้องสามารถเปลี่ยนโจทย์ R&D และเอกสารองค์กรที่อนุญาตให้ใช้ เป็นชุดทางเลือกและ handoff ที่ตรวจย้อนกลับได้ แล้วเห็นทันทีว่าเมื่อ evidence หรือ constraint เปลี่ยน ส่วนใดต้องปรับ ส่วนใดคงเดิม และเรื่องใดยังเป็น `unknown`

ผู้ใช้ไม่ได้มอบอำนาจให้ระบบตัดสินว่าโครงการผลิตได้จริง ปลอดภัย มีประสิทธิผล สอดคล้องกฎ ระบุ patentability/FTO หรืออนุมัติการทดลองกับคน

## 2. ขอบเขต core delivery slice

```text
approved brief + allowed sources
        ↓
organization capability/policy map
        ↓
source-linked opportunities and route options
        ↓
draft feasibility / pilot / R&D–RA–Clinical Research handoff
        ↓
confirmed change event → affected fields and before/after diff
```

ทุกขั้นต้องเก็บ source ID และตำแหน่งข้อความเมื่อเป็นข้ออ้างจากแหล่งจริง แยก `evidence`, `hypothesis`, `stipulation` และ `unknown` ออกจากกัน ข้อความที่ไม่พบใน packet ไม่ได้แปลว่าไม่มีข้อมูลในโลก

## 3. สิ่งที่ระบบรับและส่งมอบ

### 3.1 Inputs และ prerequisites

ก่อนเริ่ม workflow ผู้ใช้หรือเจ้าของข้อมูลต้องระบุ:

- `brief`: เป้าหมาย ขอบเขต คำถาม และผลลัพธ์ที่ต้องการ
- `organization_context`: เอกสาร public/approved และขอบเขตสิทธิ์การใช้
- `allowed_sources`: source ID, version/snapshot, วันที่ และตำแหน่งที่อ้างได้
- `constraints`: ข้อจำกัดที่ยืนยันแล้วหรือ stipulation ของ benchmark โดยระบุ scope และ effective date
- `output_target`: งานที่จะส่งต่อ เช่น R&D, RA หรือ Clinical Research

ถ้า source, effective date, ownership หรือความหมายของ hard constraint ไม่ชัด ระบบต้องหยุดที่ confirmation queue หรือคงค่าเป็น `unknown`; ห้ามเติมจากความน่าจะเป็น

### 3.2 Canonical artifacts

| Artifact | ต้องตอบอะไร | ข้อมูลขั้นต่ำ | ผู้ใช้ตรวจอะไร |
|---|---|---|---|
| Brief | งานนี้ต้องการตัดสินใจอะไร | goal, scope, output target, version | โจทย์ตรงหรือไม่ |
| Capability/policy map | องค์กรมี/จ้าง/ยังไม่ยืนยันอะไร | field, state=`owned|external|unknown`, source/stipulation, confidence, effective date, confirmation state | source support และ scope |
| Opportunity card | ตัวเลือกนี้เกี่ยวกับโจทย์อย่างไร | option, source evidence, hypothesis, open questions | ไม่สรุปเกิน passage |
| Route comparison | ทางเลือกต่างกันอย่างไร | route, constraints, evidence, trade-offs, conflicts, unknowns | ทุก route ผ่านกฎใด |
| Handoff pack | คนถัดไปต้องทำอะไร | rationale, evidence ledger, draft test specification, reviewer questions, risks | พร้อมตรวจต่อ ไม่ใช่ approval |
| Change diff | การเปลี่ยนกระทบอะไร | event, affected fields, invalidated evidence/options, preserved fields, before/after, reason | ไม่มี collateral change และประวัติไม่หาย |
| Confirmation queue | คนต้องยืนยันจุดใด | question, impact, source conflict/ambiguity, proposed interpretations | ถามเฉพาะจุด critical |

### 3.3 สถานะข้ออ้าง

ทุก field ที่มีผลต่อ route หรือ handoff ต้องใช้สถานะที่แยกกันได้:

- `evidence`: มี source assertion หรือ checked fact พร้อม locator; ไม่ได้แปลว่าพิสูจน์ feasibility/safety
- `stipulation`: เงื่อนไขที่ผู้สร้าง case ระบุเพื่อการพัฒนา/ประเมิน; ไม่ใช่ข้อเท็จจริงขององค์กรจริง
- `hypothesis`: ข้อเสนอที่ต้องตรวจเพิ่ม
- `unknown`: packet นี้ยังไม่รองรับการตัดสิน
- `confirmed_interpretation`: ผู้มีอำนาจยืนยันความหมายที่ critical แล้ว พร้อมผู้ยืนยัน/เวลาในระบบจริงภายหลัง

ระบบต้องเก็บ source version, effective date และประวัติการถอนหลักฐาน เพื่อไม่ให้ evidence เก่ากลับมาใช้โดยไม่มีเหตุผล

## 4. Workflow และ acceptance gates

### Gate 0 — รับ brief และกำหนดขอบเขต

ระบบแสดง brief version, allowed sources, constraints และ output target ให้ผู้ใช้ตรวจ หากขอบเขตยังไม่ชัด ให้สร้างคำถามสั้น ๆ และยังไม่เสนอ route ที่ดูเหมือน final

### Gate 1 — สร้างและตรวจ capability/policy map

ระบบจัด field เป็น `owned`, `external` หรือ `unknown` พร้อม source/stipulation และ effective date ความหมายที่เปลี่ยนเส้นทางสำคัญ เช่น “มีเครื่องเอง” กับ “ร่วมงานกับผู้ให้บริการ” ต้องเข้า confirmation queue ไม่ขยายความเอง

### Gate 2 — สร้าง opportunity และเปรียบเทียบ routes

ระบบเชื่อม option กับ evidence และ constraint ที่ใช้ตัดสินใจ แสดง trade-offs, conflicts และ open questions ข้อเสนอที่ไม่มีหลักฐานพอให้ติด `hypothesis` หรือ `unknown` ไม่เลื่อนเป็น fact

### Gate 3 — สร้าง draft handoff

handoff ต้องมี evidence ledger, draft test specification, owner/reviewer questions และรายการสิ่งที่ยังขาด ผู้รับช่วงต่อจึงตรวจได้ว่าอะไรเป็นงานเอกสาร อะไรต้องวัดจริง และอะไรนอกอำนาจระบบ หากหลักฐานขาด ให้ติด `blocked_by_missing_evidence` เฉพาะ claim/route และ derived fields ที่พึ่ง claim นั้น ส่วน claim/route ที่ไม่เกี่ยวข้องยังสร้าง draft ต่อได้และต้องแสดงสถานะของตนเอง

### Gate 4 — รับ confirmed change และคำนวณ impact

เมื่อ constraint, evidence หรือผลทดลองเปลี่ยน ระบบสร้าง event version, invalidate derived fields ที่เกี่ยวข้อง, คง field ที่ไม่เกี่ยวข้อง และแสดง before/after diff พร้อมเหตุผล การเปลี่ยนชื่อโครงการอย่างเดียวต้องไม่เปลี่ยนวัสดุ evidence หรือ policy state

### Gate 5 — ส่งต่อและรอการยืนยัน

ระบบตั้ง `ready_for_review` เมื่อ artifact ที่กำหนดครบ, source IDs/locators ตรวจย้อนกลับได้, status transitions ถูกต้อง และไม่มี traceability check ที่ล้มเหลว สถานะนี้หมายถึง “พร้อมให้ตรวจ” ไม่ใช่ reviewer approval ผู้ทบทวนอาจตรวจภายหลังและสถานะ review/approval ต้องแยกจาก readiness ของ artifact เสมอ ใน pack เดียวกัน claim/route ที่หลักฐานขาดยังติด `blocked_by_missing_evidence` ได้โดยไม่บล็อกส่วนที่ตรวจย้อนกลับได้

## 5. Authority boundary

| ระบบเสนอได้ | ต้องถาม/ให้คนยืนยัน | ระบบไม่มีอำนาจทำ |
|---|---|---|
| จัดกลุ่ม source-linked facts, options, conflicts และ unknowns | interpretation ที่เปลี่ยน route, source conflict, hard constraint, และการใช้แทนองค์กรจริง | อนุมัติ clinical use, regulatory compliance, patentability, FTO, safety, efficacy หรือ human study |
| เสนอ route comparison และ draft test questions | ความพร้อมของเครื่อง/คน/ผู้ให้บริการ และ acceptance criteria ที่เป็นขององค์กรจริง | แก้กฎองค์กรหรือเปลี่ยน hard constraint จาก feedback เอง |
| คำนวณผลกระทบจาก change ที่ยืนยันแล้ว | การรับรอง handoff ก่อนใช้งานจริง | เติม yield, cost, risk หรือผลทดลองที่ไม่มีหลักฐาน |
| เก็บ confirmed feedback ตาม scope และ version | การยืนยันว่าข้อมูลใดใช้ข้าม project/organization ได้ | รวม memory ข้ามองค์กรโดยไม่มี boundary และ consent ที่กำหนด |

## 6. ตัวอย่าง acceptance จาก PTP-0001

PTP-0001 เป็น development smoke test ที่ใช้ patent source จริงกับโจทย์องค์กรสมมติ ไม่ใช่ผล model/scientific validation และไม่ใช่คำตัดสินว่า microneedle ผลิตได้ ปลอดภัย หรือไม่ติดสิทธิ์

เมื่อ `P0` อนุญาต silicon และ glass substrate ระบบต้องแสดง candidate A/B และ `production_yield=unknown` เมื่อเกิด `P1` ห้าม silicon เฉพาะ substrate ต้องถอน/qualify A แต่คง B และ evidence ที่ไม่เกี่ยวข้องไว้ เมื่อถอน support เดียวของ B ระบบต้องเปลี่ยน B เป็น `unknown` ไม่ใช่ประกาศว่า B ใช้ไม่ได้ เมื่อผู้ใช้ขอ yield โดยไม่มีหลักฐานใหม่ ระบบต้องขอหลักฐานและไม่แต่งตัวเลข

ตัวอย่างนี้ตรวจ bookkeeping และ change impact เท่านั้น รายละเอียด evaluator-only oracle/fixtures ไม่เป็น input ของ product contract หรือ evaluated system

### 6.1 Authored E2E example — evidence → proposed test → handoff

ตัวอย่างนี้เป็นเส้นทางเอกสารที่แต่งขึ้นเพื่อ acceptance ไม่ใช่ model run หรือ scientific validation:

| ขั้น | สิ่งที่บันทึก | สถานะ/ผลที่ต้องเห็น |
|---|---|---|
| E1 source evidence | `US20060086689A1`, description ¶0016 ระบุบทบาทของ substrate แยกจาก seed layer; ¶0017–0019 กล่าวถึง pattern/micromold และบทบาทวัสดุเข็ม | `evidence` พร้อม source locator; ไม่อ้างว่า source พิสูจน์ yield หรือ manufacturability |
| E2 task stipulation | P0 อนุญาต silicon และ glass เฉพาะ substrate comparison | `stipulation`; ไม่ใช่ capability ขององค์กรจริง |
| E3 proposed route | เปรียบเทียบ candidate A=silicon substrate กับ B=glass substrate ภายใต้ explicit substrate check | A/B ผ่าน check ใน P0; `production_yield=unknown` ไม่ทำให้ทั้ง route เป็น unknown |
| E4 proposed test | วัด process feasibility และ production yield ของ candidate ที่เหลือด้วยวิธีวัดที่ผู้รับ R&D กำหนด พร้อมตรวจ source-role separation | `proposed_test`; ยังไม่มีผลวัด จึงไม่สร้างตัวเลข |
| E5 handoff | evidence ledger (E1), decision rule (E2), options matrix (E3), test specification (E4), และคำถามเรื่อง yield/ambiguity | pack มี traceable draft ส่วน yield เป็น open question; artifact status เป็น `ready_for_review` เมื่อ checks ผ่าน |
| E6 scoped change | P1 ห้าม silicon substrate | A และ dependent route ถูก `invalidated_by_policy_change`; B และ E4 ที่ไม่พึ่ง silicon เดินต่อได้; ถ้ามี claim อื่นขาดหลักฐานจึงค่อยใช้ `blocked_by_missing_evidence` เฉพาะจุด |

ดังนั้นตัวอย่างนี้มี source-backed claim และ proposed test ที่เชื่อมถึง handoff ไม่ใช่การทำให้ทุก field ผ่านด้วย `unknown` และไม่ใช้ reviewer approval เป็นเงื่อนไขสร้าง draft

## 7. Acceptance criteria ของ G01

G01 ถือว่าพร้อมสำหรับงานถัดไปเมื่อ:

1. อ่านเอกสารนี้แล้วระบุ input, canonical output และ confirmation gate ของ workflow ได้
2. ทุกข้อเสนอที่เกี่ยวกับ source มีสถานะและ locator ที่ตรวจย้อนกลับได้ หรือถูกเก็บเป็น unknown/hypothesis
3. route และ handoff แยกสิ่งที่ระบบทำได้จากสิ่งที่ผู้ใช้ต้องยืนยันและสิ่งที่อยู่นอก authority
4. change event แสดง affected/preserved fields และไม่ลบประวัติ evidence/policy
5. `blocked_by_missing_evidence` จำกัดอยู่ที่ claim/route และ downstream fields ที่ได้รับผล; ส่วนที่ไม่เกี่ยวข้องยัง draft ต่อได้
6. `ready_for_review` เกิดจาก artifact/traceability checks ไม่ใช่ reviewer approval และ reviewer state แยกต่างหาก
7. PTP-0001 walkthrough และ authored E2E example เชื่อม evidence → proposed test → handoff โดยไม่ใช้ hidden oracle และไม่ผ่านด้วย unknown ทั้งหมด

## 8. ขอบเขตที่ยังไม่ใช่ implementation และ backlog

- ยังไม่มี schema validator, UI/API, retrieval runner หรือ persistent product memory
- ยังไม่มีหลักฐานว่า workflow ลดเวลา ต้นทุน หรือข้อผิดพลาดได้จริง
- G02 ยังไม่จบ: มี bounded literature collection/gap matrix แล้ว แต่ claim/evidence map และ longitudinal gap synthesis ยังไม่ freeze
- G03 ยังไม่จบ: มี metadata/preflight และ starter-batch proposal แต่ pinned starter payload ยังไม่โหลด/parse และยังไม่มี linked-sample closure
- G04 ทำต่อแบบ parallel slice ในรอบนี้: มี [schema](../../methodology/organizations/schema.json) และ [fictional fixture](../../methodology/organizations/fictional-profile-a/v1/profile.json) bounded หนึ่งชุดเพื่อใช้ contract; ยังไม่ใช่ general extractor, approved cards หรือ full three-profile completion
- ต้องแยกและ freeze data/evaluation contract ก่อน model run; ห้ามเรียก authored smoke test เป็น independent sample
- การยืนยัน clinical, legal, regulatory และ patent counsel เป็นงานภายหลัง ไม่ใช่ acceptance ของ technical contract นี้

**เอกสารอ้างอิง:** [GOAL](../../GOAL.md), [PLAN](../PLAN.md), [user journeys](USER_JOURNEYS.md), [PTP-0001 walkthrough](../FIRST_CASE_WALKTHROUGH.md)
