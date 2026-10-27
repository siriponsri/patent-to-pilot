# Pepo → Luna / Claude — offline long-run preparation รุ่น 2

วันที่ 27 ตุลาคม 2026 · เครื่อง DESKTOP-C8EHASQ · repo `C:\Users\User\Desktop\myProject\patent-to-pilot`

## ผลที่ทำจริง

- บันทึก owner answers เป็น [requirements v2](../product/REQUIREMENTS_DECISIONS_20261027_V2_TH.md) งบใหม่รวม USD5, public/synthetic เท่านั้น, 2 named models/routes และ scoped main push ไม่อนุญาต deploy โดยปริยาย
- [Claude handoff](../product/CLAUDE_ENTREPRENEUR_INVESTOR_V2_TH.md) ปรับเป็น entrepreneur/investor evidence-backed journey, minimal/formal themes และ essential human checkpoints UI implementation ยังเป็น Claude ใน branch แยก
- เพิ่ม closed Pydantic contracts 4ชนิดใน `product/contracts.py` ไม่ใช่ HTTP API
- เพิ่ม reproducible synthetic corpus 48cases/24families/4template-components development24/demo24 ไม่มี real heldout/gold ดู [data note](../product/SYNTHETIC_DATA_V2_TH.md)
- เพิ่ม SQLite `ProjectBudget` และ `BudgetedTransport` reserveก่อนsend, debitก่อนidentity/schema, idempotent settlement, replay/unknown/breach blocking และ capรวม$5/phase$1+$4 ตัว componentไม่บังคับ older engineering CLIs ทั้งหมดเอง
- เพิ่ม `prepare_long_run_offline.py`, editable offline plan และ disabled deployment proposal พร้อม [journal evidence/manuscript outline](../research/JOURNAL_EVIDENCE_PLAN_20261027_V2_TH.md)

## Tests และหลักฐาน

Affected cohort **86 passed, 0 failures/errors/skips**: new offline-v2 tests ร่วม provider adapter, G11 adaptation, G13 readiness และ stage boundary
มี two-connection reservation race, durable reopen/replay, phase/total caps, invalid/missing billing, schema/model validation failures และ fake-secret traceback control ไม่เปิด provider socket
Actual CLI สร้าง corpus/schema/preflight ได้ ผล scientific_live_ready=false พร้อม7blockedgates ไม่ใช่ hardcoded scientific PASS
Python socket/DNS gate attempted0, provider calls0, API$0 ไม่ใช่ system-wide packet capture และไม่มี native adversarial sandbox test
Source unchangedระหว่างfinaltest; original source30ไฟล์และprotected119ไฟล์ตรงก่อนเริ่ม ไม่ rehashrawcorpus

Evidence: `results/development/long-run-offline-20261027-v2/` มี verification.json, tests.xml, pytest.log, preflight/preflight.json, product-schemas.json และ final-manifest.json
Testsเขียนโดยผู้ทำimplementation จึงเป็น executed regression evidence ไม่ใช่ independent semantic/expert validation ให้Luna reviewเฉพาะdiffนี้ ไม่เปิดacceptedG09/G10/G11auditใหม่

## สิ่งที่ยังไม่พร้อม

| Layer | สถานะและสิ่งที่ขาด |
|---|---|
| Engineering release | OFFLINE_COMPONENTS_READY_FOR_REVIEW; ยังไม่มี product HTTP API/auth/deploy integration หรือ UIจริง |
| Scientific pilot | BLOCKED: fresh endpoints/prices, full-request token bound, common scientific generator, worker isolation, exact payload manifest, shared budget integrationทุกdispatchpathและrelease receipt |
| Search B4 | NOT_IMPLEMENTED/POOL_NOT_READY; conditional ไม่ใช่บังคับสร้างfakepoolเพื่อผ่าน |
| Journal submission | NOT_READY: novelty/closest collisions, real heldout, blindexpertagreement, paireduncertainty และผลจริงยังขาด |
| Owner choices | ภาษา, auth/collaboration/retention, deploydestination/domain/hostingcostยังไม่เลือก งานอื่นเดินต่อได้ |

ค่าเครดิต$10ไม่ใช่capใหม่ ยอดเก่า source-reported $0.0001464คงในhistoryและไม่นับเป็นงบincrementalใหม่ ไม่อ่านaccount/keyเพื่อยืนยันยอดรอบนี้
Current$5รองรับfeasibilityตามboundsจริง ไม่รับรองว่าพอทั้งpaper

## Handoff และ exact next steps

1. Lunaอ่าน [GOALรุ่น2](LUNA_LONG_RUN_V2_20261027_TH.md), source/evidence manifestและrequirements แล้วรับ commonadapter/isolation/budgetintegrationที่ยังBLOCKED ไม่มีlivecommandreadyให้กดรันทันที
2. Claudeอ่านjourney/contracthandoff ใช้ current synthetic fixtureทีละไฟล์และbranchแยก ไม่แก้evaluatorหรือสร้างผลlive
3. ทำofflinepreflightซ้ำในfreshdirectories:

```powershell
python -B scripts/prepare_long_run_offline.py --plan configs/long-run-offline-v2.json --output-dir results/development/long-run-v2-NEW --corpus-dir methodology/development/synthetic-NEW
```

4. Paidcalibrationcandidate2attempts/0retriesอยู่ในapprovedmodels/data/$1phase แต่technicalgatesยังต้องผ่านก่อนส่ง ห้ามอ่าน.envเพื่อdryrun
5. หลังtechnicalreadinessผ่านค่อยLunaสร้างexactpayload/runreceiptและรันภายใต้shared$5ledger ไม่ขยายmatrixหรือresetoldjournals

## Git/access ณ verification

Localmainและremoteoriginmainเริ่มที่373a1356a8eca8c94d953bbd7e09dbd9df172e28 ตรวจremoteผ่านgitls-remoteแล้ว ไม่พบtrackeddeploymentfilesหรือGitHubActionsworkflow (API total_count0)
GitHubCLIอ่าน`C:\Users\User\AppData\Roaming\GitHub CLI\config.yml`ไม่ได้ Access denied จึงไม่ retry/แก้permissions/อ่านconfig; ใช้GitremoteและGitHubconnectorที่ได้รับอนุญาตแยกตรวจref/workflows ไม่แตะไฟล์denied
ไม่สามารถรับรองexternalhostinghooksที่ไม่ได้แสดงในrepoได้ ไม่มีactualdeploymentcommandในงานนี้ ผลcommit/pushและexactremoteCIให้ดูfinaltaskreport ไม่อ้างว่าCIผ่านเพียงเพราะไม่มีworkflow
Unrelateddirty `.gitignore`/`pyproject.toml` ต้องคงนอกcommitของPepo ห้ามstageทั้งrepo
