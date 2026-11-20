# ตอบไฟล์ 10/11 และร่าง AM-7.1 (20 พ.ย. 2026)

สถานะ: ข้อเสนอ **ยังไม่ freeze** เจ้าของเป็นผู้ตัดสินใจ
ยังไม่มีตัวเลข E2 ของระบบใดเลย และไม่ได้อ่าน TEST ใด ๆ ใช้งบ USD 0
อ่านแล้ว: `docs/owner/owner-note-20112026/` 10, 11, `citation_audit.md`, `p1_rethink_literature_insights.md`

## 1. ข้อสรุปสั้น

1. **รับข้อ audit ทั้ง 8 ข้อ** และมีสามเรื่องที่หนักกว่าที่ไฟล์ 11 ระบุ
   - confound จากการลดคะแนนตามโดเมนกระทบ E1 ด้วย ไม่ได้กระทบแค่ E2 (ข้อ 2.1)
   - E2 มีทางลัดผ่านกราฟ co-citation ที่ยังไม่มี baseline ไหนครอบ (ข้อ 2.2)
   - PatEmbed มีความเสี่ยงปนเปื้อนสูง เพราะถูกฝึกบน citation ข้ามโดเมนโดยตรง (ข้อ 2.3)
2. **วัดความแม่นของป้าย E2 ได้แล้ว** จาก PANORAMA ซึ่งมี rejection แยกราย claim: คู่เอกสารที่ "ถูกอ้างร่วมใต้ 103 ใน action เดียวกัน" ถูกรวมกันจริงใน rejection ของ claim เดียวกัน 73.6% และราว 50% ของคู่มีเอกสาร primary อยู่ด้วย (ข้อ 3)
3. **ข้อแนะนำ:** ออก AM-7.1 ก่อนรัน stage 2a ใช้ทาง 1 ของไฟล์ 11 (α และจำนวนสมมติฐานเท่าเดิม) แต่ขยายชุด comparator ของ D2 และ C4 ให้ครอบ confound ในเชิง confirmatory ร่างอยู่ในข้อ 5

## 2. สิ่งที่พบเพิ่มเมื่อคิดลึกขึ้น

### 2.1 Confound จากการลดคะแนนตามโดเมน กระทบทั้งสอง endpoint

ไฟล์ 11 ชี้ถูกแล้วว่า A1/A2 อาจได้ OUT recall เพิ่มเพียงเพราะลดคะแนนเอกสาร IN แต่ปัญหานี้ไม่ได้อยู่แค่ E2

- E1 คือ conditional OUT R@200 ระบบใดก็ตามที่แค่กดเอกสารซึ่งมี IPC3 ร่วมกับ q ลงไป จะได้ OUT R@200 เพิ่มโดยไม่ต้องรู้อะไรเลย และ C4 (P\*) ก็เปิดช่องนี้พอดี
- ทางแก้ที่เป็น confirmatory คือใส่ baseline **N4 = IPC-demotion** (ไม่ใช้ป้าย ใช้แค่ metadata) ไว้ในชุด comparator ของทั้ง D2 และ C4
- ถ้า A\* หรือ P\* ชนะ N4 ได้ ก็แปลว่าผลไม่ได้มาจากการเลี่ยง IN อย่างเดียว
- ข้อมูล IPC ของ corpus หาได้จาก `patentsview/g_ipc_at_issue` และ `pg_ipc_at_issue` ซึ่งมีอยู่บน dr-train แล้ว ไม่ต้องดาวน์โหลดใหม่

### 2.2 ทางลัดผ่านกราฟ co-citation

ใน E2 ระบบรู้ anchor ถ้าเอกสาร a กับ t เคยถูก examiner อ้างร่วมกันใน office action ของคำขออื่นมาก่อน การนับ co-citation แบบ "คนที่อ้าง a ก็อ้าง t" อาจแก้ E2 ได้ดีโดยไม่ต้องอ่านข้อความเลย

