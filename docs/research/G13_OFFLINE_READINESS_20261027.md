# G13 offline readiness and pilot preparation — 27 October 2026

สถานะ: **OFFLINE_PREFLIGHT_PASS / SCIENTIFIC_EXECUTION_BLOCKED**
ขอบเขต: G05/G06/G10/G13 preparation แบบ offline ไม่ใช่ full G13 และไม่ใช่การอนุมัติจ่ายเงิน

## ผลที่รันจริง

- ตรวจอิสระ G09/G10/G11: **57 tests ผ่าน** ใน 3.47 วินาที ตาม `results/development/pepo-readiness-20261027-r1/tests.xml`
- Source binding 5 รายการและ output hashes 7 ไฟล์ของ G10 candidate ตรง manifest
- ชุด G10 + readiness รุ่นสุดท้าย: **36 tests ผ่าน** = G10 เดิม 20 + readiness test cases ใหม่ 16 ไม่ใช่ 36 independent research samples
- Runtime calibration: 3 supported positives และ 7 deliberately wrong outputs ผ่านการตรวจตาม expected behavior ครบ
- CLI preflight: 3 exposed dev cases / 15 public states; 9 mock calls สำหรับ comparison PTP-0001 S0-S2; provider calls 0; API cost $0
- Python socket/DNS gate ไม่พบ attempt การอ่าน .env/evaluator-only/checked-facts ถูกกันใน CLI verification harness ขอบเขตนี้ไม่ใช่ system-wide packet capture หรือ OS worker isolation
- ไม่รัน model, embeddings, indexing, raw corpus parse, GPU หรือ held-out study

Evidence ใหม่: `results/development/g13-preflight-20261027-r1/`
Code: `src/patent_to_pilot/evaluation/pilot_readiness.py`
Plan: `configs/g13-offline-plan-v1.json`

## Dataset และ splits

ใช้ `methodology/evaluation/readiness-20261027/dataset-readiness.json` เป็น snapshot ใหม่ ไม่แก้ G06 registry/frozen fixtures เดิม

| Case | Source/family | Dependence component | สถานะ |
|---|---|---|---|
| PTP-0001 | US20060086689A1; family unverified | DEV-ROLE-TEMPLATE | exposed development |
| PTP-0002 | WO2001034119A2 / PLS:15973991 | DEV-ROLE-TEMPLATE | exposed development |
| PTP-0003 | WO2001021603A1 / PLS:23355646 | DEV-COUNT-TEMPLATE | exposed development |

มี 3 base cases แต่สองเคสแรกแชร์ template จึงไม่อ้าง 3 independent components ไม่มี validation/final-test/held-out organization panel ในชุดนี้ ห้ามย้ายเคสที่เปิดเฉลย/ใช้ debug แล้วไปเป็น untouched test

PLS มี G03-reported 1,421 rows ในสอง landscapes; data CC BY 4.0 แยกจาก upstream code AGPL-3.0 EnterpriseRAG v1.0.0 มี starter 39Q/39docs แต่ code MIT snapshot ไม่ยืนยัน data/release redistribution rights DAPFAM มี metadata/qrels/first-five samples ไม่ใช่ full corpus และ pharma/device counts ยัง unknown งานนี้ไม่ rehash corpus หรือรับ terms ใหม่

### การขยาย cases ที่ควรทำต่อ

เลือก real source/family ใหม่จากข้อมูลที่อนุญาต ตรวจ literal witness, original offsets, version และ rights ก่อนสร้าง case กำหนด template/base brief/component ก่อน generate variants เก็บ unsupported scientific fields เป็น unknown และมี positive/negative controls

รอบนี้เพิ่ม independent source cases **0** และเพิ่ม calibration/test coverage จากของที่ตรวจที่มาได้ ไม่แต่ง facts เพื่อให้ครบ 10 เป้าหมาย 10 dev cases ยังเป็น proposed coverage ไม่ใช่ acceptance quota หรือ power justification

Future pilot ใช้ development เพื่อ calibration ได้แต่ต้องติดป้าย exposed/descriptive ส่วน final panel ต้องเป็น source/family/template groups ที่ไม่ถูกใช้ tune และ freeze ก่อนเห็น outputs หากอ้าง cross-org ต้องมีองค์กร held out จริง ไม่ใช่ profile A/B/C ที่ต่างกันเพียง fictional policy

