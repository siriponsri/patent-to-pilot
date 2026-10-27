# Pepo → Luna: G10 audit และ offline pilot readiness
วันที่ 27 ตุลาคม 2026 · เตรียมให้รับช่วงประมาณ 18:00 น. เวลาไทย
สถานะ **G10_BOUNDED_AUDIT_PASS / NEW_READINESS_READY_FOR_LUNA_REVIEW / SCIENTIFIC_LIVE_BLOCKED**

## สิ่งที่เสร็จจริง

1. อ่าน repo/GOAL/handoffs และ skills ที่เกี่ยวข้องบนเครื่อง DESKTOP-C8EHASQ จริง Git status/log อ่านได้โดยไม่แก้ ownership/ACL HEAD ที่อ่านตอนเริ่มคือ `373a135` ไม่ได้ตรวจ remote/CI ในงานนี้
2. ตรวจ G10 candidate `g10-correctness-search-2026-10-27-r1` อิสระ: **57 tests ผ่าน** (G09/G10/G11), source binding 5/5 และ output hashes 7/7 ตรง manifest
3. รัน comparison อิสระใน run ใหม่: PASS, 9 mock calls, $0; B4 ยังคง NOT_IMPLEMENTED/NOT_RUN, POOL_NOT_READY
4. เพิ่ม readiness/preflight แบบ additive โดยไม่แก้ comparison, integration, adaptation หรือ frozen fixtures เดิม ชุดล่าสุด **36 tests ผ่าน**: G10 20 + readiness 16 ไม่ใช่ independent samples
5. CLI preflight ตัวจริงผ่าน: 3 exposed dev cases/15 current states; calibration 3 positives+7 negatives; provider calls 0, API cost $0; scientific_live_ready=false อย่างตั้งใจ
6. ทุกชุดใช้ no cache/bytecode, pytest plugin autoload disabled และ Python socket/DNS gate ไม่พบ network attempt ไม่อ้าง system-wide packet capture
7. source/หลักฐาน protected ไม่เปลี่ยนระหว่าง audit รอบแรก และตรวจซ้ำตอนปิดใน `final-manifest.json` ดูผลจริงในไฟล์นั้น

## รับอะไรได้ และยังรับอะไรไม่ได้

**รับ G10 bounded mechanics ที่แก้ F1-F4 ได้** ตาม independent 57-test run และ fresh run:
- F1 P wrapper ใช้ staged current inputs
- F2 ตรวจ actual mapped runtime output แยกจาก domain/evidence checks
- F3 persistence เป็น NOT_RUN ไม่ใช้ default success แทน real roundtrip
- F4 แยก attempt/state/validation/skip accounting และ retain generator failures

ยังไม่ใช่ full G10, fair live model comparison, model quality, scientific utility หรือ cross-task learning ผล live echo เก่าเป็น transport evidence เท่านั้น ไม่รันซ้ำหรือรีเซ็ต history

Code ใหม่ของ Pepo ทดสอบแล้วแต่ยังเป็น **READY_FOR_LUNA_REVIEW** ไม่อ้างว่าเป็น independent review ของโค้ดที่ Pepo เขียนเอง ให้ Luna review เฉพาะ additive diff นี้ ไม่ต้อง global audit/เปิด G09/G10/G11 ที่รับไว้ใหม่

## ไฟล์ใหม่ที่รับช่วง

- `src/patent_to_pilot/evaluation/pilot_readiness.py`: dev inventory/staging, family/template split checks และ actual positive/negative calibration
- `scripts/run_g13_offline_preflight.py`: offline-only CLI ไม่มี key/live switch
- `scripts/run_offline_verification.py`: fixed test cohorts, fresh outputs, socket gate, source-before/after receipt
- `tests/test_g13_readiness.py`: read-set, nested packet/profile/schema leakage, split overlap/provenance, positives, false outputs, overwrite/live rejection
- `configs/g13-offline-plan-v1.json`: offline plan และ unapproved model-calibration proposal แยกชัด
- `methodology/evaluation/readiness-20261027/dataset-readiness.json`: data rights/provenance/packet hashes; existing registryไม่เปลี่ยน
- `docs/research/G13_OFFLINE_READINESS_20261027.md`: methods, splits, pilot design, pricing assumptions, cap/stop gates
- handoff นี้

Evidence:
- `results/development/pepo-readiness-20261027-r1/`: before/after hashes, 57-test XML/log, independent comparison, audit-result
- `results/development/pepo-readiness-20261027-r1/readiness-tests/`: final 36-test XML/log/source stability
- `results/development/g13-preflight-20261027-r1/`: actual CLI output, staged current inputs, 10 calibration controls และ network-guard receipt
- `results/development/pepo-readiness-20261027-r1/final-manifest.json`: final source/evidence binding และ protected invariance

ไม่บวกจำนวน tests สองชุดเป็นจำนวน independent experiments และไม่ใช้ synthetic mutation controls เป็น expert gold

## Dataset และ next case curation

สามเคสเดิมเป็น exposed development ทั้งหมด ไม่มี held-out case ที่นำมาอ่านเพื่อ tune รอบนี้
PTP-0001 family mapping unknown; PTP-0001/0002 แชร์ role-toggle template; PTP-0003 เป็น count-definition cluster Profiles A/B/C เป็น fictional และแชร์ public NCATS context ไม่อ้าง independent companies
เพิ่ม independent source cases 0 ไม่แต่ง facts ให้ครบ target 10 เพิ่มเฉพาะ calibration/test coverage ที่มีต้นทางตรวจได้

