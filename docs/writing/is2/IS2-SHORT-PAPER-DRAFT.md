# IS2 short paper — DRAFT v0.2 (Thai, faculty template AI4BA), 22 Nov 2026

สถานะ: ร่าง (agent) ต้องให้เจ้าของและอาจารย์ที่ปรึกษาตรวจ
- ตัวเลขทุกตัวมาจาก receipt ใน repo: Stage 1 ที่ `results/B53-STAGE1-RESULTS.md` และ Stage 2 ที่ `results/B53-STAGE2-RESULTS.md`
- v0.2 (22 พ.ย. 2569): ใส่ผล Stage 2 ในบทคัดย่อ, 4.2 และ 5 แล้ว และปรับงานต่อเนื่องให้ตรงกับโปรแกรม PTP-2026-11-21
- Word ฉบับจัดตามแม่แบบคณะ: `IS2-short-paper-draft.docx` สร้างจากไฟล์นี้
- ต้องตรวจก่อนส่ง: ชื่ออาจารย์ภาษาไทย, ตำแหน่ง, DOI ของ Paper 53

---

## ชื่อบทความ (TH)
การแทนที่ตัวค้นคืนขั้นแรกเพื่อวินิจฉัยข้อจำกัดของการเปิดเผยเอกสารข้ามสาขาในการจัดอันดับสิทธิบัตรด้วยคำสั่ง

ศิริพล ศรีเฮงไพบูลย์*1 และ [ชื่ออาจารย์ที่ปรึกษา ภาษาไทย]2
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง
เลขที่ 1 ซอยฉลองกรุง 1 แขวงลาดกระบัง เขตลาดกระบัง กรุงเทพฯ 10520

### บทคัดย่อ
งาน IS1 พบว่าคำสั่ง (instruction) ที่ออกแบบเฉพาะสำหรับสิทธิบัตรแทบไม่เปลี่ยนคุณภาพการจัดอันดับเอกสารข้ามสาขาของ reranker เมื่อเทียบกับคำสั่งทั่วไป
มีเพียง 257 จาก 692 คำค้น (ร้อยละ 37.1) ที่ผลค้นคืน 100 อันดับแรกของตัวค้นคืนขั้นแรกมีเอกสารข้ามสาขาที่ทราบว่าเกี่ยวข้องอยู่เลย
คณะกรรมการจึงเสนอให้ทดสอบว่าข้อจำกัดอยู่ที่ตัวค้นคืนขั้นแรกหรือไม่ งานนี้ออกแบบการทดลองแทนที่ตัวค้นคืนขั้นแรก (first-stage substitution) บนชุดข้อมูล DAPFAM
โดยเปลี่ยนเฉพาะตัวค้นคืนขั้นแรกและตรึง reranker คำสั่ง ข้อความ และวิธีประเมินไว้ทั้งหมด
ตัวค้นคืนที่เปรียบเทียบคือ patembed-base (ตัวเดิมของงาน IS1), BM25, Arctic-embed และการรวมผลแบบ RRF
ผลบนคำค้น 905 รายการที่มีเอกสารข้ามสาขาที่เกี่ยวข้อง พบว่า patembed-base เปิดเผยเอกสารข้ามสาขาใน 100 อันดับแรกได้ร้อยละ 37.1
- BM25 ลดลง 10.5 จุด (95% CI −13.6 ถึง −7.5)
- RRF ระหว่าง BM25 กับ patembed-base ไม่ต่างอย่างมีนัยสำคัญ (+0.4 จุด)
- Arctic-embed ลดลง 5.4 จุด

ดังนั้นการเพิ่ม BM25 หรือ hybrid ไม่ได้แก้ข้อจำกัดด้าน exposure ในบริบทนี้
ในขั้นที่สองได้จัดอันดับใหม่ด้วย Qwen3-Reranker-0.6B ภายใต้คำสั่งของ Paper 53 บนคำค้น 153 รายการที่ตัวค้นคืนทุกแบบเปิดเผยเอกสารข้ามสาขา
ผลคือไม่มีการเปรียบเทียบคำสั่งใดใน 10 รายการที่มีนัยสำคัญ (ผลต่าง nDCG@100 +0.001 ถึง +0.009, Holm p ≥ 0.69)
ผลของคำสั่งที่ใกล้ศูนย์จึงคงอยู่ไม่ว่าจะใช้ตัวค้นคืนขั้นแรกแบบใด

