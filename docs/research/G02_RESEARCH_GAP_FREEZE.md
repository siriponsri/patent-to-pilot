# G02 — Bounded research-gap freeze v1

วันที่ 24 ตุลาคม 2026 · **DONE: planning synthesis** · ไม่มี model/API/GPU run หรือผล effectiveness ของ Patent-to-Pilot

เอกสารนี้เป็น **G02 research revision/addendum** ของ [RESEARCH_GAP_MATRIX](../RESEARCH_GAP_MATRIX.md) โดยไม่เขียนทับ shared file ระหว่าง Luna ทำ G03/G04 ใช้คู่กับ [CLAIM_EVIDENCE_MAP](../product/CLAIM_EVIDENCE_MAP.md) สำหรับ framing รุ่นแรก ไม่เปลี่ยน root GOAL/AGENTS, G01/G04 artifacts, data หรือ shared memory ผู้ทำงานถัดไปอ้างไฟล์นี้ได้โดยไม่ต้อง merge ไฟล์กลางก่อน

สำหรับเจ้าของ: [อ่านฉบับภาษาไทยสั้น](G02_OWNER_BRIEF_TH.md) รายละเอียดตำแหน่งแหล่งต้นฉบับ: [source coverage](G02_SOURCE_COVERAGE.md)

**Repository publication note:** local reading PDFs and the G02-only acquisition manifest remain local-only and are excluded from the public repository. Use the official citation/download URLs in [G02_SOURCE_COVERAGE.md](G02_SOURCE_COVERAGE.md), especially the arXiv links for S13 and S14, to retrieve the cited versions.

## 1. Objective, scope และจุดหยุด

คำถาม G02 คือ มีอะไรใน product/research vision ที่ทับงานเดิมแล้ว และเหลือคำถามใดที่ตรวจได้ภายใต้ no-independent-expert constraint ไม่ใช่ทำ systematic worldwide review หรือทดลองให้ proposed system ชนะ

ใช้ collection เดิม 35 external papers เป็นฐาน คัดอ่าน methods/evaluation/limits ที่เกี่ยวกับ claim โดยตรง 12 ฉบับจาก collection เดิม และเพิ่ม **SkillOpt/HarnessOpt-Bench เพียงสองฉบับตาม owner request** รวม selected sources 14 ฉบับ รายละเอียดระดับการอ่านแยกเป็นรายงาน ไม่อ้าง full critical appraisal ของทุก paper/appendix ไม่เพิ่ม general literature search เพราะ closest collisions ตอบ framing ได้แล้ว เก็บ PDF ใหม่สองฉบับกับ G02-only manifest ที่เป็น local-only ไม่มีการเปิด credentials, install workflow หรือ reproduce published systems

**จุดหยุด:** claims มี closest collision + source locators + boundary + discriminating test/falsifier; แยก repair กับ learning; มี owner brief และ G03 interface งานใหม่เปิดเฉพาะ trigger ที่กระทบข้ออ้าง ไม่ตั้ง periodic audit หรือใช้ “novelty ยังไม่แน่” เป็นเหตุให้ implementation preparation ค้าง

## 2. ข้อสรุปจาก prior work

