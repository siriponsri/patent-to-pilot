# Patent-to-Pilot long-run work breakdown — requirements draft v1
วันที่ 27 ตุลาคม 2026  
สถานะ **DRAFT_REQUIREMENTS_PENDING** ไม่ใช่ long-run goal ที่ถือว่าเสร็จหรือได้รับงบครบแล้ว

## เริ่มจากหลักฐานที่ปิดแล้ว

อ่าน [Pepo → Luna handoff](PEPO_TO_LUNA_20261027_TH.md) และ `results/development/pepo-readiness-20261027-r1/final-manifest.json` เป็น immutable baseline
G10 bounded audit อิสระผ่าน 57 tests และ readiness cohortผ่าน 36 tests โดย latterรวม G10 20 + readiness 16 ไม่บวกเป็นจำนวน independent experiments
CLI offlineมี 3 exposed dev cases/15 states, 10 calibration controls, 9 mock calls, provider calls0 และ scientific_live_ready=false
Full G10/G11/G12/G13, fair live comparison, held-out results และ full UI/APIยังไม่ถูกปิดด้วยหลักฐานนี้

กรอบ requirementsอยู่ใน [decision register](../product/REQUIREMENTS_DECISIONS_20261027_V1_TH.md) และ UI briefใหม่อยู่ใน [minimal/formal draft](../product/CLAUDE_MINIMAL_FORMAL_DRAFT_20261027_V1_TH.md)
IDs LR-A เป็นต้นไปเป็น work packages ของแผนนี้ ไม่เปลี่ยน/renumber GOAL G01-G22

## Work packages และ bounded acceptance

| Package / GOAL mapping | งานและชิ้นงาน | Owner/stream | Dependencies และ acceptance |
|---|---|---|---|
| LR-A / G01,G02,G14 | requirements decisions, research/product endpoint, minimal/formal UI scope | Pepo + owner | คำถาม R01-R08มีคำตอบ/ขอบเขตชัด ข้อเสนอไม่กลายเป็นapprovedเอง |
| LR-B / G05,G06 | source/family/template inventory, curation candidates, visibility contract, evaluator controls | Pepo/GPT Work offline; Luna curationต่อ | current devไม่เป็นholdout; every new independent caseมี witness/version/rights/unknowns; no fabricated gold |
| LR-C / G10,G11,G15 | common generation/response contract, input boundary, failure accounting และ worker isolation | Luna หลัง scope/gates | same public inputs/schema/validators/budget, verified negative controls, no oracle/future reads; protected baseline changesเสนอเป็นdiffก่อน |
| LR-D / G14,G15 | minimal/formal mock screens, evidence inspector, changes/history/export states, accessibility | Claude | R01-R05; P0 mock journeysผ่าน ไม่มี fake backend/live result |
| LR-E / G07,G09,G14,G15 | typed backend/API adapters, jobs/status/idempotency/revision conflict, export/recovery | Luna integration | agreed contracts; offline/mocked E2Eก่อน network exposure; auth/storageขึ้นกับR03/R04 |
| LR-F / G13 | explicit model calibration matrix, exact payload hashes, fresh endpoint/token bounds/ledger caps | Luna; Pepo targeted audit | R06/R07 + engineering gatesครบ; attempts/retries/cumulative capชัด; scientific callsยังNOT_RUNตอนนี้ |
| LR-G / G13,G16,G17 | scientific pilot, final freeze, main/ablationsตามclaim และ analysis | Luna + Pepo review | broader groups/calibration; heldoutไม่ถูกtune; deviations/failures retained; NO_ADVANTAGE/INCONCLUSIVEยอมรับได้ |
| LR-H / G12 | scoped confirmed-feedback learning ถ้าendpointที่ownerเลือกต้องมี | Luna หลัง protocol | chronological schedule, memory-off/same-feedback controls, org isolation/rollback; ไม่เรียก revisionเดิมว่าlearning |
| LR-I / G18-G22 | reproducibility, portfolio/manuscript, authorized publication/submission/reviewer response | ตามendpointที่ownerยืนยัน | ใช้ผลจริงและrights/attributionครบ ไม่รับรองjournal acceptance; G21/G22รอsubmission/decisionจริง |
| LR-J / cross-cutting | final scoped commit/push และ exact-commit evidence | Luna ตามowner scope | R08, tests/diff/secret+rights checks, preserved unrelated work, intended remote/ref/CI verified; ไม่deployโดยปริยาย |

## Parallelism ที่ไม่แย่ง ownership

