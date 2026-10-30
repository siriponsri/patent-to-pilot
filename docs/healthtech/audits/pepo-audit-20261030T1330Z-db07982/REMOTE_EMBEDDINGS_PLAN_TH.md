# Remote embeddings → verified local vectors

**เป้าหมายคือย้าย compute ไป dr-train แล้วใช้ผลบน Windows** ไม่ใช่ย้าย semantic gold creation ไป server แผนนี้ยัง NOT_RUN: audit ไม่ SSH, ไม่สำรวจ GPU จริง, ไม่ encode โมเดล และไม่ย้ายข้อมูลขึ้นเครื่องอื่น

## 1. Current architecture ที่ตรวจได้

`evaluation/healthtech/local_retrieval.py:223` สร้าง ONNX CPU session, tokenizer max_length256, attention-mask mean pooling แล้ว L2 normalization (`:237–240`) `SharedRetriever:294` encode corpus ทั้งชุดใน call เดียวและทำ query matrix product (`:297–301`) ไม่มี persisted shard/import/cache contract ใน tracked paths ที่ตรวจ

Existing encoder `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` เป็น384dim; current file คือ quantized AVX2 ONNX ไม่ใช่ GPUfloat32 โดยอัตโนมัติ Reranker `cross-encoder/ms-marco-MiniLM-L-6-v2` revision `233902d25c440f23af6f7d6e94d2946bac0bee0a` ทั้งสอง ONNX/tokenizer รวม4 ไฟล์ hash ตรง existingmanifest ไม่มี inference ใน audit

45,336 ×384float32 final vectors = **69,636,096bytes**, query1,247vectors =1,915,392bytes แต่ token-outputtensor N×256×384float32 เพียงตัวเดียวประมาณ**16.6GiB** ก่อน model/intermediates นี่คือ shape arithmetic ไม่ใช่ measuredOOM จึงต้อง batch ไม่ใช่ส่ง45K เอกสารเข้ารอบเดียว

DAPFAM ใช้ title_en+abstract_en และ opaque family IDs ในอีก BM25pipeline ไม่ใช่ canonicalUS/EPpublication IDs Product `healthtech/engine.py:106/130/136` ยังใช้ FTS และ lexical/token-overlapapproximation (`policies.py:21`) การเพิ่ม denseevaluationscript อย่างเดียวจะยังไม่ทำให้ localapplication ใช้ vectors

## 2. สิ่งที่ทำได้ก่อนมี semanticlabels หรือ GPUslot

ทำ runtime-only export/schema/shard writer/validated importer/exact local index/shared retrieval seam และ authored numeric fixtures ได้ทันทีด้วย CPU/no-provider Semantic labels จำเป็นสำหรับ semantic qualityclaim แต่ไม่จำเป็นสำหรับ encoding,ID-order integrity,transfer checksum หรือ localnearest-neighborfunctionality DAPFAMqrels ใช้วัด citation-familytask;existingdisclosedlinks ใช้ known-linktask ตาม scope

Proposed commands/modules ที่ futureLuna ต้อง implement เอง (ยังไม่มีใน HEAD นี้): export_embedding_inputs, encode_embedding_shards, validate_vector_bundle, import_precomputed_vectors และ runnerflags สำหรับ sharedretriever/dossierbackend ส่ง actualCLIusage หลัง implement ห้ามอ้างว่าคำสั่งเหล่านี้มีแล้ว

## 3. Remote execution contract และการอยู่ร่วมกับ Podi

ยังไม่พบ project-owneddr-trainhost/user/workspace/GPUallocationcontract ใน paths ที่ตรวจ ไม่อ่าน globalSSHconfig/privatekeys/tokens/session เพื่อเดา และไม่ถือ GPU0 ว่าง

FutureLuna ใช้ existingapprovedSSH/hostverification เมื่อมี hostalias/user และ remotejobroot ที่ระบุได้ ตรวจ read-onlycapacity/process/GPUuuid/freeVRAM/disk/packages/jobownership ก่อน run การมี SSHlogin ไม่ได้แปลว่ายึดทุก GPU ได้ ต้องมี allocation ที่บันทึกไว้: GPUUUID หรือ CPUquota,VRAM/RAM/wall-time/disk budget,allowedjobdir และ Podi/shared-serviceconstraints ถ้ามี authority นี้อยู่แล้วใช้ต่อไม่ถามซ้ำ ถ้ายังไม่มีให้ขอเฉพาะ allocation ขาดจริงพร้อม canaryplan แล้วทำ localimplementation/fixtures ต่อ

