# 00 — อ่านไฟล์นี้ก่อน (Solo Project → Solo Business)

โปรแกรมวิจัยชื่อชั่วคราว: **LOE-Bench / Abstention-aware, evidence-traced forecasting of generic and biosimilar competitive entry**
เจ้าของ: Siripon Srihangpiboon (ทำคนเดียว) | วันที่จัดทำ: 2026-11-27 | สถานะ: starter package (โค้ดผ่านเทสต์ 16 ข้อ; ยังไม่มีผลวิจัยจริง)

> กล่อง "ซื่อตรง" (อ่านก่อนลงมือ)
> 1. เอกสารนี้ไม่รับประกันว่าจะได้ผล "outstanding" หรือถูกตอบรับใน Q1–Q2 สิ่งที่ทำได้คือกำหนดเกณฑ์สำเร็จและเกณฑ์ล้มเลิกล่วงหน้า (preregistered) เพื่อให้ผลที่ได้ น่าเชื่อถือไม่ว่าจะบวกหรือลบ
> 2. ผล smoke test ใน `data/smoke_baselines_h36.txt` **ไม่ใช่ผลวิจัย** เป็นเพียงการเช็กว่า pipeline ทำงาน
> 3. ควอร์ไทล์ (Q1/Q2) ของวารสารที่เสนอ **ยังไม่ได้ตรวจ** ต้องเปิด SJR/JCR เอง
> 4. ไม่ใช่ความเห็นทางกฎหมาย/คลินิก ข้อสมมติทางกฎหมาย (เช่น exclusivity 5 ปี NCE, 12 ปี biologic) ต้องให้ผู้เชี่ยวชาญยืนยัน
> 5. มีงานก่อนหน้าเรื่องการทำนาย generic entry อยู่แล้ว (ดู 01 และ 10) ความใหม่ต้อง "แคบ" ไม่ใช่ "เราทำนาย generic entry เป็นคนแรก"

## 1. แผนในหนึ่งย่อหน้า

ใช้ข้อมูลสาธารณะของ FDA (Orange Book, Drugs@FDA, Purple Book) และ ClinicalTrials.gov สร้าง **benchmark แบบแบ่งตามเวลา** สำหรับถามว่า "ยาตัวนี้จะมี generic/biosimilar เข้าตลาดภายใน 12/24/36 เดือนหรือไม่" แล้วเสนอวิธี (method/architecture) ที่ต่างจาก paper 53: แทนที่จะปรับ prompt ให้ LLM (ซึ่ง paper 53 พบว่าผลต่างใกล้ศูนย์) ใช้ **evidence graph แบบ Kleene สามสถานะ (OPEN/BLOCKED/CONTESTED) + ความน่าจะเป็นที่ calibrate แล้ว + การงดตอบ (abstention) + VoI ของหลักฐานถัดไป** เพื่อบอกว่า "เคสไหนควรส่งให้ผู้ประเมิน FTO คนจริง" นี่คือจุดที่ปิด pain point แรก (ผู้ประเมินขาดแคลน → ทำ triage) และต่อยอดเป็น pain point ที่สอง (คาดการณ์ demand ที่เหลือหลัง launch) ในเฟสธุรกิจ

## 2. Stage gates (ไม่ใส่ระยะเวลา ให้ผ่านทีละด่าน)

