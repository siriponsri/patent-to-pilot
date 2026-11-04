# Patent-to-Pilot: audit, repair and current continuation

## Current handoff — 3 November 2026 (supersedes earlier action prompts below)

**มีงานรันจริงแล้ว และแก้เหตุที่ระบบย้อนกลับไป gate R1 แล้ว** ใช้ส่วนนี้เป็นคำสั่งปัจจุบัน ส่วนถัดไปเก็บประวัติการตรวจตามเวลา ไม่ให้ใช้ prompt เก่าที่สั่งรอ R1/SSH แทนส่วนนี้ หลักฐานรวมอยู่ใน [LOCAL_ACCOUNTING_AND_GPU_FOLLOWUP.json](LOCAL_ACCOUNTING_AND_GPU_FOLLOWUP.json)

### ทำเสร็จแล้ว

- แก้ medical screen และตรวจอิสระแล้ว: 96 queries / 3,061 patents; 1,920 positive pairs สำหรับ query-screen/full-corpus แบ่งเป็น both-screen 983 และ target-unscreened 937 คู่ ผลเป็น posthoc diagnostic ไม่ใช่ final holdout
- รัน encoder สิทธิบัตรจริงบน V100 วันที่ 3 พ.ย. เวลา 19:35:56–19:36:12 ไทย: PatEmbed และ multilingual E5 ประมวลผล corpus 41 รายการ + queries 3 รายการต่อโมเดล รวม 4 encode passes/88 rows ในหนึ่ง GPU process ใช้ production encoder source ที่ bind hash ไว้ ไม่ใช้ผลเก่ามาติดป้ายว่ารันใหม่
- รักษา shared OS lock ระหว่างทุก pass, CPU 8 threads, peak GPU reserved ประมาณ 1.48 GiB และ peak process RAM 2.39 GiB; ใช้เวลา worker รวม 15.85 วินาที คืน lock และลบ transient remote scratch แล้ว ไม่มี key/qrels ส่งไป dr-train ไม่แตะ service อื่น
- สร้าง canonical API journal บน Windows ตามคำอนุญาตเริ่ม epoch ใหม่ เก็บ provenance ของ legacy 4 settled calls/USD0.0001464 โดยไม่แก้ไฟล์เดิม ส่วนประวัติ R1 ที่หาไม่พบยังเป็น `UNKNOWN_OWNER_ACCEPTED_CUTOVER`
- แก้ runner ให้ใช้ journal E2 เดียวร่วมกันจากทุก worktree ที่ใช้ code รุ่นนี้; price refresh ไม่ทำให้บัญชีใหม่ ใช้ SQLite transaction จองก่อนส่ง, เก็บ pending/unknown ข้ามการปิดโปรแกรม, ไม่ส่งซ้ำ, เก็บ debit แม้คำตอบผิด และสร้าง recovery snapshot แบบ atomic หลัง reserve/settle
- ตัวรัน `scripts/healthtech/run_openrouter_generation_evidence_pack.py` รองรับ `--env-file` ผ่าน loader เดิมแล้ว อ่านเฉพาะ live mode และคืน process environment เมื่อจบ ไม่ copy key ไป server ไม่แก้ Windows environment ถาวร
- Provider/accounting/API regression **187 passed, 0 failed, 0 errors, 0 skipped** ดู [local-api-provider-regressions.xml](local-api-provider-regressions.xml); ไม่อ้างเป็น full suite หรือความสำเร็จของการทดลอง paid

### ผล retrieval รอบ GPU ใหม่

ใช้ frozen query pack เดียวกันในตารางนี้ มี 3 cases แต่ข้อความ query ไม่ซ้ำเพียง 2 แบบ (MitraClip และ Tendyne ใช้ข้อความเดียวกัน) และ disclosed links รวม 61 คู่ สูตร macro Recall@20 = ค่าเฉลี่ย hits/known links ของแต่ละ case; micro = hits รวม/61; nDCG@20 = คะแนนอันดับแบบ binary ที่หารด้วยอันดับอุดมคติของ known links

| วิธีใน frozen-query diagnostic | พบ known links /61 | Macro Recall@20 | Micro Recall@20 | Macro nDCG@20 |
|---|---:|---:|---:|---:|
| BM25 | 21 | 0.392685 | 0.344262 | 0.430022 |
| PatEmbed dense (fresh GPU) | 24 | 0.430073 | 0.393443 | 0.409533 |
| multilingual E5 dense (fresh GPU) | 27 | 0.481021 | 0.442623 | 0.455981 |

ตรวจซ้ำจาก saved vectors → rankings → metrics แล้วตรงทั้งหมด (ผลต่าง 0; tolerance 1e-12) นี่เป็นผลรันจริงที่มีขนาดเล็กและมี mixed outcome: PatEmbed ได้ Recall สูงกว่า BM25 ใน pack นี้ แต่ nDCG ต่ำกว่า ไม่ถือว่าโมเดลดีกว่าโดยทั่วไป ไม่เทียบตรงกับ BM25 0.662242/B4 0.498802 จาก HT frontier เดิม เพราะ query protocol ต่างกัน และไม่ถือ unlisted patents เป็น negative ผลเดิมและ DAPFAM/PANORAMA/Helmers ไม่ถูกเขียนทับ

โมเดล bind revision: `datalyes/patembed-base@244ba452908a3093be11efb8a44396652317fb14` และ `intfloat/multilingual-e5-base@d128750597153bb5987e10b1c3493a34e5a4502a` พร้อม weight/tokenizer/source/input hashes ใน receipt. ไม่ใช่ local generative Qwen run และยังไม่มี API/local paired-generation outcome ใหม่

### บัญชี API ที่ต้องใช้ต่อ

ตำแหน่งถาวรอยู่ใต้ `%LOCALAPPDATA%/PatentToPilot/healthtech/`:

- `accounting/project-api.sqlite3` — canonical journal ของ `PTP-HT-OR-E2-20261103-USD100`
- `budget-ledgers/PTP-HT-OR-E2-20261103-USD100.json` — binding เดียว ห้ามเปลี่ยนไป path ว่าง
- `accounting/project-api.initial-backup.sqlite3` — สำเนาหลัง initialize; หลังมี attempt จะมี `project-api.recovery.sqlite3` ที่อัปเดตแบบ atomic ก่อน/หลัง transport ตามจุดบัญชี
- `accounting/epoch-initialization.json` — receipt ทดสอบเปิดซ้ำและ `PRAGMA integrity_check=ok`
- `evidence/20261103-pepo-patent-current/` — vectors, rankings, original streamed receipts และสคริปต์ตรวจซ้ำ เก็บ local ไม่ stage ลง Git

เจ้าของอนุญาตให้เริ่ม epoch ใหม่เมื่อกู้ประวัติไม่ได้ แต่ไม่ได้อนุญาตเพิ่ม $100 ใหม่ จึงเปิด prospective allowance เพียง **$1** (canary $0.25 / paired $0.50 / robustness $0.25) และกัน **$98.9998536** ไว้เป็น uncertainty buffer ภายในกรอบ $100 หลังหักยอดเดิมที่รู้ **buffer ไม่ใช่ยอดใช้เงินจริงและไม่ใช่ข้อพิสูจน์เพดานประวัติที่หายไป** จึงตั้ง `lifetime_cap_guaranteed=false` ตามจริง การ initialize ซ้ำไม่ล้าง attempts หรือคืน allowance; ไม่ auto top-up และไม่สร้าง epoch ถัดไปเอง

สร้างและเปิดด้วย runner จริงแล้วในรอบนี้: new paid attempts 0, new paid cost $0; verified historical actual $0.0001464. ยังไม่มี current account balance ใหม่ และ bootstrap pricing เป็นข้อมูลเก่าที่ใช้ bind identity เท่านั้น จึงยังส่ง paid call ไม่ได้ บัญชี budget ไม่ได้เป็นหลักฐานเครดิต

**ก่อน paid run เหลือข้อมูลที่ต้องตรวจจริง:** current available credit ของ account/workspace ที่ใช้ key ใน local `.env` และ key limit ที่ยังเหลือ (หรือ unlimited ที่ตรวจแล้ว) พร้อมเวลาสังเกต จากนั้นผู้รันสร้าง v2 scoped snapshot และตรวจ exact-route pricing ใหม่ภายใน 300 วินาทีก่อน dispatch ใช้ `--credit-snapshot`, `--model-snapshot`, `--env-file` และ output directory ใหม่บน Windows; ไม่ส่ง attempt ที่ billing ยังไม่ชัดซ้ำ ไม่ต้องขอ $100/UUID/วันหมดสิทธิ์ใหม่ และไม่ต้องทำ R1 history ให้ครบเป็น gate ของ epoch นี้อีก

หาก journal/registry เสียหรือมี partial initialization ให้เก็บไฟล์ไว้ ตรวจ recovery image กับ provider receipts แล้วซ่อม binding แบบมีหลักฐาน ห้ามลบแล้ว initialize ใหม่ เพราะจะทำให้ลืม pending charge แม้ source สร้าง journal ได้ก็ไม่ใช่คำอนุญาตให้รีเซ็ต

### Management key และ MCP

ไม่จำเป็นต้องสร้าง management key สำหรับ workflow นี้ วิธีที่ใช้สิทธิ์น้อยที่สุดคือเจ้าของเปิด Credits dashboard ของ account เดียวกัน ดูยอดพร้อมเวลาและ key settings โดยไม่ส่ง key ในแชต Activity CSV อาจใช้เสริมการตรวจย้อนหลัง แต่ไม่ถือเป็น proof ว่าทุก failed/pending attempt ครบ

