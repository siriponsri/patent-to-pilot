# 01 — โปรแกรมวิจัย (Research Program)

ชื่อบทความชั่วคราว: *Abstention-aware, evidence-traced forecasting of generic and biosimilar competitive entry from public regulatory records: a time-split benchmark*
ประเภท: **outcome + method + architecture** (ไม่ใช่ diagnosis paper)

## 1. คำถามวิจัยและสมมติฐาน

- **RQ1** จากข้อมูลสาธารณะ ณ เวลา t โมเดลทำนายได้ดีแค่ไหนว่าจะมี ANDA/biosimilar รายแรกอนุมัติภายใน h เดือน (h = 12, 24, 36)?
- **RQ2** การให้โมเดล "งดตอบ" ในเคสที่หลักฐานขัดแย้ง/ไม่พอ ลด error ของเคสที่ตอบจริงได้หรือไม่ (selective prediction)?
- **RQ3** evidence graph แบบ Kleene สามสถานะเพิ่มคุณค่าเหนือโมเดลที่ใช้ตัวแปรเดียวกันแต่ไม่มีโครงสร้างหรือไม่?
- **RQ4 (ธุรกิจ/ภายหลัง)** ลำดับหลักฐานที่ควรหาถัดไป (VoI) ลดภาระผู้ประเมินคนจริงได้เท่าไร?

สมมติฐาน (กำหนดทิศทางไว้ก่อน — เป็น **ข้อเสนอ** ของแผน ไม่ใช่ผล):
- H1: ในชุดทดสอบเวลาอนาคต โมเดลเต็ม (graph + calibrated model + abstention) มี AURC ต่ำกว่า B1 (age table) โดย CI แบบ cluster ตามยาไม่คร่อม 0
- H2: ที่ coverage 70% ค่า selective error ต่ำกว่า B1 ในเชิงสัมพัทธ์อย่างน้อย 25% (ตัวเลขนี้ **เป็นตัวอย่าง** ต้องปรับหลัง power simulation ก่อน data lock)
- H3: ablation "graph only" และ "model only" แพ้โมเดลเต็มบน AURC อย่างน้อยหนึ่ง horizon

## 2. สามแทร็ก

| Track | ข้อมูล | ป้ายกำกับ | จุดแข็ง | ข้อจำกัด |
|---|---|---|---|---|
| A (prospective) | snapshot S0 วันตรึง ของยาที่ยังไม่มี ANDA/biosimilar | ตรวจซ้ำด้วยการ re-fetch ภายหลัง | ไม่มี leakage ไม่มี hindsight; คือหลักฐานที่ reviewer เชื่อมากที่สุด | ต้องรอเวลาให้ label ออก; จำนวนเหตุการณ์อาจน้อย |
| B (biologics) | Purple Book รายเดือน 2020–2026 | วัน approval 351(k) | ตรงกับเทรนด์ biosimilar ที่คุณสนใจ | n เล็ก (BLA biosimilar รวม < ~100) → เชิงพรรณนา ไม่พอเป็นข้อสรุปเชิงสถิติเดี่ยวๆ |
| C (retrospective, small molecule) | Orange Book + Drugs@FDA | first ANDA AP ภายใน h เดือนหลัง cutoff t | n พอสำหรับสถิติ | ไม่มี patent feature ย้อนหลังถ้าไม่มี OB edition เก่า (G1) |

ข้อเท็จจริงจากการ profile (เป็น **การสังเกต** ไม่ใช่ผล): entity 2,520; NME 1,495 (829 มี ANDA); Horizon 36 มี 10,873 แถว prevalence 0.1136; split (train cutoff ≤2014-01-01, test ≥2017-01-01) → test ~4,162 แถวจาก 757 ยา, positive 209 ยา (h=36) และ 189 (h=24). แถวไม่อิสระ ต้องใช้ cluster bootstrap ตามยา. Track A S0 ตัวอย่าง: 604 entity ไม่มี ANDA แต่มี OB record, 473 มีวัน patent, 417 NME → 1,251 แถว (417×3 horizons)

## 3. วิธี (Method / Architecture)

ดูรายละเอียดใน 05 สรุป: เอกสารหลักฐานต่อ entity → ตัวแปรชี้วัดระดับ element (exclusivity, patent, challenge) → Kleene tri-state ROOT = And(L_excl, Or(L_pat, L_challenge)) → verdict OPEN/BLOCKED/CONTESTED → ความน่าจะเป็น calibrated → decide(): PREDICT_ENTRY / PREDICT_NO_ENTRY / ABSTAIN_REFER_TO_EVALUATOR + next_evidence ตาม VoI

