# Execution plan — ลงมือให้จบเป็นผลลัพธ์

ทุกขั้นยัง **PROPOSED / NOT_RUN ในงานจัดเอกสารนี้** เลือกชื่อ module/CLI ตาม repo จริง ส่ง actual commands หลัง implement ไม่อ้างว่าชื่อ interface ด้านล่างมีแล้ว อ่าน [authorization](AUTHORIZATION_AND_BUDGET.md) ก่อน action

## P0 — snapshot, ownership และรวมเฉพาะ repair ที่จำเป็น

ตรวจ currentHEAD/main/origin/tracked+untracked/worktrees และ applicable AGENTS อีกครั้ง ฐานเอกสาร 0d04980 Claude UI PR#1 merged แล้ว แต่ clean branch ไม่ได้พิสูจน์ว่า worker idle ห้าม checkout/แก้ branch ของ Claude หรือ Luna สร้าง isolatedgoal branch/worktree และจด single-writer/file ownership ไม่ delegatewriters โดยไม่มี explicitauthority

Pepo vector repairs ยังอยู่ worktree `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-pepo-unblock-20261030`, branch `codex/pepo-unblock-remote-20261030` ที่ a0ec9ce มี dirty tested changes ตรวจ [repair receipt/patch](../../audits/pepo-unblock-remote-20261030T2038Z/README.md) และ current hash ก่อน port เฉพาะ vector crash-after-final-commit recovery, OS single-writer lock, child/parent binding และ regressions Main มี metadata-rights fix แล้ว ห้าม applywholeoldpatch ทับ currentengine/UI

ทำ before/after hand-computable tests ของ remaininggaps โดยไม่เอา full old experiments มารันซ้ำ ไม่รวม unrelatedowner files เพื่อให้ git สะอาด เก็บ testedworking diff hash ก่อน commit และ exactfinalcandidate checks หลัง commit

## P1 — local HTTP jobs + UI ที่รันงานได้จริง (ไม่รอ GPU/API)

ใช้ shared engine/history contracts เดิม มี local service บน loopback, durable job state/result store และ versioned HTTP adapter UI อาจเริ่มจาก `POST /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/cancel`, history read/edit/export routes **นี่คือ proposedroutes ที่ต้อง implement** ไม่ใช่คำสั่งเรียก existingservice `healthtech/api.py`ปัจจุบันเป็น dry-run/mock seam ไม่ใช่ HTTP server

State อย่างน้อย queued/running/cancel_requested/cancelled/succeeded/failed/interrupted/unknown พร้อม stablejobID, idempotencykey, inputs/model/protocol hash และ timestamps หนึ่ง writer ต่อ job บันทึก committedresults แบบ atomic และ history optimistic expected-version ห้าม browser ส่ง arbitraryshellcommand/unsafeoutputpath ห้าม cancel แล้วลบ successfulsteps/unknown billing

Provider selector มี Local Qwen3-8B และ API Qwen3-32B แสดง availability/reason, model/backend revision, estimated cost พร้อม units, settled/reserved/unknown/remaining และ freshness จาก backend Budgetcontroller บังคับทุก APIaction แม้ browser แก้ payload เอง Key อยู่ approvedserver integration เท่านั้น ไม่อยู่ browser/localStorage/logs API embeddings ไม่มีตัวเลือกหรือ hiddenfallback

หาก localmodel ไม่พร้อมหรือ APIbudget ไม่ผ่าน ให้แสดงเหตุผลและทางเลือกที่ผู้ใช้เลือกได้ ไม่ silentlyfallback เป็น paidAPI หรือเปลี่ยน model/condition เมื่อ localAPIcharge เป็น USD0 ยังต้องแสดง localresourceusage ไม่เรียก compute ว่าฟรี

เปลี่ยน capabilities เป็น true เฉพาะหลัง realservicecheck ผ่าน ช่วง pending ให้ runlocallexical/mock เฉพาะ engineeringfixtures และติดป้าย mock ชัด UI ต้องแสดงว่างานใดรันจริง/ยังรอ resource รักษา TH/ENminimalformaljourney กับ currentthemes ไม่ให้ end-user ต้องรู้ชื่อ checkpoint/CLI เพื่อใช้ dossier

ทดสอบ backendcontracts, duplicate submit, restart, cancel-before/afterdispatch, version conflict และ unknownoutcome จากนั้น browser จริงทำ start→observe→cancel acknowledgment→reopenhistory→export โดยไม่ใช้ simulation แทน servererror ต้องคง existing file import และ IndexedDBnamespace ไม่ปน backendDossierVersion

