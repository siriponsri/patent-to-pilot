# Luna pre-live long-run handoff

นี่คือ prompt สำหรับงานรอบถัดไป ไม่ได้เริ่ม long run หรือ acquire dataset ใหม่ในรอบ audit นี้ Owner อนุญาตให้รอบถัดไป download ข้อมูลที่จำเป็นและเพิ่มปริมาณเกินขั้นต่ำเพื่อ coverage ภายใต้สิทธิ์/ทรัพยากรที่เหมาะสม ไม่ครอบคลุม paid API, purchases, access-control bypass, การเผยแพร่ restricted payloads หรือ deployment

ใช้ [prompt ข้อความล้วน](LUNA_PRELIVE_PROMPT_TH.txt) พร้อม measured character count ใน [audit receipt](REPRODUCIBILITY_AUDIT.json) รุ่นโมเดล `gpt 5.6 luna max` เป็นชื่อที่ owner ขอ ไม่ยืนยันว่าเป็น provider/API model ID และไม่ต้องเปลี่ยน account/config เพื่อให้เริ่มงานได้

## เอกสารที่ยึดถือและลำดับ

1. คำสั่งล่าสุดของ owner และ runtime permissions
2. Root `AGENTS.md` สำหรับ execution/privacy/spend และ applicable local skill instructions
3. Root `GOAL.md`, `PLAN.md`, `README.md` ตาม HealthTech Pack สำหรับ thesis, HT-G0–HT-G8, HT-W01–HT-W20 และ product claims ไฟล์ `docs/GOAL.md`/`docs/PLAN.md` เป็น redirect ไม่ใช่ master อีกชุด
4. `docs/healthtech/progress.json`, `docs/healthtech/REPRODUCIBILITY_AUDIT.md`, `docs/healthtech/MIGRATION.md`, `docs/healthtech/RUNBOOK.md`, `memory/next-actions.md` สำหรับ actual state/commands ไม่ใช่สิทธิ์ override scope
5. `RELATED_PAPERS.md`, `literature-review/healthtech/paper_manifest.json`, `literature-review/healthtech/READING_NOTES.md`, `docs/healthtech/research/SUPPLEMENTAL_DATA.md`, `configs/healthtech/data_registry.json`, `configs/healthtech/task_protocol.json` สำหรับ sources/rights/tasks; task_protocol ยังเป็น engineering contract ไม่ใช่ frozen scientific protocol
6. Original papers/manifests/current source code สนับสนุนข้อเท็จจริง Historical G/B protocols/results เก็บความหมายเดิม ไม่เป็นคำสั่งกลับไปทิศทางเก่าและไม่กลายเป็น HealthTech results

Project root: `C:\Users\User\Desktop\myProject\patent-to-pilot` เริ่มด้วยตรวจ HEAD/origin/main ให้ตรง latest published correction และเปิด audit receipt ปัจจุบัน ไม่อ้าง stale SHA จากรายงานเก่า

## งาน offline ที่ทำต่อได้

| Goal | ขอบเขตที่เดินได้ก่อน live | ขอบเขตที่ยังปิดทั้ง goal ไม่ได้โดยอัตโนมัติ |
|---|---|---|
| HT-G0 | W01/W02 contracts/docs alignment | ต้องตรง implementation จริง |
| HT-G1 | W03 rights/cohort audit, W04 SciFact, W05 official snapshots/keys/provenance | Main Bridge study ยังขึ้นกับ intended-use rights และ cohort/splits |
| HT-G2 | W06/W07 evaluator/grouping; W08/W09 offline cheap/fixed-hybrid baselines; W10/W11 code and permitted local comparisons | ต้องรัน method จริงและบันทึก complete costs; mock controller ไม่พิสูจน์ adaptive advantage |
| HT-G3 | W12/W13 real public device dossiers, local TH/EN viewer/edit/history/export | Synthetic smoke ไม่ครบ minimum 3 public cases หรือ usability evidence |
| HT-G4 | Protocol/code/analysis preparation และ offline experiments เมื่อ data/model พร้อม | W14 held-out adaptive comparison ต้องมี execution จริง ไม่ปิดจาก dry-run |
| HT-G5 | W16 task script/demo/offer preparation | W17 actual participants, repeated use และ purchase ยังไม่ได้เกิดขึ้น ห้ามอ้าง market validation |
| HT-G6 | W18 source-grounded background/methods และ reproducibility materials | Manuscript results/readiness ต้องพึ่ง W14/W15 และ evidence จริง ไม่รับประกัน WPI acceptance |
| HT-G7 | W19 locally operable release/build/runbook/testing | Local readiness ไม่ใช่ deployment/production validation |
| HT-G8 | W20 inventory เฉพาะเมื่อ core stable และ branch/task มีเหตุผล | Optional expansion ไม่ควรบล็อกหรือขยาย main medical-device study |

W15 SciFact component evaluation ทำ offline ได้เมื่อ adapter/model/labels/evaluator พร้อมตาม task จริง Test labels ของ official setting ไม่เปิดตาม upstream README; อย่าเรียก dev score ว่า reproduced official held-out score ไม่มี expert recruitment gate สำหรับ engineering ที่ระบุ แต่ไม่สร้าง independent clinical/legal validation จาก owner/LLM review

## Acquisition safeguards

เริ่ม permitted SciFact claims/abstracts และ selected FDA named-device records เก็บ exact revision/source date/bytes/hash/rights แยก raw กับ normalized พร้อม split/group keys เพิ่มข้อมูลได้เมื่อช่วย acceptance/coverage แต่ประเมิน free disk, batch cap และ streaming/resume ก่อน ไม่ลง full UDI/large patent corpus เพียงเพื่อจำนวนครบ

Bridge rights ต้องชัดก่อนการใช้ที่ได้รับผลกระทบ; paper CC BY ไม่ license dataset GMDN/D&B enrichment ต้องงดเมื่อไม่มีสิทธิ์ BioASQ registration/terms ที่ยังไม่รับเป็น dependency เฉพาะ branch Raw data/PDF/restricted data อยู่ local; เผยแพร่ metadata/loader/config/authored fixtures ที่มีสิทธิ์แทน ไม่อ่าน .env/auth/session stores หรือเปลี่ยน global tools

## คำสั่งที่มีจริงและตรวจแล้ว

```powershell
rtk proxy python -B scripts/healthtech/verify_offline.py <fresh-output>
rtk proxy python -B scripts/healthtech/run_dossier.py examples/healthtech/synthetic-device/input.json <fresh-output>
rtk proxy python -B scripts/run_provider_pilot.py --dry-run --spend-cap 0
rtk proxy python -B scripts/dispatch_provider_pilot.py
```

สองคำสั่งท้ายผ่านด้วย status `DRY_RUN_NOT_EXECUTABLE` และ `READY_AWAITING_FUNDING_AND_BUDGET_APPROVAL` ตามลำดับ โดยไม่อ่าน key หรือเรียก paid API เป็น **historical transport preflight** ยังไม่ยืนยันว่า HT-B4/HealthTech API request ถูกเชื่อมแล้ว Future long run ต้องเพิ่ม HT-specific config/request seam และ fake-transport/schema/visibility checks ที่ขาดก่อนอ้าง HT dry-run readiness ไม่ใช้ `--live` หรือ historical spending cap เป็น permission ใหม่

รอบนี้ตรวจ public regression หลัง correction จาก clean Git snapshot ได้ 262/262 ไม่มี skip รวม HealthTech 27 และ provider/budget/security 106 กรณี รายละเอียด module/commands อยู่ใน audit ไม่เพิ่ม tests count จาก untracked local work