1. ตอนนี้ Pepoทำ additive docs/input verification/calibration readiness ได้ โดยไม่รอ UI/model calls
2. หลัง requirementsชัด Claudeทำ UI mock ด้วย public/fictional fixtures แยกจาก backend/evaluator stream
3. Lunaทำ adapter/isolation/contracts/case curation ในขอบเขตที่ไม่แก้ protected baselineเงียบ ๆ
4. Integrationเกิดหลัง contractsตรงกัน ไม่ให้ frontendสร้างendpoint/enumหรือผลliveขึ้นเอง
5. Paid calibrationเริ่มเฉพาะ exact scope/cap/transmissionที่approvedแล้ว ไม่ใช้การเติมเงินหรือข้อความlong runแทนreceipt
6. การทดลองและ UIไม่ต้องรอกันถ้าไม่มีdependencyจริง แต่ scientific readinessไม่อาศัยUIที่ดูเรียบร้อยเป็นหลักฐาน
7. ไม่เปิด agent/account หรือส่งงานไป external Claude/Luna serviceเองจากแผนนี้ ชื่อ Luna Maxเป็นexecutor preference ไม่ใช่ product inference model ID

## Research acceptance และ data integrity

- แยก source assertion/stipulation/interpretation/unknown ไม่มี independent clinical/legal goldที่ยืมจาก owner/LLM
- Related papersช่วยกำหนดcomparators ไม่พิสูจน์firstnessหรือว่า reproduce แล้ว
- Stage current inputsเท่านั้น; expected_doc_ids/gold answers/checked facts/clean repairs/future eventsเป็น evaluator assets
- Shared sources/templates/briefsอยู่componentเดียวกันก่อนvariants; currentสามcasesเป็นdevelopmentทั้งหมด
- Literal/hash integrityไม่แทนsemantic support และ source claimไม่แทนefficacy/feasibility/FTO
- ทุกmethodได้same input opportunities/validators; costsรวมfailed/repair/validation; denominator0เป็นNAไม่ใช่100%
- Main panel/global prompts/metrics/budgetfreezeก่อนheldout outcomes; ถ้าใช้testdebugต้องmarkcontamination
- B4ยังPOOL_NOT_READY ไม่เพิ่มfake distractors/recoveryเพื่อปิดงาน; ถ้าไม่ศึกษาsearchให้จำกัดclaimแทน
- G11 full-generator-then-scoped-mergeต้องนับcomputeตามจริง ไม่เรียกว่าประหยัดgenerationจากชื่อscoped

## Backend/evaluator boundaries

รักษา typed IDs/version/statusและappend-onlyhistoryเดิม APIงานใหม่เป็นadapterไม่ใช่เหตุให้rewritecore
สิ่งที่ทำได้ก่อนownerตอบ: input shape/hash/size/path checks, synthetic failure controls, reproducibility receipts และ documentation
สิ่งที่ยังรอ: network exposure/auth/collaboration/storage topology/private imports, model routing/scientificbudget และsource payloadที่จะส่งออก
OS/process-isolated workerยังเป็นblocker input verifierใหม่ช่วยตรวจขอบเขตไฟล์แต่ไม่อ้างว่าตัดparentfilesystemได้แล้ว

## UI/human review acceptance

Core journeyตามdraft: project/brief → source/org map/critical confirmation → options/routes → draft handoff → change/diff → history/export
แสดงevidence basis, source/version/locator, unknown/conflict/withdrawal, next actionและroute-localblock
ready_for_reviewแยกจากreviewer approved; proposed testsแยกจากcompleted measurements; human activity journalไม่ใช่automatic transcript captureหรือlearning
Loading/empty/error/blocked/unsaved/recoveryต้องออกแบบก่อนpolish และสามารถใช้keyboard/จอแคบได้
Minimal + formalยืนยันแล้ว แต่EN/TH/colors/rolesไม่freezeจนR01-R05ตอบ

## Budget gate และข้อเสนอที่ยังไม่ approved

- ข้อเสนอใหม่ $5 overall ($1 calibration+$4 subsequent work) เป็น PENDING เท่านั้น ไม่ใช่capที่ใส่ในdispatcher
- ข้อเสนอ18 attemptsใน G13 readinessเดิมเป็นcalibration candidate ไม่ใช่matrixที่ownerเลือกแล้ว
- ต้องตอบว่าcapเป็นincrementalหรือรวมhistory, ค่าsetup/reserveนับอย่างไร และstopเมื่อunknown usage/drift/breach
- Fresh input boundรวมschema/framingและoutput max_tokensต้องverified ไม่ใช้fixed allowanceเป็นguarantee
- Pinmodel/upstream, no fallback, exact recipients/data disclosuresและfailure/resume receiptsก่อนdispatch
- ยอดเครดิต $10 และ approval echoเดิมไม่เป็นspending authorityสำหรับscientificrun
- ถ้าcapต่ำกว่าความต้องการreserve ให้stop/deferบางmatrix ไม่ลดreservationเพื่อให้ดูready
- งานjournalfees/labour/annotation/storageไม่ได้รวมอัตโนมัติในข้อเสนอ API cap

