# Publication evidence plan — รุ่น 2

วันที่ 27 ตุลาคม 2026 · **PLANNED, ยังไม่มีผล scientific pilot/main**
เป้าหมายคือ manuscript ที่มีหลักฐานพอสำหรับพิจารณาส่งวารสารนานาชาติ ไม่ใช่คำรับรอง acceptance หรือ quartile

## Contribution ที่ต้องพิสูจน์

Candidate contribution: source/version-aware dependency repair ภายใต้ policy/organization changes ที่ลด stale/unsupported downstream claims และรักษา unaffected valid content ได้คุ้มต้นทุนกว่า matched alternatives
การมี agent, graph, UI หรือ integration ไม่ใช่ novelty โดยตัวมันเอง

| RQ | วิธีเปรียบเทียบและ primary evidence | สิ่งที่หักล้าง/ข้อจำกัด |
|---|---|---|
| RQ1 หลัง evidence change วิธี dependency-guided repair ลด stale/unsupported claims ได้หรือไม่ | paired update precision/recall, evidence support, constraint violations ต่อ independent case/family | NO_ADVANTAGE/INCONCLUSIVE ยอมรับได้; citation span ตรงอย่างเดียวไม่พิสูจน์ semantic support |
| RQ2 รักษา unaffected valid content ได้ดีเพียงใด | preservation/error propagation เทียบ full regeneration, direct revision, deterministic invalidation + same generator | ต้องตรวจว่า preserved content valid จริง ไม่ให้คะแนนเพราะไม่แก้อะไร |
| RQ3 คุณภาพต่อค่าใช้จ่ายดีขึ้นหรือไม่ | รวม initial graph construction, verification, failed attempts, repair, tokens, latency, actual/unknown cost | G11 full-generator-then-scoped-merge ไม่อ้าง compute saving จากชื่อ scoped |
| RQ4 กลไกใดทำให้เกิดผล | ablations ปิด dependency information / invalidation / policy conditioning ที่แยกได้ | ทุกวิธีได้ current evidence, same model budget/validators/retrieval opportunities; oracle graph ห้ามเข้า runtime |

## Prior work และ overlap ที่ต้องเปิดเผย

- Doyle (1979), truth maintenance: dependency-directed belief maintenance มีมานานแล้ว [primary source](https://www.sciencedirect.com/science/article/pii/0004370279900080)
- RARR: evidence-grounded minimal revision [ACL 2023](https://aclanthology.org/2023.acl-long.910/)
- Self-Refine: iterative feedback/revision [author paper](https://arxiv.org/abs/2303.17651)
- ALCE: correctness/citation quality [EMNLP 2023](https://aclanthology.org/2023.emnlp-main.398/)
- เทียบ internal Paper 53 และ Paper 86 ตาม provenance/gap matrix จริง ห้ามยก reused ideas/text/results เป็นของใหม่ หาก source/identity ของ Paper 86 ยังไม่ชัดให้ UNKNOWN และอ่านก่อน novelty claim

ต้องทำ recent closest-collision search เพิ่มก่อน freeze contribution ข้อเสนอข้างต้นยังไม่ใช่ established novelty

## ข้อมูลและ evaluator

1. Current PTP-0001..3 เป็น exposed authored development cases ทั้งหมด ไม่เป็น holdout ย้อนหลัง
2. SYN-* ใช้ stress/mechanism/UI tests เท่านั้น 48 rows ไม่ใช่ 48 independent real cases
3. เตรียม held-out real public-patent cases พร้อม rights, family/publication/template/time identity แยก actual historical updates จาก authored counterfactual perturbations
4. Freeze grouping ก่อน variants; shared source/template/dependency components อยู่กลุ่มเดียวกัน Unknown family ไม่พิสูจน์ family disjointness
5. Runtime worker เห็น current allowlisted packet เท่านั้น ไม่อ่าน future events, clean repairs, answer facts, evaluator dependency graph, expected doc IDs หรือ split selection hints
6. Independent expert rubric แบบ blind method labels, random order, agreement และ adjudication plan ต้องมีสำหรับ semantic/decision usefulness claims Owner feedback/LLM judge เป็น formative/proxy แยกต่างหาก UX ที่ลด human loop ไม่ลดความจำเป็นของ research validation

## Statistics และ sample justification

ใช้ paired case outcomes และ case/family cluster uncertainty/effect sizes; ไม่ใช้ generated rows/revisions เป็น independent N
ใช้ feasibility pilot ประเมิน variance/missingness และตั้ง precision/power rationale ก่อน final heldout sample; ไม่แต่ง N เพื่อให้ดู publication-ready
กำหนด missing/invalid/failed outputs เป็น outcomes ตาม protocol, denominator 0 เป็น NA รายงาน raw counts, intervals และ failure analysis
Pilot adaptation เปลี่ยน protocol ต้อง version/deviation log ไม่แก้ pre-registration ย้อนหลัง

## Manuscript skeleton และ evidence map

| Section | ต้องมีหลักฐาน | สถานะ |
|---|---|---|
| Introduction/RQs | domain need, literature collision/novelty matrix | ร่างได้; recent review ยังไม่ครบ |
| Data | provenance/rights, selection/splits/independent unit, counterfactual labels | development inventory มี; real heldout ยังขาด |
| Method | executable algorithm, scope/unknown/version handling, actual compute | bounded mechanisms มี; full proposed P ยังไม่พิสูจน์ |
| Experiments | strong baselines/ablations, same access/budgets, blind rubric | planned; B4 conditional pool-not-ready |
| Results | actual paired metrics, uncertainty/cost/failure tables | **NOT_RUN — ห้ามใส่ตัวเลขสมมติ** |
| Discussion | limitations, negative findings, business/legal claim boundaries | เขียนข้อจำกัดได้ ไม่อ้าง demand/valuation/FTO |
| Reproducibility | code/env hashes, exact prompts/schemas, manifests, accounting, permissible assets | offline evidence มีบางส่วน; clean-clone replay/complete package ยังต้องทำ |

## Journal fit และขอบเขตงบ

[World Patent Information](https://shop.elsevier.com/journals/world-patent-information/0172-2190) มี scope ด้าน commercial patent analysis, AI/language modelling for IP และ system benchmarking/real-data IR จึงเป็น candidate ที่ตรง domain
[Knowledge-Based Systems](https://shop.elsevier.com/journals/knowledge-based-systems/0950-7051) และ [Information Processing & Management](https://shop.elsevier.com/journals/information-processing-and-management/0306-4573) เป็นทางเลือกเมื่อ contribution เชิงวิธีแข็งแรงพอ
แหล่ง planning นี้ได้จาก parent research review; current authoritative 2026 category/year quartiles ยังไม่ verified และ author-guide ScienceDirect ติด HTTP 403 จึงยังไม่ยืนยันข้อกำหนด submission ล่าสุด

USD 5 เป็น feasibility budget ใหม่รวมทุก API call เท่านั้น ไม่ใช่งบที่พิสูจน์แล้วว่าพอทำทั้ง paper ไม่รวม expert labour/APC/hosting และไม่อนุญาต submission/APC expenditure