**คำสำคัญ:** การค้นคืนสิทธิบัตร, การค้นคืนข้ามสาขา, การจัดอันดับใหม่, ตัวค้นคืนขั้นแรก, การเปิดเผยเอกสาร

## Title (EN)
First-Stage Substitution to Diagnose Candidate-Exposure Limits in Instruction-Driven Cross-Domain Patent Reranking

Siripon Srihangpiboon*1 and Tuchsanai Ploysuwan2
School of Information Technology, King Mongkut's Institute of Technology Ladkrabang, 1 Chalong Krung 1 Alley, Lat Krabang, Bangkok 10520

### Abstract
In our IS1 study, patent-specific reranking instructions barely changed cross-domain ranking quality relative to a generic
instruction. Only 257 of 692 queries (37.1%) had a known cross-domain (OUT) relevant family in the first-stage top 100.
Following the IS1 committee, we test whether that limit lies in the first stage, with a first-stage substitution on DAPFAM. Only the
first-stage retriever changes; the reranker, instructions, text rendering and evaluation are held fixed. We compare
patembed-base (the IS1 first stage), BM25, Arctic-embed and their reciprocal-rank-fusion hybrids. On 905 OUT-eligible
queries, patembed-base exposed a known OUT family in the top 100 for 37.1% of queries:
- BM25 lowered exposure by 10.5 points (95% CI −13.6 to −7.5);
- the BM25–patembed hybrid was indistinguishable (+0.4 points);
- Arctic-embed lowered it by 5.4 points.

Adding BM25 or a hybrid did not relieve the exposure limit in this setting. In the second stage, we reranked with
Qwen3-Reranker-0.6B under the Paper 53 instructions, on the 153 queries exposed under every first stage. None of the 10
instruction contrasts was significant (Δ nDCG@100 from +0.001 to +0.009; Holm p ≥ 0.69). The near-zero instruction effect
therefore persisted under every first stage.

**Keywords:** patent retrieval, cross-domain retrieval, reranking, first-stage retrieval, candidate exposure

\* Author's e-mail: 68076060@kmitl.ac.th
1. Postgraduate Student, Artificial Intelligence for Business Analytics Program, School of Information Technology, KMITL
2. [ตำแหน่ง], School of Information Technology, KMITL

---

## 1. บทนำ
การค้นหางานที่มีมาก่อน (prior art) ในระบบสิทธิบัตรมักต้องหาเอกสารจากสาขาเทคโนโลยีอื่นที่ใช้กลไกเดียวกันแต่ใช้คำศัพท์ต่างกัน
ระบบค้นคืนแบบหลายขั้นตอนจะหาผู้สมัคร (candidate) ด้วยตัวค้นคืนขั้นแรกก่อน แล้วจึงจัดอันดับใหม่ด้วย reranker ที่รับคำสั่ง (instruction) ได้
งาน IS1 (Paper 53) ศึกษาว่าคำสั่งเฉพาะด้านสิทธิบัตรช่วยการจัดอันดับเอกสารข้ามสาขาหรือไม่ ภายใต้ candidate pool ที่ตรึงไว้
ผลคือความต่างของค่าเฉลี่ย strict OUT nDCG@100 ใกล้ศูนย์ (Patent-aware +0.0008, Claim-focused −0.0007)
และมีเพียงร้อยละ 37.1 ของคำค้นที่ pool มีเอกสารข้ามสาขาที่ทราบว่าเกี่ยวข้อง [1]

คณะกรรมการ IS1 ให้ข้อเสนอแนะสองข้อหลัก
- (K1) ให้อธิบายที่มาของตัวค้นคืนขั้นแรก patembed-base และลอง BM25 หรือ hybrid เพราะ exposure เพียงร้อยละ 37.1 อาจเป็นข้อจำกัดหลัก รวมทั้งระวังการสรุปเชิงสาเหตุจากสมการแยกผล
- (K2) ให้ IS2 เปลี่ยนตัวค้นคืนขั้นแรกเพื่อทดสอบว่าข้อจำกัดอยู่ตรงนั้นจริงหรือไม่ และให้อธิบายประโยชน์ต่อผู้ใช้