| กลุ่ม | Source-backed observation | ผลต่อโครงการ |
|---|---|---|
| Adaptive patent search | S01 §§4–5/S31–S32 ให้ทบทวน what/where/how และลอง alternatives จาก intermediate results รวม learning จากการค้น | generic adaptive searching ไม่ใช่ gap ต้องมี adaptive-search comparator ไม่เอา practitioner assertion มาเป็น quantified timing evidence |
| Patent workflow/hypotheses | S02 §2/PDF pp.3–5 มี orchestration, DAG, critique, Graph RAG และ scientific hypothesis generation | เปลี่ยนชื่อเป็น patent→pilot หรือเพิ่ม agent roles ไม่ใช่ novelty ด้วยตัวเอง การเรียก LLM ว่า expert/gold ใน paper ไม่ทำให้เป็น independent human gold |
| Accumulated context/memory | S03 §§3–3.2/PDF pp.4–5 evolving playbook/delta updates; S04 §3/PDF pp.3–4 แยก local/shared procedures กับ user-bound preferences | memory structure/localization/scope มีแล้ว ต้องทดสอบ information-matched benefit และ scope errors |
| Transfer beyond one task | S05 §§2.3–3.2/PDF p.4 วัด specificity/generality, skill versioning/rollback; S06 §§4–6.1/PDF pp.5–8 ใช้ developer feedback และ sister-task transfer | “เรียนรู้จากคำแก้ไขแล้วทำงานถัดไปดีขึ้น” เป็น prior work โดยตรง คำถามเราแคบลงเป็น fresh patent-project transfer/family disjointness/evidence fidelity ภายใต้ controls |
| Repeated scoped maintenance | S07 §§3.1–3.6/PDF pp.3–6 รับ reviewer/policy/trajectory feedback, revise scoped skills และเก็บ regression history; Appendix D.3/p.20 แยก replayable feedback กับ advice | source-linked skills, per-category guards และหลาย update cycles ไม่ใช่ของใหม่ ต้องเปรียบเทียบ simple invalidation และไม่แปลง free-form advice เป็น scored truth |
| Graph-guided replay | S08 §II/PDF p.2 คัด candidates จาก graph และ replay ด้วย paired clean messages ภายใน declared domain | graph/minimal repair มี prior work แต่ clean counterparts เป็น oracle assistance ไม่ใช่ repair generator ที่เรามี ห้ามอ้าง exact minimality ของ runtime incomplete graph |
| Search workspace/drift | S09 §3/PDF pp.4–5 persistent candidates/selective presentation; S10 §3/PDF pp.3–4 reranker feedback anchored to original query | cache/workspace/query feedback ไม่ใหม่ ต้องแยก retrieval gain จาก downstream repair bookkeeping |
| Existing skill optimization | S13 §3/PDF pp.4–6: frozen target, bounded text edits, validation-selected reusable artifact | natural-language skill learning มี direct prior work ใช้เป็น comparator/building block ไม่สร้างใหม่เพื่ออ้าง novelty |
| Harness-optimization evaluation | S14 §3.1/PDF p.5 รวม memory/prompts/tools/control flow/code, fixes target model/environment/verifier และ separates dev/validation/test | memory-vs-code ไม่ใช่ valid distinction; fixed disclosure/budget boundary เป็น prior protocol |
| Evidence/testing | S11 §3/PDF pp.3–4 แยก correctness/citation quality; S12 §2/PDF pp.2–3 MFT/invariance/directional tests | literal witnesses/metamorphic behavior เป็น technical evidence เท่านั้น ไม่พิสูจน์ semantic feasibility หรือ clinical/legal truth |

นี่เป็นข้อสังเกตจาก inspected versions/sections ไม่ใช่คำยืนยันว่าทุกงานไม่มี feature ที่ไม่ได้อ่าน รายละเอียด evaluations ของงานเหล่านี้อยู่คนละ setting ไม่ใช้ reported improvements มาคาดผล PTP

### Material update: SkillOpt และ HarnessOpt-Bench

S13 เป็น SkillOpt โดยทีม Microsoft และมหาวิทยาลัยร่วมวิจัย; S14 เป็น HarnessOpt-Bench โดย Scale AI ตาม first-page affiliations เป็นคนละงาน S14 ประเมิน optimizer capability ไม่ใช่ประกาศ optimizer algorithm ที่จำเป็นต้องใช้เพียงแบบเดียว และ feasible harness รวม memory อยู่แล้ว

**Implementation default ที่เสนอ:** ใช้ existing SkillOpt-style optimization ผ่าน adapter เป็น base เมื่อเหมาะกับงานและงบ เพิ่มเฉพาะ domain-specific org/source/version/dependency safeguards ที่ test ได้ ไม่สร้าง generic optimizer ใหม่เป็นเงื่อนไขผ่าน goal และไม่อ้าง source-linked labels อย่างเดียวเป็น algorithm contribution

**Fairness correction:** S14 cap target-evaluation calls/passes/tokens แต่ optimizer inference metered/uncapped (§3.1/p.5); PTP งบจำกัดต้อง cap/report ทั้ง target และ optimizer รวม reflection/retrieval/retries ไม่หยิบ published target-only budget มาเทียบ total costs เรา S13 cheap deployment ไม่เท่ากับ cheap optimization; train cost ต้องรวมด้วย

