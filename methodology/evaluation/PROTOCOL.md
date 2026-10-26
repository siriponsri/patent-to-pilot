# Protocol: การแก้ชุดหลักฐานเมื่อข้อจำกัดเปลี่ยน

**Current scope:** [GOAL G05/G06/G10–G17](../../GOAL.md) ขยาย product โดยแยก extraction/org fit/revision/longitudinal learning protocol นี้เป็นฐาน within-case evaluation ไม่ใช่เพดาน product Primary coding/research executor คือ `gpt 5.6 luna max` (mapping/availability unverified) แยกจาก exact experiment inference model ที่ต้อง log จริง การจัดเอกสารนี้ไม่เปลี่ยน frozen receipts หรือสร้างผลทดลอง

24 ตุลาคม 2026 · ข้อเสนอก่อนทดลอง · มี PTP-0001 development fixture หนึ่งเคส ยังไม่มี main benchmark/model runs/empirical scores

เอกสารนี้เป็นเครื่องมือประเมินผลิตภัณฑ์ Patent-to-Pilot เป้าหมายคือชุดส่งต่องาน R&D ที่มีประโยชน์ ส่วน benchmark จำกัดสิ่งที่พิสูจน์ได้ไว้ที่ explicit constraints, evidence provenance และต้นทุน ผู้วิจัยไม่มี independent experts มาสร้าง gold ของแผน R&D ความรู้เภสัชกรของเจ้าของช่วยเลือกและอ่านโจทย์ แต่ไม่ทำให้ owner/LLM labels เป็น independent clinical/legal gold

## หน่วยทดลองและข้อมูลที่ระบบเห็น

หนึ่ง base group มี approved organization brief/capability card, fixed option set สำหรับงานที่ต้องใช้ monotonicity, allowed source snapshot, observable facts พร้อม provenance, output schema, initial output และ change events แต่ละ variant มี expected-update specification ที่ evaluator เห็นเท่านั้น

แยก registry เป็น source (publication ID, family ID, document version, source file SHA256, date fields), passage (page/section, character offsets, quote/hash และ extraction version), fact (value, unit, status, evidence), constraint (ID, version, effective event, rule), option/test และ typed dependencies เก็บ source history หลังถอนหรือแทนรุ่น

Fact ทุกช่องระบุ origin เป็น source assertion / benchmark stipulation / interpretation คำกล่าวใน patent เป็นสิ่งที่เอกสารอ้าง ไม่ใช่ผลยืนยัน efficacy ข้อที่ไม่ชัดให้ unknown ไม่อนุมาน absence จากการค้นคำไม่พบ

ระบบเห็น brief, current allowed sources และ output schema ไม่เห็น gold dependencies, expected answers, hidden change oracle, clean repaired output หรือ future event ถ้าให้ supplied graph ต้องรายงานเป็น oracle upper bound แยกจาก graph ที่สร้างเอง

## การคัด 10 feasibility cases

1. เลือกเอกสารจริงที่อ่านได้และมี publication/family mapping ย้อนกลับได้ จาก 1–2 กลุ่มเทคนิคแคบที่เกี่ยวกับงานเภสัชหากหาแหล่งพอ
2. คัด fact ที่ตรวจเชิง extractive ได้ ระบุ span และหน่วย ห้ามตั้ง efficacy/manufacturability เป็น deterministic label
3. เขียน approved brief และ constraint contract ให้แยกจาก source fact หากทำ dependency ให้ชัดไม่ได้ ให้พักเคสนั้นพร้อม exclusion reason
4. สร้าง change อย่างน้อยหนึ่งครั้ง พร้อม affected/unaffected field IDs และ allowed output states
5. กำหนด validator positive/negative fixtures ให้ deliberately wrong source/version/value/eligibility ตกจริง ตรวจตัว validator ก่อนใช้ให้คะแนนระบบ
6. บันทึก oracle coverage ว่าส่วนใดตรวจไม่ได้ รวมถึง semantic entailment และความเหมาะสมของ experiment

ครบ 10 cases ที่มี provenance และ validators แล้วเริ่ม technical pilot ได้ ไม่ต้องรอ expert panel เป้าหมายขยาย 30–60 independent groups × 4–8 transformations เป็นข้อเสนอที่ปรับหลัง calibration ไม่ใช่ sample size ที่สร้างแล้วหรือรับรอง power

## Change operators และ preconditions