งานนี้ตอบด้วยการทดลอง B53 ซึ่งเปลี่ยน **เฉพาะ** ตัวค้นคืนขั้นแรกบนชุดข้อมูล DAPFAM [2] และตรึงปัจจัยอื่นไว้ คำถามวิจัยมีดังนี้
- (RQ1) การเปลี่ยนตัวค้นคืนขั้นแรกที่ความลึกเท่ากันเปลี่ยน exposure ของเอกสารข้ามสาขาที่ทราบว่าเกี่ยวข้องเพียงใด
- (RQ2) ผลต่างระหว่างคำสั่งเปลี่ยนไปอย่างไรเมื่อตัวค้นคืนขั้นแรกเปลี่ยน
- (RQ3) ความลึกของ pool (100 เทียบ 200 และ 1,000) มีผลต่อ exposure อย่างไร

## 2. แนวคิด ทฤษฎี และงานวิจัยที่เกี่ยวข้อง
**2.1 DAPFAM**
DAPFAM เป็นชุดข้อมูลค้นคืนสิทธิบัตรระดับ family มีคำค้น 1,247 family และเอกสารเป้าหมาย 45,336 family
แบ่งความเกี่ยวข้องเป็นภายในสาขา (IN) และข้ามสาขา (OUT) ตามการไม่มีรหัส IPC สามหลักร่วมกัน [2]
บทความต้นฉบับรายงานว่าผลข้ามสาขาต่ำกว่าภายในสาขามาก และ BM25 กับ RRF ไม่ได้ปิดช่องว่างนี้

**2.2 ตัวค้นคืนขั้นแรก**
- BM25 เป็นตัวเปรียบเทียบเชิงคำศัพท์มาตรฐาน [3]
- patembed เป็นตระกูลโมเดล embedding เฉพาะด้านสิทธิบัตรจากโครงการ PatenTEB [4] ฝึกแบบ multi-task บน 13 งาน
- Arctic-embed-m-v2.0 [5] และ Qwen3-Embedding [6] เป็น embedding ทั่วไปที่แข็งแรงในงานค้นคืน
- การรวมผลแบบ Reciprocal Rank Fusion (RRF) [7] เป็นวิธี hybrid ที่ใช้กันแพร่หลาย
- งานค้นคืนข้ามโดเมนในสิทธิบัตรชี้ว่าวิธี neural ไม่ได้ชนะ BM25 เสมอ และต้องรายงานแบบทำซ้ำได้ [8]

**2.3 Reranker และคำสั่ง**
Qwen3-Reranker-0.6B ให้คะแนนคู่คำค้น–เอกสารภายใต้คำสั่งที่กำหนดได้ [9] reranker เรียงลำดับใหม่ได้เฉพาะผู้สมัครที่อยู่ใน pool แล้วเท่านั้น
ถ้าเอกสารเกี่ยวข้องไม่อยู่ใน pool ทุกคำสั่งจะได้คะแนนศูนย์เท่ากัน

**2.4 ความสัมพันธ์เชิงบัญชี**
เมื่อคำค้นที่ไม่มีเอกสารเกี่ยวข้องใน pool ได้คะแนนศูนย์ทุกคำสั่งบน pool เดียวกัน
ผลต่างเฉลี่ยของทั้งกลุ่มจะเท่ากับสัดส่วน exposure คูณผลต่างในกลุ่มที่ exposed (Δ_all = π·Δ_exp)
นี่เป็นเอกลักษณ์ทางบัญชีเท่านั้น ไม่ใช่หลักฐานเชิงสาเหตุ [1]

