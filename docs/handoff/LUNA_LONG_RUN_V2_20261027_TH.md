# Luna Max — GOAL prompt: bounded long run รุ่น 2

วันที่ 27 ตุลาคม 2026 · เริ่มจาก repo `C:\Users\User\Desktop\myProject\patent-to-pilot`
ใช้ **GOAL prompt** ใน UI executor ที่เจ้าของเลือก ไม่ใช่คำสั่งเปลี่ยน product inference model
อ่าน AGENTS, GOAL เฉพาะ G ที่ทำ และ [requirements รุ่น 2](../product/REQUIREMENTS_DECISIONS_20261027_V2_TH.md) ก่อน ไม่ถือ historical status เป็น work order ปัจจุบัน

## เป้าหมายและ stopping conditions

ทำ repository ให้พร้อมไปสู่ deployable product และ evidence-supported international-journal manuscript โดยแบ่ง engineering release, scientific pilot และ journal submission เป็นคนละ acceptance
ไม่ตั้งเปอร์เซ็นต์เสร็จหรือสัญญาวันตอบรับ ผล NO_ADVANTAGE/INCONCLUSIVE เป็นผลที่ถูกต้องได้
owner อนุมัติงบใหม่ USD 5 รวมทุก agent/retry/calibration/pilot/UI test ผ่าน OpenRouter ตาม named models/routes เท่านั้น ไม่ใช่ $5 ต่อคนหรือ per-run
Pepo ทำ offline preparation ในรอบนี้ ส่วน live long run เป็น Luna รับช่วง ไม่รันเพียงเพราะเอกสารมี approved budget

## W1 — Reconcile source/evidence และ ownership

- อ่าน `PEPO_TO_LUNA_20261027_TH.md` + immutable final manifest และ closeout รุ่น 2 ล่าสุด
- ตรวจ working tree/source hashes/concurrent changes ก่อนแก้ ระบุ PASS/FAIL/BLOCKED/NOT_RUN แยก inspected/reported/independently run
- Protected: G11 adaptation, historical G09/G10 artifacts, frozen evaluation, `docs/research/pilot-next/`, old paid journals, delivered ZIPs, denied preflight ห้ามอ่าน/แก้/ย้าย/สร้างสำเนาเพื่อหลบ denial
- อย่าแก้ G01–G22 definitions เพื่อปิด milestones เอง ผูก work package กลับ G จริง

## W2 — Common current-input scientific adapter (G10/G13)

ใช้ existing staged inputs และ common closed output contracts ไม่ใช้ hardcoded case answer/clean repair
ปิด common-generation/response gaps ของ B1/B2/B3 และ proposed P เฉพาะ layer ที่อนุญาต รักษา old comparison outputs ไว้ในเดิม ถ้าต้องแก้ protected core เสนอ exact diff แล้วหยุดเฉพาะส่วน
Negative controls ต้องทำให้ actual validators fail: wrong value/role, absent span, withdrawn evidence, future key, schema-invalid output, persistence/readback mismatch และ provider failure accounting
Same facts, policy, model/output limit และ retrieval opportunity ต้องเท่ากันทุก comparator ไม่ตั้ง PASS จาก defaults/schema hash
`P_existing_workflow` ไม่เปลี่ยน label ให้เป็น full P; G11 full generator then scoped merge นับ full generation จริง

## W3 — Worker isolation และ accounting integration (G15/G18)

Input-boundary verifier ตรวจไฟล์/keys ได้ แต่ยังไม่ใช่ OS-isolated worker ต้องเตรียม constrained worker แบบที่ไม่อ่าน curator/evaluator/future files และตรวจด้วย denied-read controls ภายใต้ permissions ที่มี
ห้ามเปลี่ยน ACL/security เพื่อสร้าง sandbox หรือผ่าน Git ownership หากข้อจำกัด runtime ทำไม่ได้ ให้ BLOCKED พร้อม exact action ไม่ให้ broad filesystem worker เป็น ready
ทุก scientific/UI call ต้องผ่าน `providers/project_budget.py` database เดียวและ owner policy เดียว เปิดจาก path ที่กำหนดใน run manifest
SQLite transaction reserve ก่อน send; pending/unknown retain reservation และหยุด; settle debit ก่อน identity/schema; mismatch/overrun/failed calls เก็บค่าใช้จ่าย; retries มี attempt IDs ใหม่ แต่ replay ID เดิมห้าม dispatch
มี budget primitive/transport seam แล้ว ไม่อ้างว่า older engineering CLIs ถูกบังคับใช้ shared envelope อัตโนมัติ ต้องทดสอบทุก live entry point ที่จะเปิดจริง

