# dr-train resource preflight — 31 ตุลาคม 2026

**ตรวจอ่านอย่างเดียวสำเร็จ 2 ครั้ง ไม่มี allocation ให้ใช้ GPU/CPU จากรายงานนี้ และยังไม่เริ่มงาน compute** ใช้ existing SSH `chaw@100.77.149.83`, `StrictHostKeyChecking=yes`, `IdentitiesOnly=yes`, `BatchMode=yes`, `ForwardAgent=no` ทั้งสองครั้ง exit0 และ remote hostname เป็น `dr-train`

Snapshot1 `2026-10-31T00:49:34.766688Z`; snapshot2 `2026-10-31T00:51:00.341841Z` ห่างกัน 85.575 วินาที ไม่ใช่การยืนยันว่าทรัพยากรจะว่างต่อเนื่องตลอดคืน รายงานนี้มีไว้เก็บ requirements และเสนอ allocation ก่อนงานจริง ไม่ใช่ goal implementation หรือการปลด allocation gate

## GPU ที่เห็นจริง

| Index ตอนตรวจ | รุ่น | UUID | VRAM total MiB | Free MiB | Used MiB | Utilization |
|---|---|---|---:|---:|---:|---:|
| 0 | NVIDIA GeForce RTX 2080 Ti | `GPU-044a8b11-4729-458b-a07b-297e45439419` | 11264 | 10818 | 1 | 0% |
| 1 | Tesla V100-SXM2-32GB | `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089` | 32768 | 32495 | 0 | 0% |

ค่าทั้งสอง snapshot ตรงกัน Driver `580.178.04`, compute mode `Default` Free/used/total เป็นค่าคนละ fieldจากdriver ไม่เติมส่วนต่างให้ดูเหมือนว่างทั้งหมด Indexอาจเปลี่ยน ให้ผูกงานด้วยUUIDเมื่อมี allocation จริง ไม่มีการรันCUDA kernel/torch/modelเพื่อตรวจcompatibility

## CPU, RAM, disk

- Intel Xeon E5-2696 v3 @2.30GHz, 2 sockets ×18 cores ×2 threads =72 logical CPUs; process affinityเห็น72 แต่ไม่ใช่ quotaที่ได้รับอนุมัติ
- Load1/5/15นาที: snapshot1 [0.63720703125, 0.54443359375, 0.46728515625]; snapshot2 [0.36767578125, 0.4560546875, 0.4404296875] ค่าที่เห็นไม่ได้รับรองการใช้งาน CPU72 threads
- RAM total 125.76GiB, MemAvailable 117.03GiB ใน snapshot2 ไม่เอา MemFree มาปนกับ available และไม่ตีความ host available เป็น allocation
- `/home/chaw` และ `/tmp` เห็น filesystemเดียวกัน มี freeประมาณ 150.69GiB นับครั้งเดียว ค่านี้ไม่ใช่ user disk quota
- `/home/chaw/patent-to-pilot-jobs` ยังไม่มี ไม่ได้สร้าง การจะสร้าง directoryในownerjobscopeเป็นงาน executionภายหลัง ไม่ต้องถือชื่อ directoryเป็นเหตุหยุดงานlocalอิสระ

## Runtime และ cache ที่ตรวจ

`/usr/bin/python3` เป็น Python3.12.3 แต่ไม่พบ torch, onnxruntime/onnxruntime-gpu, sentence-transformers, transformers, tokenizers, numpy, safetensors, huggingface-hub, accelerate หรือ faiss ใน interpreterนี้ `nvcc` ไม่อยู่บนPATH ไม่ได้อ้างว่าไม่มีruntimeเหล่านี้ทั้งเครื่อง

ตรวจ metadata ของ named owned paths `.venvs`, `venvs`, `.venv`, `venv`, miniconda/anaconda/miniforge/mambaforge และ `.conda/envs` ภายใต้ homeของchaw ไม่พบ environmentที่ตรงขอบค้น ไม่ execute activation scripts/Pythonของenvอื่น ไม่ค้นหรือใช้ envของ Podi/ทีมอื่น

default HF cache `/home/chaw/.cache/huggingface/hub` มีอยู่ แต่ไม่พบ modeldirectoryที่ตรงคำค้น embedding/patent/MiniLM/PatEmbed รายละเอียดขอบคำค้นอยู่ใน probe ไม่ได้เปิดweightsหรือtokens Other named owned roots `~/models`, `~/model-cache`, `~/hf-cache`, `~/.cache/torch/sentence_transformers` ไม่มี อาจมี custompathที่ไม่ได้ให้ไว้ จึงไม่สรุปว่าไม่มีcacheทั้งเครื่อง

## PatEmbed ที่ผู้ใช้ใช้จริง

