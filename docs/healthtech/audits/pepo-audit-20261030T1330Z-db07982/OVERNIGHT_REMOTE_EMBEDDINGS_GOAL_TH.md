# Overnight Goal — remote embeddings จาก dr-train กลับมาใช้งานบน Windows

**ใช้ NEW GOAL กับ Luna Max** รอบนี้เปลี่ยน outcome จาก M42 coverage/semantic-source intake เป็นการทำ remote embedding และ vector portability ให้ใช้ในระบบจริง จึงไม่ใช่ Normal และไม่ใช่การ Resume M42 เดิมโดยไม่เปลี่ยนขอบเขต หากต้องใช้ session เดิม ให้บันทึก scope amendment ก่อนเริ่ม แล้ว resume ตาม checkpoint ของ goal ใหม่นี้

เอกสารนี้เป็นแผนดำเนินงาน **ยังไม่ได้ SSH, encode, transfer หรือเริ่ม overnight job ในรอบเตรียมเอกสาร** คำสั่งที่เกี่ยวกับ remote ทั้งหมดด้านล่างเป็น templates ที่ยังไม่ได้รัน ต้องตรวจ client/runtime และแทน proposed paths ด้วยค่าที่มีสิทธิ์จริงก่อนใช้

## 1. อ่านอะไรและยึดบริบทไหน

ทำงานที่ `C:/Users/User/Desktop/myProject/patent-to-pilot` โดยทำตาม system/developer/runtime และ scoped AGENTS ที่ใช้กับพื้นที่นั้น Root GOAL/PLAN/README เป็นข้อกำหนดของโครงการ อ่าน [GOAL sections 0–4](../../../../GOAL.md), [PLAN](../../../../PLAN.md), [README](../../../../README.md), [AGENTS](../../../../AGENTS.md), [progress](../../progress.json) และ [next actions](../../../../memory/next-actions.md) ก่อนเลือกงาน

ใช้ชุดนี้เป็นหลักฐานตั้งต้น ไม่เปิด broad audit 102 commits ซ้ำ:

- [ผล audit และลำดับข้อบกพร่อง](AUDIT_TH.md), [claim/evidence matrix](claim-evidence-matrix.csv), [receipt ของ audit](receipt.json)
- [บริบทต้นฉบับจากเจ้าของ](SOURCE_CONTEXT_TH.md): ไม่มี experts/organizational data ใหม่ และต้องการทั้ง research กับ dossier สำหรับผู้ประกอบการ/นักลงทุน
- [Goal ฉบับรายละเอียดเดิม](LUNA_REMOTE_EMBEDDINGS_GOAL_TH.md) และ [สถาปัตยกรรม/vector contract](REMOTE_EMBEDDINGS_PLAN_TH.md)
- [ช่องว่างของ DAPFAM และ dataset เสริม](DATASET_GAPS_TH.md), [หลักฐานการ reproduce](evidence/REPRODUCE.md)

ฐาน audit คือ `db0798276e3158b04131b4e910abc0a11511e94c` แต่ให้ตรวจ HEAD/status ใหม่ และอธิบาย source drift ที่กระทบงาน ไม่ถือว่า receipt เดิมยืนยัน candidate ใหม่ Audit COMPLETE ภายใต้ scope ที่ระบุ แต่โครงการยังไม่ COMPLETE

งานตรงกับ HT-W06/W08/W09/W10/W12 และ backend contract ส่วนที่เกี่ยวกับ HT-W13 ของ PLAN ไม่บังคับเปิด full scientific final study หรือทำ UI ของ Claude ในรอบนี้

## 2. Outcome ข้ามคืนและขอบเขต concurrent work

ส่งเส้นทางที่รันได้จริง: **permitted runtime inputs บน Windows → batched encoding บน dr-train → committed vector shards → transfer กลับ → validated local import/exact index → matched retrieval results และ dossier backend 3 กรณีที่ใช้ vectors ชุดนั้นจริง**

อย่าจบงานเมื่อมีแต่ schema, scripts, coverage report หรือ receipt หาก remote dependency ยังขาด ให้ส่ง local engineering package ที่ใช้ต่อได้เป็น PARTIAL และระบุ remote branch เป็น BLOCKED_LOCAL ไม่ใช้ synthetic vectors อ้างว่าได้ remote output แล้ว

Claude กำลังทำ UX/UI ตามคำสั่งล่าสุดของ owner แยก Luna backend/data/vector branch และ worktree ของตัวเอง ก่อนทำให้ตรวจ metadata/ownership ใหม่ ประวัติที่ audit เห็นคือ branch `claude/healthtech-ux-local-20261028` และ worktree `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-claude-ux-20261028` ชื่อเหล่านี้อาจเปลี่ยนได้ ไม่ checkout/switch/merge/stash/reset หรือแก้ UI-owned files ทุก dirty/untracked file ของคนอื่นต้องอยู่ครบ