### Nearest collision ที่ต้องให้ความสำคัญเพิ่ม

**PolicyBank S06** ใกล้ longitudinal vision มากกว่าคำว่า generic RAG: หลังจบ task ให้ developer pass/fail และคำอธิบาย แล้ว update policy entries ซึ่งมี capability scope ในการทดลอง sister tasks ถูกวางทันทีหลัง parent (§6.1/PDF p.8) จึงเป็น one-shot transfer ของ policy gap ที่เกี่ยวข้อง ไม่ใช่หลักฐาน distant independent patent-project learning ของเรา ความต่างนี้เป็นเหตุออกแบบ test ให้แยก ไม่ใช่ sufficient novelty proof

**ESCROW S07** ทับทั้ง cumulative revisions และ cost/guard claims: skills ถูกปรับเป็นรอบพร้อม persistent regression pool แต่ paper รายงาน primary evidence จาก proprietary financial workflow และระบุ no code/data release ใน Limitations/PDF p.32 นี่เป็น source-reported release limitation ของ version ที่อ่าน ไม่ใช่การค้นยืนยันว่าปัจจุบันไม่มี implementation ทุกแห่ง

**GCJR S08 v2** บอกชัดว่า oracle-assisted และไม่สร้าง replacement messages อัตโนมัติ (§I/PDF p.1; §II.A/p.2) Exactness จำกัด graph-feasible candidate domain/fixed replay outcomes การมี gold graph หรือ clean repaired output ให้ PTP จึงใช้ได้เฉพาะ oracle diagnostic แยก ไม่ใช่ผล autonomous system

## 3. คำถามที่ freeze สำหรับ implementation รุ่นแรก

### RQ-L — primary question ของส่วน cumulative learning

หลังได้รับ **0, 2, 5, 10 confirmed corrections** จาก earlier project briefs ความจำที่ผูกองค์กรช่วยลด objectively checkable errors บน **fresh family-disjoint patent projects** ได้ดีกว่าการให้ **exact same corrections ทั้งหมดตรงใน prompt** หรือไม่ โดยไม่เพิ่ม source errors หรือการนำ policy ผิดองค์กรมาใช้ และคุ้มกับ memory overhead หรือไม่

จุด K เหล่านี้เป็น proposed calibration schedule ไม่ใช่ completed runs หรือ final powered sample size ปรับได้จาก feasibility/cost ก่อน freeze final protocol ไม่เพิ่มจำนวนด้วยการนับ paraphrases เป็น independent projects

คำว่า confirmed จำกัดเป็น explicit organization stipulation/authorized declaration หรือ literal source fact ที่ผู้จัดทำตรวจ locator แล้ว ไม่หมายถึง owner/LLM รับรอง efficacy/manufacturability หรือ legal interpretation คำ self-critique ของ model อาจเป็น candidate feedback แต่ไม่เป็น confirmed evidence ด้วยตัวมันเอง

### RQ-R — distinct within-project revision question

เมื่อ approved constraint/source/result ที่ระบุชัดเปลี่ยน dependency-guided revision ลด residual contract violations หรือ update cost เหนือ deterministic invalidation, full regeneration, direct revision และ ordinary adaptive search ได้หรือไม่ พร้อมรักษา unaffected fields, source history และ unknowns

RQ-R ใช้ old handoff+change events; RQ-L ใช้ fresh project และ past feedback จะไม่ใช้ความสำเร็จของการซ่อมเคสเดิมมารองรับ learning across tasks สอง track รวมอยู่ใน product ได้ แต่ main paper อาจต้องจำกัด claims ตามข้อมูลและงบที่มีจริง

### Candidate contribution ที่ยังไม่ยืนยัน

1. Source-anchored constructed patent–organization task set ที่แยก organization grounding, extraction, revision และ cumulative transfer
2. Transparent implementation ของ scoped feedback memory ที่เชื่อมกับ current evidence/constraint dependencies และการถอน/แทนรุ่น
3. Empirical boundary ว่าเมื่อใดวิธีนี้คุ้มกว่าวิธีง่าย และเมื่อใดควรใช้ rules/direct feedback แทน

ไม่ใช้คำว่า first, universal organization learning หรือ novel generic memory ไม่รับรอง product effectiveness/WPI acceptance