## 3. วิธีดำเนินการวิจัย
**3.1 ข้อมูล**
- DAPFAM (revision a59a74ce ซึ่งข้อมูลตรงกับ 780f4011)
- ข้อความแบบ TAC (ชื่อเรื่อง บทคัดย่อ ข้อถือสิทธิ) ทั้งคำค้นและเอกสาร ตามที่ Paper 53 ใช้
- คู่ที่ relevance_score > 0 ถือว่าเกี่ยวข้อง
- กลุ่มหลักคือคำค้นที่มีเอกสาร OUT อย่างน้อยหนึ่งรายการ: 905 คำค้น (IN 1,217; ALL 1,247)
- กลุ่ม 692 คำค้นของ Paper 53 กู้รายการเดิมไม่ได้ งานนี้จึงเป็นการสร้างซ้ำ (re-implementation) ไม่ใช่การทำซ้ำผล (replication)

**3.2 ตัวค้นคืนขั้นแรก**
แขนหลักมีห้าแบบ
- F0 patembed-base @244ba452 (prompt แบบ MIXED)
- F1 BM25 (k1 = 1.5, b = 0.75)
- F2 RRF(F1, F0)
- F3 Arctic-embed-m-v2.0
- F4 RRF(F1, F3)

แขนรอง (ประกาศล่วงหน้า): F0 ที่ใช้ prompt แบบ OUT, F6 patembed-large และ F7 Qwen3-Embedding-0.6B
ทุกแขนดึง 1,000 อันดับแรกด้วย inner product แบบแม่นตรง และตัดข้อความที่ 512 tokens

**3.3 Reranker (ขั้นที่สอง)**
- Qwen3-Reranker-0.6B @e61197ed กับคำสั่งสี่แบบตามตาราง I ของ Paper 53: Generic, Patent-aware, Claim-focused, Scrambled
- ข้อความคำสั่งคัดลอกตรงจาก source ของ Paper 53
- ตัดคำค้นที่ 2,048 tokens และเอกสารที่ 4,096 tokens
- ตัวควบคุม: ไม่จัดอันดับใหม่ และ BGE-reranker-v2-m3
- reranker และคำสั่งเดียวกันใช้กับตัวค้นคืนขั้นแรกทุกแบบ

**3.4 ตัวชี้วัดและสถิติ**
- ตัวชี้วัดหลักของขั้นแรก: exposure π@100 = สัดส่วนคำค้นที่มีเอกสาร OUT ที่ทราบว่าเกี่ยวข้องอย่างน้อยหนึ่งรายการใน 100 อันดับแรก
- ตัวชี้วัดรอง: π@200, π@1000, อันดับของเอกสาร OUT ฉบับแรก, OUT Recall@100 และ @200, strict OUT nDCG@100
- ความต่างจาก F0: paired bootstrap 10,000 รอบ (seed 20261119), McNemar แบบแม่นตรง, ปรับ Holm บนสี่การเปรียบเทียบหลัก
- ขั้นที่สอง: เปรียบเทียบคำสั่งบนกลุ่มคำค้นที่ exposed ภายใต้ตัวค้นคืนหลักทุกแบบ (C) ปรับ Holm บน 10 การเปรียบเทียบ
- แผนการทดลองทั้งหมดตรึงไว้ก่อนเห็นตัวเลขใด ๆ (pre-declaration)

## 4. ผลการวิจัย
**4.1 Exposure ของตัวค้นคืนขั้นแรก (RQ1, RQ3)**

ตารางที่ 1 สัดส่วนคำค้นที่มีเอกสาร OUT ที่ทราบว่าเกี่ยวข้องใน k อันดับแรก (n = 905)

| ตัวค้นคืน | π@100 | π@200 | π@1000 |
|---|---|---|---|
| F0 patembed-base | 0.371 | 0.471 | 0.733 |
| F1 BM25 | 0.266 | 0.344 | 0.548 |
| F2 RRF(F1, F0) | 0.376 | 0.469 | 0.701 |
| F3 Arctic-embed | 0.317 | 0.419 | 0.632 |
| F4 RRF(F1, F3) | 0.336 | 0.431 | 0.643 |

OUT Recall@100 ของ F0–F4 เท่ากับ 0.160, 0.107, 0.170, 0.125 และ 0.141 ตามลำดับ และ strict OUT nDCG@100 เท่ากับ 0.061, 0.041, 0.063, 0.048 และ 0.052

ตารางที่ 2 ความต่างของ π@100 เทียบกับ F0