ไฟล์ handoff ชุดนี้อาจเป็น untracked จึงไม่ตามไป new worktree อัตโนมัติ ให้คัดลอกเฉพาะ authored goal/audit notes ที่จำเป็นพร้อมตรวจ manifest hash ไป workspace ของ Luna หรือตั้ง read-only reference มายังไฟล์ต้นฉบับ ห้ามแก้ AGENTS ของ owner เพื่อให้ git สะอาด ห้ามเริ่ม writer หลายตัวบนไฟล์/remote run เดียวกัน ไม่มี unsolicited message ถึง Claude ให้สร้าง versioned API/schema handoff ที่อ่านต่อได้แทน

Commit เฉพาะ scoped tested files บน branch ของ Luna การอนุญาต push main ในอดีตเป็นบริบทประวัติ ไม่ให้อนุมาน authority ใหม่จาก audit นี้ **ไม่มี automatic merge/push main** หรือการเปลี่ยน Claude branch บันทึก publication authority/checks แยกไว้ ไม่ deploy/public release/force push

## 3. เริ่มจาก checkpoint แล้วลงมือแก้

สร้าง run ID ใหม่ที่ใช้ ASCII เช่น `luna-remote-embeddings-YYYYMMDDThhmmZ` บันทึก parent audit, start HEAD, branch/worktree, source/config hashes, file ownership และ output locations ใน `docs/healthtech/audits/<run-id>/` อ่าน existing checkpoint ก่อนเริ่มใหม่ ห้ามสร้าง ledger/run ID ใหม่เพื่อให้ดูเหมือนไม่เคยมี failures หรือค่าใช้จ่าย

ปิด confirmed repairs ที่เกี่ยวกับ package นี้ด้วย hand-computable before/after regressions:

| งาน | สิ่งที่ต้องพิสูจน์ |
|---|---|
| Query/company metadata rights | ทุก external JSON, TH/EN display และ export ใช้ origin/field policy เดียวกับ source/evidence รวม restricted explicit request และ user-authored origin; local record ไม่เสียค่าเดิม |
| DAPFAM evaluator | unique task IDs ก่อน K, unknown query/candidate handling, missing/failure denominator และ metric bounds; probe เดิม duplicate positive ให้ nDCG@2=1.6309 ต้องไม่เกิดอีก ห้าม clamp เพื่อกลบปัญหา |
| Clean checkout | cross-cohort default tests ไม่พึ่ง ignored `results/healthtech`; newline portability แก้ที่ authored fixture/contract ที่ถูกต้อง ไม่ปิด raw-source hash checks; exact final HEAD ผ่าน targeted+guarded checks |
| Claim/split records | แก้ stale full-context8 ให้ตรง full11 และแยก descriptive transfer จาก untouched final; ไม่กล่าวหาว่าเคย tune-on-test หากไม่มีหลักฐาน |
| Budget/source-stage assurance | canonical ledger ต่อ authorization เดียว, immutable pricing binding และ draft-vs-approved stage ตาม audit; ใช้ offline fixtures ไม่อ่าน private billing journal เพื่อเขียนเอกสาร ไม่ให้ branch นี้หยุด embedding ที่ไม่ใช้ provider |

ผล clean Git checkout ของ audit เดิมคือ **455 passed, 3 failed, 1 optional-tokenizer skip** ไม่เอา archive-only missing `.git` มานับเป็น regression ของ repo และไม่เอา optional cache skip มาซ่อน 3 failures จริง ดู exact reproduction ใน linked evidence ไม่ rerun old model/provider experiments แทนการตรวจโค้ดที่เปลี่ยน

## 4. SSH ที่ทราบจริง และสิ่งที่ยังไม่ทราบ

