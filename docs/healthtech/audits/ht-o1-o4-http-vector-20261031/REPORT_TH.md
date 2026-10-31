# รายงานแพ็กเกจ HealthTech O1-O4: HTTP และ vector - 31 ตุลาคม 2026

สถานะ: `READY_FOR_REVIEW_PARTIAL_O4_O3_API_BLOCKED_LOCAL`

แพ็กเกจนี้ตรวจงานขอบเขต O1-O4 บน implementation commit
`928729ee1381280cc11d85439e63a71dff91432f` โดยเก็บเฉพาะ code provenance,
hash, sanitized receipt และผลคำสั่งที่ตรวจได้ Raw corpus, source payload,
vector bundle, model weights, evaluator labels, credentials และ private path
ยังอยู่นอก Git

## ผลลัพธ์

- **O1: COMPLETE** — loopback HTTP jobs, cancel/resume, source inspection,
  history version 1 ไป 2, export JSON/TH/EN และ provider selector ผ่าน
  browser acceptance จริงบน Chrome; backend/frontend bind อยู่ที่ loopback
  เท่านั้น
- **O2: COMPLETE** — PatEmbed-base และ multilingual-e5-base ถูกผูกกับ
  server-owned runtime/vector bundle อย่าง fail-closed; MitraClip, Tendyne และ
  TriClip ผ่าน HTTP/vector/history/export ครบ 3/3 ต่อโมเดล; ไม่มี provider call
  และไม่มีค่าใช้จ่าย
- **O3: BLOCKED_LOCAL** — local Qwen3-8B สร้างผล schema-valid ได้ 3/3 แต่การ
  เปรียบเทียบกับ `qwen/qwen3-32b` ยังไม่รัน เพราะ ledger identity, account credit,
  authorization และสิทธิ์ส่ง prompt ยังไม่ครบ
- **O4: PARTIAL** — real named-device HTTP/vector path ผ่าน แต่ adaptive report
  ยังเป็น descriptive offline evidence; deterministic controller ไม่ใช่ Qwen3,
  HT-B4 เป็น mock-only และ local generation ยังไม่ใช่ HTTP provider action

## หลักฐานสำคัญ

Full Python suite ผ่านด้วย exit code 0; มี optional skip เดิม 2 รายการและ
warnings เท่านั้น. Frontend suite ผ่าน `74/74`. Chrome loopback integration ผ่าน
การ start job, cancel ระหว่าง running, resume/retry, source inspection, history
edit, reload และ export JSON/TH/EN. Windows cleanup มี `EPERM` หลัง retry และ
ถูก defer เฉพาะ temp directory; acceptance ไม่ fail

Vector binding ตรวจ model/revision, config compatibility, role passage/query,
dimension, runtime order, query text hash, query id และ exact corpus patent ids
ก่อนเริ่ม job. Browser ไม่ได้รับ path หรือ raw vector bundle.

PatEmbed ใช้ revision `244ba452908a3093be11efb8a44396652317fb14` และ e5 ใช้
revision `d128750597153bb5987e10b1c3493a34e5a4502a`. ทั้งสองโมเดลมี corpus
41 patents และ 3 queries; HTTP jobs สำเร็จ `3/3`, dense candidates `33/33/41`,
vector errors `0`, source inspection HTTP `200`, history `1 -> 2`, export version
`2`, provider calls `0` และ paid cost `$0.00`

## การแยก adaptive evidence

- `HT-B0a/B0b`: company control และ BM25 lexical control
- `HT-B1`: fixed hybrid; dense + fixed fusion + local reranker
- `HT-B2`: fixed multi-query reciprocal-rank schedule
- `HT-B3`: simple observable heuristic; ไม่ใช่ LLM
- offline deterministic controller และ `HT-B4-MOCK`: ใช้ตรวจ action/accounting
  contract เท่านั้น; ไม่ใช่ provider evidence
- Qwen3-8B: local generation/schema-integrity evidence แยกจาก HTTP lifecycle
- qwen/qwen3-32b: `BLOCKED_LOCAL`, ไม่มี provider request

ผล Abbott offline controller: 3 devices, 41 patents, macro Recall@20 `0.4988`,
micro `0.4754`, 5 query calls, 0 provider calls. Boston: 2 devices, 7 patents,
macro/micro `1.0000`, 2 query calls, 0 provider calls. HT-B4-MOCK: macro `0.8857`,
micro `0.8462`, provider-shaped calls 8, simulated cost `$0.0008`, unknown billing
0. ตัวเลขทั้งหมดเป็น descriptive และไม่ใช่ semantic gold

## ข้อจำกัดและงานถัดไป

Product-level disclosed links ไม่ใช่ claim-level semantic relevance labels;
unlisted links ยังคง unjudged. DAPFAM เป็น citation-based diagnostic แยกต่างหาก.
แพ็กเกจนี้ไม่ยืนยัน clinical suitability, approval, FTO, validity, exhaustive
recall, investment merit, commercial adoption หรือ publication readiness.

เมื่อ O3 gates ครบ ให้ผูก local generation action เข้า HTTP job lifecycle เดียวกัน
แล้วเทียบกับ fixed controls ภายใต้ rights-cleared, hash-frozen protocol. ระหว่างนี้
คง paid provider dispatch เป็น fail-closed.