| ตัวค้นคืน | Δπ@100 | 95% CI | Holm p |
|---|---|---|---|
| F1 BM25 | −0.105 | [−0.136, −0.075] | < 0.001 |
| F2 RRF(F1, F0) | +0.004 | [−0.015, +0.024] | 0.75 |
| F3 Arctic-embed | −0.054 | [−0.077, −0.032] | < 0.001 |
| F4 RRF(F1, F3) | −0.035 | [−0.061, −0.010] | 0.017 |

จำนวนคำค้นที่เปลี่ยนจากไม่ exposed เป็น exposed เทียบกับที่เปลี่ยนกลับ (ได้/เสีย) ของ F1–F4 เท่ากับ 55/150, 46/42, 34/83 และ 54/86

ข้อค้นพบจากสองตาราง
- ตัวค้นคืนขั้นแรกเปลี่ยน exposure ได้จริง การใช้ BM25 อย่างเดียวลด exposure ลงชัดเจน
- hybrid แบบ RRF กับ patembed-base ไม่ต่างจาก patembed-base อย่างมีนัยสำคัญ
- แขนรองแสดงทิศทางเดียวกัน: patembed-large +0.002, Qwen3-Embedding −0.024
- การเปลี่ยนเฉพาะ prompt ของ patembed-base เป็นแบบ OUT เพิ่ม exposure 3.0 จุด (เชิงพรรณนา)
- แม้ดูลึกถึง 1,000 อันดับ ยังมีคำค้นร้อยละ 27 ที่ไม่พบเอกสาร OUT ที่ทราบว่าเกี่ยวข้องเลย
- ค่า π@100 ของ F0 (0.371) เท่ากับร้อยละ 37.1 ของ Paper 53 ในเชิงตัวเลข แต่กลุ่มคำค้นและขั้นตอนต่างกัน จึงไม่ถือเป็นการทำซ้ำผล

**4.2 ผลของคำสั่งภายใต้ตัวค้นคืนแต่ละแบบ (RQ2)**

ตารางที่ 3 ผลต่าง strict OUT nDCG@100 ระหว่างคำสั่ง บนกลุ่มคำค้น C ที่ตัวค้นคืนหลักทุกแบบเปิดเผยเอกสาร OUT (n = 153)

| ตัวค้นคืน | Patent-aware − Generic [95% CI] (ได้/เสีย) | Holm p | Claim-focused − Generic [95% CI] (ได้/เสีย) | Holm p |
|---|---|---|---|---|
| F0 patembed-base | +0.004 [−0.005, +0.014] (78/71) | 1.000 | +0.006 [−0.003, +0.016] (74/74) | 1.000 |
| F1 BM25 | +0.001 [−0.007, +0.012] (62/74) | 1.000 | +0.004 [−0.005, +0.014] (64/72) | 1.000 |
| F2 RRF(F1, F0) | +0.003 [−0.006, +0.013] (77/70) | 1.000 | +0.006 [−0.003, +0.016] (76/70) | 1.000 |
| F3 Arctic-embed | +0.007 [−0.003, +0.017] (84/64) | 1.000 | +0.009 [−0.000, +0.019] (81/65) | 0.695 |
| F4 RRF(F1, F3) | +0.005 [−0.004, +0.016] (84/64) | 1.000 | +0.007 [−0.001, +0.018] (77/66) | 1.000 |

ตารางที่ 4 ค่าเฉลี่ย strict OUT nDCG@100 บนคำค้น OUT ทั้งหมด (n = 905; คำค้นที่ไม่ exposed ได้ 0) เชิงพรรณนา

| ตัวค้นคืน | Generic | Patent-aware | Claim-focused | Scrambled | BGE (ไม่มีคำสั่ง) | ไม่ rerank |
|---|---|---|---|---|---|---|
| F0 patembed-base | 0.062 | 0.063 | 0.063 | 0.063 | 0.054 | 0.061 |
| F1 BM25 | 0.043 | 0.043 | 0.044 | 0.043 | 0.039 | 0.041 |
| F2 RRF(F1, F0) | 0.064 | 0.065 | 0.066 | 0.065 | 0.057 | 0.063 |
| F3 Arctic-embed | 0.052 | 0.054 | 0.054 | 0.053 | 0.044 | 0.048 |
| F4 RRF(F1, F3) | 0.056 | 0.057 | 0.058 | 0.057 | 0.048 | 0.052 |

