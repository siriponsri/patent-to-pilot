# Prompt สำหรับ Claude Code account ถัดไป (Paper 1, 13 พ.ย. 2026)

คัดลอกข้อความในกรอบด้านล่างไปวางเป็นข้อความแรกใน session ใหม่

---

```text
คุณรับช่วงงาน Patent-to-Pilot Paper 1 ต่อจาก Claude Code account ก่อนหน้า (session ปิดเพราะใกล้ weekly limit)
repo: C:\Users\User\Desktop\myProject\patent-to-pilot (branch main). รายงานผมเป็นภาษาไทย

## อ่านก่อนเริ่ม (ตามลำดับ)
1. CLAUDE.md: section บนสุดคือสถานะล่าสุด ส่วนที่เหลือเป็นประวัติ
2. docs/healthtech/research/plans/PAPER1-ACQUISITION-PROTOCOL-DRAFT-20261113.md
   - FROZEN แล้ว; ชื่อไฟล์ยังมีคำว่า DRAFT เพื่อให้ลิงก์เดิมใช้ได้
   - รวม Amendment A1 ท้ายไฟล์
3. docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112/
   - paper1-freeze/freeze-manifest.json
   - paper1-freeze/amendment-a1.json
   - owner-paper1-*.json: requirements, freeze approval, controls approval, false-stop approval
   - PAPER1-S2-SUMMARY.json
4. takeover_lib.py, freeze_paper1_s2.py, native_control.py, settle_synthetic.py
   รูปแบบ freeze → claim → observe → settle ที่ต้องใช้ซ้ำอยู่ในไฟล์เหล่านี้

ตรวจก่อนแก้ไฟล์ใด ๆ:
- git status/HEAD/origin/main ต้องตรงกัน
- ไม่มี session อื่นเขียน repo นี้อยู่ (ผู้เขียนมีได้คนเดียว)
- remote journal อยู่ที่ generation 106, IDLE, active null
- ไม่มี container ptp-* กำลังรัน

## สถานะ ณ ส่งต่อ
คำถามวิจัย: query-side acquisition ของ cross-domain prior art บน DAPFAM

Arms:
- B0: วัดแล้ว
- SACR faithful: pilot-20 ทำแล้ว; rescue OUT ได้ 0
- GR: generic rewrite
- FA: functional abstraction (method)
- RRF fusion ของแต่ละ arm กับ B0

Primary: OUT Recall@200
- Gatekeeping: H1 F-FA>B0 → H2 F-FA>F-GR → H3 F-FA>F-SACR
- δ=0.010
- cluster bootstrap 10k, seed 20261113

Amendment A1 (descriptive control; ไม่เปลี่ยน H1–H3):
- C1 manipulation check: ถ้า arm ใดให้ top-200 เหมือน B0 เกิน 95% ของ query ที่ไม่ได้ fallback = ENGINEERING_FAULT
- C2 F-shuffle: fuse B0 กับ query ที่สลับลำดับคำ ไม่เรียก LLM
- C3 family-overlap sensitivity
- code: src/patent_to_pilot/research/paper1_controls.py

ขั้นที่ผ่านแล้ว:
- S1: grammar FA/GR 13/13
- CPU fixture v2: PASS (v1 FAIL; เก็บบันทึกไว้)
- S2: synthetic GPU FA และ GR ผ่านทั้งคู่ arm ละ 1 call; settle แล้วที่ gen 103 และ 106

งบ:
- GPU charged 22,342.6 s (cap 192 h)
- fidelity remaining 208,362 s
- CPU remaining ~28.4 ks (cap 86,400 s)
- model_calls 247 (lower bound)

## ขั้นต่อไป
S3: pilot-20 technical run ของ FA และ GR
- ไฟล์ pilot-20 ชุดเดียวกับ SACR native v5: remote dispatch/queries.jsonl ของ job ptp-auto-native-sacr-pilot20-20261112-v5, sha b5d837f4...
- วัด throughput/failure เท่านั้น ไม่ evaluate แยก

ข้อสังเกตทางเทคนิค:
(a) configuration() ใน freeze_paper1_s2.py ฝัง 'stage' ไว้ใน config
    - stage fidelity ต้องมี config sha ใหม่ แล้ว amend_authority เพิ่มก่อน qualify (additional_synthetic_attempts 0)
    - predecessor ของ fidelity = synthetic smoke ของ arm เดียวกัน
(b) journal PREDECESSOR: full_dev ต้องมี stage 'pilot' ที่ settle แบบ calls_complete
    - สำหรับ FA/GR ให้ทำ job pilot-20 retrieval/encode (แบบ run_sacr_pilot_retrieval.py) เป็น stage 'pilot'
    - ไม่ evaluate แยก; ตรงกับ protocol S3
(c) gate accounting pin ledger
    - ห้าม book CPU ระหว่าง freeze กับ claim
    - freeze/รัน arm ทีละตัว: FA settle ก่อนค่อย freeze GR
(d) SACR full-dev
    - job dir ptp-auto-native-sacr-fulldev-b1-20261113-v1 ถูก stage แล้ว (FULL_DEV_ACCOUNTING_INIT ทำแล้วที่ gen 92) แต่ยังไม่ได้ qualify
    - full_dev stage envelope amendment ยังไม่ได้ apply
    - อ่าน freeze_fulldev.py แล้วเขียนตัว resume (amendment + qualify)
    - ห้ามรัน freeze_fulldev.py ซ้ำ

ลำดับหลังจากนั้น:
- S4: full-dev 474 queries ของ SACR (6x79 batches), FA และ GR; ขนาด batch จาก throughput ที่วัดได้
- S5: retrieval + RRF + control C1–C3 + dev evaluation (CPU, dev qrels เท่านั้น)
- S6: หยุดรอผม (owner checkpoint) ห้ามแก้ arm/prompt/δ/ลำดับทดสอบ ผมจะเลือกได้แค่ไปต่อหรือหยุด
- S7–S8: การเปิด test (773 queries, 556 OUT) ต้องได้คำสั่ง go ชัดเจนจากผมอีกครั้ง พร้อม journal stage 'test'

## กฎที่ห้ามละเมิด
- ห้าม paid API / subscription / extra usage
- ห้าม training, corpus re-encoding, Neo4j writes, full-corpus LLM extraction
- ห้ามเข้าถึง protected test ก่อนผมสั่ง
- ห้าม pull/reset/clean/checkout ทับงานในเครื่อง
- ห้ามปรับ cohort/scoring/controls/stop rules หลังเห็นผล
- ห้าม outcome-driven retry
- ห้ามอ้างว่า schema-valid หรือ unit-test PASS = semantic/retrieval validity
- ซ่อม engineering fault ได้ แต่ไม่ใช่สิทธิ์ replay model/data stage อัตโนมัติ; stage ที่ fail ต้องถามผมก่อนรันใหม่
- GPU ทีละ 1 job
- unknown/running ≠ failed
- settle ครั้งเดียวต่อ job
- ห้ามส่ง manuscript หรือยอมรับ publisher terms แทนผม
- ห้ามเอ่ยถึง paper ฉบับก่อนหน้าที่ถูก supersede และ label ของมัน (ดู memory); Paper 53 อ้างเป็น related work ได้
- Graph = feasibility/negative เท่านั้น; ห้ามรัน Graph screening
- ไม่มี human audit และไม่มี LLM judge

## วิธีทำงาน (เรียนรู้จาก session ก่อน)
- วัด CPU ทุกคำสั่ง local: python scripts/healthtech/meter_local_cpu.py <takeover>/local-cpu-measurements.jsonl -- <cmd>
- segment booking ใช้เลขถัดจากล่าสุด (ล่าสุด 33)
- package() ต้องการให้ src/ และ scripts/healthtech ถูก commit ก่อน
- โค้ดที่มี backslash/escape ให้เขียนด้วย Write/Edit ไม่ใช่ heredoc ใน bash
- observe job ด้วย native_control.py observe <subdir> หรือ cpu_v2_control.py
  - ห้าม start ซ้ำ: launch.json/admission.json กัน replay ไว้
- อัปเดต HANDOFF.md, CLAUDE.md, INDEX-PLAN.md (section บนสุด) ทุกขั้นสำคัญ แล้ว commit + push ทันที
- ห้ามแตะไฟล์ untracked ของผม: uv.lock และ docs/healthtech/research/PATENT_TO_PILOT_RESEARCH_AND_CLAUDE_HANDOFF_2026-11-09.md

เริ่มด้วยการสรุปสถานะที่ตรวจได้จริงและแผนสั้น ๆ ของ S3 แล้วลงมือได้เลย
ขั้น S1–S6 อยู่ในสิทธิ์ของ protocol ที่ freeze แล้ว ไม่ต้องขออนุมัติซ้ำ
ยกเว้นสิ่งที่ fail และต้องรันใหม่ หรือสิ่งที่อยู่นอก protocol
```
