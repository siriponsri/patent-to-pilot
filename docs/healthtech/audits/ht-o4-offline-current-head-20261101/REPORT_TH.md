# รายงาน O4 offline current-head revalidation — 1 พฤศจิกายน 2026

สถานะ: `PASS_CURRENT_HEAD_OFFLINE_ADAPTIVE_REVALIDATION_O3_BLOCKED_LOCAL`

รัน deterministic HT-B4 offline ซ้ำบน Abbott และ Boston cohorts ที่ freeze ไว้
แล้ว โดยใช้ candidate ปัจจุบัน `94ce5b1` และ local MiniLM ONNX เดิม ไม่ดาวน์โหลด
model ใหม่ ไม่ใช้ API และไม่เปลี่ยน denominator, K หรือ max-steps

| Cohort | Devices | Macro Recall@20 | Micro Recall@20 | Query calls | Rerank pairs | Failed | Paid cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Abbott | 3 | 0.498802 | 0.475410 | 5 | 205 | 0 | USD0.00 |
| Boston | 2 | 1.000000 | 1.000000 | 2 | 14 | 0 | USD0.00 |

ผลนี้เป็นหลักฐาน reproducibility และ descriptive engineering/scientific
evidence เท่านั้น ไม่ใช่หลักฐานว่า adaptive policy ชนะ fixed baseline หรือมี
semantic device-patent gold เนื่องจาก cohort ยังมี independent groups น้อย,
Boston มี K ceiling และลิงก์ระดับผลิตภัณฑ์ไม่ใช่ semantic relevance gold

Paid API, external business validation และการอ้าง generalization ยังคงไม่ปิด
ในรอบนี้