## 4. กลไกที่เสนอ — สิ่งที่ระบบต้องทำ ไม่ใช่แค่ตั้งชื่อสถานะ

**M1: รับ correction ที่ตรวจได้** พร้อม organization/project scope, issuer/confirmation origin, effective interval, source witness หรือ explicit stipulation และสิ่งที่แก้ ถ้าขัดกับ hard policy ที่อนุมัติแล้ว ให้แสดง conflict/critical confirmation ไม่เขียนทับกฎเอง

**M2: แยกเนื้อหาที่จดจำ** ระหว่าง organization-bound capability/policy กับ reusable procedure เช่น “แยก substrate จาก final device material ก่อนเช็กข้อจำกัด” ไม่แปลงค่า material/yield ของ patent เก่าให้เป็น fact ของ patent ใหม่ และไม่แชร์ organization preferences ข้ามองค์กรโดยปริยาย

**M3: เลือกใช้ current scoped entries** ด้วย exact organization boundary, active version และ task relevance ก่อน semantic retrieval เก็บว่า entry ใดถูกใช้ บทเรียนต้องมี back-link ไป correction/source ที่ยืนยัน การตรวจ scope แบบ deterministic ต้องมี baseline ของมันเอง

**M4: สร้าง dependency จากสิ่งที่ระบบเห็น** ให้ current source assertion/constraint เชื่อม option/route/proposed test/handoff พร้อม uncertain links ไม่รับ evaluator-only expected dependencies

**M5: เมื่อเกิด change ให้ invalidation แบบระบุเหตุ** ค้น/อ่านเพิ่มเฉพาะ evidence gap ใน budget เดียวกับ baseline, recheck current witness, revise derived artifacts และคง unaffected records; graph ไม่ครบต้องเปิดเผย uncertainty/ขยาย bounded repair ไม่ประกาศว่าซ่อมน้อยที่สุดแน่นอน

**M6: ตรวจและเก็บรุ่น** ทุกวิธีใช้ validators เดียวกัน เก็บ memory revision/project diff และรองรับ rollback คำแนะนำที่ยังไม่ยืนยันเป็น hypothesis ไม่ถูก promote เป็น fact การขาดข้อมูลบล็อกเฉพาะ affected claim/route; unrelated draft/handoff เดินต่อได้ตาม G01

ความจำมีไว้ช่วย “ใช้วิธีทำงานและข้อกำหนดให้ถูก” ไม่แทนการอ่าน evidence ของ case ใหม่ การตรวจ semantic support ที่ยากยังไม่เป็น deterministic gold

## 5. Experiment blueprint ที่แยกสอง track

### T-L: cumulative transfer แบบ checkpointed learning curve

