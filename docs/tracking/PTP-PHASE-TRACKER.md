# PTP-2026-11-21 Phase Tracker

ไฟล์นี้เตรียมไว้ import เข้า AFFiNE (Import → Markdown)
- สถานะ ณ 22 พ.ย. 2026 บ่าย
- แหล่งความจริงคือ `HANDOFF.md` ใน repo เสมอ
- ถ้าต้องการหน้าใหม่ ให้ agent สร้างไฟล์นี้ใหม่แล้ว import อีกครั้ง

**เป้าหมาย:** นำเสนอ IS2 เดือนมีนาคม 2027
**ชื่องาน (ชั่วคราว):** An Adaptive Evidence Engine for Structured Retrieval and Revision

## ภาพรวม Phase

| Phase | Goals | ช่วงเวลาที่วางไว้ | สถานะ |
|---|---|---|---|
| Foundation | G01, G02 | ปลาย พ.ย. – กลาง ธ.ค. 2026 | ✅ เสร็จ |
| Method development | G03 | ธ.ค. 2026 – ต้น ม.ค. 2027 | 🔄 กำลังทำ |
| Evidence | G04, G05 | ม.ค. – ต้น ก.พ. 2027 | ⏳ ยังไม่เริ่ม |
| Product and paper | G06, G07 | ก.พ. 2027 | ⏳ ยังไม่เริ่ม |
| IS2 delivery | G08 | ก่อนนำเสนอ มี.ค. 2027 | ⏳ ยังไม่เริ่ม |

## G01 Shared core and local vertical slice: ✅ เสร็จ (21 พ.ย.)

- [x] เปิดแอป → รันงานตัวอย่าง → ดูเวอร์ชันแหล่งข้อมูล → แก้แหล่งข้อมูล → restart แล้วสถานะยังอยู่
- [x] 16 tests, smoke 15/15, browser QA ที่ 1280 และ 360 px
- [ ] คุณยังต้องลองเอง: ดับเบิลคลิก `Start-PTP.cmd` ใน Explorer แล้วดูว่า browser เปิดเอง

หลักฐาน: `artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md`

## G02 Provider, ingestion and dataset contracts: ✅ เสร็จ (22 พ.ย.) + ส่วนเพิ่ม

- [x] Provider ports: Ollama / OpenAI-compatible / Anthropic
- [x] Index generations และ hybrid mode
- [x] รับไฟล์ text/Markdown
- [x] Dataset registry
- [x] ทดสอบ route จริง: Qwen3-Embedding บน dr-train
- [x] D8: อ่าน PDF ด้วย pypdf (22 พ.ย.)
- [x] D7: profile OpenRouter 4 ตัว ปิด reasoning (22 พ.ย.)
- [ ] ทดสอบ profile OpenRouter กับของจริง (ใช้ไม่เกิน USD 0.20; รอ `OPENROUTER_API_KEY`)

## G03 Baselines and candidate policy (P1-DEV/VAL): 🔄 กำลังทำ

Baseline F\* = Qwen3×2 + PatEmbed×2 (ALL R@200: P1-DEV 0.423, VAL 0.452)
ช่องว่างถ้าเลือกชุดที่ดีที่สุดรายคำค้นได้ (oracle): +0.079

- [x] v1 support_frontier_v0: **PARK** (VAL −0.020)
- [x] A1 แยกคำค้นเป็นส่วนย่อย: **PARK** (VAL −0.0054; พบว่าเส้นทาง T/C ไม่ได้กรองเอกสาร บันทึกไว้แล้ว)
- [x] A2 learned selector: **PARK** (VAL +0.0017 [−0.0019, +0.0054]; IN ขอบล่าง −0.0060)
- [x] A3 LLM query expansion: freeze โปรโตคอลและเขียนโค้ดแล้ว, smoke test ผ่าน 4 โมเดล
- [ ] **ตัดสินใจ:** กติกางบ A3 ถ้า Haiku ชนะ (Stage B ~USD 7.8 เกินเพดาน USD 6)
- [ ] **คุณ:** ตั้ง `OPENROUTER_API_KEY`
- [ ] A3 pilot: 2,000 คำค้น × 4 โมเดล (~USD 1.2, ~3–4 ชม.) → GO/STOP
- [ ] A3 Stage B (ทำเฉพาะเมื่อ GO) → ตัดสินบน VAL
- [ ] เขียน memo §4c, ดึงและบีบอัดไฟล์บน dr-train, สรุปปิด G03