ไม่ kill/restart/renicejob คนอื่น ไม่แก้ Podi ไม่เปิด remoteinferenceport ไม่เปลี่ยน SSHhost-key/security/ACL ไม่ปิด host-keychecking ไม่สร้าง key/credential ใหม่ ไม่ติดตั้ง unknownexecutables/remote-code model loaders การเช่า GPU/ซื้อ storage ไม่อยู่ใน OpenRouter8USD

## 4. Windows runtime input bundle

- Stable dataset-scoped ID namespaces: `dapfam_family` กับ `patent_publication` แยกกัน ห้าม convertopaqueIDs เป็นเลขสิทธิบัตรปลอม
- Export เฉพาะ source text ที่เลือก,IDs,source/text/config hashes และ provenance ที่จำเป็น **ไม่มี qrels/gold/semanticjudgments/split answers** ขึ้น encoder
- DAPFAM เริ่ม title+abstract เดิมเพื่อเทียบ BM25 ได้ตรง Representation ทดลองถัดไปค่อยเพิ่ม claims/sections/chunks เมื่อข้อมูลและสิทธิ์มี ไม่เปลี่ยน representation+model+controller พร้อมกันแล้วสรุปว่า adaptation ชนะ
- Manifest: dataset/source revision, raw/normalized/input SHA256, row-count/ID-order hash,exact text normalization/query-document prefixes,source-use/controlled-remote-processing decision,byte/disk bounds
- Empty/missing/duplicate/conflicting IDs/text ต้อง diagnose ไม่สร้าง zero vector หรือ skip เงียบๆ
- DAPFAMNC/SA/research-only และ restrictedsource-derivedvectors ยังไม่เข้า publicGit/productioncommercialscope โดยอัตโนมัติ เก็บ attribution และ intendeduse ตาม source เฉพาะ permittednon-sensitiveinputs ไม่มี patient/customer/privatejournal

## 5. Freeze model และ numeric semantics

MiniLM max_length256 เป็น integration baseline สำหรับตรวจ portability ไม่ใช่ patent semantic performance ceiling ต้องประกาศ truncation/chunking และ coverage ของข้อความที่ใช้ Alternative embedding model/longer context/chunking comparison เป็น separately specified condition พร้อม model/config namespace และ matched evaluation ไม่ปรับ baseline เงียบ ๆ

เริ่ม baseline384dim ที่ existingcache รองรับเพื่อพิสูจน์ portability ก่อน strongerencoder ถ้าเลือก PyTorch/CUDAFP32 แทน CPUquantizedONNX ให้เป็น**new named model/backend condition** ไม่แกล้งเรียก numericallyidentical model เดียวกัน

Pin model ID+immutable revision+artifact hashes,tokenizer,max length,truncation direction,special tokens,prefixes,chunk boundaries/overlap,mask pooling,normalization,dimension,inference/backend/export dtype,library versions และ device/job configuration ใช้ safetensors/ONNX จาก reviewedsource ตาม license ไม่ trust_remote_code/executeunknowncode

Canary เริ่มประมาณ32–100documents+10queries ที่มี short/long/Unicode/edgecases ไม่ใช้ testgold เลือก model Verify row/order/shape/norm/finite values และ same-modelCPU/GPUcosine เทียบ sameFP32graph เริ่ม tol เช่น abs1e-4/cosine1e-5 แล้วบันทึกเหตุผลปรับตาม backend หาก quantization/backend ต่างให้ reportdifference/rank-stability เป็น compatibilitystudy ไม่บังคับ bitwiseequality หรือ silentmix

Queryencoder บน local ต้อง matchdocumentmodel/text/prefix/pooling/norm/dimension หรือมี explicitcompatiblevariant ที่ canary พิสูจน์แล้ว Fixedqueryvectors ใช้ได้เฉพาะ querytext/confighash ตรง Dynamicappquery ยังต้อง localCPUqueryencoder หรือ approvedqueryjob ไม่ใช่ reusevector ของ query อื่น

อ้างอิง API ปัจจุบัน: [SentenceTransformer model/encode](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html) ต้อง pin actual revision/config ตามที่ใช้จริง ไม่พึ่ง defaultdevice/modeldownload โดยไม่บันทึก