1. สร้าง development feedback curriculum และ fresh test projects โดย split family/base brief/scenario template ก่อน variants แยก donor feedback families จาก test-family groups ตรวจ near-duplicates หาก family mapping ไม่ยืนยัน อย่าเรียก family-disjoint จนตรวจได้
2. แต่ละ organization เริ่ม memory ว่างตาม policy ชุดเดียวกัน รับ prefix K corrections ที่เหมือนกันทุกวิธี; reset ระหว่าง independent organizations ไม่ใช้ cross-org memory store ร่วม
3. ก่อน test แต่ละ K ให้ checkpoint/freeze memory และ global prompts/tools/model configuration ทดสอบ fresh tasks แบบ read-only memory ไม่คืน test labels/results/feedback ให้ระบบ Learning เกิดจาก prior curriculum ไม่ใช่จากชุดทดสอบนี้
4. ถ้าใช้ held-out test panel เดิมหลาย K ให้ isolate แต่ละ run จากกัน ไม่ส่ง previous test outputs/results เข้า state และไม่ retune หลังดู panel ถ้าต้องการ online scored test stream ภายหลัง ให้แยก protocol/claims ไม่ปนกับ checkpoint design นี้
5. ใส่ exact same K correction records ให้ direct-feedback control ครบทั้งหมดภายใน context limit ถ้าใส่ไม่ครบให้ลด K/record length ด้วยกติกาที่ใช้ร่วมกันก่อน freeze อย่า truncate control เพื่อให้ memory ชนะ
6. Baselines: L0 no feedback memory; L1 all raw confirmed corrections in prompt; L2 retrieval-only raw-correction memory ไม่มี learned rewrite; L3 ACE-style playbook เป็น secondary comparator; L4 proposed scoped structured memory; L5 SkillOpt-style base/adapter เป็น closest optimizer comparator หรือ building block ตาม matched cohort ด้านล่าง ใช้ model/corpus/tools/output schema/validators/ceilings เดียวกัน ไม่ได้รับ extra labels
7. แยก **fixed-feedback cohort** (K raw confirmed corrections, ไม่มี adaptive selection feedback เพิ่ม) จาก **matched-optimizer cohort T-O** ถ้าใช้ SkillOpt validation gating: ให้ทุก optimizer เห็น training evidence ชุดเดียวกัน ใช้ current target model/environment/verifier เดียวกัน มี aggregate selection-score interface/target-call budget/optimizer-cost cap ที่เท่าเทียมและ hidden final test Freeze candidate ก่อน final test ไม่มี expected test answers/future feedback อนุญาตให้ direct-feedback/rules controls ใช้ inputs/selection opportunity ที่กำหนดเหมือนกันแต่ไม่บังคับใช้เงินจนหมด Log K corrections และ scored rollout/selection feedback แยกกัน ผล fixed-feedback อย่างเดียวไม่พออ้างว่าดีกว่า SkillOpt
8. ใน T-O เปรียบเทียบ same SkillOpt-style base กับ base+scoped org/source safeguards โดย same allowed edit surface, feedback opportunity และ checker wrapper ไม่ให้ P ได้ extra checker ยกเว้น feature ที่กำลัง ablate อย่างประกาศชัด หากจำกัด SkillOpt ให้เหมาะงบ เรียก scaled/inspired adaptation และบอก deviation ไม่เรียก exact reproduction
9. Rules+same extraction เป็น anchor ใน tasks ที่ explicit logic ตัดสินได้ หากอ้าง policy interpretation learning แบบใหม่ให้เพิ่ม PolicyBank-style method หรือจำกัดความแรงของ claim; การ implement แนวคิดเองไม่เรียก official reproduction
10. มี wrong-organization/superseded-feedback/contradictory-feedback/rollback challenges ที่ถูกประกาศล่วงหน้า ความขัดแย้งที่ resolution ยังไม่ยืนยันให้ report conflict ไม่เลือกคำตอบที่ตรงใจ evaluator

Primary learning outcomes ที่เสนอคือ explicit error burden บน fresh projects และ paired cost–correctness trade-off เสริม source-ID/locator/role integrity, false unknowns บน known fields, wrong-org/stale-rule usage และ artifact completeness รายงาน per-K curves/eligible counts ไม่อ้าง lifelong learning จาก curriculum สั้น

### T-R: within-project revision

แยก checked-fact bookkeeping, open-text fixed-source และ adaptive-search track ตาม protocol เดิม Track A ให้ checked facts เท่ากันทุกวิธีและ rules ควรทำได้ครบ Track open text ให้ raw current passages ไม่แจก tuples/graph; ใช้ lexical/component-window extractor และ one-pass extraction+rules เป็น strong comparator

R0 rules+same extraction; R1 full regeneration; R2 direct revision; R3 deterministic invalidation+same generator; R4 adaptive what/where/how search+ordinary regeneration/revision; P runtime dependency-guided targeted repair R4 เป็น implementation interpretation ของ S01 ไม่ใช่ reproduction ของ algorithm ที่ paper ไม่ได้ให้

adaptive-search pool ต้องมี verified distractors/recoverable evidence นอก initial retrieval และให้ทุกวิธีเข้าถึง pool เดียวกัน Fixed-source revision ไม่มีสิทธิ์อ้าง search-efficiency effect ถ้าใช้ memory ใน R ให้ freeze checkpoint เท่ากันทุกวิธีเพื่อไม่ปน learning effect

### Ablations, costs และ analysis