[OpenRouter MCP documentation](https://openrouter.ai/docs/guides/overview/mcp-server) (อ่าน 3 พ.ย. 2026) ระบุ `get-credits` และ `get-generation` สำหรับ generation ID ที่ทราบ แต่ไม่ระบุ complete all-attempt export. OAuth จะออก key แยกอายุสูงสุด 7 วัน วงเงินเริ่มต้น $10 ที่แก้ได้ใน consent; `send-message` และ `generate-image` คิดเงิน รอบนี้ **ไม่ได้ configure/connect/test MCP กับบัญชีจริง ไม่สร้าง credential** หากเลือกใช้ต้องให้เจ้าของยืนยัน action แล้วอนุมัติ OAuth เอง ใช้เครื่องมืออ่านเครดิต; paid experiment ยังคงผ่าน local journal ไม่เรียก MCP inference ข้ามบัญชีนี้

### งานต่อและขอบเขตสถานะ

**Resume goal เดิม** ไม่ต้องสร้าง goal ใหม่: ทำ paired generation เมื่อ credit/route พร้อม และ bind release/reproducibility กับ dirty candidate ที่รวม patch นี้ งาน GPU ต่อให้ตรวจ resource ใหม่และถือ shared slot ตาม grant ถึง 15 Nov 23:59 Thai. API บน Windows กับ GPU บน dr-train ทำคู่ขนานได้เมื่อแยก output dirs/queues, ใช้ immutable inputs และไม่มี duplicate jobs; GPU คง concurrency1 และ API มี pending slot เดียว ส่วน GPU branch ไม่ต้องรอ API credit

ยังไม่ปิด G1/G2/G4/G5/G6/G7 เพิ่มจาก diagnostic/tests นี้ และไม่ได้เปลี่ยนสถานะ goal ผ่าน Luna runtime (control/session state ไม่ทราบ) รักษา solo amendment/G8 future scope/AI4AI optional ตามเดิม ไม่เพิ่มงานบังคับก่อน 15 พ.ย. ไม่มี commit/push/merge และไม่ลบเอกสารหลักฐาน; ปรับ canonical entrypoints ให้รู้ว่า section นี้มีผลก่อนคำสั่งเก่า

```text
Resume Patent-to-Pilot goal เดิม อ่าน README.md ส่วน Current handoff ใน docs/healthtech/audits/pepo-blocked-goal-repair-20261103/ ก่อน ใช้ canonical local journal E2 ที่สร้างแล้ว ห้ามสร้างงบใหม่หรือวนหา R1 เป็น gate อีก เก็บ unknown history และ legacy 4 calls/$0.0001464 ตามจริง รอบใหม่จำกัด $1; paid run ต้องมี current scoped credit+fresh route pricing ใช้ .env บน Windows เท่านั้น เก็บผล/receipts/journal local ให้ dr-train ประมวลผลภายใต้ shared GPU slot เดิม ใช้ผล fresh patent encoder ที่เสร็จแล้วโดยไม่ปน protocol กับ B0b/B4 หรือ final holdout ทำ paired generation และ release verification เมื่อ prerequisites พร้อม ไม่ส่ง call ค้างซ้ำ ไม่ปิด research goal จาก tests/canary และรายงาน actual costs/results
```

Recorded UTC: 2026-11-03T13:04:31.743999+00:00. Actual resources this follow-up: 1 GPU job / 4 encode passes / 88 rows; paid calls 0 / cost $0; authenticated metadata calls 0; new datasets 0. GPU/CPU มีต้นทุนเครื่องที่ไม่ได้ตีราคาเป็น USD ใน receipt นี้

---

## Historical audit record — earlier observations and prompts are superseded by Current handoff

# Patent-to-Pilot: แก้ blocked goal และรันผลจริง — 3 พฤศจิกายน 2026

**ให้ resume goal เดิม** เพราะเป้าหมายและ acceptance ไม่ได้เปลี่ยน การตั้ง goal ใหม่ไม่ทำให้ ledger หรือ SSH พร้อม และเสี่ยงทำให้ประวัติงบ/ผลทดลองหลุดจากกัน รอบนี้แก้ code แล้ว รันตรวจข้อมูลจริงแล้ว และเตรียม checkpoint ที่แยก blocker เฉพาะ branch โดยไม่ได้เปลี่ยน external goal state ของ Luna

Candidate: `codex/patent-to-pilot-long-run-20261103`, HEAD `88dc40471cb9078f929c02bb893cfa1e364da841` พร้อม uncommitted source/doc patches ผลนี้ไม่ใช่ clean-commit release ไม่มี commit/push/merge และไม่มีการเขียนทับงาน guard/route ของ Luna

## ทำอะไรเสร็จจริง

1. แก้ `scripts/healthtech/analyze_dapfam_coverage.py`: SQL regex literal ต้องเก็บ backslash ของ regex ไว้ แยกจาก helper สำหรับ Windows path; เดิม `medical\ device` กลายเป็น `medical/ device` จึงนับวลีหลายคำไม่ครบ
2. เพิ่ม regression tests 9 กรณี ครอบคลุมวลีหลายคำ, ตัวพิมพ์ใหญ่เล็ก, metacharacters, apostrophe, null fields และ SQL ที่รันผ่าน DuckDB จริง พร้อมจำกัด coverage analyzer ที่ 4 threads/4 GB
3. รัน native DuckDB 2.0.0 กับ corpus 45,336 แถว, queries 1,247 แถว และ qrels 49,869 คู่จริง เมื่อ 18:47:14–18:47:16 น. ไทย สำเร็จใน 1.981 วินาที ผลใหม่อยู่ใน `coverage-summary.json` และ `coverage-run-receipt.json`
4. ประเมิน saved rankings ของ PatEmbed/E5/BM25 ใหม่บน corrected medical query subset 96 queries เมื่อ 18:48:33 น. ใช้ประมาณ 0.668 วินาที ผลอยู่ใน `medical-subset-results.json` นี่เป็นการคำนวณประเมินจริงจากอันดับเก่า ไม่มี inference/encoding ใหม่
5. แก้เอกสาร resource precedence ให้ใช้ USD100 สะสมและ GPU ถึง 15 พ.ย. ตามสิทธิ์ที่มีแล้ว เก็บ USD8/24h เดิมเป็นประวัติ ไม่เปลี่ยน budget controller, ledger หรือสร้างยอดเริ่มใหม่

## ผล medical screen ที่แก้แล้ว

| รายการ | Receipt เดิม | รันหลังแก้ |
|---|---:|---:|
| Queries ผ่าน medical lexicon | 86 | **96** |
| Corpus patents ผ่าน medical lexicon | 2,859 | **3,061** |
| Positive pairs ที่ query ผ่าน | 1,720 | **1,920** |
| Positive pairs ที่ทั้งสองฝั่งผ่าน | 901 | **983** |
| IN: ทั้งสองฝั่งผ่าน | 836 | 916 |
| OUT: ทั้งสองฝั่งผ่าน | 65 | 67 |

Input SHA-256 ทั้ง corpus/queries/qrels ตรงกับ receipt เดิมทุกไฟล์ และ summary เก่าคง hash เดิม ไม่มีการเขียนทับผลย้อนหลัง Pharma/biologics counts ไม่เปลี่ยน: 304 queries / 12,163 corpus rows Lexical screen เป็นการคัดด้วยคำ ไม่ใช่คำตัดสิน semantic relevance

## ผลประเมินใหม่เฉพาะ 96 medical queries

เลือก query ด้วย lexicon ที่แก้แล้ว ใช้ corpus เดิม 45,336 รายการ และ positive ของ queries เหล่านี้ทั้งหมด **1,920 คู่** ไม่กรอง target ให้เหลือเฉพาะ medical corpus จึงต้องไม่สับสนตัวหาร 1,920 กับ both-screened count 983

| วิธี | Hits@100 / 1,920 | Macro Recall@100 | nDCG@100 |
|---|---:|---:|---:|
| BM25 | 326 | 0.169792 | 0.149408 |
| PatEmbed dense | 715 | **0.372396** | **0.310173** |
| PatEmbed + BM25 / RRF | 628 | 0.327083 | 0.264248 |
| E5 dense | 488 | 0.254167 | 0.213106 |
| E5 + BM25 / RRF | 457 | 0.238021 | 0.202883 |

ทั้ง 96 queries มี positive คนละ 20 คู่ จึงได้ macro/micro Recall เท่ากันภายใน floating-point precision ไม่มี query หายหรือ ranked ID ซ้ำ PatEmbed dense สูงกว่าวิธีอื่นใน subset นี้ และ hybrid ต่ำกว่า dense ทั้งสองโมเดล เก็บผลที่ไม่สนับสนุนการเพิ่ม complexity ตามจริง

ขอบเขต: **posthoc diagnostic**, ไม่ใช่ final holdout หรือการค้น patent ให้ device โดยตรง ใช้อันดับจาก 31 ต.ค. บน source revision `257037ab349ec88e5600c074deccfc8a62fe5fc2`; ไม่ relabel เป็น model run บน HEAD ปัจจุบัน Self matches ยังอยู่ตาม protocol เดิม Unlisted pairs เป็น unjudged ไม่ใช่ negative ใหม่ รุ่น PatEmbed `244ba452908a3093be11efb8a44396652317fb14`; E5 `d128750597153bb5987e10b1c3493a34e5a4502a` มี hashes ของอันดับเดิมใน result receipt

## ทวนผล audit ก่อนหน้า

ผลจัดอันดับเดิมไม่ได้ผิดเพราะบั๊กนี้ บั๊กกระทบการคัด medical subset เท่านั้น ผลที่คำนวณซ้ำไว้ก่อนหน้าและยังต้องรักษาความหมายเดิมคือ:

- Abbott: BM25 macro Recall@20 **0.6622417083**, 39/61 คู่; B4-OFFLINE **0.4988024195**, micro **29/61 = 0.4754098361** B4 ไม่ได้ชนะ BM25 ใน development slice นี้ คำค้นและ realized resources ต่างกัน จึงไม่ใช่ causal proof ว่า encoder/adaptive แย่กว่าโดยลำพัง
- DAPFAM เต็มชุด: PatEmbed dense **0.4225251715**, E5 dense **0.2874142386**, matched BM25 **0.2142252517** ที่ Recall@100 ตัวหาร positive 24,929 คู่ ไม่ใช่ qrels ทั้งหมด 49,869 คู่ ไม่รวมคะแนนของ medical subset เข้า mean เต็มชุดใหม่
- PANORAMA: PAR4PC test gold hit@1 **0.7151243094**, PI4PC test **0.4012345679**; hit@8 = 1.0 เพราะคืนครบ 8/5 ตัวเลือก จึงไม่ใช้เป็น headline คุณภาพ เช่นเดียวกับ Abbott Recall@50 เมื่อ corpus มี 41 รายการ
- Helmers: macro AP **0.8854504326**, macro AUC **0.8800118443**, 10 targets/450 judged pairs มี 258 positives ในข้อมูลที่ตรวจไม่มี score ties จึงไม่พบผลพองจาก tie policy ปัจจุบัน แต่การใช้ label ช่วยตัด tie ควรปรับก่อนใช้กับข้อมูลใหม่ที่มี ties
- Local Qwen 3/3 เป็น schema/contract smoke test ไม่ใช่ retrieval quality หรือ semantic correctness; software test counts ไม่ใช่ sample size ของงานวิจัย

ดัชนี audit เดิมมี 158 รายการ: 146 VERIFIED, 8 INCONSISTENT (medical counts จาก root cause เดียว), 3 NOT_RECOMPUTABLE และ 1 REPORT_ONLY รอบนี้ปิดบั๊กและคำนวณ counts ใหม่ ไม่แก้สถานะใน receipt เก่า ไม่รวม historical Stryker/transfer diagnostic เข้ากับ Abbott current slice และไม่กล่าวอ้าง adaptive superiority หรือผล business validation ที่ยังไม่ได้วัด

## ทำไม BLOCKED และแก้อะไรได้

| สาขางาน | ข้อเท็จจริงล่าสุดในรอบนี้ | ผลที่ควรมีต่อ goal |
|---|---|---|
| CPU/offline evaluation | แก้และรัน coverage/subset evaluation สำเร็จ | มีงานที่ทำได้จริง ไม่ควรติด paid/GPU gate |
| Paid API | ตรวจ exact known journal paths ใน registered worktrees 10 แห่ง + canonical registry รวม 21 จุด ไม่พบ; ไม่ใช่ exhaustive machine scan | BLOCKED ก่อน reservation เฉพาะ paid dispatch |
| Current credit | metadata receipt R8 ของ key ปกติรายงาน lifetime usage $0.0001464 แต่ไม่ทราบ scoped remaining credit/history completeness; ไม่ได้เรียก metadata ซ้ำในรอบนี้ | ใช้แทน ledger ที่ครบหรือ remaining balance ไม่ได้ |
| GPU owner grant | มีแล้ว: UUID เดิม/concurrency 1/ถึง 15 พ.ย. 23:59 ไทย | ไม่ต้องถามอนุมัติ UUID/วันเดิมซ้ำ |
| GPU access/conflict | strict-host-key SSH ไป `chaw@100.77.149.83:22` ถูกปฏิเสธ `Permission denied` ก่อนตรวจเครื่อง | **DENIED** สำหรับ connection ครั้งนี้; ไม่ได้เริ่ม job และไม่ได้ลองเส้นทางอ้อม |
| Operator allocation | R8 พบเครื่องว่างแต่เขียน allocation unknown; ยังไม่พบ policy ที่พิสูจน์ว่าต้องมี lease แยกจาก owner grant | แยก authorization จาก current availability; ห้ามถือ idle/zero-byte lock เป็น allocation และห้ามสร้าง prerequisite ที่ไม่มีแหล่งกำหนด |

Local guard ของ Luna เชื่อมกับ generation/embedding/query encoding อยู่แล้ว และใช้ cooperative OS lock ที่ผูกกับ parent ของ model directory ไม่ได้แก้ให้ bypass lock ในรอบนี้ ต้องตรวจ resolved lock path ว่าตรงกันสำหรับทุก GPU launcher พร้อม process/resource สดและ acquire slot ก่อนงาน GPU เมื่อ access ใช้ได้

ตรวจ journal แบบเจาะจงเพิ่มแล้ว แต่ไม่พบไฟล์ จึงไม่สร้าง empty R1 registry ไม่รวม receipt ตัวอย่างเป็นประวัติจริง และไม่สรุปว่า lifetime key usage คือยอดโครงการที่กระทบครบ ต้องการจาก owner/ช่องทางที่ได้รับสิทธิ์เพียง: (1) ที่อยู่ journal เดิม หรือ sanitized all-attempt export รวม settled/pending/unknown/retry (2) current scoped account/key credit snapshot ตาม schema v2 ไม่มี secret key เมื่อมีหลักฐานจึง reconcile และ recheck route/pricing ก่อน reserve ไม่ถามอนุมัติ $100 ใหม่

การแก้ source/doc รอบนี้ได้รับอนุญาตและเขียน project ได้ ส่วน SSH เป็น transport denial จริง ไม่ใช่ความเห็นว่าต้องขอ GPU window ใหม่ การ enumerate โฟลเดอร์ Programs ที่ใช้หา DuckDB ถูกปฏิเสธด้วย จึงหยุดวิธีนั้นและใช้ executable path ที่มีใน historical project receipt อยู่แล้ว ไม่มีการเปลี่ยน ACL/global settings

## การทดสอบและขอบเขตการตรวจ

- Native SQL/regex coverage tests: **14 passed**
- Coverage + adjacent BM25 evaluator tests ที่เลือกตามขอบเขต: **22 passed**, provenance test 1 ตัวไม่ได้เลือก เพราะเรียก recursive Git status และต้องเข้าบริบท repository-owner ที่ไม่ได้เปิดใน sandbox นี้
- การรันรวมครั้งแรก: 22 passed / 1 failed จาก Git dubious ownership; ไม่ใช่ regression ของ regex เก็บ XML เดิมไว้ การรัน scoped ครั้งกลางมี temp-directory setup errors 2 ตัวจาก default `pytest-of-User`; เปลี่ยนเฉพาะ test temporary directory ไปพื้นที่ task แล้วผ่าน ไม่เปลี่ยนสิทธิ์ directory เดิม
- `git diff --check` ผ่านสำหรับ source/test ที่แก้ ไม่รัน full suite/บริการซ้ำโดยไม่จำเป็น; guard/provider source ไม่ถูกเปลี่ยน
- Coverage runner เรียก repaired analyzer และ SQL จริงทั้งหมด มีเพียง Git metadata probes ที่รับค่า HEAD/dirty snapshot จาก scoped check เพื่อไม่สแกน denied/unrelated paths ไม่มี mock data หรือ fabricated results

ค่าใช้จ่ายรอบนี้: **paid model calls 0, paid cost $0, metadata calls 0, GPU jobs 0, dataset downloads 0, ledger mutations 0** มีเพียง CPU evaluation และ tests ใช้ข้อมูลเดิม สิทธิ์งบสะสม $100 ไม่ได้หมายความว่าเหลือ $100 และต้นทุน API $0 ไม่ได้หมายความว่า CPU ไม่มีต้นทุน

## สถานะและงานต่อ

G0 contract ปิดแล้ว; G3 engineering workflow ผ่านในขอบเขตที่มีหลักฐาน; G1/G2/G4/G5/G6 ยัง PARTIAL ตามส่วนข้อมูล/วิทยาศาสตร์/คุณค่า/การเตรียมส่ง; G7 มี isolated release เดิมแต่ยังต้อง bind แพ็ก patch ล่าสุด; G8 เป็น future scope ไม่เพิ่มเป็น mandatory goal AI4AI ก็ไม่ได้เพิ่มเป็น mandatory goal งานนี้ไม่ปิด research goals ด้วย counts/tests

**Resume goal เดิมจากรายงานนี้** พร้อม R8 เป็นประวัติ ให้ทำ release/reproducibility ของ candidate ที่รวม patch ล่าสุดต่อใน environment ที่มีสิทธิ์ ก่อนรวม main ส่วน paid/remote รอเฉพาะ evidence/access ที่ระบุ ห้ามวนขอ metadata เดิมหรือรัน gate-only audit ซ้ำหลายรอบโดยไม่มีข้อมูลใหม่ ถ้า branch ที่เหลือทั้งหมดติด external state จริง ให้สรุป BLOCKED_LOCAL พร้อมหลักฐานครั้งเดียว ไม่อ้างว่าทั้ง project ไม่มีงานเพียงเพราะ API ไม่พร้อม

### Prompt สั้นสำหรับ resume

```text
Resume goal Patent-to-Pilot เดิม อ่าน docs/healthtech/audits/pepo-blocked-goal-repair-20261103/README.md ก่อน รักษา dirty work ทั้งหมด ใช้ medical-screen fix และผล 96 queries/3061 patents พร้อม posthoc subset metrics โดยไม่ปนกับ final study ทำงานอิสระและ release verification ที่พร้อมต่อ บล็อกเฉพาะ paid API จนมี R1 history+current scoped credit และ remote GPU จนเข้าถึง host/ตรวจ conflict ได้ งบ $100 สะสมรวมประวัติเดิม, V100 ใบเดิม concurrency1 ถึง 15Nov23:59Thai ไม่รีเซ็ต ledger/window ไม่ถามสิทธิ์เดิมซ้ำ และไม่วน gate-only audit เมื่อไม่มีหลักฐานใหม่ รายงาน actual runs/costs และข้อจำกัดตามจริง
```

ไฟล์ประกอบในโฟลเดอร์นี้: `verification.json`, `coverage-summary.json`, `coverage-run-receipt.json`, `medical-subset-results.json`, `ledger-path-check.json`, JUnit receipts และ reproduction scripts ซึ่งรับ path ของข้อมูล/เครื่องมือจากผู้รัน ไม่บรรจุ raw text, qrels, vectors, weights หรือ credentials ในเอกสารนี้


**Latest access update:** owner-authorized read-only SSH retry succeeded; see the final Authorized SSH / journal follow-up section. Earlier DENIED entries remain historical.

## Independent review — 3 พ.ย. 2026 เวลา 19:09 น. ไทย

ตรวจ source และ raw parquet ซ้ำด้วย PyArrow + literal substring matching และคำนวณคะแนนจากตำแหน่งอันดับโดยตรง ไม่ import หรือเรียก evaluator/SQL ของ production ในการตรวจอิสระนี้ ผลอยู่ใน `independent-review.json` และสคริปต์ `independent_review.py` ซึ่งรับ path จากผู้รัน

**ยืนยันตัวเลขเดิม ไม่พบข้อผิดพลาดในคะแนน:** 96 queries, 3,061 corpus patents; positive query-target pairs 1,920 คู่ แบ่งเป็น target ผ่าน medical lexicon 983 คู่ และ target ไม่ผ่าน 937 คู่ คำว่า positive มาจาก qrel ของ DAPFAM ไม่ได้หมายความว่าแพทย์หรือผู้เชี่ยวชาญยืนยันความเกี่ยวข้องเชิงเครื่องมือแพทย์

| เงื่อนไขของ positive pair | Target ผ่าน lexicon | Target ไม่ผ่าน lexicon |
|---|---:|---:|
| Query ผ่าน lexicon | 983 | 937 |
| Query ไม่ผ่าน lexicon | 2,357 | 20,652 |

1,920 จึงเป็นตัวหารที่ถูกสำหรับ **เลือกเฉพาะ query แล้วค้นใน corpus เต็ม** ส่วน 983 เป็นจำนวนคู่สำหรับคำถามอีกแบบที่คัดทั้งสองฝั่ง มี 10 จาก 96 queries ที่ไม่มี positive ผ่าน target screen เลย หากจะประเมินแบบนั้นต้องกำหนด corpus/ranking/zero-positive-query policy ใหม่ก่อน ไม่เปลี่ยนตัวหารอย่างเดียวและไม่ตั้งเป็นงานบังคับเพิ่มใน goal นี้

ทั้ง 96 queries มี positive คนละ 20 คู่ ไม่มี qrel คู่ซ้ำ ไม่มี ranking record ซ้ำ ไม่มี ranked ID ซ้ำ/หลุด corpus และทุก method มีครบ 96 queries × 100 อันดับ BM25 จาก model packs ทั้งสองเหมือนกันทุกอันดับ ทุก label เป็น 0/1 จึงใช้ binary normalized Discounted Cumulative Gain (nDCG) ได้ตรงตามสูตร คะแนนทั้ง 6 model-method rows (5 วิธีไม่ซ้ำ) ตรงกับรายงานเดิม; ผลต่างมากสุด 5.56e-17 ซึ่งต่ำกว่า tolerance 1e-12

**ข้อจำกัดเรื่อง leakage และการกล่าวอ้าง:** 8 queries มี ID อยู่ใน corpus แต่ไม่มี positive self-pair ใน subset นี้ จึงไม่มี self-match ที่เพิ่ม numerator; ไม่ได้พิสูจน์ว่า corpus ไม่มี patent-family overlap หรือข้อมูลปนกับการฝึก encoder ผลยังเป็น posthoc diagnostic จากอันดับวันที่ 31 ต.ค. ไม่ใช่ untouched final holdout และ 96 queries ไม่ควรถูกถือเป็น 96 independent families โดยไม่มี family mapping ห้ามยกผลต่างคะแนนเป็นนัยสำคัญทางสถิติเพราะยังไม่ได้ทดสอบ uncertainty ที่เคารพ group dependence การคัด subset รอบนี้ใช้ข้อความกับ lexicon ไม่ใช้ qrel/คะแนนโมเดลเลือกสมาชิก แต่การตัดสินใจใช้ lexicon เกิดหลังเห็นผลชุดหลักแล้ว

### แก้ provenance ของสคริปต์ทำซ้ำ

พบว่า portable `run_coverage.py` เดิมเขียน `source_inputs_unchanged=True` และ `dirty=True` โดยตรึงค่า ไม่ได้ตรวจก่อน–หลังภายใน runner นั้น แม้การตรวจ input hashes แยกในรอบก่อนจะตรงก็ตาม ข้อนี้เป็นช่องว่างของ provenance ไม่ใช่การพบว่าคะแนนผิด

แก้ runner ให้ hash corpus/queries/qrels/analyzer/runner ก่อน–หลังจริง ตรวจ HEAD ก่อน–หลัง และตรวจ dirty จาก tracked analyzer diff แบบเจาะจง ถ้าข้อมูล/source/HEAD เปลี่ยนระหว่างรัน ให้ receipt และ summary เป็น INVALID แล้วหยุด; หาก scoped diff ไม่พบการแก้ จะบันทึก whole-checkout dirty เป็น unknown แทนการอ้างว่า clean รัน runner ที่แก้จริงเวลา 19:07:00–19:07:04 น. ได้ counts เท่าเดิมทุกช่องและ hashes คงที่ ดู `reviewed-coverage-run-receipt.json` เก็บ receipt เดิมไว้โดยไม่แก้ย้อนหลัง

การทดสอบล่าสุด `independent-review-tests.xml`: **24 passed, 0 failed, 0 errors, 0 skipped; 1 deselected** รวม coverage/native DuckDB, adjacent BM25 และ provenance mutation checks ใหม่ 2 tests ตัว provenance test เดิมที่เรียก recursive Git status ยังไม่ได้เลือกด้วยเหตุ environment ที่อธิบายไว้ข้างต้น ไม่ใช่ full-suite/release pass Source fix และ tests ใน production ยัง hash เดิมที่ผ่าน review ไม่มีการเขียนทับงาน Luna

### ขอบเขต blocker ที่ตรวจยืนยันได้

อ่าน `local_execution.py` กับ call sites ของ generation/embedding/query encoding แล้ว: ไม่พึ่ง API budget/credit; imported-query-vector evaluation มีทาง CPU ที่ไม่ผ่าน GPU guard การไม่มี R1 จึงไม่ใช่เหตุให้หยุดงานเหล่านี้ทั้งหมด อย่างไรก็ตาม lock อยู่ที่ parent ของ model directory จึงประสาน launcher ที่ใช้ parent เดียวกันเท่านั้น ก่อนรัน GPU พร้อมกับงานอื่นต้องตรวจ resolved lock path และ resource conflicts จริง; ในรอบนี้ยังพิสูจน์ path/state บน host สดไม่ได้เพราะ SSH ถูกปฏิเสธ ไม่อ้างว่า lock เป็น allocation หรือครอบคลุมทุก process บนเครื่อง

Owner แจ้งว่าพร้อมอนุมัติแล้ว แต่ยังไม่ได้อนุมัติ action ใหม่ที่ระบุเฉพาะ จึงไม่มีการ retry SSH ที่ถูกปฏิเสธและไม่มี provider call ใน review นี้ สิ่งที่ต้องแก้การเข้าถึงคือ **อนุมัติ/เปิดสิทธิ์ network สำหรับ strict-host-key SSH จาก execution environment นี้ไป `chaw@100.77.149.83:22` เพื่ออ่าน resource/process/lock metadata หนึ่งครั้งด้วย credential เดิม**; ถ้า runtime มี approval สำหรับคำสั่งนั้นให้ใช้เส้นทางนั้น ไม่เปลี่ยน host-key policy/ACL/credential และไม่ใช้เส้นทางอ้อม ข้อความ `connect ... Permission denied` เกิดก่อน authentication จึงยังระบุไม่ได้ว่าเป็นนโยบาย sandbox, local network หรือ host-side network control ไม่ควรขอ secret key หรืออนุมัติ V100 window ซ้ำ

Paid API ยังต้องการหลักฐานที่ไม่ใช่ secret สองอย่างตาม `OWNER_ONE_TIME_INPUT_TH_EN.md`: ตำแหน่ง journal R1 เดิมหรือ sanitized all-attempt export `ptp-r1-all-attempt-export-v1`, และ current scoped v2 credit snapshot ของ account/key เดียวกันพร้อม timestamp ไม่ต้องขออนุมัติ USD100 ใหม่ และการอนุมัติใช้ API ไม่สามารถทดแทนประวัติยอดที่หายได้ เมื่อหลักฐานครบจึง reconcile ก่อน reservation/paid dispatch

Review นี้มีเฉพาะ CPU/file evaluation/tests: paid calls 0, metadata calls 0, GPU jobs 0, ledger writes 0 ไม่มี commit/push/merge ไม่ลบเอกสารหรือ raw evidence และไม่เปลี่ยน external goal state **ข้อเสนอคงเดิม: resume goal เดิม** พร้อมรักษาขอบเขตผล posthoc และทำ branch ที่พร้อมต่อ


## Authorized SSH / journal follow-up — 3 พ.ย. 2026 เวลา 19:21–19:23 น. ไทย

**SSH blocker เดิมได้รับการแก้เรื่องสิทธิ์เข้าถึงแล้วในครั้งที่ owner อนุมัติ**: ใช้ execution-environment approval กับ strict host key และ credential เดิมหนึ่ง connection สำเร็จ; ไม่มีการลด host-key policy หรือใช้เส้นทางอ้อม หลักฐานใหม่อยู่ใน `ACCESS_AND_HISTORY_FOLLOWUP.json` ข้อความ DENIED ด้านบนเป็นประวัติก่อน owner อนุมัติ retry ไม่ใช่สถานะของ connection ล่าสุด

ผลสดบน dr-train: V100 UUID ที่อนุมัติใช้ memory 0 MiB, free 32,495 MiB, utilization 0%, ไม่มี compute process บนใบนั้น ไม่พบ kernel lock record ของ shared slot ณ เวลาตรวจ Qwen3-8B, multilingual-e5-base และ PatEmbed อยู่ใต้ resolved parent `models` เดียวกัน จึง resolve lock file เดียวกันได้ มี Python process อื่นของบัญชีอยู่สองตัวนอก job-root ตาม cwd ที่สังเกต ไม่อ่าน command line/credentials ไม่ kill หรือเปลี่ยน service ไม่ตีความ process เหล่านั้นว่าเป็น Luna และไม่สรุปว่า Luna idle

GPU owner grant ถึง 15 พ.ย. มีอยู่แล้ว และยังไม่พบ infrastructure policy ที่บังคับ lease แยก จึงไม่ควรติด gate “ขอ allocation/window จาก owner ใหม่” ตามข้อความเก่า ข้อมูลว่าง ณ จุดเวลานี้ไม่ใช่การจอง: ตอน launch จริงต้องตรวจ resource state สดและ acquire cooperative lock ที่ยืนยัน path แล้ว ภายใน concurrency1/CPU8/RAM32GiB/incremental disk40GiB เดิม ผลตรวจนี้ไม่ได้เริ่ม inference, transfer หรือถือ slot ค้างไว้

### ผลค้น R1 และยอดที่ยืนยันได้

ค้นชื่อไฟล์ใน registered worktrees ของ Patent-to-Pilot 16 แห่งรวม ignored files ได้ 220 candidates; 6 roots ตรวจครบตาม scope และ 10 roots มี test-cache/temp directories ที่ถูกปฏิเสธจึงเป็น partial scan ไม่ลอง denied paths ซ้ำและไม่กล่าวว่าได้ค้นทั้งเครื่อง พบ SQLite ใน worktrees 9 ไฟล์ที่อยู่ใน mock-labelled runs และไม่มี canonical `budget_ledger_meta`; ไม่ใช้เป็นเงินจริง ไม่พบ canonical registry, R1 journal ที่ยืนยันได้ หรือ sanitized all-attempt export ใน scope ที่ตรวจ

ตาม recovery reference เดิมไปตรวจไฟล์จริงใน `_preserved-main-untracked-20261030/results-development-provider-pilot/` แบบ SQLite read-only และ immutable แล้วพบ:

| Journal | Attempts | สถานะ billing | ยอดเงินจริงที่บันทึก |
|---|---:|---|---:|
| `live.sqlite3` | 2 | settled ทั้งคู่ | USD0.0000732 |
| `paired-revalidation-1.sqlite3` | 2 | settled ทั้งคู่ | USD0.0000732 |
| รวม legacy pilot | 4 | unresolved ในสองไฟล์นี้ = 0 | **USD0.0001464** |

หนึ่ง attempt มีผล `model_drift` แต่ถูกคิดเงินแล้ว จึงยังรวมในยอด ไม่ตัดทิ้งเพราะผลล้มเหลว SHA-256 ของทั้งสอง journal ตรงกับ receipt เดิมและไม่เปลี่ยนหลังอ่าน ไม่ copy raw journal ลง project และไม่สร้าง empty registry/ledger

หลักฐาน key metadata ล่าสุดที่อ่านจากไฟล์เดิมลงเวลา 15:50:19 น. ไทย (08:50:19 UTC) แสดง usage USD0.0001464 ตรงกัน, daily/weekly/monthly usage 0 และ `limit_remaining=null`/account scope unreconciled ข้อมูลนี้สอดคล้องกับการไม่มีค่าใช้จ่ายเพิ่มของ key นี้ถึงเวลาที่สังเกต แต่ยังไม่ใช่หลักฐาน R1 pending exposure ครบหรือยอดเครดิต account ปัจจุบัน รอบนี้ไม่ได้เรียก provider metadata ซ้ำ

สองไฟล์ที่กู้ได้เป็น **legacy pilot ก่อน R1** ไม่ได้มี canonical R1 tables/identity จึงผูกกับ live controller ตรง ๆ ไม่ได้ และไม่ตีความ “หา R1 ไม่พบ” ว่า “R1 ไม่เคยมี” Current migration ตั้งใจไม่สร้างหรือแทน ledger หากไม่มีหลักฐานครบ จึงยังไม่เรียก migration หรือ paid dispatch

### ข้อมูลจาก owner ที่ยังต้องการจริง

ไม่ต้องให้ owner แต่ง JSON, สร้าง R1 journal หรือยืนยัน $100/วันหมดสิทธิ์ GPU ซ้ำ ต้องการเพียงแหล่งหลักฐานจริงที่ไม่ใช่ secret: **activity/billing export ของ provider/account ที่ครอบคลุมช่วง R1 ตั้งแต่ 28 ต.ค. เป็นต้นมา รวมรายการล้มเหลว/ค้างถ้ามี และ current balance ที่ผูกกับ account/key เดียวกันพร้อมเวลาสังเกต** หรือชี้ตำแหน่ง all-attempt export เดิมที่มีอยู่ ผู้ implementer จะตรวจและแปลง field ที่มีจริงเข้ารูปแบบ review เอง; field ที่ไม่มีจะคง unknown ไม่แต่งย้อนหลัง ถ้า export ไม่สามารถยืนยัน pending/completeness ได้ ให้ระบุช่องว่างนั้น ไม่กล่าวว่ามี $100 เหลือเต็ม

**Resume goal เดิม:** ทำ branch local/offline ต่อภายใต้ grant เดิมโดยไม่รอ R1; ตอน launch GPU ต้องตรวจ fresh state และถือ shared slot จริง หยุดเฉพาะ paid branch จนประวัติและ credit reconcile ได้ ห้ามวนเรียก key metadata ที่ให้ข้อมูลชนิดเดิมซ้ำ หรือสแกน denied directories ซ้ำโดยไม่มีสิทธิ์ใหม่ การตรวจครั้งนี้เปลี่ยนความพร้อมของการเข้าถึง host ไม่เปลี่ยนสถานะการปิด research goals หรือแปล canary เป็นผลวิทยาศาสตร์ใหม่

Prompt ที่ปรับตามผลล่าสุด:

```text
Resume Patent-to-Pilot goal เดิม อ่าน docs/healthtech/audits/pepo-blocked-goal-repair-20261103/README.md ส่วน Authorized SSH / journal follow-up และ ACCESS_AND_HISTORY_FOLLOWUP.json ก่อน SSH retry ที่อนุมัติผ่านแล้ว, V100 ไม่มี conflict ณ snapshot และสาม model directories ใช้ shared lock parent เดียวกัน ให้เดินงาน local ที่พร้อมตาม grant เดิมหลัง fresh prelaunch check+acquire slot โดยไม่รอ R1 และไม่ขอวัน/UUID ใหม่ เก็บ medical posthoc 96 queries/1920 positives แยกจาก both-screen983 และ final holdout Legacy journals สองไฟล์ยืนยัน4 settled calls/USD0.0001464 แล้ว แต่ยังไม่ใช่ R1 complete history/current credit จึงปิด paid dispatch ไว้จนได้ genuine account activity/export+balance แล้ว reconcile ห้ามสร้าง zero ledger, รีเซ็ตงบ/window, ใช้ mock เป็นเงินจริง หรือวน gate-only checks รักษา dirty work/บริการอื่น และรายงาน actual runs/costs ตามจริง
```

รอบ follow-up: SSH read-only 1 connection สำเร็จ, provider/metadata calls 0, GPU jobs 0, remote writes 0, ledger mutations 0 ไม่มี commit/push/merge เอกสาร canonical ได้ปรับ next action ให้แยก local readiness ออกจาก paid evidence แล้ว