## Input boundary และ evaluator

`current_stage(case, state)` โหลดเฉพาะ current public packet กับ declared profile มี read-set test ของ S0 ยืนยันว่าไม่เปิด S1-S4/answer keys/source archives Runtime payload มีเพียง packet/profile ส่วน schema แยกอีกไฟล์ และตรวจ nested evaluator/future keys ทั้ง packet, profile และ schema

การ stage ลงหลาย folders ใน curator directory **ยังไม่ใช่ security sandbox** วิธีที่จะถูกประเมินจริงต้องอยู่ worker ที่ไม่อ่าน parent repo, sibling future states, evaluator files หรือ clean replacements ได้ ห้ามส่ง directory ทั้งชุดให้ model agent

Runtime output contract แยกจาก domain evaluator และ persistence ผล comparison เป็น NOT_RUN ด้าน persistence ไม่เรียก default boolean ว่า roundtrip สำเร็จ Quote/span match ตรวจ literal presence ไม่ใช่ entailment, feasibility หรือ clinical/legal gold

## Methods: ready แบบใด

| Cohort | ใช้ได้ตอนนี้ | สิ่งที่ยังไม่พร้อม |
|---|---|---|
| B0/B1/B2/B3/P_existing_workflow | deterministic/mock mechanics บน PTP-0001 S0-S2 | ไม่ใช่ fair live generation comparison |
| PTP-0002/0003 | typed current packet inventory, integration S0 positive controls | common comparison view/B2 adapter ยังจำกัด PTP-0001 |
| G11 bounded adaptation | prior accepted explicit dependency/full-generator-then-scoped-merge slice | ไม่แก้ในงานนี้ และยังไม่มี common live scientific P adapter |
| B4-RG/B4-DR | NOT_IMPLEMENTED / NOT_RUN | ต้องมี verified shared recovery/distractor pool และ equal budget |
| G12 learning | NOT_RUN | chronological confirmed feedback + memory controls + clean final panel |

ดังนั้น P wrapper ปัจจุบันห้ามใช้แทน full proposed dependency-guided method ใน scientific superiority claim และห้ามเรียก scoped merge ว่าประหยัด generator compute ถ้ายัง full-generate ก่อน merge

## G13-A: ข้อเสนอ calibration รอบแรก ยังไม่อนุมัติและยัง dispatch ไม่ได้

วัตถุประสงค์แรกคือทดสอบ response binding, error modes และ token/cost จริงบน exposed dev ไม่ตอบ efficacy หรือ algorithm-superiority RQ

Matrix ที่เสนอหลัง gates ครบ:
- PTP-0001 S0/S1/S2
- B1 full regeneration, B2 direct revision, B3 deterministic invalidation + same generator
- 2 models × 3 states × 3 provider methods × 1 repetition = **18 dispatched attempts สูงสุด**
- B0 และ P wrapper เป็น local diagnostics แยก ไม่ปลอมเป็น model calls
- ไม่มี retry/automatic repair; เก็บ failures/schema-invalid/unknown billing และ dependent skips ตามจริง
- Google `google/gemini-2.5-flash-lite` pinned `google-ai-studio`; GPT `openai/gpt-4.1-mini` pinned `openai`
- HTTPS OpenRouter endpoint ที่ตรวจแล้ว, provider.only, allow_fallbacks=false, require_parameters=true, no tools/web/reasoning/tier overrides; ตรวจ requested/reported identities
- Target input upper bound 4,000 tokens รวม prompt/schema/framing และ output max_tokens 1,500 แต่ **input bound ยังไม่ verified** ห้ามใช้ byte count หรือ fixed allowance แทน tokenizer proof โดยเงียบ ๆ
- Export exact outgoing payloads/hash ให้ตรวจ scope ก่อนขอ scientific transmission/budget approval ไม่มี live command ให้รันจากเอกสารนี้

หนึ่ง repetition มีไว้ calibration ไม่ประมาณ seed variance หรือสรุปชนะ เพิ่ม repetitions/panel หลังทราบ coverage/failure/cost และกำหนดล่วงหน้า ไม่ rerun จนได้ผลที่ชอบ

### งบที่เสนอ ไม่ใช่อนุมัติ

