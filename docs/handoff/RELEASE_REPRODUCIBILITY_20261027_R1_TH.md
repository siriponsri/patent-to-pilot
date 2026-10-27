# Release reproducibility checkpoint — 27 ตุลาคม 2026 รุ่น 1

ต่อจาก [offline long-run closeout](PEPO_OFFLINE_LONG_RUN_V2_CLOSEOUT_TH.md) และ [Luna GOAL](LUNA_LONG_RUN_V2_20261027_TH.md)
นี่เป็น engineering reproduction เท่านั้น ไม่ใช่ scientific validation หรือการปลด live gates

## สิ่งที่พบจาก remote จริง

Clone แยกของ `66be5b2a086a273d0a9110cae01349e4c9d44cb3` ไม่มี `.env` ใช้ venv ใหม่ ติดตั้ง `.[test]` จาก official PyPI ตาม README และ `pip check` ผ่าน ไม่อาศัย packages/ไฟล์ที่ไม่อยู่ใน Git ของ working tree เดิม

Baseline cohort 137 tests: 117 ผ่าน, 4 failures, 16 setup errors ไม่ได้ถือว่า 86 tests ในเครื่องเดิมพิสูจน์ clean checkout ได้แล้ว
Workflow, G10 comparison, default provider dry-run และ preflight v2 รันได้ แต่ G13 v1/stage bundle checks ยังไม่ครบ

## Defects และ narrow repair

1. `evaluation/pilot_readiness.py:114` อ้าง `methodology/evaluation/splits/g06-dev-assignments.json` ที่ยังไม่ track
2. `pilot_readiness.py:136` ต้องใช้ `PTP-0002/public-input/output-schema.json` และ `PTP-0003/public-input/output-schema.json` ที่ยังไม่ track
3. `tests/test_g13_stage_boundary.py:14` ยืม bundle จาก `results/development/g13-preflight-20261027-r1/` ทำให้ทุก test ที่ใช้ fixture พังเมื่อไม่มีประวัติ local run

Repair: track development metadata/public shape contracts ทั้งสามแบบ **ไม่เปลี่ยน bytes** และสร้าง boundary fixture จาก current tracked packet/profile + public output contract ใน TEMP แทนผลรันเก่า
ไม่มีการเผยแพร่ evaluator answers, future events หรือ frozen held-out examples และไม่มี assertion/negative control ถูกลบหรือลดความเข้ม
Production adaptation/comparison/provider ledger ไม่ถูกแก้

## Candidate checks ที่ทำจริง

Candidate overlay บน clone เดิมมี **142 passed, 0 failures/errors/skips**
เพิ่ม 5 regressions: concurrent child processes, durable crash reservation, retry cumulative charges/idempotent settlement, unverified readiness flags และ rejection ของ live activation
คำสั่งครบ 6 รายการผ่าน: README workflow, G10 comparison, default provider dry-run, v2 preparation, G13 preflight และ stage verification
Generated corpus ยังเป็น SYNTHETIC 48 cases/24 families/4 template components; schemas 4ชนิด import/export ได้

Socket/DNS attempted0, original-workspace/.env read attempts0, provider calls0, API$0 ระหว่าง verification Source files ไม่เปลี่ยนระหว่างรัน
Child-process budget tests ปิด socket ของแต่ละ child เอง ไม่มี live transport/key
Venv ติดตั้ง pydantic2.14.1, jsonschema4.26.0, pytest8.4.2 ตาม version ranges ของ repo; เวอร์ชันอื่นใน published evidence manifest ไม่ใช่การอ้างว่า dependency ranges ถูก lock แล้ว

## Reproduce หลังติดตั้งจาก clean checkout

```powershell
$releaseCheck = Join-Path $env:TEMP ("ptp-release-" + (Get-Date -Format "yyyyMMdd-HHmmss-fff"))
$commit = git rev-parse HEAD
.\.venv\Scripts\python.exe -B scripts/verify_release_offline.py --source-commit $commit --output-dir $releaseCheck
```

ใช้ fresh output directory เสมอ Scriptคืน nonzero เมื่อ tests/commands/hash checks ล้มเหลว ไม่เปิด `.env` หรือ live mode
`--source-commit` เป็นค่าที่ผู้รันตรวจด้วย Git แยกต่างหาก ตัว script ไม่ได้ตรวจ `.git` เอง หากต้องห้ามการอ่าน workspace เก่า เพิ่ม `--forbid-root <original-repo>` ได้
Preflight scientific_live_ready ยังคง false แม้มีงบอนุมัติหรือ config อ้างว่า gates ผ่านเอง

## Access และข้อจำกัด

Git ที่เรียกใน Python test process ถูก `dubious ownership` เพราะ clone เป็นของ `User` แต่ process เป็น `CodexSandboxOffline` จึงหยุด operation นั้น ไม่เพิ่ม safe.directory/แก้ ACL/เปลี่ยน ownership หรืออ่าน GitHub CLI config ที่เคย denied
การตรวจ files ใช้ ordinary permitted source reads โดยไม่แตะ `.git`; file invariance ไม่ใช่ Git-index audit ใช้ authorized Git นอก test process ตรวจ remote/ref แยกต่างหาก
Dependency installation ใช้ PyPI network ก่อนปิด socket การทดสอบ offline ไม่อ้างว่า installation ใช้ network0

## Final remote verification

Candidate PASS ข้างต้นเป็น overlay ไม่ใช่การกล่าวว่า commit66be5b2ผ่านแล้ว ต้อง clone published repair commit ใหม่และรัน helper ซ้ำก่อนปิด clean-checkout acceptance
ผลสุดท้าย/commit/CI และ exact file hashes อยู่ใน versioned local artifact `results/development/release-reproducibility-20261027-r1/` และ final task report เก็บ baseline failure ไว้ ไม่เขียนทับประวัติ

Scientific adapter, isolated live worker, fresh prices/token bounds และ shared-budget dispatch integration ยังเป็นงาน Luna ตาม GOAL เดิม ไม่เพิ่ม UI/paid-run/deploy scope ใน checkpoint นี้
