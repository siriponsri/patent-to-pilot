# ตารางตอบข้อเสนอแนะกรรมการ IS1 (Paper 53) สำหรับ IS2 — v2

> **หมายเหตุการแก้ไข (22 พ.ย. 2569, owner note 22112026).** ตัวเลข "37.1%" ของ Paper 53 ถูกทำเครื่องหมาย **denominator to be recovered; do not reuse** ทุกจุดด้านล่าง เพราะยังไม่ได้ตรวจตัวหาร (257/692 คำค้น) กับตารางต้นฉบับของ Paper 53 ส่วนค่า π@100 = 0.371 ของ B53 (905 คำค้น) เป็นผลวัดของ B53 เอง ไม่ใช่ตัวเลขของ Paper 53 ข้อความเดิมคงไว้ตามเดิม

สถานะ: DRAFT v2 (agent, 19 พ.ย. 2026) อิงจาก:
- ผลประเมิน IS1 รายบุคคล (สอบ 15 พ.ย. 2569, 85/100, S);
- owner file `owner-note-19112026/09_PAPER53_BRIDGE_AND_COMMITTEE_RESPONSE.md` และ `PTP_IS2_Paper53_Research_Program_University_Impact_2026-11-19.md`;
- ผลที่วัดแล้วใน repo

ทุกตัวเลขติดป้ายระดับหลักฐานตาม evidence ladder (§3) ไม่มีตัวเลขใดเป็นการ replicate Paper 53 เพราะ qrels/pool/per-query เดิมกู้ไม่ได้

## 1. ตารางคำตอบ (Appendix D ของเล่ม IS2)

| # | ข้อเสนอแนะ | คำตอบใน IS2 | หลักฐาน | ป้าย | บทในเล่ม | สถานะ |
|---|---|---|---|---|---|---|
| K1a | อธิบายที่มาของ patembed-base ที่ใช้เป็น first stage ตัวเดียว | แยกให้ชัด: (1) เหตุผลที่บันทึกจริงใน Paper 53 คือที่มา PatenTEB/model card; (2) หลักฐานเสริมย้อนหลังที่ติดป้าย; (3) การเปรียบเทียบจริงใน B53 | `K1a-PATEMBED-RATIONALE.md` v2 | HISTORICAL RECORD + MEASURED (ต่าง cohort) | Ch.2, Ch.6 | ร่างเสร็จ; รอเจ้าของตรวจ |
| K1b | มีเพียง 37.1% ที่มีเอกสารเกี่ยวข้องใน Top-100 [**แก้ไข 22 พ.ย. 2569:** ตัวเลข 37.1% ของ Paper 53 ต้องกู้ตัวหารจากต้นฉบับ Paper 53 ก่อน ห้ามนำไปใช้ซ้ำ / denominator to be recovered; do not reuse] → ลอง BM25/hybrid | B53 F1 = BM25, F2 = RRF(BM25, F0), F4 = RRF(BM25, F3) ที่ K=100 (หลัก) และ 200 วัด exposure, first-hit rank, zero-exposure rate | B53 Stage 1 (`results/B53-STAGE1-RESULTS.md`): π@100 F0 0.371, BM25 −0.105, RRF(BM25,F0) +0.004 (ns), Arctic −0.054, RRF(BM25,Arctic) −0.035 | MEASURED | Ch.3–4 | **วัดแล้ว 19 พ.ย.** |
| K1c | อย่าสรุปเชิงสาเหตุจากสมการย้อนใน RQ2 | ใช้ Δ_all = π·Δ_exp เป็น accounting identity เท่านั้น และใช้เฉพาะเมื่อ unexposed = 0 ทุก arm บน pool เดียวกัน ข้อสรุปว่า "เปลี่ยน first stage แล้ว exposure เปลี่ยน" มาจาก B53.1 ซึ่งเป็น intervention จริง | owner file 09 §6 language policy | METHOD | Ch.3, Ch.6 | นโยบายภาษาตกลงแล้ว |
| K2a | IS2 ควรเปลี่ยน first stage เพื่อทดสอบว่าข้อจำกัดอยู่ที่การค้นคืนจริง | B53: เปลี่ยน **เฉพาะ** first stage โดยตรึง reranker (Qwen3-Reranker-0.6B, 4 instruction ตาม Table I + BGE plain), depth, TAC, label และ evaluator | B53 Stage 2 (`results/B53-STAGE2-RESULTS.md`): ไม่มี contrast คำสั่งใดใน 10 รายการที่มีนัยสำคัญบน C = 153 (Δ +0.001 ถึง +0.009, Holm p ≥ 0.695); Scrambled ≈ Generic; ผลคำสั่งใกล้ศูนย์ภายใต้ first stage ทุกแบบ | MEASURED | Ch.3–4 | **วัดแล้ว 22 พ.ย.** |
| K2b | ผู้ตรวจสิทธิบัตรได้ประโยชน์อะไร | รายงาน proxy ที่วัดได้: zero-exposure rate (1−π), first-OUT-hit rank, review depth (K=100 เทียบ 200), cost per recovered citation พร้อม demo Solution Scout; ผลต่อผู้ใช้จริง = NOT_MEASURED + แผนสัมภาษณ์ | B53 metrics + product demo | HYPOTHESIS / NOT_USER_VALIDATED | Ch.5 | ออกแบบแล้ว |