| รายการ | ที่มา/สถานะ |
|---|---|
| Remote machine | `dr-train` ตามคำขอ owner |
| Previous destination | `chaw@100.77.149.83` มาจากประวัติการเชื่อมต่อที่ owner ใช้สำเร็จ ซึ่ง parent ส่งต่อมาในคำสั่งเตรียม goal ไม่ใช่ข้อมูลที่ตรวจสดจากเครื่อง remote |
| Previous Windows key location | `~/.ssh/id_ed25519_dr_train` ตามประวัติเดียวกัน อ่านผ่าน SSH client ปกติเมื่อได้รับอนุญาตเท่านั้น ห้ามเปิด/พิมพ์เนื้อหา key |
| Project metadata search | ใน project-owned refs ที่ audit ตรวจ ยังไม่พบ host/user/jobroot/allocation contract ที่ยืนยันเพิ่มเติม ไม่อ่าน global SSH configs/session stores/private keys เพื่อเดา |
| Host fingerprint | ไม่ได้ตรวจ/บันทึกใน audit นี้ ต้องใช้ known-host entry ที่เคยตรวจอย่างน่าเชื่อถือ หากยังไม่มี/เปลี่ยน ให้ขอ fingerprint ผ่านช่องทางที่เชื่อถือได้ก่อน login |
| Job root | **proposed, ยังไม่สร้าง/ยังไม่ยืนยัน**: `/home/chaw/patent-to-pilot-jobs/<run-id>` ใช้ได้เมื่อ parent path/ownership/allocation รองรับจริง |
| GPU/resource allocation | ไม่ได้ยืนยัน GPU UUID, window, quotas หรือผลกระทบ Podi จากรอบ audit ห้ามตีความว่า GPU0 ว่างจาก login สำเร็จหรือ utilization ต่ำ |

ไม่ต้องขอสิทธิ์เดิมซ้ำ หากมี allocation ที่ยังใช้ได้ใน authorized project context ให้บันทึกอ้างอิงแล้วทำต่อ หากขาด ให้ขอ **ครั้งเดียวแบบรวมรายการเฉพาะที่ขาด**: destination/jobroot, GPU UUID หรือ CPU quota, ช่วงเวลา/เวลาสิ้นสุด, VRAM/RAM/disk limits และข้อห้ามของ Podi/shared services พร้อมประมาณ canary/full-run และงานที่เตรียมเสร็จแล้ว ระหว่างรอให้ทำ repairs, exporter, shard writer, importer, local search และ authored tests ต่อ

### PowerShell connection template — NOT_RUN

รันด้วย Windows account ของ owner ที่เก็บ key จริง ไม่ repurpose `$HOME` และไม่เปลี่ยน global SSH settings หาก clientอยู่ใต้ sandbox/service profile คนละ account ให้ใช้ approved integration/explicit owner key path ที่มีอยู่แล้ว ไม่คัดลอก key มาใน repo

```powershell
$ptpUserProfile = [Environment]::GetFolderPath('UserProfile')
$ptpKey = Join-Path $ptpUserProfile '.ssh\id_ed25519_dr_train'
$ptpTarget = 'chaw@100.77.149.83'
$ptpOptions = @(
  '-i', $ptpKey,
  '-o', 'IdentitiesOnly=yes',
  '-o', 'StrictHostKeyChecking=yes',
  '-o', 'BatchMode=yes',
  '-o', 'ForwardAgent=no',
  '-o', 'ConnectTimeout=15',
  '-o', 'ServerAliveInterval=30',
  '-o', 'ServerAliveCountMax=3'
)
ssh @ptpOptions $ptpTarget 'hostname'
```

Expected: host identity ตรง dr-train ที่ยืนยันไว้และ exit0 ไม่ใช่แค่ต่อถึง IP ได้ ห้าม `StrictHostKeyChecking=no`, blind `accept-new`, blind fingerprint acceptance หรือเอา `ssh-keyscan` output ไปเชื่อทันที ถ้า unknown/changed host key ให้หยุดเฉพาะ remote branch ไม่แก้/ลบ known_hosts เพื่อผ่าน ถ้า BatchMode ติด passphrase ให้ใช้ existing approved owner agent/session ไม่สร้าง/บันทึก passphrase หรือ key ใหม่

หลัง verified login ใช้คำสั่ง read-only ทีละรายการตาม installed tools เช่น `pwd`, `uname -s`, `df -Pk .` และ `nvidia-smi --query-gpu=uuid,name,memory.total,memory.used,utilization.gpu --format=csv,noheader` บันทึกเฉพาะ capacity/job facts ที่จำเป็น ห้าม dump environment หรือ full process command lines ที่อาจมี secrets Capacity check ไม่ใช่ allocation และไม่ใช้เป็นเหตุ kill/restart/renice jobs คนอื่น

## 5. แผนทรัพยากรที่มีขอบ ไม่ถือเป็น grant ใหม่

Owner อนุญาต long run ข้ามคืน แต่ยังต้องอยู่ใน allocation ที่มีจริง ให้เลือกตามข้อมูล canary ไม่เปิด background job ไม่จำกัดเวลา ข้อเสนอตั้งต้นนี้ใช้เพื่อประมาณ/implement guard ไม่ได้จอง GPU ให้:

| ทรัพยากร | ค่าเริ่มต้นที่เสนอ/วิธีตัดสิน |
|---|---|
| Remote concurrency | 1 encoder job, 1 writer ต่อ run; ใช้ GPU UUID ที่จัดสรรเท่านั้น หรือ CPU quota ที่ระบุ |
| Wall time | finite deadline ไม่เกินจุดสิ้นสุด allocation; วางแผนตัวอย่างสูงสุด8ชั่วโมง ถ้าได้ window สั้นกว่านั้นใช้ค่าที่สั้นกว่า |
| Batch/shards | เริ่ม16–32ตาม tokens/VRAM; shardไม่เกิน5,000rows เป็น default ที่ปรับพร้อมเหตุผลได้ |
| Temporary disk | proposed localเพิ่มไม่เกิน15GiB / remote20GiB สำหรับ baselineหนึ่งเงื่อนไข; วัด bytesจริงก่อนส่ง/encode เก็บ free-space reserve อย่างน้อย max(5GiB,20% ของพื้นที่ที่ใช้ได้) ถ้าไม่พอให้ลด bundle/shard/copies ไม่ลบงานอื่น |
| Model/data acquisition | reuse pinned local DAPFAM และ weights ก่อน; downloadเฉพาะ immutable reviewed artifacts ที่จำเป็นตาม rights บันทึก size/hash/source/resume; ถ้าต้องเกิน disk bound ให้ลด scopeหรือขอเฉพาะresourceที่ขาด ไม่ซื้อ GPU/storage |
| GPU RAM / host RAM | บันทึก allocationจริงและ canary peak; ไม่สมมติค่าจากชื่อ GPU; เหลือ headroom ตาม shared-service constraints |
| Provider/API | default USD0 ไม่มีความจำเป็นใช้ OpenRouter เพื่อ encode/import/compareนี้; original round1 **cumulative USD8** รวม agents/resumes/retries/pending ไม่ได้ให้เพิ่มอีก8 |

Final DAPFAM corpus45,336×384float32 =69,636,096bytes และ queries1,247×384 =1,915,392bytes ไม่รวม ID map/index/chunks บาง representation อาจมีหลาย chunks ต่อเอกสาร จึงต้องคำนวณใหม่จาก rows จริง ห้ามอ้าง final vector size เป็น peak VRAM; all-token tensor เดิม N×256×384 อาจมีขนาด16.6GiB เพียงตัวเดียวก่อน overhead ต้องใช้ batches

ไม่อ่าน key/token ลง logs/repo ไม่สร้าง credentials ใหม่ ไม่เปลี่ยน account/security/ACL ไม่ซื้อ credits/subscription/topup ไม่เปิด public endpoint หรือ deploy การใช้ API ภายหลังที่พึ่ง budget gap ต้องรอ canonical cumulative guard ผ่านและใช้อำนาจเดิมที่ยังตรง scope เท่านั้น ไม่หยิบ paid calls มาเติมเวลาข้ามคืน

## 6. Data และ model contract ก่อนส่งขึ้น remote

ใช้ DAPFAM3parquets ที่ตรวจ hashes/countsแล้ว ไม่ต้องขอ owner โหลดเดิมอีก corpus45,336/query1,247/qrels49,869 ซึ่งรวม sampled zero labels ไม่ใช่49,869positive links DAPFAM เป็น citation-derived family retrieval, IN/OUTตามIPC3 ไม่ใช่ device–patent semantic gold

Runtime export เฉพาะ permitted non-sensitive text, stable dataset-scoped IDs, source revision/hash, text hash, representation และ model/config metadata **ไม่มี qrels/gold/adjudications/split answers** ไป encoder แยก `dapfam_family` จาก `patent_publication` ห้ามเปลี่ยน opaque IDs เป็นเลขสิทธิบัตรปลอม Patent/device text ใช้ได้เฉพาะ source-specific controlled processing rights ที่รองรับ ข้อมูลผู้ป่วย/ลูกค้า/private journals ไม่อยู่ในงานนี้

อ่าน [dataset gap note](DATASET_GAPS_TH.md) แล้วเลือก supplement เท่าที่ตอบโจทย์: existing SciFact สำหรับ evidence component; PatentMatch สำหรับ claim–passageเมื่อ dataset termsพร้อม; CLEF-IP edition/task subset เมื่อมีเหตุผล/พื้นที่ ไม่เริ่ม huge bulk download เพื่อให้ดูว่ามีงาน Bridge rights/cohortติดได้เฉพาะ branchนั้น ไม่ fabricate gold/unjudged negatives และไม่ตั้ง owner expert adjudication เป็น global prerequisite

