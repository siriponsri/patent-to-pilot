# Long GOAL — G10 correctness, search readiness และ scoped repository delivery

โครงการ: C:\Users\User\Desktop\myProject\patent-to-pilot
ประเภท prompt: **GOAL**
ผู้ลงมือด้าน correctness/search และ Git delivery: Luna; ผู้รับผิดชอบ README/branding/diagrams และ audit: Pepo
สถานะเอกสาร: คำสั่งสำหรับงานถัดไป ยังไม่ได้ดำเนินการตามเอกสารนี้

## 1. เป้าหมายและวิธีเริ่มงาน

ใช้เอกสารนี้เป็น Long GOAL สำหรับปิดข้อบกพร่องของ bounded G10 comparison ให้ผลตรวจและ accounting ตรงกับสิ่งที่ระบบทำจริง แล้วเตรียม shared search pool และ B4 comparators เฉพาะส่วนที่มีหลักฐานพร้อม

เจ้าของเป็นผู้เลือก GPT 5.6 Luna Max ใน UI เอง หากชื่อหรือโหมดไม่พร้อม ให้แจ้งตามจริง ไม่สร้าง model alias หรือสลับ OpenRouter model เพื่อให้ดูเหมือนใช้ executor ที่เลือกแล้ว ชื่อ executor กับ model IDs ที่ผลิตภัณฑ์ใช้เป็นคนละเรื่อง

รอบนี้เป็น **offline engineering และ repository documentation work: 0 provider/model inference calls / USD 0** ไม่ทำ UI งาน UI ยังเป็นของ Claude และไม่เปิด scientific pilot หรือ G12 learning การเชื่อมต่อ Git เพื่อ scoped push และการอ่าน CI ของ exact commit อนุญาตเฉพาะ W11 ไม่ใช่สิทธิ์เรียก product/provider API

เมื่อเริ่ม ให้ทำดังนี้:

1. อ่าน AGENTS.md และเอกสารอ้างอิงเฉพาะที่จำเป็นในส่วนท้าย
2. ตรวจ candidate ปัจจุบันเทียบกับ audit snapshot แยกการเปลี่ยนที่เกิดหลัง audit ออกจาก defect เดิม
3. ลงมือ W1–W11 ภายในขอบเขต ไม่เสนอแผนแล้วหยุดทั้งที่งาน offline พร้อมทำ
4. หากงานย่อยติดสิทธิ์หรือจำเป็นต้องแก้ protected code ให้หยุดเฉพาะส่วนนั้น เสนอ diff และเหตุผล แล้วทำส่วนอิสระที่เหลือต่อ
5. ปิด W1–W11 แล้วส่ง READY_FOR_PEPO_AUDIT พร้อมหลักฐานและ commit/push/CI status ตามจริง หาก publication gate ติด ให้รายงาน PUBLISH_BLOCKED โดยไม่ขยายสิทธิ์หรือเปิด audit/repair loop แบบไม่มีขอบเขต

คำสั่ง owner และ runtime permissions มีอำนาจเหนือเอกสารนี้ เอกสารไม่ยกเลิก access denial และไม่ให้สิทธิ์เพิ่ม workload หรือเปลี่ยน security policy เอง

## 2. ฐาน audit ที่ต้องใช้

### 2.1 สิ่งที่ตรวจยืนยันแล้ว

Pepo ตรวจ source และ saved artifacts แบบ read-only โดยไม่รัน comparison runner หรือ tests เพิ่ม พบว่า:

- Output artifacts ทั้งหกไฟล์ตรงกับ evidence-manifest.json
- Hashes ของ historical Phase A และ fresh paired journal/receipt/marker ยังตรงกับ closeout ก่อนหน้า
- มี mock-call records 9 รายการ: B1, B2, B3 อย่างละ 3
- Mock cost เป็น 0 ตาม implementation ไม่ใช่ measured inference cost
- พบ test functions 37 ตัวจากสามไฟล์: comparison 6, G09/G10 integration 25 และ G11 adaptation 6
- จำนวน tests ที่ Pepo รันอิสระใน audit นี้คือ **0** จึงยังไม่ได้รับรอง “37 passed” ด้วยการรันทวน
- network_calls=0 เป็นค่าที่โค้ดใส่ใน report เส้นทางปกติไม่มี HTTP transport แต่ audit ไม่ได้วัด network activity
- ไม่พบการอ่าน evaluator-only gold archive ในเส้นทางที่ตรวจ แต่ P wrapper โหลด public states เกิน staged slice
- Readiness notes แก้ test counts เป็น 107/10 และยอมรับ NO_ADVANTAGE/INCONCLUSIVE แล้ว ไม่กลับไปตั้งเงื่อนไขว่าต้องชนะ baseline เพื่อให้ pilot ผ่าน

Audit ไม่ได้ยืนยัน protected-file diff ทั้ง repository เพราะ manifest ของ G10 ผูกกับ outputs แต่ยังไม่ผูก source candidate และ protected baselines ครบ ห้ามขยายคำว่า “hashes match” เป็น “ทั้ง repo ไม่เปลี่ยน”

### 2.2 Snapshot ของ source ที่ audit

| ไฟล์ | SHA256 ณ audit |
|---|---|
| src/patent_to_pilot/evaluation/comparison.py | 70709aea19e6173105f56dfabaccf40c62f00dad68c01e5c4b6ea273a7bb37d1 |
| scripts/run_g10_offline_comparison.py | 980450d91227f8d6a456162c3ddf517ce11501d874e5d8c6f045ded909b37abf |
| tests/test_g10_offline_comparison.py | d7f77607e7418cdf2f9b8f307125a1b352873d88c274e464597a195af4b92149 |

Line locators ในส่วนถัดไปอ้างอิง snapshot นี้ หากมีการเพิ่มบรรทัด ให้ตามชื่อ function และบันทึกตำแหน่งใหม่ ไม่ย้ายหรือแก้ code ให้ตรงเลขบรรทัดเก่า

### 2.3 ประวัติ paid ที่ต้องคงไว้

- Historical Phase A: 2 attempts, PHASE_FAILED, API-reported debit USD 0.0000732
- Fresh pair ก่อนงานนี้: 2 attempts, PAIR_COMPLETE, pair debit USD 0.0000732
- Cumulative debit ตาม closeout เดิม: USD 0.0001464
- ไม่มีการอนุมัติ calls เพิ่มใน GOAL นี้ ยอดเติม OpenRouter USD 10 ไม่ใช่ spending authority
- ห้ามรัน Phase A, Gemini-only recovery หรือ pair เดิมซ้ำ และห้ามนำ journal เก่ามาใช้บันทึก mock runs

