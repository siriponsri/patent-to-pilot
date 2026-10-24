# G02 — Claim/evidence map v1

24 ตุลาคม 2026 · **PLANNING FREEZE / NO EMPIRICAL PTP CLAIMS** · scope `research/patent-to-pilot`

รวม material update จาก SkillOpt และ HarnessOpt-Bench ที่เจ้าของส่งเพิ่มไว้ใน S13/S14 และ C08 แล้ว ไม่เปิด general search ต่อ

Freeze เฉพาะคำถาม กลไกที่เสนอ ขอบเขตข้ออ้างและสิ่งที่จะหักล้างสำหรับ implementation รุ่นแรก ยังไม่ใช่ preregistered final experiment, sample-size justification หรือหลักฐาน effectiveness หน้า/sections อ้างจาก local PDF versions ใน [source coverage](../research/G02_SOURCE_COVERAGE.md) ไม่ใช้ชื่อ framework เป็นหลักฐานเอง

Repository note: the cited local PDFs are workspace-only and are not published here; use the official citation/download links in [G02 source coverage](../research/G02_SOURCE_COVERAGE.md).

G01 documentation เป็น input; ไม่แก้ G01/G04, datasets หรือ shared memory ใน G02 รอบนี้ [Gap freeze](../research/G02_RESEARCH_GAP_FREEZE.md) เป็น research revision/addendum ของ [matrix เดิม](../RESEARCH_GAP_MATRIX.md) โดยเก็บไฟล์ shared เดิมไว้เพื่อไม่ชน Luna

## กติกาการอ่านตาราง

- `SOURCE_REPORTED`: สิ่งที่แหล่งต้นฉบับกล่าว ไม่ใช่ผล reproduce ของเรา
- `OWNER_PRODUCT_GOAL`: จุดหมายผลิตภัณฑ์ ไม่ใช่ novelty/performance claim
- `HYPOTHESIS`: ต้องมีการทดลองที่กำหนดไว้ก่อนจึงอ้างได้
- `UNRESOLVED_GAP`: ขอบเขตที่ยังไม่ตอบจาก selected sections ไม่ใช่การพิสูจน์ absence ทั่วโลก
- `EXCLUDED_CLAIM`: ไม่ใช้เป็นข้ออ้างจากงานปัจจุบัน

## Candidate claims และการหักล้าง