| Operator | Preconditions | Expected behavior ที่ตรวจได้ |
|---|---|---|
| Material/capability toggle | fixed options และ positive declared fact/dependency ที่ชัด | option ที่พึ่งสิ่งถูกห้ามไม่เป็น eligible; evidence เดิมยังเก็บอยู่ |
| Irrelevant/no-op change | ยืนยันว่าความหมายของ technical constraints ไม่เปลี่ยน | eligibility/fact/evidence IDs เดิมคงอยู่; อนุญาตเฉพาะ presentation fields ที่ระบุ |
| Threshold tightening | fixed facts/options, normalized known values/units, ไม่มี missing-value inference | eligible set หลังลด maximum เป็น subset; missing remains unknown |
| Sole-support withdrawal | ระบุ sole support ใน allowed snapshot และไม่มีแหล่งทดแทนที่อนุญาต | affected field เปลี่ยนเป็น unsupported/unknown หรือหา evidence ใหม่ในงบ; ไม่ใช้ revoked source ต่อ |
| Source replacement | scenario ระบุการแทนรุ่นและค่าที่เปลี่ยนชัด | downstream fields ใช้รุ่นใหม่; ประวัติรุ่นเก่าไม่หาย ไม่ยึดค่าที่ถูกใจ |
| Family duplication | verified same-family mapping | publication count เพิ่มได้ แต่ distinct-family count ไม่เพิ่ม |
| Metadata date trap | scenario ระบุ required date field เช่น publication date | ไม่ใช้ priority/earliest-claim date แทน; ถ้า field ไม่ชัดให้ unknown |
| Explicit conflicting facts | facts สองชุดใช้ definition/unit เดียวและขัดกันชัด | report conflict/uncertainty ไม่ silently overwrite; semantic conflict ที่กำกวมอยู่นอก primary oracle |
| Missing evidence | required slot ไม่มี observable support ใน allowed snapshot | appropriate unknown/abstention/clarification ไม่แต่ง fact ให้เต็ม schema |

Paraphrase invariance ใช้เฉพาะ transformation ที่ผู้สร้างตรวจความหมายแล้ว ไม่ใช้ LLM paraphrase เป็น truth อัตโนมัติ Metamorphic consistency ตรวจความสัมพันธ์ระหว่างคำตอบ ระบบอาจตอบผิดอย่างสม่ำเสมอได้ จึงต้องมี source checks ร่วมด้วย

## Baseline matrix

| Method | วิธีอัปเดต | วัตถุประสงค์ |
|---|---|---|
| B0 rules + frozen facts | deterministic eligibility/recompute | ทดสอบว่างานจำเป็นต้องใช้ agent หรือไม่ |
| B1 static RAG/full regeneration | generate handoff ใหม่ทั้งหมด | ค่าใช้จ่ายและข้อผิดพลาดของการเริ่มใหม่ |
| B2 direct revision | old output + change + same evidence | strong simple editing comparator |
| B3 deterministic invalidation + same generator | invalidate ด้วยกฎ แล้วให้ generator เดียวกันแก้ | แยกผลของกฎจาก adaptive agent |
| B4-RG adaptive-search + regeneration | bounded what/where/how alternatives จาก intermediate results แล้ว regenerate | comparator inspired by Oltra-Garcia; implementation interpretation ไม่ใช่ exact reproduction |
| B4-DR adaptive-search + direct revision | search policy เดียวกับ B4-RG แล้วแก้ old handoff ทั่วไป | แยก search effect จาก regeneration/editing |
| P dependency-guided repair | runtime graph + bounded evidence-gap retrieval/revision | proposed workflow |

ใช้ same model/corpus/schema/validators และงบที่ประกาศเท่ากัน ไม่ให้ P ได้ checker พิเศษ รายงาน actual token/tool usage และ failures ไม่บังคับให้ทุกวิธีใช้เงินจนหมด หากต้องเลือกขนาดให้ primary B0/B1/B2/B3/B4-RG/P พร้อม B4-DR เป็น diagnostic variant ก่อนเพิ่ม memory หรือหลาย agent

Ablations: ตัด links, ตัด gap retrieval และตัด version tracking Static-memory secondary experiment ต้อง dev-only feedback และ freeze ก่อน test พร้อม same-feedback-in-prompt comparator; longitudinal online adaptation เป็นอีก track ใช้เฉพาะ chronological past confirmed feedback ตาม frozen schedule ด้านล่าง แบบจำลอง GCJR ที่ใช้ paired clean replacements เป็น oracle diagnostic ไม่ใช่ autonomous repair baseline