หลักฐาน paid เดิมเป็น read-only อย่า reset, reconcile, relabel หรือเขียนทับเพื่อให้เอกสารรอบใหม่ดูผ่าน

## 3. Findings ที่ต้องปิด: F1–F4

### F1 — P wrapper ทำงานเกิน staged slice

[comparison.py:568](../../src/patent_to_pilot/evaluation/comparison.py#L568) เรียก run_case(case_id) ซึ่ง [pipeline.py:906](../../src/patent_to_pilot/integration/pipeline.py#L906) โหลด S*.json ทั้งหมด แล้ว wrapper จึงเลือกผล S0–S2

Artifact ระบุ full_case_state_count=5 แต่ comparison ระบุ staged states เพียง 3 ทำให้ method P ทำงานบนขอบเขต input และ elapsed time ต่างจากวิธีอื่น การติด staged hash ลง output ไม่ได้พิสูจน์ว่า method ใช้เฉพาะ staged input

นี่เป็น fairness/scope defect ไม่ใช่หลักฐานว่ามี hidden gold leakage เกิดขึ้นแล้ว

### F2 — Declared output schema ไม่ได้ถูกบังคับตรวจ

[comparison.py:345](../../src/patent_to_pilot/evaluation/comparison.py#L345) รายงาน schema version/hash/availability แต่ไม่ได้ตรวจ output กับ schema ที่ stage ไว้

[Public output schema](../../methodology/evaluation/cases/PTP-0001/public-input/output-schema.json) ประกาศ fields ที่ saved output ไม่มี เช่น:

- Top level: event_id, display_name, source_ambiguity_status, interpretation_limits
- Options: candidate_id, component, selected_material, current_support_ids, historical_support_ids, measured_production_yield, final_needle_material, next_action_code

Schema เดิมมี note ว่าเป็น documentation schema ไม่ใช่ executed product API จึงต้องกำหนด bounded runtime contract หรือ mapping ให้ชัด ไม่อ้างว่า hash ของ documentation schema คือผล output validation

### F3 — SQLite read-back ผ่านจาก default

[comparison.py:332](../../src/patent_to_pilot/evaluation/comparison.py#L332) เรียก DevelopmentEvaluator.evaluate โดยไม่ส่ง actual persistence result จึงได้รับ default sqlite_payload_read_back=True จาก [pipeline.py:310](../../src/patent_to_pilot/integration/pipeline.py#L310)

Saved results แสดง read-back ผ่านสำหรับ B0–B3 ทั้งที่เส้นทางเหล่านั้นเรียก run_state ไม่ได้ทำ persistence round-trip ของตัวเอง

### F4 — Failure metrics นับซ้ำและตกหล่น exception

[comparison.py:430](../../src/patent_to_pilot/evaluation/comparison.py#L430) รวม failed state กับ failed call ทำให้ timeout เดียวถูกนับสองครั้ง

[comparison.py:211](../../src/patent_to_pilot/evaluation/comparison.py#L211) เรียก generate ก่อน append trace ถ้า generator โยน exception ปกติ trace อาจหายและ runner อาจหยุดก่อนออก report

นอกจากนี้ valid_state_count ที่บรรทัด 422 ดู execution status ไม่ได้ดู validator result จึงอาจนับ state ที่ validation fail ว่า valid

## 4. ขอบเขตการแก้

### ขอบเขตเขียนรวมและเจ้าของไฟล์

- Comparison layer ใน src/patent_to_pilot/evaluation/ เท่าที่จำเป็น
- scripts/run_g10_offline_comparison.py และ offline entry points ที่จำเป็นต่อ slice
- Associated comparison tests และ additive test fixtures
- เอกสาร closeout, schema/method contracts และ manifests ที่จำเป็น
- README.md และ docs/assets/patent-to-pilot/ อยู่ใน eventual scope ของ Pepo เท่านั้น จนกว่าจะส่ง handoff ตาม W10
- Evidence ของ run ใหม่ใน directory ใหม่ ห้ามเขียนทับ results/development/g10-offline-comparison/ ชุดที่ audit แล้ว

ใช้โครงสร้างและ dependencies เดิมก่อน ไม่สร้าง framework ใหม่เพียงเพื่อแยกหลาย methods

**การแบ่งงานล่าสุด:** Pepo เป็น writer ของ README.md และ docs/assets/patent-to-pilot/ ซึ่งสงวนไว้สำหรับ original SVG logo, workflow/architecture diagrams และ accessible text/source ที่เกี่ยวข้อง Luna ไม่เขียนหรือ rewrite พื้นที่นี้ระหว่างงานของ Pepo ให้ส่ง factual correction พร้อม source/evidence ให้ Pepo แล้วรับ handoff ก่อนรวม publication งานอื่นของ Luna เดินต่อได้ ไม่ต้องรอเอกสารหากไม่มี dependency

### ต้องรักษาเป็น read-only

- src/patent_to_pilot/integration/ และ accepted G09/G10 baseline behavior
- src/patent_to_pilot/adaptation/ ของ G11
- Frozen evaluation files ใน methodology/evaluation/ รวม schema, expected outputs, oracles, public case states, splits และ protocol
- docs/research/pilot-next/
- Historical paid journals, markers, approvals และ result snapshots
- Accepted core, ingestion, retrieval และ extraction modules ที่ไม่อยู่ใน comparison diff
- Unrelated files และงานของ Claude

หากการปิด finding จำเป็นต้องเปลี่ยน protected code ให้ส่ง proposed diff พร้อมเหตุผลและ impact หยุด affected subgoal ไว้ก่อน ห้ามขยายสิทธิ์เอง ส่วนที่ไม่พึ่ง diff นั้นให้เดินต่อ

### สิ่งที่ห้ามทำ

ไม่มี product/provider/model API calls, key/.env reads, GPU/RunPod, credential setup, ACL changes, denied-file reads, journal resets, deploy หรือ UI implementation

**Owner authorization ล่าสุด:** อนุญาตให้ Luna commit และ push เฉพาะ completed scoped changes รวม README/assets ที่ Pepo ส่งมอบแล้ว หลัง tests, secret scan, source/evidence consistency และ staged diff review ผ่านตาม W11 ไม่ต้องขออนุมัติซ้ำแบบกว้างเมื่อ destination และ publication scope ชัดเจน หาก remote/destination หรือ publication sensitivity ยังไม่ชัด ให้ถามเฉพาะจุดก่อน push การอนุญาตนี้ไม่รวม repo creation, visibility change, force-push, merge หรือ deploy และไม่ให้ทำ commit/push ระหว่าง drafting turn นี้

ห้ามแก้ frozen facts/schema/checkers เพื่อทำให้ outputs ผ่าน ห้ามลด tests, เพิ่ม skip, เปลี่ยน expected facts หรือใช้ default PASS แทน actual assertions

## 5. W1 — ล็อก source, provenance และ candidate

1. อ่าน G10 handoff, source, tests และ existing output manifest ก่อนเปลี่ยนไฟล์
2. ตรวจ SHA256 ของ source snapshot ในส่วน 2 และระบุสิ่งที่เปลี่ยนหลัง audit หากมี ห้าม overwrite concurrent edits
3. บันทึก current candidate revision ตามที่ตรวจได้ หาก Git ownership/access ปฏิเสธ ให้รายงาน Git metadata BLOCKED ไม่ตั้ง safe.directory หรืออ่านผ่านทางอื่นเพื่อหลบข้อจำกัด
4. ทำ manifest ของไฟล์ที่จะเปลี่ยนและ dependencies ที่ใช้ประเมินผล เช่น IntegrationResult, DevelopmentEvaluator, adapter และ schema versions
5. แยก source hashes, input/schema hashes, output hashes และ test execution evidence ไม่รวมทั้งหมดเป็นคำว่า verified
6. กำหนด run ID และ output directory ใหม่ก่อนรัน ไม่ใช้ directory ชุดที่ audit เป็น scratch space

**Drafting checkpoint:** read-only Git probe ถูกปฏิเสธด้วย exit 128 / dubious ownership เพราะ repo เป็นของ User แต่ process เป็น CodexSandboxOffline จึงยังไม่ได้ยืนยัน current remote, branch หรือ upstream ใน drafting turn นี้ ไม่มีการเปลี่ยน safe.directory หรืออ่าน Git config ผ่านทางอื่น ให้ W11 ตรวจจากบริบทที่ได้รับอนุญาตตาม repo guidance ก่อนใช้ remote ใด ๆ และอย่าเดาจากชื่อ project

**Acceptance**

- Candidate อ้างกลับได้ถึง source/files ที่ตรวจจริง
- Original artifacts และ paid history ไม่เปลี่ยน
- ข้อจำกัดด้าน revision/access ระบุเป็น UNKNOWN/BLOCKED ตามจริง ไม่เดา clean tree หรือ remote state

## 6. W2 — Staged-input fairness: ปิด F1

**W2 ในเอกสารนี้หมายถึง input fairness ไม่ใช่ W2 access blocker ของ handoff เก่า** งาน access เก่ายังคง BLOCKED และไม่ใช่ prerequisite ของ GOAL นี้

1. ให้ทุก method รับชุด staged inputs ที่ส่งเข้า runner จริงเท่านั้น รวม profile/version, evidence, policy/event และ previous output ตาม method contract
2. แก้ P wrapper ไม่ให้เรียก full-case loader แล้วค่อยเลือกผล ให้ใช้ composition หรือ adapter ใน comparison layer โดยไม่แก้ accepted integration pipeline
3. รวมข้อมูลที่มีผลต่อผลลัพธ์ใน input contract/hash อย่าผูกแค่ packet แล้วส่ง profile หรือ raw state นอก hash โดยไม่บันทึก
4. ให้ generator/mock seam รับ request contract ที่ตรวจได้ ไม่ใช้ hash metadata เป็นหลักฐานแทนการตรวจ actual inputs
5. บันทึก state IDs ที่โหลด/ประมวลผลจริง แยก previous output ที่ method มีสิทธิ์เห็นออกจากข้อมูล future state
6. คงชื่อ P_existing_workflow หรือชื่อ bounded wrapper ที่ตรงความจริง ไม่เปลี่ยนเป็น full dependency-guided P หากยังไม่ได้ implement

**Negative controls ที่ต้องมี**

- Adapter ที่ throw เมื่ออ่าน S3/S4 ต้องไม่ถูกเรียกใน S0–S2 slice
- Custom staged packet ที่ต่างจากไฟล์บน disk ต้องทำให้ผลเปลี่ยนตาม staged packet ไม่ใช่กลับไปใช้ default case
- การเปลี่ยน profile/version หรือ permitted evidence ต้องสะท้อนใน input provenance และผลตาม contract
- ไม่มี expected recovery IDs, gold answers หรือ future events เข้า method request

**Acceptance**

ทุก method ทำงานบน scope ที่ประกาศจริง ไม่มี extra-state generation แฝงใน timing/accounting และมี negative test จับ F1 ได้ ไม่ใช่แค่ทุก method รายงาน hash เดียวกัน

## 7. W3 — Actual bounded output schema: ปิด F2

1. ระบุ common runtime output contract ที่ตรงกับ slice ปัจจุบัน อาจใช้ comparison view ที่ map จาก IntegrationResult หรือ bounded schema ของตัวเอง
2. เขียน field mapping ไปยัง documentation schema เดิม บอก fields ที่รองรับ, fields ที่เป็น explicit unknown และ fields ที่ยังอยู่นอก scope
3. ตรวจ required fields, types, enum/state, option identity และ evidence reference ตาม contract ที่เลือกจริง
4. แยก schema validation ออกจาก evidence/policy validation การมี shape ถูกต้องไม่ทำให้เนื้อหามี support
5. ใช้ schema/validator versions เดียวกันทุก method ไม่ให้ P มี checker หรือ repair พิเศษที่วิธีอื่นไม่ได้
6. เก็บ validation failures พร้อม path/reason อย่างปลอดภัย ไม่เติม missing measurement เป็น 0 หรือแต่ง field เพื่อให้ครบ

ห้ามแก้ frozen public output-schema.json ให้ตรงกับ output ปัจจุบันโดยไม่มี authorization หาก schema เดิมเป็น documentation-only ให้รายงานขอบเขตนั้นและเลือก runtime contract อย่างเปิดเผย

**Negative controls ที่ต้องมี**

- Missing required field
- Invalid type หรือ policy state
- Option/evidence reference ที่ไม่ตรง contract
- Unknown measurement ที่มี numeric value แฝง
- Output shape ถูกแต่ evidence/policy check ผิด

**Acceptance**

Schema hash เป็น provenance เท่านั้น PASS ต้องมาจาก actual validation ของ actual output ทุก state ที่อ้างว่าผ่าน และ malformed output ต้องทำให้ method/aggregate status เปลี่ยนตาม required checks

## 8. W4 — Truthful persistence/read-back: ปิด F3

1. แยก execution, schema validation, domain validation และ persistence status ไม่ใช้ boolean เดียวแทนทุกอย่าง
2. ถ้าจะรายงาน SQLite round-trip PASS ให้บันทึกแล้วอ่านกลับจริง ตรวจ typed payload, ID และ version ตามขอบเขตที่ประกาศ
3. ถ้า persistence ไม่อยู่ในขอบเขตของ method ให้แสดง NOT_RUN หรือ NOT_APPLICABLE พร้อมเหตุผล ไม่ผ่าน default True และไม่รวมเป็น validated success
4. หาก persistence เป็น common evaluator layer ให้ใช้ layer เดียวกันทุก method เพื่อไม่ให้ computation strategy ได้เปรียบจาก checker ที่ต่างกัน
5. ระบุว่าตรวจ in-memory round-trip หรือ durable restart/recovery จริง ห้ามใช้คำว่า durable เมื่อทดสอบเพียง in-memory SQLite
6. อย่าเปลี่ยน default ใน protected evaluator เพื่อให้รายงานใหม่สวย ให้แก้ comparison composition หรือเสนอ protected diff แยกหากจำเป็น

**Negative controls ที่ต้องมี**

- Method ไม่ได้ persist ต้องไม่มี read-back PASS
- Payload/ID/version ที่อ่านกลับไม่ตรง ต้อง FAIL
- Unavailable persistence evidence ต้องคง NOT_RUN/BLOCKED ไม่แปลงเป็น True
- Schema/domain validation ผ่านไม่ได้กลบ read-back failure ที่เป็น required check

**Acceptance**

ทุก persistence claim มี actual evidence หรือ explicit non-applicable status ตัวนับ valid states และ aggregate PASS ไม่ใช้ default ของ evaluator เป็นผลตรวจจริง

## 9. W5 — Failure, accounting และ status semantics: ปิด F4

1. แยก provider/generator calls, failed attempts, failed states และ dependent skips พร้อมนิยาม ไม่บวกซ้ำแล้วเรียกเป็น failure count เดียว
2. ครอบ generator execution ให้บันทึก safe exception trace เมื่อมี ValueError, runtime error หรือ controlled timeout หลังเริ่ม call
3. ระบุการแยก pre-dispatch validation error ออกจาก generator attempt ที่เริ่มแล้ว ไม่สร้าง call ปลอมให้สิ่งที่ยังไม่ได้เรียก
4. คง zero retries การเริ่ม state ถัดไปที่ไม่พึ่ง previous output ต้องอธิบายตาม method contract ส่วน dependent revision ที่ขาด prior state ให้เป็น SKIPPED/BLOCKED อย่างชัดเจน
5. ให้ valid_state_count และ valid_revision_count นับ required validations ที่ผ่านจริง ไม่ใช่แค่ code execution สำเร็จ
6. แสดง actual call records และ aggregate counts ที่คำนวณจาก records ไม่ hardcode PASS หรือเลข calls
7. แยก configured mock cost=0, observed mock call count, Python execution time และ real inference cost อย่าใช้ mock timing/cost อ้าง model savings
8. หาก generation scope เป็น full_then_scoped_merge ให้คง label และนับ full generation ตามจริง No-op preservation ไม่ได้แปลว่าไม่มี computation

**Negative controls ที่ต้องมี**

- Timeout หนึ่ง call ต้องไม่กลายเป็นสอง failed attempts
- Generator exception ต้องมี trace และไม่หายไปก่อน report
- Validator fail ต้องไม่เพิ่ม valid-state count
- Dependent skip ต้องไม่ถูกนับเป็น provider call หรือ retry
- Invalid output และ execution exception ต้องไม่ถูกกลบด้วย state status PASS

**Acceptance**

Counts กระทบยอดได้จาก records, failures เก็บครบ, status ตรงกับ execution/validation และไม่มีการอ้างเงินจริงหรือประสิทธิภาพจาก mock ตัวเลข

## 10. W6 — Offline guards, regressions และ reproducibility

1. รันทดสอบที่เกี่ยวข้องกับ comparison diff และ affected integration/adaptation regressions ภายใต้ fake credentials และ guards ที่ปฏิเสธ network กับ production .env access
2. ใช้ Python -B และปิด pytest cache หากจำเป็นต่อพื้นที่ write ที่อนุญาต ใช้ temp/run directory ใหม่ที่ได้รับสิทธิ์จริง
3. Baseline “37 functions” ไม่ใช่ test-count quota ให้รายงาน actual command, collected/passed/failed/skipped/error counts และ exit code
4. เพิ่ม F1–F4 negative controls ที่กล่าวไว้ ไม่ mirror implementation อย่างเดียวและไม่ลด assertions เพื่อปิดงาน
5. Compile/whitespace checks เฉพาะ changed/affected files ไม่รัน corpus หรือ asset audit ทั้งโครงการ
6. ตรวจ report generation ว่าเขียนลง run ใหม่และไม่ overwrite audit evidence เดิม Resume/replay ต้องไม่ทำ output เก่าดูเหมือนเกิดจาก source ใหม่
7. เก็บ source/input/schema/output manifests, method traces, actual validators/diffs และ JUnit หรือ equivalent execution receipt
8. แยก declared network count ออกจาก observed guard/monitor evidence หากไม่ได้วัด ให้บอกว่ายังไม่วัด ไม่ใช้ค่า 0 คงที่เป็นผล measurement ขอบเขต network guard นี้คือ tests/comparison runner ไม่ใช่คำกล่าวว่าไม่มี Git traffic ในขั้น publication ที่อนุญาต
9. หาก evidence ใหม่อ่านไม่ได้ด้วย account ที่ต้องใช้ตรวจ ให้รายงาน visibility BLOCKED แยกจาก test correctness ไม่คัดลอกหรือสร้างแทน denied preflight เก่าเพื่อเลี่ยงข้อจำกัด

ชุด regression ที่เกี่ยวข้องเดิมมี:

~~~text
tests/test_g10_offline_comparison.py
tests/test_g09_g10_integration.py
tests/test_g11_adaptation.py
~~~

เพิ่มเฉพาะ tests ที่จำเป็นต่อ changes และ shared-pool/search boundaries การอนุญาตให้รันทดสอบไม่ใช่การอนุญาตให้แก้ frozen fixtures หรือ accepted baseline behavior

**Acceptance**

F1–F4 มี positive/negative evidence, output hashes/source bindings ครบ และมี replay instructions ที่ทำซ้ำ engineering slice ได้ ไม่อ้าง scientific reproducibility หรือ test pass จากจำนวน functions เพียงอย่างเดียว

## 11. W7 — Conditional verified shared pool

ทำขั้นนี้หลัง comparison correctness มีฐานที่เชื่อได้ ใช้ข้อมูล public/local เดิมที่ได้รับอนุญาตเท่านั้น ไม่ดาวน์โหลด corpus ใหม่และไม่เรียก API

1. เลือก pool เล็กที่สุดที่มี initial active evidence, recoverable evidence และ distractors ที่ตรวจ source/locator/version ได้
2. แยก source facts ออกจาก authored synthetic development conditions หากมี synthetic examples ต้องติดป้ายชัด ไม่เรียกว่า verified real-world evidence
3. บันทึก source ID, permitted excerpt/locator, hash/version, availability และสิทธิ์การใช้ตาม manifest ที่มี ไม่คัดลอก full source เกินขอบเขตที่ได้รับอนุญาต
4. กำหนด temporal availability ให้ถูกต้อง ห้ามเปิด future evidence ก่อน revision ที่มีสิทธิ์ใช้ หรือเอา future policy มาเลือก pool ล่วงหน้าให้ agent
5. แยก curator/evaluator witness map ออกจาก agent-facing candidate pool ห้าม expected recovery IDs, hidden answer hints หรือ oracle ranking เข้า retrieval/generator input
6. ทุกวิธีต้องได้ visibility และ information/tool budget ตาม protocol เดียวกัน ไม่ให้ P/B4 ได้ source ที่วิธีอื่นไม่มีสิทธิ์เข้าถึง
7. ใช้ additive manifests/test fixtures/run artifacts นอก frozen evaluation tree ไม่แก้ PTP-0001 public states หรือ source witnesses เดิม

**Acceptance แบบมีเงื่อนไข**

- หากตรวจ pool ได้จริง: ส่ง verified pool manifest และ tests สำหรับ distractor/availability/leakage
- หากยังตรวจไม่ได้: รายงาน POOL_NOT_READY พร้อมสิ่งที่ขาด แล้วส่ง W1–W6 ที่จบแล้วต่อได้
- การไม่มี pool ไม่ทำให้ต้อง fabricate data หรือขยาย corpus เพื่อบังคับ package ให้ PASS

## 12. W8 — Conditional B4-RG / B4-DR readiness

B4-RG และ B4-DR ไม่ใช่เงื่อนไขบังคับให้รอบ correctness ต้องรันครบ หาก pool หรือ policy contract ยังไม่พร้อม ให้คง NOT_IMPLEMENTED/NOT_RUN ตามจริง

เมื่อ W7 พร้อม:

1. ให้ B4-RG เลือก what/where/how จาก observable intermediate gaps ภายใน budget ที่ประกาศ บันทึก query/decision/candidate/selected evidence ที่เกิดจริง
2. ห้ามใช้ case-ID lookup, hidden recovery map หรือ expected IDs แทน adaptive search
3. ถ้าเป็น deterministic retrieval-policy prototype หรือ mocked generation seam ให้เรียกตามนั้น ไม่อ้าง full adaptive-search implementation หรือ exact paper reproduction
4. ใช้ pool/schema/validators และสิทธิ์ข้อมูลเท่ากันกับ methods ที่เปรียบเทียบตาม PROTOCOL
5. หากทำ B4-DR diagnostic ให้ใช้ search policy/information budget เดียวกับ B4-RG แล้วแยก direct revision จาก regeneration จริง
6. ไม่เปลี่ยน P_existing_workflow เป็น full P จากการเปลี่ยน label Runtime graph + bounded evidence-gap retrieval ต้องมี implementation/evidence ก่อนอ้าง
7. ไม่มี model-quality หรือ scientific advantage claim จาก mock execution

**Acceptance แบบมีเงื่อนไข**

มี method-readiness matrix ระบุ IMPLEMENTED, MOCK-ONLY, NOT_IMPLEMENTED, BLOCKED และ NOT_RUN พร้อมเหตุผลและหลักฐาน สำหรับ method ที่รันจริงต้องมี trace และ negative checks ส่วนที่ยังไม่พร้อมไม่ถูกนับว่ารันสำเร็จ

## 13. W9 — Closeout และ G13 readiness ส่ง Pepo

1. ออก closeout report หลักหนึ่งฉบับ เช่น docs/handoff/G10_CORRECTNESS_CLOSEOUT.md พร้อม evidence manifest ของ run ใหม่
2. ปิด F1–F4 ทีละข้อด้วย before/after code locator และ actual regression result ห้ามใช้คำว่า fixed โดยไม่มี check ที่จับ defect เดิมได้
3. แสดง scope/input/schema/persistence/accounting table ของทุก method และแยก method implementation จาก wrapper/prototype
4. แสดง original audit artifacts unchanged และ source/input/output hashes ของ candidate ใหม่
5. รายงาน G10 เต็มที่ยังเปิด เช่น B4 readiness หรือ full proposed workflow ไม่อ้าง full G10 จาก bounded smoke
6. อัปเดต readiness note ที่จำเป็นให้ตรง evidence ใหม่ แต่รักษา docs/research/pilot-next/ และ frozen methodology เป็น read-only หากต้องเปลี่ยน protected text ให้เสนอ diff แยก
7. G13 readiness ต้องแยก engineering checks, scientific pilot และ main study พร้อม dependencies, failure/cost drivers และ proposed next matrix แบบ UNAPPROVED/NOT_RUN
8. ผล NO_ADVANTAGE หรือ INCONCLUSIVE ยอมรับได้เมื่อ experimental integrity ผ่าน ไม่ตั้งผลชนะ baseline เป็นเงื่อนไขผ่าน
9. ระบุว่ารอบนี้ไม่มี paid calls, ไม่มี G12 confirmed-feedback learning runtime และไม่มี UI implementation

W9 เตรียม auditable candidate และหลักฐานเพื่อส่งต่อ W10–W11 ยังไม่ใช่จุดจบก่อน Git delivery ที่ owner อนุมัติ Pepo ตรวจหนึ่ง focused pass โดยผูกกับ candidate/source hashes และ final commit เมื่อมีแล้ว หากพบ defect ให้แก้และ retest เฉพาะ affected paths ไม่เปิด broad audit หรือเพิ่ม goals เพื่อเลื่อนจุดจบ

**Acceptance สุดท้าย**

- F1–F4 ปิดด้วย actual negative controls หรือมี proposed protected diff และ BLOCKED ที่ชัดเจน
- ไม่มี PASS จาก defaults, schema hash หรือ test-function count
- ไม่ overwrite old artifacts/history และไม่มี API/key/env/GPU/ACL/denied-file action
- W7/W8 เป็น conditional readiness ไม่บังคับสร้าง pool หรือ B4 ปลอมเพื่อให้ผ่าน
- ส่ง READY_FOR_PEPO_AUDIT หรือ READY_WITH_BLOCKED_SUBGOALS พร้อมขอบเขตที่ยังไม่จบ
- UI, paid study และ deploy ยังอยู่นอกขอบเขต ส่วน commit/push ทำได้เฉพาะ W11 หลัง gates ครบ

## 14. W10 — ประสานและรวม README/branding/diagrams ของ Pepo

**ผู้เขียนส่วนนี้คือ Pepo ไม่ใช่งานให้ Luna rewrite README อีกชุด**

พื้นที่สงวนของ Pepo:

- README.md
- docs/assets/patent-to-pilot/ สำหรับ original SVG logo, workflow/architecture diagrams, Mermaid sources และ accessible text ที่เกี่ยวข้อง

Luna เดิน correctness/search ต่อได้โดยไม่แก้พื้นที่สงวน เมื่อ code/tests/status เปลี่ยน ให้ส่ง factual delta พร้อม source/evidence ให้ Pepo ไม่แก้ทับงานที่กำลังเขียน รอ handoff ที่ระบุไฟล์/hash และ DOCS_READY_FOR_LUNA ก่อนรวมงาน หากหลัง handoff ต้องแก้ข้อเท็จจริง ให้ประสานเป็น change เล็กที่ตกลงกัน ไม่ rewrite หรือเปลี่ยนทิศทางเอกสารเอง

### Deliverables ของ Pepo ที่ Luna ต้องตรวจตอนรับ handoff

1. **Professional English README:** project purpose, intended users, current scope/status, useful navigation และคำอธิบายที่อ่านได้โดยไม่ต้องรู้ประวัติแชต
2. **Original polished SVG logo:** งาน vector ต้นฉบับ ไม่ยืม trademark/สัญลักษณ์องค์กรอื่น มี viewBox, title/description และ alt text ตามการใช้งาน อ่านได้เมื่อย่อและในบริบทสีที่เลือก ไม่มี script, remote font หรือ external asset ที่ไม่จำเป็น การทำ logo ไม่ใช่การเริ่ม product UI
3. **Workflow และ architecture diagrams:** ใช้ Mermaid พร้อมคำอธิบายข้อความที่เข้าถึงได้ แยก product vision/planned components ออกจาก implemented path จริง แสดง staging, method/evaluator boundary, evidence/unknowns, revision/history และ provider/accounting seam ตามที่มีจริง
4. **Status ที่ตรงหลักฐาน:** แยก mock mechanics, bounded live pair เดิม, scientific pilot NOT_RUN, historical W2 access BLOCKED, B4 conditional และ G10/full G01–G22 ที่ยังไม่จบ อย่าใช้โลโก้หรือ diagram ทำให้ระบบดูเหมือนรับรอง clinical/regulatory/legal results
5. **Quickstart ที่ตรวจได้:** อ้าง command/options/files ที่มีจริง ตรวจ --help และ offline execution ในพื้นที่ที่อนุญาต ไม่ให้ quickstart overwrite old audit artifacts หาก runner ต้องมี output directory ใหม่ ให้ปรับคำสั่งตาม implementation จริง ไม่แต่ง CLI option
6. **Setup/config ที่ปลอดภัย:** ใช้ placeholders เท่านั้น อธิบาย local prerequisites และ explicit configuration behavior ไม่แสดง key ไม่แนะนำให้ paste secret ลง chat/browser ไม่อ้าง dotenv auto-load หรือ clean-clone reproducibility ที่ยังไม่ได้ตรวจ หากแหล่งข้อมูล local-only/ignored/licence-restricted จำเป็นต่อ command ต้องบอก prerequisite ตามจริง
7. **Module structure และ reproducibility/evaluation:** อธิบาย source modules จริง, contracts, targeted tests, run/evidence manifests, failed attempts และข้อจำกัดของ mock/one-case evidence ไม่เติม API/UI/memory runtime ที่ยังไม่มี
8. **Security/privacy/cost safeguards:** keys ฝั่ง backend/process ที่อนุญาต, no private patent data transmission, evaluator isolation, unknown billing, spend/attempt ceilings และ public/private artifact boundaries
9. **Contributor guidance:** วิธีตรวจ changed scope, เพิ่ม tests และรายงาน issue แบบไม่แนบ secrets/private documents รักษา frozen protocol/source witnesses และขอ authorization สำหรับ paid/security/publication changes ที่เกิน scope
10. **Actual licence information:** ตรวจ LICENSE/COPYING/package metadata และแยก code, datasets, source documents และ original assets ห้ามเลือก MIT/Apache/CC หรือเพิ่ม licence badge เอง ขณะ drafting ไม่พบ root LICENSE ในรายการที่ตรวจ และไม่พบ licence field จาก pyproject search จึงยังไม่ยืนยัน repository-wide code licence ต้องตรวจให้ครบก่อนเขียนข้อความ final

Data rights ที่มีบันทึกอยู่แล้วต้องอ้างอย่างจำกัด: G03 notes ระบุ PLS patent_ls เป็น CC BY 4.0; EnterpriseRAG MIT snapshot ยืนยัน repository/code terms ของต้นทาง ไม่ได้ยืนยัน data/release-asset terms ของเรา ส่วน DAPFAM และ PDF reading copies มีข้อจำกัดแยก อย่านำสิทธิ์ของ dataset/source repo มาใช้เป็น licence ของโครงการนี้

ห้าม invent badges, release/version claims, green CI, results, accuracy, novelty หรือ licence หาก CI ยังไม่มีให้บอกตามจริง ไม่สร้าง badge เพื่อแต่ง README

### Integration acceptance

- Pepo ส่ง path/hash list และการตรวจที่ทำจริง พร้อมข้อจำกัดของ setup/quickstart/rendering
- Luna เทียบ README กับ final code/options/tests/method-readiness และ evidence ล่าสุด รวม diagram nodes/edges และ caption
- relative links/assets ใช้งานได้ มี accessible text และไม่มี secrets/private raw payloads
- ค่าที่เป็น historical snapshot ติดป้ายแยกจาก current test counts ไม่อ้างว่า echo pair คือ scientific benchmark
- หาก docs ยังไม่พร้อม ให้ engineering subgoals จบต่อได้ แต่ final combined push เป็น BLOCKED_DOCS_HANDOFF ห้าม publish งาน Pepo ที่ยังไม่ส่งมอบ
- ทั้งสองฝ่ายไม่ทำ product UI งาน UI ยังคงเป็นของ Claude

## 15. W11 — Scoped final commit + push และตรวจ remote/CI

Owner อนุมัติให้ Luna commit และ push completed scoped changes รวม README/assets ของ Pepo หลัง gates ด้านล่างผ่านแล้ว การอนุมัตินี้แทนข้อห้าม commit/push แบบกว้างของ prompt ก่อนหน้า ไม่ต้องถามอนุมัติซ้ำสำหรับ scope ที่ชัดเจน แต่ต้องถามเฉพาะเรื่องที่ยังไม่ทราบเกี่ยวกับ destination หรือ publication sensitivity

**ขั้นนี้ใช้เมื่อดำเนิน Long GOAL จริงเท่านั้น ห้าม commit/push ระหว่างร่างหรือปรับเอกสารนี้**

### A. ตรวจ destination และ existing work โดยไม่เปลี่ยนสิทธิ์

- อ่าน repo guidance และตรวจ branch, HEAD, upstream, configured fetch/push remotes จาก execution context ที่ได้รับอนุญาต
- ใช้ established intended remote เท่านั้น ไม่เดา GitHub owner/repo/branch จากชื่อโครงการ ไม่สร้าง repository หรือเปลี่ยน visibility
- ปกปิด userinfo/token/query ที่อาจอยู่ใน remote URL ก่อน log ไม่อ่าน credential store หรือแสดง auth material
- หากมีหลาย remote, ไม่มี upstream, push URL ต่างจาก fetch URL หรือไม่ชัดว่า owner ตั้งใจปลายทางใด ให้ถามสั้น ๆ พร้อมตัวเลือกจาก metadata ที่อ่านได้ก่อน push
- หาก Git ownership/access ปฏิเสธ ให้หยุด Git action นั้น ไม่ตั้ง safe.directory, เปลี่ยน ACL, take ownership หรืออ่าน .git/config ผ่านทางอื่นเพื่อหลบ guard
- ตรวจ unrelated dirty/staged work และ outgoing commits เทียบ destination ที่ยืนยันแล้ว การ push HEAD อาจรวม commits เก่าที่ไม่ได้อยู่ใน scope ห้ามอนุมานว่า stage เฉพาะไฟล์ใหม่แล้ว publication scope ปลอดภัยเสมอ
- หากมี pre-existing outgoing commits หรือ private-data sensitivity ที่ยังไม่ชัด ให้หยุด publication และถามเฉพาะ scope นั้น ไม่ rewrite/merge history เพื่อทำให้ผ่าน

### B. Gates ก่อน commit และ push

1. F1–F4 และ required local checks ของ completed slice ผ่านด้วย evidence จริง Conditional pool/B4 ที่ยังไม่พร้อมต้องรายงานตรง ไม่ลด guard เพื่อให้มี green summary
2. รับ Pepo README/assets handoff ตาม W10 แล้ว ตรวจ factual consistency, quickstart, links, diagrams, licence wording และ current/historical status
3. ตรวจ source/evidence consistency กับ candidate ที่จะ commit จริง รวม source/input/schema/output hashes และ actual command/test receipts
4. ทำ secret/privacy scan เฉพาะ intended changed/staged files และ relevant outgoing publication scope ที่ได้รับอนุญาต รายงาน path/type/line แบบ redacted ไม่พิมพ์ค่าที่พบ ไม่สแกน home/private projects หรือ excluded raw corpus ทั้งชุด
5. Review diff ของ intended scope และ staging ให้ครบหลัง scan ไม่มี real .env, keys, private patent/org documents, denied evidence, PDF library, private/raw datasets, unrelated billing/session records หรือ extraneous generated artifacts
6. ตรวจ actual licence/redistribution boundary ของไฟล์ที่จะส่ง ไม่อ้างว่าการดาวน์โหลด source ได้ทำให้เผยแพร่ได้ทั้งหมด หากสิทธิ์หรือ sensitivity ไม่ชัด ให้ถาม narrowly ก่อน push
7. Stage explicit relevant paths หรือ hunks ที่เป็น completed work เท่านั้น ห้าม git add ., git add -A หรือ commit -a แบบกวาดทั้งหมด อย่า reset/restore/stash งานคนอื่นเพื่อทำ tree ให้สะอาด
8. ตรวจ staged diff/whitespace และ staged secret scan อีกครั้งให้ตรง exact commit candidate หากไฟล์มี mixed unrelated edits ให้แยกอย่างปลอดภัยหรือพักไฟล์นั้น ไม่ commit รวมเพียงเพราะอยู่ชื่อเดียวกัน

ไม่ต้องเพิ่ม framework/CI service ใหม่เพื่อให้ผ่าน gate ใช้ tooling ที่พร้อมและได้รับอนุญาต หากการตรวจจำเป็นยังทำไม่ได้ ให้รายงาน BLOCKED แทนการข้าม

### C. Commit, push และ verification

- สร้าง normal commit ของ completed scoped changes ตาม repo conventions ไม่ amend/rewrite history โดยไม่มี authorization
- บันทึก commit SHA และตรวจไฟล์ใน commit ว่าตรง reviewed scope รวม Pepo README/assets ที่พร้อมแล้ว
- Push เฉพาะ branch/ref และ established remote ที่ยืนยันแล้ว ไม่ force-push, merge, create repo, change visibility หรือ deploy
- หาก non-fast-forward/conflict หรือ authorization failure ให้หยุดและรายงาน ไม่เปลี่ยน destination หรือใช้ force/merge เพื่อหลบข้อผิดพลาด
- หากผล push uncertain ให้ตรวจ remote ref ด้วย read-only operation ที่ได้รับอนุญาตก่อนอ้าง success หรือพิจารณา retry ไม่สร้าง duplicate commit หรือ retry denial ผ่านช่องทางอื่น
- หลัง push ตรวจว่า remote ref ชี้ exact commit SHA ที่บันทึกไว้ แล้วจึงรายงาน PUSH_VERIFIED
- ตรวจ CI สำหรับ exact SHA หากระบบมีและเข้าถึงได้ ใช้ existing authorized auth เท่านั้น ไม่ setup credential หรือเพิ่มบริการเอง รายงาน PASS/FAIL/PENDING/NOT_CONFIGURED/BLOCKED ตามจริง ไม่ใช้ผลจากคนละ commit หรือป้าย latest green แทน
- CI pending/failed ต้องปรากฏใน final report ไม่อ้าง all checks passed หากยังไม่ทราบ ไม่เปิด deploy หรือ paid run ต่อเอง

### Final handoff

รายงาน completed commit SHA, remote/branch/ref ที่ตรวจแล้วแบบไม่มี secret, push/ref verification, CI exact SHA และ unrelated dirty work ที่คงไว้ ไม่อ้าง clean working tree หากยังมีงานอื่นค้าง

หาก destination/security/docs handoff ยังไม่พร้อม สามารถส่ง auditable completed work พร้อม PUBLISH_BLOCKED และ exact next action ได้ ไม่ต้องหยุดทุก offline subgoal หรือสร้าง permission workaround

Pepo audit ผูกกับ exact source candidate/final commit ที่ส่งมอบ หยุดหลัง scoped publication verification และรายงานผล ไม่ต่อ UI, deploy, model API หรือ paid study


## 16. เอกสารอ้างอิงและเกณฑ์ Goal จริง

- [AGENTS.md](../../AGENTS.md)
- [GOAL.md — G10](../../GOAL.md#L507): common method interface, same input/evidence/schema/validators, failures/costs และ isolated staging
- [GOAL.md — G13](../../GOAL.md#L579): รู้ cost/failure drivers เพื่อเลือก study ที่จบได้ ไม่จำเป็นต้องชนะ baseline
- [PROTOCOL.md](../../methodology/evaluation/PROTOCOL.md): B0/B1/B2/B3/B4-RG/P เป็น primary methods; B4-DR เป็น diagnostic ตามความพร้อม
- [G10 offline comparison handoff](G10_OFFLINE_COMPARISON_HANDOFF.md)
- [Current comparison source](../../src/patent_to_pilot/evaluation/comparison.py)
- [Current runner](../../scripts/run_g10_offline_comparison.py)
- [Current comparison tests](../../tests/test_g10_offline_comparison.py)
- [Prior W1–W8 handoff](LUNA_GOAL_CLOSEOUT_AND_PAIRED_REVALIDATION_TH.md)
- [Original comparison evidence manifest](../../results/development/g10-offline-comparison/evidence-manifest.json)
- [Readiness note](../provider-pilot/PAIRED_REVALIDATION_READINESS.md)

W1–W11 ในไฟล์นี้เป็น work packages ของรอบใหม่ ไม่ได้ตั้ง G หมายเลขใหม่หรือเปลี่ยน acceptance ของ G01–G22

## 17. Template รายงานที่ต้องส่ง

~~~text
Status: READY_FOR_PEPO_AUDIT / READY_WITH_BLOCKED_SUBGOALS / PUBLISH_BLOCKED
Candidate: verified revision หรือ UNKNOWN + source hashes
Changed files:
Protected files/baselines checked and limits:

F1: PASS / FAIL / BLOCKED — code locator, actual negative-control result
F2: PASS / FAIL / BLOCKED — runtime schema and validation evidence
F3: PASS / FAIL / BLOCKED — actual read-back / NOT_RUN / NOT_APPLICABLE
F4: PASS / FAIL / BLOCKED — call/state/skip counts and retained errors

W1 ... W11:
- Status:
- Actual command, exit code, test counts, run ID and evidence path:
- Limit / unresolved dependency:

Methods:
- Implemented logic vs wrapper/mock:
- States actually consumed:
- Input/profile/evidence/schema/validator versions:
- Execution / output validation / persistence status:
- Calls / failures / skips / retries:
- Mock cost and timing semantics:

Search readiness:
- Shared pool evidence and availability:
- Curator/evaluator boundary:
- B4-RG / B4-DR: IMPLEMENTED / MOCK-ONLY / NOT_IMPLEMENTED / BLOCKED / NOT_RUN

History and privacy:
- Old artifacts/journals unchanged:
- Provider/model inference API calls in this goal: 0
- Real key/.env reads: 0
- No denied-file or ACL action:
- No UI/deploy; scoped Git delivery only under W11:

README/assets and Git delivery:
- Pepo handoff paths/hashes and factual review:
- Verified quickstart / setup NOT_RUN limits:
- Actual license statement and data/source restrictions:
- Established remote/branch/upstream (redacted as needed):
- Explicit staged paths and excluded unrelated work:
- Local tests / secret scan / consistency / staged diff review:
- Commit SHA / pushed remote ref / ref-match verification:
- CI for exact SHA: PASS / FAIL / PENDING / NOT_CONFIGURED / BLOCKED
- Unresolved publication sensitivity / narrow owner question:

Goal limits:
- Full G10 still open:
- G12/G13 scientific work NOT_RUN:
- NO_ADVANTAGE / INCONCLUSIVE handling:

Owner-facing Thai:
- ตอนนี้ระบบพร้อมใช้ทำอะไร
- ยังใช้พิสูจน์อะไรไม่ได้
- ขั้นถัดไปที่ต้องตัดสินใจจริง โดยไม่โยน implementation details ให้ owner
~~~

ส่ง evidence ที่ตรวจได้ พร้อม scoped commit/push/remote-ref/CI status ตาม W11 แล้วหยุดรอ Pepo audit หาก publication gate ยังไม่ครบ ให้คง PUBLISH_BLOCKED และไม่ push ไม่ต้องทำทุก conditional method ให้เสร็จด้วยการลดมาตรฐานของหลักฐาน