## 2. สิ่งที่วัดไว้แล้วและใช้ได้ทันที (พร้อมข้อจำกัด)

| ประเด็น | หลักฐาน | ที่มา | ข้อจำกัด |
|---|---|---|---|
| K1b BM25/hybrid บน DAPFAM | DAPFAM dev (OUT 349): dense B0 (PatEmbed-large) OUT R@200 0.1477, BM25 0.0690, RRF −0.0197 (IN −0.0555) | `paper2-precheck/HEADROOM-RESULT.md` | คนละ encoder (large), depth 200, ไม่ใช่ cohort 692 |
| K1b exposure | B0 top-200 exposed 136/349 (39.0%); union BM25+dense ที่ 400 เพิ่มได้ 12 query | `audits/ptp-native-exposure-20261111` | bin หยาบ, judgments ไม่ครบ |
| K1b / K2a งานของผู้วิจัยที่ยังไม่เผยแพร่ (Paper 86) | Top-200 ของระบบ PatEmbed-large: 78.3% ของคู่ strict-OUT ไม่อยู่ใน pool; reorder แบบ ideal ได้แค่ 0.188 → 0.260 | `PAPER86-AND-P1DAPFAM-SELECTION.md` S1 | ระบบ/ความลึกต่างกัน; ห้ามเรียก replication |
| K2a ข้อมูลชุดอื่น | P1-DEV (USPTO OA, 1M): OUT R@200 BM25 0.1727, Arctic 0.2248, Qwen3 0.2741, PatEmbed-large 0.3282 | `paper1-bridgeret/dev-results/` | คนละ benchmark, descriptive |

ข้อความที่ใช้ได้: *"ในการตั้งค่านี้ การเพิ่ม BM25 ด้วย RRF ไม่ได้เพิ่ม exposure ข้ามสาขา (OUT) บน DAPFAM dev"*
ข้อความที่ห้ามใช้: *"exposure เป็นสาเหตุที่ instruction ไม่มีผล"*, *"instruction ไม่สำคัญ"*, *"พิสูจน์แล้วว่าข้อจำกัดอยู่ที่ retrieval"*

## 3. Evidence ladder (ป้ายใต้ตัวเลข/ภาพทุกชิ้น)
`MEASURED / REPOSITORY RECEIPT` · `HISTORICAL PROJECT RECORD` · `ENGINEERING VALIDATED / SYNTHETIC` · `DESIGNED / NOT_RUN` ·
`HYPOTHESIS / NOT_USER_VALIDATED` · `PUBLISHED / ACCEPTED` (ต้องมีเอกสารตีพิมพ์จริง; สถานะ Paper 53 รอ DOI จากเจ้าของ)

## 4. สิ่งที่ต้องการจากเจ้าของ
- DOI / IEEE Xplore record ของ Paper 53 (PDF มี ISBN proceedings 979-8-3195-1044-0/26 แต่ไม่มี DOI)
- O17: bodies คัดจาก LaTeX source ของ Paper 53 (`IS_1/revision_05/source/main.tex` บรรทัด 102–105) ตรงตัวอักษร; นับ token ด้วย tokenizer ของ Qwen3-Reranker ได้ Generic 13 (ตรง), Patent-aware 28 (Table 29), Claim-focused 113 (Table 119), Scrambled 113 (ตรง) — caption ของ Table I ระบุว่าตัวเลขมาจาก submitted record และไม่ได้ tokenize ใหม่ จึงอาจมี whitespace/ขึ้นบรรทัดต่างกัน; ขอเจ้าของยืนยันว่าใช้ bodies ตาม source