## W4 — Data readiness / synthetic development (G03/G05/G06)

ใช้ generator `evaluation/synthetic_corpus.py`: default 24 fictional families, 48 cases, 4 template components, development24/demo24 ไม่มี real holdout
ใช้ `current/*.json` ทีละเคส ไม่ mount corpus.json/inventory/future events; synthetic label ติดไปจน export
เพิ่ม useful realism/negative cases ได้เมื่อ provenance/stipulations ตรวจได้ ไม่เพิ่มแต่ duplicate count Default scale สูงสุด120 families เป็น capacity guard ไม่ใช่เป้าจำนวน paper
จัด real public-patent heldout panel แยกจาก synthetic ด้วย family/template/time components, rights, chronological visibility และ independent case unit ห้ามเอา exposed PTP1–3 หรือเคส debug กลับไปเรียก holdout
Data acquisition ใหม่ที่มีเงื่อนไข license/paywall/download ไม่อยู่ใน blanket permission ไม่สั่ง full corpus เพื่อปิดงาน bounded

## W5 — Calibration ที่ได้งบแล้ว แต่ยังติด technical gates (G13)

แผน editable: `configs/long-run-offline-v2.json`
Candidate เริ่มเล็ก: PTP-0001/S0 × B1 × 2 models × 1 repetition = **2 attempts total, 0 retries**, output1500 เป็น feasibility/schema calibration ไม่วัด method advantage
Model/route: google/gemini-2.5-flash-lite → google-ai-studio; openai/gpt-4.1-mini → openai ผ่าน HTTPS OpenRouter เท่านั้น require_parameters true, fallback false, no tools/web/tier override
Public/synthetic payload ต้องอยู่ exact manifest พร้อม hashes/schema/framing ไม่มี private patent/org/user/evaluator content
ตรวจ official endpoint prices/capabilities ใหม่และ input upper bound รวม schema/framing ก่อน dispatch อย่าเอา fixed 128 tokens หรือ byte count มาอ้างเป็น tokenizer guarantee
Historical full-context reservation estimate ต่อ attempt: Gemini $0.1054576, GPT $0.4214304 รวม $0.526888 ภายใต้ราคา/context เก่า **ไม่ใช่ verified current bound**
หากต้อง reserve conservative full context จริง ให้นับ worst-case reservation แม้ prompt สั้น และยอม BLOCKED หากเกิน calibration $1 อย่าลด bound เพื่อให้ผ่าน
หลัง readiness ผ่าน ให้สร้าง new manifest/receipt ผูก approval owner ID/plan/database และ exact payloads ไม่ต้องขอ budget/models/data เดิมซ้ำถ้าอยู่ scope แต่ material expansion ต้องชี้ให้เจ้าของเลือก
ห้าม reset historical debit/journals ยอดเก่า source-reported $0.0001464 อยู่นอก incremental $5 แต่ต้องแสดงใน provenance

## W6 — Subsequent pilot / conditional search (G10/G13/G16/G17)

ปล่อย remainder $4 หลัง calibration พร้อมและ exact matrix/source/budget bounds เท่านั้น ยังไม่มี approved executable subsequent matrix ใน config ปัจจุบัน
Matched full-regeneration/direct-revision/deterministic-invalidation+same-generator และ dependency method ใช้ current facts/model accessเท่ากัน รวม graph/verification/retrieval/failures ใน cost
B0 diagnostics และ local P workflow แยกจาก model-based proposed method ไม่เอา mock output ไปเป็น scientific result
B4-RG/B4-DR **NOT_IMPLEMENTED/POOL_NOT_READY** จนมี shared verified distractor/recovery pool ที่ทุก methodเข้าถึงตามสิทธิ์เท่ากัน ไม่มี oracle/recovery IDs/future evidence
B4 conditional ไม่ใช่เกณฑ์บังคับให้สร้างผลผ่าน หาก pool ไม่พร้อมให้จำกัด claim และรายงาน NOT_RUN
Freeze protocol/matrixก่อน heldout outcome ใช้ paired family/case uncertainty/effect sizes ไม่ pseudo-replicate rows/revisions