Pin encoder ID/revision/artifact/tokenizer hashes, prefixes, max length, truncation, chunk sizes/overlap/aggregation, pooling, normalization, dimension, inference+export dtype และ library/backend versions ก่อน encode ห้าม `trust_remote_code` หรือ execute unknown installers/loaders

Existing `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`,384dimensions/max_length256 เป็น **integration/portability baseline ไม่ใช่เพดาน patent semantic performance** รายงาน truncated-text coverage GPU FP32 แทน quantized CPU ONNX เป็นคนละ named condition ต้องตรวจ compatibility ห้าม silent mix query/document vectors

หลัง core path เสร็จ หาก remaining allocation/rights/diskพอและมี hypothesisชัด เลือก alternative encoder/longer context/chunking comparison ที่แยก conditionและmatchedcontrolsเพียงชุดที่ตอบคำถาม ห้ามเปลี่ยนหลายปัจจัยพร้อมกันแล้วอ้างว่า adaptationดีขึ้น ไม่บังคับ modelใหญ่เพื่อปิดงาน

## 7. Implement interface แล้ว canary → full shards

ชื่อ `export_embedding_inputs`, `encode_embedding_shards`, `validate_vector_bundle`, `import_precomputed_vectors` ใน [แผนสถาปัตยกรรม](REMOTE_EMBEDDINGS_PLAN_TH.md) เป็น **proposed interfaces ยังไม่มีใน audited HEAD** Luna เลือกชื่อ/moduleตามrepoได้ แต่ต้องส่ง actual `--help`/commands และ config ที่ใช้จริง ไม่คัดลอกคำสั่งที่ยังไม่มีแล้วเรียกว่า runnable

ทำ local authored numeric fixtures ก่อน จากนั้นเมื่อ remote allocation/rightsพร้อมให้รัน canary32–100docs+10queries ที่มี short/long/Unicode/empty/errorcases ตรวจ ID/order/text/config/hash, finite vectors, normalization และ same-condition CPU/GPU numeric/rank consistency กำหนด tolerancesพร้อมเหตุผล เช่น abs1e-4/cosine1e-5 สำหรับ comparable FP32graph ไม่บังคับ bitwiseตรงกับquantizedbackend

Full targetเริ่ม45,336 corpus+1,247queryvectors หรือ exact eligible manifestcounts ที่บอกเหตุผลชัด เก็บ vector `.npy` little-endianfloat32 / `allow_pickle=False`, orderedIDJSONL, per-rowtext/config hashes และ optional chunk→documentmap

Writer contract: write `.partial` → close/flush/fsync → validate bytes/shape/count/finite/hash → publish immutable shard → atomic committed manifest/checkpoint หนึ่งwriter ห้าม committed manifest ชี้ incomplete data Consumerเห็นเฉพาะ committedgeneration ไม่เห็น0byte/intermediatefileหลัง crash

Resumeต้องเทียบ parent input/model/config/orderedIDs และ shardhashก่อน reuse ห้าม recompute completedmatching shards หรือสร้าง duplicate/missingrows Inject interruptionอย่างน้อยหนึ่งครั้งใน isolated runแล้วพิสูจน์ replay idempotence ไม่ใช้ zero vectorแทนfailedrow ห้ามเปลี่ยน model/configเพื่อหลบresume mismatch ถ้าต้องเปลี่ยนให้เป็นnewconditionชัด

OOM: rollbackเฉพาะ uncommittedbatch ลด batchครึ่งหนึ่งภายใต้ configเดิมและ clear owned worker state เริ่มใหม่ได้ไม่เกิน3consecutive OOM reductions/condition ถ้า batch1ยังไม่สำเร็จหรือ budgetหมดให้หยุดconditionนั้นพร้อมfailureIDs/peakmemory ไม่retryไม่จบ Transient retriesไม่เกิน2ต่อshardและต้องยังอยู่ใน wall/resourcebudget นี่เป็น default safety bound ไม่ใช่เป้าหมายจำนวนรอบงาน

## 8. Supervision, disconnect และ checkpoint

ก่อนปล่อย unattendedต้องมี finite supervisor ที่บังคับ deadline/resource/disk stop และเก็บ exit statusได้จริง ใช้ schedulerหรือ existing tmux/user-level mechanismที่เครื่องมีและได้รับอนุญาต หากไม่มีให้เขียน bounded runnerในjobdirเอง ไม่ install service/system daemon หรือเปลี่ยน security settings