- R: no dependencies, no gap retrieval, no source-version tracking
- L: no learned consolidation (retrieval-only), no scope/version guard เมื่อใช้ synthetic nonprivate fixtures และ evaluator ยังคุมสิทธิ์ ไม่ใช้ ablation เป็นเหตุเปิดจริงข้ามองค์กร; rollback/contradictory feedback challenge
- นับ model calls/tokens, memory building/reflection/retrieval, retrieval/index setup, validation, repairs, retries/errors/timeouts และ wall time รายงาน total amortized กับ marginal cost แยกกัน ไม่มี valid handoff ให้ cost-per-valid เป็น undefined พร้อม totals ไม่แทนเป็นศูนย์
- ใช้ paired comparisons บน projects เดียวกัน uncertainty cluster ตาม connected family/brief groups และ organization/sequence ตาม design; variants ไม่ใช่ independent samples องค์กรน้อยต้องรายงาน descriptive limits
- Same-information design ไม่ได้แปลว่าทุก method ต้องใช้ token/calls จนเต็มเพดาน แต่ P ห้ามเห็น future feedback/expected answers/graph เพิ่ม Context allocation และ control fit ต้องบันทึกจริง ตาม disclosure discipline ที่มี prior work ใน S13/S14 ไม่อ้างว่า hidden-test/version-budget protocol เป็นสิ่งใหม่ของเรา
- ชื่อ inference model/provider/version/prices ตรวจ ณ การรันจริง แยกจาก owner-selected coding executor ไม่มี paid run authorization ใน G02

## 6. หลักฐานที่อ้างได้โดยไม่มี independent experts

| ชั้น | Reference/oracle | ข้ออ้างที่จำกัด |
|---|---|---|
| Literal source checks | publication/family/date fields ที่นิยามชัด, source versions, exact spans/locators | source กล่าวว่าอะไร/มีข้อความอยู่ตรงไหน ไม่ใช่ semantic/clinical truth |
| Explicit organization contracts | declared fictional rule หรือ authorized clear statement | ถูกตามกฎที่ทดสอบ ไม่ใช่ actual commercial/engineering feasibility |
| Controlled change relations | affected/unaffected fields, allowed states, known-positive/unknown slots | update/preservation/abstention ตาม coverage ไม่ใช่ complete plan quality |
| Released dataset labels | PLS classification/DAPFAM citation-family/enterprise QA ตาม convention | task-specific diagnostics ไม่ถ่าย labels เป็น gold ของ organizational utility |
| Semantic/clinical/legal interpretation | ไม่มี independent gold ใหม่ | unknown/exploratory owner observations; LLM/NLI proxies แยกและเปิดข้อจำกัด |

**All-unknown defense:** ต้องมี supported known-positive fields และ checks ที่ลงโทษ false unknowns การคง yield unknown เมื่อ packet ไม่มีผลวัดเป็นสิ่งถูก แต่การไม่ใช้ explicit source-backed material/role ที่มีให้เป็น failure ไม่เปลี่ยน positive interpretation ที่ต้องใช้ผู้เชี่ยวชาญให้เป็น deterministic label เพียงเพื่อเพิ่มคะแนน

Real patent text + synthetic company/constraints เป็น constructed scenario ไม่ใช่ validated actual pairing Public capability pages ไม่ยืนยัน current capacity/cost/access สมมติฐาน clinical/manufacturing อยู่ใน draft questions ไม่เป็น fact

## 7. หลักฐานแบบไหนสนับสนุน/หักล้าง

| ผลที่เกิด | สิ่งที่อ้างต่อได้ |
|---|---|
| L4 ดีกว่า L1/L2 บน predeclared cost–correctness comparison โดย source/scope error controls ไม่เสีย | สนับสนุน scoped-memory value ใน bounded task family ไม่ใช่ universal learning/business success |
| L4 ชนะ no-memory แต่ไม่ชนะ exact-feedback control | แสดงว่าข้อมูล feedback มีประโยชน์ ยังไม่แสดง superiority ของ memory method |
| R proposed เสมอ/แพ้ rules หรือ direct revision ด้วยต้นทุนสูงกว่า | ลด repair complexity; รายงาน boundary ไม่ซ่อนผลลบ |
| gain มาจาก gold dependencies/clean replacements/future feedback หรือ control context ถูกตัด | core comparison invalid ต้องแก้สาเหตุ ไม่ใช้เป็น evidence ของ method |
| source role/locator หรือ wrong-org errors เพิ่ม | แก้ mechanism/จำกัด claim ก่อนขยาย ไม่ตีความ correctness เฉลี่ยมาปิดบัง |
| CI/coverage ไม่พอแยก benefit | inconclusive ไม่ใช่พิสูจน์ว่าเท่ากันหรือไม่มีประโยชน์ |