ข้อค้นพบจากสองตาราง
- ไม่มีการเปรียบเทียบใดใน 10 รายการที่มีนัยสำคัญหลังปรับ Holm
  - ค่า p ที่ปรับแล้วต่ำสุดคือ 0.695 (ก่อนปรับ 0.070)
  - ค่าประมาณเป็นบวกเล็กน้อยทุกค่า แต่ช่วงความเชื่อมั่นครอบศูนย์ทั้งหมด
- คำสั่งแบบสลับคำ (Scrambled) ให้ผลใกล้เคียงคำสั่งจริง (+0.0002 ถึง +0.0010 เทียบ Generic บนคำค้นทั้งหมด)
  ทั้งที่การเปลี่ยนคำสั่งทำให้ผลของคำค้นที่ exposed เปลี่ยนไปถึงร้อยละ 91–98
- BGE-reranker แบบไม่มีคำสั่งต่ำกว่า Generic ทุกตัวค้นคืน (−0.004 ถึง −0.008 และช่วงความเชื่อมั่นไม่ครอบศูนย์)
- ค่า nDCG สัมบูรณ์อยู่ระหว่าง 0.04 ถึง 0.07 และเปลี่ยนตาม π@100 ของตัวค้นคืนแต่ละแบบ
  - ความสัมพันธ์ Δ_all = π·Δ_exp ตรงทุกแขน ซึ่งเป็นความสัมพันธ์เชิงบัญชี
- ตรวจความถูกต้อง: คอลัมน์ "ไม่ rerank" ตรงกับ strict OUT nDCG@100 ของขั้นแรกในหัวข้อ 4.1 ทุกแขน และกลุ่ม C มี 153 คำค้นเท่ากับขั้นแรก
- ข้อจำกัดในการตีความ
  - ผลนี้ไม่ได้พิสูจน์ว่าคำสั่งไม่มีผลเลย เพราะช่วงความเชื่อมั่นกว้างประมาณ ±0.01
  - ผลนี้ไม่ได้บอกว่า exposure เป็นสาเหตุ

## 5. สรุปผลการวิจัย
- **K1a:** Paper 53 ใช้ patembed-base ซึ่งเป็นโมเดลเฉพาะด้านสิทธิบัตรจากโครงการ PatenTEB [4]
  - ในการทดลองนี้ patembed-base เป็นตัวค้นคืนขั้นแรกที่ exposure สูงที่สุดในแขนหลัก
  - patembed-large ไม่ต่างกัน ส่วน Qwen3-Embedding และ Arctic-embed ต่ำกว่า
- **K1b:** BM25 และ hybrid ไม่ได้เพิ่ม exposure ข้ามสาขาบน DAPFAM ในการตั้งค่านี้ ข้อเสนอให้ใช้ BM25 หรือ hybrid จึงไม่ใช่ทางแก้ของเพดาน exposure ร้อยละ 37
- **K1c:** สมการ Δ_all = π·Δ_exp ใช้เป็นการบัญชีเท่านั้น ข้อสรุปว่า "การเปลี่ยนตัวค้นคืนขั้นแรกเปลี่ยน exposure" มาจากการเปลี่ยนตัวค้นคืนจริงในการทดลองนี้
- **K2a:** ผลยืนยันว่าตัวค้นคืนขั้นแรกกำหนดขอบเขตของสิ่งที่ reranker ทำได้
  - เมื่อเปลี่ยนเฉพาะตัวค้นคืนขั้นแรกและตรึง reranker ไว้ ผลของคำสั่งยังใกล้ศูนย์ในทุกแบบ (ตารางที่ 3)
  - ข้อสรุปว่าคำสั่งแทบไม่มีผลของ Paper 53 จึงไม่ได้เกิดจากการเลือก patembed-base ในการตั้งค่านี้
  - ผลนี้ตอบ RQ2: ผลต่างระหว่างคำสั่งไม่ได้เปลี่ยนไปตามตัวค้นคืนขั้นแรกอย่างมีนัยสำคัญ
  - ข้อจำกัดของ endpoint คือเพดาน exposure ไม่ใช่ถ้อยคำของคำสั่ง แต่ข้อนี้เป็นข้อสังเกตเชิงบัญชี ไม่ใช่ข้อพิสูจน์เชิงสาเหตุ