**ยังระบุ model ID/revision/checkpoint จริงไม่ได้** `git grep` ใน tracked textและ scoped `rg` ใน docs/configs/scripts/src/memory/methodology ไม่พบ `PatEmbed`, `PatentSBERTa` หรือ `bert-for-patents` ในขอบที่ตรวจ exit1หมายถึง no match ไม่ใช่ permission failure ดู [search record](PATEMBED_CHECKPOINT_SEARCH.json)

Local HealthTech model directoriesที่พบคือ `all-MiniLM-L6-v2`, `cross-encoder-ms-marco-MiniLM-L-6-v2`, `sentence-transformers-all-MiniLM-L6-v2` หลักฐานที่ใช้จริงของ Luna ยังเป็น MiniLM encoder ตาม [canary receipt](../luna-remote-embeddings-20261030T155013Z/CANARY_RECEIPT.json) และ source `scripts/healthtech/encode_vector_shards.py` ใช้ `DenseEncoder` ซึ่ง audited implementationเป็นCPU ONNX ไม่เรียกมันว่าPatEmbedหรือGPUencoder

ชื่อ PatEmbedจากคำถามownerยังไม่พอเลือกcheckpoint ให้ parentเทียบ modelrepository/revisionกับบริบทในแชต “Pepo patent-to-pilot” และ primary model research ก่อนเขียนgoalใหม่ หากยังหาไม่ได้ เก็บ requirementเฉพาะ exactmodelreferenceหรือsourceไฟล์เดิม ไม่เดาแทนผู้ใช้

## ข้อมูลสำหรับเสนอ allocation และเก็บ requirements

| ประเด็น | ข้อเท็จจริง/สิ่งที่ยังต้องตกลง |
|---|---|
| GPU candidate | V100มีobservedfree32,495MiBมากกว่า2080Ti10,818MiB แต่ยังไม่จอง/ไม่อนุมัติให้ใช้ ไม่รับรองmodel fitหรือCUDAwheelcompatibilityจากVRAMอย่างเดียว |
| เวลาและการแชร์ | ขอเฉพาะ allocation referenceที่มีอยู่ หรือยืนยันUUID/CPUquota+window/deadline+ข้อห้ามsharedservices ไม่เดาว่าทั้งเครื่องเป็นexclusive ไม่แตะPodi |
| Runtime | ต้องเลือกexisting environmentที่ownerมีสิทธิ์และบอกpath หรือ isolated pinned setupในscopeถัดไป ขณะนี้ยังไม่มีinstallation/downloadauthorityเพิ่มจากpreflightนี้ |
| Model | ต้องมีexactPatEmbed ID/revision/checkpoint, license/use, representation/chunkingและbackendก่อนประมาณVRAM/disk/เวลาจริง MiniLMเป็นintegrationbaselineได้แต่ไม่ใช่เพดานpatentsemantics |
| Bounds | ตกลงwall/VRAM/RAM/disk/downloadlimitsตามmodelจริง จากนั้นcanaryวัดpeak/throughputก่อนfullrun ไม่เสนอตัวเลขperformanceหรือcostที่ยังไม่วัด |
| งบ | API$0ในpreflightนี้ ไม่ใช่การรีเซ็ตงบOpenRouterเดิมUSD8หรือการอนุมัติใหม่ หากขอบpaidproviderยังไม่ชัดให้เก็บrequirementsกับownerแยก ไม่ทำpaidcalls |

ไม่ต้องขอ expert labels ใหม่เพื่อเริ่ม embedding/import ภายใต้สิทธิ์ที่มี ปัญหา semantic-label evidence เป็นอีก branch การเห็นhardwareพร้อมไม่ได้ทำให้gold/source-rights/budgetหรือallocationพร้อมอัตโนมัติ

## ขอบเขตและหลักฐาน

Repo start/end HEAD `0d049802d36bc2eebe60331ec444d62469fd767f` tracked treeสะอาดและไม่เปลี่ยน มีเพียง report folderใหม่นี้ ไม่commit/push/เปลี่ยนmainimplementation/เปิดjob/download/install/settings/credentials/Podi รายงานใช้ lightweightread-onlymetadata probes2processes ไม่ใช่model inference ไม่dumpenv/processcmdlinesหรืออ่านprivatekeycontents

- [Snapshot1](snapshot-1.json), [snapshot2](snapshot-2.json), [machine verification](verification.json), [manifest](manifest.json)
- [Probe snapshot1](resource_probe_snapshot_1.py), [probe snapshot2](resource_probe_snapshot_2.py), [invocation template](invoke_preflight.ps1)
- [Next actions](NEXT_ACTIONS.md)

Timestampในsnapshot exportsมีoffset `+07:00` เพราะPowerShellแปลงJSONdateเป็นlocaloffsetขณะserialize เก็บต้นฉบับexportsไว้ครบและ normalize instantเป็นUTCในverification/รายงานนี้ ไม่ใช่remoteclockคลาด7ชั่วโมง ไม่มีunresolvedtooldenial