## Metric definitions ที่ต้อง freeze ก่อน test

กำหนด field IDs ที่คงที่และตรวจ normalization ก่อนเปรียบเทียบ ให้ A = fields ที่ oracle กำหนดว่าต้องแก้, U = fields ที่ต้องรักษา, C = fields ที่ระบบแก้ และ K = affected fields ที่ผลหลังแก้ตรง allowed states เก็บ TP/FP/FN ดิบต่อ episode ด้วย

| Metric | นิยามก่อนรวมผล |
|---|---|
| Required-update recall | จำนวน K / จำนวน A |
| Required-update precision | จำนวน correct required edits / จำนวน C; การแก้ presentation ที่ contract อนุญาตแยกออก |
| Unchanged-field preservation | จำนวน U ที่ยังตรงเดิม / จำนวน U |
| Unnecessary-change rate | จำนวน U ที่เปลี่ยนโดยไม่มีเหตุอนุญาต / จำนวน U |
| Residual violation rate | failed explicit checks / applicable explicit checks หลัง revision |
| Source integrity | resolvable allowed source IDs + matching locator/hash/quote / required provenance links รายงานย่อยแต่ละชนิด |
| Obsolete-source reuse | links ที่อ้าง revoked/superseded source ใน derived current fields / current links ที่ตรวจได้ |
| Conflict reporting/unknown handling | ช่องที่ตรง controlled allowed states / ช่องที่ oracle ประเมินได้ แยก conflict และ missingness |
| Valid structured handoff | binary: schema เหมาะสมและ deterministic checks ที่ applicable ผ่านทั้งหมด ไม่ใช่ clinical validity |
| Cost per valid revision | total cost ของทุก attempted revisions รวม failed attempts / จำนวน valid revisions; ถ้าไม่มี valid ให้ undefined และรายงาน total cost/failures |

ถ้า denominator เป็นศูนย์ ให้ NA และรายงาน eligible counts ไม่แทนเป็น 100% เงียบ ๆ No-op cases ให้แยก preservation และ violation ไม่ตีความ recall ที่ NA เป็นความสำเร็จ หากไม่มี attempted edits ทั้งที่ต้องแก้ ให้ recall = 0 และ precision = NA

รายงาน macro per base group เป็นหลัก พร้อม per-operator counts ห้ามทำ variants จำนวนมากให้กลุ่มหนึ่งมีน้ำหนักเหนือกลุ่มอื่น Candidate-pool known-link recall และ final DAPFAM Recall@k/nDCG@k รายงานแยก ไม่เรียก exhaustive patent recall

LLM/NLI semantic support score เป็น exploratory proxy เท่านั้น Exact quote match พิสูจน์ได้ว่ามีข้อความนั้น แต่ไม่พิสูจน์ entailment, feasibility, novelty, FTO, clinical safety หรือ commercial utility

## Splits, สถิติ และ logs

Split source family/base scenario ก่อนสร้าง variants กัน near-duplicates และ shared sources ข้าม split เมื่อทำได้ หาก groups แชร์ family ให้ระบุ connected components สำหรับ resampling Freeze dev/validation/final test, task generator, prompts, memory, metrics และ budget ก่อนดู final outputs

ใช้ paired differences ระหว่างวิธีบน groups เดียวกัน และ clustered bootstrap CI ตาม brief/family component แสดง seeds/variance และ failure examples กำหนด primary comparisons กับ multiple-comparison handling ก่อนรัน ห้ามเลือก test ที่ให้ผลชนะแล้วรายงานเป็น preplanned

Log ต้องมี task/source hashes, versions, public family mapping, visible inputs, retrieved passages, raw structured outputs, tool calls, errors/timeouts, validator results, tokens, wall time, model/runtime versions และ costs แยก fixed indexing/setup, marginal revision, repair/retry/validation overhead ห้ามตัด failed runs ออกจาก cost ledger

## Natural cases และเกณฑ์หยุด

แยก 5–10 natural briefs ไว้จากการจูน prompts ให้ผู้วิจัยเภสัชกรทบทวนเอง เก็บ corrections, สิ่งที่ใช้ต่อไม่ได้, เวลาของตน และความครบของ artifact เป็น descriptive formative cases ไม่มี expert consensus หรือ inter-rater reliability การตรวจซ้ำของคนเดิมหลังเว้นเวลาเรียก intra-rater stability ได้เมื่อวัดจริงเท่านั้น

