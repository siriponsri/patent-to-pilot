# ร่างคำตอบข้อคิดเห็นกรรมการ IS1 (Paper 53) — สำหรับ IS2

สถานะ: DRAFT (agent, 19 พ.ย. 2026) อิงไฟล์ owner `owner-note-19112026/09_PAPER53_BRIDGE_AND_COMMITTEE_RESPONSE.md` (B53-0.1) และผลที่วัดแล้วใน repo เท่านั้น
ตัวเลขทุกตัวด้านล่างเป็น **descriptive บน DAPFAM dev ที่เปิดดูแล้ว** หรือ **OA P1-DEV** ไม่ใช่ผลยืนยัน และไม่ใช่การ replicate Paper 53
(ข้อมูลรันเดิมของ Paper 53 — qrels, pool, per-query — กู้ไม่ได้)

## ข้อคิดเห็นของกรรมการ
| # | ประเด็น |
|---|---|
| K1a | อธิบายที่มาของ patembed-base ที่ใช้เป็น first stage ตัวเดียว |
| K1b | มีเพียง 37.1% ของ query ที่มีเอกสารเกี่ยวข้องใน top-100 → ลอง BM25 หรือ hybrid แล้วรายงานในเล่ม |
| K1c | ระวังการสรุปเชิงสาเหตุใน RQ2 ที่มาจากการคำนวณย้อน (สมการ exposure) |
| K2a | ใน IS2 เปลี่ยน first stage เพื่อพิสูจน์ว่าข้อจำกัดอยู่ที่การค้นคืนจริง |
| K2b | เชื่อมกับผู้ใช้: ผู้ตรวจสิทธิบัตรได้ประโยชน์อะไร |

## สิ่งที่วัดไว้แล้ว (ใช้ตอบได้ทันที พร้อมข้อจำกัด)
| ประเด็น | หลักฐานที่มี | ที่มา | ข้อจำกัด |
|---|---|---|---|
| K1b BM25/hybrid บน DAPFAM | DAPFAM dev (474 query, OUT 349): first stage dense B0 (PatEmbed-large) OUT R@200 0.1477; BM25 0.0690; RRF(B0, BM25) 0.1280 (−0.0197; IN −0.0555). ทำซ้ำได้ทิศทางเดียวกันด้วย BM25 อีกค่าตั้ง (5 พ.ย.: −0.0223) | `paper2-precheck/HEADROOM-RESULT.md`, `audits/ptp-org-adaptive-stage1-20261105` | encoder ไม่ใช่ patembed-base, depth 200 ไม่ใช่ 100, cohort ไม่ใช่ 692 query ของ Paper 53 |
| K1b exposure | B0 มี OUT positive อย่างน้อย 1 ฉบับใน top-200 สำหรับ 136/349 query (39.0%); union BM25+dense ที่ 400 เพิ่ม exposure ได้แค่ 12 query; 201 query ไม่มี OUT positive ในทั้งสอง pool | `audits/ptp-native-exposure-20261111`, `HEADROOM-RESULT.md` | ไม่ใช่ rank แรกที่แน่นอน (bin หยาบ); judgments ไม่ครบ |
| K2a (ข้อมูลชุดอื่น) | OA P1-DEV (25,941 task, corpus 1M): OUT R@200 BM25 0.1727, Z-Arctic 0.2248, Z-Qwen3 0.2741, Z-PatEmbed-large 0.3282; RRF กับ BM25 ช่วย Arctic (+0.010) แต่ทำให้ Qwen3 แย่ลง (−0.008) | `paper1-bridgeret/dev-results/` | ต่าง benchmark (USPTO OA), descriptive |

ข้อความที่ใช้ได้: *"ในการตั้งค่านี้ การเพิ่ม BM25 ด้วย RRF ไม่ได้เพิ่ม exposure ข้ามสาขา (OUT) ของ DAPFAM dev และ query ส่วนใหญ่ที่ไม่มี OUT positive ใน pool ยังคงไม่มีแม้รวม pool สองแบบ"*
ข้อความที่ห้ามใช้: *"exposure เป็นสาเหตุที่ instruction ไม่มีผล"*, *"instruction ไม่สำคัญ"*

## สิ่งที่ยังต้องทำ (B53, ยังไม่รัน)
แผนอยู่ใน `plans/B53-FIRST-STAGE-SUBSTITUTION-DRAFT.md`: สลับเฉพาะ first stage (patembed-base, BM25, RRF, Arctic, Qwen3/PatEmbed-large ถ้าเจ้าของอนุมัติ, S* เมื่อ P1 เสร็จ) บน DAPFAM โดยคง query, label, การ render TAC, depth, reranker และ instruction ไว้ แล้ววัด exposure และ contrast ของ instruction บนชุด query ที่ exposed ในทุก first stage (common-exposed set) — ตอบ K2a โดยตรง

## K1a ที่มาของ patembed-base
ยังไม่พบเหตุผลที่บันทึกไว้ใน repo → ต้องให้เจ้าของเขียน (O16) อย่าเดา เหตุผลที่น่าจะใช้ได้ต้องมาจากบันทึกจริงของ Paper 53 เท่านั้น

## K1c ภาษาเชิงสาเหตุ
ใช้นโยบายภาษาใน file 09 §6: สมการ Δ = π · Δ_exp เป็น accounting identity เท่านั้น; ข้อสรุปว่า "การเปลี่ยน first stage เปลี่ยน exposure" มาจาก B53.1 ซึ่งเป็นการ manipulate จริง

## K2b ประโยชน์ต่อผู้ตรวจ
ยังไม่มีการวัดผู้ใช้จริง (NOT_MEASURED) ใช้ proxy ที่วัดได้บน benchmark: zero-exposure rate (1 − π), rank ของ OUT ฉบับแรก (r1), recall ภายใต้ budget การอ่าน; สมมติฐาน H5 ใน product roadmap ต้องยืนยันด้วยการสัมภาษณ์/ทดลองกับผู้ใช้