Localservice/tunnel ผูก 127.0.0.1 เท่านั้น ใช้ exactapprovedSSHforward เมื่อจำเป็น ไม่ publicports/0.0.0.0/CORSwildcard/firewall/accountsettings/credentialcreation จาก goal นี้ ไม่มี deployment

## P2 — acquire/freeze models + runtime/data export

ใช้ [model/data protocol](MODEL_AND_DATA_PROTOCOL.md) ดาวน์โหลด HF shortlist weights/config/tokenizer/modules/license เข้า permitted Windows storage ก่อนบันทึก immutable commit+file SHA256+byte counts แล้ว securecopy เฉพาะ named artifacts ไป dr-train ตาม allocation/setup ที่อนุมัติ ไม่ execute unknown remote code หรือ raw dataset scripts เก็บทั้ง Windows และ remote storage accounting รวม caches/staging/temp/shards/env/dependencydownloads ภายใต้ additionaldisk รวม 40 GiB ไม่ใช่ 40 GiB ต่อเครื่อง

ทำ peak storage plan ก่อน download: allowlist เพียง weight format ที่ใช้จริง ไม่โหลดทั้ง bin และ safetensors/ทุก quantization ไม่สร้าง cache หรือ staging สำเนาซ้อนโดยไม่คิด bytes รัน embedding ทีละ model และเก็บ verified Windows ต้นฉบับไว้ หลัง vectors กลับมาและยืนยัน hash แล้วจึง reclaim เฉพาะ recoverablejob-ownedremoteweights/temp ของ condition ที่จบเพื่อเหลือที่ให้ Qwen3-8B ไม่ลบ original/sharedcache/evidence ของผู้อื่น ถ้า actual required peak เกิน 40 GiB ให้หยุด dependent download และเสนอ phase ลด duplicates หรือขอเพิ่มเฉพาะส่วนที่เกินจริง ห้าม silent ใช้พื้นที่เพิ่ม

ส่ง encoder เฉพาะ runtime text/IDs/source+text hashes/config ไม่มี qrels/gold/splitanswers Use DAPFAM เดิม 45336corpus/1247queries สำหรับ citation-familydiagnostic และแยก realpatentpublicationbundle สำหรับ devicecases ไม่ coerceopaqueDAPFAMIDs เป็น patentIDs

Pin reviewed runtime ที่รองรับ V100 SM70 จาก officialdependencies ใน isolatedenv/container **setup ได้รับอนุมัติแล้ว** ไม่ upgradesystem Python/driver ใช้ FP16 หรือ qualifiedquantization/eager หรือ compatible attention ไม่สมมติ BF16/FlashAttention2 Checkactualcompiled arch/kernel และ small numeric canary ก่อน fullrun การเห็น nvidia-smi ไม่พิสูจน์ runtime compatibility

## P3 — remote canary/full shards → verified Windows import

ใช้ SSHexistingidentity `chaw@100.77.149.83`, strictknown-hostchecking/BatchMode/ForwardAgent=no ห้าม copy หรือ printprivatekey ตัวอย่าง Windowskeypath สร้างด้วย `Join-Path ([Environment]::GetFolderPath('UserProfile')) '.ssh/id_ed25519_dr_train'` ใช้ approvedaccount ไม่ย้าย key เข้าระบบอื่น

ตรวจ capacity อีกครั้งแต่ใช้ UUID เฉพาะที่ owner ยืนยัน concurrency 1 และ embedding/generation สลับกัน บันทึก 24hUTCdeadline ก่อน runtime job แรก ใช้ finite owned-process supervisor, hard wall/resource limits, log rotation, heartbeat, shutdown ของ run ตัวเองเท่านั้น ไม่ kill/renice/restartjob อื่นหรือแตะ Podi

ผูก device ด้วย approvedUUID และ assert มองเห็น GPU เดียว ไม่ใช้ index0 ของ host เป็น authority จำกัด CPU ที่ process/jobscope ให้รวมไม่เกิน 8 threads (เช่น OMP/MKL/PyTorch/ORTthreadlimits และ worker count ที่ตรึง) วัด RSS ของ ownedjobtree รวมไม่เกิน 32 GiB หยุดก่อนชน bound และห้ามเพิ่ม workers แก้ช้า Monitoradditionaldisk รวมทั้ง Windows+remote กับ manifest ก่อนและระหว่าง write ไม่เปลี่ยน globalsettings หรือยืมทรัพยากรคนอื่นเพื่อให้ผ่าน