เสนอ **incremental hard cap $1.00 สำหรับ G13-A** หลัง prerequisites/owner approval ครบ เป็นเพดาน stop ไม่ใช่เป้าหมายให้ใช้หมด และไม่รับรองว่าจะครบ 18 attempts

Public endpoint check วันที่ 27 ต.ค.: OpenAI route ยังแสดง prompt $0.40 / completion $1.60 ต่อ 1M และรองรับ structured_outputs/response_format/max_tokens
Source: https://openrouter.ai/api/v1/models/openai/gpt-4.1-mini/endpoints

Gemini endpoint เปิดผ่าน web tool ไม่สำเร็จในรอบนี้ จึงต้อง recheck ก่อน dispatch อัตรา $0.10/$0.40 ต่อ 1M เป็น historical snapshot เดิม ไม่อ้างว่า verified current
Source ที่ต้องตรวจ: https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints

ถ้า 4,000+1,500 เป็น upper bound ที่ verified จริง ภายใต้ rates ดังกล่าว estimate คือ Gemini $0.001/attempt และ GPT $0.004/attempt; 9 attempts/model รวม $0.045 ข้อนี้เป็น conditional arithmetic ไม่ใช่ hard cost guarantee

หากยังต้อง reserve full context ตาม historical conservative bounds ประมาณ $0.1054576/$0.4214304 ต่อ attempt ทั้ง 18 attempts อาจต้อง reserve รวมประมาณ $4.741992 แบบ worst-case ดังนั้น cap $1 ต้องหยุดก่อนครบได้ ห้ามลด reservation เพื่อให้ matrixดูพร้อม Fresh prices/context/usage accounting และ tokenizer proof ยังเป็น gate

ยอดเครดิต owner-reported $10 ไม่ใช่วงเงินอนุมัติ ยอด debit สะสม $0.0001464 เป็น SOURCE_REPORTED จาก echo closeout ไม่ใช่ค่า pilot และ approval $0.60 เดิมไม่โอนมาใช้กับ scientific prompts

## Scientific pilot ที่ตอบ RQ จริง

หลัง G13-A และ case coverage พร้อม ต้องกำหนด fair common live generation/evaluation adapter ของ B0-B3 และ P ที่นิยามตรงกับ mechanism, shared payloads, paired case/event inputs, same schemas/validators และ costs ของการ generate/repair/validation ทั้งหมด ถ้าศึกษา search ต้องเพิ่ม B4 ตาม pool ที่ตรวจแล้ว หากยังไม่มี pool ให้ตัด search-efficiency claim ออกหรือคง BLOCKED ไม่สร้างผลจำลองแทน

Primary: required-update recall, unaffected-field preservation, residual explicit violation rate
Secondary: precision, unnecessary changes, source integrity/stale-source reuse, unknown/conflict handling, schema validity, total cost/cost per valid revision และ latency/failures
รายงาน TP/FP/FN, eligible denominators, NA เมื่อ denominator 0; macro per base/dependence component และ paired differences ผล pilot เล็กเป็น descriptive ไม่อ้าง power/generalization

Acceptable outcomes: NO_ADVANTAGE, INCONCLUSIVE, NEGATIVE_RESULT หาก rules/direct revision เพียงพอให้ simplify ไม่บังคับ P ชนะ

## Stop rules และ accounting

หยุดเมื่อ code/source hash drift, oracle/future leak, missing upper bound, model/provider drift, unknown_pending billing, reservation/cumulative breach หรือ payload/matrixไม่ตรงapproval
Reserve ก่อนทุก dispatch, retain actual debit ก่อน model/schema validation, failed attempts คิดต้นทุนด้วย; absent usage ไม่เป็นศูนย์ ไม่มี silent fallback/retry/ledger reset

## คำสั่งที่รันได้ตอนนี้

จาก repo root เลือก output ใหม่เสมอ:

```powershell
python -B scripts/run_offline_verification.py --suite readiness --output-dir "$env:TEMP/ptp-readiness-luna-20261027-01"
python -B scripts/run_g13_offline_preflight.py --plan configs/g13-offline-plan-v1.json --output-dir results/development/g13-preflight-luna-20261027-01
```

คำสั่งหลังเป็น offline-only ไม่มี --live และไม่โหลด key หาก output มีอยู่ให้เลือก run ID ใหม่ ห้ามลบ/ทับ retained evidence เพื่อให้รันผ่าน