## Commit/push gate

Ownerต้องการให้มีcommit/pushในlong run แต่R08 targetยังpending และรอบเตรียมนี้ไม่push
ก่อนpublishให้Luna inspect branch/upstream/remotesและdiffจริง ใช้ established intended destinationเท่านั้น ไม่guess/create repo/changevisibility/force-push/merge/deploy
Stage explicit scoped filesหลังtests, source/evidence consistency, secrets/private-data/rights review ห้าม git add . หรือรวมunrelated .gitignore/pyproject work
Record commit SHA, verifyremote refของexactcommit และCIหากมี pending/failedต้องรายงานตามจริง
หากpublication sensitivityหรือtargetยังไม่resolved ให้ถามเฉพาะประเด็นนั้น ไม่ขอapproval routineต่อไฟล์

## งานที่ทำเพิ่มในรอบ requirements นี้

Additive staged-input verifier:
- exact2-file bundle, SHA256 binding, closed packet/profile envelope
- strict JSONไม่มีduplicate keys/NaN, bounded reads
- case/state/profile-version binding, nestedoracle/future keysทั้งinputและschema
- rejectoutside-root path, extra future/hidden files และsymlink/reparse metadata
- ไม่โหลดkey/เรียกprovider ไม่แก้ readinessรุ่นเดิมหรือimmutablemanifest

ผล: readiness16 + boundary16 = **32 testsผ่าน**, actual CLIตรวจ15bundlesผ่าน, socket attempts0, provider calls0
Reparse rejectionมี deterministic mocked control ไม่อ้างว่าเป็นOS permissions/junction penetration audit
ขอบเขตที่ยังไม่แก้: OS worker isolation, semantic leakageในprose, curator manifest authenticityและscientificadapter

Evidenceใหม่: `results/development/pepo-requirements-20261027-v1/`  
ไฟล์ codeใหม่: `src/patent_to_pilot/evaluation/stage_boundary.py`, `scripts/verify_g13_stage_boundary.py`, `tests/test_g13_stage_boundary.py`

## คำสั่ง offline ที่ใช้ตรวจต่อได้

เลือกoutputใหม่เสมอ:

```powershell
python -B scripts/verify_g13_stage_boundary.py --preflight results/development/g13-preflight-20261027-r1/preflight.json --output results/development/g13-boundary-luna-20261027-01.json
```

คำสั่งนี้ไม่dispatchและไม่ทำให้scientific_live_ready=true

## ส่งต่อให้ใคร

**ทำแล้วตอนนี้:** requirements register, minimal/formal Claude draft, long-run breakdown, bounded input checks/testsและfresh receipts  
**รอ owner:** R01-R08 โดยเฉพาะ endpoint/privacy/language/budget/transmission/branch  
**Claude:** UI mock/design/state/accessibilityตามbriefที่finalizeแล้ว; ไม่แก้ backend/frozen evaluation  
**Luna:** focused reviewของadditive code, live adapter/isolation/integration, case curationและexperimentsหลังgates; finalscopedcommit/push  
**Pepo:** reconcileคำตอบเป็นrequirements v2, refineacceptance/contractsและtargetedaudit ไม่ส่งงานข้ามบัญชีเอง

## Startup prompt หลัง owner answers

> อ่าน AGENTS.md, docs/product/REQUIREMENTS_DECISIONS_20261027_V1_TH.md และเอกสารนี้ก่อน ตรวจว่าคำตอบ R01-R08 ได้บันทึกเป็น versionใหม่แล้วหรือยัง ถ้ายัง ให้ทำเฉพาะ offline work ที่ไม่ขึ้นกับคำตอบ ไม่สมมติ $5, EN/TH, สี หรือ branch ว่า approved รักษา immutable handoff/final manifest/history/G11/frozen evaluation/pilot-next/ZIPs ให้แยก backend/evaluator กับ UIของClaude ทำ targeted testsและfresh evidenceตามงานจริง ไม่มี API/key/pushจากdraftนี้ เมื่อ approved run matrix/payload/cap/targetครบแล้วค่อยทำ Luna long runในขอบเขตนั้น และรายงาน PASS/FAIL/BLOCKED/NOT_RUN ตามหลักฐาน ไม่ต้องให้ proposed methodชนะจึงจะถือว่าexperimentจบ