Canary64rows+queries ที่มี long/Unicode/edgecases ใช้ same frozen encoder config ทั้ง query/doc จากนั้น fulleligiblebundle ด้วย batch ที่วัดได้/shards เช่น≤5000rows Publish.partial→fsync→validate/hash→atomiccommit→checkpoint; importer ไม่เห็น 0byte/intermediategeneration Resumematchingcompletedshards เท่านั้น proveinterruption/reconnect/idempotence โดยไม่ compute สำเร็จซ้ำ

Lock เป็น process-owned หรือ lease ที่ตรวจ identity ได้จริง ห้ามเดาจาก PID/อายุไฟล์เพื่อ takeover ถ้า disconnect ให้ reconnect อ่าน heartbeat/exit/status ก่อน launch ซ้ำ Unknownjobstate หยุดเฉพาะ remoteactions ใช้ boundedretries; OOM ลด batch โดยคง semanticconfig ถ้าลด context/เปลี่ยน chunk/precision ให้เป็น condition ใหม่และไม่ mixshards หยุดเมื่อ budget/deadline/ขั้นต่ำยัง fail ไม่ retry ไม่จบ

SFTP/SCP ส่ง namedshards กลับ`.partial` ตรวจ SHA256 ทั้งสองฝั่งและ manifestinput/model/order/shape/dtype/finite/IDs ก่อน localcommit PlainSCP ไม่ใช่ byte-rangeresume; retrywholeboundedshard หรือ SFTPresume บน immutablefile แล้ว fullhashcheck ห้าม recursive sync/delete/homecopy

เริ่ม exactNumPy/memmaplocalindex deterministicties ตรวจ corrupt/swap/missing/extra/duplicate/wrongmodel และ queryconfignegativecases ต่อ shared retrieval provider เข้า evaluation และ dossierbackend จริง Dynamicqueries ต้อง matchinglocal query encoder หรือ declaredprivatequeryservice ไม่แทน cross-encoderreranker ด้วย docvectors

## P4 — adaptive acquisition + frozen-evidence generation

ทำ B0/B1/B2/B3 ก่อนบน development แล้วเลือก budget/actiondefaults Freeze ก่อน untouchedgroups อย่าถือ Stryker หรือ holdout ที่เคยเห็นว่า globallyuntouched รัน boundedB4 โดยใช้ localQwen3-8B เป็น defaultcontroller; APIcontroller ถ้าจำเป็นต้องใช้ Qwen3-32B ตัวเดียวที่เลือกและ admit ผ่าน ledger แยก condition ชัดจาก generationcomparison

For O3 สร้าง evidence pack ที่ outbound rights อนุญาตทั้งสองระบบ hashorder/exactspans/tokenbudgets/schema/prompts; รัน local8B และ API32B แบบ nonthinking ตรวจ modeparameters/output ที่ route รองรับจริง หาก honormode ไม่ได้ให้ markincompatible/separatecondition ไม่ปลอมว่าเทียบ mode เดียวกัน Noextra paidjudgebydefault

## P5 — real E2E, report และ PR

สาม case เดิน browserHTTPjob→returnedvectors→shared acquisition→bounded generation→source/locatorchecks→useredit/history→selected-versionJSON/TH/ENexports มี attribution/unresolved/associationtypes ถูก ถ้า source หนึ่ง blockexternalexport ให้ UI แสดงจริงและ local research เก็บได้ตามสิทธิ์ ไม่ใช้ sourcepublicURL เป็น license

Runrelevanttargetedchecks ก่อน แล้ว finalbackendguardedtests+frontendunit/browseracceptance ที่แตะจริง ใช้ freshallowedtesttemp ไม่แก้ ACL เพื่อผ่าน tests ตัวอย่าง existingentrypoints ที่ตรวจพบ: `rtk proxy python -B scripts/healthtech/verify_offline.py <fresh-output> --suite all`; ใน `frontend/healthtech-web`: `rtk proxy npm test`, `rtk proxy npm run test:e2e`, `rtk proxy npm run test:integration` ตรวจ requiredenv/options จาก currentharness ก่อนใช้ ไม่รันทันทีจากเอกสารนี้

ส่ง report ตาม [checkpoint/reporting](CHECKPOINT_AND_REPORTING.md), scoped testedcommits/push branch/test PR พร้อม exactremoteidentity และ secret/license checks Owner อนุมัติ merge main หลังผ่าน acceptance แล้ว ตรวจ main/PRhead ก่อน merge และ retestcandidate หากเกิด race เคารพ required reviews/protections โดยไม่ impersonateApprove หรือ bypass ไม่มี force push ถ้า 24h/เงินหมดให้หยุด paid/compute และส่ง partial พร้อม actual deliverables/next command ไม่เริ่ม full sweep เพิ่มเพื่อใช้เวลาให้ครบ