| Gate | ชื่อ | ผ่านเมื่อ | ใครทำ |
|---|---|---|---|
| G0 | Setup & รันโค้ดได้ | เทสต์ 16 ข้อผ่านบนเครื่องคุณ; fetch/profile/baselines รันจบ | agent + คุณกดรัน |
| G1 | ข้อมูล patent ย้อนหลัง | ได้ Orange Book edition ย้อนหลัง (หรือประกาศใช้ Track A อย่างเดียว) | คุณ (ดาวน์โหลด) + agent |
| G2 | Preregistration | เขียน success/kill criteria + ตรึง split/ตัวชี้วัด + power simulation แล้ว timestamp (OSF) | คุณตัดสินใจ, agent ร่าง |
| G3 | Data lock + freeze S0 | ตรึง snapshot, บันทึก sha256 | agent |
| G4 | รันโมเดลและ ablation | ได้ตารางผลตาม 01 | agent |
| G5 | ตัดสิน | ผ่านเกณฑ์ → เขียน IS2; ไม่ผ่าน → รายงานเป็นผลลบ/วารสารข้อมูล | คุณ |
| G6 | Customer discovery | คุยผู้ใช้จริงครบตามสคริปต์ใน 07 และมีสัญญาณซื้อ | คุณ (ต้องเป็นคน) |
| G7 | Pilot แบบจ่ายเงิน | มีลูกค้าจ่ายอย่างน้อยหนึ่งราย | คุณ |

## 3. คำสั่งรัน

```bash
cd solo_to_business
python3 -m unittest loe_bench.tests.test_all          # G0: ต้อง OK 16 tests
python3 -m loe_bench.openfda_fetch --out data/raw      # ดึงข้อมูล (ใช้โควตา openFDA ไม่มี key; ~ร้อยครั้ง)
python3 -m loe_bench.run_profile --raw data/raw --out data/profile.json
python3 -m loe_bench.run_baselines --raw data/raw --horizon 36
python3 -m loe_bench.trackA_freeze --raw data/raw --out data/trackA_S0.csv --t0 YYYY-MM-DD
python3 -m loe_bench.purplebook_fetch 2020 2026        # พิมพ์รายการ URL ของ Purple Book
```
หมายเหตุ: ใช้ Python มาตรฐาน (numpy ไม่บังคับ); อย่าใช้ sklearn/pandas/scipy ใน environment ที่ import ค้าง; `data/raw` (~108 MB) ไม่รวมใน zip ให้ดึงใหม่ แล้วเทียบ sha256 กับ `data/MANIFEST.json` (ข้อมูล openFDA เป็น snapshot ปัจจุบัน ค่าอาจเปลี่ยนจากที่บันทึกไว้)

## 4. แผนที่โฟลเดอร์

- `loe_bench/` โค้ด (common, dataset, baselines, metrics, evidence_graph, kleene, voi, purplebook, ...)
- `data/` MANIFEST, profile, smoke result, ตัวอย่าง freeze (`trackA_S0_example.csv` สาธิต pipeline เท่านั้น)
- `docs/` 00–10 (ชุดนี้)

## 5. ลำดับอ่าน

00 → 01 (วิจัย) → 06 (roadmap) → 08 (task cards ส่ง agent) → 03 (วารสาร) → 02 (IS2) → 04/05 (ข้อมูล/สถาปัตยกรรม) → 07 (ธุรกิจ) → 09 (ความเสี่ยง) → 10 (อ้างอิง)

## 6. ใครทำอะไร (คุณไม่ต้องมี expertise ทุกด้าน)

| งาน | Agent ทำได้ | ต้องเป็นคุณ |
|---|---|---|
| เขียน/แก้โค้ด รันเทสต์ ดึงข้อมูล | ใช่ | กดสั่งและอ่านผลสรุป |
| ร่าง preregistration | ใช่ | ตัดสินใจเกณฑ์ และกด submit |
| ตรวจข้อสมมติกฎหมาย exclusivity | ไม่ควร | หาที่ปรึกษา regulatory/patent สัก 1 คนรีวิว |
| เลือกวารสาร ตรวจ quartile/APC | ช่วยร่าง | ตรวจ SJR/JCR เอง |
| คุยลูกค้า ขาย รับเงิน | ไม่ได้ | คุณ |
| ตรวจว่าตัวเลขในต้นฉบับตรงกับ output | ใช่ (ทำซ้ำได้) | สุ่มตรวจ |
