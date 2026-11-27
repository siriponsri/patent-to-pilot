# 05 — Architecture Spec

## แผนภาพข้อความ
```
openFDA OB / Drugs@FDA / Purple Book / ClinicalTrials.gov
        │ (openfda_fetch, purplebook, SHA-256 MANIFEST)
        ▼
common.py  → norm_ingredient, ingredient_key, dates
dataset.py → Entity → features_at(t) → samples(cutoff t, horizon h) → time_split(+embargo)
        │
        ├─► baselines.py  B0 base rate | B1 age hazard | B2 logistic | B3 exclusivity rule
        │
        └─► evidence_graph.py  (Kleene strong 3-valued logic)
               ROOT = And( L_excl , Or( L_pat , L_challenge ) )
               leaf ∈ {TRUE, FALSE, UNKNOWN} → verdict ∈ {OPEN, BLOCKED, CONTESTED}
               + calibrated P(entry in h)  (ผูกกับ model บน validation)
               decide(): PREDICT_ENTRY | PREDICT_NO_ENTRY | ABSTAIN_REFER_TO_EVALUATOR
               + next_evidence (voi.py): หลักฐานชิ้นต่อไปที่ลดความไม่แน่นอนได้มากสุดต่อต้นทุน
        │
        ▼
metrics.py: Brier, ECE, AUROC, risk–coverage, AURC, selective error, cluster bootstrap (ตามยา)
trackA_freeze.py: ตรึง S0 + sha256 → ตรวจซ้ำภายหลัง
```

## ทำไมเลือกแบบนี้ (เชื่อมกับ paper 53)
- Paper 53 พบว่าการปรับ instruction ให้ผลใกล้ศูนย์ → ใช้โครงสร้างหลักฐานที่ตรวจสอบได้แทน
- สามสถานะ Kleene แยก "ไม่รู้" ออกจาก "เป็นเท็จ" → CONTESTED/UNKNOWN เป็นตัวกระตุ้น abstention
- VoI ให้ลำดับงานแก่ผู้ประเมินที่หายาก

## ข้อจำกัดที่ทราบ (ต้องแก้ใน task card)
- ค่าเริ่มต้น lo=0.25/hi=0.75 ทำให้แทบไม่ abstain: Track A ตัวอย่าง h12: BLOCKED 215 / CONTESTED 128 / OPEN 74 ทั้งหมด PREDICT_NO_ENTRY; h36: abstain 3 ราย
- โมเดลอิง age ไม่ใช้ patent feature จึงขัดกับ verdict OPEN → ต้องมี OPEN-conditional model (T2) และ threshold calibration (T1)
- ผล smoke ไม่ใช่ผลวิจัย; LLM arm ยังไม่ได้รัน
- ใช้ Python มาตรฐาน; ไม่มี sklearn/pandas

## ส่วนต่อขยายธุรกิจ (IS3)
ClinicalTrials.gov → ทำนาย launch date → เทียบกับ LOE ที่ทำนาย → remaining effective exclusivity = LOE − launch → demand-erosion forecast. ต้องการข้อมูลยอดขาย/ตลาด ซึ่งยังไม่ใช่ข้อมูลเปิด
