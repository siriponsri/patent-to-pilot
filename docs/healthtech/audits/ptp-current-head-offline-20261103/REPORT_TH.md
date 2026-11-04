# Checkpoint current-head offline frontier: 3 พฤศจิกายน 2026

แพ็กเกจนี้ทำต่อใน goal Patent-to-Pilot เดิม ไม่เปิด goal ใหม่ และไม่แก้
`run_real_baselines.py` ซ้ำ เพราะ failure-accounting repair อยู่บน candidate
แล้วและ regression test ยืนยันพฤติกรรมที่ต้องการ

## ผลการตรวจและรัน

- Candidate: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Frozen cohort: 3 อุปกรณ์, 41 patents, 61 disclosed reference pairs
- Config: `candidate_depth=41`, `rerank_depth=41`, `K=20`
- Baseline runner: 5 วิธี, จบครบทุก method/device row, failed queries = 0
- B4 offline controller: จบ 3/3 devices, failed devices = 0, controller steps = 8
- Failure regression: `4 passed`
- Full Python suite: `599 passed, 1 skipped, 2 warnings`; exit code `0`
- API calls = 0, paid cost = USD0.00, GPU jobs = 0, dataset downloads = 0,
  ledger mutations = 0

## Metrics ที่ได้จริง

| วิธี | Macro Recall@20 | Query calls | Rerank pairs |
|---|---:|---:|---:|
| HT-B0a | 0.442739 | 3 | 0 |
| HT-B0b | 0.662242 | 3 | 0 |
| HT-B1 | 0.498802 | 3 | 123 |
| HT-B2 | 0.568912 | 9 | 369 |
| HT-B3 | 0.498802 | 5 | 205 |
| HT-B4 offline | 0.498802 | 5 | 205 |

B4 มี Micro Recall@20 `0.475410` และ 8 controller steps เพิ่มเติม ตัวเลขนี้
ไม่ใช่หน่วยเดียวกับ query หรือ rerank pairs

ดังนั้นผลที่รองรับคือ **descriptive realized quality-resource frontier**:
B0b สูงสุดใน development slice, B2 สูงกว่า B1/B3/B4 ที่ endpoint นี้แต่ใช้
retrieval มากกว่า และ B4 เสมอ B1/B3 ไม่ใช่หลักฐานว่า adaptive ดีกว่า fixed

Shared inputs และ per-call depth เท่ากัน แต่ realized total budget ไม่เท่ากัน
จึงห้ามสรุป equal-total-budget superiority หรือ adaptive superiority จากตารางนี้
Post-hoc same-unit slice เดิมยังจำกัดที่ B1/B2-prefix-1/B3-prefix-1
(`3/123`, macro Recall@20 `0.498802` ทุกวิธี); B4 ไม่ถูกใส่ใน slice นี้
เพราะ controller steps ไม่ใช่ query/rerank budget ที่เทียบตรงกันได้

## Failure accounting และประวัติเดิม

Runner ปัจจุบันเก็บ partial attempts, measured wall/CPU time และ explicit
unknown resource fields โดยไม่เติม synthetic zero attempt ผลที่เข้าถึงได้ยัง
ไม่พบ completed round ที่ยืนยันว่าได้รับผลกระทบ (`NONE_KNOWN`) จึงไม่เขียน
ต้นทุนย้อนหลังและไม่แก้ historical receipts ความครบถ้วนของ private journals
ยังไม่ถูกพิสูจน์

## สถานะและข้อจำกัด

- Engineering: `COMPLETE`
- Scientific evidence: `PARTIAL`; ไม่มี semantic relevance gold, final holdout
  หรือจำนวน independent groups เพียงพอสำหรับ inferential claim
- Business validation: `PARTIAL_OPERATIONAL_POTENTIAL_ONLY`; ไม่มี external user,
  revenue, ROI หรือ willingness-to-pay evidence
- Manuscript: `PARTIAL_OWNER_REVIEW_AND_WPI_GUIDE_RECHECK`
- O3 paid/API: ยัง `BLOCKED_LOCAL` ตาม gate เดิม

Raw/parsed outputs อยู่ใน private artifact id
`healthtech/ptp-current-head-offline-20261103`; public audit เก็บเฉพาะ hashes,
metrics และข้อจำกัด ไม่เก็บ key หรือ restricted payload

Checkpoint ถัดไปคือ owner review ผล current-head และ manuscript ก่อน merge/push
ใด ๆ โดยไม่รวมผลจากคนละ candidate เป็น PASS เดียว