ใช้ run lock พร้อม runID/host/PID/process-start identity/lease/conditionhash และ heartbeatประมาณ60วินาที PIDอย่างเดียวไม่พอ ไม่ขโมย stale lock จนพิสูจน์ว่า owned processเดิมไม่อยู่และไม่มีwriterใหม่ Job supervisorจัดการเฉพาะ child/processgroupของrunตัวเอง ห้าม killทุกpython/GPU process ปิดrunเมื่อ deadlineมาถึงและ checkpointก่อนgraceful shutdown

SSHหลุดไม่ได้แปลว่า jobตายหรือสำเร็จ หลังreconnectอ่านrun-specific heartbeat/checkpoint/exitreceiptและverifyownedprocessก่อนlaunchซ้ำ ใช้ bounded reconnect≤3ครั้งด้วยbackoffภายในwindow ไม่เปิดencoderซ้อนถ้าสถานะเดิมuncertain หากheartbeatค้างและยืนยันไม่ได้ ให้หยุดเฉพาะremoteactions ทำlocalworkต่อและรายงานUNKNOWNแทนclaimCOMPLETE

ทุก completedshard/workpackageบันทึก checkpoint; อย่าเขียนreceiptแทนoutcome ตั้ง `CHECKPOINT.json` ให้มี runID/startHEAD/currentcandidate/model+inputhashes/allocationref/deadline/status/completedshards/pendingrows/attempts/resources/lastheartbeat/nextcommand และ `NEXT_ACTIONS.md` ที่resumeได้ Receiptต้องไม่เก็บ env,keys,rawrestrictedtext หรือprivateprocessargs

Code/control-plane restart ให้อ่านcheckpointและตรวจartifactsก่อนเริ่ม ไม่resetattempts/budgetหรือoverwrite historicalevidence ถ้าไม่มีremainingusefulworkหรือcriticaldependencyค้างให้ส่งpartialhandoffแล้วจบ ไม่สร้างdocumentationloopเพื่อให้ครบ8ชั่วโมง

## 9. Transfer/resume และ checksum templates — NOT_RUN

สร้าง named run/jobroot เมื่อสิทธิ์directoryพร้อมและตรวจ resolvedpath อยู่ในขอบที่ตกลง ห้าม bulk sync home/repo, recursive delete, `--delete` หรือtransfer evaluatorlabels ส่งreviewed codeและruntimebundleที่ไม่มีsecretsเท่านั้น ไม่มีprivatekeysในbundle

ตัวอย่างต่อจาก PowerShell connection variables (proposedremotejobroot ต้องแทนให้ตรงค่าจริง; runIDใช้ `[A-Za-z0-9._-]+`):

```powershell
$ptpRunId = 'luna-remote-embeddings-YYYYMMDDThhmmZ'
if ($ptpRunId -notmatch '^[A-Za-z0-9._-]+$') { throw 'Invalid run ID' }
$ptpRemoteRoot = '/home/chaw/patent-to-pilot-jobs/' + $ptpRunId
$ptpLocalRun = Join-Path 'C:/Users/User/Desktop/myProject/patent-to-pilot-local-artifacts' $ptpRunId
$ptpInput = Join-Path $ptpLocalRun 'runtime-input.jsonl'
$ptpPartial = Join-Path $ptpLocalRun 'part-00000.npy.partial'
$ptpInputDestination = '{0}:{1}/input/runtime-input.jsonl' -f $ptpTarget, $ptpRemoteRoot
scp @ptpOptions $ptpInput $ptpInputDestination
$ptpVectorSource = '{0}:{1}/vectors/part-00000.npy' -f $ptpTarget, $ptpRemoteRoot
scp @ptpOptions $ptpVectorSource $ptpPartial
if ($LASTEXITCODE -ne 0) { throw 'Transfer incomplete: keep partial uncommitted' }
Get-FileHash -Algorithm SHA256 -LiteralPath $ptpPartial
```

Localrunpathด้านบน **proposed, ไม่ได้สร้างแล้ว** ใช้ permittedlocalstorageที่มีdiskbudgetจริง SCP templateเป็น whole-shardretry ไม่อ้างbyte-range resume ตรวจ exitcodeหลัง uploadด้วยก่อนremoteuseและตรวจ hashทั้งinput/vectorแต่ละไฟล์เทียบmanifestที่trustedจากrunเดียวกันก่อนpublish

หากinstalledSFTPรองรับ resume และremote committedfileคงเดิม ใช้ interactive `sftp @ptpOptions $ptpTarget` แล้วแทนpathจริงในตัวอย่าง:

```text
lcd C:/Users/User/Desktop/myProject/patent-to-pilot-local-artifacts/luna-remote-embeddings-YYYYMMDDThhmmZ
cd /home/chaw/patent-to-pilot-jobs/luna-remote-embeddings-YYYYMMDDThhmmZ/vectors
reget part-00000.npy part-00000.npy.partial
```

`reput` ใช้สำหรับresume uploadไปยัง uncommitted inputpartialที่runตัวเองownsเท่านั้น ไม่ใช้กับ committed output ผู้ผลิตต้องไม่แก้remotecommittedfileระหว่างresume ถ้าpartialมาจากคนละhash/versionให้เปลี่ยนชื่อ/กักเฉพาะpartialของrunตัวเองแล้วtransferwholefileใหม่ SFTP resumeไม่พิสูจน์ว่าข้อมูลถูกต้อง ต้องverifySHA256fullfileและrowcontractเสมอ

บนremoteใช้ `sha256sum` เฉพาะnamedfileภายใต้verifiedjobroot หรือreviewedPythonhashhelperเมื่อtoolไม่มี ตรวจlocalSHA256เทียบexpectedก่อนrename `.partial` เป็นcommittedlocalartifact การมีhashตรงพิสูจน์byteintegrityไม่พิสูจน์ว่าsource/model/labelsถูก ต้องvalidateparentmanifestด้วย

