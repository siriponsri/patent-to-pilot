# K1a: why Paper 53 used `datalyes/patembed-base` as its single first stage

Status: DRAFT for IS2 (agent, 19 Nov 2026), written from the sources the owner named: the attached paper
arXiv:2605.24297 and the model card https://huggingface.co/datalyes/patembed-base. Every number below is quoted from those
sources (checked against the arXiv HTML tables). None is a new measurement from this project.
Paper 53 already cites both sources: [5] PatenTEB (arXiv:2510.22264) and [15] arXiv:2605.24297, with the model card at
revision `244ba452…` as [18]. The rationale therefore follows the paper's own reference list.

## ข้อความสำหรับเล่ม IS2 (ภาษาไทย)

งาน Paper 53 ใช้ `datalyes/patembed-base` (model card revision `244ba452908a3093be11efb8a44396652317fb14`) เป็น first stage
ตัวเดียว ด้วยเหตุผล 4 ข้อ

1. **เป็นโมเดลเฉพาะด้านสิทธิบัตรจากกลุ่มเดียวกับผู้สร้าง DAPFAM**
   - patembed เป็นตระกูลโมเดลของโครงการ PatenTEB (Ayaou & Cavallucci, 2025) ทีม ICUBE, INSA Strasbourg ทีมเดียวกับผู้สร้าง DAPFAM (Ayaou, Cavallucci & Chibane, 2026)
   - model card ระบุว่าฝึกแบบ multi-task บน 13 งานฝึกของ PatenTEB และออกแบบมาเพื่อ prior-art search, patent retrieval, classification และ clustering
   - ใช้ตัวนี้จึงลดความเสี่ยงว่าโมเดลกับชุดข้อมูลใช้รูปแบบข้อความสิทธิบัตรคนละแบบ
2. **มีผลเทียบอิสระจากผู้ประเมินภายนอก (arXiv:2605.24297, Clarivate)** ซึ่งทดสอบ 22 โมเดลบน citation retrieval ของสิทธิบัตร WIPO assistive technology (46,069 queries)
   - patembed-base ได้ nDCG@10 เฉลี่ย 0.1634 (Table 5) อันดับ 7 จาก 19 โมเดล single-vector และสูงสุดในกลุ่มโมเดลเฉพาะด้านสิทธิบัตร
   - สูงกว่า Qwen3-Embedding-0.6B (0.1620), BGE-M3 (0.1410), PatentSBERTa (0.1397) และ BM25 (0.1435)
   - โมเดลที่อยู่สูงกว่าทั้งหมดมีขนาด 1B ถึง 12B พารามิเตอร์ ส่วน patembed-base มี 193M (model card)
   - ช่องว่าง IN−OUT ของ patembed-base (0.0948) แคบกว่าทั้ง 6 โมเดลที่อยู่สูงกว่า (0.1015–0.1081)
3. **บน DAPFAM เอง ทำได้ดีที่สุดในกลุ่มที่ผู้ประเมินภายนอกทดสอบ**
   - Table 19 ของ arXiv:2605.24297 แบบ zero-shot: mean nDCG@10 0.5406, TAC 0.5647, IN 0.5423 สูงสุดใน 4 base models (Qwen3-0.6B, BGE-M3, EmbeddingGemma-300m) และสูงกว่า BM25 (0.4208)
   - การ fine-tune เพิ่มบน landscape อื่นไม่ได้ช่วย patembed-base บน DAPFAM: R3 −0.3% และ R4 −7.5% ของค่าเฉลี่ย
   - ข้อนี้สนับสนุนการใช้โมเดลแบบ off-the-shelf โดยไม่ปรับเพิ่ม ซึ่งเป็นสิ่งที่ Paper 53 ต้องการ เพราะ Paper 53 ศึกษา reranker และ instruction โดยตรึง first stage ไว้
4. **ใช้งานได้จริงในขอบเขตงาน**
   - รับข้อความได้ 512 tokens และให้ embedding 768 มิติ จึงเข้ารูปแบบ TAC passage + MaxP บน GPU ตัวเดียว
   - สัญญาอนุญาต CC BY-NC-SA 4.0 ครอบคลุมงานวิจัยที่ไม่ใช่เชิงพาณิชย์
   - pin revision ได้ ทำให้ระบุตัวโมเดลซ้ำได้

