# รายงานเช้า 19 พ.ย. 2026 — P1-BridgeRet (งานคืน 18→19 พ.ย.)

ทุกอย่างในรายงานนี้มาจาก receipt/log จริงใน repo หรือบน dr-train ไม่มีการเปิด TEST qrels หรือข้อความ query ของ TEST

## 1. เสร็จแล้ว
| งาน | ผล | หลักฐาน |
|---|---|---|
| Freeze split | manifest-v2 แบ่งตาม family, sha `c8443600…`, L-B PASS; P1-TEST 10,000 / P2-TEST 43,587 | `manifest-v2/FREEZE-RECEIPT.json` |
| Freeze แผน P1 | pre-declaration ล็อกก่อนมีตัวเลข retrieval ใด ๆ (commit `b9b2bd0`) | `plans/P1-BRIDGERET-PREDECLARATION.md` |
| Challenge-1M | 1,000,000 unit; tier1 (positive ของชุดประเมิน P1) 147,410 + tier2 (ถูกอ้างในงานอื่น) 852,590; gold ของ P1-TEST ปิดผนึก | `challenge1m` report (sha ใน pre-declaration) |
| ข้อความ | query non-TEST 149,933, corpus 1M passage (ไม่มี abstract 515) | `texts-v1-report.json` |
| Truncation | query ถูกตัดหาง claim ~9–11%, corpus 16.6%, ไม่ตัด title | `truncation-arctic-full-v1.json` |
| Coverage DEV | P1-DEV: OUT positive ที่ค้นได้ 95.7%; positive ที่เคยเห็นใน TRAIN 20.3%; task ที่ไม่มี positive เห็นใน TRAIN 48% | `dev-coverage-v1.json` |
| L-C near-dup | P1-DEV 0.53%, VAL 0.21% ของ query มี claim 1 คล้าย TRAIN (J ≥ 0.8) | `lc-neardup-summary-v1.json` |
| RunPod pilot | A40: encode fp16 457–669 p/s (1M ใน 0.4–0.6 ชม.); full FT ~11.5 ชม./epoch (7 negatives); pod ลบแล้ว | `runpod-pilot/RESULT.md` |

## 2. ตัวเลข DEV (descriptive เท่านั้น ไม่ใช่ผลยืนยัน)
P1-DEV n = 25,941 task ที่มี OUT positive ค้นได้ (VAL n = 1,957)

| ระบบ | OUT R@200 (P1-DEV) | IN R@200 | ALL R@200 | OUT R@1000 | OUT nDCG@10 | OUT R@200 (VAL) |
|---|---|---|---|---|---|---|
| B-BM25 | 0.1727 | 0.2529 | 0.2174 | 0.2866 | 0.0347 | 0.1794 |
| Z-Arctic (zero-shot) | 0.2248 | 0.3588 | 0.2979 | 0.3762 | 0.0435 | 0.2583 |
| RRF(BM25, Z-Arctic) | 0.2352 | 0.3625 | 0.3055 | 0.3820 | 0.0460 | 0.2655 |
| Z-Qwen3 (zero-shot) | QWEN_PLACEHOLDER |
| E0 (ตามกติกา: RRF กับ dense ที่ดีกว่าบน P1-DEV) | E0_PLACEHOLDER |

Power planning (DEV): σ_diff 0.22–0.33, design effect ตาม art unit 1.0–1.46 → ถ้า S* ต่างจาก comparator แบบ dense vs lexical ต้องใช้ ~12.8k task เพื่อจับ δ = 0.010 (มากกว่า n₁ = 10,000; MDE ≈ 0.011–0.012); ถ้าต่างแบบ E0 vs Z-Arctic ใช้ ~4k ก็พอ (`power-planning-dev-v1.json`)

## 3. ค่าใช้จ่าย
RunPod: USD 0.0752 (pod A40 ~18 นาที, list-pod-billing; pod ลบแล้ว, list-pods ว่าง). API: USD 0. ดาวน์โหลด: claims 11.28 GB + abstracts 3.3 GB + continuity 0.87 GB (รวมสะสม ~18 GB จากเพดาน 60 GB).

## 4. ต้องให้คุณตัดสินใจ (lane C)
1. Amendment A1 + งบ fine-tuning USD 20 (`plans/P1-BRIDGERET-AMENDMENT-A1-PROPOSAL.md`)
2. รับ light-approval protocol ไหม (`plans/OWNER-LIGHT-APPROVAL-PROTOCOL.md`)

## 5. ข้อจำกัด/สิ่งที่ควรรู้
- V100 บน dr-train มี service TTS ของ CIE ถือหน่วยความจำ 26.5 GB อยู่ งานของเราจึงรันแบบจำกัดหน่วยความจำ (~3.6 GB) ข้างกัน และช้ากว่าปกติ
- task ที่ไม่มี pre-grant publication (P1-DEV 949 จาก 26,575) ไม่มี query และได้คะแนน 0 ทุกระบบตามกติกาที่ล็อกไว้