Syntaxอ้างอิงจาก primary OpenSSH manuals: [ssh](https://man.openbsd.org/ssh), [scp](https://man.openbsd.org/scp), [sftp](https://man.openbsd.org/sftp), [host verification options](https://man.openbsd.org/ssh_config) clientWindowsที่ติดตั้งจริงอาจต่างversion ต้องตรวจcapabilityโดยไม่รันremotejobในขั้นเตรียมเอกสารนี้

## 10. Local integration และการประเมินที่มีความหมาย

Importerต้องreject modifiedshard/hash, wrongmodel/config/text, missing/extra/duplicate/swappedID-order, wrongshape/dtype/dimension/nonfinite/partialmanifest/pathtraversalก่อนindex Publishlocalgenerationแบบatomic เริ่ม exactNumPy/memmapsearchและdeterministicIDtiesที่45Kscale ANNเพิ่มเมื่อมีเหตุผลและวัดrecallagainstexact

ต่อ precomputedretrievalprovider ให้ทั้ง `SharedRetriever` และ dossierbackendที่ `healthtech/engine.py` ใช้งานจริง มี matchinglocalqueryencoderสำหรับdynamicquery หากbackend/precisionต่างต้องprovecompatibility Fixedqueryvectorsใช้เฉพาะquerytext/confighashตรง ไม่ใช้docembeddingแทนcross-encoder reranker และaggregatechunks→document/familyก่อนK

เปรียบเทียบ actual BM25/dense/hybrid บนsameeligiblequeries/corpus/K/representation/selfpolicyและdeclaredresources ใช้correctedevaluator บันทึกperquery/groupmetrics/rawranks/latency/indexing+servingresources/failures/retries/cachelineage ตรวจofficialself-IDpolicyก่อนclaimparity; policyยังไม่ชัดให้reportexplicitself-excludeddiagnosticเหมือนกันทุกmethod ไม่skipfailedqueries

DAPFAMวัดcitation-familyretrieval; localdevicecohortวัดknown/disclosedlinks; SciFactแยกverificationcomponent ไม่เรียกทุกอย่างsemanticgold ใช้truegroup/sampleuncertaintyและreportstatisticallimits Seed/paraphraseไม่เพิ่มindependentn ไม่บังคับadaptivewin Goldอยู่evaluatorเท่านั้น

ทำ public/permitteddossier3cases ที่ใช้returnedvectorsจริง เดินnameddevice/comparator→facts/candidates/evidence/gaps→source/version/hash/locator→edit/reopenhistory→selected-versionJSON/TH/ENexport ต้องแยกdisclosedlink/retrievedcandidate/unjudged และenforcefieldrightsทุกchannel ส่งAPI/schemaexamples+compatibilitynoteให้Claudeผ่านrepo ไม่มีautomaticUImerge ไม่อ้างfrontendcompleteจากCLI

## 11. Acceptance และลำดับตัดงานเมื่อเวลาไม่พอ

| Milestone | หลักฐานขั้นต่ำ | ถ้าไม่พร้อม |
|---|---|---|
| Repairs | before/aftercounterexamples, exactcandidateclean-checkoutchecks, rights/evaluatornegativeboundaries | repairต่อโดยไม่provider |
| Export/contract | runtime-onlybundle, IDs/text/source/modelhashes, permittedremoteuse, counts/size | ทำlocalfixture/exportต่อ |
| Remote canary | exactcommands+allocationref+actualresource/numericreport | remoteBLOCKED_LOCAL; localworkต่อ |
| Full vector return | actualshards/counts/hash/order, interruptedresume, both-sidechecksums | PARTIALตามจริง ไม่claimfull |
| Local use | rejectedcorruptbundles+actualverifiedimport/exactsearch, matchingqueryencoder | แก้import/adapterต่อ |
| Shared evaluation/backend | matchedBM25/dense/hybridresultsและ3realdossiersที่traceถึงreturnedbundle | แยกcomponentที่completeจากที่pending |
| Closeout | exacttestedrevision, clean-checkoutscope, morningreport, resumablenextactions, Claudecontracthandoff | noforcedG1/G2/G3complete |

เมื่อallocation/timeเหลือน้อย ให้ให้ความสำคัญกับ correctedend-to-endbaselineและlocalimport/demoก่อนmodelcomparisonเพิ่มเติม ถ้าพอทำหนึ่งconditionครบให้ส่งครบ ไม่เริ่มหลายmodelแล้วทิ้งทุกอย่างpartial หากremoteถูกblockตลอดคืน งานlocalrepairs/export/import/tests/sharedseamยังส่งได้ ไม่สร้างmockscientificscoreแทนremoteexecution

Stopเฉพาะdependentbranchเมื่อunknownhostkey/rights/allocation,hashmismatch,nonfinite/data-integrityfailure,resource/deadlineexhaustion,conflictingwriter,uncertainjobstateหรือusercancelled ไม่มีretryเพื่อbypassdenial/controls ไม่รันข้ามwindowโดยอ้างownerกำลังหลับ

## 12. Morning report และสิ่งที่ต้องเก็บใน repo

สร้าง canonical run folder ใหม่ตาม [audit convention](../README.md) เก็บ authoredsanitizedreports/receipts/manifests/checkpoint/NEXT_ACTIONS/contracthandoff ในrepo ตัวrawcorpora/qrels/weights/vectorbundles/privatejournalsอยู่permittedlocalstorageไม่ใช่publicGit สิทธิ์ดาวน์โหลดไม่ได้แปลว่าสิทธิ์redistributeหรือcommercialuse

`MORNING_REPORT_TH.md` ต้องมี:

1. Goalstatusแยกrepairs,remotecompute,vectorreturn,localintegration,evaluation,dossierbackend,UIpending พร้อมstart/endHEAD+branch/worktreeและconcurrentdrift
2. ExactSSH/code/configcommandsที่ใช้จริง,previousconnectionvsnewverifiedhostfacts,allocation/window/GPUUUIDหรือCPUquotaและactualjobexit ไม่ใส่keycontents/env/privateprocessargs
3. Input/model/source/manifesthashes,eligible/completed/failedcounts,shardsและmatchinglocalstoragepaths,checksums,interruption/resume/no-duplicateproof
4. Actualwall/CPU/GPUminutes/peakVRAM/RAM/disk/transferbytes/retries/OOM,providercalls/actualorunknowncostแยกกัน ไม่สรุปhistoricalspend0จากofflineguardcounts
5. Correctedmetricsพร้อมtask/label/selfpolicy/failuredenominator/groupuncertainty,3casewalkthroughและexacttestedcandidate/skipreasons
6. Remainingblockerระบุaction/target/reason,completedindependentwork,denied/pending/uncertainstate และnextcommandที่resumeได้ ขอownerเฉพาะสิทธิ์หรือresourceที่ขาดจริง ไม่ขอให้เลือกimplementationdetails

OpenRouterรอบแรกยังเป็นcumulativeUSD8จากauthorizationเดิม รวมsettled/pending/reservationsทุกrun ไม่ตั้งnewledgerเพื่อได้8ใหม่ งานนี้ควรจบโดยAPIUSD0 ถ้าไม่รู้historicalremainingให้เขียนUNKNOWNและไม่dispatchpaidcall การใช้GPUที่มีอยู่ไม่ใช่OpenRouterchargeแต่ต้องมีallocationของมันเอง ไม่มีautomaticbudgetexpansion/topup

เก็บhistoricalevidenceไว้และmarkproposed/implemented/mocked/NOT_RUNให้ตรง Artifact/testPASSไม่ใช่publication,clinical/FTO,commercialvalidationหรือjournalacceptance เวลาownerกลับมา ควรเปิดreturnedbundle+ผลเปรียบเทียบ+dossierbackendที่ใช้ได้จริง หรือเห็นpartialพร้อมexactremainingaction ไม่ต้องอ่านreceiptloopหลายชุดเพื่อรู้ว่างานไปถึงไหน