- งานเก่าใช้ co-citation เป็นตัว rerank ทับ text retrieval แล้วได้ผล เช่น TREC-CHEM และ [Mahdabi & Crestani, CIKM 2014](https://www.idiap.ch/~pmahdabi/papers/cikm2014_mahdabi.pdf) reviewer จะถามถึงเรื่องนี้แน่
- ข้อเสนอ: ใส่ **N5 = co-citation prior** เข้าไปในชุด comparator ของ D2 เงื่อนไขของ N5:
  - นับจาก `oa2017/citations.csv` (ไม่ต้องดาวน์โหลด)
  - ใช้เฉพาะ action ที่ส่งก่อน action ที่ถูกเลือกของ q
  - ตัดคำขอทุกตัวในบล็อก TEST ออกจากแหล่งข้อมูล
  - ตัด q และสมาชิก family ของ q ออก
- ด้านบวก: N5 อาจเป็นเส้นทาง "wow" ที่แท้จริงก็ได้ คือ hybrid ระหว่างข้อความกับ co-citation ถ้า A\* เป็น hybrid แล้วชนะทั้ง N5 และ U0 ข้อเสนอนี้มีน้ำหนักกว่า A1/A2 มาก
- ข้อนี้ต้องประกาศก่อนเห็นตัวเลข N5 ใด ๆ

### 2.3 PatEmbed ถูกฝึกบน citation ข้ามโดเมนโดยตรง

จาก [PatenTEB (arXiv:2510.22264)](https://arxiv.org/html/2510.22264) และ [การ์ด retrieval_OUT](https://huggingface.co/datasets/datalyes/retrieval_OUT/blob/main/README.md):

- ข้อมูลมาจาก Lens.org ตั้งแต่ปี 1980 แบ่ง split แบบสุ่มโดย stratify ตาม IPC3 ไม่ได้แบ่งตามเวลา
- งานฝึกมี `retrieval_OUT` ซึ่งเป็น citation pair ที่ IPC3 ไม่ทับกัน ตรงกับนิยาม OUT ของเราเกือบเท่ากัน ป้าย positive ระบุเป็น `CITED_BY`
- เปิดเผยเฉพาะ test split ส่วน train ราว 1.74M ตัวอย่างยังไม่ปล่อย จึงตรวจทับซ้อนกับ P1 ตรง ๆ ไม่ได้
- ตัวเลข Z-PatEmbed 0.3282 จึงอาจสูงเกินจริงบางส่วน และอาจอธิบายได้ว่าทำไมห่าง Qwen3 มากขนาดนั้น ข้อนี้ยังเป็นสมมติฐาน ยังไม่ได้ยืนยัน

ผลที่ตามมา:

- C3 และ C4 รวมถึงทุกระบบที่สร้างบน vector ของ PatEmbed ต้องมี caveat นี้กำกับ
- เสนอให้เพิ่ม sensitivity ที่สร้าง A\* ใหม่บน backbone ที่ไม่ได้ฝึกด้วย citation (Qwen3-Emb หรือ BM25) เป็นผลเชิงพรรณนา
- ถ้าเจ้าของอนุมัติให้ดาวน์โหลด test split สาธารณะของ PatenTEB (CC BY-NC-SA, ต้องยอมรับเงื่อนไขก่อน) จะวัดได้ว่าคู่เอกสารในชุดของเขาทับกับคู่ใน P1-DEV เท่าไร ตรวจเฉพาะ DEV เท่านั้น
- ข้อ 2.3 ใช้ model card และ PatenTEB เท่านั้น ไม่ได้อ้าง arXiv:2605.24297 ซึ่งถูกถอนไปแล้ว

## 3. ความแม่นของป้าย E2 วัดจาก PANORAMA (CPU, USD 0)

PANORAMA (`parsed_CTNF`) แยก rejection ทุกข้อเป็นราย claim และเรียงเอกสารอ้างอิงตามลำดับที่ examiner เขียน ตัวแรกคือ primary จึงใช้ตรวจป้ายแบบของเราได้

- สคริปต์ `scripts/healthtech/panorama_combo_precision.py` ผลอยู่ที่ `am7/panorama-combo-precision.json`
- ไฟล์ข้อมูล: parquet sha256 `827a3940…`

| ชุด | action ที่มี 103 ≥ 2 ฉบับ | คู่เอกสาร | คู่ที่รวมกันจริงใน claim เดียวกัน | คู่ที่มี primary อยู่ด้วย |
|---|---|---|---|---|
| ทั้งหมด (8,143 records) | 5,188 | 21,174 | **73.6%** (macro 88.1%) | 49.5% |
| ยื่นถึงปี 2014 | 1,154 | 4,402 | 74.7% | 52.2% |

วิธีอ่านตาราง:

- ป้าย "co-cited" ของเราผิดในระดับคู่ราว 1 ใน 4 noise ระดับนี้ต้องเขียนเป็น limitation ไว้ใน paper
- anchor ที่เลือกด้วย hash เป็น primary ราวครึ่งเดียว ซึ่งตรงกับที่ AM-7 ใช้คำว่า "an IN co-reference"
- PANORAMA ยื่นช่วงปีหลังกว่า P1 (ส่วนใหญ่ 2013-2020) ตัวเลขนี้จึงเป็นการประมาณจากภายนอก ไม่ได้วัดจากชุดเดียวกัน

ทางเลือกที่ยังไม่ได้ทำ: ใช้ PANORAMA เป็นชุด validation แบบ claim-level ภายนอก โดยให้ primary เป็น anchor ป้ายชุดนี้แม่นกว่าป้ายของเรา แต่ต้องสร้าง corpus ของตัวเอง เพราะเอกสารที่อ้างหลายฉบับอยู่นอกหน้าต่าง Challenge-1M

## 4. Novelty: ต้องกรอบให้ถูก

- [TRP-Pat (Yoo & Han, J. Intellectual Property 2025)](https://doaj.org/article/7fea1022e8d0463baa5911b3f852bc76) ทำโจทย์เดียวกันในแก่นคิด คือให้บางองค์ประกอบพร้อมเอกสารที่อ้างแล้ว แล้วแนะนำเอกสารสำหรับองค์ประกอบที่เหลือ บนข้อมูล USPTO ที่ถูกปฏิเสธเพราะ non-obviousness
  - ยังเปิดเนื้อเต็มไม่ได้ (403) จึงไม่รู้ขนาดชุดข้อมูลและผลของเขา
- ไฟล์ 11 สรุปถูกแล้วว่าห้ามอ้าง "first" หรือ "new task"
- สิ่งที่ป้องกันได้มีห้าอย่าง:
  - สเกล: P1-DEV 20,857 task และ TRAIN 73,897 task
  - นิยามข้ามโดเมน IN→OUT
  - TEST ที่แบ่งตามเวลาและปิดผนึกไว้
  - control ครบชุด: N4 IPC-demotion, N5 co-citation, decoy, shuffled
  - ความแม่นของป้ายที่วัดได้จริง
- โอกาส "wow" ยังเป็นสมมติฐาน ผมคิดว่า A1/A2 แบบไม่ฝึกน่าจะให้ผลเล็กหรือถูก N4 อธิบายได้หมด ทางที่มีลุ้นกว่าคือ hybrid ข้อความกับ co-citation และ reranker แบบมีเงื่อนไขที่ฝึกบน 73,897 task ข้อนี้เป็นความเห็น ยังไม่มีตัวเลขรองรับ

## 5. ร่าง AM-7.1 (English, ยังไม่ freeze)

> **AM-7.1 (proposed, before any E2 number on any block).** Amends AM-7 §3-§6 for the items below only; α, the number of confirmatory hypotheses and the decision rule are unchanged (option 1 of owner file 11).
>
> 1. **Label-free domain baseline N4 (IPC-demotion).** s(d) = cos(q, d) − γ·1[IPC3(d) ∩ IPC3(q) ≠ ∅], γ ∈ {0.05, 0.10, 0.20}, IPC from PatentsView `g_ipc_at_issue`/`pg_ipc_at_issue` (unit = union over its documents). An E2 version uses the same score (the anchor is only removed from the ranking).
> 2. **Co-citation baseline N5.** score(d) = number of office actions in `oa2017/citations.csv` (citation_in_oa = 1, action_type 102/103) that cite both a(q) and d, counting only actions mailed before q's chosen action. Actions of applications in any TEST block, of q, and of q's continuity family are excluded. Ties and zero-score units are ordered by U0. N5 has no tuning parameter.
> 3. **Comparator sets.** N\* (D2) = the strongest on P1-DEV MR@200 of {N1, N2, N3, N4-E2, N5}. C4 becomes P\* − L\*, where L\* = the strongest label-free E1 comparator on P1-DEV OUT R@200 of {Z-PatEmbed-large, N4-E1, MMR over U0 (λ ∈ {0.5, 0.7, 0.9})}.
> 4. **Hybrid candidate A4.** A4 = RRF(best stage-2a candidate, N5) and A4′ = RRF(U0, N5), plain RRF with k = 60. These are registered candidates for A\* under the AM-7 §4 rule; they are selected only on P1-DEV MR@200.
> 5. **Decoy anchor (validity, descriptive).** d(q) = the highest-ranked U0 unit that shares an IPC3 with q and is not in C103(q) (any basis). Report A\*(q, a) − A\*(q, d) with the §5 bootstrap. If the interval includes 0, E2 gains are described as domain or perturbation effects, not as anchor complementarity.
> 6. **Selection margin for paid stages.** A candidate more complex than the simplest stage-2a candidate goes to a paid stage only if it beats it by ≥ 0.010 on P1-DEV MR@200 and its paired bootstrap interval excludes 0.
> 7. **Label precision and wording.** Reports cite the PANORAMA measurement (`am7/panorama-combo-precision.json`: 73.6 % of co-cited 103 pairs are combined in one claim-level rejection; 49.5 % include the first-listed reference). The label is called "co-cited under §103 in the same first non-final action", never "combined by the examiner". E2 is recall conditional on ≥ 1 OUT3 co-cited unit; the all-co-reference variant stays secondary.
> 8. **Contamination.** PatEmbed-large was trained on Lens.org citation pairs including a disjoint-IPC3 retrieval objective, with a non-temporal split (PatenTEB). All PatEmbed-based numbers carry this caveat. A\* is re-run on the Qwen3-Emb zero-shot backbone as a descriptive sensitivity. If the owner approves the PatenTEB public test-split download, its pair overlap with P1-DEV is reported (DEV only).
> 9. **Size.** Pre-opening TEST cohort sizes are given as ranges (A-eligible about 7,360-7,850; clean about 2,420-2,570 of 10,000).

## 6. สิ่งที่ต้องให้เจ้าของตัดสินใจ

1. ออก AM-7.1 ตามร่างหรือไม่ (ผมแนะนำให้ออก และต้องออกก่อนรัน stage 2a เพราะถ้าไม่มี N4 กับ N5 ผล E2 จะตีความไม่ได้)
2. อนุญาตให้ดาวน์โหลด test split สาธารณะของ PatenTEB เพื่อตรวจการทับซ้อนกับ P1-DEV หรือไม่ (เป็น light gate 3)
3. จะใช้ PANORAMA เป็น validation ภายนอกแบบ claim-level หรือไม่ (ข้อมูลมีอยู่แล้ว แต่ต้องสร้าง corpus เพิ่ม)
4. TRP-Pat: ถ้าเจ้าของมี PDF เนื้อเต็ม ขอไว้ใช้เขียน related work

## แหล่งอ้างอิงที่ค้นรอบนี้

- [PatenTEB, arXiv:2510.22264](https://arxiv.org/html/2510.22264)
- [retrieval_OUT dataset card](https://huggingface.co/datasets/datalyes/retrieval_OUT/blob/main/README.md)
- [patembed-large model card](https://huggingface.co/datalyes/patembed-large)
- [TRP-Pat, DOAJ](https://doaj.org/article/7fea1022e8d0463baa5911b3f852bc76)
- [PANORAMA, arXiv:2510.24774](https://arxiv.org/abs/2510.24774)
- [Patently-O, "Three Is Company" (2026)](https://patentlyo.com/patent/2026/06/three-is-company-new-data-on-%C2%A7-103-reference-counts.html): reference count ของ §103 เฉลี่ย 3.08 ต่อ statement และ 2-3 ฉบับคิดเป็น 65%
- [Mahdabi & Crestani, CIKM 2014](https://www.idiap.ch/~pmahdabi/papers/cikm2014_mahdabi.pdf)
- [TREC-CHEM co-citation re-ranking](https://trec.nist.gov/pubs/trec19/papers/fraunhofer-scai.chem.rev.pdf)