Arms เปรียบเทียบ:
- B0 base rate; B1 age/hazard table; B2 logistic; B3 exclusivity-expiry rule
- M1 model-only (ตัวแปรเดียวกับ graph แต่ไม่มีโครงสร้าง)
- M2 graph-only (verdict → ความน่าจะเป็นตาราง)
- M3 graph+model+abstention (ข้อเสนอ)
- M4 = M3 + VoI ordering (ประเมินในแง่ลำดับหลักฐาน)
- (ทางเลือก) L1 LLM one-shot ด้วย harness ใน `local_llm_smoke/` — ยังไม่ได้รันและไม่ได้ตรวจบน GPU

## 4. ตัวชี้วัด

หลัก: **AURC** (area under risk–coverage) ต่อ horizon. รอง: Brier, ECE, AUROC, selective error ที่ coverage 70%/50%, lead-time error (เฉพาะ Track A/B). เก็บ Brier/ECE เป็น calibration evidence ไม่ใช่ชัยชนะหลัก

## 5. สถิติ

- cluster bootstrap ตาม entity (ยา) สำหรับ CI ทุกตัว; paired difference ระหว่าง arms บน resample เดียวกัน
- multiple comparison: Holm ตลอดชุดสมมติฐานหลัก (H1–H3 × 2 horizons)
- embargo ระหว่าง train/test เท่ากับ horizon; ตัด right-censored rows
- Calibrate threshold lo/hi บน validation ให้ได้ coverage เป้าหมาย (task card ใน 08) — **ห้าม** จูนบน test
- Smoke result: B0 Brier 0.1064; B1 0.0985 (AUROC 0.771; AURC 0.0449); B2 0.1040 (AURC 0.0722). **นัยยะ:** age clock เดี่ยวๆ แข็งอยู่แล้ว การชนะ B1 ต้องมีสัญญาณจริง

## 6. เกณฑ์สำเร็จ / ล้มเลิก (ข้อเสนอ — ตรึงก่อน freeze)

- **สำเร็จ**: H1 จริงที่ h=24 และ 36 หลัง Holm และ Track A ไม่ขัดแย้งทิศทาง
- **ล้มเลิก/เปลี่ยนทาง**: CI ของ ΔAURC คร่อม 0 ทั้งสอง horizon → รายงานเป็นผลลบอย่างซื่อตรง และเปลี่ยนเป็นบทความ "benchmark + data descriptor" (Scientific Data) แทน และอย่าเรียกว่า "outstanding"
- ก่อน data lock ให้รัน power simulation (task card T4) ตารางพลัง McNemar แบบ exact ที่เคยคำนวณ (ใช้ประมาณการสำหรับ pilot ตัดสินใจเท่านั้น): ที่ n=60 คู่ผลต่าง (0.30 vs 0.05) พลัง 0.919; (0.20 vs 0.05) 0.581; (0.15 vs 0.05) 0.308

## 7. ความใหม่เทียบ prior art (ต้องอ้างให้ครบ ดู 10)

มีงานทำนาย/ประมาณ generic entry อยู่แล้ว (เช่น J Law Med Ethics 2019; Value in Health 2018; Clin Pharmacol Ther 2019/2020; Pharmaceutical Medicine 2020) และงาน biosimilar/patent thicket (J Law Biosci 2022 ฯลฯ) ช่องว่างที่ค้นพบ (จากการค้นระดับ abstract ของผม ไม่ใช่การรับประกันว่าไม่มีงานอื่น): ไม่พบงานที่รวม LLM/AI + FTO/infringement + selective prediction/abstention. ดังนั้นข้อเรียกร้องความใหม่ที่ปลอดภัย: (i) calibrated abstention พร้อม risk–coverage; (ii) benchmark แบบแบ่งเวลา + prospective freeze ที่เปิดเผย; (iii) evidence trace แบบ Kleene; (iv) ครอบคลุม biologics/biosimilars

## 8. ภัยต่อความถูกต้อง (Threats to validity)

1. ANDA approval ≠ วัน launch จริง
2. Drugs@FDA เก็บเฉพาะสถานะล่าสุด ไม่มีประวัติ
3. Orange Book patent เป็น snapshot ปัจจุบัน → leakage ถ้าใช้ย้อนหลัง
4. ingredient key เป็นการตัด salt แบบหยาบ ไม่ใช่ active moiety จริง
5. Survivorship: ยาที่ถูกถอนอาจหายจาก snapshot
6. แถวไม่อิสระ (ยาเดียวหลาย cutoff)
7. Track B n เล็ก
8. ผลของ paper 53 เองยังไม่ได้ตรวจซ้ำอิสระ (ไม่ได้กู้ original-run records)
9. ควอร์ไทล์วารสารยังไม่ยืนยัน