หยุดขยายเมื่อ P ไม่คุ้มกว่า rules/direct revision, ชนะจากการไม่ตรวจ, ต้องใช้ oracle graph หรือโจทย์ส่วนใหญ่ต้องอาศัย interpretation ที่ไม่มีผู้เชี่ยวชาญยืนยัน หาก rules ทำได้หมด ให้ใช้ผลนั้นออกแบบผลิตภัณฑ์อย่างเรียบง่ายและจำกัด claim ไม่เพิ่มความซับซ้อนเพื่อให้ได้ชื่อ agent

เอกสารนี้อิงแนว behavioral testing ของ [CheckList](https://aclanthology.org/2020.acl-main.442/), [metamorphic testing](https://arxiv.org/abs/2511.02108), [LLMORPH](https://arxiv.org/abs/2603.23611) และแยก citation quality ตาม [ALCE](https://aclanthology.org/2023.emnlp-main.398/) การประยุกต์และเกณฑ์ข้างต้นเป็นข้อเสนอของโครงการ ยังไม่ได้ reproduce งานเหล่านี้


## อัปเดต first case และการแยก extraction/search

[PTP-0001](cases/PTP-0001/README.md) เป็นหนึ่ง development case ที่เตรียมแล้ว ไม่ใช่ผลรันระบบ Track A แจก checked facts เท่ากันทุกวิธีและคาดว่า rules ทำได้ครบ ใช้แยก bookkeeping เท่านั้น Track B ให้ raw current passages ไม่มี tuples/hidden dependency graph ให้ทุกวิธีใช้ extraction budget และ deterministic evaluator เดียวกัน รายงาน role/witness extraction แยกจาก update consistency

อย่ารวม fixed-source repair กับ adaptive-search track: track หลังต้องเพิ่ม verified distractors/recoverable evidence ที่อยู่นอก initial retrieved subset โดยให้ทุกวิธีเข้าถึง pool/งบเดียวกัน ยังไม่สร้างหรือรันใน case แรกนี้ การมี full source archive ใน repo ไม่ใช่ permission ให้ evaluated system อ่าน oracle/withdrawn evidence เมื่อทำ runner จริงต้อง stage เฉพาะ public current packet ในพื้นที่แยก

## Planned extension: longitudinal organization adaptation

ก่อนรัน track นี้ให้ freeze protocol extension ตาม GOAL G06/G12/G13 ไม่อ้างว่าระเบียบนี้เคยใช้กับ existing case checks แล้ว Proposed pilot=10 development cases/3 fictional organization profiles; main sample size ขึ้นกับ pilot coverage/variance/budget ไม่รับรอง power

- แยก scores ของ retrieval/extraction, explicit organization fit, within-case revision และ cumulative learning ไม่เอา quote match เป็น entailment หรือ plan feasibility
- Split source family/base brief/scenario template ก่อน variants; held-out organizations จำเป็นเฉพาะ cross-org claim Reset memory ระหว่าง independent orgs ให้สะสมได้เฉพาะ within-org chronological learning track
- Freeze global prompts/rules/task contracts, feedback schedule, metrics และ budget ก่อน test Memory เปลี่ยนได้เฉพาะ confirmed past feedback ตาม schedule ไม่เปิด future feedback, hidden expected answers หรือ evaluator graph
- เปรียบเทียบ memory off, same-feedback-in-prompt, scoped persistent memory และ rollback/contradictory-feedback challenge ให้ feedback/information budget เท่ากัน รวม summarization/retrieval/repair/failed-call costs
- วิเคราะห์ paired differences ตาม base groups และ uncertainty ที่ account for family/brief/organization/sequence เมื่อองค์กรน้อยรายงาน descriptive limits ไม่อ้าง variants เป็น independent samples

Agent implementation/debug/testing อยู่ภายใน approved work package; one scoped review แล้ว affectedfix/retest ไม่ต้องรัน benchmark เดิมจาก prose edit/เริ่ม session ใหม่ Owner review formative และไม่มี independent gold ไม่บล็อก technical evidence checks ข้อ clinical/regulatory/legal validation อยู่นอก claims ไม่เป็น acceptance gate ของ runner
