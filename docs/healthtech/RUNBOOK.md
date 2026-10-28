# HealthTech local runbook

ใช้ Python 3.12+ และ dependencies ใน `pyproject.toml` ตัวอย่างนี้ไม่เรียกเครือข่าย ไม่โหลด `.env` และไม่ใช้โมเดล

```powershell
python -B scripts/healthtech/run_dossier.py examples/healthtech/synthetic-device/input.json results/healthtech/demo-001
python -B -m pytest -p no:cacheprovider tests/test_healthtech.py
```

เลือก output directory ใหม่ทุกครั้ง Runner จะปฏิเสธ directory ที่มีอยู่แล้ว ผลประกอบด้วย `dossier.json`, `dossier.md`, `acquisition_events.jsonl` และ `manifest.json` แฟ้ม Markdown เปิดตรวจ/แก้ได้ตามปกติ ส่วน `user_edits`, parent/version เป็นสัญญาข้อมูลที่เตรียมไว้ ยังไม่มี UI หรือบริการจัดเก็บประวัติ

Input แบ่ง `query`, แหล่งข้อมูลที่อนุญาต, corpus สิทธิบัตร, evidence และ policy. ใน synthetic `run_dossier.py` เดิม `HT-B0a` ใช้ company/metadata query เป็น control, `HT-B0b` ใช้ technical query เดียว, และ `HT-B1` ยังคงเป็น legacy token-overlap approximation; อย่าใช้ slice นี้แทน G2 strong baseline. สำหรับ real public-cohort comparison ให้ใช้ `scripts/healthtech/run_real_baselines.py`: `HT-B0a` company control, `HT-B0b` deterministic BM25, `HT-B1` BM25+dense retrieval+RRF+actual local cross-encoder, `HT-B2` fixed technical/features schedule with the same representations, and `HT-B3` transparent observable continuation/stop heuristic. `HT-B3` is development evidence only, not a final G4 adaptive result

Budget ใน slice นี้นับ calls และจำนวนผลที่คืนรวมทุกครั้ง แม้ผลซ้ำก็ใช้ทรัพยากร เหตุผลหยุดไม่สื่อว่าค้น patent ที่เกี่ยวข้องครบแล้ว `paid_cost_usd=0` เพราะไม่มี paid action ไม่ใช่การประมาณราคางานจริง เวลา total รวมสร้าง index; event times เป็นเวลาค้นเท่านั้น

Source payload hash ใช้ SHA-256 ของ canonical UTF-8 JSON (`sort_keys=True`, compact separators, `ensure_ascii=False`) แม้ payload เป็นข้อความ ไม่ใช่ raw-file hash ทุก source ต้องระบุ revision, jurisdiction, source date และ synthetic flag ข้อความใช้ `chars:start:end` ตาม Python Unicode offsets; structured field ใช้ `field:name` และตรวจชนิด/value ตรงกัน

ค่าจาก local openFDA 510(k) snapshot เก็บเฉพาะ core device/decision fields ที่อยู่ใน allowlist และเก็บ decision code ตามต้นทาง ไม่แปลงเป็น PMA approval หรือ clinical endorsement ยังไม่มี network fetcher การเปลี่ยน snapshot ต้อง pin revision/hash/date ใหม่ ค่า source_date ของ adapter นี้คือวัน snapshot/retrieval ไม่ใช่วันที่ตัดสินของ FDA ซึ่งยังอยู่ใน payload เดิม

Evaluator HT-T1 อ่าน references แยกผ่าน `evaluate_known_links` ให้ expected query IDs, corpus universe, predictions และ statuses ล่วงหน้า Query ที่ missing/failed ได้ 0; reference-empty แสดงเป็น excluded/unjudged unknown IDs กินลำดับแต่ไม่เป็น hit dedup canonical IDs ก่อน K; ไม่คำนวณ open-world precision/F1 ไม่มี official SciFact evaluator ใน slice นี้

Schema สร้างซ้ำได้ด้วย:

```powershell
python -B scripts/healthtech/export_schemas.py schemas/healthtech
```

`scripts/healthtech/run_api_dry_run.py` ตรวจ HT request/config/schema/source visibility โดยไม่เปิด network. `HealthTechAPIConfig(mode="mock")` ใช้ได้เฉพาะ injected `MockHTTPTransport`; `mode="live"` ปิดตายในการ pre-live package. Live providers ต้องใช้ adapter/ledger/explicit env loader เดิมพร้อม authorization ที่ครอบคลุมรอบนั้น และต้องนับ controller/query/retry/rerank costs ครบก่อนเรียก paid action

ตรวจ public release cohort จาก clean checkout ได้ด้วย `python -B scripts/healthtech/verify_offline.py <fresh-output>`. `--suite public` ระบุ published regression modules รวม HealthTech และ provider budget/security guards; `--suite all` ใช้ pytest discovery ใน `tests` directory ของ checkout ปัจจุบัน. The current clean tracked checkout at `HEAD` passes 275 tests with zero failures/errors/skips, zero network attempts, zero credential-file reads, zero provider calls and zero paid cost. Neither suite uses local provider journals

สำหรับ HT-G1/G2 development run ใช้ cohort ที่มี manifest และ runtime/evaluator separation ชัดเจน:

```powershell
python -B scripts/healthtech/run_real_baselines.py --runtime results/healthtech/ht-public-cohort-20261028-r1/runtime.json --references results/healthtech/ht-public-cohort-20261028-r1/evaluator/references.json --groups results/healthtech/ht-public-cohort-20261028-r1/groups.json --model-root data/raw/healthtech/models --output <fresh-output> --code-commit <scoring-code-commit> --protocol-hash <protocol-hash> --cohort-manifest-hash <cohort-manifest-hash>
```

The run records raw ranked IDs, all attempts, per-device/group results and offline resource units. It is a development-only public disclosure experiment: no final holdout, exhaustive-recall claim, clinical/FTO conclusion, live provider call or paid cost is implied.

Paired-provider behavior tests สร้าง prior journal จำลองผ่าน fake transport ใน tmp ของแต่ละ test ส่วน frozen plan/payload hash test ยังตรวจ config ต้นฉบับโดยไม่แก้ ไม่มีการเผยแพร่ journal เดิม ดู [reproducibility audit](REPRODUCIBILITY_AUDIT.md) สำหรับเหตุผลที่ receipt ก่อนหน้าเลือก 185 เทียบกับ 262 และ correction ที่ทำ
