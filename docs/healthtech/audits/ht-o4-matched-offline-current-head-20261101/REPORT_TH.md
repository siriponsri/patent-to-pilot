# รายงาน O4 matched offline frontier — 1 พฤศจิกายน 2026

สถานะ: `PASS_DESCRIPTIVE_MATCHED_OFFLINE_FRONTIER_O3_BLOCKED`

รัน fixed controls `HT-B0a` ถึง `HT-B3` และ deterministic offline `HT-B4`
บน Abbott frozen cohort เดิม 3 อุปกรณ์ 41 สิทธิบัตร 61 disclosed pairs โดยใช้
candidate `891f3b3`, K=20, candidate/rerank depth 41 และ local MiniLM bundle เดิม

| วิธี | Macro Recall@20 | Query calls | Rerank pairs | Failed |
|---|---:|---:|---:|---:|
| HT-B0a | 0.442739 | 3 | 0 | 0 |
| HT-B0b | 0.662242 | 3 | 0 | 0 |
| HT-B1 | 0.498802 | 3 | 123 | 0 |
| HT-B2 | 0.568912 | 9 | 369 | 0 |
| HT-B3 | 0.498802 | 5 | 205 | 0 |
| HT-B4 offline | 0.498802 | 5 | 205 | 0 |

HT-B4 มี micro Recall@20 `0.475410` และ controller steps `8` ทุก attempt สำเร็จ
ไม่มี provider call, paid cost, GPU job หรือ ledger mutation

ผลนี้เป็นหลักฐาน reproducibility และ descriptive frontier เท่านั้น ไม่ใช่หลักฐาน
ว่า adaptive method ชนะหรือแพ้โดยทั่วไป เพราะ cohort ไม่มี final holdout มีเพียง
2 exact-patent groups และ 1 company group อีกทั้ง labels เป็น product-level
disclosed links ไม่ใช่ semantic relevance gold

raw rankings และ evaluator outputs เก็บอยู่นอก Git ที่ private artifact root ตาม
`CHECKPOINT.json` และ `verification.json`
