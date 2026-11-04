# ผล audit และงานซ่อม O3 — 31 ตุลาคม 2026

แก้ช่องโหว่ในโค้ดและทดสอบแบบ offline แล้ว งานเตรียม O1–O4 เดินต่อได้ ส่วน paid dispatch ยังต้องรอประวัติ R1 ที่ reconcile ครบและข้อมูล availability ของ account/key ปัจจุบัน สิทธิ์เดิม USD8 ยังมีอยู่ ไม่ต้องอนุมัติซ้ำ และไม่ได้เริ่มงบหรือ clock 24 ชั่วโมงใหม่

## Candidate และขอบเขตที่ตรวจ

- Luna และ [Draft PR #2](https://github.com/siriponsri/patent-to-pilot/pull/2) อยู่ที่ `8b64ca09a4237a28ad121997985b081ca8781804` ขณะตรวจ PR ยัง open/draft และไม่ merged ดู `pr-state.json`
- งานซ่อมอยู่ที่ `C:/Users/User/Documents/Codex/2026-10-31/task-5/repair-candidate` บน branch `pepo/o3-safety-repair-snapshot-20261031` เป็น repo สำเนาของ source ที่อ่านได้ ไม่มี ancestry ของ PR ต้นทาง จึงส่งต่อเป็น patch ของ commit งานซ่อมเท่านั้น ห้ามนำ snapshot root commits ไป merge เข้า main
- การ clone จาก `C:/Users/User/Desktop/myProject/patent-to-pilot/.git` ถูก Git ปฏิเสธด้วย `detected dubious ownership` เพราะ owner เป็น User แต่ sandbox เป็น CodexSandboxOffline ไม่มีการเปลี่ยน `safe.directory`, ACL หรือ retry ผ่านทางลัด งานอ่าน source และแก้สำเนาที่เขียนได้ยังทำต่อได้
- ตรวจ source ของไฟล์เดิมที่แก้เทียบ baseline โดย normalize CRLF เพื่อแยกความต่างของ line ending ดู `source-baseline-binding.json` และ source hashes ใน `verification.json`
- ไม่อ่าน `.env`/key จริง ไม่เรียก account metadata หรือ paid generation ไม่ใช้ GPU ไม่แก้ journal จริง ไม่ push/merge/แก้ PR และไม่แตะ Luna/Claude/owner dirty files
- Parent ระบุว่าได้ส่ง configuration `gpt-6-astra`, thinking `xhigh` สำเร็จ รายงานนี้อ้าง configuration ที่ขอ ไม่อ้างว่าได้ตรวจ runtime identity แยกอีกครั้ง ใช้แนวทาง `kien-thai` ในเอกสาร ไม่มีการเรียกโมเดลภาษาไทยเพิ่ม

## ช่องโหว่ที่ทำซ้ำได้ และสิ่งที่แก้

หลักฐานก่อนซ่อมอยู่ใน `baseline-counterexamples.json` สร้างเฉพาะ synthetic files ใน temp และไม่มี transport/network call สคริปต์ `reproduce_repair_baseline.py` ใช้ source snapshot ก่อนซ่อมที่อยู่ใน workspace เดียวกัน

| ประเด็น | หลักฐานก่อนซ่อม | ผลหลังซ่อมและ source |
|---|---|---|
| Ledger ว่างผ่านเป็น canonical | register ไฟล์ 0 bytes ได้ แล้วเปิด R1 ledger และ reserve USD0.01 ได้ ทั้งที่ไม่มีประวัติ | `providers/ledger_registry.py:78` ตรวจ SQLite/namespace/identity/path/history review จริง และ `project_budget.py:183` ตรวจ registry ทุก reserve การเรียก component ตรงก็เปิด ledger ที่สองไม่ได้ |
| Policy hash คนละรูปแบบ | hash แบบ compact ของ registry ต่างจาก hash แบบมี spaces ที่เก็บใน SQLite | ใช้ `project_budget.py:39` สำหรับ durable authority แยกจาก `round1.py:99` ที่ยังผูก config ราย run กับราคา exact snapshot เปลี่ยนราคาใน DB เดิมได้โดยไม่ reset ยอด แต่ไม่ migrate hash เก่าหรือ journal จริงแบบเงียบ ๆ |
| Snapshot เก่าหรืออนาคตผ่าน | วันที่ปี 2000 และ 2999 ผ่าน normalizer เดิม | `providers/credit.py:35` ตรวจ UTC, freshness สูงสุด 300 วินาทีก่อน live dispatch, USD, account/key/authority, finite/nonnegative amounts และปัด availability ลง หนึ่ง hash ยืนยันได้เพียงความคงเดิมของ JSON |
| เครดิตก้อนเดิมถูกใช้ซ้ำ | gate เดิมเทียบ balance กับ run bound ครั้งเดียว ไม่มีการหัก exposure ข้าม run | `providers/credit.py:73` ตรวจใน transaction เดียวกับ reserve นับ bound ของคำขอหลัง snapshot และคำขอที่ยังไม่ settle ตอนเก็บ snapshot รวมการเปิดจากหลาย process แยก account credits, key limit และ project cap |
| Payload ที่ส่งไม่ตรง frozen messages | `parameters.messages` เขียนทับ messages ที่ bind ไว้ได้ | `providers/openrouter.py` ปฏิเสธการเขียนทับ model/messages/provider/response_format/tools/stream/max_tokens และ runner ยอมรับเฉพาะรูปแบบ non-thinking ที่กำหนด |
| เครดิตไม่ผูก key ที่ dispatch | identifier ในไฟล์ไม่รับรองว่าใช้ credential เดียวกัน | R1 บังคับ `key_scope=sha256:<digest>` และ transport ตรวจ fingerprint ของ credential ที่ใช้จริงก่อนส่ง ไม่พิมพ์ค่า key ทดสอบด้วยข้อความ synthetic เท่านั้น |
| Cost/ID หายหลัง output fail | receipt เดิมรวม debit จาก successful output เท่านั้น และไม่เก็บ provider generation ID | ledger เก็บ generation ID ก่อนตรวจ output, receipt อ่าน debit/state จาก ledger แม้ schema fail, unknown billing ไม่ถูกแทนด้วย known zero และเก็บเคสที่ยังไม่รันใน denominator ดู `healthtech/api_generation.py:281` |
| Token bound และ model snapshot | ใช้ UTF-8 length หาร 4 และ strict pricing schema กลับไม่รับ non-thinking fields ที่ runner ต้องใช้ | ใช้ byte upper bound พร้อม schema/framing และ reserve ตาม rate ceiling ที่ส่งจริง แยก pricing fields ออกจาก bounded runtime fields ดู `healthtech/api_generation.py:69` และ `:154` |
| สิทธิ์/field/hash ไม่ครอบคลุม payload | source label อย่างเดียวไม่ตรวจ query/association text; evidence dict รับ field เพิ่ม; library ไม่ตรวจ pack hash | allowlist evidence fields, ปฏิเสธ duplicate IDs, ตรวจ pack hash ที่ library boundary, ผูก non-synthetic transfer review กับข้อความจริงทุก field และเก็บ wire payload hash ตรงกับ ledger ดู `healthtech/generation_payload.py:56`, `:233`, `:309` |

ภายใน DB เดียวยังคง reserve ก่อน dispatch, `BEGIN IMMEDIATE`, settle ได้ครั้งเดียว, timeout/crash คง reservation และเมื่อค่าใช้จ่ายจริงเกิน bound จะเก็บยอดเต็มแล้วปิดการส่งครั้งถัดไป ไม่ clamp ค่าใช้จ่ายให้ดูอยู่ในงบ

## สิ่งที่ Luna แก้ไว้แล้ว

- `docs/healthtech/audits/ht-research-product-20261031/o3-gate.json:57` เปลี่ยน authorization เป็น `APPROVED_EXISTING_OWNER_SCOPE` แล้ว แต่ PR description ยังเรียก exact spend authorization ว่าเป็นสิ่งที่ขาด มีข้อความร่างให้แก้ภายหลังใน `PR_BODY_DRAFT.md` งานนี้ไม่ได้แก้ PR
- Validator ตรวจ candidate classification ให้ตรง association status และปฏิเสธ candidate นอก preview แล้ว regression เดิมยังผ่าน ไม่เพิ่ม expert-gold gate
- มี shared messages และ API generation runner จริงในระดับ CLI/library พร้อม mock integration แล้ว ยังไม่มี actual API paired comparison และ HTTP API provider ยังปิดอยู่
- O4 แก้ตารางเป็น Stryker holdout reference แล้ว แต่ท้ายรายงานยังกล่าวว่า O3 เป็น blocker เดียว จึงแก้ข้อความส่งต่อให้ชัดว่า O4 research ยังขาด matched current-cohort comparison และ per-job provenance

## Journal ที่ Luna พบ และการกู้ต่อ

อ่านเฉพาะสอง path ที่ระบุใน recovery receipt ไม่ scan Documents/Desktop ซ้ำ:

- `_preserved-main-untracked-20261030/results-development-provider-pilot/live.sqlite3`: 2 attempts, SHA256 `a10f81d79a37a39b53547cb4417437499aa81b69a896048f352ff3a8ba8e9d36`
- `paired-revalidation-1.sqlite3`: 2 attempts, SHA256 `f6943c6b99b999f88e5df839e35c15bd86119cb19a89ab4507d61b40d7de9fcb`

hash ตรงกับ receipt เดิมและไม่เปลี่ยนหลังอ่าน ยังเป็น legacy pilot รวม USD0.0001464 ตาม `docs/handoff/LUNA_CLOSEOUT_EVIDENCE.json` ลงวันที่ 26 ตุลาคม ไม่ใช่หลักฐานยอด R1 ครบทั้งหมด ใน reservation และ top-level response ID fields ที่ตรวจ ไม่พบ provider generation ID ที่ใช้ lookup ได้ ไม่อ้างว่าได้ค้นทุก log หรือ nested response field ทั้งเครื่อง ดู `recovered-journals-bounded-check.json`

เพิ่ม `scripts/healthtech/inspect_r1_history_export.py` สำหรับตรวจ sanitized all-attempt export โดยไม่แก้ DB ตรวจ duplicate/conflicting IDs, mixed scope/currency/mock history, invalid amounts, missing counts, exact phase/model/provider และคง unresolved reservation ผลสูงสุดคือ `CONSISTENT_EXPORT_ONLY` ไม่ใช่ completeness proof และไม่ทำ import/activate

`budget_history_anchor` เป็นบันทึก reconciliation ใน trusted local application state ต้องมาจากการตรวจหลักฐานจริงและหยุด old writers แล้ว ไม่มี API ใน patch นี้ที่รับ export แล้วสร้าง anchor ให้อัตโนมัติ `review_reference`, hash หรือคำว่า reviewed ไม่ใช่ลายเซ็นจาก provider และห้ามคัดลอก fixture ใน tests ไปใช้เป็นหลักฐานเงินจริง การออกแบบ migration/activation กับ journal จริงยังต้องอาศัย schema และหลักฐานที่กู้ได้ก่อน

## READY และ BLOCKED ที่เหลือ

**READY:** patch และ regressions แบบ offline, การตรวจ consistency ของ export, การเตรียม field-level rights projection, การตรึง paired messages, การเตรียม matched fixed/adaptive study และการแก้ checkpoint ให้แยก engineering/research ตามจริง

**BLOCKED เฉพาะ paid branch:** ยังไม่มีหลักฐานที่ยืนยัน historical R1 actual + unresolved exposure ครบ และยังไม่มี current scoped account/key observation จากช่องทางที่ได้รับอนุญาต การหา canonical path และทำ manifest เป็นงาน implementer ไม่ใช่ให้ owner แต่งเอกสารใหม่

เมื่อข้อมูลมีครบ ผู้ implement ต้องตรวจ writers ทุกตัวที่เคยใช้ authority นี้ให้หยุดหรือถูกปิดสิทธิ์ในระดับ application, reconcile/import โดยรักษาทุก attempt และคง unresolved, ผูก registry เดียว, ตรวจ real credential scope ผ่าน approved runtime และ refresh route/rights/credit ก่อน canary ห้ามตั้ง ledger ใหม่เป็น zero เพื่อผ่าน gate

credit snapshot เป็น availability observation ที่ผู้ส่งรายงาน ไม่ใช่การรับรอง authenticity หรือ project spend แม้ผ่าน check แล้ว การใช้บัญชีเดียวกันจากระบบอื่นยังทำให้เครดิตเปลี่ยนได้ ระบบนี้ไม่รับประกัน account-wide availability และไม่รับประกัน lifetime exposure ของ old writers/ประวัติที่ไม่ทราบ การแก้เฉพาะ checkout นี้ไม่ได้ถอนสิทธิ์ process หรือ checkout เก่า

ถ้าต้องถาม owner หลังใช้ข้อมูลที่มีแล้ว ให้ถามเฉพาะแหล่ง all-attempt/account export ที่ครอบคลุมช่องว่างของ R1 และช่องทางดูเครดิต/key limit ปัจจุบัน ห้ามถาม USD8 ซ้ำ ห้ามขอ new key/top-up และห้ามให้ส่ง secret

## การตรวจและการส่งต่อ

คำสั่ง ผล test จำนวน pass/skip/warnings, code commit และ hashes อยู่ใน `verification.json` พร้อม JUnit XML ชุด adversarial ใช้ authored fixtures และ mock transports เท่านั้น ไม่มีการทดสอบ provider, GPU, browser หรือ semantic model quality ใหม่ ไม่มี independent sub-agent review; มี self-review ของ boundary และ counterexamples

ก่อนนำ patch เข้า Luna ให้ตรวจ HEAD/dirty state และ source binding อีกครั้ง แล้ว apply/check/test ใน isolated branch ด้วย Git ภายใต้ owner ที่มีสิทธิ์ งานนี้ไม่ได้เปลี่ยน ownership settings ทดสอบก่อน push/test PR ตามสิทธิ์เดิม และ merge ได้เฉพาะเมื่อ acceptance กับ protections ครบ

คง window เดิม: start ที่บันทึกอย่างช้า `2026-10-31T02:47:23Z`, deadline ไม่ช้ากว่า `2026-11-01T02:47:23Z` ถ้าพบ start ก่อนหน้านั้นให้ใช้ earliest start คง GPU UUID เดิม concurrency 1, CPU 8 threads, RAM 32 GiB, disk เพิ่มรวม 40 GiB งานซ่อมนี้ไม่ได้ใช้ allocation ดังกล่าว


อ้าง source paths ที่ขึ้นต้น providers/ หรือ healthtech/ ภายใต้ `src/patent_to_pilot/` ของ repair candidate

Code commit ที่ทดสอบ: `1ccd58293a48577923531c0436fd9d924b4701b4` ผลสุดท้าย 562 passed, 1 skipped, 2 warnings และ compile/diff check ผ่าน