ให้ Luna เลือก source/familyใหม่จาก acquired permitted dataแบบ bounded ตรวจ witness/offset/version/rightsก่อนสร้าง next case แล้วกำหนด component/splitก่อนvariants เก็บ final panel ไม่ให้ถูก tuning/feedback อย่าเปลี่ยนชื่อเคส dev แล้วเรียก held-out

## สิ่งที่ block scientific execution จริง

1. Comparison runner ยังมี mock generator ไม่ใช่ live common response adapter
2. PTP-0002/0003 ยังไม่ใช้ common PTP-0001 comparison output contract/B2 adapter; อย่าฝืน schemaเพื่อให้นับครบ
3. P_existing_workflow ไม่ใช่ full scientific P; G11 เป็น full-generator-then-scoped-merge ต้องคิดต้นทุนตามนั้น
4. current staged folders เป็น curator material ไม่ใช่ OS/process isolation ต้องไม่ให้ evaluated worker อ่าน sibling future states/evaluator repo
5. ไม่มี verified shared recovery/distractor pool สำหรับ B4 ไม่ fabricate pool/results
6. ไม่มี verified input tokenizer+schema/framing upper bound; Gemini public endpoint recheck ไม่สำเร็จผ่าน web toolในรอบนี้ ต้องตรวจใหม่ก่อน live
7. ไม่มี approval ใหม่สำหรับ exact scientific payload/matrix/spend การอนุมัติ echo เดิมและเครดิต $10 ไม่ใช่อำนาจรัน pilot

ข้อเสนอ G13-A ในเอกสารคือ 18 attempts สูงสุด, zero retries, 1 dev repetition, capเพิ่ม $1 หลัง prerequisites/explicit approval เป็น calibration ไม่อ้าง efficacy/algorithm superiority และ capอาจหยุดก่อนครบหากใช้ full-context reservations ไม่มี live command ที่อนุมัติแล้วใน handoff นี้

## คำสั่งรับช่วงที่เล็กที่สุด

จาก repo root:

```powershell
python -B scripts/run_offline_verification.py --suite readiness --output-dir "$env:TEMP/ptp-readiness-luna-20261027-01"
python -B scripts/run_g13_offline_preflight.py --plan configs/g13-offline-plan-v1.json --output-dir results/development/g13-preflight-luna-20261027-01
git diff --check
```

เลือกชื่อ output ใหม่หากมีอยู่ ห้าม overwrite results/history และไม่จำเป็นต้อง rerun 57-test cohort เดิมจาก prose edit หากมีแก้ code ที่เกี่ยวข้องให้เลือก affected suite ตามจริง

หลัง targeted review ให้ทำ current common scientific adapter/isolation/case curation เฉพาะ scope ที่ผู้ใช้อนุมัติ หากต้องเปลี่ยน protected integration/adaptation/frozen protocol ให้เสนอ concrete diff ของส่วนนั้นก่อน ไม่แอบแก้ baseline

## สิ่งที่รักษาไว้

ไม่แก้ original Phase A journal, historical G10 evidence, G11 adaptation, frozen evaluation, docs/research/pilot-next/, delivered ZIPs, README, Flint setup หรือ credentials
.gitignore และ pyproject.toml มี dirty changes อยู่ก่อนเริ่ม ไม่ใช่งานของ Pepo อย่า stage รวมเอง
.pytest_cache ถูกปฏิเสธการอ่าน; ไม่ retry/ลบ/เปลี่ยนสิทธิ์ ใช้ no cache + fresh temp แทน
Git ownership ไม่ถูกแก้ ไม่มี safe.directory/ACL change ไม่อ่าน denied external preflight และไม่อ่าน .env
ไม่มี commit/push/deploy/API/GPU ในงานนี้ Luna ดูแล final scoped combined commit/push ตาม owner authorization เดิม โดยตรวจ intended remote/upstream, secrets, diff และ CI ของ exact commitก่อนรายงานสำเร็จ ห้าม git add . หรือรวม unrelated dirty files

## Startup prompt สำหรับ Luna

> GOAL prompt — ทำงานต่อที่ C:\Users\User\Desktop\myProject\patent-to-pilot อ่าน AGENTS.md และ docs/handoff/PEPO_TO_LUNA_20261027_TH.md ก่อน พร้อม final-manifest.json ที่อ้างในเอกสาร ตรวจรับ additive readiness code ของ Pepo แบบ targeted แล้วต่อ case/evaluator/live-adapter/isolation readiness ตาม actual blockers อย่าเปิด audit loop ของ G10 ที่รับแล้ว อย่าอ่าน key/เรียก API/ใช้เงินจาก approval echo เดิม อย่าแก้ protected history/frozen fixtures/G11 adaptation/docs research pilot-next หรือ ZIPs และอย่าทำ UI ที่ Claude รับผิดชอบ เก็บผล PASS/FAIL/BLOCKED/NOT_RUN ตามจริง เลือก fresh run directories เสมอ เตรียม exact next payload/matrix/cap ให้ owner review เมื่อ engineering gatesครบ แล้วค่อยขอ paid approval ถ้าจำเป็น ทำ scoped commit/push เฉพาะเมื่อ diff/tests/rights/secrets/remote พร้อมตามอนุมัติเดิม
