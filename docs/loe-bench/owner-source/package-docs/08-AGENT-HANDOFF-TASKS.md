# 08 — Agent Handoff Task Cards

รูปแบบ: ให้ agent ทำทีละใบ; แต่ละใบมี Input / Output / Acceptance test. กติการวม: ห้าม sklearn/pandas/scipy; ห้ามจูนบน test; ทุกตัวเลขต้องมาจากไฟล์ output; อย่าสร้างตัวเลขเอง; เขียนเทสต์ก่อนปิดใบ

**T0 Setup**: รัน `python3 -m unittest loe_bench.tests.test_all`. Accept: OK 16 tests.

**T1 Threshold calibration (บังคับ)**: เขียน `calibrate_thresholds.py` เลือก lo/hi บน validation (ตัด 20% ของ train ตามเวลา) ให้ได้ coverage เป้าหมาย 50/70/90%. Accept: coverage บน validation ใกล้เป้า ±3 จุด; test ไม่ถูกแตะ; มี unit test ด้วยข้อมูลสังเคราะห์.

**T2 OPEN-conditional model**: ให้โมเดลใช้ verdict (OPEN/BLOCKED/CONTESTED) และ patent/exclusivity feature แบบมีเงื่อนไข. Accept: บน Track A ตัวอย่าง จำนวนเคส OPEN ที่ทำนาย PREDICT_NO_ENTRY ต้องลดลงอย่างมีเหตุผล (รายงานจำนวน); ไม่ขัด unit test เดิม.

**T3 Ablation runner**: M1/M2/M3/M4 + B0–B3 บน Track C ต่อ h=12/24/36 พร้อม cluster bootstrap 2,000 ครั้ง. Accept: ตารางผล CSV + sha256; seed คงที่; ผลซ้ำได้.

**T4 Power simulation (ก่อน data lock)**: จำลองจากโครงสร้างจริง (757 ยาทดสอบ, prevalence ~0.12) ว่าขนาดผลต่าง ΔAURC เท่าใดจึงตรวจพบด้วยพลัง 80%. Accept: รายงาน minimum detectable effect; ใช้ปรับเกณฑ์ H2 ก่อนตรึง.

**T5 Preregistration draft**: ร่าง OSF prereg จาก 01 (สมมติฐาน, split, ตัวชี้วัด, kill criteria). Accept: ไม่มีตัวเลขเกณฑ์ที่ขัดกับ T4.

**T6 Historical Orange Book (G1)**: ค้นและดาวน์โหลด edition ย้อนหลัง (FDA archive/Wayback), parse patent/exclusivity ตามวันที่, สร้าง `features_at` แบบ as-of. Accept: edition ≥2 ปี, sha256, ตรวจ leakage ด้วยเทสต์ว่าไม่ใช้ข้อมูลหลัง cutoff. ถ้าไม่ได้ → บันทึกว่า BLOCKED.

**T7 Ingredient key audit**: สุ่ม 100 entity ตรวจ norm_ingredient ด้วยมือ/แหล่งอ้างอิง active moiety. Accept: รายงานอัตราผิดและตัวอย่างความผิดพลาด.

**T8 Track B downloads**: ดึง Purple Book รายเดือน 2020–2026 (ผ่านบริการ scrape), ตรวจ URL ของแต่ละเดือนจากหน้ารายการ, dedupe ตาม BLA, สร้างตาราง first-biosimilar-by-reference. Accept: จำนวนเดือนที่ได้/ไม่ได้ระบุชัด; sha256; รายงาน n ของ BLA biosimilar.

**T9 Track A re-score script**: re-fetch แล้วให้คะแนนต่อ S0 โดยตรวจ sha256 ของ S0 ก่อน. Accept: ปฏิเสธรันถ้า hash ไม่ตรง.

**T10 (ทางเลือก) LLM one-shot arm**: ใช้ `local_llm_smoke/` ให้ LLM ตอบ schema เดียวกัน. Accept: รันบน GPU จริงก่อนอ้างผลใดๆ (ตอนนี้ยังไม่ได้ตรวจบน GPU).

**T11 IS3 prototype (หลังผ่าน G5)**: ดึง ClinicalTrials.gov, สร้างตัวทำนาย launch (ขอบเขตแคบ), คำนวณ remaining exclusivity, backtest. Accept: ระบุขอบเขตข้อมูลที่ไม่มี (ยอดขาย) ชัดเจน.

**T12 Manuscript table builder**: สคริปต์สร้างตารางต้นฉบับจาก output อัตโนมัติ (ไม่คัดลอกมือ). Accept: diff เป็นศูนย์เมื่อรันซ้ำ.