- **K2b:** ตัวชี้วัดที่สื่อถึงผู้ใช้คือ
  - สัดส่วนคำค้นที่ไม่พบเอกสารข้ามสาขาเลย (1 − π)
  - อันดับของเอกสารข้ามสาขาฉบับแรก (มัธยฐาน 22 ภายใต้ F0)
  - ความลึกที่ต้องอ่าน

  ส่วนประโยชน์ต่อผู้ใช้จริงยังไม่ได้วัด และต้องทดสอบกับผู้ใช้ในอนาคต
- **ข้อจำกัด:**
  - ข้อความร้อยละ 92 ยาวเกิน 512 tokens จึงถูกตัด
  - judgments มาจากการอ้างอิงและไม่ครบ
  - ผลอยู่บน benchmark เดียว
- **งานต่อเนื่อง:** โครงการ Patent-to-Pilot ขยายคำถามจากการจัดอันดับภายใน pool ที่ตรึงไว้ ไปสู่การได้มาและการดูแลหลักฐาน (evidence acquisition and maintenance)
  - ใช้ Evidence Engine ตัวเดียวร่วมกันทั้งงานวิจัยและต้นแบบ Workbench ที่ทำงานบนเครื่อง
  - เปรียบเทียบกับตัวค้นคืนแบบ lexical, dense และ hybrid ภายใต้เงื่อนไขที่จับคู่กัน
  - การทดลองฝึกตัวค้นคืนด้วยการอ้างอิงของผู้ตรวจ (BridgeRet) บนชุดพัฒนายังไม่ชนะตัวค้นคืนแบบ zero-shot จึงไม่ใช้เป็นข้อเสนอหลัก
  - งานต่อยอดเหล่านี้ยังไม่มีผลที่ตีพิมพ์

**กิตติกรรมประกาศ:** ในการเตรียมบทความนี้ ผู้เขียนใช้ Claude (Anthropic) ช่วยร่างข้อความ เขียนโค้ดทดลอง และจัดตาราง ผู้เขียนตรวจทานและรับผิดชอบเนื้อหาและผลทั้งหมด

## เอกสารอ้างอิง
[1] S. Srihangpiboon and T. Ploysuwan, "Diagnosing near-zero instruction effects in cross-domain patent reranking," in *Proc. iSAI-NLP 2026* (accepted; presented 20 Nov 2026; DOI pending).
[2] I. Ayaou, D. Cavallucci, and H. Chibane, "DAPFAM: A domain-aware family-level dataset to benchmark cross-domain patent retrieval," *Array*, vol. 29, p. 100720, 2026.
[3] S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," *Foundations and Trends in Information Retrieval*, vol. 3, no. 4, pp. 333–389, 2009.
[4] I. Ayaou and D. Cavallucci, "PatenTEB: A comprehensive benchmark and model family for patent text embedding," arXiv:2510.22264, 2025.
[5] P. Yu, L. Merrick, G. Nuti, and D. Campos, "Arctic-embed 2.0: Multilingual retrieval without compromise," arXiv:2412.04506, 2024.
[6] Y. Zhang *et al.*, "Qwen3 embedding: Advancing text embedding and reranking through foundation models," arXiv:2506.05176, 2025.
[7] G. V. Cormack, C. L. A. Clarke, and S. Buettcher, "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods," in *Proc. SIGIR*, 2009, pp. 758–759.
[8] S. Althammer, S. Hofstätter, and A. Hanbury, "Cross-domain retrieval in the legal and patent domains: A reproducibility study," in *Proc. ECIR*, 2021.
[9] Qwen Team, "Qwen3-Reranker-0.6B," Hugging Face model card, revision e61197ed, 2025.
[10] S. Holm, "A simple sequentially rejective multiple test procedure," *Scand. J. Stat.*, vol. 6, no. 2, pp. 65–70, 1979.