ไม่กำหนด arbitrary target accuracy หรือรับรอง zero-risk จาก sample เล็ก Final endpoints, non-inferiority margins ถ้าจะใช้, multiple comparisons, sample size และ budgets ต้อง justify จาก pilot และ freeze ก่อน main runs

## 8. Interface ให้ Luna G03 โดยไม่แตะไฟล์ที่ Luna เป็นเจ้าของ

G02 ไม่พึ่ง bulk download เพื่อปิด framing และไม่ได้ตรวจสถานะ download ปัจจุบันของ Luna ส่งเพียง input contract สำหรับ G03:

1. ส่ง **actual local paths**, source URL, revision/release, license/attribution, actual parsed schema/counts และ acquisition limitations ของไฟล์ที่รับจริง ไม่เดาว่ายังอยู่ `methodology/datasets/` หาก Luna เลือก `data/`
2. Patent records ต้องคง publication IDs/family IDs เมื่อ source มี, date-field meanings, raw text และ text/version provenance ถ้า family mapping ไม่มีให้ประกาศ unknown ไม่สร้าง family keys จากชื่อคล้ายกัน
3. Enterprise sample ให้คำถามกับ **เอกสารทุก expected_doc_ids** ที่ตรวจว่ามีจริงใน pinned release แยก reference answer/expected IDs สำหรับ evaluator/curator ออกจาก runtime packet ของระบบที่ทดสอบ การมี linked sample ไม่ใช่ real pharma profile
4. แยก research-only/noncommercial data จาก product-eligible corpus และเก็บ source-specific conditions ไม่ใช้ data availability แทน permission เพื่อเผยแพร่
5. Coverage/domain/split report เป็นสิ่งที่ต้องตรวจจาก actual data ต่อ ไม่บังคับให้ G03 สร้าง clinical gold, confirmed actual pharma capability หรือจับคู่ real org–patent ให้ได้

เมื่อ G03 ส่งข้อมูลข้างต้นแล้ว G05/G06 จะใช้เลือก independent source groups และ final task construction ไม่ต้องกลับมา audit วรรณกรรมทั้งหมดใหม่

## 9. Exact unknowns และ targeted reopen triggers

ยังไม่ทราบว่า selected mechanism ให้ประโยชน์จริงหรือไม่, data domain coverage/independent families เพียงพอเท่าไร, main size/model/budget/variance จะเป็นเท่าไร, semantic claims ใดตรวจโดยไม่ใช้ expert ไม่ได้ และ journal จะเห็น contribution เพียงพอหรือไม่ สิ่งเหล่านี้เป็นสิ่งที่จะศึกษา ไม่ขวางการปิด G02

เปิด gap review ใหม่เฉพาะเมื่อ (a) พบ primary paper ที่รายงาน equal-feedback fresh patent-project transfer พร้อม source/scope/revision controls ตรง claim, (b) pilot แสดงว่าประโยชน์มาจาก known mechanism/simple rule ทั้งหมด, หรือ (c) data/feedback setting เปลี่ยนจน assumption ของ test ใช้ไม่ได้ ให้แก้เฉพาะ claim ที่ได้รับผล ไม่ค้นทั้งสาขาใหม่โดยไม่มีขอบเขต

## 10. Internal provenance และ publication boundary

Paper53 คงเป็น internal foundation ตาม [PROVENANCE](../../literature-review/internal/PROVENANCE.md) ไม่ใช่ external bibliography ในรอบนี้ ไม่ใช้ old aggregates เป็น fresh empirical evidence แนวคิด evidence absent vs within-pool response มี reuse note เดิม ก่อน submission ให้ resolve attribution/disclosure ตามสิ่งที่ใช้จริง ไม่อ้าง inherited formulation ว่าเพิ่งคิดขึ้น

WPI เป็น ambition; G02 ไม่ตรวจ current guideline/APC ใหม่และไม่รับรอง acceptance Owner review formative; งาน clinical/regulatory/legal validation ไม่เป็น gate ของ bounded technical study สถานะและไฟล์ส่งมอบอยู่ใน [G02 handoff](G02_HANDOFF.md)