**ข้อจำกัดที่ต้องเขียนคู่กัน (เชื่อมไป K1b และ K2a)**
- ใน OUT slice ของ DAPFAM ตาม Table 19, Qwen3-0.6B (0.0511) สูงกว่า patembed-base (0.0484) เล็กน้อย จึงไม่ควรเขียนว่า patembed-base ดีที่สุดในทุก slice
- ทั้งสอง benchmark แสดงว่าโมเดลทุกตัวตกหนักเมื่อเป็นข้ามสาขา: 55–65% บน WIPO และประมาณ 90% บน DAPFAM
- ดังนั้นการใช้ first stage ตัวเดียว แม้เป็นตัวที่ดีที่สุดที่มีหลักฐานในตอนนั้น ก็ยังจำกัดว่า reranker จะเห็นเอกสาร OUT ได้กี่ query (37.1% ใน Paper 53)
- นี่คือเหตุผลที่ IS2 สลับ first stage (B53: patembed-base, BM25, hybrid, Arctic และโมเดลจาก Paper 1) โดยตรึงส่วนอื่นไว้ทั้งหมด

**ข้อควรระวังในการอ้างตัวเลข**
- ตัวเลขของ arXiv:2605.24297 เป็น nDCG@10 แบบ document-level ภายใต้นิยาม relevance ของผู้เขียนเอง (relevance_score > 0)
- เทียบตรงกับ nDCG@100 ของ DAPFAM paper ไม่ได้ และเทียบกับ exposure@100 ของ Paper 53 ไม่ได้
- arXiv:2605.24297 ระบุ patembed-base ว่า "344M, BERT-for-Patents backbone" แต่ model card ระบุ 193M, distilled จาก patembed-large (12 จาก 24 layers)
- ในเล่มให้ใช้ข้อมูลสถาปัตยกรรมจาก model card เพราะเป็นแหล่งต้นทาง
- รายการอ้างอิงของ arXiv:2605.24297 พิมพ์ชื่อผู้เขียน PatenTEB ผิดเป็น "Tarek Ayaou" ชื่อที่ถูกคือ Iliass Ayaou ให้อ้างตาม PatenTEB/model card

## English version (for an English chapter or appendix)

Paper 53 used `datalyes/patembed-base` (model-card revision `244ba452…`) as its only first-stage encoder, for four reasons.

**(i) Domain fit and provenance.** patembed-base belongs to the PatenTEB model family, which was trained with multi-task
learning on 13 patent tasks. Its authors (ICUBE, INSA Strasbourg) also released DAPFAM.

**(ii) Independent evidence.** In an external 22-model benchmark of patent citation retrieval (arXiv:2605.24297), it was
the strongest patent-specialised encoder (mean nDCG@10 0.1634, rank 7 of 19 single-vector models; every model above it has
1–12 B parameters).

**(iii) Strongest of four on DAPFAM.** On DAPFAM in the same study it was the strongest of the four zero-shot base models
evaluated (mean nDCG@10 0.5406). Further fine-tuning on another patent landscape did not improve it (R3 −0.3%, R4 −7.5%).
This supports a frozen, off-the-shelf first stage for a study whose manipulated factor is the reranking instruction.

**(iv) Practical fit.** It is a 193 M-parameter, 768-dimensional encoder with a 512-token input, a non-commercial research
licence (CC BY-NC-SA 4.0) and a pinnable revision.

**Limitation (motivates IS2).** The same sources show that every encoder loses most of its effectiveness on cross-domain
(OUT) queries: 55–65% relative on WIPO and about 90% on DAPFAM. On DAPFAM's OUT slice, Qwen3-Embedding-0.6B was marginally
higher (0.0511 vs 0.0484). A single first stage therefore bounds how many queries the reranker can help, which is the
question the first-stage substitution study (B53) answers directly.

## Sources
- Paper 53 reference list (`literature-review/internal/paper53_ieee_express.pdf`, refs [2], [5], [15], [18]).
- A. Yousefiramandi and C. Cooney, arXiv:2605.24297 (2026): Tables 4, 5, 19, 20; §3.2, §3.8, §4.12. https://arxiv.org/abs/2605.24297
- datalyes/patembed-base model card: https://huggingface.co/datalyes/patembed-base (read 19 Nov 2026).
- I. Ayaou and D. Cavallucci, PatenTEB, arXiv:2510.22264 (2025).