## W7 — Product/backend และ Claude integration (G07/G09/G14/G15)

Entrepreneur/investor discovery/due diligence เป็นหน้าแรก; R&D เป็น underlying engine ไม่ใช่ investment execution/legal verdict
Contracts จริงอยู่ `product/contracts.py`; proposed HTTP routes และ9screen/journey requirements อยู่ Claude handoff ใหม่ ยังไม่ถือว่า API implemented
ทำ adapter/jobs/version conflict/idempotency/export/history แบบไม่ rewrite accepted core และไม่เปิด serverสาธารณะก่อน auth/deploy decisions
Claude ทำ UI minimal/formal/configurable themes ใน branch แยกเท่านั้น Pepo/Lunaไม่สร้าง UIแทน; verify official KMITL/ICT identityก่อนใช้ตรา/สีเป็นofficial
แสดง claim/source assertion/stipulation/interpretation/unknown, source/version/locator, before-after และ affected/preserved scopes Essential human confirmationsต้องคง ไม่เพิ่มปุ่ม approve ทุกfield

## W8 — Journal evidence / reproducibility (G02/G06/G17–G22)

ทำตาม `docs/research/JOURNAL_EVIDENCE_PLAN_20261027_V2_TH.md`:
precise falsifiable RQs, novelty beyond Doyle/RARR/Self-Refine/ALCE/internal53/Paper86, strong matched baselines/ablations, real heldout rights, blind expert rubric/agreement/adjudication, case/family intervals, cost-quality tradeoffs และ failure analysis
Synthetic stress testsพิสูจน์ mechanics ไม่พิสูจน์ real-world demand/business/investment outcomes Owner reviewไม่ใช่ independent expert gold
World Patent Informationเป็น domain-fit candidate ไม่อ้าง current Q1/Q2 หากไม่มี authoritative year/category evidence; current author guideยังunverified
Manuscript Results เป็น NOT_RUN/TODOจนมีผลจริง ไม่ invent tables/APC/submission/acceptance
USD5เป็น feasibility cap ไม่รับประกันว่าเพียงพอทั้งpaper ถ้าไม่พอต้องจบ bounded reportก่อนเสนอรอบใหม่

## W9 — Release/publication gates และ closeout

Ownerอนุมัติ scoped commit/push เข้า **existing origin main**: ตรวจ branch/remote, concurrent dirty work, tests/secret+rights/diff reviewก่อน Explicit file stagingเท่านั้น ไม่ add . ไม่รวมunrelated .gitignore/pyproject
ตรวจ deploy-triggerในrepoและบริการภายนอกที่เกี่ยวข้อง ถ้ายังไม่ทราบ external auto-deploy ต้องรายงาน/หยุด push ที่อาจเผยแพร่โดยปริยาย ไม่ force-push/reset/mergeClaude/deploy
Verify remote exact commitและ CIสถานะจริง ไม่มีworkflowก็รายงานไม่มีconfigured CI ไม่เขียนCI PASSเอง
Deployment proposal `configs/deployment-plan-v1.json` disabled จน destination/auth/costพร้อม ไม่มีdeploy authorizationในรอบนี้
Closeout ใส่ commands, source/evidence hashes, attempted/completed/failed counts, actual vs pending debit, blocked gates, protected invariance และ exactnextcommand แยก release/pilot/submission readiness

## คำสั่ง offline ที่มีจริง

```powershell
python -B scripts/prepare_long_run_offline.py --plan configs/long-run-offline-v2.json --output-dir results/development/long-run-v2-NEW --corpus-dir methodology/development/synthetic-NEW
python -B -m pytest -q -p no:cacheprovider tests/test_longrun_offline_v2.py tests/test_provider_adapter.py tests/test_g11_adaptation.py tests/test_g13_readiness.py tests/test_g13_stage_boundary.py
```

เลือก NEW ที่ไม่เคยใช้ ทั้งสองคำสั่งไม่ใช่ live dispatcher ต้องใช้ socket-denied verification harness และ TEMP outputsสำหรับ audit environmentตาม handoff
ไม่มี live command ที่พร้อมรันแล้วในเอกสารนี้ เพราะ technical gatesยังไม่ครบ ให้ Lunaทำและทดสอบ adapter/isolated workerก่อน ไม่เปลี่ยน falseเป็นtrueเพื่อข้าม
