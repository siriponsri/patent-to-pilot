# G10 correctness/search closeout

วันที่: 2026-10-27
สถานะ engineering: `READY_FOR_PEPO_AUDIT`
สถานะ combined publication: `PUBLISH_BLOCKED` จนกว่าจะมี Pepo handoff ที่ประกาศ `DOCS_READY_FOR_LUNA`

## ขอบเขต

งานนี้เป็น offline correctness/search-readiness slice บน public PTP-0001 เฉพาะ `S0 -> S1 -> S2` ไม่มี model/API/GPU/RunPod, paid call, UI, deploy, corpus expansion, frozen fixture edit หรือ evaluator-only input.

ไม่แก้ `README.md` และไม่แก้ `docs/assets/patent-to-pilot/`; พื้นที่ดังกล่าวยังเป็นความรับผิดชอบของ Pepo.

## W1-W11 disposition

| Work item | ผลลัพธ์ |
|---|---|
| W1 | PASS: อ่าน current handoff, source boundary และ protected prior evidence |
| W2 | PASS: แก้ F1 ให้ P wrapper ใช้เฉพาะ `self.stages` ผ่าน `run_state(stage.loaded)` |
| W3 | PASS: เพิ่ม bounded runtime contract และตรวจ actual mapped output แยกจาก domain/evidence validation |
| W4 | PASS: แยก persistence ออกจาก domain evaluator; comparison reports `NOT_RUN` และไม่อ้าง durable persistence |
| W5 | PASS: แยก execution/validation/skip/failure accounting; จับ generator exception และ malformed output |
| W6 | PASS: เพิ่ม 14 negative/control assertions ครอบคลุม staged slice, schema, evidence, unknowns, persistence และ accounting |
| W7 | PASS: รัน targeted G09/G10/G11 suite `57 passed`; G10 file มี `20 passed` |
| W8 | PASS: สร้าง run ใหม่โดยไม่ overwrite historical evidence; old evidence และ paid journal hashes unchanged |
| W9 | PASS: สร้าง closeout, search-pool readiness และ source/dependency/output manifest |
| W10 | PENDING: รอ Pepo handoff สำหรับ README/assets พร้อม `DOCS_READY_FOR_LUNA` |
| W11 | BLOCKED: ยังไม่ stage/commit/push combined publication ก่อน W10 handoff และ remote audit |

## F1-F4 ที่ปิดแล้ว

- **F1:** `P_existing_workflow` ไม่เรียก `run_case(case_id)` และไม่มี full-case state/evaluation claims; test monkeypatch `run_case` ให้ throw แล้ว comparison ยังผ่าน.
- **F2:** runtime view `ptp-0001-comparison-view-v1` ถูก map จาก `IntegrationResult` แล้วตรวจ required fields, policy states, option IDs, evidence references และ explicit unknown shape. Domain/evidence validator อยู่คนละผลลัพธ์.
- **F3:** comparison เรียก evaluator ด้วย `sqlite_payload_read_back=False`, ลบ synthetic SQLite failure ออกจาก domain-only result และบันทึก persistence แยกเป็น `NOT_RUN` / `NOT_APPLICABLE`.
- **F4:** metrics แยก provider calls, failed attempts, failed states, validator failures, dependent skips, retries, mock cost และ timing. Timeout ไม่ถูกนับซ้ำ; dependent revision state เป็น `SKIPPED`; generator exception เก็บ bounded trace.

## Search boundary

`B4-RG` และ `B4-DR` ยัง `NOT_IMPLEMENTED` / `NOT_RUN`. Search readiness เป็น `POOL_NOT_READY`: มีเพียง evidence ใน active public packet, ไม่มี verified recoverable-evidence pool และไม่มี distractor pool. ไม่มีการ fabricate candidate search results หรือดาวน์โหลด corpus ใหม่.

## Evidence

Run ID: `g10-correctness-search-2026-10-27-r1`
Output: `results/development/g10-correctness-search-2026-10-27-r1/`

- `comparison.json`, `comparison.md`, `comparison.html`
- `before-after-diff.json`
- `validator-results.json`
- `method-traces.json`
- `search-pool-readiness.json`
- `candidate-source-manifest.json`
- `evidence-manifest.json`

Run result: `PASS`; five methods passed; nine mock calls; mock cost USD `0.0000000`; retries `0`; declared network calls `0`, observation `NOT_MEASURED`.

Candidate source hashes:

| Path | SHA256 |
|---|---|
| `src/patent_to_pilot/evaluation/comparison.py` | `019bf3e0b48993ff7d39693546d818fe0d9cc17db83bd078d4335cff3bdba12e` |
| `scripts/run_g10_offline_comparison.py` | `2f63eb67f0439571b2491382dc79bd200d6a0a46db3f58ea44a4062749efbeff` |
| `tests/test_g10_offline_comparison.py` | `f72129520c3149448d91c923f1bdd8dd2cb13d0517e2333249c509c1333b5e4b` |

New output hashes and protected baseline hashes are recorded in `candidate-source-manifest.json`. The historical `results/development/g10-offline-comparison/` files and `results/development/provider-pilot/live.sqlite3` were rehashed after the run and remained unchanged.

## Verification

```text
python -B -m pytest -p no:cacheprovider tests/test_g10_offline_comparison.py -q
20 passed

python -B -m pytest -p no:cacheprovider tests/test_g09_g10_integration.py tests/test_g10_offline_comparison.py tests/test_g11_adaptation.py -q
57 passed

python -B -m compileall -q src scripts tests/test_g10_offline_comparison.py
PASS

git diff --check -- src/patent_to_pilot/evaluation/comparison.py scripts/run_g10_offline_comparison.py tests/test_g10_offline_comparison.py
PASS

python -B scripts/run_g10_offline_comparison.py
PASS; five methods; nine mock calls; new output directory
```

## Limits and next step

This evidence validates bounded implementation mechanics, contract enforcement and failure accounting only. It is not evidence of model quality, retrieval quality, scientific utility, feasibility, efficacy, safety, regulatory approval, patentability or FTO.

Next smallest action: receive Pepo's README/assets handoff, audit its paths/hashes and `DOCS_READY_FOR_LUNA` marker, then inspect remotes and stage only the explicitly reviewed candidate paths. Until then, do not commit or push the combined publication.
