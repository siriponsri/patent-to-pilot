# K1a: why Paper 53 used `datalyes/patembed-base` as its single first stage

Status: DRAFT v2 for IS2 (agent, 19 Nov 2026), which replaces v1 of the same day.

**Correction log (v1 → v2).** v1 rested on arXiv:2605.24297 (Yousefiramandi & Cooney). That preprint was **withdrawn by arXiv Admin
on 5 Nov 2026** because it "does not meet arXiv's research content quality standards"; this was checked on the arXiv abs page on
19 Nov 2026. v1 was drafted from the owner's v1 PDF without checking the current status. v2 removes every number taken from that
preprint. Paper 53 cites the preprint as ref. [15], but only in its related-work list of patent-embedding benchmarks
("[14]-[16]"), not as the reason for choosing the encoder. If IS2 mentions it, state that it was withdrawn.

## What Paper 53 actually records (historical fact, not reconstructed)

Paper 53 §III-B (`literature-review/internal/paper53_ieee_express.pdf`) records:

> "Candidate generation indexed 45,336 frozen TAC records with the datalyes/patembed-base encoder [5], [18] and returned 100
> candidates per query. Normalized inner product served as cosine similarity, with deterministic ties ..."

- [5] = PatenTEB (Ayaou & Cavallucci, arXiv:2510.22264, 2025).
- [18] = the model card at revision `244ba452908a3093be11efb8a44396652317fb14`.

The paper records **which** encoder was used and **where it comes from**. It does **not** record a comparative selection
experiment. IS2 must not invent one after the fact.

Paper 53 §VI already lists this as a limitation: "one benchmark, candidate generator, TAC rendering, primary reranker, pool
depth of 100". It names broader retriever comparisons as future work.

## Answer for the IS2 report (Thai)

**เหตุผลที่ Paper 53 ใช้ `patembed-base` (ตามที่บันทึกไว้จริง)**

1. **ที่มาของโมเดล:** เป็นโมเดลตระกูล PatenTEB จากทีม ICUBE (INSA Strasbourg) ทีมเดียวกับผู้สร้าง DAPFAM [Paper 53 ref. 5, 18]
   - model card ระบุว่าฝึกแบบ multi-task บน 13 งานด้านสิทธิบัตรของ PatenTEB
   - ออกแบบมาสำหรับ prior-art search และ patent retrieval
   - Paper 53 จึงเลือก encoder เฉพาะทางสิทธิบัตรที่สอดคล้องกับ benchmark ที่ใช้
2. **ข้อมูลทางเทคนิค (จาก model card):**
   - distilled จาก patembed-large (12 จาก 24 layers)
   - 193M parameters, embedding 768 มิติ, รับข้อความได้ 512 tokens
   - ใบอนุญาต CC BY-NC-SA 4.0
   - pin revision ได้ ทำให้สร้าง candidate pool ที่ตรึงและตรวจซ้ำได้ ซึ่งเป็นเงื่อนไขของการเปรียบเทียบ instruction แบบ paired ใน Paper 53
3. **สิ่งที่ Paper 53 ไม่ได้ทำ:** ไม่ได้เปรียบเทียบ first stage หลายตัวก่อนเลือก
   - ข้อนี้คือข้อจำกัดที่กรรมการชี้ (K1a/K1b) และ Paper 53 ยอมรับไว้แล้วใน §VI
   - IS2 ตอบโดยทำการเปรียบเทียบจริงใน B53 แทนการเขียนเหตุผลย้อนหลัง

**หลักฐานเสริมย้อนหลังที่มีในโครงการ (ต้องติดป้ายให้ชัด ไม่ใช่เหตุผลตอนเลือก)**

| หลักฐาน | สิ่งที่บอก | ป้ายสถานะ |
|---|---|---|
| Paper 86 (งานของผู้วิจัย ยังไม่เผยแพร่ ถอนจาก IEEE) — 2026 nine-cell execution, 250 DAPFAM dev queries | PatEmbed (**large**) นำ Qwen3-Embedding-0.6B และ Arctic-embed-m-v2.0 ทุก recipe (ประมาณ 0.419 Recall@100) | HISTORICAL PROJECT RECORD; คนละรุ่นกับ base |
| P1-DAPFAM dev (B0 = PatEmbed-large) | OUT R@200 0.1477 บน DAPFAM dev 349 queries | MEASURED / REPOSITORY RECEIPT; คนละรุ่นกับ base |
| P1-BridgeRet P1-DEV (USPTO OA, 1M corpus) | Z-PatEmbed-large 0.3282 > Z-Qwen3 0.2741 > Z-Arctic 0.2248 OUT R@200 | MEASURED (DEV, descriptive); คนละ benchmark |

ทั้งสามแถวชี้ว่าตระกูล PatEmbed เป็น first stage dense ที่แข็งในงานแบบนี้ แต่ **ไม่มีแถวไหนวัด patembed-base บน cohort ของ Paper 53** จึงใช้เป็นบริบทได้เท่านั้น

**หลักฐานตรงที่ IS2 จะผลิต:** B53 วัด F0 = patembed-base เทียบกับ BM25, RRF(BM25, F0), Arctic และ RRF(BM25, Arctic) บน DAPFAM ชุดเดียวกัน ที่ K=100/200 (รองลงไปคือ F6 PatEmbed-large และ F7 Qwen3-Embedding) ผลนี้คือคำตอบเชิงประจักษ์ของ K1a/K1b

## English version

Paper 53 used `datalyes/patembed-base` (model-card revision `244ba452…`) as its single first-stage encoder, citing PatenTEB
[5] and the model card [18]. The archived text records provenance, not a comparative selection. The encoder is a
patent-specific PatenTEB model from the group that released DAPFAM. It was trained multi-task on 13 patent tasks. It is a
193 M-parameter, 768-dimensional, 512-token model with a pinnable revision. That allowed a frozen, reproducible candidate pool
for the paired instruction comparison.

Paper 53 did not compare first stages and names this as a limitation. Retrospective project evidence points the same way, but
none of it measures patembed-base on the Paper 53 cohort:
- the owner's unpublished study found PatEmbed-large ahead of Qwen3-Embedding-0.6B and Arctic-embed-m-v2.0 on 250 DAPFAM
  development queries;
- PatEmbed-large is also the strongest zero-shot encoder on a separate USPTO office-action development set.

IS2 replaces after-the-fact justification with a direct first-stage substitution (B53).

## Sources
- Paper 53, §III-B, §VI and refs [5], [15], [18] (`literature-review/internal/paper53_ieee_express.pdf`).
- datalyes/patembed-base model card, https://huggingface.co/datalyes/patembed-base (read 19 Nov 2026).
- I. Ayaou and D. Cavallucci, PatenTEB, arXiv:2510.22264 (2025).
- arXiv:2605.24297: withdrawn by arXiv Admin, 5 Nov 2026 (https://arxiv.org/abs/2605.24297). Not used as evidence.
- Paper 86 (owner, unpublished; withdrawn from IEEE): `myDegree/IS/IS_2/` (see `PAPER86-AND-P1DAPFAM-SELECTION.md` S2).
- P1-DAPFAM dev receipt: `docs/healthtech/audits/ptp-native-dense-preparation-20261110/dev-metrics-v1.json`.
- P1-BridgeRet DEV: `docs/healthtech/research/paper1-bridgeret/dev-results/`.