หลักฐาน: `docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md`

## G04 Matched patent benchmark (DAPFAM): ⏳ ยังไม่เริ่ม

- [x] B53.0: pipeline ของเราได้ผลตรงกับเปเปอร์ DAPFAM 11 จาก 12 ช่อง
- [x] D3 audit PatEmbed: ชุด train ของ PatenTEB ยังไม่เผยแพร่; พบ DAPFAM ใน PatenTEB (query 50, corpus 466) → "อาจปนเปื้อน"
- [ ] **ตัดสินใจ:** ทางเลือก PatenTEB (ยอมรับผลบางส่วน / โหลด test เพิ่ม 12 ชุด / เขียนถึงผู้เขียน)
- [ ] Freeze วิธีจาก G03 แล้ววัดบน DAPFAM (ใช้ BM25, Qwen3, Arctic เป็นหลัก; รายงาน PatEmbed แยกพร้อมข้อควรระวัง)
- [ ] ตาราง bridge ของ Paper 53 / B53

## G05 Transfer and evidence maintenance: ⏳ ยังไม่เริ่ม

- [ ] Thai Gazette transfer (ใช้ controller ที่ freeze แล้ว)
- [ ] ชุดทดสอบการอัปเดต: เพิ่ม / แก้ / ถอน / เปลี่ยนข้อกำหนด / การเปลี่ยนที่ไม่เกี่ยวข้อง
- [ ] งบ E2 สำหรับ contextual chunks (ต้องขออนุมัติแยก)
- [ ] NitiBench+ (ไม่บังคับ)

## G06 English-first product beta: ⏳ ยังไม่เริ่ม

- [ ] ขัดเกลา flow: Workbench, Evidence, Runs, Changes, Providers
- [ ] Launcher, export, error states, การหยุดและเริ่มใหม่อย่างปลอดภัย

## G07 Unified paper and evidence audit: ⏳ ยังไม่เริ่ม

- [ ] เปเปอร์ภาษาอังกฤษใน `docs/writing/journal/` (ห้ามใช้ Paper 86; ห้ามอ้าง arXiv:2605.24297)
- [ ] ตรวจ claim ทุกข้อเทียบกับหลักฐาน

## G08 IS2 demonstration and release rehearsal: ⏳ เตรียมเนื้อหา

- [x] D1 / D5 / D6: research + demo, byline, กิตติกรรมประกาศ
- [x] D10: ใส่ผลเรื่องเพดานของ pool จาก Paper 86 (78.3% ไม่เข้า Top-200) ลงในโครงเรื่อง
- [x] Outline v3: `docs/writing/is2/IS2-OUTLINE-v3-20261122.md`
- [ ] **ตัดสินใจ:** เขียนเปเปอร์ใหม่เลย หรือรอผล A3
- [ ] เขียนเปเปอร์ IS2 ใหม่ทั้งฉบับไทยและอังกฤษ
- [ ] Slides + demo storyboard
- [ ] ซ้อมเดโมจริง + เตรียมวิดีโอสำรอง

## งานค้างที่รอคุณ

- [ ] `OPENROUTER_API_KEY`
- [ ] กติกางบ A3
- [ ] เขียน IS2 ใหม่เลย หรือรอ
- [ ] ทางเลือก PatenTEB
- [ ] งบต่องานของ RunPod
- [ ] DOI ของ Paper 53
- [ ] ทดสอบ `Start-PTP.cmd`

## งบที่ใช้ไป

| Envelope | เพดาน | ใช้ไป | หมายเหตุ |
|---|---|---|---|
| OpenRouter E1 | USD 8 / 35,000 req | USD 0.00064 / 4 req | เครดิตเหลือ ~USD 8.365 |
| RunPod (P1 FT) | USD 30 | USD 18.54 | ปิดแล้ว ลบ pod ครบ |