## 6. Batching, shards, restart และ transfer

เริ่ม batch16–32 ปรับตาม observedVRAM/tokens ภายใน allocation ไม่ encodeallN ใน call เดียว บันทึก max/actualbatch,token counts,elapsed,GPUminutes,errors/OOM retries เริ่ม shard≤5000rows (384float32 ประมาณ7.7MB) และ finitewall/diskbudget ที่วัดได้ Retry/OOM ลด batch ด้วย samefrozenconfig ไม่ใช้ retry เป็นเหตุเปลี่ยน model เงียบๆ

Output: little-endianfloat32 `.npy` (`allow_pickle=False`), ordered IDs JSONL,per-rowtext/confighash,optionalchunkmap และ manifest ต่อ shard(start/end/count/shape/dtype/dim/bytehash/ID-orderhash/source+modelparenthash)

เขียน.partial → validatecount/shape/finite/hash → flush/fsync/atomicpublish → commitmanifest Resume เฉพาะ completedmatching shards Reject source/model/order/config mismatch Failures ต้องมี status/ID ที่ replay ได้ ไม่มี zero-filledsuccessfulrows

ใช้ approvedSSH/SCP/SFTP ส่งเฉพาะ namedjobartifacts ภายใต้ ownerjobdir ตรวจ checksum ทั้ง remote/local ก่อน atomicpromote PlainSCP ไม่ได้รับรอง arbitrarybyte-rangeresume ให้ retrywhole smallshards หรือ existingapprovedresumabletool ไม่ sync/delete ทั้ง home/repo/cloudvolume

## 7. Local validated import และ shared application seam

Importer ตรวจ sameexpected dataset/model/config hashes,exactIDset/order,uniqueIDs,shape/dimension/dtype/endianness,NaN/Inf/nonzero norms,shardcounts/checksums และ complete coverage ก่อน index พร้อม negative tests: swapped rows,duplicated/missing/extra IDs,altered shard/wrong model/stale query vector/partialmanifest/pathtraversal

เริ่ม exactcosine/dot ด้วย NumPy/memmap ที่45Kscale ก่อน ANN (ANN ถ้าเพิ่มต้องวัด recallvs exact) Deterministic ties byID ใช้ chunk→document→family aggregation ก่อน K ตาม task;dedup ก่อน cutoff ไม่คิด chunk ซ้ำเป็น hits เพิ่ม

เพิ่ม injectableprecomputedvector/retrievalprovider ที่ SharedRetriever และ dossierengine ใช้ร่วมกัน คง lexicalfallback/currentpolicynames และ lineage/rights/history/disclosedvscandidate distinctions Querydensevector+documentvector+BM25fusion+cross-encoder เป็น components ต่างกัน Documentembeddings แทน cross-encoderquery-documentrerank ไม่ได้

## 8. Deliverables ที่ตรวจได้

1. Exportedruntimebundle+source/model manifest และ no-evaluator-accesscheck
2. Remotejobcode/exactcommands+allocation/readinessrecord และ canarynumericreport
3. FullpermittedDAPFAMcorpus/queryvectors หรือ explicitpartialfailuremanifest ไม่ใช่ coverageaudit ใหม่เฉยๆ
4. Interrupted/resumedrun ที่ reusescompletedshards และ IDchecks ผ่าน
5. Hash-verifiedreturnedlocalshards+rejectiontests+localexactindex
6. BM25/dense/hybridmatchedtaskresults ด้วย correctedduplicate/self-IDpolicy และ actualresourcecounts
7. Localdossierbackenddemo ที่ใช้ returnedvectors จริง พร้อม source/edit/history/THENexport โดยไม่แตะ active Claude UI; backend worktree และ versioned contract handoff แยกจาก UIbranch ไม่มี automaticmerge
8. Report แยก remotecompute/numericintegrity/taskquality/source-rights/businessclaims และ preciseremainingblocks

หาก GPUallocation ยังไม่มา งาน1/5/adapter/tests ทำต่อได้เอง แต่ห้ามเขียนว่า remotevectors สำเร็จจาก syntheticmatrix หาก dataset/gold หนึ่งติด ให้ compute/evaluatecomponent ที่มีสิทธิ์และ labels เดิมได้ก่อน
