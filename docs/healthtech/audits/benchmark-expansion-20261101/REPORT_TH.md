# Benchmark expansion checkpoint report — 1 พฤศจิกายน 2026

สถานะรวม: `PASS_OFFLINE_COMPONENT_RESULTS_READY_FOR_OWNER_REVIEW`

งานนี้เป็น continuation ของ goal Patent-to-Pilot O1–O4 เดิม ไม่เปิด goal ใหม่ และไม่รวมผลจากคนละ candidate หรือคนละ protocol เป็น PASS เดียว

## Candidate และขอบเขต

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-research-product-20261031`
- Branch: `codex/research-product-o1-o4-20261031`
- Candidate ที่ใช้ score ก่อนรัน: `cd7e5d364d529a001fc51f78c217c10d7d9c8945`
- Reviewed implementation candidate: `80da253969f7973cc630ce03ac83da9900f16628`
- Audit metadata base ก่อน provenance correction: `41e5923664921ba5d0b34d2084d015dadf6ab5ea`; การแก้รอบนี้เป็น documentation-only และไม่เปลี่ยน code, payload, score, push หรือ merge
- Source pack: `pepo-dataset-benchmark-expansion-20261101`; parent audit commit `f826069dddb74d4df9ca820a33c07355bec8b357`
- Raw payload และ row-level predictions อยู่นอก Git; ไม่เก็บ secret, key หรือ restricted payload ใน repository

## สถานะตามมิติ

| มิติ | สถานะ | หลักฐานและขอบเขต |
|---|---|---|
| Engineering | `COMPLETE` สำหรับ staged acquisition, integrity, freeze, deterministic runners และ receipts ของ component package | 5/5 files ผ่าน rights/version/size/hash/schema; focused tests `6/6`; scripts compile; diff check ผ่าน |
| Scientific evidence | `PARTIAL` | PANORAMA และ Helmers ให้ component/diagnostic evidence จริง แต่ยังไม่ประเมิน adaptive dossier superiority หรือ exhaustive device–patent relevance |
| Business validation | `PARTIAL / NOT_VALIDATED` | วัด machine-side operational potential ได้; ไม่มี external user validation, willingness-to-pay, revenue หรือ ROI |
| Manuscript readiness | `PARTIAL / OWNER_REVIEW_REQUIRED` | manuscript, supplemental addendum, WPI checklist และ cover letter draft ผูกผลใหม่แล้ว; ต้อง recheck official author instructions และ owner declarations ก่อนส่ง |

## Acquisition และ freeze

รับชุดข้อมูลตาม manifest เท่านั้น และ reuse DAPFAM/PatEmbed/multilingual-e5 vectors/rankings เดิมโดยไม่ดาวน์โหลดหรือ embed ซ้ำ

- Helmers `human_eval.zip`: 13,962,880 bytes, MD5 `83465f1a95805d963d4aabe085e2af98`
- PANORAMA 4 files: รวม 166,093,884 bytes; ทุกไฟล์ parse ด้วย `pyarrow`
- Application overlap ระหว่าง validation/test: PAR4PC `0`, PI4PC `0`
- Shared candidate IDs ข้าม official splits ถูกเก็บเป็น diagnostic: PAR4PC `149`, PI4PC `38`; ไม่ถูกลบหรือเรียกว่า leakage โดยอัตโนมัติ
- Gold/silver/negative fields ถูกกันออกจาก runtime ranking; unjudged ไม่ถูกแปลงเป็น negative
- `FINAL_EVALUATION_FREEZE.json` ถูกสร้างก่อน final component scoring และกำหนด endpoint, grouping, retry, cost และ stopping rules แล้ว ผลหลัง freeze ถูกผูกกับ pre-run scoring candidate, reviewed implementation candidate, protocol hash และ result hashes ใน [`FINAL_EVALUATION_BINDING.json`](FINAL_EVALUATION_BINDING.json) และ [`CHECKPOINT_V6.json`](CHECKPOINT_V6.json)
- Freeze file คงสถานะ pre-run เดิมไว้เพื่อรักษาความไม่เปลี่ยนรูป; `FINAL_EVALUATION_BINDING.json` เป็น post-run record ที่ยืนยันผลจริงหลัง freeze

## ผลรันจริง

### PANORAMA lexical baseline

เป็น CPU deterministic option-ranking baseline ที่ใช้ context และ candidate options ของแต่ละแถวเท่านั้น

| Task | Split | Rows | Macro gold hit@1 | Failed-output rate | Machine time/row |
|---|---:|---:|---:|---:|---:|
| PAR4PC | validation | 3,029 | 0.733575 | 0.0 | 0.013497 s |
| PAR4PC | test | 2,896 | 0.715124 | 0.0 | 0.013348 s |
| PI4PC | validation | 3,937 | 0.377699 | 0.0 | 0.002704 s |
| PI4PC | test | 3,402 | 0.401235 | 0.0 | 0.002343 s |

ผลนี้ตอบคำถาม component option/paragraph selection เท่านั้น ไม่ใช่ผล adaptive evidence acquisition ของ dossier และไม่ใช่ device–patent semantic gold

### Helmers diagnostic

- 10 target patents, 450 judged pairs, 258 positive pairs
- Term-count cosine diagnostic: macro AP `0.885450`, macro AUC `0.880012`
- เป็น selected judged pool ของ source authors; ไม่ใช่ independent global sample, exhaustive recall หรือ modern official dev/test split

## การตรวจสอบซอฟต์แวร์

คำสั่งและผลจริง:

- `python -m pytest -q tests\test_healthtech_benchmark_expansion.py` → `6 passed`
- `python -m py_compile scripts\healthtech\acquire_benchmark_expansion.py scripts\healthtech\download_ranges.py scripts\healthtech\run_panorama_lexical_baseline.py scripts\healthtech\run_helmers_diagnostic.py` → `PASS`
- `git diff --check` → `PASS`
- `python -m pytest -q` → exit code `0`; one existing skip observed

มี stale partial file ขนาด `35,309,248` bytes อยู่นอก Git ที่ `.../PI4PC/test.parquet.part` การลบถูก shell guard ปฏิเสธ จึงเก็บเป็น cleanup limitation และไม่ใช้ไฟล์นี้เป็น input

Literature metadata/public links are preserved in `LITERATURE_INDEX.md`; local reading PDFs remain outside Git. Live WPI pages returned HTTP 403 in this environment, so the checklist remains owner-recheck-required.

## ขอบเขตข้ออ้าง

ผลนี้สนับสนุนว่า acquisition, rights/hash/schema verification, freeze และ deterministic component baselines ทำซ้ำได้บน candidate นี้ ผลยังไม่สนับสนุน:

- adaptive superiority หรือ quality-cost superiority ของ dossier system
- exhaustive recall, semantic relevance, clinical suitability, FTO, patent validity หรือ investment merit
- independent user validation, customer demand, willingness-to-pay, revenue หรือ ROI
- journal acceptance หรือ permission ให้ส่งบทความแทน owner

External business validation ยังคง `NOT_VALIDATED` ตาม solo-project decision และไม่เป็น gate ของ offline engineering หรือ manuscript work รอบนี้

## Selected manifest extension

หลัง core acquisition มีการรับไฟล์ขนาดเล็กตาม manifest เพิ่มโดยไม่โหลด DAPFAM ซ้ำและไม่ re-embed vectors เดิม:

- PatSnap claim-charting: 30 Parquet rows, hash/schema ผ่าน; เก็บเป็น optional diagnostic และยังไม่ score
- PatentsView AIR-UMASS/NBER: 185,250 และ 216,847 CSV rows, Git blob hash/schema ผ่าน; สิทธิ์ standalone ของ benchmark data ยังไม่ยืนยัน จึงไม่ใช้ทำคะแนนหรืออ้างเชิงพาณิชย์
- AffRoDB: 1,374 JSONL rows, MD5/schema ผ่าน; ยังไม่มี ROR v1.40 snapshot จึงยังไม่คำนวณ organization-linkage score

รอบแรกของ verifier ตีความ `git_blob_sha1` เป็น raw SHA-1 ทำให้ reject ไฟล์ PatentsView หลังดาวน์โหลด แต่ไม่ได้ใช้ไฟล์นั้นในการ score; แก้ semantics แล้ว rerun จาก bytes เดิมจนผ่าน และเก็บ failure ไว้ใน `SELECTED_ACQUISITION_FAILURES.json` ตามหลักฐานจริง

ไม่มี final endpoint/split ใหม่สำหรับชุด optional/conditional นี้ จึงไม่อ้างผลเปรียบเทียบเพิ่ม; freeze และผล PANORAMA/Helmers เดิมยังคงเป็น component evidence ของ candidate เดิม

## Next checkpoint

Owner review reviewed implementation candidate นี้ก่อน push/merge และตรวจ official *World Patent Information* aims/scope กับ Guide for Authors ล่าสุดก่อน submission หลังจากนั้น หากจะทำ adaptive final study ให้ตรึง matched cohort, group split, endpoint และ fair-budget controls แยกเป็น audit ใหม่ โดยคง paid/API branch และ canonical ledger gates เดิม