| ID / สถานะ | ข้ออ้างที่อนุญาตให้ตั้งเป็นโจทย์ | Closest collision และ source locator | ขอบเขต / evidence ที่ต้องมี | Test / falsifier |
|---|---|---|---|---|
| C01 OWNER_PRODUCT_GOAL | รวม org understanding → patent/research opportunities → route comparison → draft pilot/handoff และ adaptation เป็น workspace ที่ใช้ต่อได้ | [PatExpert S02](../research/G02_SOURCE_COVERAGE.md#s02-patexpert), §2 PDF pp.3–5 มี patent orchestration, DAG, critique และ hypothesis generation อยู่แล้ว | Integration/product slice เป็น deliverable ไม่อ้าง patent agent/hypothesis generation ตัวแรก ต้องมี artifact ที่เชื่อมกันและใช้ known evidence ไม่ตอบ unknown ทั้งหมด | T-P: authored then implemented E2E journey แยกจาก empirical utility; ถ้าส่งได้แต่ prose/unknown ไม่ครบ useful slice ให้ปรับ product ไม่ใช้ชื่อ integration เป็น performance result |
| C02 HYPOTHESIS — within-project revision | P อาจลด residual explicit violations หรือ revision cost พร้อมรักษา unaffected fields หลัง change | [S01 WPI](../research/G02_SOURCE_COVERAGE.md#s01-oltra-garcia-2018) §§4–5/S31–S32: adaptive search; [S07 ESCROW](../research/G02_SOURCE_COVERAGE.md#s07-escrow) §§3.3–3.6 PDF pp.4–6: scoped updates/non-regression/cost; [S08 GCJR](../research/G02_SOURCE_COVERAGE.md#s08-gcjr) §II PDF p.2: graph-constrained replay | ผลเฉพาะ explicit contract/allowed sources/declared change domain ไม่อ้าง global minimal repair หรือ semantic feasibility Graph ต้องสร้างจาก observable inputs | T-R: rules+same extraction, deterministic invalidation+same generator, full regeneration, direct revision และ adaptive search+ordinary revision; ถ้า P ไม่ได้ cost–correctness benefit หรืออาศัย gold graph/clean replacements ให้ลด method claim |
| C03 HYPOTHESIS — primary learning question | เมื่อได้รับ confirmed corrections ในงานก่อนหน้า ความจำเฉพาะองค์กรอาจลดข้อผิดพลาดใน fresh family-disjoint projects เหนือการให้ corrections ชุดเดียวกันตรง ๆ | [S03 ACE](../research/G02_SOURCE_COVERAGE.md#s03-ace) §§3–3.2,4.1–4.2 PDF pp.4–6: evolving playbooks/ICL; [S06 PolicyBank](../research/G02_SOURCE_COVERAGE.md#s06-policybank) §§4–6.1 PDF pp.5–8: developer feedback→policy memory→sister tasks; [S05 AFTER](../research/G02_SOURCE_COVERAGE.md#s05-after) §§2.3–3.2 PDF p.4: transfer/versioned skills; [S13 SkillOpt](../research/G02_SOURCE_COVERAGE.md#s13-skillopt) §3 PDF pp.4–6: trajectory-driven validated skills | Learning across tasks ไม่ใช่แค่ repair เคสเดิม หรือการมีข้อมูลมากกว่า control ขอบเขตใหม่ที่เสนอคือ patent/project transfer, source fidelity, organization isolation และ equal-feedback cost accounting; ยังไม่พิสูจน์ novelty | T-L: no memory, exact same-feedback-in-prompt, retrieval-only correction memory, ACE-style playbook, scoped structured memory; ถ้าไม่ดีกว่า direct feedback ตาม prespecified trade-off ให้คง useful product แต่ไม่อ้าง stronger learning method; evidence ไม่พอให้ inconclusive ไม่ใช่ equivalence |
| C04 HYPOTHESIS / guard property | versioned scope/feedback handling อาจลด wrong-organization/stale-policy use และรองรับ rollback | [S04 ShareMem](../research/G02_SOURCE_COVERAGE.md#s04-sharemem) §§3.1–3.3 PDF pp.3–4 แยก reusable experience กับ user-bound preferences; [S07 ESCROW](../research/G02_SOURCE_COVERAGE.md#s07-escrow) §3.5 PDF p.5 มี cross-cycle regression history | scope separation/rollback ไม่ใช่สิ่งใหม่ในตัวเอง ข้อเสนอคือทดสอบการใช้กับ explicit organization facts/policies/source versions ไม่แชร์ organization preferences โดยปริยาย | T-L challenge + scope/version ablations และ deterministic scope filter baseline; ถ้า memory เพิ่ม wrong-org errors/ยึด revoked declarations ต้องแก้ guard และห้ามอ้าง reliable transfer |
| C05 HYPOTHESIS / evaluation boundary | source/role/version checks และ controlled unknown rules อาจช่วยคง evidence accountability โดยไม่ทำให้ทั้ง pack หยุดเพราะช่องเดียว | [S11 ALCE](../research/G02_SOURCE_COVERAGE.md#s11-alce) §3 PDF pp.3–4 แยก correctness/citation quality ใช้ NLI proxy; [S12 CheckList](../research/G02_SOURCE_COVERAGE.md#s12-checklist) §2.2 PDF p.3 มี behavioral relations | ตรวจ resolvability, quote/locator, component role ที่ตรวจชัด, allowed-state handling แยก semantic support ทุกชั้นมี known-positive coverage ป้องกัน all-unknown shortcut | T-R/T-L: false-unknown on explicit supported fields, unsupported assertion, revoked-source reuse, conflict/missingness; ถ้าผ่านด้วย unknown ทั้งหมดหรือ exact quote แต่สรุปเกิน span ไม่ผ่าน artifact/evidence objective |
| C06 UNRESOLVED_GAP / candidate artifact contribution | ชุดงาน constructed patent–organization ที่แยก extraction/org fit/revision/learning พร้อม provenance อาจมีคุณค่าเป็น benchmark/artifact | [S02 PatExpert](../research/G02_SOURCE_COVERAGE.md#s02-patexpert) §3 PDF pp.5–6, [S05 AFTER](../research/G02_SOURCE_COVERAGE.md#s05-after) §2 PDF pp.2–4 และ enterprise sources ตาม existing reading notes เป็น prior task/evaluation work | การอ่านชุดนี้ยังไม่พบการทดสอบครบแบบที่เรากำหนด ไม่ได้พิสูจน์ว่าไม่มีใครทำ ต้องมี real patent text, explicit constructed profiles, independent base groups และ limits ไม่อ้าง unrelated datasets เป็น validated real pairs | T-B: schema/source witnesses/split leakage controls และ baseline discriminability; ถ้า tasks มีแต่ trivial rules หรือ oracle อาศัย interpretation ที่ไม่มีผู้ตรวจ ให้ลด/ปรับ benchmark ไม่แต่ง gold |
| C07 HYPOTHESIS / formative utility | workspace อาจช่วยให้เจ้าของจัดงานและตรวจสิ่งที่เปลี่ยนได้สะดวกขึ้น | [S01](../research/G02_SOURCE_COVERAGE.md#s01-oltra-garcia-2018) S31–S32 กล่าวถึง search efficiency แบบ practitioner guidance ไม่ให้ quantified causal effect ของเรา; [G01 contract](PRODUCT_CONTRACT.md) เป็น product specification | owner correction count/time และ artifact usefulness เป็น descriptive/formative เท่านั้น ไม่ใช่ RA/clinician population saving หรือ R&D success | T-P/natural cases แยก primary scores; ถ้า pack ใช้ต่อไม่ได้ให้รายงาน ไม่ซ่อน ถ้าต้องแก้เท่าเดิมยังอาจมี portfolio value แต่ไม่อ้าง proven benefit |

| C08 HYPOTHESIS / existing optimizer as building block | การเพิ่ม explicit org/source/version safeguards ให้ existing optimization method อาจเพิ่ม domain accountability บน patent-project tasks | [S13 SkillOpt](../research/G02_SOURCE_COVERAGE.md#s13-skillopt) §§3–4/PDF pp.4–6,12–15; [S14 HarnessOpt-Bench](../research/G02_SOURCE_COVERAGE.md#s14-harnessopt-bench) §3.1/PDF p.5: feasible harness space includes memory/tools/prompts/control flow | ไม่อ้าง general text/harness optimizer ใหม่ หรือแยกงานเราเพียง memory-vs-code ต้องเปรียบเทียบ existing method/adapter ภายใต้ allowed edits และ evaluation feedback budget เท่ากัน | T-O matched-optimizer cohort: SkillOpt-style base vs same base+org/source safeguards; ถ้า base ทำได้พอแล้วใช้ base และลด method claim ถ้า gain มาจาก extra validator feedback/compute/permission ถือว่าเทียบไม่เป็นธรรม |

## Excluded claims

| ID | ไม่อ้าง | เหตุผล/ขอบเขตที่ใช้แทน |
|---|---|---|
| X01 | first adaptive patent search / first organization-aware memory / first graph repair / first no-gold testing | S01–S08/S12 เป็น prior work โดยตรง; ชุดอ่านไม่เป็น worldwide novelty clearance |
| X02 | quote match/citation linkage ยืนยัน entailment, efficacy, safety, manufacturing feasibility, compliance, FTO หรือ patentability | S11 แยก citation quality จาก correctness; source assertion ไม่ใช่ independent domain truth ของแผน |
| X03 | owner pharmacist หรือ LLM/NLI เป็น independent clinical/legal gold | ไม่มี independent panel; ใช้ literal/source checks กับ explicit stipulations และแยก expert-dependent interpretation |
| X04 | PTP-0001 checks เป็น model results หรือ scientific validation | เป็นหนึ่ง development source unit กับ authored fixtures ไม่ใช่ multiple independent experiments |
| X05 | Paper53 เป็น published/accepted external evidence หรือผล PTP ใหม่ | [internal ledger](../../literature-review/internal/PROVENANCE.md) ระบุ internal only/reuse pending; ไม่เพิ่มใน external bibliographyหรือใช้ old aggregates เป็น fresh result |
| X07 | HarnessOpt เป็นของ Microsoft หรือ harness optimization ไม่ครอบคลุม memory | S14 first page ระบุ Scale AI และ §3.1 รวม memory ใน feasible harness space; S13 มี Microsoft/มหาวิทยาลัยร่วมวิจัย เป็นคนละงาน |
| X06 | synthetic enterprise data + patent benchmark คือ validated real organization–patent pairs | เป็น separate tracks และ declared constructed scenarios ไม่มี capability gold ที่เกิดจากการนำสองชุดมาต่อกัน |

## Baseline obligations: ใช้เท่าที่ตอบ claim ไม่เพิ่มทุกระบบโดยอัตโนมัติ

1. C02 ต้องมี deterministic rules+same extraction และ invalidation+same generator เป็น strong simple comparators รวม adaptive-search+ordinary revision ตาม S01 ไม่ใช้ static-only comparison
2. C03 ต้องมี **exact same corrections directly in prompt** ที่ใส่ได้ครบ ไม่ใช่ control ที่ถูกตัด context และมี no-memory control ถ้าอ้าง memory organization/selection ให้มี retrieval-only memory ด้วย
3. SkillOpt-style adapter เป็น closest existing optimization comparator/building block ไม่สร้าง generic optimizer แข่งเพื่อชื่อ novelty; ACE-style playbook เป็น secondary เมื่อกลไก/งบทำให้จำเป็น ถ้าอ้าง policy-interpretation learning ใหม่ให้มี PolicyBank-style adaptation หรือจำกัด claim ทุกแบบระบุ inspired/adapted ไม่เรียก reproduction จนรันจริง
4. C04 แยก explicit scope/version guards จาก LLM memory writing เพื่อไม่เอาประโยชน์ของ simple rules มาอ้างเป็น agent novelty
5. แยก fixed-feedback curve จาก matched-optimizer cohort ถ้ามีการ query selection scores/extra scored rollouts ต้องให้คู่แข่งมีโอกาสและเพดานเท่ากันและ log disclosure ไม่เรียกว่าข้อมูลทั้งหมดมีแค่ K corrections ทั้งที่มี feedback เพิ่มจาก verifier
6. นับ construction/reflection/retrieval/validation/retries/failures และ latency ทั้ง fixed setup กับ marginal task cost ใช้ model/tools/corpus/output format/validators และ ceilings เดียวกัน

## G02 closure

ทุก candidate claim C01–C08 มี source collision, boundary และ test/falsifier แล้ว ไม่มี PTP empirical claim ผ่านจากตารางนี้โดยอัตโนมัติ สิ่งที่ freeze คือ framing v1 สำหรับทำงานต่อ ส่วน final sample sizes/models/prices/statistical margins/protocol ต้อง calibrate และ freeze ใน goals ที่เกี่ยวข้องภายหลัง ดู [handoff](../research/G02_HANDOFF.md) ไม่มี owner decision ใหม่ที่ต้องรอเพื่อปิด G02
